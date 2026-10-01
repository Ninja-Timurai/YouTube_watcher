"""YouTube Data API v3: video metadata, description chapters, channel and playlist listing."""
from __future__ import annotations

import re
from urllib.parse import parse_qs, urlsplit

from . import config
from .http import TIMEOUT, session

API = "https://www.googleapis.com/youtube/v3"
_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
_DUR = re.compile(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")
_CHAPTER = re.compile(r"^\s*(?:[-•*▶►]\s*)?\(?((?:\d{1,2}:)?\d{1,2}:\d{2})\)?\s*[-–—:|.)]*\s*(.+?)\s*$")


def video_id(url_or_id: str) -> str:
    s = url_or_id.strip()
    if _ID.match(s):
        return s
    p = urlsplit(s if "://" in s else "https://" + s)
    host = p.netloc.lower().removeprefix("www.").removeprefix("m.")
    if host == "youtu.be":
        vid = p.path.strip("/").split("/")[0]
    elif host.endswith("youtube.com"):
        vid = parse_qs(p.query).get("v", [""])[0]
        if not vid:
            m = re.match(r"^/(?:shorts|live|embed|v)/([A-Za-z0-9_-]{11})", p.path)
            vid = m.group(1) if m else ""
    else:
        vid = ""
    if not _ID.match(vid):
        raise SystemExit(f"Not a YouTube video link: {url_or_id}")
    return vid


def watch_url(vid: str, at: int | None = None) -> str:
    return f"https://www.youtube.com/watch?v={vid}" + (f"&t={at}s" if at is not None else "")


def iso_duration(d: str) -> int:
    m = _DUR.fullmatch(d or "")
    if not m:
        return 0
    days, h, mi, s = (int(x or 0) for x in m.groups())
    return days * 86400 + h * 3600 + mi * 60 + s


def chapters(description: str, duration: int) -> list[dict]:
    """Creator chapters from the description, as YouTube itself derives them: lines starting with a timecode,
    the first at 0:00, at least three, ascending. Returns [{start, end, title}] or []."""
    found = []
    for line in description.splitlines():
        m = _CHAPTER.match(line)
        if m and m.group(2).strip():
            found.append((config.parse(m.group(1)), m.group(2).strip()))
    if len(found) < 3 or found[0][0] != 0 or any(b[0] <= a[0] for a, b in zip(found, found[1:])):
        return []
    if duration and found[-1][0] >= duration:
        return []
    ends = [f[0] for f in found[1:]] + [duration or found[-1][0] + 60]
    return [{"start": s, "end": e, "title": t} for (s, t), e in zip(found, ends)]


def _get(path: str, **params) -> dict:
    params["key"] = config.key("YOUTUBE_API_KEY")
    r = session().get(f"{API}/{path}", params=params, timeout=TIMEOUT)
    if r.status_code != 200:
        try:
            msg = r.json()["error"]["message"]
        except Exception:
            msg = r.text[:200]
        raise SystemExit(f"YouTube API {path}: HTTP {r.status_code}: {msg}")
    return r.json()


def metadata(vid: str) -> dict:
    items = _get("videos", part="snippet,contentDetails,statistics", id=vid).get("items", [])
    if not items:
        raise SystemExit(f"Video {vid} not found, private, or removed.")
    it = items[0]
    sn, cd, st = it.get("snippet", {}), it.get("contentDetails", {}), it.get("statistics", {})
    duration = iso_duration(cd.get("duration", ""))
    desc = sn.get("description", "")
    return {
        "id": vid,
        "url": watch_url(vid),
        "title": sn.get("title", ""),
        "channel": sn.get("channelTitle", ""),
        "channel_id": sn.get("channelId", ""),
        "published": sn.get("publishedAt", "")[:10],
        "duration": duration,
        "description": desc,
        "tags": sn.get("tags", []),
        "language": sn.get("defaultAudioLanguage") or sn.get("defaultLanguage") or "",
        "live": sn.get("liveBroadcastContent", "none"),
        "views": int(st.get("viewCount", 0) or 0),
        "likes": int(st.get("likeCount", 0) or 0),
        "chapters": chapters(desc, duration),
    }


def _uploads_playlist(channel: str) -> str:
    """Uploads playlist of a channel given as @handle, channel URL or UC... id."""
    c = channel.strip()
    if "youtube.com" in c:
        path = urlsplit(c if "://" in c else "https://" + c).path.strip("/").split("/")
        c = path[1] if path[0] in ("channel", "c", "user") and len(path) > 1 else path[0]
    if c.startswith("UC") and len(c) == 24:
        q = {"id": c}
    elif c.startswith("@"):
        q = {"forHandle": c}
    else:
        q = {"forUsername": c}
    items = _get("channels", part="contentDetails", **q).get("items", [])
    if not items and "forUsername" in q:
        items = _get("channels", part="contentDetails", forHandle="@" + c).get("items", [])
    if not items:
        raise SystemExit(f"Channel not found: {channel}")
    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]


def latest(source: str, n: int) -> list[dict]:
    """Newest-first videos from a channel (@handle / URL / id) or a playlist (URL with list= / PL... id)."""
    qs = parse_qs(urlsplit(source).query) if "://" in source else {}
    playlist = qs.get("list", [""])[0] or (source if re.match(r"^(PL|UU|OL|FL)[\w-]{10,}$", source) else "")
    playlist = playlist or _uploads_playlist(source)
    out, token = [], None
    while len(out) < n:
        params = {"part": "snippet,contentDetails", "playlistId": playlist, "maxResults": min(50, n - len(out))}
        if token:
            params["pageToken"] = token
        body = _get("playlistItems", **params)
        for it in body.get("items", []):
            sn = it.get("snippet", {})
            vid = it.get("contentDetails", {}).get("videoId")
            if vid and sn.get("title") not in ("Private video", "Deleted video"):
                out.append({"id": vid, "url": watch_url(vid), "title": sn.get("title", ""),
                            "published": (it["contentDetails"].get("videoPublishedAt") or sn.get("publishedAt", ""))[:10]})
        token = body.get("nextPageToken")
        if not token:
            break
    return out[:n]
