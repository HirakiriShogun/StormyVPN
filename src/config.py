import json
import os
from pathlib import Path
from typing import List, Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
IMAGES_DIR = ASSETS_DIR / "images"
VIDEOS_DIR = ASSETS_DIR / "videos"
BACKUPS_DIR = BASE_DIR / "backups"


def _load_env_file() -> None:
    """Simple .env loader without extra dependencies."""
    if not ENV_PATH.exists():
        return

    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key and key.strip() and key.strip() not in os.environ:
            os.environ[key.strip()] = value.strip()


_load_env_file()


def _parse_admin_ids(raw_value: str, fallback: List[int]) -> List[int]:
    ids = []
    for part in raw_value.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.append(int(part))
        except ValueError:
            continue
    return ids or fallback


DEFAULT_SERVERS: List[Dict[str, Any]] = []


def _load_servers() -> List[Dict[str, Any]]:
    raw = os.environ.get("SERVERS_JSON")
    if raw:
        try:
            servers = json.loads(raw)
            if isinstance(servers, list) and servers:
                return servers
        except json.JSONDecodeError:
            pass
    return DEFAULT_SERVERS


def _resolve_path(raw_path: str) -> str:
    path = Path(raw_path)
    if not path.is_absolute():
        path = BASE_DIR / path
    return str(path)


API_TOKEN = os.environ.get("API_TOKEN", "")
SHOP_ID = os.environ.get("SHOP_ID", "")
SHOP_API = os.environ.get("SHOP_API", "")
ADMIN_IDS = _parse_admin_ids(os.environ.get("ADMIN_IDS", ""), fallback=[1902290413])
PAYMENT_RETURN_URL = os.environ.get("PAYMENT_RETURN_URL", "https://t.me/StormyVPN_bot")
SUBSCRIPTION_PRICE = float(os.environ.get("SUBSCRIPTION_PRICE", "179"))

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "stormyvpn")
DB_USER = os.environ.get("DB_USER", "stormy")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "stormypass")
DB_URL = os.environ.get(
    "DB_URL",
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
)

MAINTENANCE_CONTACT = os.environ.get("MAINTENANCE_CONTACT", "@hirakiri_shogun")
MAINTENANCE_MODE = os.environ.get("MAINTENANCE_MODE", "true").lower() == "true"
SERVERS = _load_servers()

# Ensure important directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
