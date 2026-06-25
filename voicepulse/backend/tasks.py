import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.add_dll_directory(r"E:\Programming\ffmpeg-8.1.1-full_build-shared\bin")

import sys
import json
import re
import logging
from datetime import datetime
from pathlib import Path
from celery import Celery
from pymongo import MongoClient

# Ensure backend/ is on sys.path so 'services' and 'config' are importable
_backend_dir = str(Path(__file__).resolve().parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from config import cfg

_log_dir = Path(__file__).resolve().parent.parent / "logs"
_log_dir.mkdir(exist_ok=True)
_error_log = _log_dir / "task_errors.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(_log_dir / "worker.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("sentiment_pulse")

_results_dir = Path(__file__).resolve().parent.parent / "results"
_results_dir.mkdir(exist_ok=True)

app = Celery("sentiment_pulse", broker=cfg.REDIS_URL, backend=cfg.REDIS_URL)
app.conf.update(task_track_started=True, task_serializer="json", result_serializer="json")
sync_db = MongoClient(cfg.MONGO_URI)[cfg.DB_NAME]

_sys_prompt = (
    "You are a Customer Success Coach. Given the customer's historical "
    "interaction notes and their latest call sentiment analysis, generate "
    "a concise Approach Brief (max 150 words) for the CS agent. "
    "Include: tone to use, topics to avoid, key pain point to address first, "
    "and one suggested opener. Be warm, empathetic, and tactical."
)

# ---------------------------------------------------------------------------
# Smart name detection — expanded patterns
# ---------------------------------------------------------------------------
_NAME_PATTERNS = [
    # "my name is John" / "I'm Sarah" / "this is Priya"
    re.compile(r"(?:my name (?:is|'?s)|i'?m|this is|name'?s?s?|i am) +([A-Z][a-z]+(?:[ -][A-Z][a-z]+)?)", re.I),
    # "call me Raj" / "you can call me Amit"
    re.compile(r"(?:call me|you can call me|people call me) +([A-Z][a-z]+(?:[ -][A-Z][a-z]+)?)", re.I),
    # "Mr./Ms./Mrs. Patil here"
    re.compile(r"(?:mr\.?|ms\.?|mrs\.?|dr\.?) +([A-Z][a-z]+(?:[ -][A-Z][a-z]+)?)", re.I),
    # Greeting patterns: "hi this is Vikram" / "hello, Ramesh speaking"
    re.compile(r"(?:hi|hello|hey)[,.]? (?:this is|it'?s) +([A-Z][a-z]+(?:[ -][A-Z][a-z]+)?)", re.I),
    # Bare name at start: "Rajesh here" / "Sunita, can you..." / "Yes, Ananya"
    re.compile(r"(?:^|[,.]\s*)([A-Z][a-z]{2,})\s+(?:here[,.]?|speaking|from|call)", re.I),
]

# Words that are NEVER valid customer names
_NAME_BLACKLIST = {
    "trying", "to", "the", "and", "for", "you", "can", "this", "that",
    "what", "with", "have", "from", "your", "just", "like", "will",
    "okay", "hello", "yeah", "right", "well", "actually", "please",
    "thank", "thanks", "sorry", "about", "they", "there", "their",
    "speaking", "calling", "would", "could", "should", "need", "want",
    "going", "been", "here", "was", "how", "when", "where", "why",
    "sure", "fine", "great", "good", "morning", "afternoon", "evening",
    "customer", "support", "service", "product", "problem", "issue",
    "today", "yesterday", "tomorrow", "now", "then", "before", "after",
}

_AGENT_PATTERNS = [
    # Opening phrases (strong signal)
    re.compile(r"(?:how (?:can|may) i help|thank you for (?:calling|contacting|reaching out)|welcome to (?:customer|tech|product|our))"),
    # Agent action phrases
    re.compile(r"(?:let me (?:look|check|pull|see|verify|review|transfer|connect)|one moment|bear with me|i'?ll (?:transfer|connect|look into))"),
    # Empathy / de-escalation
    re.compile(r"(?:i understand (?:your|the) (?:concern|frustration|issue|problem)|i (?:apologize|'?m sorry) for)"),
    # Role identification
    re.compile(r"(?:customer (?:support|service|care)|tech(?:nical)? support|representative|my name is [A-Z][a-z]+ (?:and|from|with) (?:customer|support|tech))"),
    # Closing phrases
    re.compile(r"(?:thank you for (?:your (?:time|patience|call)|calling)|is there (?:anything else|something else) i can (?:help|do|assist))"),
]

def _detect_speaker_roles(segments: list[dict]) -> dict:
    """Multi-signal speaker role detection."""
    speaker_texts = {}
    speaker_duration = {}
    first_speaker = None
    for seg in segments:
        spk = seg.get("speaker", "SPEAKER_00")
        if first_speaker is None:
            first_speaker = spk
        speaker_texts.setdefault(spk, []).append(seg.get("text", ""))
        dur = seg["end"] - seg["start"]
        speaker_duration[spk] = speaker_duration.get(spk, 0) + dur

    # Score each speaker on multiple signals
    speaker_scores = {}
    for spk, texts in speaker_texts.items():
        combined = " ".join(texts)
        word_count = sum(len(t.split()) for t in texts)
        turn_count = len(texts)

        # Signal 1: Agent phrase matches (strongest signal)
        agent_phrases = sum(1 for pat in _AGENT_PATTERNS if pat.search(combined))

        # Signal 2: First speaker is usually the agent (greets the customer)
        is_first = 1.0 if spk == first_speaker else 0.0

        # Signal 3: Agent usually talks less overall (customer tells the story)
        # Normalize — if one speaker talks > 60%, they're likely the customer
        total_dur = sum(speaker_duration.values())
        talk_ratio = speaker_duration[spk] / total_dur if total_dur > 0 else 0.5
        # Higher score for shorter talker (more likely agent)
        dur_signal = 2.0 if talk_ratio < 0.45 else (1.0 if talk_ratio < 0.6 else 0.0)

        # Composite score
        speaker_scores[spk] = (agent_phrases * 3.0) + (is_first * 1.5) + dur_signal

    # Highest score = agent
    agent_spk = max(speaker_scores, key=speaker_scores.get) if speaker_scores else "SPEAKER_00"
    customer_spk = [s for s in speaker_scores if s != agent_spk]

    # Extract customer name from ALL speakers (customer name can appear in agent speech too)
    customer_name = ""
    # First try customer speaker(s)
    for spk in ([c for c in customer_spk] if customer_spk else ["SPEAKER_00"]):
        combined = " ".join(speaker_texts.get(spk, []))
        customer_name = _extract_name(combined)
        if customer_name:
            break
    # Fallback: search all speaker text
    if not customer_name:
        all_text = " ".join(" ".join(v) for v in speaker_texts.values())
        customer_name = _extract_name(all_text)

    return {
        "agent": agent_spk,
        "customer": customer_spk[0] if customer_spk else "SPEAKER_01",
        "customer_name": customer_name
    }

def _extract_name(text: str) -> str:
    """Extract a valid customer name from text using expanded patterns."""
    for pat in _NAME_PATTERNS:
        m = pat.search(text)
        if m:
            raw_name = m.group(1).strip()
            # Validate: must be 2-20 chars, not a common word
            if 2 <= len(raw_name) <= 20 and raw_name.lower() not in _NAME_BLACKLIST:
                # Check it looks like a name (capitalized)
                if raw_name[0].isupper():
                    return raw_name
    return ""

def _build_speaker_blocks(segments: list[dict], roles: dict) -> list[dict]:
    """Collapse consecutive same-speaker segments into conversation blocks."""
    blocks = []
    current_role = None
    current_text = []

    for seg in segments:
        spk = seg.get("speaker", "SPEAKER_00")
        role = "agent" if spk == roles["agent"] else "customer"
        text = seg.get("text", "").strip()
        if not text:
            continue
        if role == current_role:
            current_text.append(text)
        else:
            if current_text:
                blocks.append({"role": current_role, "text": " ".join(current_text)})
            current_role = role
            current_text = [text]
    if current_text:
        blocks.append({"role": current_role, "text": " ".join(current_text)})
    return blocks

# ---------------------------------------------------------------------------
# GPT Brief (non-critical)
# ---------------------------------------------------------------------------
def _brief(cid: str, result: dict) -> str:
    from openai import OpenAI

    if not cfg.GROQ_API_KEY:
        raise RuntimeError("No GROQ_API_KEY configured")

    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=cfg.GROQ_API_KEY)

    cust = sync_db.customers.find_one({"cid": cid})
    past = list(sync_db.calls.find({"cid": cid}).sort("processed_at", -1).limit(10))
    notes = cust.get("notes", []) if cust else []
    ctx = {"notes": notes, "past_calls": [p.get("tag", "") for p in past]}
    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": _sys_prompt},
            {"role": "user", "content": json.dumps({"history": ctx, "latest": result})}
        ],
        max_tokens=250
    )
    return resp.choices[0].message.content

