from fastapi import APIRouter
from bson import ObjectId
from db import calls
from schemas import CallOut, SentimentHistory

rt = APIRouter(prefix="/api/sentiment", tags=["sentiment"])

def _to_out(doc: dict) -> CallOut:
    return CallOut(
        id=str(doc["_id"]),
        cid=doc["cid"],
        rec=doc["rec"],
        tag=doc["tag"],
        score=doc["score"],
        summary=doc.get("summary", ""),
        topics=doc.get("topics", []),
        shift=doc.get("shift", ""),
        brief=doc.get("brief", ""),
        processed_at=doc["processed_at"],
        turns=doc.get("turns", [])
    )

@rt.get("/history/all")
async def all_calls():
    docs = await calls.find({}).sort("processed_at", -1).to_list(100)
    return SentimentHistory(cid="all", calls=[_to_out(d) for d in docs])

@rt.get("/history/{cid}")
async def history(cid: str):
    docs = await calls.find({"cid": cid}).sort("processed_at", -1).to_list(50)
    return SentimentHistory(cid=cid, calls=[_to_out(d) for d in docs])

@rt.get("/{cid}")
async def latest(cid: str):
    doc = await calls.find_one({"cid": cid}, sort=[("processed_at", -1)])
    if not doc:
        return {"error": "not found"}
    return _to_out(doc)
