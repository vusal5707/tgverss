import logging
import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from dotenv import load_dotenv

# Загрузка переменных из .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_INPUT_ID = int(os.getenv("GROUP_INPUT_ID"))
GROUP_OUTPUT_ID = int(os.getenv("GROUP_OUTPUT_ID"))

# Настройка бота
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хранение соответствия между запросами и пользователями
user_requests = {}

# Обработчик сообщений от пользователей
@dp.message()
async def handle_user_message(message: Message):
    chat_id = message.chat.id
    text = message.text
    
    parts = text.split()
    if len(parts) < 4:
        await message.reply("Ошибка! Отправьте данные в формате: \nТип документа Party ID Email Дата")
        return
    
    doc_type, party_id, email, date = parts[0], parts[1], parts[2], " ".join(parts[3:])
    
    formatted_message = (f"🔹 Дополнительная верификация\n"
                         f"Клиент предоставил документы\n"
                         f"📄 Тип документа: {doc_type}\n"
                         f"🆔 Party ID: {party_id}\n"
                         f"📧 Email: {email}\n"
                         f"📅 Дата: {date}")
    
    sent_message = await bot.send_message(GROUP_OUTPUT_ID, formatted_message)
    user_requests[sent_message.message_id] = chat_id
    
    await message.reply("Запрос отправлен!")

# Запуск бота
async def main():
    logging.info("Бот запущен!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
