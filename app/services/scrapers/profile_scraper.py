"""
TikTok Profile Scraper

This script scrapes TikTok to extract the first 10 video IDs from a user's profile.
It uses Selenium to automate the browser and retrieve video links.
"""

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


def get_profile_info(profile_url: str) -> dict | None:
    """
    Scrapes basic profile information and engagement metrics from a TikTok profile.

    Args:
        profile_url (str): The TikTok profile URL.

    Returns:
        dict: Dictionary containing profile metrics including:
            - profile_name: User's display name
            - profile_picture: User's profile image URL
            - followers: Number of followers
            - average_views: Average views across last 10 videos
            - video_ids: List of first 10 video IDs
    """
    driver = WebDriverManager.get_driver()

    wait_time = random.uniform(15, 20)
    wait = WebDriverWait(driver, wait_time)
    profile_data = {}

    try:
        driver.get(profile_url)
        time.sleep(random.uniform(2, 5))

        name_element = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'h1[data-e2e="user-title"]')
            )
        )
        profile_data["profile_name"] = name_element.text

        image_element = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '[data-e2e="user-avatar"] img')
            )
        )
        profile_data["profile_picture"] = image_element.get_attribute("src")

        followers_element = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'strong[data-e2e="followers-count"]')
            )
        )
        followers_text = followers_element.text
        profile_data["followers"] = format_metric(followers_text)

        view_elements = wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, 'strong[data-e2e="video-views"]')
            )
        )
        views = [format_metric(element.text) for element in view_elements[:10]]
        profile_data["average_views"] = sum(views) / len(views) if views else 0

        video_elements = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[href*="/video/"]'))
        )
        video_ids = []
        for video in video_elements:
            video_id = video.get_attribute("href").split("/video/")[-1].split("?")[0]
            if video_id not in video_ids:
                video_ids.append(video_id)
            if len(video_ids) == 10:
                break
        profile_data["video_ids"] = video_ids

    except (TimeoutException, NoSuchElementException) as e:
        logger.error(f"Error retrieving profile info: {e}")
        return None

    except Exception as e:
        logger.error(f"An unexpected error occurred while scraping profile: {e}")
        return None

    return profile_data
