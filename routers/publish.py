import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .base_auth import get_token

router = APIRouter()

BASE_API = "https://api.thebase.in/1"


class PublishRequest(BaseModel):
    product_id: str
    title: str
    description: str
    price: int
    image_url: str
    platform: str  # "base" | "instagram" | "both"


async def post_to_base(title: str, description: str, price: int, image_url: str) -> dict:
    token = get_token()
    if not token:
        return {"status": "error", "message": "BASE未認証。/auth/base にアクセスして認証してください。"}

    access_token = token.get("access_token")
    headers = {"Authorization": f"Bearer {access_token}"}

    # 画像をダウンロードしてBASEにアップロード
    async with httpx.AsyncClient(timeout=30) as client:
        img_res = await client.get(image_url)
        img_bytes = img_res.content
        content_type = img_res.headers.get("content-type", "image/jpeg")

        res = await client.post(
            f"{BASE_API}/items/add",
            headers=headers,
            data={
                "title": title,
                "detail": description,
                "price": str(price),
                "stock": "10",
                "visible": "1",
            },
            files={"images[0]": ("product.jpg", img_bytes, content_type)},
        )

    data = res.json()
    if res.status_code == 200:
        item = data.get("item", {})
        item_id = item.get("item_id")
        return {
            "status": "success",
            "item_id": item_id,
            "admin_url": f"https://admin.thebase.com/items/detail/{item_id}",
        }
    return {"status": "error", "message": data.get("error_description", str(data))}


@router.post("/publish")
async def publish_product(req: PublishRequest):
    results = {}

    if req.platform in ("base", "both"):
        results["base"] = await post_to_base(
            title=req.title,
            description=req.description,
            price=req.price,
            image_url=req.image_url,
        )

    if req.platform in ("instagram", "both"):
        # TODO: Instagram Graph API実装
        results["instagram"] = {
            "status": "pending",
            "message": "Instagram APIキー設定後に自動投稿できます",
        }

    return results
