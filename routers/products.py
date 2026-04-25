import os
import httpx
from fastapi import APIRouter
from pydantic import BaseModel
from google import genai
from config import calc_sell_price, get_config, save_config

router = APIRouter()

RAPIDAPI_HOST = "aliexpress-datahub.p.rapidapi.com"
USD_TO_JPY = 150


# AliExpress APIで安定して動くキーワード一覧
RELIABLE_KEYWORDS = ["dress", "jacket", "hat", "romper", "skirt", "coat", "hoodie", "cardigan"]


async def translate_keywords(keyword: str) -> list[str]:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=(
            f"次の日本語キーワードに最も近い英単語を、以下のリストから3つ選んでカンマ区切りで返してください。"
            f"選択肢: {', '.join(RELIABLE_KEYWORDS)}\n"
            f"単語のみ、説明不要。\n"
            f"キーワード: {keyword}"
        ),
    )
    raw = response.text.strip().strip('"').strip("'")
    candidates = [k.strip().lower() for k in raw.split(",") if k.strip()]
    # 安全のため確実に動くキーワードのみ使用
    valid = [k for k in candidates if k in RELIABLE_KEYWORDS]
    return valid if valid else RELIABLE_KEYWORDS[:3]


async def translate_titles_to_japanese(titles: list[str]) -> list[str]:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(titles))
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=(
            f"以下の英語商品タイトルを自然な日本語に翻訳してください。\n"
            f"番号付きリストで、番号と翻訳のみ返してください。\n\n{numbered}"
        ),
    )
    lines = [l.strip() for l in response.text.strip().splitlines() if l.strip()]
    result = []
    for line in lines:
        if ". " in line:
            result.append(line.split(". ", 1)[1])
        else:
            result.append(line)
    while len(result) < len(titles):
        result.append(titles[len(result)])
    return result[:len(titles)]


async def search_aliexpress(keyword: str) -> list:
    api_key = os.getenv("RAPIDAPI_KEY")
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
    }

    # 日本語キーワードを英語候補に変換して順番に試す
    en_keywords = await translate_keywords(keyword)
    items = []

    async with httpx.AsyncClient(timeout=15) as client:
        for en_kw in en_keywords:
            res = await client.get(
                f"https://{RAPIDAPI_HOST}/item_search_4",
                headers=headers,
                params={"q": en_kw, "page": "1"},
            )
            data = res.json()
            items = data.get("result", {}).get("resultList", [])
            if items:
                break
    products = []
    for item in items[:10]:
        info = item if "itemId" in item else item.get("item", item)
        sku = info.get("sku", {}).get("def", {})
        price_usd = float(sku.get("promotionPrice") or sku.get("price") or 0)
        price_jpy = int(price_usd * USD_TO_JPY)

        image = info.get("image", "")
        if image.startswith("//"):
            image = "https:" + image

        products.append({
            "id": str(info.get("itemId", "")),
            "title": info.get("title", ""),
            "price_jpy": price_jpy,
            "image_url": image,
            "product_url": "https:" + info.get("itemUrl", "") if info.get("itemUrl", "").startswith("//") else info.get("itemUrl", ""),
            "description": info.get("title", ""),
            "shop_name": "",
            "rating": float(info.get("averageStarRate") or 4.5),
            "orders": int(info.get("sales") or 0),
        })

    # タイトルを日本語に翻訳
    if products:
        en_titles = [p["title"] for p in products]
        ja_titles = await translate_titles_to_japanese(en_titles)
        for p, ja in zip(products, ja_titles):
            p["title"] = ja
            p["description"] = ja

    return products


MOCK_PRODUCTS = [
    {
        "id": f"mock_{i}",
        "title": f"【サンプル商品{i}】キーワード関連商品",
        "price_jpy": 500 + i * 200,
        "image_url": f"https://placehold.co/400x400?text=商品{i}",
        "product_url": "https://ja.aliexpress.com/",
        "description": f"高品質な商品です。サイズ展開: S/M/L/XL。サンプル説明文{i}。",
        "shop_name": f"サンプルショップ{i}",
        "rating": round(4.0 + (i % 10) * 0.1, 1),
        "orders": 100 + i * 50,
    }
    for i in range(1, 11)
]


class SearchRequest(BaseModel):
    keyword: str
    category: str


@router.post("/search")
async def search_products(req: SearchRequest):
    try:
        products = await search_aliexpress(req.keyword)
    except Exception:
        products = []

    if not products:
        products = [
            {**p.copy(), "title": f"【{req.keyword}】{p['title']}"}
            for p in MOCK_PRODUCTS
        ]

    for p in products:
        p["suggested_price"] = calc_sell_price(p["price_jpy"])

    return {"products": products, "keyword": req.keyword}


class PricingConfig(BaseModel):
    price_multiplier: float


@router.get("/pricing-config")
async def get_pricing_config():
    return get_config()


@router.post("/pricing-config")
async def update_pricing_config(req: PricingConfig):
    config = get_config()
    config["price_multiplier"] = req.price_multiplier
    save_config(config)
    return {"message": "更新しました", "config": config}
