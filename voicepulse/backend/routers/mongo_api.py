"""API endpoints for MongoDB collections: calls, customers, conversations, critiques, lang tables."""
from datetime import datetime
from fastapi import APIRouter, Query
from bson import ObjectId
from db import pulse_db
from schemas import CallOut, SentimentHistory

rt = APIRouter(prefix="/api/mongo", tags=["mongo"])

def _serialize(doc: dict) -> dict:
    if not doc:
        return {}
    out = {}
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            out[k] = str(v)
        elif isinstance(v, list) and v and isinstance(v[0], ObjectId):
            out[k] = [str(x) for x in v]
        else:
            out[k] = v
    return out

@rt.get("/customers")
async def list_customers():
    docs = await pulse_db.customers.find({}).sort("last_call_date", -1).to_list(100)
    return [_serialize(d) for d in docs]

@rt.get("/customers/{cid}")
async def get_customer(cid: str):
    doc = await pulse_db.customers.find_one({"cid": cid})
    return _serialize(doc) if doc else {"error": "not found"}

@rt.get("/calls")
async def list_calls(
    lang: str = Query("all"),
    cid: str = Query(""),
    limit: int = Query(50)
):
    col = pulse_db["calls_all"] if lang == "all" else pulse_db.get_collection(f"calls_{lang}")
    if col is None:
        col = pulse_db.calls
    query = {}
    if cid:
        query["cid"] = cid
    docs = await col.find(query).sort("processed_at", -1).to_list(limit)
    return [_serialize(d) for d in docs]

@rt.get("/conversations/{call_id}")
async def get_conversation(call_id: str):
    try:
        doc = await pulse_db.conversations.find_one({"call_id": call_id})
    except Exception:
        doc = await pulse_db.conversations.find_one({"_id": ObjectId(call_id)})
    return _serialize(doc) if doc else {"error": "not found"}

@rt.get("/critiques")
async def list_critiques(
    cid: str = Query(""),
    ctype: str = Query(""),
    limit: int = Query(50)
):
    query = {}
    if cid:
        query["cid"] = cid
    if ctype:
        query["type"] = ctype
    docs = await pulse_db.critiques.find(query).sort("processed_at", -1).to_list(limit)
    return [_serialize(d) for d in docs]

@rt.get("/stats")
async def lang_stats(lang: str = Query("all")):
    col = pulse_db.calls if lang == "all" else pulse_db.get_collection(f"calls_{lang}")
    if col is None:
        col = pulse_db.calls

    total = await col.count_documents({})
    pipeline = [{"$group": {"_id": "$tag", "count": {"$sum": 1}}}]
    tag_docs = await col.aggregate(pipeline).to_list(10)
    tag_counts = {d["_id"]: d["count"] for d in tag_docs}

    avg_pipeline = [{"$group": {"_id": None, "avg": {"$avg": "$score"}}}]
    avg_result = await col.aggregate(avg_pipeline).to_list(1)
    avg_score = round(avg_result[0]["avg"], 3) if avg_result else 0.0

    # Unique customers
    cust_pipeline = [{"$group": {"_id": "$cid"}}, {"$count": "unique"}]
    cust_result = await col.aggregate(cust_pipeline).to_list(1)
    unique_customers = cust_result[0]["unique"] if cust_result else 0

    return {
        "lang": lang,
        "total_calls": total,
        "unique_customers": unique_customers,
        "avg_score": avg_score,
        "tag_counts": tag_counts
    }

# Sentiment-tag → user-friendly call-type label
_TAG_TO_CALL_TYPE = {
    "Positive": "Praise",
    "Satisfied": "Praise",
    "Negative": "Complaint",
    "Frustrated": "Complaint",
    "Neutral": "Enquiry",
}

@rt.get("/customer-profiles")
async def customer_profiles(
    search: str = Query(""),
    cid: str = Query(""),
    date_from: str = Query(""),
    date_to: str = Query(""),
    call_type: str = Query(""),
):
    """Return enriched customer profiles with calls, critiques, and behavioral notes."""
    # ── Fetch all customers ──
    cust_query = {}
    if cid:
        cust_query["cid"] = cid
    custs = await pulse_db.customers.find(cust_query).sort("last_call_date", -1).to_list(200)

    profiles = []
    for cust in custs:
        cust_cid = cust["cid"]
        cust_name = cust.get("name", "") or cust_cid

        # Search filter (by name or cid)
        if search and search.lower() not in cust_name.lower() and search.lower() not in cust_cid.lower():
            continue

        # ── Fetch calls for this customer ──
        call_query = {"cid": cust_cid}
        if date_from:
            call_query.setdefault("processed_at", {})["$gte"] = datetime.fromisoformat(date_from)
        if date_to:
            call_query.setdefault("processed_at", {})["$lte"] = datetime.fromisoformat(date_to)

        all_calls = await pulse_db.calls.find(call_query).sort("processed_at", -1).to_list(100)

        # ── Derive call type for each call ──
        calls_out = []
        type_set = set()
        for c in all_calls:
            tag = c.get("tag", "")
            ct = _TAG_TO_CALL_TYPE.get(tag, "Enquiry")
            # Also check critiques for additional types
            csr = await pulse_db.critiques.find({"call_id": str(c["_id"])}).to_list(20)
            critique_types = [cr.get("type", "") for cr in csr]
            # Combine: use sentiment-derived type + critique types
            all_types = [ct] + [t.capitalize() for t in critique_types if t]
            type_set.update(all_types)

            calls_out.append({
                "_id": str(c["_id"]),
                "call_date": c.get("call_date", ""),
                "call_time": c.get("call_time", ""),
                "processed_at": c.get("processed_at", "").isoformat() if c.get("processed_at") else "",
                "duration_secs": c.get("duration_secs", 0),
                "tag": tag,
                "score": c.get("score", 0),
                "summary": c.get("summary", ""),
                "brief": c.get("brief", ""),
                "topics": c.get("topics", []),
                "shift": c.get("shift", ""),
                "call_type": ct,
                "critique_types": critique_types,
            })

        # ── Call-type filter ──
        if call_type:
            ct_lower = call_type.lower()
            matched = any(
                ct_lower in (c["call_type"] or "").lower() or
                any(ct_lower in (t or "").lower() for t in c.get("critique_types", []))
                for c in calls_out
            )
            if not matched:
                continue

        profiles.append({
            "cid": cust_cid,
            "name": cust_name,
            "total_calls": len(calls_out),
            "avg_sentiment": cust.get("avg_sentiment", 0),
            "last_call_date": cust.get("last_call_date", "").isoformat() if cust.get("last_call_date") else "",
            "notes": cust.get("notes", []),
            "tags": cust.get("tags", []),
            "call_types": sorted(type_set),
            "calls": calls_out,
        })

    return profiles

# ── Customer Tags ──
from pydantic import BaseModel

class TagUpdate(BaseModel):
    tags: list[str]

@rt.patch("/customers/{cid}/tags")
async def update_customer_tags(cid: str, body: TagUpdate):
    """Replace the tags array for a customer."""
    result = await pulse_db.customers.update_one(
        {"cid": cid},
        {"$set": {"tags": body.tags}},
        upsert=False
    )
    if result.matched_count == 0:
        return {"error": "customer not found"}
    return {"ok": True, "tags": body.tags}
