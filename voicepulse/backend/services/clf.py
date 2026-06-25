import json
import torch
from openai import OpenAI
from transformers import pipeline
from config import cfg

# 5 fine-grained labels — Groq handles these as primary
# 3 primary labels — local DeBERTa fallback (higher confidence with fewer labels)
tags = ["Positive", "Neutral", "Frustrated", "Satisfied", "Negative"]
primary_tags = ["Positive", "Negative", "Neutral"]
_clf = None
_device = None
_gpt_client = None

TAG_MAP_3TO5 = {
    "Positive": "Positive",
    "Negative": "Negative",
    "Neutral": "Neutral",
}

def _init():
    global _clf, _device
    if _clf is not None:
        return
    _device = 0 if torch.cuda.is_available() else -1
    print(f"[clf] Loading DeBERTa-v3 zero-shot classifier on {'GPU' if _device==0 else 'CPU'}...")
    _clf = pipeline(
        "zero-shot-classification",
        model="MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli",
        device=_device
    )
    print("[clf] Classifier loaded")

def _get_gpt_client():
    """Groq API client (OpenAI-compatible) - primary sentiment engine."""
    global _gpt_client
    if _gpt_client is not None:
        return _gpt_client
    if cfg.GROQ_API_KEY:
        _gpt_client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=cfg.GROQ_API_KEY
        )
    return _gpt_client

def _classify_utterance_3label(text: str) -> tuple[str, float]:
    """Local DeBERTa-v3 with 3 labels — higher per-label confidence."""
    _init()
    result = _clf(text, candidate_labels=primary_tags)
    return result["labels"][0], result["scores"][0]

def _aggregate_local(segments: list[dict]) -> dict:
    """Primary: Groq-based 5-label classification with high confidence."""
    turns = []
    for seg in segments:
        txt = seg["text"].strip()
        turns.append({"speaker": seg["speaker"], "text": txt})

    client = _get_gpt_client()
    if client is None:
        raise RuntimeError("No GROQ_API_KEY configured")

    # Truncate to fit free tier TPM limits
    if len(turns) > 15:
        input_turns = turns[:5] + turns[-10:]
    else:
        input_turns = turns

    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": (
                "You are a senior call-quality analyst. Analyze this customer-service transcript. "
                "Return ONLY valid JSON with these fields:\n"
                '- "tag": one of Positive, Neutral, Frustrated, Satisfied, Negative\n'
                '- "score": your confidence (0.0-1.0). Use HIGH confidence (0.85-0.99) when the sentiment is clear. '
                'Only use LOW confidence (0.50-0.70) when the transcript is genuinely ambiguous or contradictory.\n'
                '- "summary": one-sentence summary of the call\n'
                '- "topics": list of 1-3 key topics discussed\n'
                '- "shift": emotional shift, e.g. "Frustrated -> Satisfied" or "Neutral -> Positive" or empty string\n\n'
                'Sentiment definitions:\n'
                '- Positive: customer is happy, pleased, or thankful\n'
                '- Neutral: purely factual, transactional, information-seeking\n'
                '- Frustrated: customer is visibly angry, irritated, or annoyed — stronger than just unhappy\n'
                '- Satisfied: customer is content, their issue was resolved, they feel heard\n'
                '- Negative: customer is mildly unhappy, disappointed, or dissatisfied — but NOT angry\n\n'
                'IMPORTANT: Do NOT default to Neutral. Be decisive. '
                'Distinguish Frustrated (angry tone, complaints) from Negative (mild disappointment). '
                'Distinguish Satisfied (content/resolved) from Positive (happy/pleased).'
            )},
            {"role": "user", "content": json.dumps(input_turns)}
        ]
    )
    result = json.loads(resp.choices[0].message.content)
    # Validate tag
    if result.get("tag") not in tags:
        result["tag"] = "Neutral"
    result["score"] = float(result.get("score", 0.85))
    return result

def _aggregate_local_fallback(segments: list[dict]) -> dict:
    """Fallback: Local DeBERTa-v3 with 3 labels (higher confidence than 5-label)."""
    _init()
    turns = []
    weighted = {t: 0.0 for t in primary_tags}
    total_dur = 0.0
    for seg in segments:
        txt = seg["text"].strip()
        if not txt:
            tag, score = "Neutral", 1.0
        else:
            tag, score = _classify_utterance_3label(txt)
        dur = seg["end"] - seg["start"]
        turns.append({"speaker": seg["speaker"], "text": txt, "tag": tag, "score": round(score, 3)})
        weighted[tag] += dur * score
        total_dur += dur
    call_tag = max(weighted, key=weighted.get) if total_dur > 0 else "Neutral"
    call_score = round(weighted[call_tag] / total_dur, 3) if total_dur > 0 else 0.0
    return {
        "tag": TAG_MAP_3TO5.get(call_tag, call_tag),
        "score": call_score,
        "turns": turns,
        "summary": "",
        "topics": [],
        "shift": ""
    }

def classify(segments: list[dict]) -> dict:
    """Primary: Groq 5-label (high confidence). Fallback: local DeBERTa 3-label."""
    try:
        result = _aggregate_local(segments)
        # Enrich turns with local tags for display
        base = _aggregate_local_fallback(segments)
        result["turns"] = base.get("turns", [])
        return result
    except Exception as e:
        print(f"[clf] Groq failed ({e}), falling back to local 3-label classifier")
        return _aggregate_local_fallback(segments)
