import uuid
from typing import Optional, Tuple

import yookassa
from yookassa import Payment


class PaymentService:
    def __init__(self, shop_id: str, secret_key: str, return_url: str):
        self.shop_id = shop_id
        self.secret_key = secret_key
        self.return_url = return_url
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
        payment = Payment.find_one(payment_id)
        return payment.status if payment else None
