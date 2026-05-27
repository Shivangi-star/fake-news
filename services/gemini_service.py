import json
import os
import re

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

# gemini-2.0-flash free tier quota is often exhausted; these models work on current keys
MODEL_FALLBACKS = [
    "gemini-2.5-flash",
    "gemini-3-flash-preview",
    "gemini-flash-latest",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
]

TEXT_PROMPT_HEAD = """You are forensic., an AI credibility verifier. Run three analysis passes on this text claim/headline/article.

PASS 1 — Claim reasoning: Test against world knowledge. Flag loaded language, contradictions, unverifiable specifics.
PASS 2 — Source & context: Assess whether the claim pattern matches known misinformation tropes.
PASS 3 — Weighted verdict: Combine into one defensible score and label.

Respond ONLY with valid JSON (no markdown fences). Use this exact structure:
{
  "score": 75,
  "verdict": "Likely Real",
  "summary": "two or three sentences",
  "pixel_forensics": { "score": null, "findings": ["item"] },
  "claim_reasoning": { "score": 70, "findings": ["item"] },
  "incident": "event or Unknown",
  "location": "place or Unknown",
  "red_flags": ["item"],
  "rationale": "explanation",
  "suggested_actions": ["item"]
}

verdict must be exactly one of: Likely Real, Likely Fake, Unverified
"""

IMAGE_PROMPT_HEAD = """You are forensic., an AI credibility verifier. Run three analysis passes on this image and optional caption.

PASS 1 — Pixel forensics: Scan for splicing, warped geometry, AI-generation artefacts, lighting inconsistencies, impossible reflections.
PASS 2 — Claim reasoning: If caption provided, test it against the image and world knowledge.
PASS 3 — Weighted verdict: One credibility score (0-100) and label.

Also provide image_description and image_created_date (YYYY-MM-DD when possible).

Respond ONLY with valid JSON (no markdown fences). Use this exact structure:
{
  "score": 75,
  "verdict": "Likely Real",
  "summary": "two or three sentences",
  "image_description": "what the image shows",
  "image_created_date": "2024-01-15",
  "date_source": "EXIF or visual clues or estimated",
  "pixel_forensics": { "score": 80, "findings": ["item"] },
  "claim_reasoning": { "score": 70, "findings": ["item"] },
  "incident": "event or Unknown",
  "location": "place or Unknown",
  "red_flags": ["item"],
  "rationale": "explanation",
  "suggested_actions": ["item"]
}

verdict must be exactly one of: Likely Real, Likely Fake, Unverified
"""


def configure(api_key: str) -> None:
    genai.configure(api_key=api_key)


def get_model_name() -> str:
    return os.getenv("GEMINI_MODEL", MODEL_FALLBACKS[0]).strip() or MODEL_FALLBACKS[0]


def _models_to_try(preferred: str | None = None) -> list[str]:
    preferred = (preferred or get_model_name()).strip()
    ordered = [preferred] + MODEL_FALLBACKS
    seen: set[str] = set()
    result: list[str] = []
    for name in ordered:
        if name and name not in seen:
            seen.add(name)
            result.append(name)
    return result


def _friendly_error(exc: Exception) -> str:
    if isinstance(exc, google_exceptions.ResourceExhausted):
        return (
            "Gemini API quota exceeded for this model. "
            "Wait a few minutes, enable billing in Google AI Studio, "
            "or set GEMINI_MODEL=gemini-2.5-flash in your .env file."
        )
    if isinstance(exc, google_exceptions.InvalidArgument):
        return f"Invalid request to Gemini: {exc}"
    if isinstance(exc, google_exceptions.PermissionDenied):
        return "API key rejected. Check GEMINI_API_KEY in your .env file."
    if isinstance(exc, google_exceptions.NotFound):
        return f"Model not available: {exc}"
    return str(exc)


def _response_text(response) -> str:
    try:
        text = response.text
        if text:
            return text
    except ValueError:
        pass
    if response.candidates:
        parts = response.candidates[0].content.parts
        return "".join(getattr(p, "text", "") or "" for p in parts)
    raise ValueError("Gemini returned an empty response. Try again or use a different image.")


def _parse_json_response(raw: str) -> dict:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group())
        raise ValueError("Model did not return valid JSON. Please try again.") from None


def _generate_json(prompt_parts, preferred_model: str | None = None) -> dict:
    last_error: Exception | None = None
    for model_name in _models_to_try(preferred_model):
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt_parts)
            return _parse_json_response(_response_text(response))
        except google_exceptions.ResourceExhausted as exc:
            last_error = exc
            continue
        except google_exceptions.NotFound as exc:
            last_error = exc
            continue
    if last_error:
        raise RuntimeError(_friendly_error(last_error)) from last_error
    raise RuntimeError("No Gemini model available.")


def analyze_text(text: str, model_name: str | None = None) -> dict:
    prompt = (
        TEXT_PROMPT_HEAD
        + "\nText to analyze:\n---\n"
        + text
        + "\n---\n"
    )
    return _generate_json(prompt, model_name)


def analyze_image(
    image_bytes: bytes,
    mime_type: str,
    caption: str = "",
    exif_date: str | None = None,
    model_name: str | None = None,
) -> dict:
    exif_line = (
        f"EXIF capture date from file metadata: {exif_date}"
        if exif_date
        else "No reliable EXIF capture date in file metadata."
    )
    caption_line = caption.strip() if caption else "(none provided)"
    prompt = (
        IMAGE_PROMPT_HEAD
        + "\n"
        + exif_line
        + "\nCaption/context from user: "
        + caption_line
        + "\n"
    )
    return _generate_json(
        [
            {"mime_type": mime_type, "data": image_bytes},
            prompt,
        ],
        model_name,
    )
