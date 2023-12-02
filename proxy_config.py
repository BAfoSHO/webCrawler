import random
import time
import os
import subprocess
from selenium import webdriver


class ProxyManager:
    def __init__(self, proxy_list):
        self.proxy_list = proxy_list
        self.current_proxy = None

    def get_proxy(self):
        if not self.proxy_list:
            return None
        self.current_proxy = random.choice(self.proxy_list)
        return self.current_proxy

    def rotate_proxy(self):
        if not self.proxy_list:
            return None
        new_proxy = random.choice(self.proxy_list)
        while new_proxy == self.current_proxy:
            new_proxy = random.choice(self.proxy_list)
        self.current_proxy = new_proxy
        return self.current_proxy

    def format_proxy_for_selenium(self, proxy):
        if proxy:
            return {
                "http": f"http://{proxy}",
                "https": f"https://{proxy}",
                "ftp": f"ftp://{proxy}"
            }
        return None

    # Call this method before using a proxy to ensure it's alive
    def test_proxy(proxy):
        try:
            host, port = proxy.split(':')
            # Adjust the number of pings and timeout as needed
            ping_command = f"ping -c 3 -W 2 -q -p {port} {host}"  # Ping 3 times with a 2-second timeout
            response = subprocess.run(ping_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Check the return code; 0 indicates successful ping
            if response.returncode == 0:
                return True
        except Exception:
            pass  # Any exception means the proxy is not working or not responsive

        return False

proxy_manager = ProxyManager(['proxy1:port', 'proxy2:port', 'proxy3:port'])
proxy = proxy_manager.get_proxy()
formatted_proxy = proxy_manager.format_proxy_for_selenium(proxy)

# Set this proxy in Selenium WebDriver
options = webdriver.ChromeOptions()
if formatted_proxy:
    options.add_argument('--proxy-server=%s' % formatted_proxy)

