"""Split a transcript into reading segments: creator chapters when the video has them, else fixed windows.

The summary must cover every segment, so a segment is the unit that proves the whole video was read.
"""
from __future__ import annotations

import math

from . import config


def lines(text: str) -> list[tuple[int, str]]:
    """[(seconds, line)] for every timestamped transcript line."""
    out = []
    for line in text.splitlines():
        m = config.STAMP.match(line)
        if m:
            out.append((config.secs(m), line))
    return out


def plan(duration: int, chapters: list[dict], minutes: int) -> list[dict]:
    window = minutes * 60
    if chapters:
        segs = []
        for c in chapters:
            span = c["end"] - c["start"]
            parts = max(1, math.ceil(span / window)) if span > 2 * window else 1
            step = span / parts
            for i in range(parts):
                segs.append({"start": int(c["start"] + i * step),
                             "end": int(c["start"] + (i + 1) * step) if i < parts - 1 else c["end"],
                             "title": c["title"] + (f" (part {i + 1}/{parts})" if parts > 1 else "")})
        return segs
    n = max(1, math.ceil(duration / window - 0.1)) if duration else 1
    step = duration / n if duration else window
    return [{"start": int(i * step), "end": int((i + 1) * step) if i < n - 1 else max(duration, int(step)),
             "title": ""} for i in range(n)]


def snap(segs: list[dict], tl: list[tuple[int, str]]) -> list[dict]:
    """Move each segment start to the first transcript line at or after it, so headings carry real timecodes;
    drop segments with no transcript lines (silence, music)."""
    out = []
    for s in segs:
        inside = [t for t, _ in tl if s["start"] <= t < s["end"]]
        if inside:
            out.append({**s, "start": s["start"] if s["start"] in inside or not out and s["start"] == 0 else inside[0]})
    for a, b in zip(out, out[1:]):
        a["end"] = b["start"]
    return out


def build(text: str, duration: int, chapters: list[dict], minutes: int) -> list[dict]:
    tl = lines(text)
    if not duration and tl:
        duration = tl[-1][0] + 10
    segs = snap(plan(duration, chapters, minutes), tl)
    if segs:
        segs[0]["start"] = 0
        segs[-1]["end"] = max(segs[-1]["end"], duration, (tl[-1][0] + 1) if tl else 0)
    for s in segs:
        body = [ln for t, ln in tl if s["start"] <= t < s["end"]]
        s["words"] = sum(len(ln.split()) - 1 for ln in body)
        s["text"] = "\n".join(body) + "\n"
    return segs
