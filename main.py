import os
import time
import requests
import pandas as pd
from jobspy import scrape_jobs

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
MODE = os.environ.get("MODE", "digest").strip() or "digest"

DB_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}


def send(chat_id, msg):
    """Send one Telegram message. Returns the HTTP status (0 on network error).
    Never prints the token or the chat id."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(
            url,
            json={"chat_id": chat_id, "text": msg, "disable_web_page_preview": True},
            timeout=30,
        )
        return r.status_code
    except Exception:
        return 0


def get_users():
    q = "select=chat_id,profession,city"
    if MODE == "today":
        q += "&today_requested=eq.true"
    r = requests.get(f"{SUPABASE_URL}/rest/v1/users?{q}", headers=DB_HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def delete_user(chat_id):
    try:
        requests.delete(
            f"{SUPABASE_URL}/rest/v1/users?chat_id=eq.{chat_id}",
            headers=DB_HEADERS,
            timeout=30,
        )
    except Exception:
        pass


def clear_today_flag(chat_id):
    try:
        requests.patch(
            f"{SUPABASE_URL}/rest/v1/users?chat_id=eq.{chat_id}",
            headers=DB_HEADERS,
            json={"today_requested": False},
            timeout=30,
        )
    except Exception:
        pass


def find_jobs(profession, city):
    """Same scrape as v1: Indeed + Naukri, 72h, dedupe, top 15."""
    try:
        jobs = scrape_jobs(
            site_name=["indeed", "naukri", "google", "linkedin", "glassdoor"],
            search_term=profession,
            location=city,
            results_wanted=10,
            hours_old=72,
            country_indeed="India",
        )
    except Exception as e:
        print("scrape failed:", type(e).__name__)
        return []
    if jobs is None or len(jobs) == 0 or "job_url" not in jobs.columns:
        return []
    df = pd.concat([jobs]).drop_duplicates(subset=["job_url"])
    result = []
    for _, row in df.head(15).iterrows():
        result.append(f"* {row['title']} @ {row['company']}\n{row['job_url']}")
    return result


def build_message(lines):
    return "Kajkhoj Bot - notun chakri:\n\n" + "\n\n".join(lines)


def send_long(chat_id, msg):
    """Returns the last status code. 403 means the user blocked the bot."""
    status = 200
    for i in range(0, len(msg), 4000):
        status = send(chat_id, msg[i:i + 4000])
        if status == 403:
            return status
    return status


def main():
    users = get_users()
    print("mode:", MODE, "| users:", len(users))
    cache = {}
    sent = 0
    skipped = 0

    for u in users:
        chat_id = u.get("chat_id")
        profession = (u.get("profession") or "").strip()
        city = (u.get("city") or "").strip()

        if not profession or not city:
            send(chat_id, "Age /keywords diye apnar job type ar city set korun. Example: /keywords digital marketing Kolkata")
            if MODE == "today":
                clear_today_flag(chat_id)
            continue

        key = (profession.lower(), city.lower())
        if key not in cache:
            cache[key] = find_jobs(profession, city)
            time.sleep(2)
        lines = cache[key]

        if not lines:
            skipped += 1
            if MODE == "today":
                send(chat_id, "Kajkhoj Bot: ekhon kono notun job paini, pore abar dekhbo.")
                clear_today_flag(chat_id)
            continue

        status = send_long(chat_id, build_message(lines))
        if status == 403:
            delete_user(chat_id)
        else:
            sent += 1
            if MODE == "today":
                clear_today_flag(chat_id)

    print("Done! sent:", sent, "| skipped (0 jobs):", skipped)


main()
