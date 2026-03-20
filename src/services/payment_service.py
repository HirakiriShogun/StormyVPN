import uuid
import logging
import time
from typing import Optional, Tuple

import requests
import yookassa
from yookassa import Payment
from yookassa.domain.exceptions.api_error import ApiError


TEMPORARY_HTTP_STATUSES = {429, 500, 502, 503, 504}


class PaymentService:
    def __init__(self, shop_id: str, secret_key: str, return_url: str):
        self.shop_id = shop_id
        self.secret_key = secret_key
        self.return_url = return_url
        self.status_check_max_retries = 3
        self.status_check_base_delay = 1.0
        yookassa.Configuration.account_id = shop_id
        yookassa.Configuration.secret_key = secret_key

    def create_payment(self, amount: float, chat_id: int, email: str) -> Tuple[str, str]:
        """Создаёт платёж и возвращает (payment_id, confirmation_url)."""
        idempotence_key = str(uuid.uuid4())
        payment = Payment.create(
            {
                "amount": {"value": f"{amount:.2f}", "currency": "RUB"},
                "confirmation": {"type": "redirect", "return_url": self.return_url},
                "capture": True,
                "description": f"Оплата VPN для {chat_id}",
                "metadata": {"chat_id": chat_id, "email": email},
                "receipt": {
                    "customer": {"email": email},
                    "items": [
                        {
                            "description": "Оплата VPN",
                            "quantity": 1,
                            "amount": {"value": f"{amount:.2f}", "currency": "RUB"},
                            "vat_code": 1,
                        }
                    ],
                },
            },
            idempotence_key,
        )
        return payment.id, payment.confirmation.confirmation_url

    def get_payment_status(self, payment_id: str) -> Optional[str]:
        last_error: Optional[Exception] = None

        for attempt in range(1, self.status_check_max_retries + 1):
            try:
                payment = Payment.find_one(payment_id)
                return payment.status if payment else None
            except ApiError as exc:
                last_error = exc
                status_code = self._extract_status_code(exc)
                is_temporary = status_code in TEMPORARY_HTTP_STATUSES

                if is_temporary and attempt < self.status_check_max_retries:
                    delay = self.status_check_base_delay * (2 ** (attempt - 1))
                    logging.warning(
                        "Временная ошибка YooKassa при проверке платежа %s: HTTP %s, попытка %s/%s, повтор через %.1f сек.",
                        payment_id,
                        status_code,
                        attempt,
                        self.status_check_max_retries,
                        delay,
                    )
                    time.sleep(delay)
                    continue
                raise
            except requests.RequestException as exc:
                last_error = exc

                if attempt < self.status_check_max_retries:
                    delay = self.status_check_base_delay * (2 ** (attempt - 1))
                    logging.warning(
                        "Сетевая ошибка при проверке платежа %s: %s, попытка %s/%s, повтор через %.1f сек.",
                        payment_id,
                        exc,
                        attempt,
                        self.status_check_max_retries,
                        delay,
                    )
                    time.sleep(delay)
                    continue
                raise

        if last_error:
            raise last_error

        return None

    @staticmethod
    def _extract_status_code(error: ApiError) -> Optional[int]:
        payload = error.args[0] if error.args else None
        if not isinstance(payload, dict):
            return None

        status_code = payload.get("error", {}).get("status_code")
        if isinstance(status_code, int):
            return status_code

        if isinstance(status_code, str) and status_code.isdigit():
            return int(status_code)

        return None
