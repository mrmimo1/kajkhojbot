"""Applied / Not interested tracker (part 1).
Every job sent gets a row (status 'shown') so the two buttons can point at it.
The webhook flips the status when the user taps. Fails open: if the table is
unreachable the jobs are still sent, just without buttons."""
import uuid
from datetime import datetime, timedelta, timezone

import kajkhoj_sent

SHOWN_KEEP_DAYS = 30


def register(requests, base, headers, chat_id, posts):
    """Insert one 'shown' row per post. Returns {post url: row id}, or {} on failure."""
    rows, ids = [], {}
    for post in posts:
        url = str(post.get("url") or "")[:1000]
        if not url or url in ids:
            continue
        row_id = str(uuid.uuid4())
        ids[url] = row_id
        rows.append({"id": row_id, "chat_id": int(chat_id), "title": str(post.get("title") or "")[:300],
                     "company": str(post.get("company") or "")[:200], "url": url, "status": "shown"})
    if not rows:
        return {}
    try:
        h = dict(headers)
        h["Prefer"] = "return=minimal"
        r = requests.post(f"{base}/rest/v1/kajkhoj_applications", headers=h, json=rows, timeout=30)
        if r.status_code >= 300:
            print("tracker: register failed, status", r.status_code, "- sending without buttons")
            return {}
        return ids
    except Exception as e:
        print("tracker: register failed:", type(e).__name__, "- sending without buttons")
        return {}


def blocked_keys(requests, base, headers, chat_id):
    """Job keys of jobs this user marked Applied or Not interested (never expire).
    None means the lookup failed."""
    try:
        r = requests.get(f"{base}/rest/v1/kajkhoj_applications", headers=headers,
                         params={"select": "title,company,url", "chat_id": f"eq.{chat_id}",
                                 "status": "in.(applied,not_interested)", "limit": "5000"}, timeout=30)
        r.raise_for_status()
        keys = set()
        for row in r.json():
            keys.update(kajkhoj_sent.job_keys(row))
        return keys
    except Exception as e:
        print("tracker: read failed:", type(e).__name__)
        return None


def keyboard(row_id, text_fn, language):
    return {"inline_keyboard": [[
        {"text": text_fn("btn_applied", language), "callback_data": "a:" + row_id},
        {"text": text_fn("btn_not_interested", language), "callback_data": "n:" + row_id},
    ]]}


def forget_user(requests, base, headers, chat_id):
    try:
        requests.delete(f"{base}/rest/v1/kajkhoj_applications?chat_id=eq.{chat_id}", headers=headers, timeout=30)
    except Exception:
        pass


def cleanup_old(requests, base, headers):
    """Applied / Not interested rows are kept. Untouched 'shown' rows older than 30 days go."""
    since = (datetime.now(timezone.utc) - timedelta(days=SHOWN_KEEP_DAYS)).isoformat()
    try:
        requests.delete(f"{base}/rest/v1/kajkhoj_applications", headers=headers,
                        params={"status": "eq.shown", "created_at": f"lt.{since}"}, timeout=30)
    except Exception:
        pass
