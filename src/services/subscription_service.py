import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

from aiogram import Bot

from utils import VPNUtils


class SubscriptionService:
    def __init__(self, database, vpn_api):
        self.database = database
        self.vpn_api = vpn_api

    def _get_user(self, chat_id: int) -> Optional[Tuple]:
        return self.database.get_user(chat_id)

    async def activate_or_extend(
        self,
        chat_id: int,
        bot: Bot,
        subscription_days: int = 30,
        payment_email: Optional[str] = None,
    ) -> bool:
        """Если пользователь есть — продлеваем, если нет — покупаем новый ключ."""
        user_data = self._get_user(chat_id)
        now = datetime.now()
        chat = await bot.get_chat(chat_id)
        username = f"@{chat.username}" if chat.username else "Без username"
        stored_payment_email = user_data[6] if user_data and len(user_data) > 6 else None
        is_active = bool(user_data[7]) if user_data and len(user_data) > 7 else False
        effective_payment_email = payment_email or stored_payment_email

        if user_data and is_active and user_data[4] and user_data[5]:
            expiry_date = datetime.strptime(user_data[2], "%d.%m.%Y %H:%M")
            base_expiry_date = expiry_date if expiry_date > now else now
            new_expiry_date = base_expiry_date + timedelta(days=subscription_days)
            new_expiry_str = new_expiry_date.strftime("%d.%m.%Y %H:%M")

            success = self.vpn_api.renew_vpn(
                user_data[4], user_data[5], int(new_expiry_date.timestamp() * 1000)
            )

            if success:
                self.database.update_expiry_date(chat_id, new_expiry_str)
                if effective_payment_email and effective_payment_email != stored_payment_email:
                    self.database.update_payment_email(chat_id, effective_payment_email)
                await bot.send_message(
                    chat_id,
                    f"✅ Подписка продлена!\n⏳ Действительна до: {new_expiry_str}",
                )
                return True

            await bot.send_message(
                chat_id,
                "❌ Ошибка продления подписки. Свяжитесь с поддержкой.\n@hirakiri_shogun",
            )
            return False

        # Новый пользователь
        new_expiry_date = now + timedelta(days=subscription_days)
        new_expiry_str = new_expiry_date.strftime("%d.%m.%Y %H:%M")

        vpn_email = VPNUtils.get_vpn_email(chat_id)
        self.vpn_api.select_server()

        if not self.vpn_api.active_server:
            logging.error("Нет активного сервера для активации подписки (chat_id=%s)", chat_id)
            await bot.send_message(
                chat_id,
                "❌ Нет доступных серверов. Повторите позже или свяжитесь с поддержкой.",
            )
            return False

        try:
            result = self.vpn_api.buy_vpn(vpn_email, subscription_days)
        except Exception as e:
            logging.exception("Ошибка при активации VPN для chat_id=%s: %s", chat_id, e)
            await bot.send_message(
                chat_id,
                "❌ Ошибка при активации VPN. Обратитесь в поддержку.\n@hirakiri_shogun",
            )
            return False

        if not result:
            logging.error("VPN API вернул пустой результат при активации (chat_id=%s)", chat_id)
            await bot.send_message(
                chat_id,
                "❌ Не удалось получить VPN-ключ. Проверьте сервер или обратитесь в поддержку.",
            )
            return False

        vless_key, inbound_id, server_url = result

        if vless_key:
            self.database.add_user(
                chat_id,
                username,
                vless_key,
                new_expiry_str,
                inbound_id,
                server_url,
                payment_email=effective_payment_email,
                is_active=True,
            )
            await bot.send_message(
                chat_id,
                "✅ Подписка активирована!\n"
                f"🔑 Ваш VLESS-ключ:\n```\n{vless_key}\n```\n"
                f"⏳ Действителен до: {new_expiry_str}",
                parse_mode="Markdown",
            )
            return True

        await bot.send_message(
            chat_id, "❌ Ошибка активации. Свяжитесь с поддержкой @hirakiri_shogун"
        )
        return False
