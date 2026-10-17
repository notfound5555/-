#!/usr/bin/env python3
"""Refresh official event-source links and update the Japan-time timestamp.
This deliberately does not claim to scrape every event listing: source sites may
change their page structures or restrict automated access.
"""
import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "events.json"
JST = timezone(timedelta(hours=9))

SOURCES = [
    {
        "title": "東京都公式 My TOKYO｜イベント情報",
        "url": "https://www.my.metro.tokyo.lg.jp/event/",
        "description": "東京都の公式イベント情報。開催日や詳細はリンク先で確認。",
    },
    {
        "title": "GO TOKYO｜東京イベントカレンダー",
        "url": "https://www.gotokyo.org/jp/calendar/index.html",
        "description": "東京観光公式サイトのイベントカレンダー。",
    },
    {
        "title": "東京ビッグサイト｜イベント情報",
        "url": "https://www.bigsight.jp/visitor/event/",
        "description": "展示会・イベントの開催予定。",
    },
    {
        "title": "東京ドームシティ｜公式サイト",
        "url": "https://www.tokyo-dome.co.jp/",
        "description": "公演・イベント情報は公式サイトで確認。",
    },
    {
        "title": "日本武道館｜公式サイト",
        "url": "https://www.nipponbudokan.or.jp/",
        "description": "公演情報は公式サイトで確認。",
    },
    {
        "title": "有明アリーナ｜公式サイト",
        "url": "https://ariake-arena.tokyo/",
        "description": "イベント・公演情報は公式サイトで確認。",
    },
]

def check_url(url):
    try:
        req = Request(url, headers={"User-Agent": "HANEDA-TAXI-LIVE-event-link-check/1.0"})
        with urlopen(req, timeout=15) as response:
            return 200 <= response.status < 400
    except Exception as exc:
        print(f"Warning: could not check {url}: {exc}")
        return False

def main():
    # Link checking is best-effort; keep official links even if a host temporarily fails.
    for source in SOURCES:
        source["available_at_last_check"] = check_url(source["url"])
    data = {
        "updated_at_jst": datetime.now(JST).strftime("%Y-%m-%d %H:%M"),
        "note": "公式イベント掲載ページへのリンク集です。イベント全件・開催時間の自動抽出を保証するものではありません。",
        "sources": SOURCES,
    }
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Updated {DATA_FILE} at {data['updated_at_jst']} JST")

if __name__ == "__main__":
    main()
