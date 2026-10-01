"""Summary markdown -> self-contained HTML (and markdown) with timecodes linked to the video."""
from __future__ import annotations

import html
import re

import markdown

from . import config
from .validate import TS
from .youtube import watch_url

CSS = """
:root{--bg:#fbfaf7;--fg:#1d1d1b;--muted:#6b6862;--rule:#e4e1da;--accent:#b4232a;--chip:#f1eee7}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--fg:#ecebe7;--muted:#a19e97;--rule:#33322f;--accent:#ff6b6b;--chip:#252422}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,sans-serif}
main{max-width:760px;margin:0 auto;padding:32px 16px 64px}
h1{font-size:1.7rem;line-height:1.25;margin:.2em 0 .3em}h2{font-size:1.1rem;text-transform:uppercase;letter-spacing:.06em;margin:2.2em 0 .6em;padding-top:.8em;border-top:1px solid var(--rule)}
h3{font-size:1rem;margin:1.4em 0 .3em}em{color:var(--muted)}a{color:var(--accent)}
a.ts{font:500 .85em ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--chip);padding:1px 6px;border-radius:4px;text-decoration:none;white-space:nowrap}
img.thumb{width:100%;border-radius:8px;display:block;margin-bottom:12px}li{margin:.35em 0}blockquote{margin:0;padding-left:1em;border-left:3px solid var(--rule)}
"""


def link_stamps(md: str, vid: str) -> str:
    def sub(m):
        return f"[{m.group(0)[1:-1]}]({watch_url(vid, config.parse(m.group(1)))})"
    return TS.sub(sub, md)


def to_html(md: str, meta: dict, lang: str = "en") -> str:
    linked = link_stamps(md, meta["id"])
    body = markdown.markdown(linked, extensions=["extra", "sane_lists"])
    body = re.sub(r'<a href="(https://www\.youtube\.com/watch\?v=[\w-]+&amp;t=\d+s)"', r'<a class="ts" href="\1"', body)
    thumb = f'<a href="{meta["url"]}"><img class="thumb" alt="" src="https://i.ytimg.com/vi/{meta["id"]}/hqdefault.jpg"></a>'
    return (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" '
            f'content="width=device-width,initial-scale=1"><title>{html.escape(meta["title"][:80])}</title>'
            f'<style>{CSS}</style></head><body><main>{thumb}{body}</main></body></html>')
