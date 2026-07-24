import logging
import random
import time

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.utils.formatters import format_metric
from app.utils.web_driver import WebDriverManager

logger = logging.getLogger(__name__)


def get_tiktok_video_data(video_url: str) -> dict | None:
    """
    Scrapes TikTok to extract likes, comments, shares and saves from a video.

    Args:
        video_url (str): The TikTok video URL to scrape.

    Returns:
        dict: A dictionary containing the extracted data including:
            - likes: Number of likes on the video
            - comments: Number of comments on the video
            - shares: Number of shares of the video
            - saves: Number of saves of the video
    """
    driver = WebDriverManager.get_driver()

    wait_time = random.uniform(8, 12)
    wait = WebDriverWait(driver, wait_time)
    data = {}

    try:
        driver.get(video_url)
        time.sleep(random.uniform(2, 5))

        likes_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-e2e="like-count"]'))
        )
        data["likes"] = format_metric(likes_element.text)

        comments_element = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '[data-e2e="comment-count"]')
            )
        )
        data["comments"] = format_metric(comments_element.text)

        shares_element = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '[data-e2e="share-count"]')
            )
        )
        data["shares"] = format_metric(shares_element.text)

        data["saves"] = 0
        for selector in (
            '[data-e2e="collect-count"]',
            '[data-e2e="save-count"]',
            '[data-e2e="undefined-count"]',
        ):
            saves_elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if saves_elements:
                data["saves"] = format_metric(saves_elements[0].text)
                break

    except (TimeoutException, NoSuchElementException) as e:
        logger.error(f"Error retrieving video data: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return None

    return data
