import logging
import os
import re
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, ParseMode
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
    category = "другие"
    priority = "средний"

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

# Интерфейс для администраторов (просмотр запросов и фильтрация)
@dp.message_handler(commands=['admin'])
async def admin_interface(message: Message):
    admin_id = message.from_user.id
    if admin_id == YOUR_ADMIN_ID:  # Замените на ID администратора
        text = "Административный интерфейс:\n\n"
        for request in requests_log:
            text += (f"📄 {request['doc_type']} | 🆔 {request['party_id']} | 📧 {request['email']} | "
                     f"🗂 {request['category']} | ⚠️ {request['priority']} | 📅 {request['date']}\n"
                     f"{request['attached_file']}\n\n")
        await message.reply(text)
    else:
        await message.reply("У вас нет доступа к этому интерфейсу.")

# Функция для создания отчетов (по запросам с фильтрацией)
@dp.message_handler(commands=['report'])
async def generate_report(message: Message):
    admin_id = message.from_user.id
    if admin_id == YOUR_ADMIN_ID:  # Замените на ID администратора
        text = "Отчет по запросам:\n\n"
        
        # Фильтруем по категориям
        category_filter = message.text.split()[-1] if len(message.text.split()) > 1 else None
        filtered_requests = [req for req in requests_log if (category_filter and req['category'] == category_filter) or not category_filter]
        
        for req in filtered_requests:
            text += (f"📄 {req['doc_type']} | 🆔 {req['party_id']} | 📧 {req['email']} | "
                     f"🗂 {req['category']} | ⚠️ {req['priority']} | 📅 {req['date']}\n"
                     f"{req['attached_file']}\n\n")
        await message.reply(text)
    else:
        await message.reply("У вас нет доступа к этому отчету.")

# Запуск бота
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
