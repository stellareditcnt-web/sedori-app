import json
from pathlib import Path

CONFIG_FILE = Path("pricing_config.json")

DEFAULT_CONFIG = {
    "price_multiplier": 3.0,
}


def get_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return DEFAULT_CONFIG.copy()


def save_config(data: dict):
    CONFIG_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def calc_sell_price(cost: int) -> int:
    multiplier = get_config().get("price_multiplier", 3.0)
    return int(cost * multiplier)
