import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Bot, Dispatcher, F, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup
from pathlib import Path

from api_requests import VPNApi
from config import (
    ADMIN_IDS,
    API_TOKEN,
    DATA_DIR,
    IMAGES_DIR,
    MAINTENANCE_CONTACT,
    MAINTENANCE_MODE,
    PAYMENT_RETURN_URL,
    SHOP_API,
    SHOP_ID,
    VIDEOS_DIR,
)
from database import VPNDatabase
from keyboards import get_admin_keyboard, get_main_keyboard, get_vpn_guide_keyboard
from services.payment_service import PaymentService
from services.subscription_service import SubscriptionService
from states import AdminState, EmailState
from utils import VPNUtils

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)


async def notify_admin(message: str):
    """Отправляет уведомление первому админу (если задан)."""
    if not ADMIN_IDS:
        return
    admin_id = ADMIN_IDS[0]
    try:
        await bot.send_message(admin_id, message)
    except Exception as e:
        logging.exception("Не удалось отправить уведомление админу: %s", e)


class AdminOnlyMiddleware(BaseMiddleware):
    def __init__(self, admins: list[int], maintenance_contact: str, maintenance_mode: bool):
        super().__init__()
        self.admins = set(admins)
        self.maintenance_contact = maintenance_contact
        self.maintenance_mode = maintenance_mode

    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        # Если нет режима техработ — пропускаем всех
        if not self.maintenance_mode:
            return await handler(event, data)

        chat_id = None
        if isinstance(event, types.Message):
            chat_id = event.chat.id
        elif isinstance(event, types.CallbackQuery):
            chat_id = event.message.chat.id if event.message else None

        if chat_id is None:
            return await handler(event, data)

        if chat_id not in self.admins:
            maintenance_msg = (
                "⛔️ Сейчас ведутся технические доработки.\n"
                f"Если что — пишите {self.maintenance_contact}"
            )
            if isinstance(event, types.CallbackQuery) and event.message:
                await event.message.answer(maintenance_msg)
                await event.answer()
            elif isinstance(event, types.Message):
                await event.answer(maintenance_msg)
            return

        return await handler(event, data)


if not API_TOKEN:
    raise RuntimeError("API_TOKEN is not set. Add it to .env before running the bot.")

if not ADMIN_IDS:
    raise RuntimeError("ADMIN_IDS is empty. Add your Telegram ID to .env (ADMIN_IDS=123456789).")

if not SHOP_ID or not SHOP_API:
    logging.warning("SHOP_ID or SHOP_API is not configured. Payments will not work until values are set.")

# Инициализация бота
from aiogram.client.default import DefaultBotProperties

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
storage = MemoryStorage()
dp = Dispatcher()

admin_middleware = AdminOnlyMiddleware(ADMIN_IDS, MAINTENANCE_CONTACT, MAINTENANCE_MODE)
dp.message.middleware.register(admin_middleware)
dp.callback_query.middleware.register(admin_middleware)

# База данных и API
vpn_api = VPNApi()
database = VPNDatabase()
payment_service = PaymentService(SHOP_ID, SHOP_API, PAYMENT_RETURN_URL)
subscription_service = SubscriptionService(database, vpn_api)

async def simulate_activity():
    while True:
        try:
            test_chat_id = ADMIN_IDS[0]
            await bot.send_message(test_chat_id, "🔄 Авто-проверка бота...")

            try:
                users = database.get_all_users()
                
                if users:
                    file_path = DATA_DIR / "users_list.txt"
                    with open(file_path, "w", encoding="utf-8") as file:
                        file.write("📋 Список всех пользователей StormyVPN:\n\n")
                        for user in users:
                            file.write(f"🔹 ID: {user[0]}\n")
                            file.write(f"🔹 Username: {user[1]}\n")
                            file.write(f"🔹 Подписка до: {user[2]}\n")
                            file.write(f"🔹 Сервер: {user[6]}\n")
                            file.write(f"🔹 Inbound ID: {user[5]}\n")
                            file.write("-" * 30 + "\n")
                    doc = FSInputFile(file_path)
                    await bot.send_document(test_chat_id, doc, caption="📂 Список пользователей в файле")
                else:
                    await bot.send_message(test_chat_id, "❌ Нет зарегистрированных пользователей.")
                            
                await bot.send_message(test_chat_id, f"✅ Бот работает, пользователей: {len(users)}")
            except Exception as db_error:
                await bot.send_message(test_chat_id, f"❌ Ошибка работы бота: {db_error}")

        except Exception as e:
            logging.exception("⚠️ Ошибка в simulate_activity: %s", e)

        await asyncio.sleep(1800)

