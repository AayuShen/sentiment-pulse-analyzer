from datetime import datetime, timedelta
from fastapi import APIRouter, Query
from db import calls, pulse_db
from schemas import AnalyticsSummary, TrendPoint

rt = APIRouter(prefix="/api/analytics", tags=["analytics"])
tags = ["Positive", "Negative", "Neutral", "Frustrated", "Satisfied"]

def _get_col(lang: str = "all"):
    if lang != "all":
        col = pulse_db.get_collection(f"calls_{lang}")
        if col is not None:
            return col
    return calls

@rt.get("/summary")
async def summary(lang: str = Query("all")):
    col = _get_col(lang)
    total = await col.count_documents({})
    tag_counts = {}
    for t in tags:
        tag_counts[t] = await col.count_documents({"tag": t})
    week_ago = datetime.utcnow() - timedelta(days=7)
    neg_week = await col.count_documents({"tag": "Negative", "processed_at": {"$gte": week_ago}})
    total_week = await col.count_documents({"processed_at": {"$gte": week_ago}})
    pos_week = await col.count_documents({"tag": "Positive", "processed_at": {"$gte": week_ago}})

    pipeline = [{"$group": {"_id": None, "avg": {"$avg": "$score"}}}]
    avg_result = await col.aggregate(pipeline).to_list(1)
    avg_score = round(avg_result[0]["avg"], 3) if avg_result else 0.0

    # Unique customers
    cust_pipeline = [{"$group": {"_id": "$cid"}}, {"$count": "unique"}]
    cust_result = await col.aggregate(cust_pipeline).to_list(1)
    unique = cust_result[0]["unique"] if cust_result else 0

    return AnalyticsSummary(
        total=total,
        unique_customers=unique,
        tag_counts=tag_counts,
        negative_pct=round((neg_week / total_week) * 100, 1) if total_week > 0 else 0.0,
        positive_pct=round((pos_week / total_week) * 100, 1) if total_week > 0 else 0.0,
        avg_score=avg_score
    )

@rt.get("/trend")
async def trend(lang: str = Query("all"), frm: str = Query(None), to: str = Query(None)):
    col = _get_col(lang)
    match = {}
    if frm:
        match.setdefault("processed_at", {})["$gte"] = datetime.fromisoformat(frm)
    if to:
        match.setdefault("processed_at", {})["$lte"] = datetime.fromisoformat(to)
    pipeline = [
        {"$match": match},
        {"$group": {
            "_id": {"week": {"$dateToString": {"format": "%Y-W%V", "date": "$processed_at"}}, "tag": "$tag"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id.week": 1}}
    ]
    results = await col.aggregate(pipeline).to_list(500)
    return [TrendPoint(week=r["_id"]["week"], tag=r["_id"]["tag"], count=r["count"]) for r in results]

@rt.get("/daily-sentiment")
async def daily_sentiment(lang: str = Query("all"), months: int = Query(3)):
    """Return daily sentiment counts for heatmap (default last 3 months)."""
    col = _get_col(lang)
    cutoff = datetime.utcnow() - timedelta(days=months * 30)
    pipeline = [
        {"$match": {"processed_at": {"$gte": cutoff}}},
        {"$group": {
            "_id": {
                "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$processed_at"}},
                "tag": "$tag"
            },
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id.date": 1}}
    ]
    results = await col.aggregate(pipeline).to_list(400)
    daily = {}
    for r in results:
        d = r["_id"]["date"]
        tag = r["_id"]["tag"]
        daily.setdefault(d, {})[tag] = r["count"]
    return daily

@rt.get("/agent-performance")
async def agent_performance(lang: str = Query("all"), limit: int = Query(50)):
    """Return per-call agent-side metrics for agent performance tab."""
    col = _get_col(lang)
    calls_list = await col.find({}).sort("processed_at", -1).to_list(limit)
    out = []
    for c in calls_list:
        cid_str = str(c["_id"])
        conv = await pulse_db.conversations.find_one({"call_id": cid_str})
        agent_blocks = 0
        customer_blocks = 0
        agent_words = 0
        customer_words = 0
        agent_speaker = ""
        if conv:
            agent_speaker = conv.get("agent_speaker", "")
            for b in conv.get("speaker_blocks", []):
                wc = len(b.get("text", "").split())
                if b.get("role") == "agent":
                    agent_blocks += 1
                    agent_words += wc
                else:
                    customer_blocks += 1
                    customer_words += wc
        total_words = agent_words + customer_words
        talk_ratio = round(agent_words / total_words * 100, 1) if total_words > 0 else 50.0

        out.append({
            "call_id": cid_str,
            "cid": c.get("cid", ""),
            "customer_name": c.get("customer_name", ""),
            "call_date": c.get("call_date", ""),
            "processed_at": c.get("processed_at", "").isoformat() if c.get("processed_at") else "",
            "duration_secs": c.get("duration_secs", 0),
            "tag": c.get("tag", ""),
            "score": c.get("score", 0),
            "agent_blocks": agent_blocks,
            "customer_blocks": customer_blocks,
            "agent_words": agent_words,
            "customer_words": customer_words,
            "talk_ratio_pct": talk_ratio,
            "agent_speaker": agent_speaker,
        })

    if out:
        avg_talk = round(sum(o["talk_ratio_pct"] for o in out) / len(out), 1)
        pos_count = sum(1 for o in out if o["tag"] in ("Positive", "Satisfied"))
        neg_count = sum(1 for o in out if o["tag"] in ("Negative", "Frustrated"))
    else:
        avg_talk = 0
        pos_count = 0
        neg_count = 0

    return {
        "calls": out,
        "summary": {
            "total": len(out),
            "avg_talk_ratio": avg_talk,
            "positive_calls": pos_count,
            "negative_calls": neg_count,
        }
    }

