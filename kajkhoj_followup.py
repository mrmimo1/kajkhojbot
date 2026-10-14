// JavaScript-compatible TypeScript; no external dependencies.
// Worker AI model is configured in GitHub, not called from this webhook.
const env = (key) => Deno.env.get(key) ?? "";
const BOT_TOKEN = env("TELEGRAM_BOT_TOKEN");
const WEBHOOK_SECRET = env("TELEGRAM_WEBHOOK_SECRET");
const GH_PAT = env("GH_PAT");
const SUPABASE_URL = env("SUPABASE_URL").replace(/\/$/, "");
const SERVICE_KEY = env("SUPABASE_SERVICE_ROLE_KEY");
const GH_REPO = "mrmimo1/kajkhojbot";
const GH_WORKFLOW = "daily.yml";
const DB_HEADERS = {
  apikey: SERVICE_KEY,
  Authorization: `Bearer ${SERVICE_KEY}`,
  "Content-Type": "application/json",
};
const LANGUAGES = ["banglish", "english", "hinglish"];
export const normalizeLanguage = (value) => LANGUAGES.includes(String(value ?? "").trim().toLowerCase())
  ? String(value).trim().toLowerCase() : "banglish";
const COPY = {
 banglish: {
  successAsk: "Darun khobor! 🎉 Tumi job peyecho? Count-e nijer self-report save korte /gotjob pathao. Ekjon ekbar-i count hobe. Eta KajKhoj thekei job hoyeche bole proof noy.",
  successSaved: "Obhinondon! 🎉 Tomar notun shuruta bhalo hok. Tomar self-reported job success save korechi, ekbar-i count hobe. Alert bondho korte chaile /stop.",
  successAlready: "Tomar khobor agei save ache 🎉 Ekjon-ke ekbar-i count kori. Notun shurur jonno shubhechha!",
  successError: "Success report save/confirm korte parini. Ektu pore /gotjob abar try koro.",
  successRemoved: "Tomar success report tule dilam. Job alerts ar preferences same ache.",
  successHelp: "\n/gotjob - nijer job pawar khobor count-e save\n/notgotjob - bhul success report tule dao",

  btnApplied: "✅ Applied korechi", btnNotInterested: "🚫 Pochhondo noy", btnUndo: "↩️ Undo",
  labelApplied: "✅ Applied", labelHidden: "🚫 Aar dekhabo na",
  appliedSaved: "Applied hishebe save korlam ✅", hiddenSaved: "Thik ache, ei job aar dekhabo na.", undone: "Undo hoyeche.",
  expired: "Ei button-er somoy shesh. Notun digest-e abar pabe.", tapError: "Save korte parini. Ektu pore abar tap koro.",
  appliedHelp: "\n/applied - jegulote Applied korechho tar list",
  appliedHeader: "Tumi ei job gulote Applied korecho:", appliedEmpty: "Ekhono kono job-e Applied tap koro ni. Job-er niche Applied korechi button ache.",
  appliedError: "List ekhon dekhate parchhi na. Ektu pore abar try koro.",
  fu_c1: "📞 Hya, call esheche",
  fu_c0: "⏳ Ekhono na",
  fu_cx: "❌ Reject / hoyni",
  fu_i1: "✅ Interview hoye geche",
  fu_i0: "⏳ Ekhono na",
  fu_ix: "🚫 Aar egochhe na",
  fu_o1: "🎉 Job peyechi",
  fu_o0: "⏳ Ekhono opekkha",
  fu_ox: "❌ Pai ni",
  fuA_c1: "Darun khobor! 📞 Kichu din por interview niye jiggesh korbo.",
  fuA_c0: "Thik ache, kichu din por abar jiggesh korbo.",
  fuA_cx: "Shune kharap laglo. Cholte thako, roj sokale notun job ashe.",
  fuA_i1: "Khub bhalo! ✅ Duo din por result jiggesh korbo.",
  fuA_i0: "Thik ache, kichu din por abar jiggesh korbo.",
  fuA_ix: "Thik ache, note korlam. Roj sokale notun job ashe.",
  fuA_o0: "Thik ache, shubhechha. Pore abar jiggesh korbo.",
  fuA_ox: "Shune kharap laglo. Cholte thako, porer-ta ashche.",
  fuA_stale: "Ei proshner uttor agei deoa hoyeche ba eta bondho.",
  stage_applied: "Applied",
  stage_call: "Call esheche",
  stage_interview: "Interview hoyeche",
  stage_got_job: "Job peyechi 🎉",
  stage_closed: "Bondho",
  welcome: "Swagatam! ", unknown: "Ei command ta chini na.",
  choose: "Kon language e kotha bolbo?\n/language banglish - Bengali + English\n/language english - English\n/language hinglish - Hindi + English\nEkhon: {language}",
  languageFirst: "Age /keywords diye job type ar city save koro. Tarpor /language diye nijer language choose koro.",
  languageSaved: "Language save hoyeche: {language}. Ebar bot-er reply ar job alert ei language e pabe.",
  languageError: "Language save/confirm korte parini. Ektu pore abar try koro.",
  parseError: "Ekta clear job type ar city dao. Alada role ekshathe noy.\n/keywords digital marketing Kolkata\n/keywords content writer, New Delhi\nOnno multiword city hole role ar city-r majhe comma dao.",
  saveError: "Save korte somossa hocche. Ektu pore abar try koro.",
  saved: "Save hoyeche: {profession} - {city}\n{normalized}Daily alert existing schedule-e cholbe. Ekhoni dekhte /today pathao. AI consent-er jonno /ai dekho. Language choose korte /language.",
  normalized: "Digital/social/content phrase gulo digital marketing family-te rakhlam. Remote/gig existing rule-e search hobe; remote-only filter set hoyni.\n",
  first: "Age /keywords set koro. Example: /keywords digital marketing Kolkata",
  aiError: "AI setting save hoyni. Ektu pore abar try koro.",
  aiConfirm: "AI setting confirm korte parini. /ai diye notice dekho.",
  aiOn: "AI on hoyeche.", aiOff: "AI off hoyeche. Normal jobs/gigs cholbe.",
  notReady: "Ei feature ekhono ready noy: save, cover note ar interview prep. Job-er niche Applied korechi / Pochhondo noy button ache, ar /applied-e list pabe. /today diye job dekho.",
  stopError: "Somossa hocche. Ektu pore /stop abar try koro.",
  stopped: "Alert bondho, profile delete kore dilam. Abar shuru korte /keywords pathao; AI default off ar language Banglish thakbe.",
  error: "Ektu jhamela hocche 🙏 Ektu pore abar try koro.",
  dispatchError: "Ekhon job search shuru korte parchhi na. Ektu pore abar try koro.",
  searching: "Job search shuru korchi. Queue ar source-er upor somoy lagte pare; result worker pathabe.",
  aiNotice: "AI default off. Chaile /ai on, bondho korte /ai off. AI on hole tomar profession ar job post-er title/description configured Gemini/Groq/OpenRouter-e jabe. Gemini free-tier lekha Google improvement-e use hote pare. Personal CV ba secret dio na. Eta title-match explanation, qualification ba chakri pawar guarantee noy. Salary sudhu original post-e thakle dekhano hoy. Dine 3 AI explanation batch-er limit; failed attempt-o count hoy.",
  help: "KajKhoj commands:\n\n/keywords <job type> <city>\nExample: /keywords digital marketing Kolkata\nMultiword city: /keywords content writer, New Delhi\nEkbare ekta clear job family dao. City-r age comma dile bujhte subidha hoy.\n\n/today - ekhoni job search\n/language - Banglish, English ba Hinglish\n/ai on | /ai off - AI title-match note\n/stop - alert bondho ar profile delete\n/help - command gulo dekho\n\n/save, /applied, /cover, /prep ekhono ready noy.\nDaily alert existing schedule onujayi."
 },
 english: {
  successAsk: "That sounds like good news! 🎉 Did you get a job? Send /gotjob to save your self-report in the count. Each user counts once. This is not proof that KajKhoj got you the job.",
  successSaved: "Congratulations! 🎉 Wishing you a good start. Your self-reported job success is saved and counts once. Use /stop if you want to stop alerts.",
  successAlready: "Your news is already saved 🎉 Each user counts once. Wishing you a good start!",
  successError: "I couldn't save or confirm your success report. Please try /gotjob again later.",
  successRemoved: "Your success report was removed. Your job alerts and preferences are unchanged.",
  successHelp: "\n/gotjob - save your own job success in the count\n/notgotjob - remove an incorrect success report",

  btnApplied: "✅ I applied", btnNotInterested: "🚫 Not interested", btnUndo: "↩️ Undo",
  labelApplied: "✅ Applied", labelHidden: "🚫 Hidden",
  appliedSaved: "Saved as applied ✅", hiddenSaved: "Okay, I won't show this job again.", undone: "Undone.",
  expired: "This button has expired. You'll see fresh jobs in the next digest.", tapError: "I couldn't save that. Please tap again later.",
  appliedHelp: "\n/applied - list jobs you marked as applied",
  appliedHeader: "Jobs you marked as applied:", appliedEmpty: "You haven't tapped Applied on any job yet. Look for the I applied button under each job.",
  appliedError: "I can't show the list right now. Please try again later.",
  fu_c1: "📞 Yes, got a call",
  fu_c0: "⏳ Not yet",
  fu_cx: "❌ Rejected / no luck",
  fu_i1: "✅ Interview done",
  fu_i0: "⏳ Not yet",
  fu_ix: "🚫 Not going ahead",
  fu_o1: "🎉 I got the job",
  fu_o0: "⏳ Still waiting",
  fu_ox: "❌ Didn't get it",
  fuA_c1: "Great news! 📞 I'll ask about the interview in a few days.",
  fuA_c0: "Okay, I'll check again in a few days.",
  fuA_cx: "Sorry to hear that. Keep going, new jobs arrive every morning.",
  fuA_i1: "Well done! ✅ I'll check on the result in a couple of days.",
  fuA_i0: "Okay, I'll check again in a few days.",
  fuA_ix: "Okay, noted. New jobs arrive every morning.",
  fuA_o0: "Okay, fingers crossed. I'll ask again later.",
  fuA_ox: "Sorry to hear that. Keep going, the next one is coming.",
  fuA_stale: "This question was already answered or is closed.",
  stage_applied: "Applied",
  stage_call: "Got a call",
  stage_interview: "Interview done",
  stage_got_job: "Got the job 🎉",
  stage_closed: "Closed",
  welcome: "Welcome! ", unknown: "I don't know that command.",
  choose: "Which language should I use?\n/language banglish - Bengali + English\n/language english - English\n/language hinglish - Hindi + English\nCurrent: {language}",
  languageFirst: "First save your job type and city with /keywords. Then choose your language with /language.",
  languageSaved: "Language saved: {language}. Bot replies and job alerts will now use this language.",
  languageError: "I couldn't save or confirm your language. Please try again later.",
  parseError: "Give one clear job type and city, rather than several different roles.\n/keywords digital marketing Kolkata\n/keywords content writer, New Delhi\nFor another multiword city, put a comma between the role and city.",
  saveError: "I couldn't save that. Please try again later.",
  saved: "Saved: {profession} - {city}\n{normalized}Daily alerts will follow the existing schedule. Send /today to search now, /ai for the AI consent notice, or /language to choose your language.",
  normalized: "I grouped the digital/social/content phrases under digital marketing. Remote/gig searches follow existing rules; no remote-only filter was set.\n",
  first: "Set /keywords first. Example: /keywords digital marketing Kolkata",
  aiError: "Your AI setting wasn't saved. Please try again later.",
  aiConfirm: "I couldn't confirm your AI setting. Use /ai to read the notice.",
  aiOn: "AI is on.", aiOff: "AI is off. Normal jobs/gigs will continue.",
  notReady: "This feature isn't ready yet: saving jobs, cover notes and interview prep. Use the buttons under each job, and /applied to see your list. Use /today to see jobs.",
  stopError: "Something went wrong. Please try /stop again later.",
  stopped: "Alerts stopped and your profile was deleted. Send /keywords to restart; AI will default to off and language to Banglish.",
  error: "Something went wrong 🙏 Please try again in a little while.",
  dispatchError: "I couldn't start the job search right now. Please try again later.",
  searching: "Starting your job search. The queue and sources may take some time; the worker will send the results.",
  aiNotice: "AI is off by default. Use /ai on to enable it or /ai off to stop it. When enabled, your profession and job-post titles/descriptions go to the configured Gemini/Groq/OpenRouter provider. Google may use Gemini free-tier text to improve its products. Don't share a personal CV or secrets. These are title-match explanations, not proof of qualifications or a job guarantee. Salary is shown only when listed in the original post. Limit: 3 AI explanation batches per day; failed attempts count too.",
  help: "KajKhoj commands:\n\n/keywords <job type> <city>\nExample: /keywords digital marketing Kolkata\nMultiword city: /keywords content writer, New Delhi\nUse one clear job family. A comma before the city helps.\n\n/today - search for jobs now\n/language - Banglish, English or Hinglish\n/ai on | /ai off - AI title-match note\n/stop - stop alerts and delete your profile\n/help - see commands\n\n/save, /applied, /cover, /prep aren't ready yet.\nDaily alerts follow the existing schedule."
 },
 hinglish: {
  successAsk: "Yeh toh achhi khabar lag rahi hai! 🎉 Tumhe job mil gayi? Apna self-report count mein save karne ke liye /gotjob bhejo. Har user ek baar count hoga. Yeh KajKhoj se hi job mili, iska proof nahi hai.",
  successSaved: "Badhai ho! 🎉 Nayi shuruaat achhi ho. Tumhara self-reported job success save ho gaya, ek baar count hoga. Alerts band karne ke liye /stop.",
  successAlready: "Tumhari khabar pehle se save hai 🎉 Har user ek baar count hota hai. Nayi shuruaat ke liye shubhkamnayein!",
  successError: "Success report save ya confirm nahi kar paya. Thodi der baad /gotjob phir try karo.",
  successRemoved: "Tumhara success report hata diya. Job alerts aur preferences same hain.",
  successHelp: "\n/gotjob - apni job milne ki khabar count mein save karo\n/notgotjob - galat success report hatao",

  btnApplied: "✅ Apply kar diya", btnNotInterested: "🚫 Interested nahi", btnUndo: "↩️ Undo",
  labelApplied: "✅ Applied", labelHidden: "🚫 Ab nahi dikhaunga",
  appliedSaved: "Applied ke taur par save kar diya ✅", hiddenSaved: "Theek hai, yeh job dobara nahi dikhaunga.", undone: "Undo ho gaya.",
  expired: "Yeh button expire ho gaya. Agle digest mein nayi jobs milengi.", tapError: "Save nahi kar paya. Thodi der baad phir tap karo.",
  appliedHelp: "\n/applied - jin jobs par Applied dabaya unki list",
  appliedHeader: "Tumne in jobs par Applied dabaya hai:", appliedEmpty: "Abhi kisi job par Applied nahi dabaya. Har job ke neeche Apply kar diya button hai.",
  appliedError: "Abhi list nahi dikha paya. Thodi der baad phir try karo.",
  fu_c1: "📞 Haan, call aaya",
  fu_c0: "⏳ Abhi nahi",
  fu_cx: "❌ Reject / nahi hua",
  fu_i1: "✅ Interview ho gaya",
  fu_i0: "⏳ Abhi nahi",
  fu_ix: "🚫 Aage nahi badha",
  fu_o1: "🎉 Job mil gayi",
  fu_o0: "⏳ Abhi intezaar",
  fu_ox: "❌ Nahi mili",
  fuA_c1: "Badhiya khabar! 📞 Kuch din baad interview ke baare mein poochhunga.",
  fuA_c0: "Theek hai, kuch din baad phir poochhunga.",
  fuA_cx: "Sunke bura laga. Chalte raho, roz subah nayi jobs aati hain.",
  fuA_i1: "Bahut badhiya! ✅ Do din baad result poochhunga.",
  fuA_i0: "Theek hai, kuch din baad phir poochhunga.",
  fuA_ix: "Theek hai, note kar liya. Roz subah nayi jobs aati hain.",
  fuA_o0: "Theek hai, best of luck. Baad mein phir poochhunga.",
  fuA_ox: "Sunke bura laga. Chalte raho, agli job aa rahi hai.",
  fuA_stale: "Is sawaal ka jawab ho chuka hai ya yeh band hai.",
  stage_applied: "Applied",
  stage_call: "Call aaya",
  stage_interview: "Interview ho gaya",
  stage_got_job: "Job mil gayi 🎉",
  stage_closed: "Band",
  welcome: "Swagat hai! ", unknown: "Yeh command samajh nahi aaya.",
  choose: "Kaunsi language mein baat karun?\n/language banglish - Bengali + English\n/language english - English\n/language hinglish - Hindi + English\nAbhi: {language}",
  languageFirst: "Pehle /keywords se job type aur city save karo. Phir /language se apni language chuno.",
  languageSaved: "Language save ho gayi: {language}. Ab bot ke replies aur job alerts isi language mein aayenge.",
  languageError: "Language save ya confirm nahi kar paya. Thodi der baad phir try karo.",
  parseError: "Ek clear job type aur city likho. Alag roles ek saath mat likho.\n/keywords digital marketing Kolkata\n/keywords content writer, New Delhi\nDoosri multiword city ke liye role aur city ke beech comma lagao.",
  saveError: "Save karne mein dikkat ho rahi hai. Thodi der baad phir try karo.",
  saved: "Save ho gaya: {profession} - {city}\n{normalized}Daily alerts existing schedule par aayenge. Abhi search ke liye /today bhejo. AI consent notice ke liye /ai aur language chunne ke liye /language.",
  normalized: "Digital/social/content phrases ko digital marketing family mein rakha. Remote/gig search existing rules par chalegi; remote-only filter set nahi hua.\n",
  first: "Pehle /keywords set karo. Example: /keywords digital marketing Kolkata",
  aiError: "AI setting save nahi hui. Thodi der baad phir try karo.",
  aiConfirm: "AI setting confirm nahi kar paya. /ai se notice dekho.",
  aiOn: "AI on ho gaya.", aiOff: "AI off ho gaya. Normal jobs/gigs aate rahenge.",
  notReady: "Yeh feature abhi ready nahi hai: save, cover note aur interview prep. Har job ke neeche buttons hain, aur /applied se list dekho. Jobs ke liye /today bhejo.",
  stopError: "Dikkat aa rahi hai. Thodi der baad /stop phir try karo.",
  stopped: "Alerts band aur profile delete kar di. Phir shuru karne ke liye /keywords bhejo; AI default off aur language Banglish hogi.",
  error: "Thodi dikkat aa rahi hai 🙏 Thodi der baad phir try karo.",
  dispatchError: "Abhi job search shuru nahi kar paya. Thodi der baad phir try karo.",
  searching: "Job search shuru kar raha hoon. Queue aur sources ki wajah se thoda time lag sakta hai; worker results bhejega.",
  aiNotice: "AI default off hai. Chaho toh /ai on, band karne ke liye /ai off. AI on hone par tumhara profession aur job post ke title/description configured Gemini/Groq/OpenRouter ko jayenge. Google Gemini free-tier text ko products improve karne ke liye use kar sakta hai. Personal CV ya secrets mat bhejo. Yeh title-match explanation hai, qualification ya job milne ki guarantee nahi. Salary sirf original post mein di ho toh dikhate hain. Din mein 3 AI explanation batches ki limit; failed attempts bhi count hote hain.",
  help: "KajKhoj commands:\n\n/keywords <job type> <city>\nExample: /keywords digital marketing Kolkata\nMultiword city: /keywords content writer, New Delhi\nEk clear job family likho. City se pehle comma lagana madad karta hai.\n\n/today - abhi job search\n/language - Banglish, English ya Hinglish\n/ai on | /ai off - AI title-match note\n/stop - alerts band aur profile delete\n/help - commands dekho\n\n/save, /applied, /cover, /prep abhi ready nahi hain.\nDaily alerts existing schedule par aayenge."
 }
};
export function copy(key, language, values = {}) {
 return COPY[normalizeLanguage(language)][key].replace(/\{(\w+)\}/g, (match, name) =>
   Object.hasOwn(values, name) ? String(values[name]) : match);
}
const help = (language) => copy("help", language) + copy("successHelp", language) + copy("appliedHelp", language) + "\n\n" + copy("aiNotice", language);