# ---------------------------------------------------------------------------
# Critique / Improvement / Emotion extraction
# ---------------------------------------------------------------------------
_CRITIQUE_PATTERNS = [
    # Suggestions & Improvements
    (re.compile(r"(?:you should|i suggest|you could|it would be (?:better|nice|great) if|"
               r"please (?:improve|fix|change|update|add|make)|i (?:wish|want|need|would like) (?:you )?to)", re.I),
     ["suggestion", "improvement"]),
    # Complaints & Disappointment
    (re.compile(r"(?:the problem is|the issue is|i don't like|i'm (?:unhappy|dissatisfied|not happy|disappointed|upset|annoyed|frustrated)|"
               r"this (?:doesn't|does not) work|this is (?:broken|bad|terrible|awful|poor|useless)|worst)", re.I),
     ["complaint", "disappointed"]),
    # Enquiry / Questions
    (re.compile(r"(?:can you (?:tell|explain|help|check|confirm|verify|clarify)|"
               r"i (?:want to|need to) (?:know|understand|check|ask|find out|confirm)|"
               r"what (?:is|are|about|happens)|"
               r"how (?:do|can|does|long|much|many)|"
               r"(?:do you|could you) (?:know|have|offer|provide)|"
               r"tell me (?:about|more|what|how|if)|i have a question)", re.I),
     ["enquiry"]),
    # Happy / Praise
    (re.compile(r"(?:thank you (?:so much|very much)|i (?:really )?appreciate|that's (?:great|wonderful|fantastic|excellent|perfect|amazing)|"
               r"i'm (?:happy|pleased|satisfied|glad|grateful)|"
               r"good (?:job|service|work|experience)|well done|impressed|love (?:it|this|that))", re.I),
     ["happy"]),
]

