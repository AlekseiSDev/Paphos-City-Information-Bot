import json
import os
import requests
import feedparser
import datetime
import subprocess
import shlex

from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Constants for API keys
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
BING_API_KEY = os.getenv('BING_API_KEY')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')

# Constants for APIs
BING_SEARCH_ENDPOINT = "https://api.bing.microsoft.com/v7.0/search"
NEWS_RSS_FEED_URL = "https://www.paphosnews.com.cy/rss"  # Example RSS feed URL
SEA_TEMPERATURE_API_URL = "https://api.openweathermap.org/data/2.5/weather"

# Allowed system commands for execution
ALLOWED_COMMANDS = ['echo', 'date', 'uptime']  # Example commands

def load_data(file_path):
    """
    Load and return data from a JSON file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return {}

def initialize_openai():
    """
    Initialize the OpenAI API client.
    """
    import openai
    openai.api_key = OPENAI_API_KEY
    return openai

def perform_internet_search(query, max_links=3):
    """
    Perform an internet search using Bing Search API and return top links.
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
        print(f"Error during internet search: {e}")
        return ["No links found."]

def fetch_latest_news():
    """
    Fetch the latest news headlines from the RSS feed.
    """
    try:
        feed = feedparser.parse(NEWS_RSS_FEED_URL)
        headlines = []
        for entry in feed.entries[:3]:  # Get top 3 headlines
            headlines.append(f"- \"{entry.title}\"")
        return headlines
    except Exception as e:
        print(f"Error fetching news: {e}")
        return ["No news available at the moment."]

def get_sea_water_temperature():
    """
    Get the current sea water temperature in Paphos using OpenWeatherMap API.
    """
    try:
        # Coordinates for Paphos, Cyprus
        latitude = 34.7757
        longitude = 32.4243
        params = {
            'lat': latitude,
            'lon': longitude,
            'appid': WEATHER_API_KEY,
            'units': 'metric'
        }
        response = requests.get(SEA_TEMPERATURE_API_URL, params=params)
        response.raise_for_status()
        weather_data = response.json()
        # Assuming 'main.temp' gives the sea water temperature; adjust based on API
        temperature = weather_data['main']['temp']
        return f"The current sea water temperature in Paphos is {temperature}°C."
    except Exception as e:
        print(f"Error fetching sea water temperature: {e}")
        return "Unable to retrieve sea water temperature at the moment."

def report_system_time():
    """
    Report the current system time.
    """
    current_time = datetime.datetime.now().strftime("%H:%M")
    return f"The current system time is {current_time}."

def execute_allowed_command(command):
    """
    Execute a system command if it's in the allowed list.
    """
    try:
        cmd_parts = shlex.split(command)
        cmd = cmd_parts[0]
        if cmd not in ALLOWED_COMMANDS:
            return "This command is not allowed."
        result = subprocess.run(cmd_parts, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error executing command: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"

def generate_response(user_input, data, openai_client):
    """
    Generate a response by combining LLM output with data.json.
    """
    try:
        prompt = f"""You are a helpful assistant with knowledge about Paphos city. Use both your general knowledge and the following data to answer the user.

Data:
{json.dumps(data)}

User Query: {user_input}

Response:"""

        response = openai_client.Completion.create(
            engine="text-davinci-003",  # You can choose the appropriate model
            prompt=prompt,
            max_tokens=500,
            n=1,
            stop=None,
            temperature=0.7,
        )
        return response.choices[0].text.strip()
    except Exception as e:
        print(f"Error generating response: {e}")
        return "I'm sorry, I couldn't process your request at the moment."

def main():
    # Load data from data.json
    data = load_data('data.json')

    # Initialize OpenAI
    openai_client = initialize_openai()

    print("Welcome to the Paphos City Information Bot! Type 'exit' to quit.\n")

    while True:
        user_input = input("User: ").strip().lower()

        if user_input == 'exit':
            print("Bot: Goodbye!")
            break

        elif 'time' in user_input:
            response = report_system_time()

        elif 'sea water temperature' in user_input or 'sea temperature' in user_input:
            response = get_sea_water_temperature()

        elif any(keyword in user_input for keyword in ['command', 'execute']):
            # Example: User might ask to execute a command
            command = user_input.replace('execute', '').strip()
            response = execute_allowed_command(command)

        else:
            # General query about Paphos
            llm_response = generate_response(user_input, data, openai_client)

            # Perform internet search
            search_links = perform_internet_search(user_input + " Paphos")

            # Fetch latest news
            latest_news = fetch_latest_news()

            # Combine all parts
            response = f"{llm_response}\n\nHere are some links you might find helpful:\n" + "\n".join(search_links) + \
                       "\n\nAlso, here are the latest news from Paphos:\n" + "\n".join(latest_news)

        print(f"Bot: {response}\n")

if __name__ == "__main__":
    main()
