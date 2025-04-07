import os
import logging
import uuid
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from yookassa import Configuration, Payment
import asyncio
from dotenv import load_dotenv

# Загружаем переменные из .env, если запускается локально
load_dotenv()

# Настройки из переменных окружения
API_TOKEN = os.environ["API_TOKEN"]
CHANNEL_ID = int(os.environ["CHANNEL_ID"])
Configuration.account_id = os.environ["YUKASSA_ACCOUNT_ID"]
Configuration.secret_key = os.environ["YUKASSA_SECRET_KEY"]

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

# База пользователей с датами окончания подписки
user_subscriptions = {}

# Подписки
SUBSCRIPTIONS = {
    "1_month": {
        "title": "Подписка на 1 месяц",
        "price": 24900,
        "description": "1 месяц в aesthetic club — шаблоны, стикеры, идеи 💖",
        "duration_days": 30
    },
    "3_months": {
        "title": "Подписка на 3 месяца",
        "price": 64900,
        "description": "3 месяца — шаблоны, стикеры и эстетика + бонус 💝",
        "duration_days": 90
    },
    "12_months": {
        "title": "Подписка на 12 месяцев",
        "price": 229000,
        "description": "Годовой доступ ко всему 💎 материалы и бонусы в подарок",
        "duration_days": 365
    },
}

def main_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(
        KeyboardButton("🔐 Доступ в клуб"),
        KeyboardButton("📚 Купить материалы"),
        KeyboardButton("❤️‍🩹 Помощь"),
    )
    return keyboard

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.answer(
        "🌸 Привет! Я бот-помощник *eng_with_alice* ✨\n\n"
        "Добро пожаловать в заботливый клуб для преподавателей английского 💕\n\n"
        "✨ Здесь тебя ждут шаблоны, стикеры, находки и магия оформления\n\n"
        "Выбирай, что по душе:",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

@dp.message_handler(lambda message: message.text == "🔐 Доступ в клуб")
async def show_subscription_options(message: types.Message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🌸 1 месяц — 249₽", callback_data="sub_1_month"),
        types.InlineKeyboardButton("🎀 3 месяца — 649₽ + подарок", callback_data="sub_3_months"),
        types.InlineKeyboardButton("💎 12 месяцев — 2290₽ + материалы в подарок", callback_data="sub_12_months"),
    )
    await message.answer("Выбери тариф и присоединяйся 💌", reply_markup=markup)

@dp.message_handler(lambda message: message.text == "📚 Купить материалы")
async def show_materials_shop(message: types.Message):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("⭐️ Открыть каталог", url=os.environ.get("TELEGRAM_CHANNEL_URL", "https://t.me/engwithaliceshop"))
    )
    await message.answer(
        "✨ Здесь ты найдёшь каталог с авторскими шаблонами и стикерами для оформления уроков!\n"
        "Если что-то приглянулось — напиши Алисе прямо сюда: @alisa2003A 💌",
        reply_markup=markup
    )

@dp.message_handler(lambda message: message.text == "❤️‍🩹 Помощь")
async def show_help(message: types.Message):
    await message.answer(
        "🛟 Поддержка:\n\n"
        "Если возникли вопросы или что-то не работает — не стесняйся писать!\n"
        "Я помогу тебе быстро и с теплом 💖\n\n"
        "👉 [Написать в поддержку](https://t.me/alisa2003A)\n"
        "✉️ Или на почту: s1267076@gmail.com",
        parse_mode="Markdown"
    )

@dp.callback_query_handler(lambda c: c.data.startswith('sub_'))
async def process_subscription(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    subscription_key = callback_query.data.split("sub_")[1]
    subscription = SUBSCRIPTIONS[subscription_key]

    amount = subscription['price'] / 100
    description = subscription['description']

    payment = Payment.create({
        "amount": {
            "value": f"{amount:.2f}",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/eng_with_alice"
        },
        "capture": True,
        "description": description
    }, uuid.uuid4())

    expires_at = datetime.now() + timedelta(days=subscription['duration_days'])
    user_subscriptions[user_id] = {
        "expires_at": expires_at
    }

    await bot.send_message(
        user_id,
        f"🔗 [Нажми здесь, чтобы оплатить подписку]({payment.confirmation.confirmation_url})",
        parse_mode="Markdown"
    )

async def check_expired_subscriptions():
    while True:
        now = datetime.now()
        for user_id, data in list(user_subscriptions.items()):
            if now >= data["expires_at"]:
                try:
                    await bot.ban_chat_member(CHANNEL_ID, user_id)
                    await bot.unban_chat_member(CHANNEL_ID, user_id)
                    logging.info(f"Удалён пользователь {user_id} из канала")
                    del user_subscriptions[user_id]
                except Exception as e:
                    logging.error(f"Не удалось удалить пользователя {user_id}: {e}")
        await asyncio.sleep(86400)  # проверка раз в сутки

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(check_expired_subscriptions())
    executor.start_polling(dp, skip_updates=True)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(check_expired_subscriptions())
    executor.start_polling(dp, skip_updates=True)
