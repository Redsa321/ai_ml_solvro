"""Explicit opt-in Gemini REST adapter; prompt artifacts exist before calls."""

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

from .context import unknown_citations
from .files import read_json, utc_now, write_json


def settings(env_path: Path = Path(".env")) -> dict[str, str]:
    keys = ("GENERATION_PROVIDER", "GEMINI_API_KEY", "GEMINI_MODEL")
    values = {key: "" for key in keys}
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, separator, raw = line.partition("=")
            if separator and key.strip() in keys:
                raw = raw.strip()
                if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
                    raw = raw[1:-1]
                values[key.strip()] = raw
    return {key: os.environ.get(key, value) for key, value in values.items()}


def generate_gemini(prompt: str, api_key: str, model: str, *, transport=None) -> dict:
    if not api_key or not model:
        raise ValueError("Ustaw lokalnie GEMINI_API_KEY i GEMINI_MODEL; klucza nie podawaj w CLI.")
    model = model.removeprefix("models/")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", model):
        raise ValueError("Niepoprawna nazwa modelu Gemini.")
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 1536},
    }
    request = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )
    opener = transport or urllib.request.urlopen
    try:
        with opener(request, timeout=45) as response:
            body = json.load(response)
    except urllib.error.HTTPError as exc:
        # Do not log a request, headers or a provider error body which might echo secrets.
        status = exc.code
        exc.close()
        raise ValueError(f"Gemini API zwróciło HTTP {status}; prompt pozostał zapisany.") from None
    except (urllib.error.URLError, TimeoutError):
        raise ValueError("Brak odpowiedzi Gemini API; prompt pozostał zapisany.") from None
    if not isinstance(body, dict):
        raise ValueError("Gemini zwróciło niepoprawny format odpowiedzi.")
    candidates = body.get("candidates", [])
    if not isinstance(candidates, list) or not candidates or not isinstance(candidates[0], dict):
        raise ValueError("Gemini nie zwróciło odpowiedzi; sprawdź dostęp lub blokadę generacji.")
    candidate = candidates[0]
    answer = "\n".join(
        part["text"] for part in candidate.get("content", {}).get("parts", [])
        if part.get("text") and not part.get("thought")
    )
    if not answer.strip():
        raise ValueError("Gemini zwróciło pustą odpowiedź.")
    return {
        "answer": answer, "model": model,
        "finish_reason": candidate.get("finishReason"),
        "usage": body.get("usageMetadata", {}),
    }


def generate_packet(directory: Path, config: dict, *, transport=None) -> dict:
    metadata_path = directory / "metadata.json"
    info = read_json(metadata_path)
    sources = read_json(directory / "sources.json")
    if not sources:
        info.update(generation_status="not_run", generation_reason="no_matching_sources")
        write_json(metadata_path, info)
        return info
    info.update(
        generation_provider="gemini", generation_started_at=utc_now(),
        generation_status="in_progress",
    )
    write_json(metadata_path, info)
    try:
        response = generate_gemini(
            (directory / "prompt.txt").read_text(encoding="utf-8"),
            config.get("GEMINI_API_KEY", ""), config.get("GEMINI_MODEL", ""),
            transport=transport,
        )
    except (ValueError, json.JSONDecodeError) as exc:
        info.update(generation_status="failed", generation_error=str(exc))
        write_json(metadata_path, info)
        raise ValueError(f"{exc} Pakiet: {directory}") from None
    (directory / "answer.md").write_text(response.pop("answer"), encoding="utf-8")
    answer = (directory / "answer.md").read_text(encoding="utf-8")
    unknown = unknown_citations(answer, sources)
    info.update(
        generation_status="generated" if not unknown else "invalid_citations",
        generation_completed_at=utc_now(), generation_quality="nie oceniano — wymaga oceny ręcznej",
        unknown_citations=unknown, **response,
    )
    write_json(metadata_path, info)
    return info
