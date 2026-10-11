import os
import time
import requests
import pandas as pd
from jobspy import scrape_jobs
from kajkhoj_filter import score_job
import re

FRIENDLY_ERROR = "Ektu jhamela hocche 🙏 Ektu pore abar try koro."

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
        if r.status_code == 200:
            # A malformed response may conceal a successful send. Status 0 is ambiguous.
            try:
                payload = r.json()
                return 200 if payload.get("ok") else int(payload.get("error_code") or 0)
            except (ValueError, TypeError, AttributeError):
                return 0
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


def field(row, name):
    """Normalize nullable JobSpy scalar fields without turning NaN into job text."""
    value = row.get(name)
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (ValueError, TypeError):
        return ""
    return str(value).strip()


def row_to_job(row):
    location = field(row, "location")
    country = field(row, "country")
    if country and country.casefold() not in location.casefold():
        location = location + ", " + country if location else country
    mode = field(row, "work_mode")
    # JobSpy normally provides is_remote as bool; NaN/False must not become true.
    is_remote = field(row, "is_remote").casefold() == "true"
    if is_remote:
        mode = "remote"
    description = field(row, "description")
    eligibility = field(row, "remote_eligibility")
    # Only explicit eligibility language, not a random mention of India in company text.
    if not eligibility:
        for pattern in [
            r"\b(?:remote|work from home)\s+(?:in|from|within|across)\s+india\b",
            r"\b(?:based|reside|located)\s+in\s+india\b",
            r"\b(?:work from anywhere|remote worldwide|globally remote)\b",
        ]:
            match = re.search(pattern, description, flags=re.I)
            if match:
                eligibility = match.group()
                break
    return {"title": field(row, "title"), "location": location,
            "description": description, "work_mode": mode,
            "remote_eligibility": eligibility}


def find_jobs(profession, city):
    """Preserve five-source/72h scrape; filter before choosing up to 15 alerts.
    None = failed scrape/schema, [] = successful scrape with no strong matches.
    The search city is NOT proof of a job's actual location.
    """
    try:
        jobs = scrape_jobs(
            site_name=["indeed", "naukri", "google", "linkedin", "glassdoor"],
            search_term=profession,
            location=city,
            results_wanted=10,
            hours_old=72,
            country_indeed="India",
        )
        if jobs is None:
            return None
        if len(jobs) == 0:
            return []
        if "job_url" not in jobs.columns or "title" not in jobs.columns:
            return None
        df = jobs.drop_duplicates(subset=["job_url"])
        result = []
        for _, row in df.iterrows():
            job = row_to_job(row)
            if not score_job(job).strong:
                continue
            url = field(row, "job_url")
            # Keep the actual provider URL; never fabricate missing destinations.
            if not re.match(r"^https?://[^\s]+$", url):
                continue
            company = field(row, "company") or "Company not listed"
            result.append(f"* {job['title']} @ {company}\n{url}")
            if len(result) == 15:
                break
        return result
    except Exception as e:
        print("scrape failed:", type(e).__name__)
        return None


def build_message(lines):
    return "Kajkhoj Bot - notun chakri:\n\n" + "\n\n".join(lines)


def send_long(chat_id, msg):
    """Returns the last status code. 403 means the user blocked the bot."""
    status = 200
    for i in range(0, len(msg), 4000):
        status = send(chat_id, msg[i:i + 4000])
        if status != 200:
            # A chunk may have landed. Stop here, no retry/fallback send.
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
            status = send(chat_id, "Age /keywords diye apnar job type ar city set korun. Example: /keywords digital marketing Kolkata")
            if status == 403:
                delete_user(chat_id)
            elif MODE == "today":
                clear_today_flag(chat_id)
            continue

        key = (profession.lower(), city.lower())
        if key not in cache:
            cache[key] = find_jobs(profession, city)
            time.sleep(2)
        lines = cache[key]

        if lines is None:
            status = send(chat_id, FRIENDLY_ERROR) # one attempt only
            if status == 403:
                delete_user(chat_id)
            elif MODE == "today":
                clear_today_flag(chat_id) # also on ambiguous sends, avoid automatic repeats
            skipped += 1
            continue

        if not lines:
            skipped += 1
            if MODE == "today":
                status = send(chat_id, "Kajkhoj Bot: ekhon kono notun matching job paini, pore abar dekhbo.")
                if status == 403:
                    delete_user(chat_id)
                else:
                    clear_today_flag(chat_id)
            continue

        status = send_long(chat_id, build_message(lines))
        if status == 403:
            delete_user(chat_id)
        else:
            if status == 200:
                sent += 1
            else:
                print("Telegram delivery incomplete; no retry. status:", status)
            if MODE == "today":
                clear_today_flag(chat_id)

    print("Done! sent:", sent, "| skipped (0 jobs):", skipped)


if __name__ == "__main__":
    main()
