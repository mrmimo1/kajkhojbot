"""Simple scam-warning flags from the posting text. Rules only, no AI, no network.
This NEVER says a job is genuine. It only points out warning signs it can see."""
import re

RULES = (
    ("fee", r"\b(?:registration|security|joining|training|processing|refundable)\s+(?:fee|fees|deposit|charges?)\b|\bpay\s+(?:a\s+)?(?:fee|deposit)\b|\bsend\s+money\b"),
    ("chat", r"\b(?:whatsapp|telegram)\b"),
    ("freemail", r"@(?:gmail|yahoo|hotmail|outlook|rediffmail)\.com\b"),
    ("income", r"\bguaranteed\s+(?:income|salary|earning)s?\b|\bearn\s+(?:rs\.?|inr|₹)?\s*\d[\d,]*\s*(?:/|per)\s*(?:day|daily|week)\b|\bno\s+(?:experience|interview)\s+(?:needed|required)\b.{0,40}\bearn\b"),
)


def warning_reasons(post):
    blob = " ".join([str(post.get("title") or ""), str(post.get("company") or ""),
                     str(post.get("description") or "")])
    return [name for name, pat in RULES if re.search(pat, blob, flags=re.I | re.S)]
