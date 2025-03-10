import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from dotenv import load_dotenv

# Загрузка переменных из .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_INPUT_ID = os.getenv("GROUP_INPUT_ID")  # Группа, где пишут запросы
GROUP_OUTPUT_ID = os.getenv("GROUP_OUTPUT_ID")  # Группа, куда бот пересылает
YOUR_ADMIN_ID = os.getenv("YOUR_ADMIN_ID")  # ID администратора

# Настройка бота
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Хранение соответствия между запросами и пользователями
user_requests = {}

# Обработчик сообщений от пользователей
@dp.message_handler()
async def handle_user_message(message: Message):
    chat_id = message.chat.id
    text = message.text
    
    # Разбиваем сообщение по пробелам
    parts = text.split()
    if len(parts) < 4:
        await message.reply("Ошибка! Отправьте данные в формате: \nТип документа Party ID Email Дата", parse_mode="HTML")
        return
    
    doc_type, party_id, email, date = parts[0], parts[1], parts[2], " ".join(parts[3:])
    
    formatted_message = (f"🔹 Дополнительная верификация\n"
                         f"Клиент предоставил документы\n"
                         f"📄 Тип документа: {doc_type}\n"
                         f"🆔 Party ID: {party_id}\n"
                         f"📧 Email: {email}\n"
                         f"📅 Дата: {date}")
    
    # Создание кнопок для подтверждения
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Да", callback_data="yes"))
    keyboard.add(InlineKeyboardButton("Нет", callback_data="no"))
    keyboard.add(InlineKeyboardButton("Свой ответ", callback_data="custom"))

    # Отправка сообщения в группу OUTPUT с кнопками
    sent_message = await bot.send_message(GROUP_OUTPUT_ID, formatted_message, reply_markup=keyboard, parse_mode="HTML")
    user_requests[sent_message.message_id] = chat_id  # Связываем запрос с отправителем
    
    await message.reply("Запрос отправлен!", parse_mode="HTML")

# Обработчик ответов в группе OUTPUT (от админа)
@dp.message_handler()
async def handle_group_reply(message: Message):
    if message.reply_to_message and message.reply_to_message.message_id in user_requests:
        user_chat_id = user_requests[message.reply_to_message.message_id]
        await bot.send_message(user_chat_id, f"Ответ на ваш запрос:\n{message.text}", parse_mode="HTML")

# Обработчик callback кнопок (Да, Нет, Свой ответ)
@dp.callback_query_handler()
async def handle_callback(callback_query: types.CallbackQuery):
    user_chat_id = user_requests.get(callback_query.message.message_id)
    if user_chat_id:
        if callback_query.data == "yes":
            await bot.send_message(user_chat_id, "Вы подтвердили запрос.", parse_mode="HTML")
        elif callback_query.data == "no":
            await bot.send_message(user_chat_id, "Вы отклонили запрос.", parse_mode="HTML")
        elif callback_query.data == "custom":
            await bot.send_message(user_chat_id, "Пожалуйста, напишите свой ответ.", parse_mode="HTML")
        
        await callback_query.answer()

# Запуск бота
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
