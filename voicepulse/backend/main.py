from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import voice, sentiment, brief, analytics, mongo_api

app = FastAPI(title="Sentiment Pulse Analyzer")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)
app.include_router(voice.rt)
app.include_router(sentiment.rt)
app.include_router(brief.rt)
app.include_router(analytics.rt)
app.include_router(mongo_api.rt)

@app.get("/api/health")
async def health():
    return {"status": "ok"}
