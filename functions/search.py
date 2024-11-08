import os
import sys
import requests
import requests
from bs4 import BeautifulSoup
from functions.openai_wrappers import summarize_text


BING_SEARCH_ENDPOINT = "https://api.bing.microsoft.com/v7.0/search"


def perform_internet_search(query, api_key, max_links=3):
    """
    Выполнение интернет-поиска с использованием Bing Search API и возвращение ссылок.
    """
    headers = {"Ocp-Apim-Subscription-Key": api_key}
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



def search_and_summarize(query, bing_api_key, openai_client, max_links=3):
    """
    Выполняет поиск в интернете по заданному запросу и суммаризирует найденные статьи.

    :param query: Поисковый запрос.
    :param bing_api_key: API-ключ для Bing Search API.
    :param openai_client: Клиент OpenAI, инициализированный с API-ключом.
    :param max_links: Максимальное количество ссылок для поиска и суммаризации.
    :return: Словарь с списком ссылок и суммарией найденных статей.
             {
                 "links": ["- [Название1](URL1)", "- [Название2](URL2)", ...],
                 "summary": "Краткое резюме всех статей."
             }
    """
    combined_text = ""
    links = perform_internet_search(query, bing_api_key, max_links)

    for idx, link in enumerate(links, start=1):
        try:
            # Извлечение URL из формата "- [Название](URL)"
            start = link.find('(') + 1
            end = link.find(')', start)
            url = link[start:end]

            # Запрос к странице
            page_response = requests.get(url, timeout=10)
            page_response.raise_for_status()

            # Парсинг HTML контента
            soup = BeautifulSoup(page_response.text, 'html.parser')

            # Извлечение основного текста статьи
            paragraphs = soup.find_all('p')
            text = ' '.join([para.get_text() for para in paragraphs])

            # Очистка текста от лишних пробелов и символов
            text = ' '.join(text.split())

            # Ограничение длины текста для суммаризации (например, 2000 символов на статью)
            if len(text) > 2000:
                text = text[:2000] + "..."

            # Добавление текста с разделителем
            combined_text += f"text_{idx}: {text}\n\n"

        except Exception as e:
            print(f"Ошибка при обработке ссылки {link}: {e}")
            combined_text += f"text_{idx}: Не удалось получить содержание статьи.\n\n"

    # Суммаризация объединенного текста
    summary = summarize_text(combined_text, openai_client)

    return {"links": links, "summary": summary}