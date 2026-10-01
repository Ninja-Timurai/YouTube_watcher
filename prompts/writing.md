# Writing the summary

Format: `templates/summary.md`, filled into the file `python -m yw scaffold` writes. Language: the video's own language by default (`output_language: video` in `config/summary.yaml`; `python -m yw info` prints the language to use). Keep the localized headings and labels `scaffold` writes. Reader: an executive who will not watch the video and must be able to act on, repeat or cite what it says.

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
Answer "what is this and what does it conclude?" first. No preamble ("In this video…"). If the video has no conclusion, say what it shows.

## Key takeaways
Ordered by importance to the reader. Each: bold label, then the point. Prefer claims, decisions, numbers, reasons and consequences over descriptions of what happens. No two bullets make the same point.

## Section by section
One entry per scaffolded heading, in time order; keep each heading's timecode (add a title where it says TODO). Compress, don't narrate: what is argued, shown or decided, and how it connects to the previous segment. Long videos: the same density per segment — later segments are not summarised more thinly than early ones.

## Notable quotes
The 2–6 sentences that carry the video's argument or are most quotable. Not jokes or filler unless they are the point.

## Facts and figures
Every number, statistic, date, named organisation, product or study the video cites, with the basis given. "None stated." if there are none.

## Action items
What the video tells the viewer to do, try, read or use. Not your recommendations. "None stated." if none.

## Verdict
Your editorial judgement, clearly marked by the labels. "Best part" is a time range from the transcript where the densest or most important material is.

## Limits
Transcript method caveats from `python -m yw info` (sparse captions, AI transcript), visual-only content, unidentified speakers, music or non-speech gaps. "Nothing material." only if true.
