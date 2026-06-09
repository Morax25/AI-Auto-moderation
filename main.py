import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.moderation import router
from app.cache import cleanup_cache
from app.config import CACHE_TTL

# 👇 add this
from app.rabbitmq.bootstrap import setup_rabbitmq

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.on_event("startup")
def startup():
    setup_rabbitmq()

    asyncio.create_task(cleanup_cache(CACHE_TTL))

    print("[APP] Ready")
