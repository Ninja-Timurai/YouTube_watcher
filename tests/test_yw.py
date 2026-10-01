import pytest

from yw import config, segments, youtube
from yw.validate import quote_coverage, validate

TRANSCRIPT = "".join(f"[{config.fmt(t)}] {line}\n" for t, line in [
    (2, "Scientists come up with theories about how the world works."),
    (21, "That process of building the experiment takes maybe 80% of a scientist's time."),
    (130, "Each device has a different language that it speaks."),
    (300, "We started working with a microscope vendor on the second prototype."),
    (420, "It will make mistakes. So we can think about this as an iterative process."),
    (560, "He only needs two months instead of two years."),
])
META = {"id": "abcdefghijk", "duration": 600, "chapters": [], "transcript_notes": []}
CFG = {"limits": {"bottom_line_words": 90, "takeaways": [5, 10], "short_video_minutes": 10, "quotes_max": 6,
                  "section_min_words": 5, "quote_match": 0.85}}
SEGS = segments.build(TRANSCRIPT, 600, [], 5)
FILL = "words words words words words words"


def summary(quote='"It will make mistakes. So we can think about this as an iterative process." — a speaker [07:00]',
            figure="- Setup takes maybe 80% of a scientist's time [00:21]", sections=None):
    sections = sections or "".join(f"### [{config.fmt(s['start'])}] Part\n{FILL}\n\n" for s in SEGS)
    takeaways = "\n".join(f"- **T{i}:** scientists theories experiment [00:02]" for i in range(5))
    return f"""# Title

_Channel: X · Published: 2026-01-01 · Length: 10:00 · Transcript: captions (en) · Summarised: 2026-10-01_

## Bottom line

A short bottom line.

## Key takeaways

{takeaways}

## Section by section

{sections}
## Notable quotes

- {quote}

## Facts and figures

{figure}

## Action items

- None stated.

## Verdict

- **Watch in full if:** a
- **Skip if:** b
- **Best part:** [00:00–01:00] c

## Limits

- Nothing material.
"""


def errors(md):
    return validate(md, META, SEGS, TRANSCRIPT, CFG).errors


def test_valid_summary_passes():
    assert errors(summary()) == []


def test_fabricated_quote_rejected():
    assert any("Quote not found" in e for e in errors(summary(quote='"Claude never makes mistakes in the lab." [07:00]')))


def test_quote_at_wrong_timecode_points_to_fix():
    e = errors(summary(quote='"It will make mistakes. So we can think about this as an iterative process." [00:02]'))
    assert any("fix the timecode" in x for x in e)


def test_unspoken_number_rejected():
    assert any("number 95" in e for e in errors(summary(figure="- Setup takes 95% of time [00:21]")))


def test_skipped_segment_rejected():
    first = SEGS[0]
    md = summary(sections=f"### [{config.fmt(first['start'])}] Only the start\n{FILL}\n\n")
    assert any("Every segment must be covered" in e for e in errors(md))


def test_timecode_past_end_rejected():
    assert any("past the end" in e for e in errors(summary(figure="- Setup takes maybe 80% [12:00]")))


def test_quote_coverage_needs_order():
    text = "process iterative this about think we mistakes make will it"
    assert quote_coverage("It will make mistakes, so we think about this iterative process", text) < 0.5


def test_video_id_forms():
    for u in ("https://www.youtube.com/watch?v=P1zBiAQU1IA&t=30s", "https://youtu.be/P1zBiAQU1IA",
              "https://www.youtube.com/shorts/P1zBiAQU1IA", "P1zBiAQU1IA", "youtube.com/live/P1zBiAQU1IA?si=x"):
        assert youtube.video_id(u) == "P1zBiAQU1IA"
    with pytest.raises(SystemExit):
        youtube.video_id("https://example.com/watch?v=P1zBiAQU1IA")


def test_chapters_from_description():
    desc = "Intro text\n0:00 Intro\n02:15 - The problem\n1:05:00 Wrap up\nhttps://x"
    ch = youtube.chapters(desc, 4000)
    assert [(c["start"], c["end"], c["title"]) for c in ch] == [(0, 135, "Intro"), (135, 3900, "The problem"),
                                                               (3900, 4000, "Wrap up")]
    assert youtube.chapters("1:00 a\n2:00 b\n3:00 c", 400) == []  # must start at 0:00


def test_long_chapter_is_split_and_segments_cover_video():
    text = "".join(f"[{config.fmt(t)}] word word\n" for t in range(0, 3600, 30))
    segs = segments.build(text, 3600, [{"start": 0, "end": 600, "title": "A"},
                                       {"start": 600, "end": 3600, "title": "B"}], 10)
    assert [s["title"] for s in segs][:2] == ["A", "B (part 1/5)"]
    assert segs[0]["start"] == 0 and segs[-1]["end"] >= 3600
    assert all(a["end"] == b["start"] for a, b in zip(segs, segs[1:]))


def test_iso_duration():
    assert youtube.iso_duration("PT1H2M3S") == 3723 and youtube.iso_duration("PT45S") == 45
