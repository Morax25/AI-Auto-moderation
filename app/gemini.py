import json
import asyncio
from google import genai
from app.config import GEMINI_API_KEY, GEMINI_MODEL
from app.prompt import MODERATION_PROMPT

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

async def analyze_content(content: str) -> dict:
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            config={"response_mime_type": "application/json"},
            contents=MODERATION_PROMPT.format(content=content),
        )
    )
    return json.loads(response.text)

def enforce_thresholds(result: dict) -> str:
    confidence = result.get("confidence", 0)
    severity = result.get("severity", "none")
    category = result.get("category", "")

    if category == "csam":
        return "auto_remove"
    elif confidence >= 0.95 and severity in ("high", "critical"):
        return "auto_remove"
    else:
        return "allow"
