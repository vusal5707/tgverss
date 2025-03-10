import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text
from dotenv import load_dotenv
from datetime import datetime

# Загрузка переменных из .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_INPUT_ID = os.getenv("GROUP_INPUT_ID")  # Группа, где пишут запросы
GROUP_OUTPUT_ID = os.getenv("GROUP_OUTPUT_ID")  # Группа, куда бот пересылает

# Настройка бота
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Логирование запросов
requests_log = []

# Фильтрация запросов по категориям (пример категорий)
categories = ['финансовые', 'юридические', 'технические', 'другие']

# Приоритеты запросов
priorities = ['низкий', 'средний', 'высокий']

# Хранение соответствия между запросами и пользователями
user_requests = {}

# Админ ID (измените на реальный ID администратора)
YOUR_ADMIN_ID = 123456789

# Функция для создания клавиатуры администрирования
def admin_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Настроить категории", callback_data="edit_categories"))
    keyboard.add(InlineKeyboardButton("Настроить приоритеты", callback_data="edit_priorities"))
    keyboard.add(InlineKeyboardButton("Просмотреть запросы", callback_data="view_requests"))
    keyboard.add(InlineKeyboardButton("Создать отчет", callback_data="generate_report"))
    return keyboard

# Команда /admin
@dp.message_handler(commands=['admin'])
async def admin_interface(message: Message):
    admin_id = message.from_user.id
    if admin_id == YOUR_ADMIN_ID:  # Замените на ID администратора
        await message.reply("Добро пожаловать в панель администратора. Выберите опцию:", reply_markup=admin_keyboard())
    else:
        await message.reply("У вас нет доступа к этому интерфейсу.")

# Обработчик кнопок администрирования
@dp.callback_query_handler(lambda c: c.data.startswith('edit_'))
async def handle_admin_buttons(callback_query: types.CallbackQuery):
    admin_id = callback_query.from_user.id
    if admin_id == YOUR_ADMIN_ID:  # Проверка на администратора
        if callback_query.data == "edit_categories":
            await callback_query.message.reply("Введите новые категории (через запятую):")
        elif callback_query.data == "edit_priorities":
            await callback_query.message.reply("Введите новые приоритеты (через запятую):")
        elif callback_query.data == "view_requests":
            await view_requests(callback_query.message)
        elif callback_query.data == "generate_report":
            await generate_report(callback_query.message)
    else:
        await callback_query.answer("У вас нет доступа к этой функции.")

# Обработчик ввода новых категорий
@dp.message_handler(lambda message: message.text.startswith("Введите новые категории"))
async def handle_new_categories(message: Message):
    new_categories = message.text.replace("Введите новые категории", "").strip()
    global categories
    categories = new_categories.split(",")
    await message.reply(f"Категории обновлены: {', '.join(categories)}")

# Обработчик ввода новых приоритетов
@dp.message_handler(lambda message: message.text.startswith("Введите новые приоритеты"))
async def handle_new_priorities(message: Message):
    new_priorities = message.text.replace("Введите новые приоритеты", "").strip()
    global priorities
    priorities = new_priorities.split(",")
    await message.reply(f"Приоритеты обновлены: {', '.join(priorities)}")

# Просмотр запросов
async def view_requests(message: Message):
    text = "Запросы:\n\n"
    for req in requests_log:
        text += (f"📄 {req['doc_type']} | 🆔 {req['party_id']} | 📧 {req['email']} | "
                 f"🗂 {req['category']} | ⚠️ {req['priority']} | 📅 {req['date']}\n"
                 f"{req['attached_file']}\n\n")
    await message.reply(text)

# Генерация отчета
async def generate_report(message: Message):
    text = "Отчет по запросам:\n\n"
    for req in requests_log:
        text += (f"📄 {req['doc_type']} | 🆔 {req['party_id']} | 📧 {req['email']} | "
                 f"🗂 {req['category']} | ⚠️ {req['priority']} | 📅 {req['date']}\n"
                 f"{req['attached_file']}\n\n")
    await message.reply(text)

# Обработчик сообщений от пользователей
@dp.message_handler()
async def handle_user_message(message: Message):
    text = message.text
    chat_id = message.chat.id
    
    # Разбиваем сообщение по пробелам
    parts = text.split()
    if len(parts) < 4:
        await message.reply("Ошибка! Отправьте данные в формате: \nТип документа Party ID Email Дата Категория Приоритет (опционально)")
        return
    
    doc_type, party_id, email, date = parts[0], parts[1], parts[2], " ".join(parts[3:])
    
    # Запрос с прикрепленным файлом
    if message.document:
        file_info = await bot.get_file(message.document.file_id)
        file_url = f'https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}'
        attached_file = f'Файл: {file_url}'
    else:
        attached_file = "Файл не прикреплен."

    # Разбиваем дату на категории и приоритеты
    category = categories[0]  # Используем первую категорию по умолчанию
    priority = priorities[1]  # Средний приоритет по умолчанию

    # Сохраняем лог запроса
    request = {
        'doc_type': doc_type,
        'party_id': party_id,
        'email': email,
        'date': date,
        'category': category,
        'priority': priority,
        'attached_file': attached_file,
        'timestamp': datetime.now()
    }
    
    requests_log.append(request)

    # Форматируем сообщение для отправки в группу
    formatted_message = (f"🔹 Запрос от пользователя {chat_id}\n"
                         f"📄 Тип документа: {doc_type}\n"
                         f"🆔 Party ID: {party_id}\n"
                         f"📧 Email: {email}\n"
                         f"📅 Дата: {date}\n"
                         f"🗂 Категория: {category}\n"
                         f"⚠️ Приоритет: {priority}\n"
                         f"{attached_file}")

    # Отправляем запрос в группу
    sent_message = await bot.send_message(GROUP_OUTPUT_ID, formatted_message)
    user_requests[sent_message.message_id] = chat_id  # Связываем запрос с отправителем
    
    await message.reply("Запрос отправлен!")

# Запуск бота
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
