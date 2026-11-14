import json
import logging
import os

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from data_pipeline.predict_profile import predict_profile
from profile_api import ProfileRequest

router = APIRouter(prefix="/ai", tags=["AI explanations"])
logger = logging.getLogger(__name__)

# These descriptions belong specifically to the saved k=4 model.
PROFILE_FACTS = {
    0: {
        "name": "Recreational activity pattern",
        "description": (
            "Higher median reported vigorous and moderate recreational "
            "activity than the other groups."
        ),
    },
    1: {
        "name": "Active transport pattern",
        "description": (
            "Higher median reported walking/cycling for transport "
            "than the other groups."
        ),
    },
    2: {
        "name": "Higher fat-density pattern",
        "description": (
            "Higher median fat intake per 1,000 kcal. Median reported "
            "recreational and transport activity was zero."
        ),
    },
    3: {
        "name": "Higher carbohydrate-density pattern",
        "description": (
            "Higher median carbohydrate and iron intake per 1,000 kcal. "
            "Median reported recreational and transport activity was zero."
        ),
    },
}


class ExplanationResponse(BaseModel):
    profile_id: int
    profile_name: str
    explanation: str
    generation_complete: bool
    language_model: str
    note: str


@router.post("/profile/explain", response_model=ExplanationResponse)
async def explain_profile(request: ProfileRequest):
    try:
        prediction = await run_in_threadpool(
            predict_profile,
            request.model_dump(exclude={"age"}),
        )
    except FileNotFoundError:
        raise HTTPException(503, "The profile model is unavailable.")
    except ValueError as exc:
        raise HTTPException(422, str(exc))

    facts = PROFILE_FACTS[prediction["profile_id"]]
    model_name = os.getenv("OLLAMA_MODEL", "mistral:latest")

    context = {
        "profile_id": prediction["profile_id"],
        "profile": facts,
        "reported_inputs": request.model_dump(),
        "limitations": [
            "Profile descriptions summarize group medians, not every member.",
            "Profiles are exploratory and are not ranked.",
            "Dietary values describe one reported day, not usual intake.",
            "Occupational activity is not included.",
            "Age is context only and did not affect profile assignment.",
            "No menstrual phase was supplied or inferred.",
        ],
    }

    payload = {
        "model": model_name,
        "stream": False,
        "system": (
           
           "Dietary inputs cover one reported day. "
"Recreational and transport activity are minutes per typical week; "
"sedentary time is minutes per typical day. "
"Never describe all inputs as a one-day snapshot. "
"Address the user as 'you', not 'the user'. "
"Return only one paragraph of 60-90 words. "
"Do not greet, use lists, or repeat all inputs. "
"Explain the assigned profile using its supplied description. "
"Mention at most two relevant reported values. "
           
           
        ),
        "prompt": json.dumps(context),
        "options": {
            "temperature": 0.2,
            "num_predict": 300,
            "num_ctx": 2048,
        },
    }

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=5, read=240, write=10, pool=5
            ),
            trust_env=False,
        ) as client:
            response = await client.post(
                "http://127.0.0.1:11434/api/generate",
                json=payload,
            )
            response.raise_for_status()
            generated = response.json()

    except httpx.TimeoutException:
        raise HTTPException(504, "Ollama took too long. Please retry.")
    except httpx.HTTPStatusError:
        logger.exception("Ollama returned an error")
        raise HTTPException(
            502, "Ollama could not generate an explanation."
        )
    except httpx.RequestError:
        raise HTTPException(
            503, "Ollama is unavailable. Check that it is running."
        )
    except ValueError:
        raise HTTPException(502, "Ollama returned an invalid response.")

    text = generated.get("response")
    if not isinstance(text, str) or not text.strip():
        raise HTTPException(502, "Ollama returned an empty explanation.")

    return {
        "profile_id": prediction["profile_id"],
        "profile_name": facts["name"],
        "explanation": text.strip(),
        "generation_complete": (
            generated.get("done") is True
            and generated.get("done_reason") != "length"
        ),
        "language_model": model_name,
        "note": (
            "AI-generated explanation of an exploratory profile; "
            "it may contain errors and is not medical advice."
        ),
    }