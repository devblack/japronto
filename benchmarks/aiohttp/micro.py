from aiohttp import web
import asyncio
import uvloop


loop = uvloop.new_event_loop()
asyncio.set_event_loop(loop)

app = web.Application(loop=loop)

async def hello(request):
    return web.Response(text='Hello world!')

app.router.add_get('/', hello)

web.run_app(app, port=8080, access_log=None)
