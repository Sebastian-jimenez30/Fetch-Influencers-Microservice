import logging
import os
import pickle
import random
import time
import traceback

import undetected_chromedriver as uc
from dotenv import load_dotenv
from fake_useragent import UserAgent
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Configurar logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class WebDriverManager:
    """Singleton class to manage the WebDriver instance with stealth capabilities."""

    _driver = None

    @classmethod
    def get_driver(cls):
        """Return the WebDriver instance. If it doesn't exist, create it."""
        if cls._driver is None:
            options = uc.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            if os.getenv("CHROME_HEADLESS", "false").lower() == "true":
                options.add_argument("--headless=new")
            options.add_argument("--lang=es-CO")
            options.add_argument("--incognito")
            options.add_argument("--disable-blink-features=AutomationControlled")

            ua = UserAgent()
            user_agent = ua.random
            options.add_argument(f"user-agent={user_agent}")

            chrome_binary = os.getenv("CHROME_BIN")
            cls._driver = uc.Chrome(
                options=options,
                browser_executable_path=chrome_binary or None,
                use_subprocess=True,
            )

            cls._driver.execute_script(
                """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'languages', {get: () => ['es-CO', 'es']});
                Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
                Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
                Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
                Object.defineProperty(navigator, 'maxTouchPoints', {get: () => 1});
                Object.defineProperty(navigator, 'userActivation', {get: () => true});
                Object.defineProperty(window, 'chrome', {runtime: {}});
                Object.defineProperty(document, 'hidden', {get: () => false});
                Object.defineProperty(document, 'visibilityState', {get: () => 'visible'})
            """
            )

            cls._driver.execute_script(
                """
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });

                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                    Promise.resolve({ state: 'granted' }) :
                    originalQuery(parameters)
                );
            """
            )

            cls.load_cookies()

            if not cls.is_logged_in():
                load_dotenv()
                username = os.getenv("TIKTOK_USERNAME")
                password = os.getenv("TIKTOK_PASSWORD")

                cls.login_tiktok(username, password)

        return cls._driver

    @classmethod
    def close_driver(cls):
        """Close and cleanup the WebDriver instance."""
        try:
            if cls._driver is not None:
                cls._driver.quit()
                cls._driver = None
                logger.info("WebDriver closed successfully")
        except Exception as e:
            logger.error(f"Error closing WebDriver: {str(e)}")
            # Ensure driver is set to None even if quit fails
            cls._driver = None

    @classmethod
    def is_logged_in(cls):
        """Check if the user is already logged in."""
        cls._driver.get("https://www.tiktok.com")
        time.sleep(random.uniform(3, 6))

        try:
            cls._driver.find_element(By.ID, "header-login-button")
            logger.info("Login not done.")
            return False
        except NoSuchElementException:
            logger.info("Login already done.")
            return True

    @classmethod
    def login_tiktok(cls, username, password):
        """Login to TikTok and save session cookies."""
        logger.info("Attempting to log in to TikTok...")

        cls._driver.get("https://www.tiktok.com/login/phone-or-email/email")
        time.sleep(random.uniform(5, 8))

        try:
            wait = WebDriverWait(cls._driver, 10)

            username_input = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "input.tiktok-11to27l-InputContainer")
                )
            )
            password_input = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "input[type='password']")
                )
            )

            username_input.send_keys(username)
            time.sleep(random.uniform(1, 2))
            password_input.send_keys(password)
            time.sleep(random.uniform(1, 2))
            password_input.send_keys(Keys.RETURN)

            time.sleep(random.uniform(8, 12))

            pickle.dump(cls._driver.get_cookies(), open("cookies_tiktok.pkl", "wb"))
            logger.info("Session and cookies saved successfully.")

        except Exception:
            logger.error("Error trying to authenticate:")
            traceback.print_exc()

    @classmethod
    def load_cookies(cls):
        """Load the session cookies from a file."""
        try:
            cls._driver.get("https://www.tiktok.com")
            time.sleep(random.uniform(3, 5))

            cookies = pickle.load(open("cookies_tiktok.pkl", "rb"))

            for cookie in cookies:
                if "tiktok.com" in cookie["domain"]:
                    cls._driver.add_cookie(cookie)

            logger.info("Cookies loaded successfully.")
        except FileNotFoundError:
            logger.warning("No cookies found.")
        except Exception as e:
            logger.error(f"Error loading cookies: {e}")