def _extract_critiques(segments: list[dict]) -> list[dict]:
    critiques = []
    for seg in segments:
        text = seg.get("text", "").strip()
        spk = seg.get("speaker", "")
        for pat, type_list in _CRITIQUE_PATTERNS:
            m = pat.search(text)
            if m:
                # Determine which type from the list matches best
                matched = m.group(0).lower()
                if "improve" in matched or "change" in matched or "fix" in matched or "update" in matched:
                    ctype = "improvement"
                elif "disappoint" in matched or "upset" in matched or "annoyed" in matched or "frustrated" in matched or "unhappy" in matched:
                    ctype = "disappointed"
                elif "enquir" in matched or "question" in matched or "tell me" in matched or "find out" in matched:
                    ctype = "enquiry"
                elif "thank" in matched or "appreciate" in matched or "happy" in matched or "pleased" in matched or "great" in matched or "wonderful" in matched:
                    ctype = "happy"
                elif any(w in matched for w in ("suggest", "could", "should", "please", "wish", "want", "would like")):
                    ctype = "suggestion"
                else:
                    ctype = "complaint"
                critiques.append({
                    "speaker": spk,
                    "type": ctype,
                    "text": text,
                    "topic": _guess_topic(text)
                })
                break
    return critiques

def _guess_topic(text: str) -> str:
    topics = {
        "billing": ["bill", "charge", "payment", "price", "cost", "fee", "invoice", "refund"],
        "support": ["help", "support", "assist", "guide", "explain"],
        "product": ["product", "item", "quality", "defective", "broken", "damaged"],
        "service": ["service", "experience", "staff", "agent", "representative"],
        "delivery": ["delivery", "shipping", "arrived", "package", "late", "delay"],
        "account": ["account", "login", "password", "access", "profile"],
    }
    low = text.lower()
    for topic, keywords in topics.items():
        if any(kw in low for kw in keywords):
            return topic
    return "general"

