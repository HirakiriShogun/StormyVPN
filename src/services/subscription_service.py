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

    async def activate_or_extend(self, chat_id: int, bot: Bot) -> bool:
        """Если пользователь есть — продлеваем, если нет — покупаем новый ключ."""
        user_data = self._get_user(chat_id)
        now = datetime.now()
        chat = await bot.get_chat(chat_id)
        username = f"@{chat.username}" if chat.username else "Без username"

        if user_data:
            expiry_date = datetime.strptime(user_data[2], "%d.%m.%Y %H:%M")
            new_expiry_date = expiry_date + timedelta(days=30)
            new_expiry_str = new_expiry_date.strftime("%d.%m.%Y %H:%M")

            success = self.vpn_api.renew_vpn(
                user_data[4], user_data[5], int(new_expiry_date.timestamp() * 1000)
            )

            if success:
                self.database.update_expiry_date(chat_id, new_expiry_str)
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
        new_expiry_date = now + timedelta(days=30)
        new_expiry_str = new_expiry_date.strftime("%d.%m.%Y %H:%M")

        email = VPNUtils.get_vpn_email(chat_id)
        self.vpn_api.select_server()

        try:
            vless_key, inbound_id, server_url = self.vpn_api.buy_vpn(email, 0)
        except Exception:
            await bot.send_message(
                chat_id,
                "❌ Ошибка при активации VPN. Обратитесь в поддержку.\n@hirakiri_shogun",
            )
            return False

        if vless_key:
            self.database.add_user(
                chat_id, username, vless_key, new_expiry_str, inbound_id, server_url
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
