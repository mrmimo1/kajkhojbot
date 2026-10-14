"""Sent-job memory: remember which jobs each user already got, so no repeats.
Free tier: one small Supabase table (kajkhoj_sent_jobs). No AI, no new service.
Fails open: if the table cannot be read, the digest still goes out (a repeat is
better than a missing digest)."""
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, parse_qs

KEEP_DAYS = 30


def _norm(s):
    return " ".join(re.findall(r"[a-z0-9]+", str(s or "").casefold()))


def job_keys(post):
    """Stable keys for one job. A job counts as seen if ANY key matches:
    1) its link id (same job on a later day), 2) title+company (same job re-listed)."""
    keys = []
    url = str(post.get("url") or "").strip()
    try:
        u = urlparse(url)
        host = (u.netloc or "").lower()
        q = parse_qs(u.query)
        m = re.search(r"/jobs/view/(?:[^/?]*-)?(\d{6,})", u.path)
        if "linkedin." in host and m:
            keys.append("li:" + m.group(1))
        elif q.get("jk"):
            keys.append("in:" + q["jk"][0])
        elif q.get("jl"):
            keys.append("gd:" + q["jl"][0])
        elif url:
            keys.append("u:" + host + u.path.rstrip("/").lower())
    except Exception:
        if url:
            keys.append("u:" + url.lower()[:200])
    title, company = _norm(post.get("title")), _norm(post.get("company"))
    if title and company:
        keys.append("tc:" + title + "|" + company)
    return keys


def load_seen(requests, base, headers, chat_id):
    """Set of job keys this user already got in the last KEEP_DAYS days.
    None means the lookup failed (caller then skips filtering)."""
    since = (datetime.now(timezone.utc) - timedelta(days=KEEP_DAYS)).isoformat()
    try:
        r = requests.get(
            f"{base}/rest/v1/kajkhoj_sent_jobs",
            headers=headers,
            params={"select": "job_key", "chat_id": f"eq.{chat_id}",
                    "sent_at": f"gte.{since}", "limit": "5000"},
            timeout=30,
        )
        r.raise_for_status()
        return {row["job_key"] for row in r.json()}
    except Exception as e:
        print("sent memory: read failed, not filtering:", type(e).__name__)
        return None


def filter_new(result, seen):
    """Copy of a cached search result without jobs this user already got.
    Rebuilds ai_posts so their positions match the filtered lists."""
    out = {"jobs": [], "freelance": [], "partial_failure": result["partial_failure"],
           "ai_posts": [], "detail_cards": result.setdefault("detail_cards", {})}
    batch = set()
    for kind in ("jobs", "freelance"):
        for post in result[kind]:
            keys = job_keys(post)
            if seen is not None and any(k in seen for k in keys):
                continue
            if any(k in batch for k in keys):  # same job twice in one digest
                continue
            batch.update(keys)
            out[kind].append(post)
    for kind in ("jobs", "freelance"):
        for i, post in enumerate(out[kind]):
            if len(out["ai_posts"]) < 3:
                out["ai_posts"].append({"kind": kind, "index": i, "title": post["title"][:180],
                                        "description": (post.get("description") or "")[:600]})
    return out


def mark_sent(requests, base, headers, chat_id, result):
    """Remember every job in the digest that was just delivered (status 200 only)."""
    rows = []
    for kind in ("jobs", "freelance"):
        for post in result[kind]:
            for k in job_keys(post):
                rows.append({"chat_id": str(chat_id), "job_key": k})
    if not rows:
        return
    try:
        h = dict(headers)
        h["Prefer"] = "resolution=ignore-duplicates,return=minimal"
        r = requests.post(f"{base}/rest/v1/kajkhoj_sent_jobs?on_conflict=chat_id,job_key",
                          headers=h, json=rows, timeout=30)
        if r.status_code >= 300:
            print("sent memory: write failed, status", r.status_code)
    except Exception as e:
        print("sent memory: write failed:", type(e).__name__)


def forget_user(requests, base, headers, chat_id):
    try:
        requests.delete(f"{base}/rest/v1/kajkhoj_sent_jobs?chat_id=eq.{chat_id}",
                        headers=headers, timeout=30)
    except Exception:
        pass


def cleanup_old(requests, base, headers):
    """Once per run: drop memory older than KEEP_DAYS so the table stays tiny."""
    since = (datetime.now(timezone.utc) - timedelta(days=KEEP_DAYS)).isoformat()
    try:
        requests.delete(f"{base}/rest/v1/kajkhoj_sent_jobs",
                        headers=headers, params={"sent_at": f"lt.{since}"}, timeout=30)
    except Exception:
        pass
