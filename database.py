import sqlite3
import threading
import time
from datetime import datetime
from api_requests import VPNApi

vpn_api = VPNApi()

class VPNDatabase:
    def __init__(self, db_name="users.db"):
        self.db_name = db_name
        self.connection = self._connect_db()
        self._create_db()
        self._create_payments_table()
        self._start_keep_alive()

    def _connect_db(self):
        """ Устанавливает постоянное соединение с БД """
        connection = sqlite3.connect(self.db_name, check_same_thread=False, timeout=10)
        connection.execute("PRAGMA synchronous = NORMAL")  # Ускорение записи
        connection.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging
        connection.execute("PRAGMA cache_size = 10000")  # Увеличенный кеш
        return connection

    def _create_db(self):
        """ Создаёт таблицу пользователей, если её нет """
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    chat_id INTEGER PRIMARY KEY,
                    username TEXT,
                    vless_key TEXT,
                    expiry_date TEXT,
                    reminder_sent BOOLEAN DEFAULT 0,
                    gift_used BOOLEAN DEFAULT 0,
                    inbound_id INTEGER,
                    server_url TEXT
                )
            ''')

    def _create_payments_table(self):
        """ Создаёт таблицу платежей, если её нет """
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    payment_id TEXT PRIMARY KEY,
                    chat_id INTEGER,
                    amount REAL,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

    def _start_keep_alive(self):
        """ Поддерживает соединение с БД активным, отправляя пинг-запрос раз в 5 минут """
        def keep_alive():
            while True:
                try:
                    with self.connection:
                        self.connection.execute("SELECT 1")  # Пинг БД
                except Exception as e:
                    print(f"⚠️ Ошибка Keep-Alive БД: {e}")
                time.sleep(300)  # 5 минут

        thread = threading.Thread(target=keep_alive, daemon=True)
        thread.start()

    def execute_query(self, query, params=None, fetchone=False):
        """ Универсальный метод для выполнения SQL-запросов """
        start_time = time.time()
        with self.connection:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            if fetchone:
                exec_time = time.time() - start_time
                return cursor.fetchone()
            exec_time = time.time() - start_time
            return cursor.fetchall()
        print(f"⏳ SQL выполнен за {exec_time:.3f} сек: {query}")

    def add_user(self, chat_id, username, vless_key, expiry_date, inbound_id, server_url):
        self.execute_query("""
            INSERT OR REPLACE INTO users 
            (chat_id, username, vless_key, expiry_date, reminder_sent, gift_used, inbound_id, server_url) 
            VALUES (?, ?, ?, ?, COALESCE((SELECT reminder_sent FROM users WHERE chat_id=?), 0), 
            COALESCE((SELECT gift_used FROM users WHERE chat_id=?), 0), ?, ?)
        """, (chat_id, username, vless_key, expiry_date, chat_id, chat_id, inbound_id, server_url))

    def update_expiry_date(self, chat_id, new_expiry_date):
        self.execute_query("UPDATE users SET expiry_date=?, reminder_sent=0 WHERE chat_id=?", (new_expiry_date, chat_id))

    def mark_gift_used(self, chat_id):
        self.execute_query("UPDATE users SET gift_used=1 WHERE chat_id=?", (chat_id,))

    def get_user(self, chat_id):
        return self.execute_query("SELECT username, vless_key, expiry_date, gift_used, inbound_id, server_url FROM users WHERE chat_id=?", (chat_id,), fetchone=True)

    def remove_user(self, chat_id):
        result = self.get_user(chat_id)
        if result:
            inbound_id, server_url = result[4], result[5]
            delete_result = vpn_api.remove_user(inbound_id, server_url)

            if delete_result and delete_result.get("success", False):
                self.execute_query("DELETE FROM users WHERE chat_id=?", (chat_id,))
                return True
            else:
                print(f"❌ Не удалось удалить пользователя {chat_id} с сервера.")
        return False

    def mark_reminder_sent(self, chat_id):
        self.execute_query("UPDATE users SET reminder_sent = 1 WHERE chat_id=?", (chat_id,))

    def get_all_users(self):
        return self.execute_query("SELECT chat_id, username, expiry_date, reminder_sent, gift_used, inbound_id, server_url FROM users")

    def get_subscription_status(self, chat_id):
        result = self.execute_query("SELECT expiry_date FROM users WHERE chat_id=?", (chat_id,), fetchone=True)
        if result:
            expiry_date = datetime.strptime(result[0], "%d.%m.%Y %H:%M")
            return "active" if expiry_date > datetime.now() else "expired"
        return "expired"

    def add_payment(self, chat_id, payment_id, amount, status='pending'):
        self.execute_query("""
            INSERT INTO payments (payment_id, chat_id, amount, status)
            VALUES (?, ?, ?, ?)
        """, (payment_id, chat_id, amount, status))

    def update_payment_status(self, payment_id, status):
        self.execute_query("UPDATE payments SET status=? WHERE payment_id=?", (status, payment_id))

    def get_pending_payments(self):
        return self.execute_query("SELECT payment_id, chat_id FROM payments WHERE status='pending'")

    def remove_payment(self, payment_id):
        self.execute_query("DELETE FROM payments WHERE payment_id=?", (payment_id,))
        
    def clear_all_users(self):
        """Полностью очищает базу данных пользователей"""
        with self.connection:
            self.connection.execute("DELETE FROM users")
            self.connection.execute("DELETE FROM payments")
            self.connection.commit()
        return True
