import feedparser
from datetime import datetime

def fetch_latest_news(user_id, user_progress, items_per_page=5):
    """
    Получение последних новостей из нескольких RSS-лент с пагинацией для каждого пользователя.

    :param user_id: Идентификатор пользователя Telegram.
    :param user_progress: Словарь, отслеживающий прогресс каждого пользователя.
    :param feeds: Список URL RSS-лент.
    :param items_per_page: Количество новостей, выдаваемых за один раз.
    :return: Список новостей для текущей страницы пользователя.
    """
    # Объединяем все новости из всех источников
    feeds = ["https://in-cyprus.philenews.com/category/local/feed/", "https://cyprus-mail.com/tag/paphos/feed"]
    all_entries = []
    for feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                # Парсим дату публикации
                if 'published_parsed' in entry:
                    published = datetime(*entry.published_parsed[:6])
                else:
                    published = datetime.now()
                all_entries.append({
                    'title': entry.title,
                    'link': entry.link,
                    # 'summary': entry.summary if 'summary' in entry else '',
                    'published': published
                })
        except Exception as e:
            print(f"Ошибка при загрузке RSS-ленты {feed_url}: {e}")

    # Сортируем все новости по дате публикации (от новых к старым)
    all_entries.sort(key=lambda x: x['published'], reverse=True)

    # Получаем текущий прогресс пользователя
    if user_id not in user_progress:
        user_progress[user_id] = 0

    start_index = user_progress[user_id]
    end_index = start_index + items_per_page
    paginated_entries = all_entries[start_index:end_index]

    # Обновляем прогресс пользователя
    user_progress[user_id] = end_index

    # Форматируем новости для вывода
    formatted_news = []
    for entry in paginated_entries:
        formatted_news.append(f"**{entry['title']}**\n[Читать далее]({entry['link']})\n") #\n{entry['summary']}

    if not formatted_news:
        return ["Больше новостей нет."]

    return formatted_news
