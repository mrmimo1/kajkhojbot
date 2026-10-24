"""Bounded, per-source searches. Edit keywords/settings here, not in main.py.
Search phrases are discovery hints, never proof of a posting's job type or eligibility.
"""
import re
import time
import logging
from collections import Counter, deque
from datetime import datetime, timezone

from jobspy import scrape_jobs
from kajkhoj_filter import score_job, role_matches

# Google Jobs removed 2026-10-24: upstream JobSpy can no longer read Google
# (Google serves Jobs only to JS browsers; speedyapply/JobSpy issue #284, still open).
# Every Google query returned 0 rows and logged ERROR, which tripped the daily
# "source search failed" warning even though all working sources were fine.
# Re-add 'google' here when upstream issue #284 is fixed.
SOURCES = ('indeed', 'naukri', 'linkedin', 'glassdoor')
REMOTE_KEYWORDS = ('remote', 'work from home', 'WFH', 'fully remote', 'home based', 'work from anywhere', 'remote consultant', 'remote part time')
FREELANCE_KEYWORDS = ('freelance', 'freelancer', 'project based', 'contract', 'consultant', 'part time', 'independent contractor', 'short term project', 'freelance services', 'project work')
ROLE_QUERIES = {
 'digital marketing': ('digital marketing', 'social media', 'content writer', 'SEO specialist'),
 'content writer': ('content writer', 'copywriter'),
 'graphic designer': ('graphic designer', 'visual designer'),
}
LOCAL_HOURS = 72
FLEXIBLE_HOURS = 168
ROWS_PER_SOURCE = 20
LINKEDIN_ROWS = 20
MAX_JOBS = 15
MAX_FREELANCE = 5
MAX_SEARCH_CALLS_PER_RUN = 60
DESC_CHARS = 1200

class _Errors(logging.Handler):
    def __init__(self):
        super().__init__(logging.WARNING); self.count = 0; self.throttled = False
    def emit(self, record):
        if record.levelno >= logging.ERROR: self.count += 1
        if '429' in record.getMessage(): self.throttled = True
        # Only flags, not private/raw payloads, are retained.

def _field(row, key):
    import pandas as pd
    v = row.get(key)
    if v is None: return ''
    try:
        if pd.isna(v): return ''
    except (ValueError, TypeError): return ''
    return str(v).strip()

def freelance_evidence(row):
    title = _field(row,'title')
    description = _field(row,'description')
    if re.search(r'\bfreelanc(?:e|er|ers|ing)\b|\bgig\b',title,re.I): return True
    return bool(re.search(r'\b(?:hiring|seeking|need|looking for)\s+(?:an?\s+)?freelanc(?:e|er)\b|\b(?:freelance (?:project|position|opportunity)|project.based (?:work|engagement|assignment))\b',description,re.I))

def _remote_evidence(title,location,description,is_remote):
    if is_remote or re.search(r'\bremote\b|\bWFH\b|work from home',title+' '+location,re.I): return True
    return bool(re.search(r'\b(?:fully remote|remote (?:position|role|job)|work from home|work from anywhere)\b',description,re.I))

def row_job(row):
    title,location,description = (_field(row,k) for k in ('title','location','description'))
    remote = _remote_evidence(title,location,description,_field(row,'is_remote').lower()=='true')
    eligibility = ''
    for pattern in (r'\b(?:remote|work from home)\s+(?:in|from|within|across)\s+india\b',r'\b(?:based|reside|located)\s+in\s+india\b',r'\b(?:work from anywhere|remote worldwide|globally remote|worldwide remote|open to (?:candidates )?(?:worldwide|globally))\b'):
        m=re.search(pattern,description,re.I)
        if m: eligibility=m.group();break
    if re.search(r'work from anywhere|worldwide|globally',eligibility,re.I): eligibility += ' worldwide'
    return {'title':title,'location':location,'description':description,'work_mode':'remote' if remote else '', 'remote_eligibility':eligibility}

def _balanced(by_source,limit):
    queues=[deque([p for p in by_source.get(s,[]) if p.get('category')==c])
            for c in ('remote','local','freelance') for s in SOURCES]
    out=[]; seen=set()
    while len(out)<limit and any(queues):
        for q in queues:
            if not q:continue
            p=q.popleft()
            if p['url'] not in seen:
                seen.add(p['url']);out.append(p)
            if len(out)==limit:break
    return out

def query_plan(profession,city):
    base=re.sub(r'\b(?:freelance|freelancer|freelancing|gigs?|projects?)\b','',profession,flags=re.I)
    base=' '.join(base.split())
    day=datetime.now(timezone.utc).date().toordinal()
    remote_word=REMOTE_KEYWORDS[day%len(REMOTE_KEYWORDS)]
    freelance_word=FREELANCE_KEYWORDS[day%len(FREELANCE_KEYWORDS)]
    plan=[]
    # Core freelance/remote query every run, rotating extra synonyms on LinkedIn.
    for source in SOURCES:
        plan.extend([(source,'local',base,city,False,LOCAL_HOURS),
                     (source,'remote',base+' remote','India',True,FLEXIBLE_HOURS),
                     (source,'flexible',base+' freelance','India',False,FLEXIBLE_HOURS)])
    aliases=ROLE_QUERIES.get(base.casefold(),(base,))
    alias=aliases[day%len(aliases)]
    if not role_matches(alias.casefold(),profession): alias=base
    plan.extend([('linkedin','remote',alias+' '+remote_word,'India',True,FLEXIBLE_HOURS),
                 ('linkedin','flexible',alias+' '+freelance_word,'India',False,FLEXIBLE_HOURS)])
    return list(dict.fromkeys(plan))

