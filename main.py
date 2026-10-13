import os
import time
import requests
import pandas as pd
from jobspy import scrape_jobs
from kajkhoj_filter import score_job, valid_preferences
import re
from kajkhoj_language import text, normalize_language
from kajkhoj_ai import configured, explain, detail_cards

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
MODE = os.environ.get("MODE", "digest").strip() or "digest"

# Detail-card guardrails (free tier): short descriptions keep the normal format,
# at most DETAIL_MAX_PER_USER cards per digest, and a run-wide AI call budget so a
# big user list can never drain the shared free quota in one run.
DETAIL_MIN_CHARS = 200       # description shorter than this = no card, normal format
DETAIL_DESC_CHARS = 1200     # max description text sent to AI per posting
DETAIL_MAX_PER_USER = 5      # detailed cards per digest; the rest stay normal format
DETAIL_MAX_CALLS_PER_RUN = 12  # AI card calls per whole run across all users/languages

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
    q = "select=chat_id,profession,city,ai_enabled,language"
    if MODE == "today":
        q += "&today_requested=eq.true"
    r = requests.get(f"{SUPABASE_URL}/rest/v1/users?{q}", headers=DB_HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def delete_user(chat_id):
    try:
        requests.delete(
            f"{SUPABASE_URL}/rest/v1/kajkhoj_ai_usage?chat_id=eq.{chat_id}",
            headers=DB_HEADERS, timeout=30,
        )
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


def freelance_signal(row):
    """Require listing evidence, not just the freelance search query.
    Contract/temp alone is NOT proof of a client freelance project.
    """
    title = field(row, "title")
    job_type = field(row, "job_type")
    description = field(row, "description")
    if re.search(r"\b(?:freelance|freelancer|freelancing|gig)\b", title + " " + job_type, re.I):
        return True
    return bool(re.search(
        r"\b(?:seeking|hiring|looking for|need|needed)\s+(?:an?\s+)?freelanc(?:e|er)\b|\b(?:freelance position|freelance opportunity|freelance project)\b",
        description, re.I))


def posted_salary(row, language="banglish"):
    low = field(row, "min_amount"); high = field(row, "max_amount")
    currency = field(row, "currency"); interval = field(row, "interval")
    # Never convert annual/monthly, infer currency or invent an absent range.
    if (not low and not high) or not currency or not interval:
        return text("salary_missing", language)
    return text("salary", language) + currency + " " + (low + "-" + high if low and high else low or high) + " / " + interval


def add_ai_reason(result, user):
    import copy
    if user.get('ai_enabled') is not True or not configured() or not result.get('ai_posts'):
        return result
    try:
        r=requests.post(SUPABASE_URL+'/rest/v1/rpc/kajkhoj_ai_claim',headers=DB_HEADERS,json={'p_chat_id':user['chat_id']},timeout=10)
        r.raise_for_status()
        if r.json() is not True:return result
        posts=result['ai_posts']
        reasons=explain(user['profession'],[{'title':x['title'],'description':x['description']} for x in posts], language=normalize_language(user.get('language')))
        if not reasons:return result
        updated=copy.deepcopy(result) # never leak consented AI output to cached non-AI user
        for post,reason in zip(posts,reasons):
            updated[post['kind']][post['index']]['ai_reason'] = reason
        return updated
    except Exception:return result


def add_detail_cards(result, user, budget):
    """Attach AI detail cards (wants/fit) to jobs whose scraped description has
    usable detail. Cards are generated once per (profession, city) + language and
    reused for later users from the shared run cache; the run-wide budget caps AI
    calls. Any failure silently keeps the normal one-line format."""
    import copy
    language = normalize_language(user.get('language'))
    if not configured():
        print("detail cards: no AI provider configured; using normal format")
        return result
    posts = []
    for kind in ("jobs", "freelance"):
        for i, post in enumerate(result[kind]):
            if len(post.get('description') or '') >= DETAIL_MIN_CHARS:
                posts.append({'kind': kind, 'index': i, 'title': post['title'],
                              'company': post.get('company') or '',
                              'description': (post.get('description') or '')[:DETAIL_DESC_CHARS]})
        if len(posts) >= DETAIL_MAX_PER_USER:
            posts = posts[:DETAIL_MAX_PER_USER]
            break
    print("detail cards: eligible postings:", len(posts))
    if not posts:
        return result
    cards_by_lang = result.setdefault('detail_cards', {})
    cards = cards_by_lang.get(language)
    if cards is None:
        if budget[0] <= 0:
            print("detail cards: run budget exhausted; using normal format")
            return result
        budget[0] -= 1
        try:
            generated = detail_cards(user['profession'],
                                     [{'title': p['title'], 'company': p['company'],
                                       'description': p['description']} for p in posts],
                                     language=language)
        except Exception:
            generated = None
        if not generated:
            print("detail cards: AI returned no valid cards; using normal format")
            cards_by_lang[language] = {}  # one failed call must not retry for every later user
            return result
        cards = {}
        for p, card in zip(posts, generated):
            if card:
                cards[(p['kind'], p['index'])] = card
        print("detail cards: generated:", len(cards))
        cards_by_lang[language] = cards
    if not cards:
        return result
    updated = copy.deepcopy(result)  # cards are per-user rendering; the cache keeps raw listings
    for (kind, index), card in cards.items():
        updated[kind][index]['card'] = card
    return updated


def find_jobs(profession, city):
    """Two cached search passes; evidence-filtered listings, no new platforms.
    None means both scrapes failed. Partial results survive one failed pass.
    """
    base = re.sub(r"\b(?:freelance|freelancer|freelancing|gig|gigs|projects?)\b", "", profession, flags=re.I)
    base = " ".join(base.split())
    results = {"jobs": [], "freelance": [], "partial_failure": False, "ai_posts": []}
    seen = set()
    successful = 0
    for term in [base, base + " freelance"]:
        try:
            jobs = scrape_jobs(
                site_name=["indeed", "naukri", "google", "linkedin", "glassdoor"],
                search_term=term,
                google_search_term=f"{term} jobs near {city} since 3 days ago",
                location=city,
                results_wanted=10,
                hours_old=72,
                country_indeed="India",
                fetch_description=True,  # LinkedIn search cards omit descriptions by default.
            )
            if jobs is None or (len(jobs) and ("job_url" not in jobs.columns or "title" not in jobs.columns)):
                raise ValueError("scrape/schema unavailable")
            successful += 1
            if len(jobs):
                for _, row in jobs.drop_duplicates(subset=["job_url"]).iterrows():
                    job = row_to_job(row)
                    if not score_job(job, profession, city).strong:
                        continue
                    url = field(row, "job_url")
                    if not re.match(r"^https?://[^\s]+$", url) or url in seen:
                        continue
                    kind = "freelance" if freelance_signal(row) else "jobs"
                    # Extra pass must not turn non-freelance results into more ordinary alerts.
                    if term != base and kind != "freelance":
                        continue
                    limit = 5 if kind == "freelance" else 15
                    if len(results[kind]) >= limit:
                        continue
                    result_index = len(results[kind])
                    # Cache only listing facts; render labels separately for each user's language.
                    results[kind].append({"title": job["title"], "company": field(row, "company"),
                                          "location": job["location"],
                                          "description": job["description"][:DETAIL_DESC_CHARS],
                                          "salary_row": {name: field(row, name) for name in
                                                         ("min_amount", "max_amount", "currency", "interval")},
                                          "url": url})
                    if len(results['ai_posts'])<3:
                        results['ai_posts'].append({'kind':kind,'index':result_index,'title':job['title'][:180],'description':job['description'][:600]})
                    seen.add(url)
        except Exception as e:
            results["partial_failure"] = True
            print("scrape failed:", type(e).__name__)
        time.sleep(2)
    return results if successful else None


def build_message(result, language="banglish"):
    language = normalize_language(language)
    sections = []
    for kind in ("jobs", "freelance"):
        entries = []
        for post in result[kind]:
            company = post["company"] or text("company_missing", language)
            salary = posted_salary(post["salary_row"], language)
            card = post.get("card")
            if card:
                lines = [f"* {post['title']} @ {company}"]
                if post.get("location"):
                    lines.append(text("card_location", language) + post["location"])
                lines.append(salary)
                lines.append(text("card_wants", language) + card["wants"])
                lines.append(text("card_fit", language) + card["fit"])
                lines.append(post["url"])
                entries.append("\n".join(lines))
                continue
            line = f"* {post['title']} @ {company}\n{salary}\n{post['url']}"
            if post.get("ai_reason"):
                line += "\n" + text("ai_note", language) + post["ai_reason"]
            entries.append(line)
        if entries:
            sections.append(text(kind, language) + "\n\n" + "\n\n".join(entries))
    if result["partial_failure"]:
        sections.append(text("partial", language))
    return "\n\n".join(sections)


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
    detail_budget = [DETAIL_MAX_CALLS_PER_RUN]
    sent = 0
    skipped = 0

    for u in users:
        chat_id = u.get("chat_id")
        language = normalize_language(u.get("language"))
        profession = (u.get("profession") or "").strip()
        city = (u.get("city") or "").strip()

        if not valid_preferences(profession, city):
            status = send(chat_id, text("preferences", language))
            if status == 403:
                delete_user(chat_id)
            elif MODE == "today":
                clear_today_flag(chat_id)
            continue

        key = (profession.lower(), city.lower())
        if key not in cache:
            cache[key] = find_jobs(profession, city)
        lines = cache[key]

        if lines is None:
            status = send(chat_id, text("error", language)) # one attempt only
            if status == 403:
                delete_user(chat_id)
            elif MODE == "today":
                clear_today_flag(chat_id) # also on ambiguous sends, avoid automatic repeats
            skipped += 1
            continue

        if not lines["jobs"] and not lines["freelance"]:
            skipped += 1
            if lines["partial_failure"]:
                status = send(chat_id, text("error", language))
                if status == 403:
                    delete_user(chat_id)
                elif MODE == "today":
                    clear_today_flag(chat_id)
                continue
            if MODE == "today":
                status = send(chat_id, text("empty", language))
                if status == 403:
                    delete_user(chat_id)
                else:
                    clear_today_flag(chat_id)
            continue

        lines = add_detail_cards(lines, u, detail_budget)
        lines = add_ai_reason(lines, u)
        status = send_long(chat_id, build_message(lines, language))
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
