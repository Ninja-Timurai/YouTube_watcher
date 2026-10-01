# YouTube Watcher

You watch a YouTube video in full — by reading its complete transcript, segment by segment — and write an executive summary that lets the reader skip the video, or decide exactly which minutes are worth watching. Input: one or more YouTube links, or a channel/playlist plus a count. Output per video: `summaries/<published>_<id>.html` and `.md`, timecodes linked to the moment in the video. The run is single-pass: do not stop to ask the user anything.

## Non-negotiable rules

1. **The whole video.** Every segment file is read in full before writing. The summary's `Section by section` map covers every segment; `check` rejects a summary that skips one. Never summarise from the title, description or a partial read.
2. **Only what is said.** Every statement comes from the transcript. No background knowledge, no fact-checking from memory, no filling gaps. If the video does not say it, it is not in the summary. Your own judgement appears only in `Verdict`, labelled as such.
3. **Same strength.** Keep speakers' hedges ("I think", "maybe", "could"). A prediction stays a prediction, an anecdote stays an anecdote, a demo stays a demo — not a proven result. Attribute positions to who holds them.
4. **Verbatim quotes, exact figures.** Quotes are copied from the transcript at their timecode. Numbers are written as spoken; `check` rejects a number the transcript does not contain.
5. **Timecodes are evidence.** Every takeaway, quote, figure and action item carries the `[mm:ss]` (or `[h:mm:ss]`) of the transcript line it comes from.
6. **One A4 page.** At most 500 words; `check` enforces the budget. Reading the summary must take a fraction of the video's time.
7. **The video's language.** The summary is written in the language `python -m yw info` names (the video's own language by default), quotes untranslated.
8. **Config is the user's.** `config/summary.yaml` (language, limits, segment length), `prompts/writing.md`, `templates/summary.md`. Never edit them during a run.

## Procedure

Run every command from the repo root. `<id>` is the 11-character video id, printed by `fetch`.

1. `python -m yw keys` — both keys must be set; if one is missing, stop and say which.
2. For a channel or playlist: `python -m yw latest <@handle | channel URL | playlist URL> -n <N>` and take the ids.
3. `python -m yw fetch <url-or-id> [...]` — YouTube Data API metadata and chapters; Supadata transcript in the video's own audio language (captions, else AI transcription when captions are missing, sparse or a translated track); transcript split into segments (creator chapters, else `segment_minutes` windows).
4. `python -m yw info <id>` — video facts, transcript method and notes, segment list.
5. Read **every** segment file listed, in order, in full. Speaker names come only from what is said or shown in the title/description; otherwise "a speaker", "the host", "the interviewer".
6. `python -m yw scaffold <id>` — writes `runs/<id>/summary.md` with the header and one heading per segment. Write it in the language `info` names, keeping the localized headings. Fill it following `templates/summary.md` and `prompts/writing.md`. Replace every TODO. Untitled segment headings get a short descriptive title; keep the timecode.
7. Faithfulness self-check (`prompts/writing.md`), then `python -m yw check <id>` — fix every ERROR and re-run until PASS. Treat WARNs as likely wrong timecodes and fix them. Never weaken accuracy to pass: remove the claim instead.
8. `python -m yw render <id>` — writes the page and markdown and prints the page title and any link already recorded.
9. **Publish — every summary ends with a link.** Publish the page (`summaries/<published>_<id>.html`) with the Artifact tool: if `render` printed a `published:` link, pass it as `url` (read it first) so the same link updates; otherwise publish new with `icon: "video"` and a one-sentence `description` in the summary's language. Then `python -m yw link <id> <url>`. Without an Artifact tool (e.g. Codex), commit and push `summaries/` and use the `github:` link `render` printed.
10. Commit and push `summaries/` (the `.md`, `.html` and `links.json`) to the working branch.
11. Report per video in three lines or fewer: **the link first**, then title, video minutes vs reading minutes, transcript caveats.

For several videos, finish each one through `render` before starting the next.
