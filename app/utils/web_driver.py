import logging
import os
import pickle
import random
import re
import subprocess
import time
import traceback

import undetected_chromedriver as uc
from dotenv import load_dotenv
from fake_useragent import UserAgent
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
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

    @staticmethod
    def _find_chrome_binary() -> str | None:
        configured_binary = os.getenv("CHROME_BIN")
        if configured_binary:
            return configured_binary

        if os.name == "nt":
            candidates = [
                os.path.join(
                    os.getenv("PROGRAMFILES", ""),
                    "Google",
                    "Chrome",
                    "Application",
                    "chrome.exe",
                ),
                os.path.join(
                    os.getenv("PROGRAMFILES(X86)", ""),
                    "Google",
                    "Chrome",
                    "Application",
                    "chrome.exe",
                ),
                os.path.join(
                    os.getenv("LOCALAPPDATA", ""),
                    "Google",
                    "Chrome",
                    "Application",
                    "chrome.exe",
                ),
            ]
        else:
            candidates = [
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/chromium",
                "/usr/bin/chromium-browser",
            ]

        return next((path for path in candidates if os.path.isfile(path)), None)

    @staticmethod
    def _detect_chrome_major(chrome_binary: str | None) -> int | None:
        configured_version = os.getenv("CHROME_VERSION_MAIN")
        if configured_version:
            return int(configured_version)

        if os.name == "nt":
            try:
                import winreg

                registry_locations = [
                    (winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon"),
                    (winreg.HKEY_LOCAL_MACHINE, r"Software\Google\Chrome\BLBeacon"),
                    (
                        winreg.HKEY_LOCAL_MACHINE,
                        r"Software\WOW6432Node\Google\Chrome\BLBeacon",
                    ),
                ]
                for registry_root, registry_path in registry_locations:
                    try:
                        with winreg.OpenKey(registry_root, registry_path) as key:
                            version, _ = winreg.QueryValueEx(key, "version")
                            return int(version.split(".", maxsplit=1)[0])
                    except OSError:
                        continue
            except (ImportError, ValueError):
                pass

        if chrome_binary:
            try:
                result = subprocess.run(
                    [chrome_binary, "--version"],
                    capture_output=True,
                    check=True,
                    text=True,
                    timeout=10,
                )
                match = re.search(r"(\d+)\.", result.stdout)
                if match:
                    return int(match.group(1))
            except (OSError, subprocess.SubprocessError, ValueError):
                pass

        return None

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
            user_data_dir = os.getenv("CHROME_USER_DATA_DIR")
            if user_data_dir:
                user_data_dir = os.path.abspath(user_data_dir)
                os.makedirs(user_data_dir, exist_ok=True)
            else:
                options.add_argument("--incognito")
            options.add_argument("--disable-blink-features=AutomationControlled")

            ua = UserAgent()
            user_agent = ua.random
            options.add_argument(f"user-agent={user_agent}")

            chrome_binary = cls._find_chrome_binary()
            chrome_major = cls._detect_chrome_major(chrome_binary)
            if chrome_major:
                logger.info("Using Chrome/Chromium major version %s.", chrome_major)
            cls._driver = uc.Chrome(
                options=options,
                browser_executable_path=chrome_binary or None,
                version_main=chrome_major,
                user_data_dir=user_data_dir or None,
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
                login_mode = os.getenv("TIKTOK_LOGIN_MODE", "manual").lower()
                if login_mode == "manual":
                    cls.login_tiktok_manually()
                else:
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

        if not username or not password:
            raise RuntimeError(
                "TIKTOK_USERNAME and TIKTOK_PASSWORD must be configured."
            )

        cls._driver.get("https://www.tiktok.com/login/phone-or-email/email")
        time.sleep(random.uniform(5, 8))

        try:
            wait = WebDriverWait(cls._driver, 30)

            username_input = wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, 'input[name="username"]')
                )
            )
            password_input = wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, 'input[type="password"]')
                )
            )

            username_input.clear()
            username_input.send_keys(username)
            time.sleep(random.uniform(1, 2))
            password_input.clear()
            password_input.send_keys(password)
            time.sleep(random.uniform(1, 2))

            login_button = wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, 'button[data-e2e="login-button"]')
                )
            )
            login_button.click()

            manual_login_timeout = int(
                os.getenv("TIKTOK_MANUAL_LOGIN_TIMEOUT", "120")
            )
            logger.info(
                "Waiting up to %s seconds for login or manual verification.",
                manual_login_timeout,
            )
            WebDriverWait(cls._driver, manual_login_timeout).until(
                lambda driver: "/login" not in driver.current_url
            )

            with open("cookies_tiktok.pkl", "wb") as cookie_file:
                pickle.dump(cls._driver.get_cookies(), cookie_file)
            logger.info("Session and cookies saved successfully.")

        except Exception as error:
            logger.error("TikTok authentication did not complete.")
            traceback.print_exc()
            raise RuntimeError(
                "TikTok login failed. Complete any verification in the Chrome "
                "window before the configured timeout."
            ) from error

    @classmethod
    def login_tiktok_manually(cls):
        """Wait for the user to complete TikTok login in the visible browser."""
        if os.getenv("CHROME_HEADLESS", "false").lower() == "true":
            raise RuntimeError("Manual TikTok login requires CHROME_HEADLESS=false.")

        cls._driver.get("https://www.tiktok.com/login")
        print(
            "\nComplete the TikTok login manually in Chrome. "
            "Use QR, Google, email, or any method accepted by TikTok."
        )
        input("After TikTok shows you as logged in, press Enter here...")

        if not cls.is_logged_in():
            raise RuntimeError(
                "TikTok still shows the session as logged out. "
                "Complete the login before pressing Enter."
            )

        with open("cookies_tiktok.pkl", "wb") as cookie_file:
            pickle.dump(cls._driver.get_cookies(), cookie_file)
        logger.info("Manual TikTok session saved successfully.")

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
