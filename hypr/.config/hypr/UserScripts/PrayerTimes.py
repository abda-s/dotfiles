#!/usr/bin/env python3
# /* ---- 💫 https://github.com/JaKooLit 💫 ---- */  #
# Prayer Times Module for Waybar
# Uses AlAdhan API (free, no API key)
# Auto-detects location and displays next prayer countdown

import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
import requests
import html

# Configuration
CACHE_DIR = Path.home() / ".cache"
API_CACHE_PATH = CACHE_DIR / "prayer_times_cache.json"
CACHE_TTL_SECONDS = 300  # 5 minutes

PRAYER_ICONS = {
    "Fajr": "",
    "Sunrise": "",
    "Dhuhr": "",
    "Asr": "",
    "Maghrib": "",
    "Isha": "",
    "default": ""
}

HTTP_TIMEOUT = 8
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"

def esc(s):
    return html.escape(s, quote=False) if s else ""

def check_network():
    if os.system("ping -c1 -W2 8.8.8.8 >/dev/null 2>&1") == 0:
        return True
    if os.system("ping -c1 -W2 1.1.1.1 >/dev/null 2>&1") == 0:
        return True
    try:
        if requests.get("https://ipinfo.io", timeout=3).status_code == 200:
            return True
    except:
        pass
    return False

def get_coords_from_ipwho():
    try:
        resp = requests.get("https://ipwho.is/", timeout=HTTP_TIMEOUT, headers={"User-Agent": UA})
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success"):
                return data.get("latitude"), data.get("longitude"), data.get("city")
    except Exception as e:
        print(f"ipwho.is failed: {e}", file=sys.stderr)
    return None, None, None

def get_coords_from_ipapi():
    try:
        resp = requests.get("https://ipapi.co/json", timeout=HTTP_TIMEOUT, headers={"User-Agent": UA})
        if resp.status_code == 200:
            data = resp.json()
            return data.get("latitude"), data.get("longitude"), data.get("city")
    except Exception as e:
        print(f"ipapi.co failed: {e}", file=sys.stderr)
    return None, None, None

def get_coords_from_ipinfo():
    try:
        resp = requests.get("https://ipinfo.io/json", timeout=HTTP_TIMEOUT, headers={"User-Agent": UA})
        if resp.status_code == 200:
            data = resp.json()
            loc = data.get("loc")
            city = data.get("city")
            if loc and "," in loc:
                lat, lon = loc.split(",", 1)
                return float(lat), float(lon), city
    except Exception as e:
        print(f"ipinfo.io failed: {e}", file=sys.stderr)
    return None, None, None

def get_coords():
    cached = read_cache()
    if cached and "lat" in cached and "lon" in cached and "city" in cached:
        return cached["lat"], cached["lon"], cached["city"]

    lat, lon, city = get_coords_from_ipwho() or get_coords_from_ipapi() or get_coords_from_ipinfo()

    if lat and lon:
        if not city:
            city = f"{lat:.3f}, {lon:.3f}"
        return lat, lon, city

    return 21.4225, 39.8262, "Mecca"  # Fallback to Mecca

def read_cache():
    try:
        if API_CACHE_PATH.exists():
            with API_CACHE_PATH.open("r", encoding="utf-8") as f:
                data = json.load(f)
                timestamp = data.get("timestamp", 0)
                if (time.time() - timestamp) <= CACHE_TTL_SECONDS:
                    return data
    except Exception as e:
        print(f"Error reading cache: {e}", file=sys.stderr)
    return None

def write_cache(data):
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        data["timestamp"] = time.time()
        with API_CACHE_PATH.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception as e:
        print(f"Error writing cache: {e}", file=sys.stderr)

def fetch_prayer_times(lat, lon):
    try:
        url = f"http://api.aladhan.com/v1/timings"
        params = {
            "latitude": lat,
            "longitude": lon,
            "method": 2,  # Islamic Society of North America (ISNA)
            "school": 1,  # Hanafi
        }
        resp = requests.get(url, params=params, timeout=HTTP_TIMEOUT, headers={"User-Agent": UA})
        if resp.status_code == 200:
            data = resp.json()
            return data["data"]
    except Exception as e:
        print(f"Error fetching prayer times: {e}", file=sys.stderr)
    return None

def get_next_prayer(prayer_times):
    now = datetime.now()
    current_time = now.time()

    prayers = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]

    # Find the next prayer that hasn't passed yet
    for prayer in prayers:
        prayer_time_str = prayer_times.get(prayer)
        if prayer_time_str:
            try:
                time_obj = datetime.strptime(prayer_time_str, "%H:%M").time()

                # If prayer time is today and hasn't passed, return it
                if time_obj > current_time:
                    prayer_datetime = datetime.combine(now.date(), time_obj)
                    return prayer, prayer_datetime
            except Exception as e:
                print(f"Error parsing prayer time {prayer}: {e}", file=sys.stderr)
                continue

    # If all prayers have passed today, return Fajr tomorrow
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

    # Handle case where target_time might be in the past
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

def build_tooltip(prayer_times, city, next_prayer, countdown, hijri_date):
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
        f"Hijri: {hijri_date}"
    ]
    return "\n".join(tooltip_lines)

def main():
    if not check_network():
        offline_output = {
            "text": "Offline",
            "alt": "offline",
            "tooltip": "No network connection",
            "class": "offline"
        }
        print(json.dumps(offline_output, ensure_ascii=False))
        return

    lat, lon, city = get_coords()

    cached = read_cache()
    if cached and "prayer_times" in cached:
        prayer_data = cached["prayer_times"]
        date_str = cached.get("date", "")
        today = datetime.now().strftime("%Y-%m-%d")

        if date_str == today:
            prayer_times = prayer_data.get("timings", {})
            date_data = prayer_data.get("date", {})
            hijri_date = date_data.get("hijri", {}).get("date", "N/A")

            next_prayer, next_time = get_next_prayer(prayer_times)
            countdown = format_countdown(next_time)
            icon = PRAYER_ICONS.get(next_prayer, PRAYER_ICONS['default'])

            output = {
                "text": f"{next_prayer}: {countdown}",
                "alt": next_prayer.lower(),
                "tooltip": build_tooltip(prayer_times, city, next_prayer, countdown, hijri_date),
                "class": f"prayer-{next_prayer.lower()}"
            }
            print(json.dumps(output, ensure_ascii=False))
            return

    prayer_data = fetch_prayer_times(lat, lon)
    if prayer_data:
        prayer_times = prayer_data.get("timings", {})
        date_data = prayer_data.get("date", {})
        hijri_date = date_data.get("hijri", {}).get("date", "N/A")
        today = datetime.now().strftime("%Y-%m-%d")

        cache_data = {
            "lat": lat,
            "lon": lon,
            "city": city,
            "prayer_times": prayer_data,
            "date": today
        }
        write_cache(cache_data)

        next_prayer, next_time = get_next_prayer(prayer_times)
        countdown = format_countdown(next_time)

        output = {
            "text": f"{next_prayer}: {countdown}",
            "alt": next_prayer.lower(),
            "tooltip": build_tooltip(prayer_times, city, next_prayer, countdown, hijri_date),
            "class": f"prayer-{next_prayer.lower()}"
        }
        print(json.dumps(output, ensure_ascii=False))
        return

    fallback = {
        "text": "N/A",
        "alt": "error",
        "tooltip": "Prayer times unavailable",
        "class": "error"
    }
    print(json.dumps(fallback, ensure_ascii=False))

if __name__ == "__main__":
    main()
