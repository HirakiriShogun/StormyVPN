"""
One-time helper to refresh VLESS links for all users after server IP changes.
Usage:
    python scripts/refresh_vless_keys.py           # updates DB in-place
    python scripts/refresh_vless_keys.py --dry-run # shows what will change
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.parse import urlparse


BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / "src"))

from api_requests import VPNApi, _normalize_url  # noqa: E402
from database import VPNDatabase  # noqa: E402


def _signature(url: str) -> tuple[str, int | None]:
    """Returns (path, port) tuple to match old/new server URLs even if host changes."""
    parsed = urlparse(_normalize_url(url or ""))
    return parsed.path.rstrip("/"), parsed.port


def _build_server_map(servers: list[dict]) -> dict[tuple[str, int | None], str]:
    return {_signature(s["url"]): _normalize_url(s["url"]) for s in servers}


def refresh_vless_links(dry_run: bool = False) -> None:
    vpn_api = VPNApi()
    db = VPNDatabase()
    users = db.get_all_users()
    server_map = _build_server_map(vpn_api.servers)

    print(f"[info] Users in DB: {len(users)}")
    updated = skipped = 0

    for user in users:
        chat_id, username, expiry_date, _, _, inbound_id, server_url = user
        resolved_url = server_map.get(_signature(server_url), _normalize_url(server_url or ""))

        inbound_data = vpn_api.get_inbound_data(inbound_id, resolved_url)
        if not inbound_data or inbound_data.get("_error") or inbound_data.get("_not_found"):
            skipped += 1
            print(f"[skip] chat_id={chat_id} inbound={inbound_id}: {inbound_data}")
            continue

        vless_link = vpn_api.build_vless_uri(inbound_data, resolved_url)
        if not vless_link:
            skipped += 1
            print(f"[skip] chat_id={chat_id} inbound={inbound_id}: cannot build VLESS link")
            continue

        if dry_run:
            print(f"[dry-run] chat_id={chat_id} server_url: {server_url} -> {resolved_url}")
            continue

        db.execute_query(
            "UPDATE users SET vless_key=%s, server_url=%s WHERE chat_id=%s",
            (vless_link, resolved_url, chat_id),
        )
        updated += 1
        print(f"[ok] chat_id={chat_id} updated")

    print(f"[done] updated={updated}, skipped={skipped}, dry_run={dry_run}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Refresh VLESS keys for all users after server IP changes."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show planned changes without writing to DB."
    )
    args = parser.parse_args()
    refresh_vless_links(dry_run=args.dry_run)
