from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import sqlite3
import logging

API_TOKEN = '8175344328:AAE8nrjoDGDHARUmrXBuhfEP0jQOBNYO1Hg'
DATABASE_NAME = 'taxi_orders.db'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT,
            phone_number TEXT,
            from_city TEXT,
            to_city TEXT,
            status TEXT DEFAULT 'pending'
        )
    ''')
    conn.commit()
    conn.close()


def save_order(user_name, phone_number, from_city, to_city):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO orders (user_name, phone_number, from_city, to_city)
        VALUES (?, ?, ?, ?)
    ''', (user_name, phone_number, from_city, to_city))
    conn.commit()
    conn.close()


def city_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text='Омск → Кокшетау'))
    builder.add(KeyboardButton(text='Кокшетау → Омск'))
    return builder.as_markup(resize_keyboard=True)


class OrderStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()


@dp.message(Command('start'))
async def send_welcome(message: types.Message):
    await message.reply("Привет! Я бот для заказа такси между Омском и Кокшетау. Введите /order чтобы начать.")


@dp.message(Command('order'))
async def start_order(message: types.Message, state: FSMContext):
    await message.reply("Выберите направление:", reply_markup=city_keyboard())
    await state.set_state(OrderStates.waiting_for_name)


@dp.message(OrderStates.waiting_for_name)
async def process_direction(message: types.Message, state: FSMContext):
    direction = message.text
    if direction not in ['Омск → Кокшетау', 'Кокшетау → Омск']:
        await message.reply("Пожалуйста, выберите направление с помощью кнопок.")
        return

    await state.update_data(direction=direction)
    await message.reply("Введите ваше имя:")
    await state.set_state(OrderStates.waiting_for_phone)


@dp.message(OrderStates.waiting_for_phone)
async def process_name(message: types.Message, state: FSMContext):
    user_name = message.text
    await state.update_data(user_name=user_name)
    await message.reply(f"Приятно познакомиться, {user_name}! Введите ваш номер телефона:")


@dp.message(OrderStates.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    phone_number = message.text
    user_data = await state.get_data()
    user_name = user_data['user_name']
    direction = user_data['direction']
    from_city, to_city = direction.split(' → ')

    save_order(user_name, phone_number, from_city, to_city)

    await message.reply(
        f"Спасибо, {user_name}! Ваш заказ на такси {direction} принят. Мы свяжемся с вами по номеру {phone_number}.")

    await state.clear()


if __name__ == '_main_':
    logging.basicConfig(level=logging.INFO)

    init_db()  

    dp.run_polling(bot)
