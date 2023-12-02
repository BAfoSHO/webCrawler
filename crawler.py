from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException, NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from export_cookies import export_cookies_to_csv
from proxy_config import ProxyManager
import urllib.robotparser
import tldextract
from database import create_connection, init_db, insert_cookie_data, insert_research_data
from config import DATABASE_PATH
import sqlite3
import logging
import sys

#logging.basicConfig(filename='crawler.log', level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')


def check_for_duplicate(conn, table, url):
    # Check if the URL already exists in the database
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
        self.user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) " \
        
    def ask_for_proxies(self):
        use_proxy = input("Do you want to use a proxy? (yes/no): ").strip().lower()
        if use_proxy == 'yes':
            proxy_input = input("Enter 'file' to use a 'proxies.txt' file or directly enter proxies, separated by commas: ").strip()
            if proxy_input.lower() == 'file':
                try:
                    with open('proxies.txt', 'r') as file:
                        proxies = file.read().splitlines()
                        return proxies
                except IOError:
                    print("Error: proxies.txt file not found.")
                    return None
            else:
                proxies = proxy_input.split(',')
                return proxies
        else:
            return None

    def start_browser(self):
        options = webdriver.ChromeOptions()
        options.add_argument(f'user-agent={self.user_agent}')
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

    def can_fetch_url(self, url):
        # check robots.txt to see if the URL is allowed to be crawled
        parsed_url = urllib.parse.urlparse(url)
        robots_url = urllib.parse.urlunparse((parsed_url.scheme, parsed_url.netloc, '/robots.txt', '', '', ''))
        
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()

        return rp.can_fetch(self.user_agent, url)

    def accept_cookies(self):
        # List of potential selectors for consent buttons
        consent_button_selectors = [
            {'type': By.XPATH, 'value': '//button[contains(text(), "Accept")]'},
            {'type': By.XPATH, 'value': '//button[contains(text(), "Agree")]'},
            {'type': By.XPATH, 'value': '//button[contains(text(), "OK")]'},
            {'type': By.XPATH, 'value': '//button[contains(text(), "Got it")]'},
            {'type': By.XPATH, 'value': '//button[contains(text(), "Allow")]'},
            {'type': By.XPATH, 'value': '//button[contains(text(), "Accept All")]'},
            {'type': By.XPATH, 'value': '//button[contains(text(), "I agree")]'},
            {'type': By.XPATH, 'value': '//button[contains(text(), "Continue")]'},
        ]

        for selector in consent_button_selectors:
            try:
                # Wait for the consent button to be clickable
                wait = WebDriverWait(self.driver, 5)  # Adjust timeout as needed
                consent_button = wait.until(EC.element_to_be_clickable((selector['type'], selector['value'])))
                consent_button.click()
                print("Consent button clicked.")
                break  # Exit the loop if a button is clicked
            except TimeoutException:
                print("Consent button not found for selector:", selector)
                # Try the next selector
            except Exception as e:
                print(f"Error while clicking consent button: {e}")
                # Log the error and try the next selector

        # Handle cases with multiple consent steps
        # Add additional logic here if needed

        # If no consent elements are detected, proceed
        print("Proceeding without clicking consent button.")

    def get_cookies(self):
        try:
            cookies = self.driver.get_cookies()
            for cookie in cookies:
                print(f"Cookie data: {cookie}")
            return cookies
        except WebDriverException as e:
            print(f"Error getting cookies: {e}")
            return []

    def categorize_cookies(self, base_url, cookies):
        base_domain = (tldextract.extract(base_url).registered_domain)
        first_party = []
        third_party = []

        for cookie in cookies:
            # Normalize the cookie domain by stripping leading dots
            cookie_domain = cookie['domain'].lstrip('.')
            # Check if the cookie's domain is the base domain or a subdomain of the base domain
            if cookie_domain == base_domain or cookie_domain.endswith('.' + base_domain):
                first_party.append(cookie)
            else:
                third_party.append(cookie)

        return first_party, third_party

    def google_search(self, query, max_results=5):
        # Perform a Google search and return the top results
        self.navigate_to(f"https://www.google.com/search?q={query}")
        links = self.driver.find_elements(By.CSS_SELECTOR, '.tF2Cxc .yuRUbf a')
        return [link.get_attribute('href') for link in links[:max_results]]

    def extract_page_data(self, url):
        # Extract the page title and content
        self.navigate_to(url)
        try:
            title = self.driver.find_element(By.TAG_NAME, 'h1').text
            content = self.driver.find_element(By.TAG_NAME, 'body').text
            return {'url': url, 'title': title, 'content': content}
        except NoSuchElementException as e:
            print(f"Error extracting data from {url}: {e}")
            return {'url': url, 'title': '', 'content': ''}
        
    def update_domain_counter(self, domain, count):
        domain = (domain)
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
            if not self.can_fetch_url(url):
                print(f"Skipping {url} because it is disallowed by robots.txt.")
                continue
            if not check_for_duplicate(self.conn, 'cookies', url):
                try:
                    self.navigate_to(url)
                    self.accept_cookies()
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

    def export_cookies(self, csv_file_path):
        export_cookies_to_csv(DATABASE_PATH, csv_file_path)

    def purge_database(self):
        try:
            # Try executing a simple query to check if the connection is open
            if self.conn is None:
                self.conn = create_connection(DATABASE_PATH)
            else:
                self.conn.execute('SELECT 1')

            with self.conn:
                cur = self.conn.cursor()
                cur.execute("DELETE FROM cookies")
                cur.execute("DELETE FROM research_data")
            print("Database purged successfully.")
        except (sqlite3.Error, sqlite3.ProgrammingError) as e:
            # If there's an error (like a closed connection), reconnect and retry
            self.conn = create_connection(DATABASE_PATH)
            with self.conn:
                cur = self.conn.cursor()
                cur.execute("DELETE FROM cookies")
                cur.execute("DELETE FROM research_data")
            print("Database purged successfully.")
        except Exception as e:
            print(f"Error purging database: {e}")

    def display_domain_counts(self):
        # Sort the domain_counter dictionary by count in descending order
        sorted_domains = sorted(self.domain_counter.items(), key=lambda x: x[1], reverse=True)
        
        print("Crawl Complete.")
        for domain, count in sorted_domains:
            print(f"Domain: {domain}, Cookie Count: {count}")

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

        self.display_domain_counts()    # Display domain counts

        self.conn.close()
        self.quit_browser()

        if export_to_csv:
            self.export_cookies('cookies_export.csv')


