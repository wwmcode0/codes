import json, os
from playwright.sync_api import sync_playwright

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]
SEEN_FILE = "seen_codes.json"

def get_current_codes():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://codes.yar.gg/", wait_until="networkidle")
        page.wait_for_selector("section#codes article[data-code]", timeout=15000)

        seen_codes = {}
        stable_rounds = 0
        max_rounds = 60

        for _ in range(max_rounds):
            articles = page.query_selector_all("section#codes article[data-code]")
            before_count = len(seen_codes)

            for a in articles:
                code = a.get_attribute("data-code")
                classes = a.get_attribute("class") or ""
                if code:
                    seen_codes[code] = classes

            # scroll the page down to force more items to render
            page.mouse.wheel(0, 2000)
            page.wait_for_timeout(400)

            after_count = len(seen_codes)
            if after_count == before_count:
                stable_rounds += 1
            else:
                stable_rounds = 0

            # stop once nothing new has appeared for a few scrolls in a row
            if stable_rounds >= 5:
                break

        browser.close()

        # keep only unused/active codes
        return [c for c, cls in seen_codes.items() if "is-used" not in cls]

def load_seen():
    if os.path.exists(SEEN_FILE):
        return set(json.load(open(SEEN_FILE)))
    return set()

def save_seen(seen):
    json.dump(sorted(seen), open(SEEN_FILE, "w"))

import time

def post_to_discord(code):
    import requests
    url = WEBHOOK_URL
    payload = {"content": f"`{code}`"}

    while True:
        r = requests.post(url, json=payload)
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
        time.sleep(1)   # stay safely under Discord's rate limit

    if new_codes:
        seen.update(current)
        save_seen(seen)

if __name__ == "__main__":
    main()
