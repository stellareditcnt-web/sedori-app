from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class SearchRequest(BaseModel):
    keyword: str
    category: str


MOCK_PRODUCTS = [
    {
        "id": f"mock_{i}",
        "title": f"【サンプル商品{i}】キーワード関連商品",
        "price_jpy": 500 + i * 200,
        "original_price": f"¥{500 + i * 200}",
        "image_url": f"https://placehold.co/400x400?text=商品{i}",
        "product_url": "https://ja.aliexpress.com/",
        "description": f"高品質な商品です。素材は〇〇を使用しており、耐久性があります。サイズ展開: S/M/L/XL。サンプル説明文{i}。",
        "shop_name": f"サンプルショップ{i}",
        "rating": round(4.0 + (i % 10) * 0.1, 1),
        "orders": 100 + i * 50,
    }
    for i in range(1, 11)
]


@router.post("/search")
async def search_products(req: SearchRequest):
    # TODO: AliExpress APIキー取得後に実装
    # 現在はモックデータを返す
    products = []
    for p in MOCK_PRODUCTS:
        p_copy = p.copy()
        p_copy["title"] = f"【{req.keyword}】{p_copy['title']}"
        products.append(p_copy)
    return {"products": products, "keyword": req.keyword}