def find_jobs(profession,city,budget,paused=None):
    found={k:{s:[] for s in SOURCES} for k in ('jobs','freelance')}
    # Per-source health, decided after all queries: a source "failed" only when
    # NONE of its queries worked (exception, errors with 0 rows, or throttled
    # before any success). A source that delivered rows and only later hit a
    # 429 still counts as working, so one hiccup in a 14-query plan no longer
    # trips the daily warning; a genuinely dead source still does.
    state={s:{'ok':False,'failed':False} for s in SOURCES}
    budget_hit=False;success=0
    if paused is None: paused=set()
    for source,kind,term,location,remote,hours in query_plan(profession,city):
        if source in paused:
            state[source]['failed']=True; print('search:',source,kind,'skipped after throttling');continue
        if budget[0]<=0:
            budget_hit=True; print('search: run budget reached');break
        budget[0]-=1
        logger=logging.getLogger('JobSpy:'+{'linkedin':'LinkedIn'}.get(source,source.capitalize()))
        errors=_Errors();logger.addHandler(errors)
        rejects=Counter(); raw=0;kept=0;started=time.monotonic()
        try:
            df=scrape_jobs(site_name=[source],search_term=term,
                google_search_term=f'{term} jobs '+(f'near {city}' if kind=='local' else 'India')+(' since 3 days ago' if hours==72 else ' since 7 days ago'),
                location=location,is_remote=remote if source!='linkedin' else False,results_wanted=LINKEDIN_ROWS if source=='linkedin' else ROWS_PER_SOURCE,
                hours_old=hours,country_indeed='India',fetch_description=True)
            success+=1;raw=len(df) if df is not None else 0
            if df is not None:
                for _,row in df.iterrows():
                    job=row_job(row);match=score_job(job,profession,city)
                    if not match.strong:
                        rejects[match.reasons[-1]]+=1;continue
                    is_freelance=freelance_evidence(row)
                    if kind=='remote' and job['work_mode']!='remote':
                        rejects['no explicit remote evidence']+=1;continue
                    if kind=='flexible' and not is_freelance:
                        rejects['no freelance/project evidence']+=1;continue
                    url=_field(row,'job_url')
                    if not re.match(r'^https?://[^\s]+$',url):
                        rejects['invalid URL']+=1;continue
                    category='freelance' if is_freelance else 'remote' if job['work_mode']=='remote' else 'local'
                    post={'title':job['title'],'company':_field(row,'company'),'location':job['location'],
                          'description':job['description'][:DESC_CHARS],'salary_row':{k:_field(row,k) for k in ('min_amount','max_amount','currency','interval')},
                          'url':url,'source':source,'category':category}
                    found['freelance' if is_freelance else 'jobs'][source].append(post);kept+=1
            if raw>0:
                state[source]['ok']=True        # delivered rows, noise or not
            elif errors.count or errors.throttled:
                state[source]['failed']=True    # nothing back AND it errored
            else:
                state[source]['ok']=True        # healthy, just no jobs
            if errors.throttled:
                paused.add(source); print('search:',source,'throttled; remaining source queries skipped')
        except Exception as e:
            state[source]['failed']=True; print('search exception:',source,kind,type(e).__name__)
        finally:
            logger.removeHandler(errors)
        print('search:',source,kind,'rows',raw,'accepted',kept,'errors',errors.count,'rejects',dict(rejects),'seconds',round(time.monotonic()-started,1))
        time.sleep(1)
    partial=budget_hit or any(state[s]['failed'] and not state[s]['ok'] for s in SOURCES)
    print('search health:', {s:('ok' if state[s]['ok'] else 'FAILED' if state[s]['failed'] else 'no jobs') for s in SOURCES})
    jobs=_balanced(found['jobs'],MAX_JOBS);gigs=_balanced(found['freelance'],MAX_FREELANCE)
    # Remove any duplicate URLs across sections.
    used={p['url'] for p in jobs};gigs=[p for p in gigs if p['url'] not in used]
    out={'jobs':jobs,'freelance':gigs,'partial_failure':partial,'ai_posts':[]}
    for kind in ('jobs','freelance'):
        for i,p in enumerate(out[kind]):
            if len(out['ai_posts'])<3:out['ai_posts'].append({'kind':kind,'index':i,'title':p['title'][:180],'description':p['description'][:600]})
    print('search output: jobs',len(jobs),'freelance',len(gigs))
    return out if success else None
