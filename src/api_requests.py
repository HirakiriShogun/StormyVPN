
import logging
import os
import requests
import json
import urllib3
import random
import uuid
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, quote

from config import SERVERS

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "session")
logger = logging.getLogger(__name__)

def _normalize_url(url: str) -> str:
    return url.rstrip('/') if url else url

def _has_cookie(session, server_url: str) -> bool:
    """Проверяем, есть ли cookie для этого хоста в сессии."""
    from urllib.parse import urlparse
    try:
        host = urlparse(server_url).hostname
    except Exception:
        host = None
    if not host:
        return False
    jar = session.cookies
    return jar.get(SESSION_COOKIE_NAME, domain=host) is not None

class VPNApi:
    def __init__(self, servers: Optional[List[Dict[str, Any]]] = None):
        self.session = requests.Session()
        self.active_server = None
        self.session_cookie = None
        self.servers = servers or SERVERS

    def authenticate_server(self, server):
        login_data = {"username": server["username"], "password": server["password"]}
        print(f"[auth] try {server['url']} as {server['username']}", flush=True)
        try:
            login_url = f"{server['url']}/login/"
            # Попытка 1: x-www-form-urlencoded (data)
            response = self.session.post(
                login_url, data=login_data, verify=False, timeout=15
            )
            print(f"[auth-urlencoded] {server['url']} status={response.status_code} cookies={list(response.cookies.keys())}", flush=True)
            if response.text:
                print(f"[auth-urlencoded-body] {response.text[:200]}", flush=True)

            cookie = response.cookies.get(SESSION_COOKIE_NAME)
            if response.status_code == 200 and cookie:
                self.session_cookie = cookie
                print(f"[auth] success urlencoded {server['url']} cookie={SESSION_COOKIE_NAME}", flush=True)
                return True

            # Попытка 2: multipart/form-data (как в Postman) если нет cookie
            files = {k: (None, v) for k, v in login_data.items()}
            response2 = self.session.post(
                login_url, files=files, verify=False, timeout=15
            )
            print(f"[auth-multipart] {server['url']} status={response2.status_code} cookies={list(response2.cookies.keys())}", flush=True)
            if response2.text:
                print(f"[auth-multipart-body] {response2.text[:200]}", flush=True)

            cookie2 = response2.cookies.get(SESSION_COOKIE_NAME)
            if response2.status_code == 200 and cookie2:
                self.session_cookie = cookie2
                print(f"[auth] success multipart {server['url']} cookie={SESSION_COOKIE_NAME}", flush=True)
                return True

            print(f"[auth-error] {server['url']} status1={response.status_code} cookies1={response.cookies.get_dict()} status2={response2.status_code} cookies2={response2.cookies.get_dict()}", flush=True)
        except Exception as e:
            print(f"[auth-exception] {server['url']} error={e}")
        return False

    def check_server_load(self, server):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Cookie": f"{SESSION_COOKIE_NAME}={self.session_cookie}"
        }
        try:
            response = self.session.get(f"{server['url']}/panel/api/inbounds/list/", headers=headers, verify=False)
            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    total_clients = sum(len(inbound["clientStats"]) for inbound in data["obj"])
                    return total_clients / server["max_quantity"]
            print(f"Error fetching client list from {server['url']}: {response.text}")
        except Exception as e:
            print(f"Error during server check {server['url']}: {e}")
        return float('inf')

    def select_server(self):
        if not self.servers:
            print("No server configuration provided.")
            return None

        self.active_server = None
        self.session_cookie = None
        best_server = None
        min_load = float('inf')

        print(f"[select] candidates={len(self.servers)}", flush=True)
        for server in self.servers:
            server = server.copy()
            server["url"] = _normalize_url(server["url"])
            if self.authenticate_server(server):
                load = self.check_server_load(server)
                print(f"[select] {server['url']} load={load}", flush=True)
                if load < min_load:
                    min_load = load
                    best_server = server
                elif best_server is None:
                    # Если это первый успешно авторизованный сервер, сохраняем его даже при невозможности расчета нагрузки
                    best_server = server

        if best_server:
            print(f"[select] selected {best_server['url']} load={min_load}", flush=True)
            self.active_server = best_server
        else:
            print("[select-error] Failed to authenticate any configured server")

    def buy_vpn(self, email, admin):
        if not self.active_server:
            print("No active server available.")
            return None

        client_id = str(uuid.uuid4())
        sub_id = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=16))
        port = random.randint(10000, 60000)

        days_to_add = 365 if admin else 30
        expiry_time = int(time.time() * 1000) + (days_to_add * 24 * 60 * 60 * 1000)
        short_id = hex(random.randint(0, 2**32 - 1))[2:].zfill(8)
        client_data = {
            "up": 0,
            "down": 0,
            "total": 0,
            "remark": "",
            "enable": True,
            "expiryTime": expiry_time,
            "listen": "",
            "port": port,
            "protocol": "vless",
            "settings": json.dumps({
                "clients": [{
                    "id": client_id,
                    "flow": "",
                    "email": email,
                    "limitIp": 0,
                    "totalGB": 0,
                    "expiryTime": 0,
                    "enable": True,
                    "tgId": "",
                    "subId": sub_id,
                    "reset": 0
                }],
                "decryption": "none",
                "fallbacks": []
            }),
            "streamSettings": json.dumps({
                "network": "tcp",
                "security": "reality",
                "externalProxy": [],
                "realitySettings": {
                    "show": False,
                    "xver": 0,
                    "dest": "yahoo.com:443",
                    "serverNames": ["yahoo.com", "www.yahoo.com"],
                    "privateKey": "wIc7zBUiTXBGxM7S7wl0nCZ663OAvzTDNqS7-bsxV3A",
                    "shortIds": [short_id],
                    "settings": {
                        "publicKey": "2UqLjQFhlvLcY7VzaKRotIDQFOgAJe1dYD1njigp9wk",
                        "fingerprint": "random",
                        "serverName": "yahoo.com",
                        "spiderX": "/"
                    }
                },
                "tcpSettings": {
                    "acceptProxyProtocol": False,
                    "header": {"type": "none"}
                }
            })
        }
        
        try:
            response = self.session.post(f"{self.active_server['url']}/panel/api/inbounds/add/",
                                         json=client_data, verify=False)
            if response.status_code == 200:
                status_obj = response.json()["msg"]
                print(status_obj)
                if status_obj == "Create Successfully":
                    client_obj = response.json()["obj"]
                    return self.generate_vless_key(client_obj, short_id)
                elif status_obj == "Inbound has been successfully created.":
                    client_obj = response.json()["obj"]
                    return self.generate_vless_key(client_obj, short_id)
            else:
                print(f"Failed to add client: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error during client creation: {e}")
            return None

    def generate_vless_key(self, client_obj, short_id):
        inbound_id = client_obj["id"]
        server_url = self.active_server['url']
        vless_uri = self.build_vless_uri(client_obj, server_url)
        return vless_uri, inbound_id, server_url

    def build_vless_uri(self, inbound_obj: Dict[str, Any], server_url: str) -> Optional[str]:
        """Собирает VLESS ссылку из inbound данных (используем реальные настройки сервера)."""
        try:
            settings_raw = inbound_obj.get("settings")
            settings = json.loads(settings_raw) if isinstance(settings_raw, str) else (settings_raw or {})
        except Exception:
            logger.exception("Не удалось разобрать settings для inbound %s", inbound_obj.get("id"))
            return None

        clients = settings.get("clients") or []
        if not clients or not isinstance(clients, list):
            logger.warning("В inbound %s нет clients", inbound_obj.get("id"))
            return None

        client = clients[0]
        client_id = client.get("id")
        if not client_id:
            logger.warning("В inbound %s отсутствует client id", inbound_obj.get("id"))
            return None

        try:
            stream_settings_raw = inbound_obj.get("streamSettings")
            stream_settings = json.loads(stream_settings_raw) if isinstance(stream_settings_raw, str) else (stream_settings_raw or {})
        except Exception:
            logger.exception("Не удалось разобрать streamSettings для inbound %s", inbound_obj.get("id"))
            return None

        network = stream_settings.get("network", "tcp")
        security = stream_settings.get("security", "reality")
        reality_settings = stream_settings.get("realitySettings", {}) or {}
        reality_opts = reality_settings.get("settings", {}) or {}

        server_host = urlparse(server_url).hostname or ""
        port = inbound_obj.get("port")
        decryption = settings.get("decryption", "none") or "none"
        short_ids = reality_settings.get("shortIds") or []
        short_id = short_ids[0] if short_ids else ""
        server_names = reality_settings.get("serverNames") or []
        sni = server_names[0] if server_names else reality_opts.get("serverName", "")
        pbk = reality_opts.get("publicKey", "")
        fingerprint = reality_opts.get("fingerprint", "random") or "random"
        spider_x = reality_opts.get("spiderX", "/") or "/"
        flow = client.get("flow") or ""
        tag_source = client.get("email") or client.get("subId") or client_id
        tag = quote(tag_source, safe="")

        query_parts = [
            ("type", network),
            ("encryption", decryption),
            ("security", security),
            ("pbk", pbk),
            ("fp", fingerprint),
            ("sni", sni),
            ("sid", short_id),
            ("spx", spider_x),
        ]
        if flow:
            query_parts.append(("flow", flow))

        def _encode(value: Any) -> str:
            return quote(str(value), safe="")

        query = "&".join(f"{k}={_encode(v)}" for k, v in query_parts if v not in (None, ""))
        return f"vless://{client_id}@{server_host}:{port}?{query}#{tag}"

    def remove_user(self, inbound_id, server_url):
        target_url = _normalize_url(server_url)
        server = next((s for s in self.servers if _normalize_url(s["url"]) == target_url), None)
        
        if not server:
            print(f"Сервер с URL {server_url} не найден в списке.")
            return None

        if not self.authenticate_server(server):
            print(f"Не удалось авторизоваться на сервере {server_url}.")
            return None

        try:
            url = f"{server['url']}/panel/api/inbounds/del/{inbound_id}/"
            delete_response = self.session.post(url, verify=False)
            
            if delete_response.status_code == 200:
                print(f"Пользователь с inbound_id {inbound_id} успешно удалён с {server_url}")
                return delete_response.json()
            else:
                print(f"Ошибка удаления пользователя {inbound_id}: {delete_response.status_code} - {delete_response.text}")
                return None
        except Exception as e:
            print(f"Ошибка при удалении пользователя {inbound_id} с {server_url}: {e}")
            return None
        
    def renew_vpn(self, inbound_id, server_url, new_expiry_time):
        target_url = _normalize_url(server_url)
        server = next((s for s in self.servers if _normalize_url(s["url"]) == target_url), None)
        if not server:
            print(f"❌ Ошибка: Сервер {server_url} не найден!")
            return False

        if not self.authenticate_server(server):
            print(f"❌ Ошибка авторизации на сервере {server_url}. Продление невозможно.")
            return False

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Cookie": f"{SESSION_COOKIE_NAME}={self.session_cookie}"
        }

        try:
            # Получаем текущие данные inbound
            response = self.session.get(
                f"{server['url']}/panel/api/inbounds/get/{inbound_id}/",
                headers=headers, verify=False
            )

            if response.status_code != 200:
                print(f"❌ Ошибка получения inbound: {response.status_code} - {response.text}")
                return False

            inbound_data = response.json().get("obj")
            if not inbound_data:
                print("❌ Не удалось получить inbound данные!")
                return False

            # Обновляем ключевые поля
            inbound_data["expiryTime"] = new_expiry_time
            inbound_data["enable"] = True

            # Обновляем settings.clients[0].enable = True
            settings = json.loads(inbound_data.get("settings", "{}"))
            if "clients" in settings and isinstance(settings["clients"], list) and settings["clients"]:
                settings["clients"][0]["enable"] = True
            inbound_data["settings"] = json.dumps(settings)

            # Обновляем объект на сервере
            update_response = self.session.post(
                f"{server['url']}/panel/api/inbounds/update/{inbound_id}/",
                json=inbound_data, headers=headers, verify=False
            )

            if update_response.status_code == 200:
                result = update_response.json()
                if result.get("msg") in ["Update Successfully", "Inbound has been successfully updated."]:
                    print(f"✅ Подписка обновлена! Новый срок: {datetime.fromtimestamp(new_expiry_time / 1000)}")
                    return True
                else:
                    print(f"❌ Ошибка продления подписки: {result.get('msg')}")
            else:
                print(f"❌ Ошибка обновления: {update_response.status_code} - {update_response.text}")

        except Exception as e:
            print(f"❌ Ошибка при обновлении подписки: {e}")

        return False

    def get_inbound_data(self, inbound_id, server_url):
        """Возвращает inbound данные или словарь с ключами _error/_not_found."""
        target_url = _normalize_url(server_url)
        server = next((s for s in self.servers if _normalize_url(s["url"]) == target_url), None)
        if not server:
            print(f"❌ Ошибка: Сервер {server_url} не найден!")
            return {"_error": "server_not_configured"}

        need_auth = not _has_cookie(self.session, server["url"])
        if need_auth:
            if not self.authenticate_server(server):
                print(f"❌ Ошибка авторизации на сервере {server_url}.")
                return {"_error": "auth_failed"}

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Cookie": f"{SESSION_COOKIE_NAME}={self.session_cookie}",
        }

        try:
            url = f"{server['url']}/panel/api/inbounds/get/{inbound_id}/"
            response = self.session.get(url, headers=headers, verify=False, timeout=10)
            if response.status_code in (401, 403) and not need_auth:
                # Переавторизуемся один раз при просрочке cookie
                if self.authenticate_server(server):
                    headers["Cookie"] = f"{SESSION_COOKIE_NAME}={self.session_cookie}"
                    response = self.session.get(url, headers=headers, verify=False, timeout=10)
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка при запросе inbound: {e}")
            return {"_error": f"request_error: {e}"}
        except Exception as e:
            print(f"❌ Неизвестная ошибка при запросе inbound: {e}")
            return {"_error": f"unexpected_error: {e}"}

        if response.status_code == 404:
            print(f"❌ inbound_id {inbound_id} не найден на {server_url}")
            return {"_not_found": True}
        if response.status_code != 200:
            print(f"❌ Ошибка получения inbound: {response.status_code} - {response.text}")
            return {"_error": f"status_{response.status_code}"}

        try:
            inbound_data = response.json()
        except ValueError:
            print("❌ Ошибка: невалидный JSON при получении inbound")
            return {"_error": "invalid_json"}

        if not inbound_data.get("success", False):
            print(f"❌ Ошибка API при получении inbound: {inbound_data}")
            if "not found" in str(inbound_data).lower():
                return {"_not_found": True}
            return {"_error": "api_error"}

        inbound_obj = inbound_data.get("obj")
        if not inbound_obj:
            print("❌ Ошибка: объект inbound пустой!")
            return {"_error": "empty_response"}

        return inbound_obj  # Возвращаем актуальные данные
        
    def scan_all_inbounds(self, server_url):
        """Сканирует все возможные inbound_id на сервере (от 50 до 210)"""
        server = next((s for s in self.servers if s["url"] == server_url), None)
        if not server:
            print(f"❌ Ошибка: Сервер {server_url} не найден!")
            return []

        if not self.authenticate_server(server):
            print(f"❌ Ошибка авторизации на сервере {server_url}.")
            return []

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Cookie": f"{SESSION_COOKIE_NAME}={self.session_cookie}"
        }

        found_inbounds = []
        
        for inbound_id in range(50, 211):  # от 50 до 210 включительно
            try:
                response = self.session.get(
                    f"{server['url']}/panel/api/inbounds/get/{inbound_id}/",
                    headers=headers, 
                    verify=False,
                    timeout=5
                )

                if response.status_code == 200:
                    inbound_data = response.json()
                    if inbound_data.get("success", False) and "obj" in inbound_data:
                        print(f"✅ Найден валидный inbound с ID: {inbound_id}")
                        found_inbounds.append(inbound_data["obj"])
                    else:
                        print(f"ℹ️ ID {inbound_id} - невалидные данные: {inbound_data}")
                elif response.status_code == 404:
                    continue
                else:
                    print(f"⚠️ ID {inbound_id} - ошибка {response.status_code}: {response.text}")

            except requests.exceptions.RequestException as e:
                print(f"⚠️ Ошибка запроса для ID {inbound_id}: {e}")
                continue
            except Exception as e:
                print(f"⚠️ Неожиданная ошибка для ID {inbound_id}: {e}")
                continue

        print(f"🔚 Найдено inbounds: {len(found_inbounds)}")
        return found_inbounds


    def get_user_data_from_inbound(self, inbound_data, server_url):
        """Получает данные пользователя из inbound и собирает актуальную VLESS ссылку."""
        if not inbound_data:
            print("? Пустые inbound_data")
            return None

        try:
            inbound_id = inbound_data.get("id")
            print(f"?? Обрабатываем inbound ID: {inbound_id}")
            
            settings_raw = inbound_data.get("settings")
            if not settings_raw:
                print(f"? Inbound {inbound_id} не содержит settings")
                return None
                
            try:
                settings = json.loads(settings_raw) if isinstance(settings_raw, str) else settings_raw
            except json.JSONDecodeError:
                print(f"? Inbound {inbound_id} содержит невалидные settings")
                return None

            clients = settings.get("clients")
            if not clients or not isinstance(clients, list):
                print(f"? Inbound {inbound_id} не содержит clients")
                return None

            client = clients[0]
            if not isinstance(client, dict):
                print(f"? Inbound {inbound_id} содержит невалидного клиента")
                return None

            email = client.get("email")
            if not email or not isinstance(email, str):
                print(f"? Inbound {inbound_id} содержит невалидный email")
                return None

            try:
                if email.startswith("user_") and "@stormyvpn.com" in email:
                    user_part = email.split("@")[0]
                    chat_id = int(user_part.split("_")[1])
                    print(f"?? Извлечен chat_id: {chat_id} из email: {email}")
                else:
                    print(f"? Inbound {inbound_id} содержит email в неожиданном формате: {email}")
                    return None
            except (ValueError, IndexError) as e:
                print(f"? Ошибка извлечения chat_id из email: {email}, ошибка: {e}")
                return None

            expiry_time = client.get("expiryTime", inbound_data.get("expiryTime", 0))
            if expiry_time == 0:
                expiry_time = int((datetime.now() + timedelta(days=30)).timestamp() * 1000)
                print(f"?? Для inbound {inbound_id} установлена дефолтная дата окончания подписки")
            
            try:
                expiry_date = datetime.fromtimestamp(expiry_time / 1000)
                expiry_str = expiry_date.strftime("%d.%m.%Y %H:%M")
                print(f"?? Дата окончания подписки: {expiry_str}")
            except Exception as e:
                print(f"? Ошибка обработки expiryTime: {e}")
                expiry_date = datetime.now() + timedelta(days=30)
                expiry_str = expiry_date.strftime("%d.%m.%Y %H:%M")

            vless_key = self.build_vless_uri(inbound_data, server_url)
            if not vless_key:
                print(f"? Ошибка генерации VLESS ключа для inbound {inbound_id}")
                return None

            print(f"? Успешно обработан inbound {inbound_id} для пользователя {email}")
            return {
                "chat_id": chat_id,
                "email": email,
                "expiry_date": expiry_str,
                "vless_key": vless_key,
                "inbound_id": inbound_id,
                "server_url": server_url
            }

        except Exception as e:
            print(f"? Критическая ошибка обработки inbound: {e}")
            return None

    def restore_all_users_bruteforce(self):
        """Восстанавливает пользователей методом перебора всех возможных ID"""
        restored_users = []
        
        if not self.servers:
            print("No server configuration provided for restore.")
            return restored_users

        for server in self.servers:
            print(f"\n🔍 Начинаем сканирование сервера: {server['url']}")
            
            inbounds = self.scan_all_inbounds(server["url"])
            if not inbounds:
                print(f"ℹ️ На сервере {server['url']} не найдено inbounds")
                continue
                
            print(f"✅ На сервере {server['url']} найдено {len(inbounds)} inbounds")
            
            for inbound in inbounds:
                user_data = self.get_user_data_from_inbound(inbound, server["url"])
                if user_data:
                    print(f"👤 Найден пользователь: {user_data['email']}")
                    restored_users.append(user_data)
                else:
                    print(f"ℹ️ Inbound {inbound.get('id', 'unknown')} не содержит валидных данных")
        
        print(f"\n🔚 Всего восстановлено пользователей: {len(restored_users)}")
        if restored_users:
            print("Пример восстановленного пользователя:", restored_users[0])
        return restored_users

