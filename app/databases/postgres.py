import os

from dotenv import load_dotenv
from psycopg import connect
from psycopg.types.json import Json

from app.schemas.influencer import Influencer

load_dotenv()


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is required to persist influencers in PostgreSQL."
        )
    return database_url


def upsert_influencer(influencer: Influencer) -> None:
    """Insert or update an influencer without changing its moderation status."""
    with connect(get_database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO influencers (
                    username,
                    profile_name,
                    profile_picture,
                    profile_url,
                    average_likes,
                    average_comments,
                    average_shares,
                    average_saves,
                    average_views,
                    followers,
                    city,
                    featured_videos
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (username) DO UPDATE SET
                    profile_name = EXCLUDED.profile_name,
                    profile_picture = EXCLUDED.profile_picture,
                    profile_url = EXCLUDED.profile_url,
                    average_likes = EXCLUDED.average_likes,
                    average_comments = EXCLUDED.average_comments,
                    average_shares = EXCLUDED.average_shares,
                    average_saves = EXCLUDED.average_saves,
                    average_views = EXCLUDED.average_views,
                    followers = EXCLUDED.followers,
                    city = CASE
                        WHEN EXCLUDED.city = '' THEN influencers.city
                        ELSE EXCLUDED.city
                    END,
                    featured_videos = EXCLUDED.featured_videos,
                    updated_at = NOW()
                """,
                (
                    influencer.username,
                    influencer.profile_name,
                    influencer.profile_picture,
                    influencer.profile_url,
                    influencer.average_likes,
                    influencer.average_comments,
                    influencer.average_shares,
                    influencer.average_saves,
                    influencer.average_views,
                    influencer.followers,
                    influencer.city,
                    Json(influencer.featured_videos),
                ),
            )
