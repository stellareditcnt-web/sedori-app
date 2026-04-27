import os
import time
import json
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import RedirectResponse
import httpx

router = APIRouter()

TOKEN_FILE = Path("base_token.json")
BASE_AUTH_URL = "https://api.thebase.in/1/oauth/authorize"
BASE_TOKEN_URL = "https://api.thebase.in/1/oauth/token"
SCOPES = "read_items write_items read_orders"

EXPIRY_BUFFER = 60  # 期限切れ60秒前にリフレッシュ


def get_token() -> dict | None:
    if TOKEN_FILE.exists():
        return json.loads(TOKEN_FILE.read_text())
    return None


def save_token(data: dict):
    data["saved_at"] = time.time()
    TOKEN_FILE.write_text(json.dumps(data))


def _is_expired(token: dict) -> bool:
    saved_at = token.get("saved_at")
    expires_in = token.get("expires_in", 3600)
    if saved_at is None:
        return True  # saved_at がない古いトークンは期限切れ扱い
    return time.time() >= saved_at + expires_in - EXPIRY_BUFFER


async def _refresh(refresh_token: str) -> dict | None:
    client_id = os.getenv("BASE_CLIENT_ID")
    client_secret = os.getenv("BASE_CLIENT_SECRET")
    async with httpx.AsyncClient(timeout=15) as client:
        res = await client.post(BASE_TOKEN_URL, data={
            "grant_type": "refresh_token",
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
        })
    if res.status_code != 200:
        return None
    return res.json()


async def get_valid_token() -> str | None:
    """有効なアクセストークンを返す。期限切れなら自動リフレッシュする。"""
    token = get_token()
    if not token:
        return None

    if _is_expired(token):
        new_token = await _refresh(token.get("refresh_token", ""))
        if not new_token or "access_token" not in new_token:
            return None
        save_token(new_token)
        return new_token["access_token"]

    return token["access_token"]


@router.get("/auth/base")
async def base_authorize():
    client_id = os.getenv("BASE_CLIENT_ID")
    redirect_uri = os.getenv("BASE_REDIRECT_URI", "http://localhost:8010/auth/callback")
    url = (
        f"{BASE_AUTH_URL}"
        f"?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={SCOPES}"
    )
    return RedirectResponse(url)


@router.get("/auth/callback")
async def base_callback(code: str):
    client_id = os.getenv("BASE_CLIENT_ID")
    client_secret = os.getenv("BASE_CLIENT_SECRET")
    redirect_uri = os.getenv("BASE_REDIRECT_URI", "http://localhost:8010/auth/callback")

    async with httpx.AsyncClient() as client:
        res = await client.post(BASE_TOKEN_URL, data={
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
        })
        token_data = res.json()

    save_token(token_data)
    return {"message": "BASE認証完了！", "token": token_data.get("access_token", "")[:10] + "..."}


@router.get("/auth/base/status")
async def base_auth_status():
    token = get_token()
    if not token:
        return {"connected": False}
    return {"connected": True, "expired": _is_expired(token)}
