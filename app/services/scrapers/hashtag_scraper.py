import logging
import random
import re
import time

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.utils.web_driver import WebDriverManager

logger = logging.getLogger(__name__)


def get_usernames(url_hashtag: str) -> set:
    """
    Scrapes TikTok to extract usernames from videos under a specific hashtag.
    Args:
        url_hashtag (str): The TikTok hashtag URL to scrape.
    Returns:
        set: A set of unique usernames found in the videos under the hashtag.
    """

    driver = WebDriverManager.get_driver()
    usernames = set()

    try:
        driver.get(url_hashtag)
        wait = WebDriverWait(driver, random.uniform(8, 12))

        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '[data-e2e="search_video-item"]')
            )
        )

        for _ in range(10):
            driver.execute_script("window.scrollBy(0, 2000);")
            time.sleep(random.uniform(1.5, 3.5))

        videos = driver.find_elements(By.CSS_SELECTOR, '[data-e2e="search_video-item"]')
        for video in videos:
            try:
                link_element = video.find_element(By.TAG_NAME, "a")
                video_url = link_element.get_attribute("href")

                match = re.search(r"@([^/]+)/video", video_url)
                username = match.group(1) if match else ""
                usernames.add(username)
            except NoSuchElementException:
                continue

    except (TimeoutException, NoSuchElementException) as e:
        logging.error(f"Error in hashtag module: {e}")
        return None

    return usernames
