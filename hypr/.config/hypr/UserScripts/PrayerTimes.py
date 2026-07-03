#!/usr/bin/env python3
# /* ---- 💫 https://github.com/JaKooLit 💫 ---- */  #
# Prayer Times Module for Waybar
# Uses AlAdhan API calendar endpoint for monthly caching
# Defaults to Jordan Ministry of Awqaf method (23) for Amman

import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
import requests
import html

# Paths
CONFIG_PATH = Path.home() / ".config/hypr/UserConfigs/PrayerTimes.conf"
CACHE_DIR = Path.home() / ".cache"
CACHE_PATH = CACHE_DIR / "prayer_times_cache.json"

HTTP_TIMEOUT = 10
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"

PRAYER_ORDER = ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]
DISPLAY_PRAYERS = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]


def esc(s):
    return html.escape(s, quote=False) if s else ""


def read_config():
    defaults = {
        "METHOD": "23",
        "SCHOOL": "0",
        "LAT": "31.9772",
        "LON": "35.8374",
        "CITY": "Amman",
    }

    if CONFIG_PATH.exists():
        try:
            with CONFIG_PATH.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, value = line.split("=", 1)
                        defaults[key.strip().upper()] = value.strip()
        except Exception as e:
            print(f"Error reading config: {e}", file=sys.stderr)

    try:
        method = int(defaults.get("METHOD", "23"))
        school = int(defaults.get("SCHOOL", "0"))
        lat = float(defaults.get("LAT", "31.9772"))
        lon = float(defaults.get("LON", "35.8374"))
        city = defaults.get("CITY", "Amman")
    except Exception as e:
        print(f"Error parsing config: {e}", file=sys.stderr)
        method, school, lat, lon, city = 23, 0, 31.9772, 35.8374, "Amman"

    return method, school, lat, lon, city


def check_network():
    return os.system("ping -c1 -W2 8.8.8.8 >/dev/null 2>&1") == 0


def read_cache():
    try:
        if CACHE_PATH.exists():
            with CACHE_PATH.open("r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error reading cache: {e}", file=sys.stderr)
    return None


def write_cache(data):
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        data["timestamp"] = time.time()
        with CACHE_PATH.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception as e:
        print(f"Error writing cache: {e}", file=sys.stderr)


def fetch_calendar(lat, lon, method, school, year, month):
    try:
        url = f"http://api.aladhan.com/v1/calendar/{year}/{month}"
        params = {
            "latitude": lat,
            "longitude": lon,
            "method": method,
            "school": school,
        }
        resp = requests.get(url, params=params, timeout=HTTP_TIMEOUT, headers={"User-Agent": UA})
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 200 and "data" in data:
                return data["data"]
    except Exception as e:
        print(f"Error fetching calendar: {e}", file=sys.stderr)
    return None


def parse_prayer_times(month_data):
    """Convert API month data to a dict: { "YYYY-MM-DD": { "Fajr": "HH:MM", ... } }"""
    result = {}
    if not month_data:
        return result

    for day in month_data:
        date_str = day.get("date", {}).get("gregorian", {}).get("date")
        if not date_str:
            continue
        # API returns DD-MM-YYYY, convert to YYYY-MM-DD
        try:
            d, m, y = date_str.split("-")
            iso_date = f"{y}-{m}-{d}"
        except Exception:
            continue

        timings = day.get("timings", {})
        prayers = {}
        for p in PRAYER_ORDER:
            raw = timings.get(p, "")
            # Timings sometimes include timezone like "04:30 (EET)"
            if "(" in raw:
                raw = raw.split("(")[0].strip()
            prayers[p] = raw

        result[iso_date] = prayers

    return result


def get_prayer_data_for_date(prayer_calendar, date_obj):
    date_str = date_obj.strftime("%Y-%m-%d")
    return prayer_calendar.get(date_str, {})


def get_next_prayer(prayer_times):
    now = datetime.now()
    current_time = now.time()

    # Check prayers in order for today
    for prayer in DISPLAY_PRAYERS:
        prayer_time_str = prayer_times.get(prayer)
        if not prayer_time_str:
            continue
        try:
            time_obj = datetime.strptime(prayer_time_str, "%H:%M").time()
            if time_obj > current_time:
                prayer_datetime = datetime.combine(now.date(), time_obj)
                return prayer, prayer_datetime
        except Exception as e:
            print(f"Error parsing prayer time {prayer}: {e}", file=sys.stderr)
            continue

    # All prayers passed today -> next Fajr tomorrow
    fajr_time_str = prayer_times.get("Fajr", "05:00")
    try:
        fajr_time = datetime.strptime(fajr_time_str, "%H:%M").time()
        fajr_datetime = datetime.combine(now.date() + timedelta(days=1), fajr_time)
        return "Fajr", fajr_datetime
    except Exception as e:
        print(f"Error parsing Fajr: {e}", file=sys.stderr)
        return "Fajr", None


