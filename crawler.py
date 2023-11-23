from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException, NoSuchElementException
import time
import tldextract
from database import create_connection, insert_cookie_data, insert_research_data
from config import DATABASE_PATH
import threading


class Crawler:
    def __init__(self, headless=False):
        self.driver = None
        self.headless = headless
        
    def start_browser(self):
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument("--headless")
        try:
            self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
        except WebDriverException as e:
            print(f"Error starting the browser: {e}")

    def quit_browser(self):
        if self.driver:
            self.driver.quit()

    def navigate_to(self, url):
        try:
            self.driver.get(url)
            time.sleep(5)
        except WebDriverException as e:
            print(f"Error navigating to {url}: {e}")

    def get_cookies(self):
        try:
            return self.driver.get_cookies()
        except WebDriverException as e:
            print(f"Error getting cookies: {e}")
            return []
        
    def categorize_cookies(self, base_url, cookies):
        base_domain = tldextract.extract(base_url).registered_domain
        first_party = []
        third_party = []

        for cookie in cookies:
            cookie_domain = tldextract.extract(cookie['domain']).registered_domain
            if cookie_domain == base_domain:
                first_party.append(cookie)
            else:
                third_party.append(cookie)

        return first_party, third_party

    def google_search(self, query, max_results=5):
        self.navigate_to(f"https://www.google.com/search?q={query}")
        links = self.driver.find_elements_by_css_selector('.tF2Cxc .yuRUbf a')
        return [link.get_attribute('href') for link in links[:max_results]]

    def extract_page_data(self, url):
        self.navigate_to(url)
        # Example extraction logic (needs to be tailored to your needs)
        title = self.driver.find_element_by_tag_name('h1').text
        content = self.driver.find_element_by_tag_name('body').text
        return {'url': url, 'title': title, 'content': content}

    def run(self, urls, mode='scrape', max_results=5):
        conn = create_connection(DATABASE_PATH)
        if conn is None:
            print("Error! Cannot create a database connection.")
            return

        self.start_browser()
        if mode == 'research':
            for term in urls:  # In research mode, urls are search terms
                search_urls = self.google_search(term, max_results=max_results)
                for url in search_urls:
                    page_data = self.extract_page_data(url)
                    insert_research_data(conn, (term, page_data['url'], page_data['title'], page_data['content']))
        else:  # Scrape mode
            for url in urls:
                self.navigate_to(url)
                cookies = self.get_cookies()
                first_party, third_party = self.categorize_cookies(url, cookies)
                for cookie in first_party + third_party:
                    is_first_party = cookie['domain'] == tldextract.extract(url).registered_domain
                    cookie_data = (url, cookie['name'], cookie['value'], cookie['domain'], 
                                   cookie['path'], cookie.get('expiry'), cookie.get('httpOnly'), 
                                   cookie.get('secure'), is_first_party)
                    insert_cookie_data(conn, cookie_data)

        conn.close()
        self.quit_browser()

if __name__ == "__main__":
    # Example usage
    crawler = Crawler(headless=True)
    crawler.run(["https://www.example.com"], mode='scrape')