async def check_subscriptions():
    while True:
        now = datetime.now()
        users = database.get_all_users()

        for chat_id, username, expiry_date, reminder_sent, gift_used, _, _ in users:
            expiry_dt = datetime.strptime(expiry_date, "%d.%m.%Y %H:%M")
            time_left = (expiry_dt - now).total_seconds()

            if time_left <= 0:
                success = database.remove_user(chat_id)
                await bot.send_message(chat_id, "⏳ Ваша подписка на StormyVPN истекла. Продлите её, чтобы продолжить пользоваться услугами! 🔑")
                if not success:
                    print(f"⚠️ Не удалось удалить {chat_id} — будет повторено через 30 мин.")
                
            elif time_left < 86400 and not reminder_sent:
                await bot.send_message(chat_id, "⚠️ Ваша подписка скоро истекает! Продлите её, чтобы не потерять доступ к StormyVPN. 🚀")
                database.mark_reminder_sent(chat_id)

        await asyncio.sleep(1800)

async def get_user_subscription_status(chat_id):
    return database.get_subscription_status(chat_id)

async def create_payment(amount: float, chat_id: int, email: str):
    try:
        return payment_service.create_payment(amount, chat_id, email)
    except Exception as e:
        logging.exception("Ошибка создания платежа: %s", e)
        await notify_admin(f"⚠️ Ошибка создания платежа для {chat_id}: {e}")
        return None, None


async def activate_subscription(chat_id: int):
    success = await subscription_service.activate_or_extend(chat_id, bot)
    if success:
        await how_to_use_auto(chat_id)


async def sync_with_servers():
    """Периодическая синхронизация с 3x-ui: обновляет сроки, удаляет пропавшие inbound."""
    while True:
        users = database.get_all_users()
        deleted = 0
        updated = 0

        for user in users:
            chat_id, username, expiry_date, _, _, inbound_id, server_url = user
            server_data = vpn_api.get_inbound_data(inbound_id, server_url)

            if not server_data:
                database.remove_user_local(chat_id)
                deleted += 1
                continue

            server_expiry_timestamp = server_data.get("expiryTime")
            if not server_expiry_timestamp:
                database.remove_user_local(chat_id)
                deleted += 1
                continue

            server_expiry_date = datetime.fromtimestamp(server_expiry_timestamp / 1000)
            server_expiry_str = VPNUtils.format_expiry_date(server_expiry_date)

            if expiry_date != server_expiry_str:
                database.update_expiry_date(chat_id, server_expiry_str)
                updated += 1

        logging.info("Sync with 3x-ui: updated=%s, deleted=%s", updated, deleted)
        if deleted or updated:
            await notify_admin(f"🔄 Синхронизация 3x-ui: обновлено {updated}, удалено {deleted}.")
        await asyncio.sleep(1800)


async def handle_activation_with_retries(chat_id: int):
    """Пробует активировать/продлить до 3 раз с интервалом 60 сек."""
    max_attempts = 3
    delay_seconds = 60
    for attempt in range(1, max_attempts + 1):
        success = await subscription_service.activate_or_extend(chat_id, bot)
        if success:
            await how_to_use_auto(chat_id)
            return
        if attempt == 1:
            await bot.send_message(
                chat_id,
                "🔄 Оплата подтверждена, продлеваем доступ. Ключ обновится в течение 3 минут.",
            )
        if attempt < max_attempts:
            await asyncio.sleep(delay_seconds)
        else:
            # Последняя попытка не удалась — уведомляем админа
            admin_id = ADMIN_IDS[0]
            await bot.send_message(
                chat_id,
                "⚠️ Не удалось обновить доступ автоматически. Передали запрос администратору.",
            )
            await bot.send_message(
                admin_id,
                f"⚠️ Не удалось продлить/активировать для пользователя {chat_id} после оплаты. Проверь 3x-ui и базу.",
            )


