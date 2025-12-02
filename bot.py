import asyncio
import logging
import re
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
from aiogram.types import FSInputFile
from aiogram import F
from database import VPNDatabase
from api_requests import VPNApi
from utils import VPNUtils
import yookassa
from yookassa import Payment

# Фильтры
class EmailState(StatesGroup):
    waiting_for_email = State()

class AdminState(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_username = State()
    waiting_for_delete_user = State()

# Настройки
API_TOKEN = '7699898778:AAHfXlIb3icpBWdvkp2bj1xiuOwclCOi4f0'
SHOP_ID = '1027002'
SHOP_API = 'live_OaReKuBimlN-nv0rbMnSRU1OObGG_2YBKKYleuumuYs'

# SHOP_ID = '1030087'
# SHOP_API = 'test_yDarg1adaYfIdnUiQz4Gbtoa5cQH2cjjrtws1EgZE4o'

admins_id = [1902290413]

yookassa.Configuration.account_id = SHOP_ID
yookassa.Configuration.secret_key = SHOP_API

# Инициализация бота
from aiogram.client.default import DefaultBotProperties

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
storage = MemoryStorage()
dp = Dispatcher()

# База данных и API
vpn_api = VPNApi()
database = VPNDatabase()

async def simulate_activity():
    while True:
        try:
            test_chat_id = admins_id[0]
            await bot.send_message(test_chat_id, "🔄 Авто-проверка бота...")

            try:
                users = database.get_all_users()
                
                if users:
                    file_path = "/tmp/users_list.txt"
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
                    await message.answer("❌ Нет зарегистрированных пользователей.")
                            
                await bot.send_message(test_chat_id, f"✅ Бот работает, пользователей: {len(users)}")
            except Exception as db_error:
                await bot.send_message(test_chat_id, f"❌ Ошибка работы бота: {db_error}")

        except Exception as e:
            print(f"⚠️ Ошибка в simulate_activity: {e}")

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

async def create_payment(amount, chat_id, email):
    payment = yookassa.Payment.create({
        "amount": {
            "value": str(amount),
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": f"https://t.me/StormyVPN_bot"
        },
        "capture": True,
        "description": f"Оплата VPN для {chat_id}",
        "metadata": {"chat_id": chat_id},
        "receipt": {
            "customer": {
                "email": email
            },
            "items": [
                {
                    "description": "Оплата VPN",
                    "quantity": 1,
                    "amount": {
                        "value": str(amount),
                        "currency": "RUB"
                    },
                    "vat_code": 1
                }
            ]
        }
    })
    return payment.id, payment.confirmation.confirmation_url


async def activate_subscription(chat_id):
    user_data = database.get_user(chat_id)
    now = datetime.now()
    chat = await bot.get_chat(chat_id)
    username = f"@{chat.username}" if chat.username else "Без username"

    if user_data:
        expiry_date = datetime.strptime(user_data[2], "%d.%m.%Y %H:%M")
        new_expiry_date = expiry_date + timedelta(days=30)
        new_expiry_str = new_expiry_date.strftime("%d.%m.%Y %H:%M")

        success = vpn_api.renew_vpn(user_data[4], user_data[5], int(new_expiry_date.timestamp() * 1000))

        if success:
            database.update_expiry_date(chat_id, new_expiry_str)
            await bot.send_message(
                chat_id,
                escape_markdown_v2(f"✅ Подписка продлена!\n⏳ Действительна до: {new_expiry_str}"),
                parse_mode="MarkdownV2"
            )
        else:
            await bot.send_message(
                chat_id,
                escape_markdown_v2("❌ Ошибка продления подписки. Свяжитесь с поддержкой.\n@hirakiri_shogun"),
                parse_mode="MarkdownV2"
            )
        return

    new_expiry_date = now + timedelta(days=30)
    new_expiry_str = new_expiry_date.strftime("%d.%m.%Y %H:%M")

    email = VPNUtils.get_vpn_email(chat_id)
    vpn_api.select_server()

    try:
        vless_key, inbound_id, server_url = vpn_api.buy_vpn(email, 0)
    except Exception as e:
        await bot.send_message(
            chat_id,
            escape_markdown_v2("❌ Ошибка при активации VPN. Обратитесь в поддержку.\n@hirakiri_shogun"),
            parse_mode="MarkdownV2"
        )
        return

    if vless_key:
        database.add_user(chat_id, username, vless_key, new_expiry_str, inbound_id, server_url)
        await bot.send_message(
            chat_id,
            f"✅ *Подписка активирована!*\n\n"
            f"🔑 *Ваш VLESS-ключ:*\n```\n{vless_key}\n```\n"
            f"⏳ *Действителен до:* {new_expiry_str}\n\n"
            "🔄 *Продлите подписку, чтобы не потерять доступ!* 🚀",
            parse_mode="Markdown",
            reply_markup=await get_main_keyboard(chat_id)
        )
        await how_to_use_auto(chat_id)
    else:
        await bot.send_message(
            chat_id,
            escape_markdown_v2("❌ Ошибка активации. Свяжитесь с поддержкой @hirakiri_shogun"),
            parse_mode="MarkdownV2"
        )


async def check_payment_status():
    while True:
        pending_payments = database.get_pending_payments()

        for payment_id, chat_id in pending_payments:
            payment = Payment.find_one(payment_id)
            if payment is None:
                continue

            if payment.status == 'succeeded':
                database.update_payment_status(payment_id, 'succeeded')
                await activate_subscription(chat_id)
                database.remove_payment(payment_id)

            elif payment.status in ['canceled', 'failed']:
                database.update_payment_status(payment_id, payment.status)
                database.remove_payment(payment_id)

        await asyncio.sleep(10)

async def how_to_use_auto(chat_id):
    await bot.send_message(
        chat_id,
        "📖 *Как настроить VPN?*\n\n"
        "Выберите вашу платформу ниже ⬇️\n"
        "Мы предоставим подробную инструкцию по установке и настройке StormyVPN.",
        parse_mode="Markdown",
        reply_markup=await get_vpn_guide_keyboard()
    )
    
import re

def escape_markdown_v2(text: str) -> str:
    """Экранирует специальные символы для Telegram MarkdownV2"""
    escape_chars = r'([_*\[\]()~`>#+\-=|{}.!])'
    return re.sub(escape_chars, r'\\\1', text)




































#-------------------------------------------------------------------------------------------------------------------------------------------
# Главное меню
async def get_main_keyboard(chat_id):
    status = database.get_subscription_status(chat_id)
    buttons = [
        [KeyboardButton(text="Продлить VPN 🔑") if status == "active" else KeyboardButton(text="Оформить VPN 💳")],
        [KeyboardButton(text="Личный кабинет 👤")],
        [KeyboardButton(text="Как настроить VPN? 📖")]
    ]
    if chat_id in admins_id:
        buttons.append([KeyboardButton(text="Администрирование ⚙️")])
    
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


async def get_vpn_guide_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Android / Windows", callback_data="vpn_guide_android_windows")],
        [InlineKeyboardButton(text="🍏 iOS / macOS", callback_data="vpn_guide_ios_mac")]
    ])


