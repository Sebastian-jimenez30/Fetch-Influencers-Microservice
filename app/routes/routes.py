from fastapi import APIRouter

from app.use_cases.retrieve_tiktok_influencers import retrive_tiktok_influencers

router = APIRouter()

@router.get("/")
def root():
    return {"message": "API is running!"}

@router.get("/api/v1/influencers")
def get_influencers():
    return retrive_tiktok_influencers()
