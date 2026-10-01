"""Command-line tools the agent calls. Deterministic I/O only; all judgement lives in the prompts."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone

from . import config, render, segments, transcript, validate, youtube

READ_WPM = 230


def _load(slug: str) -> tuple:
    run = config.run_dir(slug)
    meta = json.loads((run / "meta.json").read_text(encoding="utf-8"))
    text = (run / "transcript.txt").read_text(encoding="utf-8")
    segs = json.loads((run / "segments.json").read_text(encoding="utf-8"))
    return run, meta, text, segs


def _write_segments(run, meta: dict, text: str, minutes: int) -> list[dict]:
    segs = segments.build(text, meta["duration"], meta["chapters"], minutes)
    sdir = run / "segments"
    sdir.mkdir(exist_ok=True)
    for f in sdir.glob("*.txt"):
        f.unlink()
    for i, s in enumerate(segs, 1):
        name = f"{i:02d}_{config.fmt(s['start']).replace(':', '-')}.txt"
        title = f"# Segment {i}/{len(segs)} · {config.fmt(s['start'])}–{config.fmt(s['end'])}" + \
                (f" · {s['title']}" if s["title"] else "")
        (sdir / name).write_text(title + "\n\n" + s.pop("text"), encoding="utf-8")
        s["file"] = f"segments/{name}"
    (run / "segments.json").write_text(json.dumps(segs, ensure_ascii=False, indent=1), encoding="utf-8")
    return segs


def cmd_fetch(a) -> None:
    cfg = config.settings()
    for src in a.videos:
        vid = youtube.video_id(src)
        run = config.RUNS_DIR / vid
        if (run / "transcript.txt").exists() and not a.force:
            print(f"{vid}: already fetched (use --force to refetch)")
            continue
        meta = youtube.metadata(vid)
        if meta["live"] in ("live", "upcoming"):
            raise SystemExit(f"{vid}: video is {meta['live']}; summarise it after the broadcast ends.")
        tr = transcript.fetch(meta["url"], meta["language"], allow_generate=not a.no_generate)
        run.mkdir(parents=True, exist_ok=True)
        meta.update(transcript_method=tr["method"], transcript_lang=tr["lang"], transcript_notes=tr["notes"],
                    fetched=datetime.now(timezone.utc).isoformat(timespec="seconds"))
        (run / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        (run / "transcript.txt").write_text(tr["text"], encoding="utf-8")
        segs = _write_segments(run, meta, tr["text"], a.minutes or cfg["segment_minutes"])
        words = sum(s["words"] for s in segs)
        print(f"{vid}: {meta['title'][:70]!r} · {config.fmt(meta['duration'])} · {tr['method']} ({tr['lang'] or '?'}) "
              f"· {words} words · {len(segs)} segments" + (f" · notes: {'; '.join(tr['notes'])}" if tr["notes"] else ""))


def cmd_info(a) -> None:
    run, meta, text, segs = _load(a.slug)
    print(f"{meta['title']}\n{meta['channel']} · {meta['published']} · {config.fmt(meta['duration'])} · "
          f"{meta['views']:,} views\nTranscript: {meta['transcript_method']} ({meta['transcript_lang'] or '?'})"
          + (f" · notes: {'; '.join(meta['transcript_notes'])}" if meta["transcript_notes"] else ""))
    print(f"Chapters from description: {'yes' if meta['chapters'] else 'no'}\nSegments (read every file in full):")
    for i, s in enumerate(segs, 1):
        print(f"  {i:>2}. {config.fmt(s['start']):>8}–{config.fmt(s['end']):<8} {s['words']:>6} words  "
              f"{s['file']}  {s['title']}")


def cmd_resegment(a) -> None:
    run, meta, text, _ = _load(a.slug)
    segs = _write_segments(run, meta, text, a.minutes)
    print(f"{len(segs)} segments")


def cmd_scaffold(a) -> None:
    run, meta, text, segs = _load(a.slug)
    path = run / "summary.md"
    if path.exists() and not a.force:
        raise SystemExit(f"{path} exists; use --force to overwrite.")
    method = {"captions": "captions", "ai_transcript": "AI transcript"}[meta["transcript_method"]]
    sections = "\n".join(f"### [{config.fmt(s['start'])}] {s['title'] or 'TODO title'}\nTODO\n" for s in segs)
    md = (f"# {meta['title']}\n\n"
          f"_Channel: {meta['channel']} · Published: {meta['published']} · Length: {config.fmt(meta['duration'])} · "
          f"Transcript: {method} ({meta['transcript_lang'] or '?'}) · Summarised: {date.today().isoformat()}_  \n"
          f"_Video: {meta['url']}_\n\n"
          "## Bottom line\n\nTODO\n\n## Key takeaways\n\n- TODO [00:00]\n\n"
          f"## Section by section\n\n{sections}\n"
          "## Notable quotes\n\n- \"TODO\" — speaker [00:00]\n\n## Facts and figures\n\n- TODO [00:00]\n\n"
          "## Action items\n\n- TODO [00:00]\n\n## Verdict\n\n- **Watch in full if:** TODO\n- **Skip if:** TODO\n"
          "- **Best part:** TODO\n\n## Limits\n\n- TODO\n")
    path.write_text(md, encoding="utf-8")
    print(path)


def _check(slug: str) -> tuple:
    run, meta, text, segs = _load(slug)
    path = run / "summary.md"
    if not path.exists():
        raise SystemExit(f"No summary at {path}. Run: python -m yw scaffold {slug}")
    md = path.read_text(encoding="utf-8")
    rep = validate.validate(md, meta, segs, text, config.settings())
    (run / "validation.json").write_text(json.dumps({"errors": rep.errors, "warnings": rep.warnings}, indent=1),
                                         encoding="utf-8")
    return run, meta, md, rep


def cmd_check(a) -> None:
    *_, rep = _check(a.slug)
    for e in rep.errors:
        print("ERROR:", e)
    for w in rep.warnings:
        print("WARN: ", w)
    print("PASS" if rep.ok else f"FAIL — {len(rep.errors)} error(s)")
    sys.exit(0 if rep.ok else 1)


def cmd_render(a) -> None:
    run, meta, md, rep = _check(a.slug)
    if not rep.ok:
        for e in rep.errors:
            print("ERROR:", e)
        raise SystemExit("Not rendered: fix the errors above and re-run check.")
    out = config.ROOT / "summaries"
    out.mkdir(exist_ok=True)
    stem = f"{meta['published']}_{meta['id']}"
    (out / f"{stem}.md").write_text(render.link_stamps(md, meta["id"]), encoding="utf-8")
    (out / f"{stem}.html").write_text(render.to_html(md, meta), encoding="utf-8")
    read_min = max(1, round(len(validate.words(md)) / READ_WPM))
    print(f"{out / stem}.html\n{out / stem}.md\nVideo {round(meta['duration'] / 60)} min -> read ~{read_min} min")


def cmd_latest(a) -> None:
    for v in youtube.latest(a.source, a.n):
        print(f"{v['id']}  {v['published']}  {v['title'][:90]}")


def cmd_keys(a) -> None:
    for k, what in config.KEYS.items():
        print(f"{'set    ' if config.key(k, required=False) else 'MISSING'}  {k:<18} {what}")


def main(argv: list[str] | None = None) -> None:
    config.load_dotenv()
    p = argparse.ArgumentParser(prog="yw", description="YouTube Watcher: executive summaries from full transcripts")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("keys", help="show which API keys are set")
    s.set_defaults(fn=cmd_keys)

    s = sub.add_parser("fetch", help="metadata + full transcript + segments for one or more videos")
    s.add_argument("videos", nargs="+", help="YouTube URLs or 11-character ids")
    s.add_argument("--minutes", type=int, help="segment length when the video has no chapters")
    s.add_argument("--no-generate", action="store_true", help="never fall back to AI transcription")
    s.add_argument("--force", action="store_true")
    s.set_defaults(fn=cmd_fetch)

    s = sub.add_parser("latest", help="list newest videos of a channel (@handle/URL) or playlist")
    s.add_argument("source")
    s.add_argument("-n", type=int, default=5)
    s.set_defaults(fn=cmd_latest)

    s = sub.add_parser("info", help="video facts and the segment files to read")
    s.add_argument("slug")
    s.set_defaults(fn=cmd_info)

    s = sub.add_parser("resegment", help="re-split the transcript with a different window")
    s.add_argument("slug")
    s.add_argument("--minutes", type=int, required=True)
    s.set_defaults(fn=cmd_resegment)

    s = sub.add_parser("scaffold", help="write summary.md skeleton with header and one heading per segment")
    s.add_argument("slug")
    s.add_argument("--force", action="store_true")
    s.set_defaults(fn=cmd_scaffold)

    s = sub.add_parser("check", help="validate summary.md against the transcript")
    s.add_argument("slug")
    s.set_defaults(fn=cmd_check)

    s = sub.add_parser("render", help="validate, then write summaries/<date>_<id>.html and .md")
    s.add_argument("slug")
    s.set_defaults(fn=cmd_render)

    a = p.parse_args(argv)
    a.fn(a)
