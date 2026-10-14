"""Follow-ups for jobs a user marked Applied: interview call? -> interview done? -> got the job?
Runs inside the daily 8 AM digest run only. A question is due when next_ask_at has passed.
Each question is asked at most 3 times, at most 3 follow-ups per user per run.
The answers come back through the webhook (index.ts)."""
from datetime import datetime, timedelta, timezone

PER_USER_PER_RUN = 3
MAX_ASKS = 3
REASK_DAYS = 3
ASKS = {"call": ("c", "fu_call"), "interview": ("i", "fu_interview"), "outcome": ("o", "fu_outcome")}


def keyboard(ask, row_id, text_fn, language):
    p = ASKS[ask][0]
    return {"inline_keyboard": [[{"text": text_fn(f"fu_{p}{n}", language), "callback_data": f"f:{p}{n}:{row_id}"}]
                                 for n in ("1", "0", "x")]}


def due_rows(requests, base, headers):
    now = datetime.now(timezone.utc).isoformat()
    try:
        r = requests.get(f"{base}/rest/v1/kajkhoj_applications", headers=headers, params={
            "select": "id,chat_id,title,company,ask,ask_count", "status": "eq.applied",
            "ask": "in.(call,interview,outcome)", "next_ask_at": f"lte.{now}",
            "ask_count": f"lt.{MAX_ASKS}", "order": "next_ask_at.asc", "limit": "300"}, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("followup: read failed:", type(e).__name__)
        return []


def run(requests, base, headers, send, text_fn, languages, on_blocked):
    """languages: {chat_id: language} for known users. Returns number of follow-ups sent."""
    sent, per_user = 0, {}
    for row in due_rows(requests, base, headers):
        chat_id = row["chat_id"]
        if chat_id not in languages:
            continue  # user left (profile deleted); nothing to ask
        if per_user.get(chat_id, 0) >= PER_USER_PER_RUN:
            continue
        language = languages[chat_id]
        ask = row["ask"]
        company = f" @ {row['company']}" if row.get("company") else ""
        msg = f"{text_fn('fu_head', language)}\n{row['title']}{company}\n\n{text_fn(ASKS[ask][1], language)}"
        status = send(chat_id, msg[:4000], keyboard(ask, row["id"], text_fn, language))
        if status == 403:
            on_blocked(chat_id)
            languages.pop(chat_id, None)
            continue
        if status != 200:
            continue
        per_user[chat_id] = per_user.get(chat_id, 0) + 1
        sent += 1
        try:  # guarded: a tap that already changed the question must not be overwritten
            requests.patch(f"{base}/rest/v1/kajkhoj_applications", headers=headers, params={
                "id": f"eq.{row['id']}", "status": "eq.applied", "ask": f"eq.{ask}"},
                json={"ask_count": int(row.get("ask_count") or 0) + 1,
                      "next_ask_at": (datetime.now(timezone.utc) + timedelta(days=REASK_DAYS)).isoformat(),
                      "updated_at": datetime.now(timezone.utc).isoformat()}, timeout=30)
        except Exception as e:
            print("followup: update failed:", type(e).__name__)
    print("followups sent:", sent)
    return sent
