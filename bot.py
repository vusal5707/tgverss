import logging
import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import F
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
dp = Dispatcher()

# Хранение соответствия между запросами и пользователями
user_requests = {}

# Переменные для настройки
request_count = 0
priority_settings = {}  # Словарь для хранения настроек приоритетов
menu_settings = {}  # Словарь для хранения настроек меню

# Обработчик сообщений от пользователей
async def handle_user_message(message: Message):
    global request_count
    chat_id = message.chat.id
    text = message.text
    
    # Разбиваем сообщение по пробелам
    parts = text.split()
    if len(parts) < 4:
        await message.reply("Ошибка! Отправьте данные в формате: \nТип документа Party ID Email Дата", parse_mode="HTML")
        return
    
    doc_type, party_id, email, date = parts[0], parts[1], parts[2], " ".join(parts[3:])
    
    # Создание кнопок для выбора приоритета
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton("Высокий", callback_data="priority_high"),
        InlineKeyboardButton("Средний", callback_data="priority_medium"),
        InlineKeyboardButton("Низкий", callback_data="priority_low")
    )
    
    # Формируем сообщение
    formatted_message = (f"🔹 Дополнительная верификация\n"
                         f"Клиент предоставил документы\n"
                         f"📄 Тип документа: {doc_type}\n"
                         f"🆔 Party ID: {party_id}\n"
                         f"📧 Email: {email}\n"
                         f"📅 Дата: {date}")
    
    # Отправка сообщения с кнопками для выбора приоритета
    sent_message = await bot.send_message(chat_id, formatted_message, reply_markup=keyboard, parse_mode="HTML")
    user_requests[sent_message.message_id] = chat_id  # Связываем запрос с отправителем
    
    # Увеличиваем счетчик запросов
    request_count += 1
    await message.reply(f"Запрос отправлен! Всего запросов: {request_count}", parse_mode="HTML")

# Обработчик выбора приоритета
async def handle_priority_choice(callback_query: types.CallbackQuery):
    user_chat_id = user_requests.get(callback_query.message.message_id)
    if user_chat_id:
        # Сохраняем приоритет
        if callback_query.data == "priority_high":
            priority = "Высокий"
        elif callback_query.data == "priority_medium":
            priority = "Средний"
        else:
            priority = "Низкий"
        
        # Отправляем сообщение пользователю о выбранном приоритете
        await bot.send_message(user_chat_id, f"Вы выбрали приоритет: {priority}", parse_mode="HTML")
        
        # Добавляем приоритет в сообщение для группы
        formatted_message_with_priority = f"{callback_query.message.text}\nПриоритет: {priority}"
        
        # Отправляем запрос в группу OUTPUT с приоритетом
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("Да", callback_data="yes"))
        keyboard.add(InlineKeyboardButton("Нет", callback_data="no"))
        keyboard.add(InlineKeyboardButton("Свой ответ", callback_data="custom"))
        
        await bot.send_message(GROUP_OUTPUT_ID, formatted_message_with_priority, reply_markup=keyboard, parse_mode="HTML")
        await callback_query.answer()

# Обработчик ответов в группе OUTPUT (от админа)
async def handle_group_reply(message: Message):
    if message.reply_to_message and message.reply_to_message.message_id in user_requests:
        user_chat_id = user_requests[message.reply_to_message.message_id]
        await bot.send_message(user_chat_id, f"Ответ на ваш запрос:\n{message.text}", parse_mode="HTML")

# Обработчик callback кнопок (Да, Нет, Свой ответ)
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

# Команда /settings для админа, где он может настроить данные
@dp.callback_query_handler(commands=['settings'])
async def settings_handler(callback_query: types.CallbackQuery):
    if callback_query.from_user.id == int(YOUR_ADMIN_ID):
        # Отправка меню с настройками
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("Настроить приоритеты", callback_data="set_priority"),
            InlineKeyboardButton("Настроить меню", callback_data="set_menu")
        )
        await bot.send_message(callback_query.from_user.id, "Выберите настройку:", reply_markup=keyboard)
    else:
        await bot.send_message(callback_query.from_user.id, "У вас нет прав на доступ к настройкам.", parse_mode="HTML")

# Настройка приоритетов запросов
@dp.callback_query_handler(lambda c: c.data == "set_priority")
async def set_priority(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id, "Введите приоритет для запроса (высокий, средний, низкий):")
    await callback_query.answer()

@dp.message_handler(lambda message: message.text in ["высокий", "средний", "низкий"])
async def set_priority_response(message: Message):
    priority = message.text
    priority_settings[message.chat.id] = priority
    await message.reply(f"Приоритет для ваших запросов установлен: {priority}", parse_mode="HTML")

# Настройка меню
@dp.callback_query_handler(lambda c: c.data == "set_menu")
async def set_menu(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id, "Введите текст для кнопки меню:")
    await callback_query.answer()

@dp.message_handler(lambda message: message.text)
async def set_menu_response(message: Message):
    menu_settings[message.chat.id] = message.text
    await message.reply(f"Меню изменено на: {message.text}", parse_mode="HTML")

# Регистрируем обработчики
dp.register_message_handler(handle_user_message, F.text)
dp.register_message_handler(handle_group_reply, F.reply_to_message & F.chat_id(GROUP_OUTPUT_ID))
dp.register_callback_query_handler(handle_callback)
dp.register_callback_query_handler(handle_priority_choice, lambda c: c.data in ["priority_high", "priority_medium", "priority_low"])

# Запуск бота
async def main():
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
