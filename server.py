import aiohttp
from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
import pymorphy2
from anyio import create_task_group

from main import process_article

routes = web.RouteTableDef()
dictionary = list(i.rstrip("\n") for i in open("negative_words.txt", "r"))

@routes.get('/')
async def analyze_article(request: Request) -> Response:
    urls = request.query.get('urls', [])
    split_urls = [url for url in urls.split(',')]

    if len(split_urls) > 10:
        raise web.HTTPBadRequest(text="too many urls in request, should be 10 or less")

    async with aiohttp.ClientSession() as session:
        morph = pymorphy2.MorphAnalyzer()
        result_box = []
        async with create_task_group() as tg:
            for article_url in split_urls:
                tg.start_soon(process_article, article_url, session, morph, dictionary, result_box)

    return web.json_response(result_box)


app = web.Application()
app.add_routes(routes)
web.run_app(app)