import json
import os
import requests
import feedparser
import datetime
import subprocess
import shlex

from bs4 import BeautifulSoup
from dotenv import load_dotenv
import telebot
import openai
from news import fetch_latest_news

# Загрузка переменных окружения из .env файла
load_dotenv()

# Получение ключей и токенов из переменных окружения
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
BING_API_KEY = os.getenv('BING_API_KEY')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')

# Константы для API
BING_SEARCH_ENDPOINT = "https://api.bing.microsoft.com/v7.0/search"

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

def perform_internet_search(query, max_links=3):
    """
    Выполнение интернет-поиска с использованием Bing Search API и возвращение ссылок.
    """
    headers = {"Ocp-Apim-Subscription-Key": BING_API_KEY}
    params = {"q": query, "textDecorations": True, "textFormat": "HTML", "count": max_links}
    try:
        response = requests.get(BING_SEARCH_ENDPOINT, headers=headers, params=params)
        response.raise_for_status()
        search_results = response.json()
        links = []
        for web_page in search_results.get("webPages", {}).get("value", []):
            links.append(f"- [{web_page.get('name')}]({web_page.get('url')})")
            if len(links) == max_links:
                break
        return links
    except Exception as e:
        print(f"Ошибка при поиске в интернете: {e}")
        return ["Ссылок не найдено."]

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
            engine="text-davinci-003",  # Можно выбрать другую модель, например, GPT-4, если доступно
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
        "- 'выполни команду [команда]': выполнить разрешенную системную команду\n"
        "- 'exit': завершить беседу с ботом\n"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    print(f"userID: {user_id}")
    user_input = message.text.strip().lower()
    print(f"User input: {user_input}")

    if user_input == 'exit':
        print("User requested to exit.")
        bot.reply_to(message, "До свидания!")
        return

    elif 'время' in user_input or "date" in user_input or "datetime" in user_input:
        print("User asked for system time.")
        response = report_system_time()

    elif ('температура' in user_input and ('моря' in user_input or 'воды' in user_input)) \
        or ('temperature' in user_input and ('sea' in user_input or 'water' in user_input)):
        print("User asked for sea water temperature.")
        response = get_sea_water_temperature()

    elif ('температура' in user_input and ('воздуха' in user_input or 'улице' in user_input)) \
        or ('temperature' in user_input and ('air' in user_input or 'outside' in user_input)):
        print("User asked for air temperature.")
        response = get_air_temperature()

    elif 'выполни команду' in user_input or 'execute' in user_input:
        print("User requested to execute a command.")
        command = user_input.replace('выполни команду', '').replace('execute', '').strip()
        response = execute_allowed_command(command)

    elif 'новости' in user_input or 'news' in user_input:
        print("User asked for news.")
        latest_news = fetch_latest_news(user_id=user_id, user_progress=user_news_progress)
        print(f"user_news_progress: {user_news_progress}")
        # print(f"Latest news: {latest_news}")
        response = "Вот последние новости из Пафоса:\n" + "\n".join(latest_news)

    else:
        print("else sectiont => user asked a general question.")
        # Общий запрос о Пафосе
        data = load_data('data.json')
        llm_response = generate_response(message.text, data)

        # Выполнение интернет-поиска
        search_links = perform_internet_search(message.text + " Пафос")

        # Составление окончательного ответа
        response = f"{llm_response}\n\nВот некоторые полезные ссылки:\n" + "\n".join(search_links) + \
                   "\n\nТакже последние новости из Пафоса:\n" + "\n".join(latest_news)

    bot.reply_to(message, response)

def main():
    print("Бот запущен и работает...")
    bot.infinity_polling()

if __name__ == "__main__":
    main()
