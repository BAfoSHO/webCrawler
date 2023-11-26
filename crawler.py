from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from export_cookies import export_cookies_to_csv
import tldextract
from database import create_connection, init_db, insert_cookie_data, insert_research_data
from config import DATABASE_PATH
import sqlite3
import logging
import sys

logging.basicConfig(filename='crawler.log', level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')


def check_for_duplicate(conn, table, url):
    """ Check if the given URL already exists in the specified table """
    try:
        cur = conn.cursor()
        sql = f"SELECT id FROM {table} WHERE url = ?"
        cur.execute(sql, (url,))
        return cur.fetchone() is not None
    except sqlite3.Error as e:
        print(f"Error checking for duplicates: {e}")
        return False


class Crawler:
    def __init__(self, headless=False):
        self.driver = None
        self.headless = headless
        self.conn = None
        self.domain_counter = {}

    def start_browser(self):
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument("--headless")
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
        except WebDriverException as e:
            print(f"Error starting the browser: {e}")

    def quit_browser(self):
        if self.driver:
            self.driver.quit()

    def navigate_to(self, url):
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
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
        links = self.driver.find_elements(By.CSS_SELECTOR, '.tF2Cxc .yuRUbf a')
        return [link.get_attribute('href') for link in links[:max_results]]

    def extract_page_data(self, url):
        self.navigate_to(url)
        try:
            title = self.driver.find_element(By.TAG_NAME, 'h1').text
            content = self.driver.find_element(By.TAG_NAME, 'body').text
            return {'url': url, 'title': title, 'content': content}
        except NoSuchElementException as e:
            print(f"Error extracting data from {url}: {e}")
            return {'url': url, 'title': '', 'content': ''}
        
    def update_domain_counter(self, domain, count):
        if domain in self.domain_counter:
            self.domain_counter[domain] += count
        else:
            self.domain_counter[domain] = count

    def research_mode_logic(self, query, max_results):
        search_results = self.google_search(query, max_results)
        for url in search_results:
            if not check_for_duplicate(self.conn, 'research_data', url):
                try:
                    page_data = self.extract_page_data(url)
                    if page_data['title'] and page_data['content']:
                        research_data = (query, page_data['url'], page_data['title'], page_data['content'])
                        insert_research_data(self.conn, research_data)
                except Exception as e:
                    print(f"Error processing {url} in research mode: {e}")
            else:
                print(f"Duplicate found, skipping: {url}")

    def scrape_mode_logic(self, urls):
        for url in urls:
            if not check_for_duplicate(self.conn, 'cookies', url):
                try:
                    self.navigate_to(url)
                    cookies = self.get_cookies()
                    first_party, third_party = self.categorize_cookies(url, cookies)

                    # Update domain counter here
                    domain = tldextract.extract(url).registered_domain
                    self.update_domain_counter(domain, len(first_party) + len(third_party))

                    for cookie in first_party + third_party:
                        is_first_party = cookie['domain'] == domain
                        cookie_data = (url, cookie['name'], cookie['value'], cookie['domain'], 
                                    cookie['path'], cookie.get('expiry'), cookie.get('httpOnly'), 
                                    cookie.get('secure'), is_first_party)
                        insert_cookie_data(self.conn, cookie_data)
                except Exception as e:
                    print(f"Error processing {url} in scrape mode: {e}")
            else:
                print(f"Duplicate found, skipping: {url}")

    def display_domain_counts(self):
        for domain, count in self.domain_counter.items():
            print(f"Domain: {domain}, Cookie Count: {count}")

    def export_cookies(self, csv_file_path):
        export_cookies_to_csv(DATABASE_PATH, csv_file_path)

    def purge_database(self):
        """Purges data from the database tables."""
        conn = self.conn or create_connection(DATABASE_PATH)
        if conn is None:
            print("Error! Cannot create a database connection.")
            return

        try:
            with conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM cookies")
                cur.execute("DELETE FROM research_data")
            print("Database purged successfully.")
        except sqlite3.Error as e:
            print(f"Error purging database: {e}")

    def run(self, input_data, mode='scrape', max_results=5, export_to_csv=False):
        self.conn = create_connection(DATABASE_PATH)
        if self.conn is None:
            print("Error! Cannot create a database connection.")
            return

        self.start_browser()
        if mode == 'research':
            for query in input_data:
                self.research_mode_logic(query, max_results)
        else:  # Scrape mode
            self.scrape_mode_logic(input_data)

        self.conn.close()
        self.quit_browser()

        if export_to_csv:
            self.export_cookies('cookies_export.csv')


def display_help():
    print("Crawler Help:")
    print("  - 'scrape': Enter scrape mode to crawl specified URLs for cookies.")
    print("  - 'research': Enter research mode to perform search queries and extract data from the results.")
    print("  - 'q', 'quit', or 'exit': Quit the crawler.")
    print("  - '-help': Display this help information.")
    print("  - 'purge': Purge the database of all data.")


def prepend_http(urls):
    return [url if '://' in url else 'http://' + url for url in urls]


if __name__ == "__main__":
    init_db()
    crawler = Crawler(headless=True)

    while True:
        command = input("Enter command ('-help' for options): ").strip().lower()

        if command == '-help':
            display_help()
        elif command in ['q', 'quit', 'exit']:
            print("Quitting the crawler.")
            break
        elif command == 'scrape':
            urls = input("Enter URLs to scrape, separated by commas: ").split(',')
            urls = prepend_http(urls)  # Prepend 'http://' if missing
            crawler.run(urls, mode='scrape')
        elif command == 'research':
            queries = input("Enter search queries, separated by commas: ").split(',')
            crawler.run(queries, mode='research')
        elif command == 'purge':
            confirmation = input("Are you sure you want to purge the database? (yes/no): ").strip().lower()
            if confirmation == 'yes':
                crawler.purge_database()
            else:
                print("Purge cancelled.")
        else:
            print("Invalid command. Enter '-help' for options.")

    print("Crawler has been stopped.")

