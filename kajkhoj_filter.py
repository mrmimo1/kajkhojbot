"""Per-user deterministic title + location filter. No network or sending.
Vague preferences never fall back to sending every scraped row.
"""
import re
from dataclasses import dataclass

@dataclass(frozen=True)
class Match:
    strong: bool
    score: int
    reasons: tuple[str, ...]

DIGITAL_ROLES = (
    r'\bdigital marketing\b', r'\bsocial media\b',
    r'\bcontent (?:writer|writing|creator|creation|strategist|strategy|marketing|marketer|editor|executive|manager|specialist)\b',
    r'\bcopywriter\b', r'\bcopywriting\b', r'\bseo (?:executive|specialist|analyst|manager)\b',
)
CITY_GROUPS = (
    ('kolkata','calcutta','salt lake','saltlake','new town','newtown','rajarhat'),
    ('mumbai','bombay'), ('bengaluru','bangalore'), ('chennai','madras'),
    ('delhi','new delhi'), ('gurugram','gurgaon'), ('kochi','cochin'), ('puducherry','pondicherry'),
)
ROLE_GROUPS = (
    ('designer','design'), ('developer','development','programmer'),
    ('accountant','accounting','accounts'), ('teacher','teaching','educator'),
    ('writer','writing'), ('recruiter','recruitment'), ('nurse','nursing'),
    ('salesperson','sales'), ('assistant','assistance'),
)
STOP = {'job','jobs','role','roles','work','wanted','looking','for','a','an','the','in','and','of','freelance','freelancer','freelancing','gig','gigs','project','projects'}
VAGUE = {'marketing','sales','office','staff','executive','manager','management','assistant','worker','employee','job','jobs','it','any','anything','all','work','fresher','intern','internship','remote'}

def tokens(text):
    return re.findall(r'[a-z0-9]+|[^\W\d_]+',str(text or '').casefold())

def significant_terms(profession):
    return [t for t in dict.fromkeys(tokens(profession)) if t not in STOP and len(t)>=2]

def valid_preferences(profession,city):
    terms=significant_terms(profession)
    return bool(terms and not all(t in VAGUE for t in terms) and len(str(city or '').strip())>=2)

def phrase_present(text,phrase):
    # Word boundaries with normalized punctuation; no Mumbai -> Navi Mumbai ambiguity hiding.
    normalized=' '.join(tokens(text))
    return bool(re.search(r'(?<!\w)'+re.escape(' '.join(tokens(phrase)))+r'(?!\w)',normalized))

def role_matches(title,profession):
    terms=significant_terms(profession)
    # Preserve earlier family matching for exactly the owner's digital-marketing preference.
    if ' '.join(terms)=='digital marketing':
        return (any(re.search(p,title) for p in DIGITAL_ROLES)
                and not re.search(r'\b(?:software|backend|frontend|full stack|data engineer|salesforce|content moderator|moderation)\b',title))
    # Content moderator can be a real profession. Exclude it only for unrelated content preferences.
    if 'content' in terms and not any(t in terms for t in ['moderator','moderation']) and re.search(r'\b(?:moderator|moderation)\b',title):
        return False
    if any(t in terms for t in ['marketing','marketer']) and not any(t in terms for t in ['field','sales']) and re.search(r'\b(?:field sales|door to door|sales representative)\b',title):
        return False
    words=set(tokens(title))
    for term in terms:
        group=next((g for g in ROLE_GROUPS if term in g),(term,))
        if not any(t in words for t in group):return False
    return True

def local_matches(location,city):
    # Never count a request for remote as a physical city or infer locality from search input.
    if ' '.join(tokens(city)) in {'remote','work from home','wfh','anywhere','global'}:return False
    group=next((g for g in CITY_GROUPS if ' '.join(tokens(city)) in g),None)
    return any(phrase_present(location,c) for c in group) if group else phrase_present(location,city)

def score_job(job,profession,city):
    if not valid_preferences(profession,city):return Match(False,0,('preference too vague; specify a role and city',))
    title=str(job.get('title') or '').casefold()
    location=str(job.get('location') or '').casefold()
    mode=str(job.get('work_mode') or '').casefold()
    eligibility=str(job.get('remote_eligibility') or '').casefold()
    description=str(job.get('description') or '').casefold()
    if not title.strip():return Match(False,0,('missing title',))
    if not role_matches(title,profession):return Match(False,0,('title does not match user role',))
    reasons=['user role matched in title'];score=60
    remote=mode in {'remote','fully remote','work from home','wfh'} or bool(re.search(r'\bremote\b',location))
    restricted=bool(re.search(r'\b(?:us only|usa only|uk only|europe only|canada only|must (?:reside|be based) in (?:the )?(?:us|usa|uk|canada))\b',location+' '+eligibility+' '+description))
    eligible=bool(re.search(r'\b(?:india|worldwide|global|anywhere)\b',location+' '+eligibility))
    if remote:
        if restricted:return Match(False,score,tuple(reasons+['remote restricted outside India']))
        if not eligible:return Match(False,score,tuple(reasons+['remote eligibility unknown']))
        score+=35;reasons.append('India/global remote eligible')
    elif local_matches(location,city):score+=35;reasons.append('user city matched')
    else:return Match(False,score,tuple(reasons+['city does not match']))
    if re.search(r'\b(?:intern|internship|fresher|junior|entry level)\b',title):score+=5;reasons.append('entry-level signal')
    return Match(score>=95,min(score,100),tuple(reasons))
