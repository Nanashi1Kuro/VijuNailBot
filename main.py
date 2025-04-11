import telebot
from telebot import types
import logging
import json
import os
from datetime import datetime

API_TOKEN = 'yoir token'

# Настройки бота
logging.basicConfig(level=logging.INFO)
bot = telebot.TeleBot(API_TOKEN)

# Путь к JSON файлу для сохранения данных
DATA_FILE = 'bot_responses.json'

# Инициализация файла данных, если он не существует
def init_data_file():
    if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False)

# Сохраняем ответ в JSON
def save_response(user_id, username, role, question, answer):
    try:
        # Проверяем существование файла
        if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
            # Если файл не существует или пуст, создаем пустой список
            data = []
        else:
            # Пробуем загрузить существующие данные
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if not isinstance(data, list):
                    data = []  # Если загружены не в формате списка, создаем новый
            except json.JSONDecodeError:
                # Если JSON некорректный
                data = []
        
        # Добавление нового ответа
        data.append({
            'user_id': str(user_id),
            'username': username or '',
            'role': role,
            'question': question,
            'answer': answer,
            'timestamp': datetime.now().isoformat()
        })
        
        # Сохранение обновленных данных
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        logging.error(f"Ошибка при сохранении в JSON: {e}")

# Кнопка для перезапуска бота
def get_restart_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("/start"))
    return keyboard

# Кнопки выбора роли
def get_role_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("💅 Клиент", callback_data="role_client"),
        types.InlineKeyboardButton("🔧 Мастер", callback_data="role_master")
    )
    return keyboard

# Кнопки для мастера
def get_master_start_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("Класс", callback_data="master_class"),
        types.InlineKeyboardButton("Не очень", callback_data="master_not_great"),
        types.InlineKeyboardButton("Неинтересно", callback_data="master_no_interest")
    )
    return keyboard

def get_master_paid_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("Да", callback_data="master_paid_yes"),
        types.InlineKeyboardButton("Нет", callback_data="master_paid_no")
    )
    return keyboard

def get_master_why_not_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("Не полезно", callback_data="master_useless"),
        types.InlineKeyboardButton("Не всё учитывает", callback_data="master_incomplete")
    )
    return keyboard

# Кнопки для клиента
def get_client_start_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("Класс", callback_data="client_class"),
        types.InlineKeyboardButton("Не очень", callback_data="client_not_great"),
        types.InlineKeyboardButton("Не понял идею", callback_data="client_dont_understand")
    )
    return keyboard

def get_client_usage_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("Да, если бесплатно", callback_data="client_free"),
        types.InlineKeyboardButton("Готов платить", callback_data="client_paid"),
        types.InlineKeyboardButton("Нет", callback_data="client_no")
    )
    return keyboard

# /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Привет! Кто вы по роли?", reply_markup=get_role_keyboard())

