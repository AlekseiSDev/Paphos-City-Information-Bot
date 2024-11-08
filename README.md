# Paphos City Information Bot

This bot provides information about Paphos city, including weather updates, search results, and more.

## Getting Started

Follow these instructions to set up and run the project on your local machine.

### Prerequisites

- [Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html)
- [Python](https://www.python.org/downloads/)

### Installation

1. **Create a Conda environment:**

    ```bash
    conda create --name paphos-bot python=3.11
    conda activate paphos-bot
    ```

2. **Install the required packages:**

    ```bash
    pip install -r requirements.txt
    ```

3. **Create a `.env` file in the root directory with the following content:**

    ```plaintext
    OPENAI_API_KEY=your_openai_api_key
    BING_API_KEY=your_bing_search_api_key
    WEATHER_API_KEY=your_weather_api_key
    TELEGRAM_TOKEN=your_telegram_bot_token
    ```

### Running the Bot

To run the bot, execute the following command:

```bash
python paphos_bot.py
```

### Usage
### Bot Commands

The bot supports the following commands:


- `/start` - Запустить бота.
- `/help` - Получить список доступных команд.
- `время` или `date` или `datetime` - Получить текущее системное время.
- `температура моря` или `температура воды` или `sea temperature` или `water temperature` - Узнать температуру воды в море.
- `температура воздуха` или `температура на улице` или `air temperature` или `temperature outside` - Узнать температуру воздуха.
- `news` или `новости` - Узнать сводку новостей о Пафосе, при повторном вызове получит более старые новости
- `выполни команду <команда>` или `execute <command>` - Выполнить разрешенную команду на сервере.


### Acknowledgments

- [OpenAI](https://www.openai.com/)
- [Bing Search API](https://www.microsoft.com/en-us/bing/apis/bing-search-api-v7)
- [OpenWeather](https://openweathermap.org/api)
- [Telegram Bot API](https://core.telegram.org/bots/api)
