import aiohttp
from aiohttp import ClientError
import enum
import asyncio
import pymorphy2
import asyncio
from anyio import create_task_group

from text_tools import split_by_words, calculate_jaundice_rate
from adapters.inosmi_ru import sanitize
from utils import measure_time_manager, analyze_time

class ProcessingStatus(enum.Enum):
    OK = 'OK'
    FETCH_ERROR = 'FETCH_ERROR'
    PARSING_ERROR = 'PARSING_ERROR'
    TIMEOUT = 'TIMEOUT'

AVAILABLE_SITES = [
    'inosmi.ru'
]

TEST_ARTICLES = [
    "https://inosmi.ru/20241217/udobreniya-271197225.html",
    "https://inosmi.ru/20241216/gaz-271184773.html",
    "https://inosmi.ru/20241216/energoresursy-271181284.html",
    # "https://lenta.ru/20241216/dollar-271179864.html",
    # "/inosmi.ru/20241216/gaz-271174809.html",
    "https://inosmi.ru/economic/20190629/245384784.html"
]


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


async def process_article(url, session, morph, dictionary, result_box):
    for site in AVAILABLE_SITES:
        if site not in url:
            result_box.append(f"URL: {url}\n Рейтинг: {None}\n Слов в статье: {None}\n Статус: {ProcessingStatus.PARSING_ERROR}")
            return
    try:
        async with asyncio.timeout(1.5):
            html = await fetch(session, url)
    except asyncio.TimeoutError:
        result_box.append(f"URL: {url}\n Рейтинг: {None}\n Слов в статье: {None}\n Статус: {ProcessingStatus.TIMEOUT}")
        return
    except ClientError:
        result_box.append(f"URL: {url}\n Рейтинг: {None}\n Слов в статье: {None}\n Статус: {ProcessingStatus.FETCH_ERROR}")
        return
    
    text_without_tags = sanitize(html, plaintext=True)
    async with measure_time_manager(split_by_words) as f:
        try:
            async with asyncio.timeout(5):
                article_words = await f(morph, text_without_tags)
        except asyncio.TimeoutError:
            result_box.append(f"URL: {url}\n Рейтинг: {None}\n Слов в статье: {None}\n Статус: {ProcessingStatus.TIMEOUT}")

    jaundice_rate = calculate_jaundice_rate(article_words, dictionary)
    result_box.append(f"URL: {url}\n Рейтинг: {jaundice_rate}\n Слов в статье: {len(article_words)}\n Статус: {ProcessingStatus.OK}\n Время анализа: {analyze_time.get()}")


async def main():
    async with aiohttp.ClientSession() as session:
        morph = pymorphy2.MorphAnalyzer()
        dictionary = list(i.rstrip("\n") for i in open("negative_words.txt", "r"))
        result_box = []
        async with create_task_group() as tg:
            for article_url in TEST_ARTICLES:
                tg.start_soon(process_article, article_url, session, morph, dictionary, result_box)
        for result in result_box:
            print(result)


asyncio.run(main())
