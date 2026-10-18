#!/usr/bin/env python3
"""Fetch today's events from official Tokyo venue pages where structured
Event data is available, and update events.json.
"""
import json
import re
from datetime import date, datetime, timezone, timedelta
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "events.json"
JST = timezone(timedelta(hours=9))

SOURCES = [
    {
        "venue": "東京ドーム",
        "title": "東京ドーム｜イベントスケジュール",
        "url": "https://www.tokyo-dome.co.jp/dome/event/schedule.html",
        "description": "東京ドームの公式イベント情報",
    },
    {
        "venue": "東京ビッグサイト",
        "title": "東京ビッグサイト｜イベント情報",
        "url": "https://www.bigsight.jp/visitor/event/",
        "description": "展示会・イベントの公式開催情報",
    },
    {
        "venue": "日本武道館",
        "title": "日本武道館｜公式サイト",
        "url": "https://www.nipponbudokan.or.jp/",
        "description": "日本武道館の公式情報",
    },
    {
        "venue": "有明アリーナ",
        "title": "有明アリーナ｜公式サイト",
        "url": "https://ariake-arena.tokyo/",
        "description": "有明アリーナの公式情報",
    },
    {
        "venue": "東京ガーデンシアター",
        "title": "東京ガーデンシアター｜イベント情報",
        "url": "https://www.shopping-sumitomo-rd.com/tokyo_garden_theater/",
        "description": "東京ガーデンシアターの公式情報",
    },
    {
        "venue": "TOYOTA ARENA TOKYO",
        "title": "TOYOTA ARENA TOKYO｜公式サイト",
        "url": "https://www.toyota-arena-tokyo.jp/",
        "description": "TOYOTA ARENA TOKYOの公式情報",
    },
]


class JsonLdParser(HTMLParser):
    """Collect JSON-LD scripts without third-party dependencies."""

    def __init__(self):
        super().__init__()
        self.in_jsonld = False
        self.parts = []
        self.documents = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "script":
            return
        attrs = dict(attrs)
        if "ld+json" in attrs.get("type", "").lower():
            self.in_jsonld = True
            self.parts = []

    def handle_data(self, data):
        if self.in_jsonld:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "script" and self.in_jsonld:
            raw = "".join(self.parts).strip()
            if raw:
                try:
                    self.documents.append(json.loads(raw))
                except json.JSONDecodeError:
                    pass
            self.in_jsonld = False
            self.parts = []


def fetch_page(url):
    request = Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; TokyoTaxiEventBot/1.0)"},
    )
    with urlopen(request, timeout=20) as response:
        return response.read().decode(
            response.headers.get_content_charset() or "utf-8",
            errors="replace",
        )


def walk_objects(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_objects(child)


def is_event(obj):
    types = obj.get("@type", [])
    if isinstance(types, str):
        types = [types]
    return any(str(item).lower().endswith("event") for item in types)


def parse_datetime(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=JST)
        return parsed.astimezone(JST)
    except (ValueError, TypeError):
        return None


def extract_events(document, source, today):
    found = []
    seen = set()

    for obj in walk_objects(document):
        if not is_event(obj):
            continue

        title = obj.get("name")
        start_raw = obj.get("startDate")
        end_raw = obj.get("endDate")
        start = parse_datetime(start_raw)
        end = parse_datetime(end_raw)

        # Date-only values are handled as JST calendar dates.
        start_date = start.date() if start else None
        end_date = end.date() if end else start_date

        if start_date is None:
            continue
        if not (start_date <= today <= (end_date or start_date)):
            continue
        if not title:
            continue

        event_url = obj.get("url") or source["url"]
        if isinstance(event_url, dict):
            event_url = event_url.get("@id", source["url"])

        key = (source["venue"], str(title), str(start_raw))
        if key in seen:
            continue
        seen.add(key)

        found.append({
            "date": today.isoformat(),
            "venue": source["venue"],
            "title": str(title),
            "start_time": start.strftime("%H:%M") if start else None,
            "end_time": end.strftime("%H:%M") if end else None,
            "source_url": str(event_url),
        })

    return found


def main():
    today = datetime.now(JST).date()
    events = []
    sources = []

    for original in SOURCES:
        source = dict(original)
        try:
            html = fetch_page(source["url"])
            parser = JsonLdParser()
            parser.feed(html)

            print(f'{source["venue"]}: HTML length = {len(html)}')
            print(f'{source["venue"]}: JSON-LD documents = {len(parser.documents)}')
            if source["venue"] == "東京ドーム":
                for keyword in ["2026", "10月", "イベント", "公演", "schedule"]:
                    print(
                        f'東京ドーム: "{keyword}" '
                        f'count = {html.lower().count(keyword.lower())}'
                    )
            source["available_at_last_check"] = True
            source["events_found_today"] = 0

            for document in parser.documents:
                events.extend(extract_events(document, source, today))

            source["events_found_today"] = sum(
                1 for event in events if event["venue"] == source["venue"]
            )
            print(
                f'{source["venue"]}: '
                f'{source["events_found_today"]} event(s) found'
            )

        except Exception as exc:
            source["available_at_last_check"] = False
            source["error"] = str(exc)
            print(f'Warning: {source["venue"]}: {exc}')

        sources.append(source)

    events.sort(key=lambda event: (
        event.get("start_time") or "99:99",
        event["venue"],
        event["title"],
    ))

    data = {
        "updated_at_jst": datetime.now(JST).strftime("%Y-%m-%d %H:%M"),
        "date": today.isoformat(),
        "note": (
            "公式ページから取得できた構造化イベント情報です。"
            "掲載形式によってはイベントが抽出されない場合があります。"
        ),
        "events": events,
        "sources": sources,
    }

    DATA_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Updated {DATA_FILE} at {data['updated_at_jst']} JST")
    print(f"Today's events: {len(events)}")


if __name__ == "__main__":
    main()
