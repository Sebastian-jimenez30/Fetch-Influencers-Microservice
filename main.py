import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.databases.redis import start_listener
from app.routes.routes import router

app = FastAPI(title="TikTok Scraper API", version="1.0")

app.include_router(router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(asyncio.to_thread(start_listener))
