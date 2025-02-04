import asyncio
from japronto import Application

app = Application()

# This is a synchronous handler.
@app.get('/sync')
def synchronous(request):
    return request.Response(text='I am synchronous!')

# This is an asynchronous handler. It spends most of the time in the event loop.
# It wakes up every second 1 to print and finally returns after 3 seconds.
# This lets other handlers execute in the same processes while
# from the point of view of the client it took 3 seconds to complete.
@app.get('/async')
async def asynchronous(request):
    for i in range(1, 4):
        await asyncio.sleep(1)
        print(i, 'seconds elapsed')

    return request.Response(text='3 seconds elapsed')

app.run()
