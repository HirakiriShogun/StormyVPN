from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def get_main_keyboard(status: str, is_admin: bool) -> ReplyKeyboardMarkup:
    buttons = [
        [
            KeyboardButton(
                text="Продлить VPN 🔑" if status == "active" else "Оформить VPN 💳"
            )
        ],
        [KeyboardButton(text="Личный кабинет 👤")],
        [KeyboardButton(text="Как настроить VPN? 📖")],
    ]
    if is_admin:
        buttons.append([KeyboardButton(text="Администрирование ⚙️")])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_vpn_guide_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📱 Android / Windows",
                    callback_data="vpn_guide_android_windows",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🍏 iOS / macOS", callback_data="vpn_guide_ios_mac"
                )
            ],
        ]
    )


def get_admin_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Посмотреть всех пользователей")],
            [KeyboardButton(text="Удалить пользователя по ID")],
            [KeyboardButton(text="Добавить пользователя")],
            [KeyboardButton(text="Написать сообщение всем пользователям")],
            [KeyboardButton(text="Послать подарки 🎁")],
            [KeyboardButton(text="Главное меню")],
        ],
        resize_keyboard=True,
    )
