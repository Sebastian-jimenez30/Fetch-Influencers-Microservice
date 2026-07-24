import argparse
import logging

from app.databases.postgres import upsert_influencer
from app.use_cases.fetch_tiktok_data import fetch_influencers_by_tag
from app.utils.get_influencer_information import get_influencer_information

logger = logging.getLogger(__name__)


def scrape_city(city: str) -> int:
    influencers = fetch_influencers_by_tag(city) or []
    for influencer in influencers:
        upsert_influencer(influencer)
        logger.info("Stored @%s in PostgreSQL.", influencer.username)
    return len(influencers)


def scrape_username(username: str, city: str) -> int:
    normalized_username = username.removeprefix("@")
    influencer = get_influencer_information(normalized_username, city)
    if influencer is None:
        return 0
    upsert_influencer(influencer)
    logger.info("Stored @%s in PostgreSQL.", influencer.username)
    return 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scrape TikTok locally and persist results in PostgreSQL."
    )
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--city", help="City/search term used to discover influencers.")
    target.add_argument("--username", help="TikTok username to insert or update.")
    parser.add_argument(
        "--assign-city",
        default="",
        help="City assigned when scraping a specific username.",
    )
    args = parser.parse_args()

    if args.city:
        stored_count = scrape_city(args.city)
    else:
        stored_count = scrape_username(args.username, args.assign_city)

    print(f"Stored influencers: {stored_count}")


if __name__ == "__main__":
    main()
