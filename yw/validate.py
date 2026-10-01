"""Summary validator: the rules that can be checked mechanically.

Errors block `render`. Warnings are shown but do not block.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import config, i18n

SECTIONS = ["Bottom line", "Key takeaways", "Section by section", "Notable quotes", "Facts and figures",
            "Action items", "Verdict", "Limits"]
TIMED = ["Key takeaways", "Notable quotes", "Facts and figures", "Action items"]
TS = re.compile(r"\[(\d{1,2}:\d{2}(?::\d{2})?)(?:\s*[-–]\s*(\d{1,2}:\d{2}(?::\d{2})?))?\]")
QUOTED = re.compile(r"[\"“]([^\"“”]*)[\"”]")
NUMBER = re.compile(r"(?<![\w:.])(\d[\d,]*(?:\.\d+)?)(?![\d:])")
WORD = re.compile(r"[^\W_]+(?:'[^\W_]+)?")
NONE = re.compile(r"^\s*(none (stated|given|made)|" + "|".join(re.escape(l["none"].rstrip(".")) for l in
                  i18n.LABELS.values()) + r")\.?\s*$", re.I)


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def split_sections(md: str) -> tuple[str, dict[str, str]]:
    """Sections keyed by canonical English name, whatever language their headings are in."""
    parts = re.split(r"^## +(.+?)\s*$", md, flags=re.M)
    alias = i18n.aliases()
    return parts[0], {alias.get(parts[i].strip(), parts[i].strip()): parts[i + 1] for i in range(1, len(parts), 2)}


def bullets(text: str) -> list[str]:
    out: list[str] = []
    for line in text.splitlines():
        if re.match(r"^[-*] ", line):
            out.append(line[2:].strip())
        elif out and line.startswith("  ") and line.strip():
            out[-1] += " " + line.strip()
    return out


def words(s: str) -> list[str]:
    return WORD.findall(s.lower().replace("’", "'"))


def quote_coverage(quote: str, text: str) -> float:
    """Share of the quote's content words found in order within one stretch of the text (tolerates dropped
    filler and an elided '...', not words scattered across the transcript)."""
    q = [w for w in words(quote) if len(w) > 2] or words(quote)
    if not q:
        return 1.0
    t = words(text)
    span, best = 3 * len(words(quote)) + 20, 0
    for start, w in enumerate(t):
        if w not in q[:2]:
            continue
        i = 0
        for tw in t[start:start + span]:
            if i < len(q) and tw == q[i]:
                i += 1
        best = max(best, i)
        if best == len(q):
            break
    return best / len(q)


def window(lines: list[tuple[int, str]], t: int, before: int, after: int) -> str:
    return "\n".join(ln for s, ln in lines if t - before <= s <= t + after)


def _plain(s: str) -> str:
    return TS.sub(" ", s)


def _num(s: str) -> str:
    return s.replace(",", "").rstrip(".")


def same_language(meta: dict, cfg: dict) -> bool:
    """False when the summary is written in another language than the transcript, so word overlap means nothing."""
    src = i18n.base(meta.get("transcript_lang"))
    return not src or i18n.summary_lang(meta, cfg) == src


def validate(md: str, meta: dict, segs: list[dict], transcript: str, cfg: dict) -> Report:
    from .segments import lines as tlines
    rep = Report()
    lim = cfg["limits"]
    tl = tlines(transcript)
    duration = meta.get("duration") or (tl[-1][0] + 10 if tl else 0)
    full_text = transcript
    full_nums = {_num(n) for n in NUMBER.findall(re.sub(r"\[\d[\d:]*\]", " ", transcript))}
    head, secs = split_sections(md)
    overlap = same_language(meta, cfg)
    lab = i18n.labels(i18n.summary_lang(meta, cfg))

    if not re.search(r"^# .+", head, re.M):
        rep.errors.append("Missing '# <video title>' heading.")
    for k in (lab["channel"] + ":", lab["length"] + ":", lab["transcript"] + ":"):
        if k not in head:
            rep.errors.append(f"Header line missing '{k}' (use `python -m yw scaffold`).")
    for name in SECTIONS:
        if name not in secs:
            local = dict(zip(i18n.KEYS, lab["sections"]))[name]
            rep.errors.append(f"Missing section '## {local}'.")
    order = [s for s in secs if s in SECTIONS]
    if order != [s for s in SECTIONS if s in secs]:
        rep.errors.append(f"Sections out of order: {order}")

    for m in TS.finditer(md):
        for g in m.groups():
            if g and config.parse(g) > duration + 5:
                rep.errors.append(f"Timecode [{g}] is past the end of the video ({config.fmt(duration)}).")

    # Bottom line
    bl = secs.get("Bottom line", "")
    n = len(words(_plain(bl)))
    if not n:
        rep.errors.append("Bottom line is empty.")
    elif n > lim["bottom_line_words"]:
        rep.errors.append(f"Bottom line is {n} words; limit {lim['bottom_line_words']}.")

    # Key takeaways
    kt = bullets(secs.get("Key takeaways", ""))
    lo, hi = lim["takeaways"]
    if duration < lim["short_video_minutes"] * 60:
        lo = min(lo, 3)
    if not lo <= len(kt) <= hi:
        rep.errors.append(f"Key takeaways: {len(kt)} bullets; need {lo}–{hi}.")

    # One A4 page: per-section caps and a total word budget.
    for name, cap in (("Notable quotes", lim["quotes_max"]), ("Facts and figures", lim["facts_max"]),
                      ("Action items", lim["actions_max"]), ("Limits", lim["limits_max"])):
        n = len([b for b in bullets(secs.get(name, "")) if not NONE.match(b)])
        if n > cap:
            rep.errors.append(f"{name}: {n} bullets; limit {cap}.")
    for name in ("Key takeaways", "Facts and figures", "Action items", "Limits"):
        for b in bullets(secs.get(name, "")):
            n = len(words(_plain(b)))
            if n > lim["bullet_words"]:
                rep.errors.append(f"{name}: bullet is {n} words; limit {lim['bullet_words']}: {b[:60]!r}")
    body = "\n".join(secs.values())
    total = len(words(_plain(re.sub(r"\(https?://[^)]*\)", " ", body))))
    if total > lim["max_words"]:
        rep.errors.append(f"Summary is {total} words; one A4 page allows {lim['max_words']}. Cut, don't cram.")

    # Every bullet in timed sections carries a timecode, and its words occur near that timecode.
    for name in TIMED:
        for b in bullets(secs.get(name, "")):
            if NONE.match(b):
                continue
            stamps = TS.findall(b)
            if not stamps:
                rep.errors.append(f"{name}: bullet without a [mm:ss] timecode: {b[:80]!r}")
                continue
            t = config.parse(stamps[0][0])
            near = window(tl, t, 60, 180)
            content = {w for w in words(_plain(re.sub(QUOTED, ' ', b))) if len(w) > 4}
            if overlap and content and len(content & set(words(near))) / len(content) < 0.15 \
                    and name != "Notable quotes":
                rep.warnings.append(f"{name}: little overlap with transcript at [{stamps[0][0]}] — check the "
                                    f"timecode: {b[:70]!r}")

    # Quotes: verbatim, at their timecode. Elsewhere in the summary: verbatim somewhere in the transcript.
    nq = bullets(secs.get("Notable quotes", ""))
    for b in nq:
        qm, stamps = next((m for m in QUOTED.finditer(b) if len(m.group(1)) >= 8), None), TS.findall(b)
        if NONE.match(b):
            continue
        if not qm:
            rep.errors.append(f"Notable quotes: no quotation marks in {b[:80]!r}")
            continue
        if stamps:
            near = window(tl, config.parse(stamps[0][0]), 30, 150)
            cov = quote_coverage(qm.group(1), near)
            if cov < lim["quote_match"]:
                where = quote_coverage(qm.group(1), full_text)
                hint = " (it appears elsewhere: fix the timecode)" if where >= lim["quote_match"] else ""
                rep.errors.append(f"Quote not found at [{stamps[0][0]}] ({cov:.0%} match){hint}: "
                                  f"\"{qm.group(1)[:80]}\"")
    for name, body in secs.items():
        if name in ("Notable quotes",):
            continue
        for q in QUOTED.findall(body):
            if len(words(q)) >= 5 and quote_coverage(q, full_text) < lim["quote_match"]:
                rep.errors.append(f"{name}: quotation not found in transcript: \"{q[:80]}\"")

    # Figures: every number must be spoken; near its timecode ideally.
    for b in bullets(secs.get("Facts and figures", "")):
        stamps = TS.findall(b)
        near = window(tl, config.parse(stamps[0][0]), 90, 180) if stamps else ""
        near_nums = {_num(x) for x in NUMBER.findall(re.sub(r"\[\d[\d:]*\]", " ", near))}
        for x in NUMBER.findall(_plain(b)):
            x = _num(x)
            if x in near_nums:
                continue
            if x in full_nums:
                rep.warnings.append(f"Facts and figures: {x} is in the transcript but not near "
                                    f"[{stamps[0][0] if stamps else '?'}]")
            else:
                rep.errors.append(f"Facts and figures: number {x} does not occur in the transcript "
                                  f"(write it as spoken, or remove it): {b[:70]!r}")

    # Coverage: timeline bullets '- [start] **Title** — line' or '- [start–end] ...'; every segment must have an
    # entry starting inside it, or lie inside an entry's explicit range (used to group segments of long videos).
    entries = []
    for b in bullets(secs.get("Section by section", "")):
        m = TS.match(b)
        if not m:
            rep.errors.append(f"Section by section: entry must start with a [mm:ss] timecode: {b[:60]!r}")
            continue
        start = config.parse(m.group(1))
        end = config.parse(m.group(2)) if m.group(2) else None
        entries.append((start, end))
        n = len(words(_plain(b)))
        if n > lim["timeline_entry_words"]:
            rep.errors.append(f"Section by section: [{m.group(1)}] is {n} words; limit {lim['timeline_entry_words']}.")
    if len(entries) > lim["timeline_max_entries"]:
        rep.errors.append(f"Section by section: {len(entries)} entries; limit {lim['timeline_max_entries']} "
                          f"(group neighbouring segments as [start–end]).")
    for s in segs:
        if not any(s["start"] <= t < s["end"] or (e is not None and t <= s["start"] + 5 and e >= s["end"] - 5)
                   for t, e in entries):
            rep.errors.append(f"Section by section: segment {config.fmt(s['start'])}–{config.fmt(s['end'])} "
                              f"({s['title'] or 'untitled'}) not covered. Every segment must be covered.")
    starts = [t for t, _ in entries]
    if starts != sorted(starts):
        rep.errors.append("Section by section: entries not in time order.")

    # Verdict
    v = secs.get("Verdict", "")
    for k in (lab["watch"], lab["skip"], lab["best"]):
        if k.lower() not in v.lower():
            rep.errors.append(f"Verdict: missing '**{k}:**' line.")

    # Limits must mention a sparse-caption or AI-transcript caveat when relevant.
    if meta.get("transcript_notes") and not bullets(secs.get("Limits", "")):
        rep.errors.append("Limits: transcript had issues (see `info`) but Limits is empty.")

    if "TODO" in md:
        rep.errors.append("Unfilled TODO markers remain.")
    return rep
