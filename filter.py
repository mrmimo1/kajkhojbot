KajKhoj jobs + freelance/gig leads, per-user

Replace BOTH files in the same GitHub repository:
1. main.py: paste ALL of KajKhoj-main-jobs-gigs.py.txt, commit.
2. kajkhoj_filter.py: paste ALL of kajkhoj_filter-jobs-gigs.py.txt, commit.
Do not rename actual repo files to the attachment names. Same folder, main.py + kajkhoj_filter.py. Workflow, secrets, requirements, MODE and SQL unchanged.

Each valid profession/city search runs two passes: role search and role + freelance. This applies to all users, not just those with freelance in keywords. "Freelance"/gig/project words are removed from matching preference terms so "freelance graphic designer" matches Graphic Designer; plain "freelance" remains too vague and gets a correction prompt. Multi-user role/city/safe remote rules retained.
At most 15 ordinary jobs + 5 freelance-labelled leads per user/run. Both in ONE composed digest, split at 4,000 characters as before. Thus normally zero or one extra chunk; not a hard one-message guarantee, because source titles/URLs vary. Two scrapes per distinct role/city cache key per run, roughly double source load/latency; cached across identical user preference strings. Source sites may block/throttle. No logged-in external platform added.

Freelance classification requires an explicit freelance/freelancer/gig signal in listing title/job_type, or a tight hiring-a-freelancer/project phrase in description. Search query alone is NOT evidence. Contract/temporary alone is NOT called a freelance client project. Job-board posts are leads, not verified clients or guaranteed genuine projects. Original post URLs only; no phone numbers, extracted emails or private contact details. Visit source and check terms/client credibility before engaging.
Google's separate google_search_term now receives explicit role/location query too; JobSpy search_term alone does not filter Google. Sources remain existing Indeed/Naukri/Google/LinkedIn/Glassdoor. No job_type filter added because Indeed's 72h filter cannot be combined reliably with job_type.

Message example:
Kajkhoj Bot - notun chakri:
* Graphic Designer @ Example Studio
[actual post link]

Freelance / gig leads - original post link:
* Freelance: Freelance Graphic Designer @ Example Client
[actual post link]

Remote eligibility still needs India/global evidence; generic remote, US/UK/Canada-only rejected. Missing location never filled from search city. Full title-role matching remains conservative.
Both passes failed -> one friendly send attempt per user. One failed -> keep accepted results and add a short incompleteness note; if no accepted results and one pass failed, friendly error instead of false "no jobs". Both succeeded with zero -> original matching-zero behavior. No second fallback send after Telegram timeout; chunk stop and today-flag clearing unchanged. Original cross-run/overlap duplicates remain possible; no persistent sent-job ledger added.
Tests mocked only; trigger existing /today workflow and inspect output after deployment. No live scrape/contact/send/deployment performed.