async def check_payment_status():
    while True:
        pending_payments = database.get_pending_payments()

        for payment_id, chat_id in pending_payments:
            status = payment_service.get_payment_status(payment_id)
            if status is None:
                continue

            if status == "succeeded":
                database.update_payment_status(payment_id, "succeeded")
                asyncio.create_task(handle_activation_with_retries(chat_id))
                database.remove_payment(payment_id)

            elif status in ["canceled", "failed"]:
                database.update_payment_status(payment_id, status)
                database.remove_payment(payment_id)

        await asyncio.sleep(10)

async def how_to_use_auto(chat_id):
    await bot.send_message(
        chat_id,
        "📖 *Как настроить VPN?*\n\n"
        "Выберите вашу платформу ниже ⬇️\n"
        "Мы предоставим подробную инструкцию по установке и настройке StormyVPN.",
        parse_mode="Markdown",
        reply_markup=get_vpn_guide_keyboard()
    )
    













@dp.message(F.text == "/start")
async def start_message(message: types.Message):
    chat_id = message.chat.id
    
    welcome_text = """
    Привет! ✌️ Спасибо, что выбрал StormyVPN — надежного партнера для твоей безопасности и анонимности в интернете. 🚀

    <b>Почему именно StormyVPN?</b>
    
    <b>⚡ Молниеносная скорость</b>: забудь о медленных соединениях и прерываниях! StormyVPN работает быстро, стабильно и без задержек.
    
    <b>🌍 Удобство использования</b>: наш сервис прост в настройке и интуитивно понятен. Мгновенно подключайся и наслаждайся безопасным интернетом.
    
    <b>🔑 Надежность и анонимность</b>: StormyVPN не просто защищает твою информацию — мы гарантируем полную анонимность и отсутствие слежки.
    
    <b>📈 Регулярные обновления и улучшения</b>: мы постоянно работаем над улучшением сервиса, чтобы ты всегда получал лучший опыт.
    """

    photo = FSInputFile(IMAGES_DIR / "preview.jpg")
    status = database.get_subscription_status(chat_id)
    reply_kb = get_main_keyboard(status, chat_id in ADMIN_IDS)
    await bot.send_photo(chat_id, photo, caption=welcome_text, reply_markup=reply_kb)
    
@dp.message(F.text.in_(["Оформить VPN 💳", "Продлить VPN 🔑"]))
async def ask_for_email(message: types.Message, state: FSMContext):
    await message.answer("📩 По 54-ФЗ мы обязаны отправить вам чек. Пожалуйста, введите вашу почту для получения квитанции. ✉️\n\n❌ Или напишите Отмена для выхода в Главное меню")
    await state.set_state(EmailState.waiting_for_email)
    #await message.answer("Приносим свои извинения, в данный момент продлить или оформить подписку невозможно - идут технические работы")


@dp.message(EmailState.waiting_for_email)
async def process_email(message: types.Message, state: FSMContext):
    email = message.text.strip()
    
    if email.lower() == "отмена":
        await state.clear()
        status = database.get_subscription_status(message.chat.id)
        reply_kb = get_main_keyboard(status, message.chat.id in ADMIN_IDS)
        await message.answer("❌ Ввод email отменён.", reply_markup=reply_kb)
        return
    
    if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
        await message.answer("🚫 Неверный формат email. Попробуйте ещё раз.")
        return
    
    await state.clear()

    amount = 149
    payment_id, payment_link = await create_payment(amount, message.chat.id, email)
    if not payment_id or not payment_link:
        return await message.answer("❌ Не удалось создать платеж. Попробуйте позже или свяжитесь с поддержкой.")
    database.add_payment(message.chat.id, payment_id, amount)
    
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить (149 руб)", url=payment_link)]
    ])

    await message.answer("✅ Почта сохранена!\n\n💳 Теперь вы можете оплатить подписку. После успешной оплаты чек будет отправлен на вашу почту.", reply_markup=markup)

    
@dp.message(F.text == "Как настроить VPN? 📖")
async def how_to_use(message):
    await how_to_use_auto(message.chat.id)
    
