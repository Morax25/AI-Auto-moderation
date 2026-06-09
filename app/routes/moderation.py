from fastapi import APIRouter, HTTPException, Request
from app.models import ReportPostRequest, ModerationResponse
from app.cache import (
    is_already_reported,
    mark_reported,
    unmark_reported,
    get_cached_result,
    set_cached_result
)
from app.gemini import analyze_content, enforce_thresholds
from app.rabbitmq.publisher import publish_moderation_job
import time
import logging

router = APIRouter()

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
            detail="Too many report requests. Please try again later."
        )

    RATE_LIMIT_STORE[ip].append(now)


def publish_event(payload: ReportPostRequest, action: str, ip: str, result: dict = None):
    publish_moderation_job({
        "reporter": payload.reporter,
        "postId": payload.postId,
        "content": payload.content,
        "action": action,
        "category": result.get("category") if result else "unknown",
        "confidence": result.get("confidence") if result else None,
        "severity": result.get("severity") if result else None,
        "reasoning": result.get("reasoning") if result else "Gemini API unavailable — flagged for manual review.",
        "ip": ip,
        "timestamp": time.time()
    })


@router.post("/report-post", response_model=ModerationResponse)
async def report_post(payload: ReportPostRequest, request: Request):

    ip = request.headers.get("x-forwarded-for")
    ip = ip.split(",")[0].strip() if ip else request.client.host

    check_rate_limit(ip)

    if is_already_reported(payload.postId):
        return ModerationResponse(
            postId=payload.postId,
            message="This post has already been reported.",
        )

    mark_reported(payload.postId)

    result = None
    content_hash = None

    try:
        cache_response = get_cached_result(payload.content)

        if isinstance(cache_response, tuple):
            result, content_hash = cache_response
        else:
            result = cache_response

        if not result:
            logging.info("Cache miss — calling analyze_content")
            result = await analyze_content(payload.content)

            if result and content_hash:
                set_cached_result(content_hash, result)

    except Exception as e:
        logging.error(f"Gemini API failed: {e}", exc_info=True)

        try:
            publish_event(payload, "human_review", ip)
            logging.info("Published human_review event due to Gemini failure")
        except Exception as pub_err:
            logging.error(f"RabbitMQ publish failed during Gemini fallback: {pub_err}", exc_info=True)

        return ModerationResponse(
            postId=payload.postId,
            message="Post has been reported successfully. We'll review it shortly.",
        )

    if not result:
        unmark_reported(payload.postId)
        logging.error("analyze_content returned empty result")
        raise HTTPException(
            status_code=500,
            detail="Moderation service returned empty result."
        )

    try:
        action = enforce_thresholds(result)
    except Exception as e:
        logging.error(f"enforce_thresholds failed: {e}", exc_info=True)
        action = "human_review"

    logging.info(f"Moderation result: {result} | Action: {action}")

    action_normalized = action.strip().lower() if action else ""

    if action_normalized in ("human_review", "auto_remove"):
        try:
            publish_event(payload, action_normalized, ip, result)
            logging.info(f"Published moderation event: {action_normalized}")
        except Exception as e:
            logging.error(f"RabbitMQ publish failed: {e}", exc_info=True)
    else:
        logging.warning(f"Unexpected action from enforce_thresholds: '{action}' — skipping publish")

    return ModerationResponse(
        postId=payload.postId,
        message="Post has been reported successfully. We'll review it shortly.",
    )
