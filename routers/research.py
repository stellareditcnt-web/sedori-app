import os
import asyncio
import json
from fastapi import APIRouter
from pydantic import BaseModel
from google import genai

router = APIRouter()


class ConceptRequest(BaseModel):
    concept: str
    category: str  # "子供服" | "ペット用品" | "レディースファッション" etc.


@router.post("/research")
async def research_trends(req: ConceptRequest):
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    prompt = f"""
あなたはせどり・転売のリサーチ専門家です。
以下の条件で、今売れている商品のトレンドキーワードを提案してください。

店舗コンセプト: {req.concept}
カテゴリ: {req.category}

以下のJSON形式で返してください（日本語で）:
{{
  "keywords": ["キーワード1", "キーワード2", ...],
  "trend_reason": "なぜ今このジャンルが売れているかの説明（2〜3文）",
  "target_audience": "ターゲット層",
  "price_range": {{
    "min": 仕入れ価格下限(円),
    "max": 仕入れ価格上限(円)
  }}
}}

JSONのみ返してください。余分なテキスト不要。
"""

    response = await asyncio.to_thread(
        client.models.generate_content,
        model="gemini-2.5-flash",
        contents=prompt,
    )
    text = response.text.strip()

    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]

    data = json.loads(text.strip())
    return data
