import aiohttp
from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
import pymorphy2
from anyio import create_task_group

from main import process_article

dictionary = list(i.rstrip("\n") for i in open("negative_words.txt", "r"))
morph = pymorphy2.MorphAnalyzer()

async def analyze_article(request: Request) -> Response:
    urls = request.query.get('urls', [])
    split_urls = [url for url in urls.split(',')]

    if len(split_urls) > 10:
        raise web.HTTPBadRequest(text="too many urls in request, should be 10 or less")

    async with aiohttp.ClientSession() as session:
        result_box = []
        async with create_task_group() as tg:
            for article_url in split_urls:
                tg.start_soon(process_article, article_url, session, morph, dictionary, result_box)

    return web.json_response(result_box)

if __name__ == '__main__':
    app = web.Application()
    app.add_routes([web.get('/', analyze_article)])
    web.run_app(app)
