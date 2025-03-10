import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_INPUT_ID = int(os.getenv("GROUP_INPUT_ID"))  # Группа, где пишут запросы
GROUP_OUTPUT_ID = int(os.getenv("GROUP_OUTPUT_ID"))  # Группа, куда бот пересылает

# Настройка бота
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Хранение соответствия между запросами и пользователями
user_requests = {}


# Обработчик сообщений от пользователей
@dp.message()
async def handle_user_message(message: Message):
    chat_id = message.chat.id
    text = message.text

    # Проверяем, что сообщение не из группы №2
    if chat_id == GROUP_OUTPUT_ID:
        return

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

    # Кнопки для админов
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да", callback_data=f"approve_{message.message_id}")],
        [InlineKeyboardButton(text="❌ Нет", callback_data=f"reject_{message.message_id}")],
        [InlineKeyboardButton(text="✏️ Свой ответ", callback_data=f"custom_{message.message_id}")]
    ])

    sent_message = await bot.send_message(GROUP_OUTPUT_ID, formatted_message, reply_markup=keyboard)
    
    # Сохраняем связь между запросом и пользователем
    user_requests[sent_message.message_id] = chat_id

    await message.reply("Запрос отправлен!")


# Обработчик нажатий на кнопки
@dp.callback_query()
async def handle_callback(callback: CallbackQuery):
    callback_data = callback.data
    admin_id = callback.from_user.id
    chat_id = callback.message.chat.id

    # Проверяем, что кнопка нажата в группе №2
    if chat_id != GROUP_OUTPUT_ID:
        return

    # Получаем ID сообщения, на которое нажали
    action, original_message_id = callback_data.split("_")
    original_message_id = int(original_message_id)

    # Проверяем, связан ли этот запрос с пользователем
    if original_message_id not in user_requests:
        await callback.answer("Ошибка: запрос не найден!", show_alert=True)
        return

    user_chat_id = user_requests[original_message_id]

    if action == "approve":
        await bot.send_message(user_chat_id, "✅ Ваш запрос одобрен!")
        await callback.message.edit_text(callback.message.text + "\n\n✅ Админ одобрил запрос.", reply_markup=None)

    elif action == "reject":
        await bot.send_message(user_chat_id, "❌ Ваш запрос отклонён.")
        await callback.message.edit_text(callback.message.text + "\n\n❌ Админ отклонил запрос.", reply_markup=None)

    elif action == "custom":
        await bot.send_message(admin_id, "✏️ Напишите свой ответ в этом чате.")
        user_requests[admin_id] = user_chat_id  # Временное хранение связи

    await callback.answer()


# Обработчик сообщений от админа (для "Свой ответ")
@dp.message()
async def handle_admin_custom_reply(message: Message):
    admin_id = message.chat.id

    # Проверяем, писал ли этот админ кастомный ответ
    if admin_id in user_requests:
        user_chat_id = user_requests.pop(admin_id)  # Убираем из памяти после отправки
        await bot.send_message(user_chat_id, f"✉️ Ответ от администратора:\n{message.text}")