def display_help():
    print("Crawler Help:")
    print("  - 'scrape': Enter scrape mode to crawl specified URLs for cookies.")
    print("  - 'research': Enter research mode to perform search queries and extract data from the results.")
    print("  - 'proxy support': Configure and test proxy settings.")
    print("  - 'q', 'quit', or 'exit': Quit the crawler.")
    print("  - '-help': Display this help information.")
    print("  - 'purge': Purge the database of all data.")


def prepend_http(urls):
    return [url if '://' in url else 'http://' + url for url in urls]


if __name__ == "__main__":
    init_db()
    crawler = Crawler(headless=True)
    proxy_manager = None  # Initialize proxy manager

    while True:
        command = input("Enter command ('-help' for options): ").strip().lower()

        if command == '-help':
            display_help()
        elif command in ['q', 'quit', 'exit']:
            print("Quitting the crawler.")
            break
        elif command == 'scrape':
            urls = input("Enter up to 3 URLs (for optimal results) to scrape, separated by commas, or type 'back' to return: ").strip()
            if urls.lower() == 'back':
                continue  # Go back to the main command loop
            urls = urls.split(',')
            urls = prepend_http(urls)  # Prepend 'http://' if missing
            crawler.run(urls, mode='scrape')
        elif command == 'research':
            queries = input("Enter search queries, separated by commas, or type 'back' to return: ").strip()
            if queries.lower() == 'back':
                continue  # Go back to the main command loop
            queries = queries.split(',')
            crawler.run(queries, mode='research')
        elif command == 'purge':
            confirmation = input("Are you sure you want to purge the database? (yes/no): ").strip().lower()
            if confirmation == 'yes':
                crawler.purge_database()
            else:
                print("Purge cancelled.")
        elif command == 'proxy support':
            if proxy_manager is None:
                proxy_manager = ProxyManager([])  # Initialize with an empty proxy list
            use_proxy = input("Do you want to use a proxy? (yes/no): ").strip().lower()
            if use_proxy == 'yes':
                while True:
                    proxy_input = input("Enter 'file' to use a 'proxies.txt' file or directly enter proxies, separated by commas, or 'back' to return: ").strip()
                    if proxy_input.lower() == 'back':
                        break
                    elif proxy_input.lower() == 'file':
                        try:
                            with open('proxies.txt', 'r') as file:
                                proxies = file.read().splitlines()
                                proxy_manager.proxy_list = proxies
                        except IOError:
                            print("Error: proxies.txt file not found.")
                    else:
                        proxies = proxy_input.split(',')
                        proxy_manager.proxy_list = proxies

                # Test the proxies
                for proxy in proxy_manager.proxy_list:
                    if proxy_manager.test_proxy(proxy):
                        print(f"Proxy {proxy} is working.")
                    else:
                        print(f"Proxy {proxy} is not responsive.")
            else:
                proxy_manager = None  # Reset the proxy manager
        else:
            print("Invalid command. Enter '-help' for options.")

    print("Crawler has been stopped.")

