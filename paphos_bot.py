import json
import os
import requests
import datetime
import subprocess
import shlex
import logging
from logging.handlers import RotatingFileHandler
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import telebot
import openai
from openai import OpenAI
from functions.news import fetch_latest_news
from functions.search import perform_internet_search, search_and_summarize
from utils import setup_logger, log_user_action

# Initialize the logger
load_dotenv()
logger = setup_logger()

BING_API_KEY = os.getenv('BING_API_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')

# Разрешенные системные команды
ALLOWED_COMMANDS = ['echo', 'date', 'uptime']  # Пример разрешенных команд
user_news_progress = {}

# Инициализация бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)

def load_data(file_path):
    """
    Загрузка данных из JSON файла.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Ошибка при загрузке {file_path}: {e}")
        return {}

def get_sea_water_temperature():
    """
    Получение текущей температуры морской воды в Пафосе с использованием OpenWeatherMap API.
    """
    try:
        # Координаты Пафоса, Кипр
        latitude = 34.7757
        longitude = 32.4243
        params = {
            'lat': latitude,
            'lon': longitude,
            'appid': WEATHER_API_KEY,
            'units': 'metric'
        }
        SEA_TEMPERATURE_API_URL = "https://api.openweathermap.org/data/2.5/weather"
        # https://api.openweathermap.org/data/2.5/weather?q=${city}&units=metric&appid={YOUR_API_KEY}
        response = requests.get(SEA_TEMPERATURE_API_URL, params=params)
        response.raise_for_status()
        weather_data = response.json()
        # Предполагается, что 'main.temp' предоставляет температуру морской воды; возможно, потребуется корректировка
        temperature = weather_data['main']['temp']
        return f"Текущая температура морской воды в Пафосе составляет {temperature}°C."
    except Exception as e:
        print(f"Ошибка при получении температуры морской воды: {e}")
        return "Не удалось получить температуру морской воды в данный момент."
    
def get_air_temperature():
    """
    Получение текущей температуры воздуха в Пафосе с использованием OpenWeatherMap API.
    """
    try:
        params = {
            'q': 'paphos',
            'appid': WEATHER_API_KEY,
            'units': 'metric'
        }
        SEA_TEMPERATURE_API_URL = "https://api.openweathermap.org/data/2.5/weather"
        response = requests.get(SEA_TEMPERATURE_API_URL, params=params)
        response.raise_for_status()
        weather_data = response.json()
        # Предполагается, что 'main.temp' предоставляет температуру морской воды; возможно, потребуется корректировка
        temperature = weather_data['main']['temp']
        return f"Текущая температура воздуха в Пафосе составляет {temperature}°C."
    except Exception as e:
        print(f"Ошибка при получении температуры воздуха: {e}")
        return "Не удалось получить температуру воздуха в данный момент."

def report_system_time():
    """
    Получение текущего системного времени.
    """
    current_time = datetime.datetime.now().strftime("%H:%M")
    return f"Текущее системное время: {current_time}."

def execute_allowed_command(command):
    """
    Выполнение системной команды, если она разрешена.
    """
    try:
        cmd_parts = shlex.split(command)
        cmd = cmd_parts[0]
        if cmd not in ALLOWED_COMMANDS:
            return "Эта команда не разрешена."
        result = subprocess.run(cmd_parts, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Ошибка при выполнении команды: {e}"
    except Exception as e:
        return f"Неожиданная ошибка: {e}"

def generate_response(user_input, data):
    """
    Генерация ответа с использованием OpenAI GPT.
    """
    try:
        openai.api_key = OPENAI_API_KEY
        prompt = f"""Ты — полезный ассистент с информацией о городе Пафос. Используй как свои общие знания, так и следующие данные для ответа пользователю.

Данные:
{json.dumps(data, ensure_ascii=False)}

Запрос пользователя: {user_input}

