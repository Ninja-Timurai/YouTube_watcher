# Writing the summary

Format: `templates/summary.md`, filled into the file `python -m yw scaffold` writes. Language: the video's own language by default (`output_language: video` in `config/summary.yaml`; `python -m yw info` prints the language to use). Keep the localized headings and labels `scaffold` writes. Reader: an executive who will not watch the video and must be able to act on, repeat or cite what it says.

**One A4 page, at most 500 words in total** (`check` enforces it with per-section caps). Every word must earn its place: no restating the same point in two sections, no narration ("the speaker then discusses…"), no adjectives that carry no information. When over budget, cut the least important point, never compress into unreadable shorthand.

## Faithfulness (every section)

The checker proves timecodes, quotes, numbers and coverage. It cannot prove a sentence means what the speaker meant. These rules close that gap.

- **Only the transcript.** No outside knowledge, no context "everyone knows", no corrections of the speaker. If a speaker is wrong, report what they said; you may note in Limits that a claim is unsupported in the video.
- **Same strength.** Keep hedges ("I think", "maybe", "could", "potentially"). A hope is not a plan, a demo is not a deployment, one example is not a pattern, a prediction is not a result.
- **Who says it.** Attribute: "the narrator says", "a Genentech scientist explains". Name a speaker only if the transcript, title or description names them. Keep jokes, hypotheticals and views a speaker rejects distinct from their position.
- **Exact facts.** Numbers, names, products, dates as spoken. No rounding, conversion or arithmetic the speaker did not do. Write a number the way it can be found in the transcript ("80%", "two years").
- **Visual gaps stay visible.** What happens on screen without being said (a demo result, a chart) is not in the transcript. Report only what the speakers say about it and list the gap in Limits.
- **Quotes.** Copy the transcript's words; you may drop filler ("um", "you know") or join two consecutive caption lines; mark omissions with "...". Do not fix grammar. Quote in the original language; only when the summary language differs (a language forced in config) add a translation after it in parentheses.

### Self-check before `check`
Re-read each takeaway, figure and action item against the transcript lines at its timecode: (1) the lines say it, (2) at the same strength, (3) by the speaker named, (4) with the same number. Fix or delete what fails.

## Bottom line
At most 50 words. Answer "what is this and what does it conclude?" first. No preamble ("In this video…").

## Key takeaways
3–5 bullets, each at most 30 words, ordered by importance. Bold label, then the point. Prefer claims, decisions, numbers and consequences over descriptions. No two bullets make the same point.

## Section by section
One line per segment, at most 25 words, in time order: `- [mm:ss] **Title** — what is argued or decided`. Keep the scaffolded timecodes and titles. More than 12 segments: merge neighbours into `- [start–end] **Title** — …` lines, where the range spans the merged segments. This is a map of the video, not a second summary: do not repeat the takeaways.

## Notable quotes
At most 2: the sentences that carry the argument. "None stated." if nothing is worth quoting.

## Facts and figures
At most 4: numbers, dates, named studies or organisations the video cites, with the basis given. "None stated." if none.

## Action items
At most 3: what the video tells the viewer to do, try, read or use. Not your recommendations. "None stated." if none.

## Verdict
Your judgement, one line per label. "Best part" is a time range where the densest or most important material is.

## Limits
At most 2 bullets: transcript method caveats from `python -m yw info`, visual-only content, unidentified speakers. "Nothing material." only if true.
