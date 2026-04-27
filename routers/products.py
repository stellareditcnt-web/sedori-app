import os
import asyncio
import hashlib
import httpx
from datetime import datetime, timezone
from fastapi import APIRouter
from pydantic import BaseModel
from google import genai
from config import calc_sell_price, get_config, save_config

router = APIRouter()

ALIEXPRESS_API_URL = "https://api-sg.aliexpress.com/sync"


def _sign(params: dict, app_secret: str) -> str:
    sorted_params = sorted(params.items())
    base = app_secret + "".join(f"{k}{v}" for k, v in sorted_params) + app_secret
    return hashlib.md5(base.encode()).hexdigest().upper()


async def translate_titles_to_japanese(titles: list[str]) -> list[str]:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(titles))
    response = await asyncio.to_thread(
        client.models.generate_content,
        model="gemini-2.5-flash-lite",
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
    app_key = os.getenv("ALIEXPRESS_APP_KEY")
    app_secret = os.getenv("ALIEXPRESS_APP_SECRET")

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    params = {
        "app_key": app_key,
        "method": "aliexpress.ds.product.search",
        "sign_method": "md5",
        "timestamp": timestamp,
        "keywords": keyword,
        "page_no": "1",
        "page_size": "20",
        "sort": "SALE_PRICE_ASC",
        "target_currency": "JPY",
        "target_language": "JA",
        "ship_to_country": "JP",
    }
    params["sign"] = _sign(params, app_secret)

    async with httpx.AsyncClient(timeout=15) as client:
        res = await client.post(ALIEXPRESS_API_URL, data=params)

    data = res.json()
    resp = data.get("aliexpress_ds_product_search_response", {})
    result = resp.get("resp_result", {}).get("result", {})
    raw_products = result.get("products", {}).get("traffic_product_dto", [])

    products = []
    for item in raw_products[:10]:
        price_str = item.get("sale_price") or item.get("original_price") or "0"
        try:
            price_jpy = int(float(price_str))
        except ValueError:
            price_jpy = 0

        products.append({
            "id": str(item.get("product_id", "")),
            "title": item.get("product_title", ""),
            "price_jpy": price_jpy,
            "image_url": item.get("product_main_image_url", ""),
            "product_url": item.get("product_detail_url", ""),
            "description": item.get("product_title", ""),
            "shop_name": "",
            "rating": float(item.get("evaluate_rate", "0").replace("%", "") or 0) / 20,
            "orders": int(item.get("lastest_volume") or 0),
        })

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