# ----- Админ панель -----
async def get_admin_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Посмотреть всех пользователей")],
        [KeyboardButton(text="Удалить пользователя по ID")],
        [KeyboardButton(text="Добавить пользователя")],
        [KeyboardButton(text="Написать сообщение всем пользователям")],
        [KeyboardButton(text="Послать подарки 🎁")], 
        [KeyboardButton(text="Синхронизировать базу данных 🔄")],
        # [KeyboardButton(text="Восстановить пользователей 55555")],  # Новая кнопка
        # [KeyboardButton(text="Восстановить пользователей 5278")],
        # [KeyboardButton(text="Очистить всю базу данных")],
        [KeyboardButton(text="Главное меню")]
    ], resize_keyboard=True)


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

    photo = FSInputFile("preview.jpg")
    await bot.send_photo(chat_id, photo, caption=welcome_text, reply_markup=await get_main_keyboard(chat_id))
    
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
        await message.answer("❌ Ввод email отменён.", reply_markup=await get_main_keyboard(message.chat.id))
        return
    
    if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
        await message.answer("🚫 Неверный формат email. Попробуйте ещё раз.")
        return
    
    await state.clear()

    amount = 149
    payment_id, payment_link = await create_payment(amount, message.chat.id, email)
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
            reply_markup=await get_main_keyboard(chat_id)
        )

    else:
        await message.answer("*❌ Вы еще не активировали VPN.*", parse_mode='Markdown')

        
