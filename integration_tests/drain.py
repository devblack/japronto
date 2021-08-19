from asyncio import sleep as async_sleep
from japronto.app import Application

app = Application()

@app.get('/')
def slash(request):
    return request.Response()

@app.get('/sleep/{sleep}')
async def sleep(request):
    await async_sleep(int(request.match_dict['sleep']))
    return request.Response(text="sleeping completed!")

if __name__ == '__main__':
    app.run()