@dp.message(F.text == "Личный кабинет 👤")
async def user_profile(message: types.Message):
    chat_id = message.chat.id
    user_data = database.get_user(chat_id)

    if user_data:
        username, vless_key, expiry_date, _, _, _ = user_data

        await message.answer(
                f"*👤 Ваш личный кабинет*\n\n"
                f"🔑 *Ваш VLESS-ключ:*\n```\n{vless_key}\n```\n"
                f"⏳ *Действителен до:* {expiry_date}\n\n"
                f"🔄 *Продлите подписку, чтобы не потерять доступ!* 🚀",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard(
                database.get_subscription_status(chat_id), chat_id in ADMIN_IDS
            )
        )

    else:
        await message.answer("*❌ Вы еще не активировали VPN.*", parse_mode='Markdown')

        
@dp.message(F.text == "Администрирование ⚙️")
async def admin_panel(message):
    chat_id = message.chat.id
    if chat_id in ADMIN_IDS:
        await message.answer("Добро пожаловать в админ панель", reply_markup=get_admin_keyboard())
        
@dp.message(F.text == "Главное меню")
async def back_to_main_menu(message: types.Message):
    chat_id = message.chat.id
    status = database.get_subscription_status(chat_id)
    await message.answer(
        "Вы вернулись в главное меню 🏠",
        reply_markup=get_main_keyboard(status, chat_id in ADMIN_IDS),
    )

@dp.message(F.text == "Посмотреть всех пользователей")
async def show_all_users(message: types.Message):
    chat_id = message.chat.id
    if chat_id in ADMIN_IDS:
        users = database.get_all_users()
        if users:
            file_path = DATA_DIR / "users_list.txt"
            with open(file_path, "w", encoding="utf-8") as file:
                file.write("📋 Список всех пользователей StormyVPN:\n\n")
                for user in users:
                    file.write(f"🔹 ID: {user[0]}\n")
                    file.write(f"🔹 Username: {user[1]}\n")
                    file.write(f"🔹 Подписка до: {user[2]}\n")
                    file.write(f"🔹 Сервер: {user[6]}\n")
                    file.write(f"🔹 Inbound ID: {user[5]}\n")
                    file.write("-" * 30 + "\n")
            doc = FSInputFile(file_path)
            await bot.send_document(chat_id, doc, caption="📂 Список пользователей в файле")
        else:
            await message.answer("❌ Нет зарегистрированных пользователей.")
        