@dp.message(F.text == "Администрирование ⚙️")
async def admin_panel(message):
    chat_id = message.chat.id
    if chat_id in admins_id:
        await message.answer("Добро пожаловать в админ панель", reply_markup=await get_admin_keyboard())
        
@dp.message(F.text == "Главное меню")
async def back_to_main_menu(message: types.Message):
    chat_id = message.chat.id
    await message.answer("Вы вернулись в главное меню 🏠", reply_markup=await get_main_keyboard(chat_id))

@dp.message(F.text == "Посмотреть всех пользователей")
async def show_all_users(message: types.Message):
    chat_id = message.chat.id
    if chat_id in admins_id:
        users = database.get_all_users()
        if users:
            file_path = "/tmp/users_list.txt"
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
    if chat_id in admins_id:
        await message.answer("📌 Введите ID пользователя, которого хотите удалить. Или отправьте 'Отмена'.")
        await state.set_state(AdminState.waiting_for_delete_user)
    else:
        await message.answer("🚫 У вас нет доступа.")

@dp.message(StateFilter(AdminState.waiting_for_delete_user))
async def process_delete_user(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    if message.text.lower() == "отмена":
        await message.answer("❌ Действие отменено.", reply_markup=await get_admin_keyboard())
        await state.clear()
        return

    try:
        user_id = int(message.text)
        if database.remove_user(user_id):
            await message.answer(f"✅ Пользователь {user_id} удалён.", reply_markup=await get_admin_keyboard())
        else:
            await message.answer("❌ Пользователь не найден.", reply_markup=await get_admin_keyboard())
    except ValueError:
        await message.answer("🚫 Введите корректный числовой ID.", reply_markup=await get_admin_keyboard())

    await state.clear()
        
@dp.message(F.text == "Добавить пользователя")
async def add_user(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    if chat_id in admins_id:
        await message.answer("📌 Введите ID пользователя, которого хотите добавить. Или отправьте 'Отмена'.")
        await state.set_state(AdminState.waiting_for_user_id)

@dp.message(StateFilter(AdminState.waiting_for_user_id))
async def process_add_user_id(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    if message.text.lower() == "отмена":
        await message.answer("❌ Действие отменено.", reply_markup=await get_admin_keyboard())
        await state.clear()
        return
    try:
        user_id = int(message.text)
        await state.update_data(user_id=user_id)
        await message.answer("✅ Теперь введите username пользователя. Или отправьте 'Отмена'.")
        await state.set_state(AdminState.waiting_for_username)
    except ValueError:
        await message.answer("🚫 Введите корректный числовой ID.", reply_markup=await get_admin_keyboard())

@dp.message(StateFilter(AdminState.waiting_for_username))
async def process_add_user_username(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    if message.text.lower() == "отмена":
        await message.answer("❌ Действие отменено.", reply_markup=await get_admin_keyboard())
        await state.clear()
        return

    data = await state.get_data()
    user_id = data.get("user_id")
    username = message.text.strip()

    email = VPNUtils.get_vpn_email(user_id)
    vpn_api.select_server()
    vless_key, inbound_id, server_url = vpn_api.buy_vpn(email, 0)

    if vless_key:
        expiry_date = VPNUtils.format_expiry_date(datetime.now() + timedelta(days=365))
        
        database.add_user(user_id, username, vless_key, expiry_date, inbound_id, server_url)
        await message.answer(f"✅ Пользователь {username} (ID: {user_id}) успешно добавлен!", reply_markup=await get_admin_keyboard())
    else:
        await message.answer("❌ Ошибка при получении VPN-ключа.", reply_markup=await get_admin_keyboard())

    await state.clear()

        
@dp.callback_query(F.data == "vpn_guide_android_windows")
async def guide_android_windows(call: types.CallbackQuery):
    chat_id = call.message.chat.id
    video = FSInputFile("vpn_guide_android_windows.mp4")
    
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
    video = FSInputFile("ios_mac_tutorial.mp4")

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
    if chat_id in admins_id:
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
    chat_id = message.chat.id
    if chat_id in admins_id:
        await message.answer("🎁 На сколько дней продлить подписку всем пользователям? Введите число:")
        await state.set_state("awaiting_gift_days")
    else:
        await message.answer("🚫 У вас нет доступа.")

@dp.message(StateFilter("awaiting_gift_days"))
async def process_gift_days(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    if not message.text.isdigit():
        await message.answer("🚫 Введите число дней!")
        return

    days = int(message.text)
    await message.answer(f"🎁 Продлеваем подписку всем пользователям на {days} дней...")

    add_days_to_all_users(days)

    await message.answer(f"✅ Подписка успешно продлена всем на {days} дней!")
    await state.clear()


def add_days_to_all_users(days):
    users = database.get_all_users()  # Получаем всех пользователей

    for user in users:
        chat_id, username, expiry_date, _, _, inbound_id, server_url = user

        # 🔄 1. Получаем актуальные данные с сервера
        server_data = vpn_api.get_inbound_data(inbound_id, server_url)

        if not server_data or "expiryTime" not in server_data:
            print(f"❌ inbound_id {inbound_id} не найден на сервере {server_url} или нет `expiryTime`. Пропускаем {chat_id}.")
            continue  # Пропускаем пользователя, не удаляем!

        # 🔄 2. Обновляем БД, если серверные данные отличаются
        server_expiry_timestamp = server_data["expiryTime"]
        server_expiry_date = datetime.fromtimestamp(server_expiry_timestamp / 1000)
        server_expiry_str = VPNUtils.format_expiry_date(server_expiry_date)

        if expiry_date != server_expiry_str:
            print(f"🔄 Синхронизация: обновляем {chat_id}. Сервер: {server_expiry_str}, БД: {expiry_date}")
            database.update_expiry_date(chat_id, server_expiry_str)

        # 🔄 3. Продлеваем подписку на `days` дней
        new_expiry_date = server_expiry_date + timedelta(days=days)
        new_expiry_timestamp = int(new_expiry_date.timestamp() * 1000)

        print(inbound_id)
        print(server_url)
        print(new_expiry_timestamp)
        is_renewed = vpn_api.renew_vpn(inbound_id, server_url, new_expiry_timestamp)

        if is_renewed:
            new_expiry_str = new_expiry_date.strftime("%d.%m.%Y %H:%M")
            database.update_expiry_date(chat_id, new_expiry_str)
            print(f"✅ {username} (ID: {chat_id}) → подписка продлена до {new_expiry_str}")
        else:
            print(f"❌ Ошибка продления для {username} (ID: {chat_id}). БД НЕ ОБНОВЛЯЕМ.")
            
@dp.message(F.text == "Синхронизировать базу данных 🔄")
async def sync_database(message: types.Message):
    chat_id = message.chat.id
    if chat_id not in admins_id:
        return await message.answer("🚫 У вас нет доступа.")

    users = database.get_all_users()
    deleted_users = []
    synced_users = []

    for user in users:
        chat_id, username, expiry_date, _, _, inbound_id, server_url = user
        server_data = vpn_api.get_inbound_data(inbound_id, server_url)

        if not server_data:
            database.remove_user(chat_id)
            deleted_users.append(chat_id)
            continue

        server_expiry_timestamp = server_data.get("expiryTime")
        if not server_expiry_timestamp:
            database.remove_user(chat_id)
            deleted_users.append(chat_id)
            continue

        server_expiry_date = datetime.fromtimestamp(server_expiry_timestamp / 1000)
        server_expiry_str = VPNUtils.format_expiry_date(server_expiry_date)

        if expiry_date != server_expiry_str:
            database.update_expiry_date(chat_id, server_expiry_str)
            synced_users.append(chat_id)

    await message.answer(f"✅ Синхронизация завершена!\n🗑️ Удалено: {len(deleted_users)}\n🔄 Обновлено: {len(synced_users)}")


@dp.message(F.text == "Восстановить пользователей 55555")
async def restore_55555_users(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    if chat_id not in admins_id:
        return await message.answer("🚫 У вас нет доступа к этой команде.")

    await message.answer("🔄 Начинаю восстановление пользователей сервера 55555...")

    users_to_restore = [
        {"id": 196880451, "username": "@Assia_G"},
        {"id": 310694093, "username": "@Mariya_forev"},
        {"id": 397835983, "username": "@Nikolai_p40"},
        {"id": 533802354, "username": "@july_razumova"},
        {"id": 642454649, "username": "@Alexandr_S_K"},
        {"id": 693473103, "username": "@margarita_kuzz"},
        {"id": 801912621, "username": "@puddddding7"},
        {"id": 911348507, "username": "@Artemi_a_ne_artem"},
        {"id": 956526375, "username": "Без username"},
        {"id": 1040013169, "username": "@Kirill_Luzianin"},
        {"id": 1150730884, "username": "Без username"},
        {"id": 1350269200, "username": "@Suleimanova_Elvina"},
        {"id": 1439561399, "username": "Без username"},
        {"id": 1626378585, "username": "Без username"},
        {"id": 1681246178, "username": "@nastyvasy"},
        {"id": 1772395192, "username": "Без username"},
        {"id": 1815468502, "username": "@ShAlbina123"},
        {"id": 5129380769, "username": "Без username"},
        {"id": 5169289993, "username": "Без username"}
    ]

    restored_count = 0
    errors = []

    for user in users_to_restore:
        try:
            # Получаем данные пользователя
            user_id = user["id"]
            username = user["username"]
            
            # Используем встроенный метод активации подписки (как при оплате)
            email = VPNUtils.get_vpn_email(user_id)
            
            # Устанавливаем срок подписки (40 дней)
            expiry_date = datetime.now() + timedelta(days=40)
            expiry_str = expiry_date.strftime("%d.%m.%Y %H:%M")
            
            # Получаем chat объект для username
            try:
                chat = await bot.get_chat(user_id)
                username = f"@{chat.username}" if chat.username else username
            except:
                pass
            
            # Проверяем, есть ли уже пользователь
            if database.get_user(user_id):
                # Обновляем подписку
                database.update_expiry_date(user_id, expiry_str)
                await message.answer(f"♻️ Обновлен пользователь {username} (ID: {user_id})")
            else:
                # Активируем подписку (имитируем успешную оплату)
                await activate_subscription(user_id)
                await message.answer(f"✅ Добавлен пользователь {username} (ID: {user_id})")
            
            restored_count += 1
            
        except Exception as e:
            error_msg = f"❌ Ошибка при восстановлении {username} (ID: {user_id}): {str(e)}"
            errors.append(error_msg)
            print(error_msg)
    
    # Формируем итоговый отчет
    result_message = (
        f"🔚 Восстановление завершено!\n"
        f"✅ Успешно: {restored_count}\n"
        f"❌ Ошибок: {len(errors)}"
    )
    
    if errors:
        # Сохраняем ошибки в файл
        error_file = "/tmp/restore_errors.txt"
        with open(error_file, "w", encoding="utf-8") as f:
            f.write("\n".join(errors))
        
        # Отправляем файл с ошибками
        doc = FSInputFile(error_file)
        await message.answer_document(doc, caption=result_message)
    else:
        await message.answer(result_message)

@dp.message(F.text == "Восстановить пользователей 5278")
async def restore_55555_users(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    if chat_id not in admins_id:
        return await message.answer("🚫 У вас нет доступа к этой команде.")

    await message.answer("🔄 Начинаю восстановление пользователей сервера 55555...")

    users_to_restore = [
        {"id": 20732275, "username": "Без username"},
        {"id": 244408185, "username": "@mikhailgorbunoff"},
        {"id": 265196721, "username": "@Juliia_N"},
        {"id": 359319167, "username": "@ttnbgltsv"},
        {"id": 412792458, "username": "Без username"},
        {"id": 523614412, "username": "@anastasstepanenko"},
        {"id": 827776464, "username": "Без username"},
        {"id": 852063364, "username": "Без username"},
        {"id": 950866927, "username": "@Timofey1211"},
        {"id": 983360115, "username": "@OkiAniki"},
        {"id": 1044005195, "username": "@m_iiiig"},
        {"id": 1070585275, "username": "@hokkaido228"},
        {"id": 1285437127, "username": "@kvkk_k"},
        {"id": 1559034649, "username": "@murchik1984"},
        {"id": 1694692368, "username": "@DashaLuzyanina"},
        {"id": 6093611141, "username": "@mir_antenn_ek"}
    ]

    restored_count = 0
    errors = []

    for user in users_to_restore:
        try:
            # Получаем данные пользователя
            user_id = user["id"]
            username = user["username"]
            
            # Используем встроенный метод активации подписки (как при оплате)
            email = VPNUtils.get_vpn_email(user_id)
            
            # Устанавливаем срок подписки (40 дней)
            expiry_date = datetime.now() + timedelta(days=40)
            expiry_str = expiry_date.strftime("%d.%m.%Y %H:%M")
            
            # Получаем chat объект для username
            try:
                chat = await bot.get_chat(user_id)
                username = f"@{chat.username}" if chat.username else username
            except:
                pass
            
            # Проверяем, есть ли уже пользователь
            if database.get_user(user_id):
                # Обновляем подписку
                database.update_expiry_date(user_id, expiry_str)
                await message.answer(f"♻️ Обновлен пользователь {username} (ID: {user_id})")
            else:
                # Активируем подписку (имитируем успешную оплату)
                await activate_subscription(user_id)
                await message.answer(f"✅ Добавлен пользователь {username} (ID: {user_id})")
            
            restored_count += 1
            
        except Exception as e:
            error_msg = f"❌ Ошибка при восстановлении {username} (ID: {user_id}): {str(e)}"
            errors.append(error_msg)
            print(error_msg)
    
    # Формируем итоговый отчет
    result_message = (
        f"🔚 Восстановление завершено!\n"
        f"✅ Успешно: {restored_count}\n"
        f"❌ Ошибок: {len(errors)}"
    )
    
    if errors:
        # Сохраняем ошибки в файл
        error_file = "/tmp/restore_errors.txt"
        with open(error_file, "w", encoding="utf-8") as f:
            f.write("\n".join(errors))
        
        # Отправляем файл с ошибками
        doc = FSInputFile(error_file)
        await message.answer_document(doc, caption=result_message)
    else:
        await message.answer(result_message)

@dp.message(F.text == "Очистить всю базу данных")
async def clear_database(message: types.Message):
    chat_id = message.chat.id
    if chat_id not in admins_id:
        return await message.answer("🚫 У вас нет доступа к этой команде.")
    
    # Запрашиваем подтверждение
    confirm_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, очистить", callback_data="confirm_clear_db")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_clear_db")]
    ])
    
    await message.answer(
        "⚠️ Вы уверены, что хотите полностью очистить базу данных?\n"
        "Это действие невозможно отменить! Все пользователи будут удалены.",
        reply_markup=confirm_markup
    )

@dp.callback_query(F.data == "confirm_clear_db")
async def confirm_clear_db(callback: types.CallbackQuery):
    try:
        # Получаем текущее количество пользователей
        users_count = len(database.get_all_users())
        
        # Очищаем базу данных
        database.clear_all_users()
        
        await callback.message.edit_text(
            f"✅ База данных полностью очищена!\n"
            f"🗑 Удалено пользователей: {users_count}"
        )
        await callback.answer()
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка при очистке БД: {str(e)}")
        await callback.answer()

@dp.callback_query(F.data == "cancel_clear_db")
async def cancel_clear_db(callback: types.CallbackQuery):
    await callback.message.edit_text("❌ Очистка базы данных отменена")
    await callback.answer()

async def start_bot():
    asyncio.create_task(check_payment_status())
    asyncio.create_task(simulate_activity())
    asyncio.create_task(check_subscriptions())
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.new_event_loop().run_until_complete(start_bot())