# ---------------------------------------------------------------------------
# Main task
# ---------------------------------------------------------------------------
@app.task(bind=True, max_retries=3)
def run(self, rec: str, cid: str, lang: str = None,
        call_date: str = None, call_time: str = None,
        original_name: str = None):
    import sys as _sys
    from pathlib import Path as _Path
    _bd = str(_Path(__file__).resolve().parent)
    if _bd not in _sys.path:
        _sys.path.insert(0, _bd)
    from services import transcriber, clf

    try:
        # ---- 1. Transcribe + Diarize ----
        self.update_state(state="TRANSCRIBING", meta={"stage": "TRANSCRIBING", "file": Path(rec).name})
        tx = transcriber.run(rec, lang=lang)

        # ---- 2. Smart name detection ----
        roles = _detect_speaker_roles(tx)
        speaker_blocks = _build_speaker_blocks(tx, roles)

        # ---- 3. Classify ----
        self.update_state(state="CLASSIFYING", meta={"stage": "CLASSIFYING", "file": Path(rec).name})
        result = clf.classify(tx)

        # ---- 4. Critique extraction ----
        critiques = _extract_critiques(tx)

        # ---- 5. Brief (non-critical) ----
        brief = ""
        try:
            self.update_state(state="BRIEFING", meta={"stage": "BRIEFING", "file": Path(rec).name})
            brief = _brief(cid, result)
        except Exception:
            log.warning("Brief generation failed (likely API quota), continuing without brief")

        # ---- 6. Compute duration ----
        duration_secs = 0.0
        if tx:
            last_seg = tx[-1]
            duration_secs = round(last_seg.get("end", 0) - tx[0].get("start", 0), 1)

        # ---- 7. Build speaker count ----
        speakers = set(s.get("speaker", "SPEAKER_00") for s in tx)

        # ---- 8. Build MongoDB documents ----
        processed_dt = datetime.utcnow()
        lang_code = lang or "en"
        rec_name = Path(rec).name
        # Use original filename for result files if available, otherwise UUID name
        if original_name:
            base_name = original_name.rsplit(".", 1)[0]
        else:
            base_name = rec_name.rsplit(".", 1)[0]

        # 8a. calls collection (tabular)
        call_doc = {
            "cid": cid,
            "customer_name": roles["customer_name"],
            "lang": lang_code,
            "duration_secs": duration_secs,
            "tag": result["tag"],
            "score": result["score"],
            "topics": result.get("topics", []),
            "shift": result.get("shift", ""),
            "summary": result.get("summary", ""),
            "brief": brief,
            "call_date": call_date or "",
            "call_time": call_time or "",
            "rec_path": str(Path(rec)),
            "result_path": f"voicepulse/results/{base_name}_summary.json",
            "transcript_path": f"voicepulse/results/{base_name}_transcript.json",
            "speaker_count": len(speakers),
            "segment_count": len(tx),
            "processed_at": processed_dt
        }
        inserted_call = sync_db.calls.insert_one(call_doc)
        call_id = str(inserted_call.inserted_id)

        # 8b. customers collection (upsert)
        cust_doc = sync_db.customers.find_one({"cid": cid})
        if cust_doc:
            sync_db.customers.update_one(
                {"cid": cid},
                {"$set": {
                    "name": roles["customer_name"] or cust_doc.get("name", ""),
                    "last_call_date": processed_dt
                },
                 "$inc": {"total_calls": 1},
                 "$push": {"calls": inserted_call.inserted_id}}
            )
            # Update avg sentiment
            all_calls = list(sync_db.calls.find({"cid": cid}))
            if all_calls:
                avg_score = round(sum(c.get("score", 0) for c in all_calls) / len(all_calls), 3)
                sync_db.customers.update_one({"cid": cid}, {"$set": {"avg_sentiment": avg_score}})
        else:
            sync_db.customers.insert_one({
                "cid": cid,
                "name": roles["customer_name"],
                "total_calls": 1,
                "avg_sentiment": result["score"],
                "last_call_date": processed_dt,
                "notes": [],
                "calls": [inserted_call.inserted_id]
            })

        # 8c. conversations collection
        conv_doc = {
            "call_id": call_id,
            "cid": cid,
            "speaker_blocks": speaker_blocks,
            "full_text": " ".join(b["text"] for b in speaker_blocks),
            "customer_name": roles["customer_name"],
            "agent_speaker": roles["agent"],
            "speaker_count": len(speakers),
            "processed_at": processed_dt
        }
        inserted_conv = sync_db.conversations.insert_one(conv_doc)

        # 8d. critiques collection
        if critiques:
            for cr in critiques:
                cr["call_id"] = call_id
                cr["cid"] = cid
                cr["processed_at"] = processed_dt
            sync_db.critiques.insert_many(critiques)

        # 8e. Language-specific tables
        lang_col = f"calls_{lang_code}"
        lang_doc = {**call_doc, "_call_id": call_id}
        sync_db[lang_col].insert_one(lang_doc)

        # Combined all-lang table
        all_doc = {**call_doc, "_call_id": call_id}
        sync_db["calls_all"].insert_one(all_doc)

        # ---- 9. Write result files (dual output) ----
        # Transcript file
        transcript_out = {
            "cid": cid,
            "customer_name": roles["customer_name"],
            "lang": lang_code,
            "duration_secs": duration_secs,
            "speakers": len(speakers),
            "agent_speaker": roles["agent"],
            "call_date": call_date or "",
            "call_time": call_time or "",
            "segments": tx,
            "processed_at": processed_dt.isoformat()
        }
        (_results_dir / f"{base_name}_transcript.json").write_text(
            json.dumps(transcript_out, indent=2, default=str)
        )

        # Summary file
        summary_out = {
            "cid": cid,
            "customer_name": roles["customer_name"],
            "lang": lang_code,
            "duration_secs": duration_secs,
            "tag": result["tag"],
            "score": result["score"],
            "topics": result.get("topics", []),
            "shift": result.get("shift", ""),
            "summary": result.get("summary", ""),
            "brief": brief,
            "speaker_blocks": speaker_blocks,
            "speaker_count": len(speakers),
            "turns": result.get("turns", []),
            "critique_count": len(critiques),
            "call_date": call_date or "",
            "call_time": call_time or "",
            "processed_at": processed_dt.isoformat()
        }
        (_results_dir / f"{base_name}_summary.json").write_text(
            json.dumps(summary_out, indent=2, default=str)
        )

        log.info("Processed %s -> %s (%.2f) | Customer: %s | Blocks: %d | Critiques: %d",
                 rec, result["tag"], result["score"], roles["customer_name"],
                 len(speaker_blocks), len(critiques))

        return {
            "status": "done",
            "tag": result["tag"],
            "score": result["score"],
            "id": call_id,
            "cid": cid,
            "customer_name": roles["customer_name"],
            "duration": duration_secs,
            "speaker_blocks": speaker_blocks,
            "speaker_count": len(speakers),
            "topics": result.get("topics", []),
            "shift": result.get("shift", ""),
            "summary": result.get("summary", ""),
            "turns": result.get("turns", []),
        }

    except Exception as exc:
        import traceback
        tb = traceback.format_exc()
        with open(_error_log, "a") as f:
            f.write(f"[{datetime.utcnow().isoformat()}] Failed {rec}: {exc}\n{tb}\n{'='*60}\n")
        log.error("Failed %s: %s", rec, exc)
        self.retry(exc=exc, countdown=60)
