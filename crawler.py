from selenium import webdriver
from selenium.common.exceptions import WebDriverException
import time
#from database import insert_cookie_data


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
            self.driver = webdriver.Chrome(self.driver_path, options=options)
        except WebDriverException as e:
            print(f"Error starting the browser: {e}")
            raise

    def close_browser(self):
        if self.driver:
            self.driver.close()
    
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
            return self.driver.getCookies()
        except WebDriverException as e:
            print(f"Error getting cookies: {e}")
            return []
        
    def run(self, url):
        self.start_browser()
        for url in urls:
            try:
                self.navigate_to(url)
                cookies = self.get_cookies()
                for cookie in cookies:
                    insert_cookie_data(url, cookie)
                print(f"Successfully stored cookies from the url(s) in the database.")
            except Exception as e:
                print(f"Error running the crawler: {e}")

        self.close_browser()

if __name__ == "__main__":
    urls = ["https://www.google.com", "https://www.facebook.com"]
    crawler = Crawler("chromedriver.exe", headless=True)
    crawler.run(urls)