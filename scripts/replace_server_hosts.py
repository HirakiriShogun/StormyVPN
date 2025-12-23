"""
Одноразовый скрипт для массовой замены IP в vless_key и server_url без обращений к панелям.
Используйте, если менялся только хост (IP) при сохранении того же порта/пути.

Пример запуска:
    python scripts/replace_server_hosts.py --map 38.135.53.154=91.149.255.134 --map 38.135.53.215=91.149.255.189
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict
from urllib.parse import urlsplit, urlunsplit


BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / "src"))

from database import VPNDatabase  # noqa: E402


def replace_hosts(text: str, host_map: Dict[str, str]) -> str:
    """Меняет хосты в строке по карте host_map (учитывает user@host:port в VLESS)."""
    try:
        parts = urlsplit(text)
    except Exception:
        return text

    netloc = parts.netloc
    userinfo, hostport = (netloc.split("@", 1) + [None])[:2] if "@" in netloc else (None, netloc)
    host_only, port = (hostport.split(":", 1) + [""])[:2] if hostport else ("", "")

    new_host = None
    if hostport in host_map:
        new_host = host_map[hostport]
    elif host_only in host_map:
        new_host = host_map[host_only]
        if ":" not in new_host and port:
            new_host = f"{new_host}:{port}"

    if not new_host:
        return text

    new_netloc = f"{userinfo}@{new_host}" if userinfo else new_host
    return urlunsplit((parts.scheme, new_netloc, parts.path, parts.query, parts.fragment))


def main(host_map: Dict[str, str], dry_run: bool) -> None:
    db = VPNDatabase()
    users = db.get_all_users()
    updated = 0

    for user in users:
        chat_id, username, expiry_date, _, _, _, server_url = user
        new_server_url = replace_hosts(server_url or "", host_map)

        # vless_key лежит в колонке vless_key (третья по схеме)
        vless_key = db.execute_query(
            "SELECT vless_key FROM users WHERE chat_id=%s",
            (chat_id,),
            fetchone=True,
        )[0]
        new_vless_key = replace_hosts(vless_key or "", host_map)

        if new_server_url == server_url and new_vless_key == vless_key:
            continue

        if dry_run:
            print(f"[dry-run] chat_id={chat_id}: server_url {server_url} -> {new_server_url}")
            print(f"          vless_key host updated")
            updated += 1
            continue

        db.execute_query(
            "UPDATE users SET server_url=%s, vless_key=%s WHERE chat_id=%s",
            (new_server_url, new_vless_key, chat_id),
        )
        updated += 1
        print(f"[ok] chat_id={chat_id} updated")

    print(f"[done] touched={updated}, dry_run={dry_run}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Replace hosts in vless_key and server_url.")
    parser.add_argument(
        "--map",
        action="append",
        required=True,
        help="Хостовая замена в формате old_host=new_host (порт оставьте вместе, если нужно). Можно несколько раз.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Показать изменения без записи в БД")
    args = parser.parse_args()

    host_map: Dict[str, str] = {}
    for item in args.map:
        if "=" not in item:
            parser.error(f"Некорректный формат --map '{item}', используйте old=new")
        old, new = item.split("=", 1)
        host_map[old.strip()] = new.strip()

    main(host_map, dry_run=args.dry_run)
