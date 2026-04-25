import os
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


def get_token() -> dict | None:
    if TOKEN_FILE.exists():
        return json.loads(TOKEN_FILE.read_text())
    return None


def save_token(data: dict):
    TOKEN_FILE.write_text(json.dumps(data))


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
    return {"connected": token is not None}
