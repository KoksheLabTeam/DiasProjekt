import asyncio
import logging
import sqlite3

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import (
    BotCommand,
    BotCommandScopeDefault,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен бота
TOKEN_BOT = "8175344328:AAE8nrjoDGDHARUmrXBuhfEP0jQOBNYO1Hg"
ADMIN_ID = 1193519748

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN_BOT)
dp = Dispatcher()

# Подключение к базе данных
conn = sqlite3.connect("taxi_orders.db")
cursor = conn.cursor()

# Создание таблицы заказов
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        full_name TEXT,
        phone TEXT,
        passengers INTEGER,
        trip_date TEXT,
        route TEXT
    )
"""
)
conn.commit()


# Команды бота
async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Начало работы"),
        BotCommand(
            command="order_kokshetau_omsk", description="Заказать такси Кокшетау - Омск"
        ),
        BotCommand(
            command="order_omsk_kokshetau", description="Заказать такси Омск - Кокшетау"
        ),
        BotCommand(command="cancel", description="Сбросить заказ"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())


# Клавиатура
buttons = [
    KeyboardButton(text="/order_kokshetau_omsk"),
    KeyboardButton(text="/order_omsk_kokshetau"),
    KeyboardButton(text="/cancel"),
]
kb = ReplyKeyboardMarkup(keyboard=[buttons], resize_keyboard=True)

# Состояние для хранения заказов
user_orders = {}


# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Добро пожаловать в службу заказа такси Кокшетау – Омск / Омск – Кокшетау!\nВыберите маршрут для заказа.",
        reply_markup=kb,
    )


# Функция для оформления заказа
async def start_order(message: types.Message, route: str):
    user_orders[message.from_user.id] = {"route": route}
    await message.answer("Введите ваше ФИО:")


@dp.message(Command("order_kokshetau_omsk"))
async def order_kokshetau_omsk(message: types.Message):
    await start_order(message, "Кокшетау - Омск")


@dp.message(Command("order_omsk_kokshetau"))
async def order_omsk_kokshetau(message: types.Message):
    await start_order(message, "Омск - Кокшетау")


@dp.message()
async def process_order(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_orders:
        order = user_orders[user_id]
        if "full_name" not in order:
            order["full_name"] = message.text
            await message.answer("Введите ваш номер телефона:")
        elif "phone" not in order:
            order["phone"] = message.text
            await message.answer("Введите количество пассажиров:")
        elif "passengers" not in order:
            if message.text.isdigit():
                order["passengers"] = int(message.text)
                await message.answer("Введите дату выезда (в формате ДД.ММ.ГГГГ):")
            else:
                await message.answer("Пожалуйста, введите число пассажиров цифрами.")
        elif "trip_date" not in order:
            order["trip_date"] = message.text
            cursor.execute(
                "INSERT INTO orders (user_id, full_name, phone, passengers, trip_date, route) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    user_id,
                    order["full_name"],
                    order["phone"],
                    order["passengers"],
                    order["trip_date"],
                    order["route"],
                ),
            )
            conn.commit()
            del user_orders[user_id]
            await message.answer(
                "Ваш заказ принят! Мы свяжемся с вами для подтверждения."
            )


async def main():
    await set_commands(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен.")
    finally:
        conn.close()
