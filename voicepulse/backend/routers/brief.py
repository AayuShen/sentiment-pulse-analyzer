from fastapi import APIRouter
from db import calls
from schemas import CallBrief

rt = APIRouter(prefix="/api/brief", tags=["brief"])

@rt.get("/{cid}")
async def get_brief(cid: str):
    doc = await calls.find_one({"cid": cid}, sort=[("processed_at", -1)])
    if not doc:
        return {"error": "not found"}
    return CallBrief(
        cid=doc["cid"],
        brief=doc.get("brief", ""),
        tag=doc["tag"],
        score=doc["score"],
        processed_at=doc["processed_at"]
    )