async function reply(chatId, text) {
  try {
    // A failed/ambiguous send is never retried with a second message.
    const r = await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chat_id: chatId, text, disable_web_page_preview: true }),
      signal: AbortSignal.timeout(15000),
    });
    if (!r.ok) console.log("sendMessage failed", r.status);
  } catch {
    console.log("sendMessage failed");
  }
}

const CITIES = [
  "new delhi", "navi mumbai", "greater noida", "salt lake", "north 24 parganas",
  "south 24 parganas", "kolkata", "calcutta", "mumbai", "delhi", "bengaluru",
  "bangalore", "hyderabad", "chennai", "pune", "ahmedabad", "noida", "gurugram",
  "gurgaon", "howrah", "durgapur", "siliguri", "jaipur", "lucknow", "bhubaneswar",
].sort((a, b) => b.length - a.length);
const DIGITAL_PHRASES = [
  "digital marketing", "social media marketing", "social media management",
  "content calendar planning",
].sort((a, b) => b.length - a.length);

export function parseKeywords(args) {
  const text = args.trim().replace(/\s+/g, " ");
  if (!text || text.length > 500) return null;
  let profession = "", city = "";
  if (text.includes(",")) {
    // Exactly one separator: multiple role/city alternatives need clarification.
    if (text.split(",").length !== 2) return null;
    [profession, city] = text.split(",").map((x) => x.trim());
  } else {
    const lower = text.toLowerCase();
    const suffix = CITIES.find((c) => lower.endsWith(" " + c));
    if (suffix) {
      city = text.slice(-suffix.length);
      profession = text.slice(0, -suffix.length).trim();
    } else {
      // Preserve old one-word city syntax; use comma for arbitrary multiword cities.
      const parts = text.split(" ");
      if (parts.length < 2) return null;
      city = parts.pop();
      profession = parts.join(" ");
    }
  }
  if (!profession || !city || city.length > 40 || !/^[\p{L} .'-]+$/u.test(city)) return null;
  if (/^(remote|job|jobs|freelance|projects|and|or)$/i.test(city)) return null;
  const originalRole = profession;
  // These are intent words, not separate saved worker filters. Worker retains its
  // existing eligible-remote/gig behavior; we do not claim a remote-only setting.
  let role = profession.toLowerCase().replace(/\b(remote jobs?|freelance projects?)\b/g, " ")
    .replace(/\s+/g, " ").trim();
  let rest = role, matched = 0;
  for (const phrase of DIGITAL_PHRASES) {
    if (rest.includes(phrase)) {
      rest = rest.replaceAll(phrase, " ");
      matched++;
    }
  }
  rest = rest.replace(/\s+/g, " ").trim();
  const normalized = matched > 0 && rest === "";
  if (normalized) profession = "digital marketing";
  else {
    // Never silently drop another role mixed into a recognized digital family.
    if (matched > 0) return null;
    if (role.length > 60 || role.split(" ").length > 6 || /\b(and|or)\b|[;|/]/.test(role)) return null;
    if (role !== originalRole.toLowerCase()) return null;
    profession = originalRole;
  }
  if (profession.length < 3 || profession.length > 60 || !/^[\p{L}\p{N} .+#'-]+$/u.test(profession)) return null;
  if (/^(marketing|manager|jobs?|freelance|remote)$/i.test(profession)) return null;
  return { profession, city, normalized: normalized && profession !== originalRole.toLowerCase() };
}

// Conservative phrase hints, not an all-language classifier or verified outcome.
// No messages or excerpts are stored. Explicit /gotjob confirms a self-report.
export function looksLikeJobSuccess(input) {
 const text = String(input).normalize("NFKC").toLowerCase().replace(/[’']/g, "").replace(/\s+/g, " ").trim();
 if (!text || text.length > 800) return false;
 // Negation, hopes, hypotheticals and third-party mentions are not success hints.
 if (/\b(?:not|no|never|havent|hasnt|didnt|dont|did not|have not|hope|wish|if|when|nahi|nahin|nai|ni|noy|na|jodi|hobe|pabo|milegi|milega|friend|brother|sister)\b|না|নেই|পাইনি|বন্ধু|भाई|दोस्त|नहीं|नही|मिलेगी|मिलेगा/.test(text)) return false;
 if (/[?？]/.test(text) || /\bjob\s+(?:description|alert|link|post|listing|interview|offer scam)\b/.test(text)) return false;
 return /\bi (?:got|have got|have gotten|landed|secured) (?:a |the |my |this )?(?:new )?job\b/.test(text)
  || /\b(?:ami\s+)?(?:job|chakri|chakri ta|job ta)\s+(?:ta\s+)?(?:peyechi|peye gechi|peye gechhi|peyেছি)\b/.test(text)
  || /(?:আমি\s*)?(?:চাকরি|জব)(?:টা|টি)?\s*(?:পেয়েছি|পেয়েছি|পেয়ে গেছি|পেয়ে গেছি)/.test(text)
  || /\b(?:mujhe|meri|mera|maine)\b.{0,45}\b(?:job|naukri)\b.{0,20}\b(?:mil gayi|mil gai|mil gaya|mil gyi|lag gayi|lag gai|mil chuki)\b/.test(text)
  || /(?:मुझे|मेरी|मैंने).{0,40}(?:जॉब|नौकरी).{0,20}(?:मिल गई|मिल गयी|मिल गया|लग गई|लग गयी)/.test(text);
}

async function getUser(chatId) {
  const r = await fetch(
    `${SUPABASE_URL}/rest/v1/users?chat_id=eq.${chatId}&select=chat_id,profession,city,ai_enabled,language,got_job_at`,
    { headers: DB_HEADERS, signal: AbortSignal.timeout(15000) },
  );
  if (!r.ok) throw new Error("db read failed");
  const rows = await r.json();
  return rows.length ? rows[0] : null;
}

export async function handle(chatId, input) {
 let language = "banglish";
 let user;
 try { user = await getUser(chatId); language = normalizeLanguage(user?.language); }
 catch {
  // Stored preference is unavailable. One short multilingual fallback, no action.
  await reply(chatId, "Ektu pore try koro / Please try again later / Thodi der baad try karo.");
  return;
 }
 const t = (key, values = {}) => copy(key, language, values);
 try {
  const m = input.trim().match(/^\/(\w+)(?:@\w+)?(?:\s+([\s\S]*))?$/);
  if (!m) {
   await reply(chatId, user && looksLikeJobSuccess(input) ? t("successAsk") : help(language)); return;
  }
  const cmd = m[1].toLowerCase(), args = (m[2] ?? "").trim();
  if (cmd === "start" || cmd === "help") {
   await reply(chatId, t("welcome") + help(language)); return;
  }
  if (cmd === "gotjob" || cmd === "notgotjob") {
   if (!user) { await reply(chatId,t("first")); return; }
   if (cmd === "gotjob" && user.got_job_at) { await reply(chatId,t("successAlready")); return; }
   const removal = cmd === "notgotjob";
   const url = `${SUPABASE_URL}/rest/v1/users?chat_id=eq.${chatId}` + (removal ? "" : "&got_job_at=is.null");
   const r = await fetch(url, {
    method:"PATCH", headers:{...DB_HEADERS, Prefer:"return=representation"},
    body:JSON.stringify({got_job_at:removal ? null : new Date().toISOString()}),
    signal:AbortSignal.timeout(15000),
   });
   if (!r.ok) { await reply(chatId,t("successError")); return; }
   const rows = await r.json();
   if (!Array.isArray(rows) || rows.length !== 1 || (removal ? rows[0].got_job_at !== null : !rows[0].got_job_at)) {
    // An overlapping confirmation may have won the null-conditional update.
    const current = await getUser(chatId);
    if (!removal && current?.got_job_at) { await reply(chatId,t("successAlready")); return; }
    await reply(chatId,t("successError")); return;
   }
   await reply(chatId,t(removal ? "successRemoved" : "successSaved")); return;
  }
  if (cmd === "language") {
   const choice = args.toLowerCase();
   if (!LANGUAGES.includes(choice)) { await reply(chatId, t("choose", {language})); return; }
   if (!user) { await reply(chatId, t("languageFirst")); return; }
   const r = await fetch(`${SUPABASE_URL}/rest/v1/users?chat_id=eq.${chatId}`, {
    method: "PATCH", headers: {...DB_HEADERS, Prefer: "return=representation"},
    body: JSON.stringify({language: choice, updated_at: new Date().toISOString()}),
    signal: AbortSignal.timeout(15000),
   });
   if (!r.ok) { await reply(chatId, t("languageError")); return; }
   const rows = await r.json();
   if (!Array.isArray(rows) || rows.length !== 1 || rows[0].language !== choice) {
    await reply(chatId, t("languageError")); return;
   }
   language = choice;
   await reply(chatId, t("languageSaved", {language})); return;
  }
  if (cmd === "keywords") {
   const parsed = parseKeywords(args);
   if (!parsed) { await reply(chatId, t("parseError")); return; }
   const r = await fetch(`${SUPABASE_URL}/rest/v1/users?on_conflict=chat_id`, {
    method: "POST", headers: {...DB_HEADERS, Prefer: "resolution=merge-duplicates,return=minimal"},
    // Deliberately omit language and ai_enabled so updates preserve both preferences.
    body: JSON.stringify({chat_id: chatId, profession: parsed.profession,
     city: parsed.city, updated_at: new Date().toISOString()}),
    signal: AbortSignal.timeout(15000),
   });
   if (!r.ok) { await reply(chatId, t("saveError")); return; }
   await reply(chatId, t("saved", {profession:parsed.profession, city:parsed.city,
    normalized:parsed.normalized ? t("normalized") : ""})); return;
  }
  if (cmd === "ai") {
   if (!["on","off"].includes(args.toLowerCase())) { await reply(chatId, t("aiNotice")); return; }
   if (!user) { await reply(chatId, t("first") + "\n" + t("aiNotice")); return; }
   const enabled = args.toLowerCase() === "on";
   const r = await fetch(`${SUPABASE_URL}/rest/v1/users?chat_id=eq.${chatId}`, {
    method:"PATCH", headers:{...DB_HEADERS, Prefer:"return=representation"},
    body:JSON.stringify({ai_enabled:enabled, updated_at:new Date().toISOString()}),
    signal:AbortSignal.timeout(15000),
   });
   if (!r.ok) { await reply(chatId,t("aiError")); return; }
   const rows = await r.json();
   if (!Array.isArray(rows) || rows.length !== 1 || rows[0].ai_enabled !== enabled) {
    await reply(chatId,t("aiConfirm")); return;
   }
   await reply(chatId,enabled ? t("aiOn")+"\n"+t("aiNotice") : t("aiOff")); return;
  }
  if (cmd === "applied") {
   if (!user) { await reply(chatId,t("first")); return; }
   const r = await fetch(`${SUPABASE_URL}/rest/v1/kajkhoj_applications?chat_id=eq.${chatId}&status=eq.applied&order=applied_at.desc&limit=15&select=title,company,url,stage`, {
    headers:DB_HEADERS, signal:AbortSignal.timeout(15000),
   });
   if (!r.ok) { await reply(chatId,t("appliedError")); return; }
   const rows = await r.json();
   if (!Array.isArray(rows) || rows.length === 0) { await reply(chatId,t("appliedEmpty")); return; }
   await reply(chatId, (t("appliedHeader") + "\n\n" + rows.map((x,i) => `${i+1}. ${x.title}${x.company ? " @ " + x.company : ""}\n${t("stage_" + (["applied","call","interview","got_job","closed"].includes(x.stage) ? x.stage : "applied"))}\n${x.url}`).join("\n\n")).slice(0,4000)); return;
  }
  if (["save","cover","prep"].includes(cmd)) { await reply(chatId,t("notReady")); return; }
  if (cmd === "stop") {
   const usage = await fetch(`${SUPABASE_URL}/rest/v1/kajkhoj_ai_usage?chat_id=eq.${chatId}`, {
    method:"DELETE", headers:DB_HEADERS, signal:AbortSignal.timeout(15000),
   });
   if (!usage.ok) { await reply(chatId,t("stopError")); return; }
   for (const table of ["kajkhoj_applications", "kajkhoj_sent_jobs"]) {
    const d = await fetch(`${SUPABASE_URL}/rest/v1/${table}?chat_id=eq.${chatId}`, {
     method:"DELETE", headers:DB_HEADERS, signal:AbortSignal.timeout(15000),
    });
    if (!d.ok) { await reply(chatId,t("stopError")); return; }
   }
   const r = await fetch(`${SUPABASE_URL}/rest/v1/users?chat_id=eq.${chatId}`, {
    method:"DELETE", headers:DB_HEADERS, signal:AbortSignal.timeout(15000),
   });
   if (!r.ok) { await reply(chatId,t("stopError")); return; }
   await reply(chatId,t("stopped")); return;
  }
  if (cmd === "today") {
   if (!user?.profession || !user?.city) { await reply(chatId,t("first")); return; }
   const flag = await fetch(`${SUPABASE_URL}/rest/v1/users?chat_id=eq.${chatId}`, {
    method:"PATCH", headers:{...DB_HEADERS, Prefer:"return=minimal"},
    body:JSON.stringify({today_requested:true}), signal:AbortSignal.timeout(15000),
   });
   if (!flag.ok) { await reply(chatId,t("error")); return; }
   const gh = await fetch(`https://api.github.com/repos/${GH_REPO}/actions/workflows/${GH_WORKFLOW}/dispatches`, {
    method:"POST", headers:{Authorization:`Bearer ${GH_PAT}`, Accept:"application/vnd.github+json",
     "X-GitHub-Api-Version":"2022-11-28", "User-Agent":"kajkhoj-webhook", "Content-Type":"application/json"},
    body:JSON.stringify({ref:"main", inputs:{mode:"today"}}), signal:AbortSignal.timeout(15000),
   });
   if (!gh.ok) { console.log("github dispatch failed",gh.status); await reply(chatId,t("dispatchError")); return; }
   await reply(chatId,t("searching")); return;
  }
  await reply(chatId,t("unknown")+"\n\n"+help(language));
 } catch { console.log("handler error"); await reply(chatId,t("error")); }
}

async function tg(method, payload) {
  try {
    const r = await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/${method}`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload), signal: AbortSignal.timeout(15000),
    });
    if (!r.ok) console.log(method, "failed", r.status);
  } catch { console.log(method, "failed"); }
}

const daysFromNow = (d) => new Date(Date.now() + d * 86400000).toISOString();
// Follow-up answers: code -> [question it answers, row changes]. Each question is asked
// again after a few days on "not yet"; closing answers stop the follow-ups.
const FOLLOWUP = {
  c1: ["call", () => ({ stage: "call", ask: "interview", next_ask_at: daysFromNow(3), ask_count: 0 })],
  c0: ["call", () => ({ next_ask_at: daysFromNow(3) })],
  cx: ["call", () => ({ stage: "closed", ask: null, next_ask_at: null })],
  i1: ["interview", () => ({ stage: "interview", ask: "outcome", next_ask_at: daysFromNow(2), ask_count: 0 })],
  i0: ["interview", () => ({ next_ask_at: daysFromNow(3) })],
  ix: ["interview", () => ({ stage: "closed", ask: null, next_ask_at: null })],
  o1: ["outcome", () => ({ stage: "got_job", ask: null, next_ask_at: null })],
  o0: ["outcome", () => ({ next_ask_at: daysFromNow(5) })],
  ox: ["outcome", () => ({ stage: "closed", ask: null, next_ask_at: null })],
};

async function handleFollowup(cq, chatId, messageId, code, id, answer) {
  let language = "banglish";
  try { language = normalizeLanguage((await getUser(chatId))?.language); } catch { /* default language */ }
  const t = (key) => copy(key, language);
  const spec = FOLLOWUP[code];
  if (!spec) { await answer(); return; }
  try {
    // Only the row's owner, only while it is still Applied and still on this question.
    const r = await fetch(`${SUPABASE_URL}/rest/v1/kajkhoj_applications?id=eq.${id}&chat_id=eq.${chatId}&status=eq.applied&ask=eq.${spec[0]}`, {
      method: "PATCH", headers: { ...DB_HEADERS, Prefer: "return=representation" },
      body: JSON.stringify({ ...spec[1](), updated_at: new Date().toISOString() }), signal: AbortSignal.timeout(15000),
    });
    if (!r.ok) { await answer(t("tapError")); return; }
    const rows = await r.json();
    if (!Array.isArray(rows) || rows.length !== 1) {
      await answer(t("fuA_stale"));
      await tg("editMessageReplyMarkup", { chat_id: chatId, message_id: messageId, reply_markup: { inline_keyboard: [] } });
      return;
    }
    await tg("editMessageReplyMarkup", { chat_id: chatId, message_id: messageId,
      reply_markup: { inline_keyboard: [[{ text: t("fu_" + code), callback_data: "x:" + id }]] } });
    if (code === "o1") {
      // Same self-reported counter as /gotjob: the user tapped it themselves; counts once per user.
      const u = await fetch(`${SUPABASE_URL}/rest/v1/users?chat_id=eq.${chatId}&got_job_at=is.null`, {
        method: "PATCH", headers: { ...DB_HEADERS, Prefer: "return=representation" },
        body: JSON.stringify({ got_job_at: new Date().toISOString() }), signal: AbortSignal.timeout(15000),
      });
      const urows = u.ok ? await u.json() : null;
      await answer();
      await reply(chatId, t(!u.ok ? "successError" : Array.isArray(urows) && urows.length === 1 ? "successSaved" : "successAlready"));
      return;
    }
    await answer();
    await reply(chatId, t("fuA_" + code));
  } catch { console.log("followup error"); await answer(t("tapError")); }
}

// Applied / Not interested / Undo taps. Each row belongs to one chat; the update
// always filters on both the row id and the tapping user's own chat id.
export async function handleCallback(cq) {
  const chatId = cq?.message?.chat?.id, messageId = cq?.message?.message_id;
  const answer = (text) => tg("answerCallbackQuery", { callback_query_id: cq.id, ...(text ? { text } : {}) });
  if (!Number.isSafeInteger(chatId) || cq.message.chat.type !== "private" || cq.from?.id !== chatId) { await answer(); return; }
  const f = String(cq.data ?? "").match(/^f:([cio][01x]):([0-9a-f-]{36})$/);
  if (f) { await handleFollowup(cq, chatId, messageId, f[1], f[2], answer); return; }
  const m = String(cq.data ?? "").match(/^([anux]):([0-9a-f-]{36})$/);
  if (!m) { await answer(); return; }
  const [, act, id] = m;
  if (act === "x") { await answer(); return; }
  let language = "banglish";
  try { language = normalizeLanguage((await getUser(chatId))?.language); } catch { /* default language */ }
  const t = (key) => copy(key, language);
  const keyboardFor = {
    a: [{ text: t("labelApplied"), callback_data: "x:" + id }, { text: t("btnUndo"), callback_data: "u:" + id }],
    n: [{ text: t("labelHidden"), callback_data: "x:" + id }, { text: t("btnUndo"), callback_data: "u:" + id }],
    u: [{ text: t("btnApplied"), callback_data: "a:" + id }, { text: t("btnNotInterested"), callback_data: "n:" + id }],
  }[act];
  const now = new Date().toISOString();
  try {
    const r = await fetch(`${SUPABASE_URL}/rest/v1/kajkhoj_applications?id=eq.${id}&chat_id=eq.${chatId}`, {
      method: "PATCH", headers: { ...DB_HEADERS, Prefer: "return=representation" },
      body: JSON.stringify({ status: act === "a" ? "applied" : act === "n" ? "not_interested" : "shown",
        applied_at: act === "a" ? now : null, updated_at: now,
        stage: act === "a" ? "applied" : null, ask: act === "a" ? "call" : null,
        next_ask_at: act === "a" ? daysFromNow(2) : null, ask_count: 0 }),
      signal: AbortSignal.timeout(15000),
    });
    if (!r.ok) { await answer(t("tapError")); return; }
    const rows = await r.json();
    if (!Array.isArray(rows) || rows.length !== 1) {
      await answer(t("expired"));
      await tg("editMessageReplyMarkup", { chat_id: chatId, message_id: messageId, reply_markup: { inline_keyboard: [] } });
      return;
    }
    await answer(t(act === "a" ? "appliedSaved" : act === "n" ? "hiddenSaved" : "undone"));
    await tg("editMessageReplyMarkup", { chat_id: chatId, message_id: messageId, reply_markup: { inline_keyboard: [keyboardFor] } });
  } catch { console.log("callback error"); await answer(t("tapError")); }
}

export async function webhook(req) {
  if (req.method !== "POST") return new Response("ok");
  if (!WEBHOOK_SECRET || req.headers.get("x-telegram-bot-api-secret-token") !== WEBHOOK_SECRET) {
    return new Response("unauthorized", { status: 401 });
  }
  try {
    const update = await req.json(), msg = update.message;
    if (update.callback_query) { await handleCallback(update.callback_query); return new Response("ok"); }
    if (msg?.chat?.type === "private" && Number.isSafeInteger(msg.chat.id)) {
      if (typeof msg.text === "string") await handle(msg.chat.id, msg.text);
      else await handle(msg.chat.id, "/help");
    }
  } catch { console.log("handler error"); }
  // Preserve existing 200 policy so Telegram does not retry a partially handled update.
  return new Response("ok");
}
if (typeof Deno !== "undefined" && typeof Deno.serve === "function") Deno.serve(webhook);
