from db import customers, calls

async def history(cid: str) -> dict:
    cust = await customers.find_one({"cid": cid})
    if not cust:
        return {"notes": [], "past_calls": []}
    past = await calls.find({"cid": cid}).sort("processed_at", -1).limit(10).to_list(10)
    return {"notes": cust.get("notes", []), "past_calls": past}