Ответ:"""

        response = openai.Completion.create(
            engine="gpt-4o-mini",
            prompt=prompt,
            max_tokens=500,
            n=1,
            stop=None,
            temperature=0.7,
        )
        return response.choices[0].text.strip()
    except Exception as e:
        print(f"Ошибка при генерации ответа: {e}")
        return "Извините, не удалось обработать ваш запрос в данный момент."

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "Добро пожаловать в Информационного Бота по городy Пафос!\n"
        "Вы можете задать мне вопросы о Пафосе, и я постараюсь помочь.\n"
        "Доступные команды:\n"
        "- 'время' или 'date': получить текущее системное время\n"
        "- 'температура моря' или 'sea temperature': получить температуру морской воды\n"
        "- 'температура воздуха' или 'air temperature': получить температуру воздуха\n"
        "- 'новости' или 'news': получить последние новости из Пафоса\n"
        "- 'найди [запрос]' или 'search [query]': выполнить поиск в интернете\n"
        "- 'найди и саммаризуй [запрос]' или 'search and summarize [query]': выполнить поиск и суммаризацию\n"
        "- 'выполни команду [команда]': выполнить разрешенную системную команду\n"
        "- 'exit': завершить беседу с ботом\n"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    user_input = message.text.strip().lower()
    log_user_action(logger, user_id, action_description=f"got user message: {user_input}")

    if user_input == 'exit':
        log_user_action(logger, user_id, action_description="handling user message: exit")
        bot.reply_to(message, "До свидания!")
        return

    elif 'время' in user_input or "date" in user_input or "datetime" in user_input:
        log_user_action(logger, user_id, action_description="handling user message: time")
        response = report_system_time()

    elif ('температура' in user_input and ('моря' in user_input or 'воды' in user_input)) \
        or ('temperature' in user_input and ('sea' in user_input or 'water' in user_input)):
        log_user_action(logger, user_id, action_description="handling user message: sea temperature")
        response = get_sea_water_temperature()

    elif ('температура' in user_input and ('воздуха' in user_input or 'улице' in user_input)) \
        or ('temperature' in user_input and ('air' in user_input or 'outside' in user_input)):
        log_user_action(logger, user_id, action_description="handling user message: air temperature")
        response = get_air_temperature()

    elif 'выполни команду' in user_input or 'execute' in user_input:
        log_user_action(logger, user_id, action_description="handling user message: execute command")
        command = user_input.replace('выполни команду', '').replace('execute', '').strip()
        response = execute_allowed_command(command)

    elif 'новости' in user_input or 'news' in user_input:
        print("User asked for news.")
        latest_news = fetch_latest_news(user_id=user_id, user_progress=user_news_progress)
        log_user_action(logger, user_id, action_description="handling user message: news")
        # print(f"Latest news: {latest_news}")
        response = "Вот последние новости из Пафоса:\n" + "\n".join(latest_news)

    elif "найди и саммаризуй" in user_input or "search and summarize" in user_input:
        log_user_action(logger, user_id, action_description="handling user message: search and summarize")
        text_for_search = user_input.replace('найди и саммаризуй', '').replace('search and summarize', '').strip()
        text_for_search = text_for_search if "Пафос" in text_for_search else text_for_search + " Пафос" 
        client = OpenAI()
        search_sum_results = search_and_summarize(text_for_search, BING_API_KEY, client)
        if search_sum_results:
            links = "\n".join(search_sum_results["links"])
            summary = search_sum_results["summary"]
            response = f"Вот краткое резюме найденных статей:\n{summary}\n\nВот некоторые полезные ссылки:\n{links}"
        else:
            response = "Не удалось найти информацию по вашему запросу."
    
    elif 'найди' in user_input or 'поищи' in user_input or 'search' in user_input:
        log_user_action(logger, user_id, action_description="handling user message: search")
        text_for_search = user_input.replace('найди', '').replace('поищи', '').replace('search', '').strip()
        text_for_search = text_for_search if "Пафос" in text_for_search else text_for_search + " Пафос" 
        search_links = perform_internet_search(text_for_search, BING_API_KEY)
        response = f"Вот некоторые полезные ссылки:\n" + "\n".join(search_links)

    else:
        log_user_action(logger, user_id, action_description="handling user message: general")
        # Общий запрос о Пафосе
        data = load_data('data.json')
        llm_response = generate_response(message.text, data)

        # Выполнение интернет-поиска
        search_links = perform_internet_search(message.text + " Пафос")

        # Составление окончательного ответа
        response = f"{llm_response}\n\nВот некоторые полезные ссылки:\n" + "\n".join(search_links) + \
                   "\n\nТакже последние новости из Пафоса:\n" + "\n".join(latest_news)

    log_user_action(logger, user_id, action_description="responding to user: " + response)
    bot.reply_to(message, response)



def main():
    print("Бот запущен и работает...")
    log_user_action(logger, user_id=None, action_description="Bot started and running.")
    bot.infinity_polling()

if __name__ == "__main__":
    main()
