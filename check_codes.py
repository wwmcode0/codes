import json, os, time
import requests

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]
SEEN_FILE = "seen_codes.json"
API_URL = "https://codes.yar.gg/api/codes"

def get_current_codes():
    r = requests.get(API_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    r.raise_for_status()
    data = r.json()
    active = data.get("active", [])
    return [entry["code"] for entry in active if entry.get("code")]

def load_seen():
    if os.path.exists(SEEN_FILE):
        return set(json.load(open(SEEN_FILE)))
    return set()

def save_seen(seen):
    json.dump(sorted(seen), open(SEEN_FILE, "w"))

def post_to_discord(code):
    payload = {"content": f"`{code}`"}
    while True:
        r = requests.post(WEBHOOK_URL, json=payload)
        if r.status_code == 429:
            retry_after = r.json().get("retry_after", 1)
            time.sleep(retry_after + 0.5)
            continue
        break

def main():
    seen = load_seen()
    current = get_current_codes()
    print(f"DEBUG: found {len(current)} active codes")
    new_codes = [c for c in current if c not in seen]

    for code in new_codes:
        post_to_discord(code)
        time.sleep(1)

    if new_codes:
        seen.update(current)
        save_seen(seen)

if __name__ == "__main__":
    main()
