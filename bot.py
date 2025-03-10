import os
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, Text
from aiogram.utils import executor
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Токен бота из .env
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Команда /start
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("Привет! Я готов к работе.")

# Обработка команды /settings
@dp.message(Command("settings"))
async def settings(message: Message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Изменить приоритет", callback_data="change_priority"))
    markup.add(InlineKeyboardButton("Настройки меню", callback_data="settings_menu"))
    await message.answer("Выберите настройку:", reply_markup=markup)

# Обработка callback запроса для изменения приоритета
@dp.callback_query(Text("change_priority"))
async def change_priority(callback: CallbackQuery):
    await callback.message.answer("Выберите приоритет (низкий, средний, высокий):")
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("Низкий", callback_data="priority_low"),
        InlineKeyboardButton("Средний", callback_data="priority_medium"),
        InlineKeyboardButton("Высокий", callback_data="priority_high")
    )
    await callback.message.answer("Выберите приоритет:", reply_markup=markup)

# Обработка выбора приоритета
@dp.callback_query(Text(lambda c: c.data.startswith("priority_")))
async def set_priority(callback: CallbackQuery):
    priority = callback.data.split("_")[1]
    await callback.message.answer(f"Выбран приоритет: {priority}")

# Обработка команд для настроек меню
@dp.callback_query(Text("settings_menu"))
async def settings_menu(callback: CallbackQuery):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Изменить название меню", callback_data="change_menu_name"))
    await callback.message.answer("Настройки меню:", reply_markup=markup)

# Обработка изменения названия меню
@dp.callback_query(Text("change_menu_name"))
async def change_menu_name(callback: CallbackQuery):
    await callback.message.answer("Введите новое название меню:")
    # Логика для изменения названия меню (можно добавить сохранение в базу данных или файл)

# Дополнительная логика для сообщений
@dp.message(Text())
async def echo(message: Message):
    # Эта логика может быть заменена на конкретную обработку
    await message.answer(f"Вы написали: {message.text}")

# Функция для получения статистики запросов
@dp.message(Command("metrics"))
async def metrics(message: Message):
    # Можете здесь подключить логику для отслеживания количества запросов
    await message.answer("Здесь будет отображаться статистика запросов.")

# Запуск бота
async def on_start():
    await dp.start_polling()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