# --- Мастера ---
@bot.callback_query_handler(func=lambda call: call.data == 'role_master')
def master_intro(call):
    save_response(call.from_user.id, call.from_user.username, "Мастер", "Роль", "Мастер")
    try:
        with open('master_video.MOV', 'rb') as video_file:
            bot.send_video(call.from_user.id, video_file, caption="🎥 Видео о приложении для мастеров")
    except Exception as e:
        logging.error(f"Ошибка при отправке видео: {e}")
        bot.send_message(call.from_user.id, "🎥 [Видео о приложении для мастеров]")
    
    bot.send_message(call.from_user.id, "Как вам идея приложения?", reply_markup=get_master_start_keyboard())
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('master_'))
def master_logic(call):
    user_id = call.from_user.id
    username = call.from_user.username
    data = call.data
    mapping = {
        "master_class": ("Идея приложения", "Класс"),
        "master_not_great": ("Идея приложения", "Не очень"),
        "master_no_interest": ("Идея приложения", "Неинтересно"),
        "master_paid_yes": ("Платная версия", "Да"),
        "master_paid_no": ("Платная версия", "Нет"),
        "master_useless": ("Причина отказа", "Не полезно"),
        "master_incomplete": ("Причина отказа", "Не всё учитывает")
    }
    if data in mapping:
        q, a = mapping[data]
        save_response(user_id, username, "Мастер", q, a)
        # Логика переходов
        if data == "master_class":
            bot.send_message(user_id, "Пользовались бы платно?", reply_markup=get_master_paid_keyboard())
        elif data == "master_not_great":
            bot.send_message(user_id, "Что именно вам не понравилось в приложении?")
        elif data == "master_paid_yes":
            bot.send_message(user_id, "Спасибо за ваш ответ! Какую сумму вы готовы платить за пользование приложением?", reply_markup=get_restart_keyboard())
        elif data == "master_paid_no":
            bot.send_message(user_id, "Почему? Что добавить, чтобы пользовались?")
        elif data == "master_no_interest":
            bot.send_message(user_id, "Что именно вас не заинтересовало? Приложение не полезно или не всё учитывает?", reply_markup=get_master_why_not_keyboard())
        elif data in ["master_useless", "master_incomplete"]:
            bot.send_message(user_id, "Что вам было бы интереснее? Какие функции стоит добавить?", reply_markup=get_restart_keyboard())
    bot.answer_callback_query(call.id)

# --- Клиенты ---
@bot.callback_query_handler(func=lambda call: call.data == 'role_client')
def client_intro(call):
    save_response(call.from_user.id, call.from_user.username, "Клиент", "Роль", "Клиент")
    try:
        with open('client_video.MOV', 'rb') as video_file:
            bot.send_video(call.from_user.id, video_file, caption="🎥 Видео о приложении для клиентов")
    except Exception as e:
        logging.error(f"Ошибка при отправке видео: {e}")
        bot.send_message(call.from_user.id, "🎥 [Видео о приложении для клиентов]")
    
    bot.send_message(call.from_user.id, "Как вам идея приложения?", reply_markup=get_client_start_keyboard())
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('client_'))
def client_logic(call):
    user_id = call.from_user.id
    username = call.from_user.username
    data = call.data
    mapping = {
        "client_class": ("Идея приложения", "Класс"),
        "client_not_great": ("Идея приложения", "Не очень"),
        "client_dont_understand": ("Идея приложения", "Не понял идею"),
        "client_free": ("Готовность использовать", "Если бесплатно"),
        "client_paid": ("Готовность использовать", "Готов платить"),
        "client_no": ("Готовность использовать", "Нет")
    }
    if data in mapping:
        q, a = mapping[data]
        save_response(user_id, username, "Клиент", q, a)
        if data in ["client_class", "client_not_great"]:
            bot.send_message(user_id, "Пользовались бы таким приложением?", reply_markup=get_client_usage_keyboard())
        elif data == "client_dont_understand":
            bot.send_message(user_id, "Что именно было непонятно? Можете описать, как вы поняли основную идею приложения?", reply_markup=get_restart_keyboard())
        elif data == "client_free":
            bot.send_message(user_id, "Спасибо! Какие функции были бы вам особенно полезны?", reply_markup=get_restart_keyboard())
        elif data == "client_paid":
            bot.send_message(user_id, "Спасибо! Сколько вы готовы платить за такое приложение в месяц?", reply_markup=get_restart_keyboard())
        elif data == "client_no":
            bot.send_message(user_id, "Что нужно добавить, чтобы вам было интересно?", reply_markup=get_restart_keyboard())
    bot.answer_callback_query(call.id)

# Открытые ответы
@bot.message_handler(func=lambda message: True)
def collect_open_feedback(message):
    if message.text != "/start":
        save_response(message.from_user.id, message.from_user.username, "Открытый ответ", "Комментарий", message.text)
        bot.reply_to(message, "Спасибо за ваш ответ! 😊", reply_markup=get_restart_keyboard())

if __name__ == '__main__':
    init_data_file()  # Инициализация файла данных при запуске
    bot.polling(none_stop=True)
