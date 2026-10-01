"""Transcripts through Supadata.

Fallback chain: native captions (original track, never a translation) -> mode=generate (AI speech-to-text on
Supadata's side) when captions are missing or implausibly sparse for the video's length. Sparse captions are kept
only when generation fails, and the summary's Limits section must say so.
"""
from __future__ import annotations

import time

from . import config
from .http import session

SUPADATA = "https://api.supadata.ai/v1/transcript"
MIN_WPM = 90        # speech runs ~130-180 words/min; far below means captions are fragmentary
MIN_SECONDS = 120   # too short to judge density reliably


def _get(s, url: str, params: dict | None = None, tries: int = 8):
    """GET that outlasts rate limits (429) and transient errors; stops at once on a spent plan quota."""
    delay, r = 5, None
    for i in range(tries):
        try:
            r = s.get(url, params=params, timeout=120)
        except Exception:
            if i == tries - 1:
                raise
        else:
            if r.status_code != 429:
                return r
            try:
                if r.json().get("error") == "limit-exceeded":
                    return r
            except ValueError:
                pass
        time.sleep(delay)
        delay = min(delay * 2, 60)
    return r


def _request(s, url: str, mode: str, lang: str = "") -> tuple[int, dict]:
    params = {"url": url, "text": "false", "mode": mode}
    if lang:
        params["lang"] = lang
    r = _get(s, SUPADATA, params)
    try:
        body = r.json()
    except ValueError:
        body = {"error": r.text[:200]}
    if r.status_code == 202 and body.get("jobId"):
        job = body["jobId"]
        for _ in range(180):  # up to ~30 min for long videos
            time.sleep(10)
            p = _get(s, f"{SUPADATA}/{job}")
            if p.status_code != 200:
                continue
            p = p.json()
            if p.get("status") == "completed":
                return 200, p
            if p.get("status") == "failed":
                return 500, p
        return 504, {"error": f"job {job} timed out"}
    return r.status_code, body


def _err(code: int, body: dict) -> str:
    return f"{code}: {body.get('error') or body.get('message') or 'empty'}"


def sparse(content: list[dict]) -> str:
    """Why captions look fragmentary, or ''."""
    if not content:
        return "empty"
    last = content[-1]
    seconds = (last.get("offset", 0) + last.get("duration", 0)) / 1000
    words = sum(len(c.get("text", "").split()) for c in content)
    if seconds >= MIN_SECONDS and words / (seconds / 60) < MIN_WPM:
        return f"captions sparse ({words / (seconds / 60):.0f} words/min)"
    return ""


def render(content) -> str:
    """One '[mm:ss] text' line per caption segment; multi-line segment text is folded into its line."""
    if isinstance(content, str):
        return content
    return "\n".join(f"[{config.fmt(c.get('offset', 0) / 1000)}] {' '.join(c.get('text', '').split())}"
                     for c in content if c.get("text", "").strip()) + "\n"


def _base(lang: str | None) -> str:
    return (lang or "").lower().split("-")[0].split("_")[0]


def fetch(url: str, audio_lang: str = "", allow_generate: bool = True) -> dict:
    """{'text', 'method', 'lang', 'notes'}; raises SystemExit when no transcript could be obtained.

    `audio_lang` (YouTube's declared audio language) pins the caption track: without it Supadata may return
    a translated track, which would misquote the speakers.
    """
    s = session(retry_429=False)
    s.headers["x-api-key"] = config.key("SUPADATA_API_KEY")
    notes: list[str] = []
    want = _base(audio_lang)
    code, body = _request(s, url, "native", want)
    native = body if code == 200 and isinstance(body.get("content"), list) and body["content"] else None
    method, issue = "captions", sparse(native["content"]) if native else f"native {_err(code, body)}"
    if native and not issue and want and _base(native.get("lang")) != want:
        issue = f"captions in '{native.get('lang')}', audio is '{want}' (translated track)"
        native = None
    if issue:
        notes.append(issue)
        if allow_generate:
            code, body = _request(s, url, "generate", want)
            method = "ai_transcript"
            if not (code == 200 and body.get("content")):
                notes.append(f"generate {_err(code, body)}")
                if native:
                    body, method, code = native, "captions", 200
                    notes.append("kept sparse captions")
    if not (code == 200 and body.get("content")):
        raise SystemExit("No transcript: " + "; ".join(notes))
    return {"text": render(body["content"]), "method": method, "lang": body.get("lang", ""), "notes": notes}
