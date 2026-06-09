import time
from fastapi import HTTPException

RATE_LIMIT_STORE = {}

MAX_REQUESTS = 2
WINDOW_SECONDS = 60


def check_rate_limit(ip: str):
    now = time.time()

    if ip not in RATE_LIMIT_STORE:
        RATE_LIMIT_STORE[ip] = []

    RATE_LIMIT_STORE[ip] = [
        ts for ts in RATE_LIMIT_STORE[ip]
        if now - ts < WINDOW_SECONDS
    ]

    if len(RATE_LIMIT_STORE[ip]) >= MAX_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail="Too many report requests. Try again later."
        )

    RATE_LIMIT_STORE[ip].append(now)
