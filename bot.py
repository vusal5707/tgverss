import logging
import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_INPUT_ID = int(os.getenv("GROUP_INPUT_ID"))  # Группа №1 (куда пишут пользователи)
GROUP_OUTPUT_ID = int(os.getenv("GROUP_OUTPUT_ID"))  # Группа №2 (куда бот отправляет)

# Настройка логов
logging.basicConfig(level=logging.INFO)

# Создаём экземпляры бота и диспетчера
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

# Хранение соответствия между запросами и пользователями
user_requests = {}


# Обработчик сообщений от пользователей (включая файлы)
@dp.message()
async def handle_user_message(message: Message):
    chat_id = message.chat.id
    text = message.caption if message.caption else message.text  # Если есть подпись к файлу, используем её

    # Проверяем, что сообщение не из группы №2
    if chat_id == GROUP_OUTPUT_ID:
        return

    if not text:
        await message.reply("Ошибка! Отправьте данные в формате:\n<b>Тип документа Party ID Email Дата</b>\n"
                            "Если прикрепляете файл, добавьте текст с данными в подпись.")
        return

    parts = text.split()
    if len(parts) < 4:
        await message.reply("Ошибка! Отправьте данные в формате:\n<b>Тип документа Party ID Email Дата</b>")
        return

    doc_type, party_id, email, date = parts[0], parts[1], parts[2], " ".join(parts[3:])
    
    formatted_message = (f"🔹 <b>Дополнительная верификация</b>\n"
                         f"Клиент предоставил документы:\n"
                         f"📄 <b>Тип документа:</b> {doc_type}\n"
                         f"🆔 <b>Party ID:</b> {party_id}\n"
                         f"📧 <b>Email:</b> {email}\n"
                         f"📅 <b>Дата:</b> {date}")

    # Кнопки для админов
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да", callback_data=f"approve_{message.message_id}")],
        [InlineKeyboardButton(text="❌ Нет", callback_data=f"reject_{message.message_id}")],
        [InlineKeyboardButton(text="✏️ Свой ответ", callback_data=f"custom_{message.message_id}")]
    ])

    sent_message = None

    # Проверяем, есть ли вложенный файл
    if message.document:
        sent_message = await bot.send_document(GROUP_OUTPUT_ID, message.document.file_id, caption=formatted_message, reply_markup=keyboard)
    elif message.photo:
        sent_message = await bot.send_photo(GROUP_OUTPUT_ID, message.photo[-1].file_id, caption=formatted_message, reply_markup=keyboard)
    elif message.video:
        sent_message = await bot.send_video(GROUP_OUTPUT_ID, message.video.file_id, caption=formatted_message, reply_markup=keyboard)
    else:
        sent_message = await bot.send_message(GROUP_OUTPUT_ID, formatted_message, reply_markup=keyboard)

    # Сохраняем связь между запросом и пользователем
    if sent_message:
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

    action, original_message_id = callback_data.split("_")
    original_message_id = int(original_message_id)

    if original_message_id not in user_requests:
        await callback.answer("Ошибка: запрос не найден!", show_alert=True)
        return

    user_chat_id = user_requests[original_message_id]

    if action == "approve":
        await bot.send_message(user_chat_id, "✅ <b>Ваш запрос одобрен!</b>")
        await callback.message.edit_text(callback.message.text + "\n\n✅ <b>Админ одобрил запрос.</b>", reply_markup=None)

    elif action == "reject":
        await bot.send_message(user_chat_id, "❌ <b>Ваш запрос отклонён.</b>")
        await callback.message.edit_text(callback.message.text + "\n\n❌ <b>Админ отклонил запрос.</b>", reply_markup=None)

    elif action == "custom":
        await bot.send_message(admin_id, "✏️ <b>Напишите свой ответ в этом чате.</b>")
        user_requests[admin_id] = user_chat_id  # Временное хранение связи

    await callback.answer()


# Обработчик сообщений от админа (для "Свой ответ")
@dp.message()
async def handle_admin_custom_reply(message: Message):
    admin_id = message.chat.id

    if admin_id in user_requests:
        user_chat_id = user_requests.pop(admin_id)
        await bot.send_message(user_chat_id, f"✉️ <b>Ответ от администратора:</b>\n{message.text}")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
