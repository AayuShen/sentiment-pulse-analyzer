import json
from openai import OpenAI
from config import cfg
from services.crm import history as crm_history

gpt = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=cfg.GROQ_API_KEY)

sys_prompt = (
    "You are a Customer Success Coach. Given the customer's historical "
    "interaction notes and their latest call sentiment analysis, generate "
    "a concise Approach Brief (max 150 words) for the CS agent. "
    "Include: tone to use, topics to avoid, key pain point to address first, "
    "and one suggested opener. Be warm, empathetic, and tactical."
)

async def gen(cid: str, result: dict) -> str:
    ctx = await crm_history(cid)
    user_msg = json.dumps({"history": ctx, "latest": result})
    resp = gpt.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_msg}
        ],
        max_tokens=250
    )
    return resp.choices[0].message.content
