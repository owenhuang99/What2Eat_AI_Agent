from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import sys
from datetime import datetime
import logging
from pathlib import Path
import platform

class BrowserTool:
    """
    A tool for browsing the web using Selenium with cloud deployment support.
    """
    def __init__(self):
        self.setup_logging()
        self.driver = None
        self.is_cloud_environment = self._detect_cloud_environment()

    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = Path(__file__).parent.parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / 'browser_tool.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.__class__.__name__)

    def _detect_cloud_environment(self):
        """Detect if running in a cloud environment"""
        cloud_indicators = [
            os.getenv('STREAMLIT_CLOUD'),
            os.getenv('HEROKU'),
            os.getenv('RAILWAY_ENVIRONMENT'),
            os.getenv('VERCEL'),
            '/app' in os.getcwd(),  # Common cloud app directory
            not os.path.exists('/usr/bin/google-chrome') and not os.path.exists('/Applications/Google Chrome.app'),
            'linux' in platform.system().lower() and not os.environ.get('DISPLAY')
        ]
        is_cloud = any(cloud_indicators)
        self.logger.info(f"Cloud environment detected: {is_cloud}")
        return is_cloud

    def setup_browser(self):
        """Setup Chrome browser with necessary options for both local and cloud"""
        try:
            chrome_options = Options()

            # Always run in headless mode for consistency between local and cloud
            self.logger.info(f"Setting up browser in headless mode (Environment: {'Cloud' if self.is_cloud_environment else 'Local'})")
            chrome_options.add_argument('--headless=new')  # Always headless for consistency
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-software-rasterizer')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            chrome_options.add_argument('--disable-features=TranslateUI')
            chrome_options.add_argument('--disable-ipc-flooding-protection')
            chrome_options.add_argument('--memory-pressure-off')
            chrome_options.add_argument('--max_old_space_size=4096')

            # Set window size for headless mode
            chrome_options.add_argument('--window-size=1920,1080')

            # Try to set Chrome binary location for cloud environments
            if self.is_cloud_environment:
                possible_paths = [
                    '/usr/bin/chromium',        # Move this first for Streamlit Cloud
                    '/usr/bin/chromium-browser',
                    '/opt/chrome/chrome',
                    '/usr/bin/google-chrome'
                ]

                for path in possible_paths:
                    if os.path.exists(path):
                        chrome_options.binary_location = path
                        self.logger.info(f"Using Chrome binary at: {path}")
                        break

            # Anti-detection options (work for both local and cloud)
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # User agent
            user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            if not self.is_cloud_environment and platform.system() == 'Darwin':
                user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            elif not self.is_cloud_environment and platform.system() == 'Windows':
                user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'

            chrome_options.add_argument(f'--user-agent={user_agent}')

            # Additional options
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-infobars')
            chrome_options.add_argument('--disable-notifications')
            chrome_options.add_argument('--disable-popup-blocking')
            chrome_options.add_argument('--disable-translate')
            chrome_options.add_argument('--disable-logging')
            chrome_options.add_argument('--disable-background-networking')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-client-side-phishing-detection')
            chrome_options.add_argument('--disable-default-apps')
            chrome_options.add_argument('--disable-hang-monitor')
            chrome_options.add_argument('--disable-prompt-on-repost')
            chrome_options.add_argument('--disable-sync')
            chrome_options.add_argument('--disable-web-resources')
            chrome_options.add_argument('--metrics-recording-only')
            chrome_options.add_argument('--no-first-run')
            chrome_options.add_argument('--safebrowsing-disable-auto-update')
            chrome_options.add_argument('--use-mock-keychain')

            # Set up the service
            if self.is_cloud_environment:
                # In cloud environments, use system chromedriver
                service = Service()  # Will use system PATH
                self.logger.info("Using system chromedriver for cloud environment")
            else:
                try:
                    # Only use ChromeDriverManager locally
                    service = Service(ChromeDriverManager().install())
                    self.logger.info("Using ChromeDriverManager for local environment")
                except Exception as e:
                    self.logger.warning(f"ChromeDriverManager failed: {e}")
                    service = Service()

            # Create the driver
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            # Execute CDP commands to prevent detection
            try:
                self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                    "userAgent": user_agent
                })
                self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                    'source': '''
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        })
                    '''
                })
            except Exception as e:
                self.logger.warning(f"CDP commands failed (expected in some environments): {e}")

            # Set page load timeout
            self.driver.set_page_load_timeout(30)

            self.logger.info("Browser setup completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error setting up browser: {str(e)}", exc_info=True)
            return False

    def navigate_to(self, url, wait_time=3):
        """Navigate to a URL with error handling"""
        try:
            if not self.driver:
                if not self.setup_browser():
                    return False

            self.logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            time.sleep(wait_time)
            return True

        except Exception as e:
            self.logger.error(f"Error navigating to {url}: {str(e)}")
            return False

    def wait_for_element(self, by, value, timeout=10):
        """Wait for an element to be present"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except Exception as e:
            self.logger.error(f"Element not found: {by}={value}, Error: {str(e)}")
            return None

    def get_page_source(self):
        """Get the current page source"""
        try:
            return self.driver.page_source if self.driver else None
        except Exception as e:
            self.logger.error(f"Error getting page source: {str(e)}")
            return None

    def get_driver(self):
        """Get the browser driver"""
        if not self.driver:
            self.setup_browser()
        return self.driver

    def close(self):
        """Close the browser"""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                self.logger.info("Browser closed successfully")
            except Exception as e:
                self.logger.error(f"Error closing browser: {str(e)}", exc_info=True)

    def __enter__(self):
        """Context manager entry"""
        self.setup_browser()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
