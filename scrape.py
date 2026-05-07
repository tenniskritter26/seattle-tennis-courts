#!/usr/bin/env python3
"""
Seattle Tennis Court Reservation Scraper

Queries the Active.com / Seattle Parks API for tomorrow's court availability.
The API shows available (bookable) time slots; the gaps between them are reservations.
Run nightly at 11:30 PM Pacific so "tomorrow" data becomes "today" data after midnight.
"""

import json
import os
import time
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

BASE_URL = "https://anc.apm.activecommunities.com/seattle/rest/reservation/resource/availability/daily"

COURTS = {
    "Bryant Playground": [
        {"id": 1325, "name": "Court 01"},
        {"id": 1326, "name": "Court 02"},
    ],
    "Froula Playground": [
        {"id": 1339, "name": "Court 01"},
        {"id": 1340, "name": "Court 02"},
    ],
    "Laurelhurst Playfield": [
        {"id": 1353, "name": "Court 01"},
        {"id": 1354, "name": "Court 02"},
        {"id": 1355, "name": "Court 03"},
        {"id": 1356, "name": "Court 04"},
    ],
    "Lower Woodland Playfield": [
        {"id": 353, "name": "Court 01"},
        {"id": 354, "name": "Court 02"},
        {"id": 355, "name": "Court 03"},
        {"id": 356, "name": "Court 04"},
        {"id": 357, "name": "Court 05"},
        {"id": 358, "name": "Court 06"},
        {"id": 359, "name": "Court 07"},
        {"id": 360, "name": "Court 08"},
        {"id": 361, "name": "Court 09"},
        {"id": 362, "name": "Court 10"},
    ],
    "Lower Woodland Playfield — Upper Courts": [
        {"id": 369, "name": "Upper Court 01"},
        {"id": 370, "name": "Upper Court 02"},
        {"id": 371, "name": "Upper Court 03"},
    ],
    "Meadowbrook Playfield": [
        {"id": 1367, "name": "Court 01"},
        {"id": 1368, "name": "Court 02"},
        {"id": 1369, "name": "Court 03"},
        {"id": 1370, "name": "Court 04"},
        {"id": 1371, "name": "Court 05"},
        {"id": 1372, "name": "Court 06"},
    ],
    "Montlake Playfield": [
        {"id": 1375, "name": "Court 01"},
        {"id": 1376, "name": "Court 02"},
    ],
    "Volunteer Park": [
        {"id": 365, "name": "Court 01 — Upper"},
        {"id": 366, "name": "Court 02 — Upper"},
        {"id": 363, "name": "Court 03 — Lower"},
        {"id": 364, "name": "Court 04 — Lower"},
    ],
    "Wallingford Playfield": [
        {"id": 1408, "name": "Court 01"},
        {"id": 1409, "name": "Court 02"},
    ],
}

WINDOW_START_MIN = 8 * 60   # 8:00 AM in minutes
WINDOW_END_MIN   = 16 * 60  # 4:00 PM in minutes

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 (compatible; SeattleTennisDashboard/1.0)",
    "Referer": "https://anc.apm.activecommunities.com/seattle/reservation/search",
}


def t_to_min(t_str):
    """Convert 'HH:MM:SS' to minutes since midnight."""
    h, m, _ = t_str.split(":")
    return int(h) * 60 + int(m)


def min_to_hhmm(minutes):
    """Convert minutes since midnight to 'H:MM' display string."""
    h = minutes // 60
    m = minutes % 60
    suffix = "am" if h < 12 else "pm"
    display_h = h if h <= 12 else h - 12
    if display_h == 0:
        display_h = 12
    return f"{display_h}:{m:02d}{suffix}"


