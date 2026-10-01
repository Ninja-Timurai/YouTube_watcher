"""Summary markdown -> a publishable HTML page (and markdown) with timecodes linked to the video.

The page is written as an Artifact body: <title> and <style> first, no <html>/<head>/<body> of its own (the
publisher wraps it), every color a theme token, the thumbnail embedded as a data: URI so nothing loads from
other hosts.
"""
from __future__ import annotations

import base64
import html
import re

import markdown

from . import config
from .http import session
from .validate import TS
from .youtube import watch_url

FONTS = ("https://fonts.googleapis.com/css2?family=Rubik:wght@500;600&family=Spectral:ital,wght@0,400;0,600;1,400"
         "&family=JetBrains+Mono:wght@500&display=swap")

CSS = """
/* Layout: one reading column; timecodes as mono chips that jump into the video. */
:root{--bg:#f7f8fb;--fg:#1b1f2a;--muted:#5d6577;--rule:#dde1ea;--accent:#2f4b9a;--chip:#e7ebf5;
--display:"Rubik",system-ui,sans-serif;--body:"Spectral",Georgia,serif;--mono:"JetBrains Mono",ui-monospace,Menlo,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#12151c;--fg:#e6e9f0;--muted:#9aa3b5;
--rule:#2a303d;--accent:#9db4ff;--chip:#1f2533;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#12151c;--fg:#e6e9f0;--muted:#9aa3b5;--rule:#2a303d;--accent:#9db4ff;--chip:#1f2533;
color-scheme:dark}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--fg);font:1.0625rem/1.65 var(--body);margin:0}
main{max-width:44rem;margin:0 auto;padding-inline:16px;padding-block:2rem 4rem}
h1,h2,h3{font-family:var(--display);text-wrap:balance;line-height:1.25}
h1{font-size:1.65rem;font-weight:600;margin:.4rem 0 .5rem}
h2{font-size:.8rem;font-weight:600;text-transform:uppercase;letter-spacing:.09em;color:var(--muted);
margin:2.4rem 0 .8rem;padding-top:1rem;border-top:1px solid var(--rule)}
h3{font-size:1.02rem;font-weight:500;margin:1.6rem 0 .3rem}
p,li{max-width:65ch}em{color:var(--muted);font-size:.92rem}
a{color:var(--accent);text-underline-offset:2px}a:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
a.ts{font:500 .78rem var(--mono);background:var(--chip);padding:.1rem .4rem;border-radius:4px;text-decoration:none;
white-space:nowrap;font-variant-numeric:tabular-nums}
ul{padding-left:1.2rem}li{margin:.45rem 0}
.thumb{display:block;max-width:100%;border-radius:6px;margin-bottom:.5rem}
.meta{font:500 .8rem var(--mono);color:var(--muted);font-variant-numeric:tabular-nums}
"""


def link_stamps(md: str, vid: str) -> str:
    def sub(m):
        return f"[{m.group(0)[1:-1]}]({watch_url(vid, config.parse(m.group(1)))})"
    return TS.sub(sub, md)


def page_title(title: str) -> str:
    """A short name for the tab and gallery: the video title up to its first separator."""
    short = re.split(r"\s[|•–—-]\s|[.!?]\s", title, maxsplit=1)[0].strip()
    return short if 3 <= len(short) <= 70 else title[:70].rstrip()


def _thumb(vid: str) -> str:
    try:
        r = session().get(f"https://i.ytimg.com/vi/{vid}/mqdefault.jpg", timeout=15)
        if r.status_code == 200 and r.headers.get("content-type", "").startswith("image/"):
            return "data:image/jpeg;base64," + base64.b64encode(r.content).decode()
    except Exception:
        pass
    return ""


def to_html(md: str, meta: dict, lang: str = "en", read_min: int = 0) -> str:
    body = markdown.markdown(link_stamps(md, meta["id"]), extensions=["extra", "sane_lists"])
    body = re.sub(r'<a href="(https://www\.youtube\.com/watch\?v=[\w-]+&amp;t=\d+s)"', r'<a class="ts" href="\1"', body)
    src = _thumb(meta["id"])
    thumb = f'<a href="{meta["url"]}"><img class="thumb" alt="" src="{src}"></a>' if src else ""
    stat = (f'<p class="meta">▶ {config.fmt(meta["duration"])} → ~{read_min} min</p>' if read_min else "")
    return (f'<title>{html.escape(page_title(meta["title"]))}</title>\n<meta charset="utf-8">\n'
            f'<link rel="stylesheet" href="{FONTS}">\n<style>{CSS}</style>\n'
            f'<main lang="{lang}">{thumb}{stat}{body}</main>\n')