def format_countdown(target_time):
    if not target_time:
        return "N/A"

    now = datetime.now()
    delta = target_time - now

    if delta.total_seconds() < 0:
        return "Now"

    hours = int(delta.total_seconds() // 3600)
    minutes = int((delta.total_seconds() % 3600) // 60)

    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m"
    else:
        return "Now"


def build_tooltip(prayer_times, city, next_prayer, countdown, hijri_date, stale=False):
    tooltip_lines = [
        f"Prayer Times for {city}",
        "",
        "Fajr:    " + prayer_times.get("Fajr", "N/A"),
        "Sunrise: " + prayer_times.get("Sunrise", "N/A"),
        "Dhuhr:   " + prayer_times.get("Dhuhr", "N/A"),
        "Asr:     " + prayer_times.get("Asr", "N/A"),
        "Maghrib: " + prayer_times.get("Maghrib", "N/A"),
        "Isha:    " + prayer_times.get("Isha", "N/A"),
        "",
        f"Next: {next_prayer} in {countdown}",
        f"Hijri: {hijri_date}",
    ]
    if stale:
        tooltip_lines.append("")
        tooltip_lines.append("Offline — using cached prayer times")
    return "\n".join(tooltip_lines)


def build_output(prayer_times, city, hijri_date, stale=False):
    next_prayer, next_time = get_next_prayer(prayer_times)
    countdown = format_countdown(next_time)

    stale_marker = " ⃠" if stale else ""

    return {
        "text": f"{next_prayer}: {countdown}{stale_marker}",
        "alt": next_prayer.lower(),
        "tooltip": build_tooltip(prayer_times, city, next_prayer, countdown, hijri_date, stale),
        "class": f"prayer-{next_prayer.lower()}",
    }


def get_hijri_date(month_data, day_index=0):
    try:
        day = month_data[day_index]
        return day.get("date", {}).get("hijri", {}).get("date", "N/A")
    except Exception:
        return "N/A"


def main():
    method, school, lat, lon, city = read_config()
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")

    cached = read_cache()
    cache_valid = False
    prayer_calendar = {}
    hijri_date = "N/A"

    if cached:
        cached_month = cached.get("month")
        cached_year = cached.get("year")
        prayer_calendar = cached.get("calendar", {})

        if cached_month == now.month and cached_year == now.year and prayer_calendar:
            cache_valid = True
            # Hijri date from cache first day
            hijri_date = cached.get("hijri_date", "N/A")

    if check_network():
        # Fetch fresh calendar if cache is missing or for a different month
        if not cache_valid:
            month_data = fetch_calendar(lat, lon, method, school, now.year, now.month)
            if month_data:
                prayer_calendar = parse_prayer_times(month_data)
                hijri_date = get_hijri_date(month_data)
                write_cache({
                    "month": now.month,
                    "year": now.year,
                    "calendar": prayer_calendar,
                    "hijri_date": hijri_date,
                    "city": city,
                    "method": method,
                    "school": school,
                })
                cache_valid = True

    # Use today's prayer times from calendar
    prayer_times = get_prayer_data_for_date(prayer_calendar, now)

    if prayer_times:
        output = build_output(prayer_times, city, hijri_date, stale=not check_network())
        print(json.dumps(output, ensure_ascii=False))
        return

    # Fallback: try to fetch today's timings directly if calendar failed
    if check_network():
        try:
            url = "http://api.aladhan.com/v1/timings"
            params = {"latitude": lat, "longitude": lon, "method": method, "school": school}
            resp = requests.get(url, params=params, timeout=HTTP_TIMEOUT, headers={"User-Agent": UA})
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 200:
                    timings = data["data"].get("timings", {})
                    hijri_date = data["data"].get("date", {}).get("hijri", {}).get("date", "N/A")
                    output = build_output(timings, city, hijri_date)
                    print(json.dumps(output, ensure_ascii=False))
                    return
        except Exception as e:
            print(f"Error fetching daily timings: {e}", file=sys.stderr)

    # No data available at all
    fallback = {
        "text": "N/A",
        "alt": "error",
        "tooltip": "Prayer times unavailable",
        "class": "error"
    }
    print(json.dumps(fallback, ensure_ascii=False))


if __name__ == "__main__":
    main()
