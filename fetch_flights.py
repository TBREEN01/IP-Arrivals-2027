"""
Adaptive flight status poller.

Runs every 10 minutes via GitHub Actions, but only actually calls the
AeroDataBox API for a given flight when it's "due" based on how close
it is to its scheduled arrival time. This keeps API usage low while
still giving near-real-time updates for flights that are about to land.

Polling tiers (minutes before/after scheduled arrival -> check interval):
  > 3 hours out            -> every 60 min
  30 min - 3 hours out     -> every 20 min
  30 min out to 1 hr after -> every 8 min   (near-real-time window)
  > 1 hr after scheduled   -> every 4 hours (assume landed, stop hammering)
"""
import json
import os
import sys
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

RAPIDAPI_KEY = os.environ.get("AERODATABOX_KEY", "")
HOST = "aerodatabox.p.rapidapi.com"
TZ = ZoneInfo("America/New_York")

SOURCE_FILE = "flights_source.json"
STATE_FILE = "state.json"
OUTPUT_FILE = "data.json"


def load_json(path, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def scheduled_dt(date_str, time_str):
    h, m = map(int, time_str.split(":"))
    d = datetime.strptime(date_str, "%Y-%m-%d")
    return datetime(d.year, d.month, d.day, h, m, tzinfo=TZ)


def poll_interval_minutes(scheduled, now):
    delta_min = (scheduled - now).total_seconds() / 60
    if delta_min > 180:
        return 60
    elif delta_min > 30:
        return 20
    elif delta_min > -60:
        return 8
    else:
        return 240


def due_for_check(key, scheduled, now, state):
    last = state.get(key)
    interval = poll_interval_minutes(scheduled, now)
    if last is None:
        return True
    last_dt = datetime.fromisoformat(last)
    return (now - last_dt).total_seconds() / 60 >= interval


def call_api(flight_num, date_str):
    url = f"https://{HOST}/flights/number/{flight_num}/{date_str}"
    req = urllib.request.Request(
        url,
        headers={
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": HOST,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode())
            if isinstance(body, list) and body:
                return body[0]
            if isinstance(body, dict):
                return body
            return None
    except Exception as e:
        return {"_error": str(e)}


def main():
    date_str = sys.argv[1] if len(sys.argv) > 1 else datetime.now(TZ).strftime("%Y-%m-%d")
    source = load_json(SOURCE_FILE, [])
    state = load_json(STATE_FILE, {})
    output = load_json(OUTPUT_FILE, {"flights": {}})
    now = datetime.now(TZ)

    calls_made = 0

    for row in source:
        flight_num = row["flight"]
        time_str = row["time"]
        key = f"{flight_num}_{time_str}"
        sched = scheduled_dt(date_str, time_str)

        if due_for_check(key, sched, now, state):
            result = call_api(flight_num, date_str)
            state[key] = now.isoformat()
            calls_made += 1

            if result and "_error" not in result:
                output["flights"][key] = {
                    "flight": flight_num,
                    "airport": row["airport"],
                    "scheduled_time": time_str,
                    "status": result.get("status"),
                    "arrival": result.get("arrival", {}),
                    "departure": result.get("departure", {}),
                    "updated_at": now.isoformat(),
                }
            elif result:
                existing = output["flights"].get(key, {
                    "flight": flight_num,
                    "airport": row["airport"],
                    "scheduled_time": time_str,
                })
                existing["last_error"] = result.get("_error")
                output["flights"][key] = existing

    output["generated_at"] = now.isoformat()
    output["date"] = date_str
    output["calls_made_this_run"] = calls_made

    save_json(STATE_FILE, state)
    save_json(OUTPUT_FILE, output)
    print(f"Checked {calls_made} flight(s) this run.")


if __name__ == "__main__":
    main()