@dp.message(F.text == "Удалить пользователя по ID")
async def delete_user_by_id(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    if chat_id in ADMIN_IDS:
        await message.answer("📌 Введите ID пользователя, которого хотите удалить. Или отправьте 'Отмена'.")
        await state.set_state(AdminState.waiting_for_delete_user)
    else:
        await message.answer("🚫 У вас нет доступа.")

@dp.message(StateFilter(AdminState.waiting_for_delete_user))
async def process_delete_user(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    if message.text.lower() == "отмена":
        await message.answer("❌ Действие отменено.", reply_markup=get_admin_keyboard())
        await state.clear()
        return

    try:
        user_id = int(message.text)
        if database.remove_user(user_id):
            await message.answer(f"✅ Пользователь {user_id} удалён.", reply_markup=get_admin_keyboard())
        else:
            await message.answer("❌ Пользователь не найден.", reply_markup=get_admin_keyboard())
    except ValueError:
        await message.answer("🚫 Введите корректный числовой ID.", reply_markup=get_admin_keyboard())

    await state.clear()
        
@dp.message(F.text == "Добавить пользователя")
async def add_user(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    if chat_id in ADMIN_IDS:
        await message.answer("📌 Введите ID пользователя, которого хотите добавить. Или отправьте 'Отмена'.")
        await state.set_state(AdminState.waiting_for_user_id)

@dp.message(StateFilter(AdminState.waiting_for_user_id))
async def process_add_user_id(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    if message.text.lower() == "отмена":
        await message.answer("❌ Действие отменено.", reply_markup=get_admin_keyboard())
        await state.clear()
        return
    try:
        user_id = int(message.text)
        await state.update_data(user_id=user_id)
        await message.answer("✅ Теперь введите username пользователя. Или отправьте 'Отмена'.")
        await state.set_state(AdminState.waiting_for_username)
    except ValueError:
        await message.answer("🚫 Введите корректный числовой ID.", reply_markup=get_admin_keyboard())

@dp.message(StateFilter(AdminState.waiting_for_username))
async def process_add_user_username(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    if message.text.lower() == "отмена":
        await message.answer("❌ Действие отменено.", reply_markup=get_admin_keyboard())
        await state.clear()
        return

    data = await state.get_data()
    user_id = data.get("user_id")
    username = message.text.strip()

    email = VPNUtils.get_vpn_email(user_id)
    vpn_api.select_server()
    try:
        vless_key, inbound_id, server_url = vpn_api.buy_vpn(email, 0)
    except Exception as e:
        logging.exception("Ошибка выдачи ключа при ручном добавлении пользователя: %s", e)
        await message.answer("❌ Ошибка при получении VPN-ключа.", reply_markup=get_admin_keyboard())
        await state.clear()
        return

    if vless_key:
        expiry_date = VPNUtils.format_expiry_date(datetime.now() + timedelta(days=31))
        
        database.add_user(user_id, username, vless_key, expiry_date, inbound_id, server_url)
        await message.answer(f"✅ Пользователь {username} (ID: {user_id}) успешно добавлен!", reply_markup=get_admin_keyboard())
    else:
        await message.answer("❌ Ошибка при получении VPN-ключа.", reply_markup=get_admin_keyboard())

    await state.clear()

        
@dp.callback_query(F.data == "vpn_guide_android_windows")
async def guide_android_windows(call: types.CallbackQuery):
    chat_id = call.message.chat.id
    video = FSInputFile(VIDEOS_DIR / "vpn_guide_android_windows.mp4")
    
    await bot.send_video(chat_id, video, caption=
        "<b>📖 Как настроить VPN на Android и Windows?</b>\n\n"
        "1️⃣ <b>Скачайте и установите Hiddify:</b>\n"
        "   📱 Hiddify для Android (GooglePlay)\n"
        "   💻 Hiddify для Windows (Microsoft Store / GitHub) <b>Запускать приложение от имени Администратора</b>\n\n"
        "2️⃣ Откройте приложение и нажмите <b>Плюсик в верхнем правом углу</b>.\n"
        "3️⃣ Скопируйте VLESS ключ или сообщение и нажмите <b>Добавить из буфера обмена</b>.\n"
        "4️⃣ Нажмите <b>Подключиться</b> и дождитесь соединения.\n\n"
        "✅ Теперь ваш интернет защищен! 🚀\n\n\n"
        "⚠️ <b><u>ВАЖНО!</u></b> ⚠️\n"
        "🔹 Один VLESS-ключ <b>не рекомендуется</b> использовать на более чем <b>3 устройствах</b> одновременно.\n"
        "🔹 Превышение лимита может привести к нестабильной работе или блокировке ключа.\n\n"
        "🔥 <b>Используйте StormyVPN с умом и оставайтесь в безопасности!</b> 🛡️",
        parse_mode='HTML',
    )


@dp.callback_query(F.data == "vpn_guide_ios_mac")
async def guide_ios_mac(call: types.CallbackQuery):
    chat_id = call.message.chat.id
    video = FSInputFile(VIDEOS_DIR / "ios_mac_tutorial.mp4")

    await bot.send_video(chat_id, video, caption=
        "<b>📖 Как настроить VPN на iOS и macOS?</b>\n\n"
        "1️⃣ <b>Установите v2Box:</b>\n"
        "   🍏 v2Box для iOS (AppStore)\n"
        "   🖥️ v2Box для macOS (AppStore)\n\n"
        "2️⃣ Откройте приложение, снизу нажмите Configs и выберите:\n"
        "   <b>Import v2ray uri from clipboard</b>.\n"
        "3️⃣ Вставьте ваш <b>VLESS-ключ или сообщение</b>.\n"
        "4️⃣ Проведите по кнопке слева направо <b>Slide to Connect</b>.\n\n"
        "✅ Теперь ваш интернет защищен! 🚀\n\n\n"
        "⚠️ <b><u>ВАЖНО!</u></b> ⚠️\n"
        "🔹 Один VLESS-ключ <b>не рекомендуется</b> использовать на более чем <b>3 устройствах</b> одновременно.\n"
        "🔹 Превышение лимита может привести к нестабильной работе или блокировке ключа.\n\n"
        "🔥 <b>Используйте StormyVPN с умом и оставайтесь в безопасности!</b> 🛡️",
        parse_mode='HTML',
    )

    
@dp.message(F.text == "Написать сообщение всем пользователям")
async def send_message_to_all(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    if chat_id in ADMIN_IDS:
        await message.answer("✍️ Введите сообщение, которое нужно отправить всем пользователям.")
        await state.set_state("awaiting_broadcast_message")
    else:
        await message.answer("🚫 У вас нет доступа.")


@dp.message(StateFilter("awaiting_broadcast_message"))
async def process_broadcast_message(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    text = message.text.strip()

    if not text:
        await message.answer("⚠️ Сообщение не может быть пустым.")
        return

    users = database.get_all_users()
    sent_count = 0
    failed_count = 0

    for user in users:
        try:
            await bot.send_message(user[0], text)
            sent_count += 1
        except Exception:
            failed_count += 1

    await state.clear()

    await message.answer(f"✅ Сообщение отправлено {sent_count} пользователям.\n❌ Не удалось отправить {failed_count}.")


@dp.message(F.text == "Послать подарки 🎁")
async def ask_for_gift_days(message: types.Message, state: FSMContext):
    if message.chat.id not in ADMIN_IDS:
        return await message.answer("🚫 У вас нет доступа.")
    await message.answer("🎁 На сколько дней продлить подписку всем пользователям? Введите число.")
    await state.set_state(AdminState.awaiting_gift_days)


@dp.message(StateFilter(AdminState.awaiting_gift_days))
async def process_gift_days(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    try:
        days = int(message.text)
        if days <= 0:
            raise ValueError
    except ValueError:
        return await message.answer("🚫 Введите положительное число дней.")

    await state.clear()
    await message.answer(f"🎁 Продлеваем подписку всем на {days} дней... Это может занять пару минут.")
    asyncio.create_task(add_days_to_all_users(days, chat_id))


async def add_days_to_all_users(days: int, notify_chat: int):
    users = database.get_all_users()
    updated = 0
    failed = 0
    skipped = 0

    for user in users:
        chat_id, username, expiry_date, _, _, inbound_id, server_url = user
        server_data = vpn_api.get_inbound_data(inbound_id, server_url)

        if not server_data or "expiryTime" not in server_data:
            skipped += 1
            continue

        server_expiry_timestamp = server_data["expiryTime"]
        server_expiry_date = datetime.fromtimestamp(server_expiry_timestamp / 1000)
        new_expiry_date = server_expiry_date + timedelta(days=days)
        new_expiry_timestamp = int(new_expiry_date.timestamp() * 1000)

        try:
            is_renewed = vpn_api.renew_vpn(inbound_id, server_url, new_expiry_timestamp)
        except Exception as e:
            logging.exception("Ошибка продления при подарке для %s: %s", chat_id, e)
            is_renewed = False

        if is_renewed:
            new_expiry_str = new_expiry_date.strftime("%d.%m.%Y %H:%M")
            database.update_expiry_date(chat_id, new_expiry_str)  # сбрасывает reminder_sent в 0
            updated += 1
        else:
            failed += 1

    summary = (
        f"🎁 Подарок завершён.\n"
        f"✅ Продлено: {updated}\n"
        f"❌ Ошибок: {failed}\n"
        f"⏭️ Пропущено (нет inbound): {skipped}"
    )
    await bot.send_message(notify_chat, summary)
    await notify_admin(summary)
    

async def start_bot():
    asyncio.create_task(simulate_activity())
    if not MAINTENANCE_MODE:
        asyncio.create_task(check_payment_status())
        asyncio.create_task(check_subscriptions())
        asyncio.create_task(sync_with_servers())
    else:
        logging.info("MAINTENANCE_MODE enabled: skipping subscription/payment background tasks.")
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    import asyncio
    asyncio.new_event_loop().run_until_complete(start_bot())
