"""Shared HTTP session with retries."""
from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

UA = "YouTubeWatcher/0.1 (+executive summaries of public YouTube videos)"
TIMEOUT = 30


def session(retry_429: bool = True) -> requests.Session:
    """retry_429=False lets the caller read a 429's body (e.g. a spent plan quota) instead of retrying blindly."""
    s = requests.Session()
    retry = Retry(total=3, backoff_factor=1.5, status_forcelist=((429,) if retry_429 else ()) + (500, 502, 503, 504),
                  allowed_methods=("GET", "HEAD"))
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.headers["User-Agent"] = UA
    return s
