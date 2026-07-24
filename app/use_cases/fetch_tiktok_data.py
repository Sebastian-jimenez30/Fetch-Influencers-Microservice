import logging
import random

from app.services.scrapers.hashtag_scraper import get_usernames
from app.utils.get_influencer_information import get_influencer_information

logger = logging.getLogger(__name__)


def fetch_influencers_by_tag(city) -> None:
    """
    Scrapes TikTok data for influencers in a given city

    Args:
        city (str): Name of city to scrape data for

    Returns:
        list[Influencer]: List of influencer data with engagement metrics
    """

    tag_url = f"https://www.tiktok.com/search/video?q={city}"
    try:
        temp_usernames = list(get_usernames(tag_url))
        sample_size = min(5, len(temp_usernames))
        usernames = random.sample(temp_usernames, sample_size)

    except Exception as e:
        logger.error(f"Error getting usernames: {e}")
        return None

    if not usernames:
        return None

    influencers = []
    for username in usernames:
        logger.info("Retrieving profile information for @%s.", username)
        influencer = get_influencer_information(username, city)
        if influencer is None:
            logger.warning("Skipping @%s because its profile could not be read.", username)
            continue
        if influencer.is_significant():
            influencers.append(influencer)
            logger.info(f"Fetched influencer: {username}")
        else:
            logger.warning(f"Influencer {username} does not meet significance criteria.")
            continue
    return influencers
