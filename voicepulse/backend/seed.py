import random
from datetime import datetime, timedelta
from pymongo import MongoClient
from config import cfg

db = MongoClient(cfg.MONGO_URI)[cfg.DB_NAME]
tags = ["Positive", "Negative", "Neutral", "Frustrated", "Satisfied"]
names = ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank"]
cids = [f"CUST{i:03d}" for i in range(1, 7)]

for cid, name in zip(cids, names):
    db.customers.update_one(
        {"cid": cid},
        {"$set": {"cid": cid, "name": name, "notes": [f"Previous interaction with {name}"]}},
        upsert=True
    )

for i in range(20):
    cid = random.choice(cids)
    tag = random.choice(tags)
    score = round(random.uniform(0.5, 0.98), 3)
    db.calls.insert_one({
        "cid": cid,
        "rec": f"sample_{i+1}.wav",
        "transcript": [],
        "tag": tag,
        "score": score,
        "turns": [
            {"speaker": "SPEAKER_00", "text": "Hello, I need help with my account.", "tag": "Neutral", "score": 0.9},
            {"speaker": "SPEAKER_01", "text": "Of course, let me look into that for you.", "tag": "Positive", "score": 0.85}
        ],
        "summary": f"Sample call with {tag.lower()} sentiment.",
        "topics": random.sample(["Billing", "Support", "Refund", "Account", "Technical"], 2),
        "shift": f"Neutral -> {tag}",
        "brief": f"Approach {cid} with empathy. Address their main concern directly.",
        "processed_at": datetime.utcnow() - timedelta(days=random.randint(0, 30))
    })

print(f"Seeded {db.calls.count_documents({})} calls and {db.customers.count_documents({})} customers.")
