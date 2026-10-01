# YouTube Watcher

Watches a YouTube video in full — every word of its transcript, segment by segment — and writes an executive summary you can read in a few minutes instead of watching. Every claim, quote and figure carries a clickable timecode into the video, and a validator rejects summaries that skip part of the video, misquote, or contain numbers nobody said.

Built on the architecture of [ahead_of_ai](https://github.com/Ninja-Timurai/ahead_of_ai): Python tools do deterministic I/O (YouTube Data API, Supadata transcripts, segmentation, validation, rendering); the coding agent (Claude Code or Codex) does the reading and writing under the rules in `AGENTS.md`.

## Run it

Claude Code, in a session on this repository:

```
/summarise-video https://www.youtube.com/watch?v=P1zBiAQU1IA
/summarise-video https://youtu.be/abc https://youtu.be/def
/summarise-video @lexfridman 2          # newest 2 videos of a channel
/summarise-video https://www.youtube.com/playlist?list=PL... 5
```

Codex: `Summarize https://youtu.be/... following AGENTS.md.`

Output: `summaries/<published>_<video id>.html` (self-contained, light/dark) and `.md`. Example: `summaries/2026-08-27_P1zBiAQU1IA.md` — an 11-minute video, ~4-minute read.

## Language

Summaries are written in the video's own language (taken from the transcript), with headings localized for en, ru, uk, de, es, fr. Set `output_language: English` (or another language) in `config/summary.yaml` to force one language.

## What the summary contains

Bottom line · Key takeaways · Section by section (one per chapter or 8-minute window) · Notable quotes · Facts and figures · Action items · Verdict (watch / skip / best minutes) · Limits (AI transcript, visual-only content).

## How "watched completely" is enforced

1. **Full transcript** via Supadata, pinned to the video's own audio language (YouTube metadata), so a translated caption track is never used. Missing, sparse (<90 words/min) or translated captions fall back to Supadata AI transcription.
2. **Segments**: creator chapters from the description, else fixed windows (`segment_minutes`); chapters longer than twice the window are split. Each segment is a file the agent reads.
3. **`check`** blocks rendering unless: every segment has a section; every takeaway/quote/figure/action has a timecode inside the video; each quote matches the transcript at its timecode (in order, ≥85% of words); every number in Facts and figures is spoken in the transcript; length limits and required sections hold. Likely wrong timecodes are flagged as warnings.

## Setup

| Variable | Service | Used for |
|---|---|---|
| `YOUTUBE_API_KEY` | Google Cloud, YouTube Data API v3 | title, channel, duration, audio language, chapters, channel/playlist listing |
| `SUPADATA_API_KEY` | Supadata | transcripts: captions, or AI transcription |

Set them as environment variables (cloud environment settings) or in a local `.env` (see `.env.example`). `pip install -r requirements.txt` (Claude Code does it at session start).

## Commands

```
python -m yw keys                          # which API keys are set
python -m yw latest <@handle|channel URL|playlist URL> [-n 5]
python -m yw fetch <url|id> [...] [--minutes N] [--no-generate] [--force]
python -m yw info <id>                     # facts, transcript caveats, segment files
python -m yw resegment <id> --minutes N
python -m yw scaffold <id>                 # summary.md skeleton: header + one heading per segment
python -m yw check <id>                    # validate against the transcript
python -m yw render <id>                   # validate, write summaries/*.html and *.md, print links
python -m yw link <id> [url]               # record or show the published page link
python -m pytest -q
```

## Editable without code

| File | Controls |
|---|---|
| `config/summary.yaml` | output language (default: the video's), segment length, limits, quote-match threshold |
| `prompts/writing.md` | how each section is written; faithfulness rules |
| `templates/summary.md` | layout |

Working files (`runs/<id>/`: metadata, transcript, segments, draft) are git-ignored.
