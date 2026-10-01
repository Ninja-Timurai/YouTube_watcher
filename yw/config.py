"""Paths, environment keys, settings and timecode helpers."""
from __future__ import annotations

import os
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
RUNS_DIR = Path(os.environ.get("YW_RUNS_DIR", ROOT / "runs"))

KEYS = {
    "YOUTUBE_API_KEY": "video metadata, chapters, channel/playlist listing (YouTube Data API v3)",
    "SUPADATA_API_KEY": "transcripts: existing captions, or AI transcription when captions are missing (Supadata)",
}


def load_dotenv(path: Path = ROOT / ".env") -> None:
    """Local convenience only; cloud sessions set these as environment variables."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def key(name: str, required: bool = True) -> str | None:
    val = os.environ.get(name) or None
    if required and not val:
        raise SystemExit(f"Missing environment variable {name} — needed for {KEYS.get(name, name)}.")
    return val


def settings() -> dict:
    return yaml.safe_load((CONFIG_DIR / "summary.yaml").read_text(encoding="utf-8"))


def run_dir(slug: str) -> Path:
    d = RUNS_DIR / slug
    if not d.exists():
        raise SystemExit(f"No run '{slug}'. Start with: python -m yw fetch <youtube url>")
    return d


STAMP = re.compile(r"\[(\d{1,2}):(\d{2})(?::(\d{2}))?\]")


def fmt(sec: float) -> str:
    sec = int(sec)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def secs(m: re.Match) -> int:
    a, b, c = m.groups()
    return int(a) * 3600 + int(b) * 60 + int(c) if c else int(a) * 60 + int(b)


def parse(stamp: str) -> int:
    """'1:02:03', '62:03' or '[02:03]' -> seconds."""
    parts = [int(x) for x in stamp.strip("[] ").split(":")]
    total = 0
    for p in parts:
        total = total * 60 + p
    return total
