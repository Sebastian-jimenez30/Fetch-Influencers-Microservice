import logging

from app.schemas.influencer import Influencer
from app.services.scrapers.profile_scraper import get_profile_info
from app.services.scrapers.video_scraper import get_tiktok_video_data
from app.utils.stats import calculate_averages

logger = logging.getLogger(__name__)

def get_influencer_information(username, city:str = "") -> Influencer:
    """
    Fetches influencer information from TikTok based on the provided username.

    Args:
        username (str): TikTok username of the influencer.
        city (str): Name of the city to scrape data for.

    Returns:
        Influencer: Influencer object with engagement metrics.
    """

    profile_url = f"https://www.tiktok.com/@{username}"
    try:
        profile_data = get_profile_info(profile_url)
    except Exception as e:
        logger.warning(f"Error getting profile data: {e}")
        return None

    if not profile_data:
        return None

    metrics = {"likes": 0, "comments": 0, "shares": 0, "saves": 0}
    total_videos = len(profile_data["video_ids"])
    featured_videos = []

    for video_id in profile_data["video_ids"]:
        video_url = f"https://www.tiktok.com/@{username}/video/{video_id}"
        try:
            video_data = get_tiktok_video_data(video_url)
        except Exception as e:
            logger.warning(f"Error getting video data: {e}")
            continue

        if not video_data:
            continue

        for metric in metrics:
            metrics[metric] += video_data[metric]

        if len(featured_videos) < 3:
            featured_videos.append(video_id)

    average_metrics = calculate_averages(metrics, total_videos)

    influencer = Influencer(
        username=username,
        profile_name=profile_data["profile_name"],
        profile_picture=profile_data["profile_picture"],
        profile_url=profile_url,
        average_views=profile_data["average_views"],
        average_likes=average_metrics["average_likes"],
        average_comments=average_metrics["average_comments"],
        average_shares=average_metrics["average_shares"],
        average_saves=average_metrics["average_saves"],
        followers=profile_data["followers"],
        city=city,
        featured_videos=featured_videos,
    )

    return influencer