def compute_reserved(available_times):
    """
    Given the API's available-to-book time slots, return reserved intervals
    within the 8 AM–4 PM window. Gaps in available slots = reservations.
    """
    clipped = []
    for slot in available_times:
        if not slot.get("available", True):
            continue
        s = max(t_to_min(slot["start_time"]), WINDOW_START_MIN)
        e = min(t_to_min(slot["end_time"]),   WINDOW_END_MIN)
        if s < e:
            clipped.append((s, e))
    clipped.sort()

    reserved = []
    cursor = WINDOW_START_MIN
    for s, e in clipped:
        if s > cursor:
            reserved.append({
                "start": min_to_hhmm(cursor),
                "end":   min_to_hhmm(s),
                "start_min": cursor,
                "end_min":   s,
            })
        cursor = max(cursor, e)
    if cursor < WINDOW_END_MIN:
        reserved.append({
            "start": min_to_hhmm(cursor),
            "end":   min_to_hhmm(WINDOW_END_MIN),
            "start_min": cursor,
            "end_min":   WINDOW_END_MIN,
        })
    return reserved


def fetch_availability(resource_id, date_str):
    url = f"{BASE_URL}/{resource_id}"
    params = {
        "start_date": date_str,
        "end_date":   date_str,
        "customer_id": 0,
        "company_id":  0,
        "event_type_id": -1,
        "attendee": 1,
        "no_cache": "true",
        "locale": "en-US",
    }
    resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()


def main():
    pacific = ZoneInfo("America/Los_Angeles")
    now = datetime.now(pacific)
    target_date = (now + timedelta(days=1)).date()
    date_str = target_date.isoformat()

    print(f"Fetching availability for {date_str} (captured at {now.strftime('%Y-%m-%d %I:%M %p %Z')})")

    result = {
        "date": date_str,
        "captured_at": now.isoformat(),
        "captured_at_display": now.strftime("%B %-d, %Y at %-I:%M %p %Z"),
        "window": "8:00am – 4:00pm",
        "parks": {},
    }

    total_courts = 0
    total_reserved = 0

    for park_name, courts in COURTS.items():
        park_data = {"courts": {}}
        for court in courts:
            total_courts += 1
            try:
                data = fetch_availability(court["id"], date_str)
                daily = data["body"]["details"]["daily_details"]

                if not daily:
                    park_data["courts"][court["name"]] = {
                        "resource_id": court["id"],
                        "status": "no_data",
                        "available_slots": [],
                        "reserved_in_window": [],
                    }
                    continue

                day = daily[0]
                times = day.get("times", [])
                reserved = compute_reserved(times)

                if reserved:
                    total_reserved += 1

                park_data["courts"][court["name"]] = {
                    "resource_id": court["id"],
                    "status": day["status"],
                    "available_slots": [
                        {
                            "start": slot["start_time"][:5],
                            "end":   slot["end_time"][:5],
                            "start_min": t_to_min(slot["start_time"]),
                            "end_min":   t_to_min(slot["end_time"]),
                        }
                        for slot in times if slot.get("available", True)
                    ],
                    "reserved_in_window": reserved,
                }
                print(f"  ✓ {park_name} / {court['name']}: {len(reserved)} reserved block(s)")
            except Exception as exc:
                print(f"  ✗ {park_name} / {court['name']}: ERROR — {exc}")
                park_data["courts"][court["name"]] = {
                    "resource_id": court["id"],
                    "status": "error",
                    "error": str(exc),
                    "available_slots": [],
                    "reserved_in_window": [],
                }
            time.sleep(0.25)

        result["parks"][park_name] = park_data

    result["summary"] = {
        "total_courts": total_courts,
        "courts_with_reservations": total_reserved,
        "courts_fully_free": total_courts - total_reserved,
    }

    os.makedirs("data", exist_ok=True)
    with open("data/reservations.json", "w") as f:
        json.dump(result, f, indent=2)

    print(f"\nDone. {total_reserved}/{total_courts} courts have reservations.")
    print(f"Saved → data/reservations.json")


if __name__ == "__main__":
    main()
