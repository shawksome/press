#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

RUMBLE_PAGE = "https://rumble.com/v7edga2-presstv-live.html"
OUTPUT = Path("presstv.m3u8")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://rumble.com/",
    "Origin": "https://rumble.com",
}

def get(url):
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=25) as response:
        return response.read()

def find_embed_id(html):
    patterns = [
        r"rumble\.com/embed/[0-9a-z]+\.([0-9a-z]+)",
        r'Rumble\(\s*["\']play["\']\s*,\s*\{[^}]*?["\']?video["\']?\s*:\s*["\']([0-9a-z]+)',
        r'["\']embedUrl["\']\s*:\s*["\']https?://(?:www\.)?rumble\.com/embed/(?:[0-9a-z]+\.)?([0-9a-z]+)',
        r"rumble\.com/embed/([0-9a-z]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.I | re.S)
        if match:
            return match.group(1).lower()
    return None

def get_metadata(video_id):
    query = urlencode({"request": "video", "ver": "2", "v": video_id})
    return json.loads(
        get(f"https://rumble.com/embedJS/u3/?{query}").decode("utf-8")
    )

def walk_strings(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from walk_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk_strings(item)
    elif isinstance(value, str):
        yield value

def find_hls(metadata):
    hls = metadata.get("ua", {}).get("hls")
    candidates = []

    if isinstance(hls, dict):
        for quality, info in hls.items():
            if not isinstance(info, dict):
                continue
            url = info.get("url")
            if not isinstance(url, str) or ".m3u8" not in url.lower():
                continue
            meta = info.get("meta") or {}
            height = meta.get("h")
            try:
                height = int(height or quality or 0)
            except (TypeError, ValueError):
                height = 0
            candidates.append({
                "url": url,
                "live": bool(meta.get("live")),
                "height": height,
            })

    live = [x for x in candidates if x["live"]]
    if live:
        return sorted(live, key=lambda x: x["height"], reverse=True)[0]["url"]

    if candidates:
        return sorted(candidates, key=lambda x: x["height"], reverse=True)[0]["url"]

    for value in walk_strings(metadata):
        if value.startswith(("https://", "http://")) and ".m3u8" in value.lower():
            return value

    return None

def main():
    print(f"Fetching {RUMBLE_PAGE}")
    html = get(RUMBLE_PAGE).decode("utf-8", errors="replace")
    video_id = find_embed_id(html)

    if not video_id:
        raise RuntimeError("Could not find the Rumble embed/video ID.")

    print(f"Rumble video ID: {video_id}")
    metadata = get_metadata(video_id)

    if metadata.get("sys", {}).get("msg"):
        print(f"Rumble message: {metadata['sys']['msg']}", file=sys.stderr)

    hls_url = find_hls(metadata)
    if not hls_url:
        raise RuntimeError("No HLS URL was found in Rumble metadata.")

    OUTPUT.write_text(
        "#EXTM3U\n"
        '#EXTINF:-1 tvg-id="presstv" tvg-name="PressTV Live" '
        'group-title="HilayTV | News",PressTV Live\n'
        f"{hls_url}\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT}")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
