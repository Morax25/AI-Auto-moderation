import hashlib
import asyncio

reported_posts: set = set()
content_cache: dict = {}

def is_already_reported(post_id: str) -> bool:
    return post_id in reported_posts

def mark_reported(post_id: str):
    reported_posts.add(post_id)

def unmark_reported(post_id: str):
    reported_posts.discard(post_id)

def get_cached_result(content: str) -> dict | None:
    content_hash = hashlib.sha256(content.strip().lower().encode()).hexdigest()
    return content_cache.get(content_hash), content_hash

def set_cached_result(content_hash: str, result: dict):
    content_cache[content_hash] = result

async def cleanup_cache(ttl: int):
    while True:
        await asyncio.sleep(ttl)
        reported_posts.clear()
        content_cache.clear()
        print("[CACHE] Cleared")
