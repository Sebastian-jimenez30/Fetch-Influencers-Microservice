import logging
import os

import redis
from dotenv import load_dotenv

from app.databases.postgres import upsert_influencer
from app.schemas.influencer import Influencer
from app.use_cases.fetch_tiktok_data import fetch_influencers_by_tag
from app.use_cases.update_tiktok_data import update_tiktok_influencer

load_dotenv()

logger = logging.getLogger(__name__)


r = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=int(os.getenv("REDIS_DB", 0)),
    decode_responses=True,
)

def add_influencer(influencer: Influencer) -> None:
    """Save an influencer in a queue."""
    if influencer is None:
        logger.warning("Skipping an empty influencer result.")
        return
    influencer_json = influencer.json()
    r.rpush("influencers", influencer_json)
    logger.info(f"Added influencer {influencer.username} to the queue.")


def get_influencer() -> Influencer:
    """Obtain the next influencer in the queue."""
    influencer_json = r.lpop("influencers")
    if influencer_json:
        return Influencer.parse_raw(influencer_json)
    return None


def start_listener():
    """Start a listener for Redis pub/sub messages."""
    pubsub = r.pubsub()
    pubsub.subscribe("tasks")

    logger.info("Listening for messages on 'tasks'...")

    for message in pubsub.listen():
        if message["type"] == "message":
            params = message["data"].split(":")
            action = params[0]
            if action == "update_influencer":
                try:
                    username = params[1]
                    influencer = update_tiktok_influencer(username)
                    if influencer is not None:
                        upsert_influencer(influencer)
                        add_influencer(influencer)
                    logger.info(f"Updated influencer: {username}")
                except Exception as e:
                    logger.error(f"Failed to update {username}: {e}")
            elif action == "fetch_influencers":
                try:
                    city = params[1]
                    influencers = fetch_influencers_by_tag(city) or []
                    for influencer in influencers:
                        upsert_influencer(influencer)
                        add_influencer(influencer)
                    logger.info("Fetched and added influencers to the queue.")
                except Exception as e:
                    logger.error(f"Failed to fetch influencers: {e}")


