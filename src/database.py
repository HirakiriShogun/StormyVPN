import threading
import time
from datetime import datetime
from typing import Any, Iterable, Optional

import psycopg2
from psycopg2.pool import SimpleConnectionPool

from api_requests import VPNApi
from config import DB_URL

vpn_api = VPNApi()


class VPNDatabase:
    def __init__(self, db_url: str = DB_URL):
        self.db_url = db_url
        self.pool = SimpleConnectionPool(minconn=1, maxconn=10, dsn=db_url)
        self._create_tables()
        self._start_keep_alive()

    def _get_conn(self):
        return self.pool.getconn()

    def _put_conn(self, conn):
        self.pool.putconn(conn)

    def _create_tables(self) -> None:
        query_users = """
        CREATE TABLE IF NOT EXISTS users (
            chat_id BIGINT PRIMARY KEY,
            username TEXT,
            vless_key TEXT,
            expiry_date TEXT,
            reminder_sent BOOLEAN DEFAULT FALSE,
            gift_used BOOLEAN DEFAULT FALSE,
            inbound_id INTEGER,
            server_url TEXT,
            payment_email TEXT,
            is_active BOOLEAN DEFAULT TRUE
        );
        """

        query_payments = """
        CREATE TABLE IF NOT EXISTS payments (
            payment_id TEXT PRIMARY KEY,
            chat_id BIGINT,
            amount REAL,
            status TEXT,
            subscription_days INTEGER DEFAULT 30,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        query_payments_subscription_days_column = """
        ALTER TABLE payments
        ADD COLUMN IF NOT EXISTS subscription_days INTEGER DEFAULT 30;
        """

        query_users_payment_email_column = """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS payment_email TEXT;
        """

        query_users_is_active_column = """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
        """

        query_payments_email_column = """
        ALTER TABLE payments
        ADD COLUMN IF NOT EXISTS payment_email TEXT;
        """

        conn = self._get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(query_users)
                    cur.execute(query_payments)
                    cur.execute(query_payments_subscription_days_column)
                    cur.execute(query_users_payment_email_column)
                    cur.execute(query_users_is_active_column)
                    cur.execute(query_payments_email_column)
        finally:
            self._put_conn(conn)

    def _start_keep_alive(self):
        """Поддерживает пул соединений живым: пинг раз в 5 минут."""

        def keep_alive():
            while True:
                conn = self._get_conn()
                try:
                    with conn.cursor() as cur:
                        cur.execute("SELECT 1")
                        conn.commit()
                except Exception as e:
                    print(f"⚠️ Ошибка Keep-Alive БД: {e}")
                finally:
                    self._put_conn(conn)
                time.sleep(300)

        thread = threading.Thread(target=keep_alive, daemon=True)
        thread.start()

    def execute_query(self, query: str, params: Optional[Iterable[Any]] = None, fetchone: bool = False):
        """Универсальный метод для выполнения SQL-запросов."""
        conn = self._get_conn()
        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params or ())
                    if fetchone:
                        return cursor.fetchone()
                    if cursor.description:
                        return cursor.fetchall()
                    return []
        finally:
            self._put_conn(conn)

    def add_user(
        self,
        chat_id,
        username,
        vless_key,
        expiry_date,
        inbound_id,
        server_url,
        payment_email=None,
        is_active=True,
    ):
        self.execute_query(
            """
            INSERT INTO users (
                chat_id, username, vless_key, expiry_date, reminder_sent, gift_used,
                inbound_id, server_url, payment_email, is_active
            )
            VALUES (%s, %s, %s, %s,
                    COALESCE((SELECT reminder_sent FROM users WHERE chat_id=%s), FALSE),
                    COALESCE((SELECT gift_used FROM users WHERE chat_id=%s), FALSE),
                    %s, %s, %s, %s)
            ON CONFLICT (chat_id) DO UPDATE
            SET username = EXCLUDED.username,
                vless_key = EXCLUDED.vless_key,
                expiry_date = EXCLUDED.expiry_date,
                reminder_sent = CASE
                    WHEN users.expiry_date IS DISTINCT FROM EXCLUDED.expiry_date THEN FALSE
                    ELSE users.reminder_sent
                END,
                inbound_id = EXCLUDED.inbound_id,
                server_url = EXCLUDED.server_url,
                payment_email = COALESCE(EXCLUDED.payment_email, users.payment_email),
                is_active = EXCLUDED.is_active
            """,
            (
                chat_id,
                username,
                vless_key,
                expiry_date,
                chat_id,
                chat_id,
                inbound_id,
                server_url,
                payment_email,
                is_active,
            ),
        )

    def update_expiry_date(self, chat_id, new_expiry_date):
        self.execute_query(
            "UPDATE users SET expiry_date=%s, reminder_sent=FALSE, is_active=TRUE WHERE chat_id=%s",
            (new_expiry_date, chat_id),
        )

    def mark_gift_used(self, chat_id):
        self.execute_query("UPDATE users SET gift_used=TRUE WHERE chat_id=%s", (chat_id,))

    def get_user(self, chat_id):
        return self.execute_query(
            """
            SELECT username, vless_key, expiry_date, gift_used, inbound_id, server_url, payment_email, is_active
            FROM users
            WHERE chat_id=%s
            """,
            (chat_id,),
            fetchone=True,
        )

    def get_payment_email(self, chat_id):
        result = self.execute_query(
            "SELECT payment_email FROM users WHERE chat_id=%s",
            (chat_id,),
            fetchone=True,
        )
        return result[0] if result and result[0] else None

    def update_payment_email(self, chat_id, payment_email):
        self.execute_query(
            "UPDATE users SET payment_email=%s WHERE chat_id=%s",
            (payment_email, chat_id),
        )

    def deactivate_user(self, chat_id):
        result = self.get_user(chat_id)
        if result:
            inbound_id, server_url = result[4], result[5]

            if inbound_id and server_url:
                delete_result = vpn_api.remove_user(inbound_id, server_url)

                if not (delete_result and delete_result.get("success", False)):
                    print(f"❌ Не удалось удалить пользователя {chat_id} с сервера.")
                    return False

            self.deactivate_user_local(chat_id)
            return True
        return False

    def deactivate_user_local(self, chat_id):
        self.execute_query(
            """
            UPDATE users
            SET vless_key=NULL,
                expiry_date=NULL,
                reminder_sent=FALSE,
                inbound_id=NULL,
                server_url=NULL,
                is_active=FALSE
            WHERE chat_id=%s
            """,
            (chat_id,),
        )
        return True

    def remove_user(self, chat_id):
        result = self.get_user(chat_id)
        if result:
            inbound_id, server_url = result[4], result[5]
            if not inbound_id or not server_url:
                self.execute_query("DELETE FROM users WHERE chat_id=%s", (chat_id,))
                return True
            delete_result = vpn_api.remove_user(inbound_id, server_url)

            if delete_result and delete_result.get("success", False):
                self.execute_query("DELETE FROM users WHERE chat_id=%s", (chat_id,))
                return True
            else:
                print(f"❌ Не удалось удалить пользователя {chat_id} с сервера.")
        return False

    def remove_user_local(self, chat_id):
        """Удаляет запись из БД без запроса к 3x-ui (используется, если inbound уже пропал)."""
        self.execute_query("DELETE FROM users WHERE chat_id=%s", (chat_id,))
        return True

    def mark_reminder_sent(self, chat_id):
        self.execute_query("UPDATE users SET reminder_sent = TRUE WHERE chat_id=%s", (chat_id,))

    def get_all_users(self):
        return self.execute_query(
            """
            SELECT chat_id, username, expiry_date, reminder_sent, gift_used, inbound_id, server_url, is_active, payment_email
            FROM users
            """
        )

    def get_all_users_with_keys(self):
        return self.execute_query(
            """
            SELECT chat_id, username, vless_key, expiry_date, reminder_sent, gift_used, inbound_id, server_url, is_active, payment_email
            FROM users
            """
        )

    def get_active_users(self):
        return self.execute_query(
            """
            SELECT chat_id, username, expiry_date, reminder_sent, gift_used, inbound_id, server_url, is_active, payment_email
            FROM users
            WHERE is_active=TRUE
            """
        )

    def get_active_users_with_keys(self):
        return self.execute_query(
            """
            SELECT chat_id, username, vless_key, expiry_date, reminder_sent, gift_used, inbound_id, server_url, is_active, payment_email
            FROM users
            WHERE is_active=TRUE
            """
        )

    def get_user_stats(self):
        result = self.execute_query(
            """
            SELECT
                COUNT(*) AS total_users,
                COUNT(*) FILTER (WHERE is_active=TRUE) AS active_users,
                COUNT(*) FILTER (WHERE is_active=FALSE) AS inactive_users
            FROM users
            """,
            fetchone=True,
        )
        return result or (0, 0, 0)

    def update_vless_key(self, chat_id, vless_key):
        self.execute_query("UPDATE users SET vless_key=%s WHERE chat_id=%s", (vless_key, chat_id))

    def update_user_binding(self, chat_id, inbound_id, server_url):
        self.execute_query(
            "UPDATE users SET inbound_id=%s, server_url=%s WHERE chat_id=%s",
            (inbound_id, server_url, chat_id),
        )

    def get_subscription_status(self, chat_id):
        result = self.execute_query(
            "SELECT expiry_date, is_active FROM users WHERE chat_id=%s",
            (chat_id,),
            fetchone=True,
        )
        if result:
            expiry_date_raw, is_active = result
            if not is_active or not expiry_date_raw:
                return "expired"
            expiry_date = datetime.strptime(expiry_date_raw, "%d.%m.%Y %H:%M")
            return "active" if expiry_date > datetime.now() else "expired"
        return "expired"

    def add_payment(
        self,
        chat_id,
        payment_id,
        amount,
        subscription_days,
        payment_email,
        status="pending",
    ):
        self.execute_query(
            """
            INSERT INTO payments (payment_id, chat_id, amount, status, subscription_days, payment_email)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (payment_id) DO NOTHING
            """,
            (payment_id, chat_id, amount, status, subscription_days, payment_email),
        )

    def update_payment_status(self, payment_id, status):
        self.execute_query(
            "UPDATE payments SET status=%s WHERE payment_id=%s",
            (status, payment_id),
        )

    def get_pending_payments(self):
        return self.execute_query(
            """
            SELECT payment_id, chat_id, COALESCE(subscription_days, 30), payment_email
            FROM payments
            WHERE status='pending'
            """
        )

    def remove_payment(self, payment_id):
        self.execute_query("DELETE FROM payments WHERE payment_id=%s", (payment_id,))

    def clear_all_users(self):
        """Полностью очищает базу данных пользователей"""
        self.execute_query("DELETE FROM users")
        self.execute_query("DELETE FROM payments")
        return True
