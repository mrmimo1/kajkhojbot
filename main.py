import os
import requests
import pandas as pd
from jobspy import scrape_jobs

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

KEYWORDS = ["digital marketing", "social media", "content writer"]

def send(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "disable_web_page_preview": True})

all_jobs = []
for kw in KEYWORDS:
    try:
        jobs = scrape_jobs(
            site_name=["indeed", "naukri"],
            search_term=kw,
            location="Kolkata",
            results_wanted=10,
            hours_old=72,
            country_indeed="India",
        )
        all_jobs.append(jobs)
        print(kw, "->", len(jobs), "jobs")
    except Exception as e:
        print(kw, "failed:", e)

if all_jobs:
    df = pd.concat(all_jobs).drop_duplicates(subset=["job_url"])
    lines = []
    for _, row in df.head(15).iterrows():
        lines.append(f"* {row['title']} @ {row['company']}\n{row['job_url']}")
    msg = "Kajkhoj Bot - notun chakri:\n\n" + "\n\n".join(lines)
    for i in range(0, len(msg), 4000):
        send(msg[i:i+4000])
    print("Done! Telegram e message pathano hoyeche")
else:
    send("Kajkhoj Bot: ekhon kono notun job paini, pore abar dekhbo.")
    print("Kono job paoa jayni")
