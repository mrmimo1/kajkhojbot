"""Standalone deterministic pre-alert filter. No network, mutation, or sending.
Input must come from parsed job data, NOT whole-page boilerplate.
Generic remote jobs need explicit India/global eligibility to avoid US-only alerts.
"""
import re
from dataclasses import dataclass

@dataclass(frozen=True)
class Match:
    strong: bool
    score: int
    reasons: tuple[str, ...]

ROLE_PATTERNS = (
    r'\bdigital marketing\b', r'\bsocial media\b', r'\bcontent (?:writer|writing|creator|creation|strategist|strategy|marketing|marketer|editor|executive|manager|specialist)\b',
    r'\bcopywriter\b', r'\bcopywriting\b', r'\bseo (?:executive|specialist|analyst|manager)\b',
)
NON_TARGET = r'\b(?:software|backend|frontend|full stack|data engineer|salesforce|content moderator|moderation)\b'
KOLKATA = r'\b(?:kolkata|calcutta|salt lake|saltlake|new town|newtown|rajarhat)\b'


def score_job(job: dict) -> Match:
    title=str(job.get('title') or '').casefold()
    location=str(job.get('location') or '').casefold()
    mode=str(job.get('work_mode') or '').casefold()
    eligibility=str(job.get('remote_eligibility') or '').casefold()
    description=str(job.get('description') or '').casefold()
    reasons=[]; score=0
    if not title.strip(): return Match(False,0,('missing title',))
    if re.search(NON_TARGET,title): return Match(False,0,('non-target role',))
    if any(re.search(p,title) for p in ROLE_PATTERNS):score+=60;reasons.append('target role in title')
    else:return Match(False,0,('no explicit target role in title',))
    # A role mention buried in employer boilerplate does not establish a match.
    remote=mode in {'remote','fully remote','work from home','wfh'} or bool(re.search(r'\bremote\b',location))
    restricted=bool(re.search(r'\b(?:us only|usa only|uk only|europe only|canada only|must (?:reside|be based) in (?:the )?(?:us|usa|uk|canada))\b',location+' '+eligibility+' '+description))
    india_remote=bool(re.search(r'\b(?:india|worldwide|global|anywhere)\b',location+' '+eligibility))
    if remote:
        if restricted:return Match(False,score,tuple(reasons+['remote restricted outside India']))
        if not india_remote:return Match(False,score,tuple(reasons+['remote eligibility unknown; review first']))
        score+=35;reasons.append('remote eligible for India/global')
    elif re.search(KOLKATA,location):score+=35;reasons.append('Kolkata area')
    else:return Match(False,score,tuple(reasons+['location not Kolkata or verified eligible remote']))
    if re.search(r'\b(?:intern|internship|fresher|junior|entry level)\b',title):score+=5;reasons.append('entry-level signal')
    # Experience/salary preference was not provided: do not silently reject senior roles.
    return Match(score>=95,min(score,100),tuple(reasons))
