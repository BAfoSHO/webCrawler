from config import DATABASE_PATH
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException, NoSuchElementException
import time
import tldextract
from database import create_connection, create_table, insert_cookie_data, init_db


# Path to your SQLite database file
DATABASE_PATH = 'cookies.db'

# Initialize the database
init_db(DATABASE_PATH)


class Crawler:
    def __init__(self, driver_path, headless=False):
        self.driver_path = driver_path
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
            raise

    def quit_browser(self):
        if self.driver:
            self.driver.quit()

    def navigate_to(self, url):
        try:
            self.driver.get(url)
            time.sleep(5)
        except WebDriverException as e:
            print(f"Error navigating to {url}: {e}")
            raise

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
    
    def run(self, urls, analyze_cookies=False):
        conn = create_connection("DATABASE_PATH")
        if conn is None:
            print("Error! Cannot create a database connection.")
            return
        self.start_browser()
        for url in urls:
            try:
                self.navigate_to(url)
                cookies = self.get_cookies()

                if analyze_cookies:
                    first_party, third_party = self.categorize_cookies(url, cookies)
                    # Process and save the categorized cookie data
                    for cookie in first_party + third_party:
                        cookie_data = (url, cookie['name'], cookie['value'], cookie['domain'], 
                                       cookie['path'], cookie.get('expiry'), cookie.get('httpOnly'), 
                                       cookie.get('secure'), cookie['domain'] == url)
                        insert_cookie_data(conn, cookie_data)
                    print(f"First-party cookies: {first_party}")
                    print(f"Third-party cookies: {third_party}")
                else:
                    # Process and save general cookie data
                    for cookie in cookies:
                        # Assume a similar structure for cookie_data as above
                        insert_cookie_data(conn, cookie_data)

            except Exception as e:
                print(f"Error running the crawler on {url}: {e}")
        conn.close()
        self.quit_browser()

if __name__ == "__main__":
    urls = ["https://www.example.com"]
    crawler = Crawler(headless=True)
    crawler.run(urls, analyze_cookies=True)

