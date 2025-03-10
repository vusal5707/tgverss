import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, CallbackQuery
from aiogram.utils import executor
from aiogram.dispatcher.filters import ReplyFilter
from dotenv import load_dotenv

# Загрузка переменных из .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_INPUT_ID = os.getenv("GROUP_INPUT_ID")  # Группа, где пишут запросы
GROUP_OUTPUT_ID = os.getenv("GROUP_OUTPUT_ID")  # Группа, куда бот пересылает

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
        await message.reply("Ошибка! Отправьте данные в формате: \nТип документа Party ID Email Дата")
        return
    
    doc_type, party_id, email, date = parts[0], parts[1], parts[2], " ".join(parts[3:])
    
    formatted_message = (f"🔹 Дополнительная верификация\n"
                         f"Клиент предоставил документы\n"
                         f"📄 Тип документа: {doc_type}\n"
                         f"🆔 Party ID: {party_id}\n"
                         f"📧 Email: {email}\n"
                         f"📅 Дата: {date}")
    
    # Отправляем сообщение в группу №2
    sent_message = await bot.send_message(GROUP_OUTPUT_ID, formatted_message)
    user_requests[sent_message.message_id] = chat_id  # Связываем запрос с отправителем
    
    # Создаем кнопки для ответа
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    approve_button = types.InlineKeyboardButton("Да", callback_data=f"approve_{sent_message.message_id}")
    reject_button = types.InlineKeyboardButton("Нет", callback_data=f"reject_{sent_message.message_id}")
    custom_button = types.InlineKeyboardButton("Свой ответ", callback_data=f"custom_{sent_message.message_id}")
    keyboard.add(approve_button, reject_button, custom_button)
    
    # Редактируем сообщение в группе №2, добавляем кнопки
    await bot.edit_message_text(formatted_message, chat_id=GROUP_OUTPUT_ID, message_id=sent_message.message_id, reply_markup=keyboard)
    
    await message.reply("Запрос отправлен!")

# Обработчик ответов в группе OUTPUT
@dp.message_handler(ReplyFilter(), chat_id=GROUP_OUTPUT_ID)
async def handle_group_reply(message: Message):
    if message.reply_to_message and message.reply_to_message.message_id in user_requests:
        user_chat_id = user_requests[message.reply_to_message.message_id]
        await bot.send_message(user_chat_id, f"Ответ на ваш запрос:\n{message.text}")

# Обработчик нажатий на кнопки (да, нет, свой ответ)
@dp.callback_query_handler(lambda c: c.data.startswith("approve") or c.data.startswith("reject") or c.data.startswith("custom"))
async def handle_callback(callback: CallbackQuery):
    action, message_id = callback.data.split("_", 1)
    message_id = int(message_id)  # Преобразуем id сообщения в число

    # Проверяем, что сообщение принадлежит группе OUTPUT
    if callback.message.chat.id != GROUP_OUTPUT_ID:
        return

    # Проверяем, есть ли запрос с таким message_id
    if message_id not in user_requests:
        await callback.answer("Ошибка: запрос не найден!", show_alert=True)
        return
    
    user_chat_id = user_requests[message_id]
    
    # Действия при нажатии кнопок
    if action == "approve":
        await bot.send_message(user_chat_id, "✅ <b>Ваш запрос одобрен!</b>")
        await callback.message.edit_text(callback.message.text + "\n\n✅ <b>Админ одобрил запрос.</b>", reply_markup=None)

    elif action == "reject":
        await bot.send_message(user_chat_id, "❌ <b>Ваш запрос отклонён.</b>")
        await callback.message.edit_text(callback.message.text + "\n\n❌ <b>Админ отклонил запрос.</b>", reply_markup=None)

    elif action == "custom":
        await bot.send_message(user_chat_id, "✏️ Напишите свой ответ в этом чате.")
        # Временно связываем админа с пользователем для ответа
        user_requests[callback.from_user.id] = user_chat_id

    await callback.answer()  # Подтверждаем нажатие кнопки

# Запуск бота
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
