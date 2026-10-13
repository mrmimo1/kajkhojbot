"""Small local message catalog. No translation API or new subscription needed."""
LANGUAGES = {"banglish": "simple Banglish (Bengali + English, Latin letters)",
             "english": "simple English",
             "hinglish": "simple Hinglish (Hindi + English, Latin letters)"}

TEXT = {
 "banglish": {
  "error": "Ektu jhamela hocche 🙏 Ektu pore abar try koro.",
  "preferences": "/keywords diye specific job type ar city dao. Example: /keywords graphic designer Mumbai. Sudhu marketing ba manager likhle strong match bojha jay na.",
  "empty": "KajKhoj: ekhon notun matching job paini. Pore abar dekho.",
  "jobs": "KajKhoj - notun chakri:",
  "freelance": "Freelance / gig leads - original post link:",
  "partial": "Ekta source search e jhamela hoyeche; paoa matching post gulo dilam. Aro result thakte pare.",
  "salary_missing": "Salary: currency ar period soho clear kore deoa nei",
  "salary": "Post e deoa salary: ",
  "company_missing": "Company er naam deoa nei",
  "ai_note": "AI title-match note (requirements dekhe nio): ",
 },
 "english": {
  "error": "Something went wrong 🙏 Please try again in a little while.",
  "preferences": "Use /keywords with a specific job type and city. Example: /keywords graphic designer Mumbai. A broad word like marketing or manager is not enough for a clear match.",
  "empty": "KajKhoj: no new matching jobs right now. Check again later.",
  "jobs": "KajKhoj - new jobs:",
  "freelance": "Freelance / gig leads - original post link:",
  "partial": "One source search failed. Here are the matching posts we found; there may be more.",
  "salary_missing": "Salary: not listed with clear currency/period",
  "salary": "Posted salary: ",
  "company_missing": "Company not listed",
  "ai_note": "AI title-match note (check requirements): ",
 },
 "hinglish": {
  "error": "Thodi dikkat aa rahi hai 🙏 Thodi der baad phir try karo.",
  "preferences": "/keywords mein specific job type aur city likho. Example: /keywords graphic designer Mumbai. Sirf marketing ya manager se clear match samajhna mushkil hai.",
  "empty": "KajKhoj: abhi koi nayi matching job nahi mili. Baad mein phir dekho.",
  "jobs": "KajKhoj - nayi jobs:",
  "freelance": "Freelance / gig leads - original post ka link:",
  "partial": "Ek source ki search mein dikkat hui. Jo matching posts mile, woh bhej diye. Aur results ho sakte hain.",
  "salary_missing": "Salary: currency aur period ke saath clearly nahi di gayi",
  "salary": "Post mein di gayi salary: ",
  "company_missing": "Company ka naam nahi diya gaya",
  "ai_note": "AI title-match note (requirements dekh lena): ",
 },
}


def normalize_language(value):
    value = str(value or "").strip().lower()
    return value if value in LANGUAGES else "banglish"


def text(key, language="banglish"):
    return TEXT[normalize_language(language)][key]
