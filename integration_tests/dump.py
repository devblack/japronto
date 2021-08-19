from base64 import b64encode
from asyncio import sleep as async_sleep
from japronto.app import Application

app = Application()

class ForcedException(Exception):
    pass

def HandleNoneMethod(request, exception):
    result = {
        "method": request.method,
        "path": request.path,
        "query_string": request.query_string,
        "headers": request.headers,
        "route": request.route and request.route.pattern,
        "exception": {
            "type": type(exception).__name__,
            "args": ", ".join(str(a) for a in exception.args)
        }
    }

    return request.Response(code=500, json=result)

@app.get('/dump/{p1}/{p2}')
@app.get('/dump1/{p1}/{p2}')
@app.get('/dump2/{p1}/{p2}')
@app.set_error_handler(ForcedException, HandleNoneMethod)
def dump(request):
    if 'Force-Raise' in request.headers:
        raise ForcedException(request.headers['Force-Raise'])

    body = request.body
    if body is not None:
        body = b64encode(body).decode('ascii')

    result = {
        "method": request.method,
        "path": request.path,
        "query_string": request.query_string,
        "headers": request.headers,
        "match_dict": request.match_dict,
        "body": body,
        "route": request.route and request.route.pattern
    }

    return request.Response(code=200, json=result)

@app.get('/async/dump/{p1}/{p2}')
@app.get('/async/dump1/{p1}/{p2}')
@app.get('/async/dump2/{p1}/{p2}')
async def adump(request):
    sleep = float(request.query.get('sleep', 0))
    await async_sleep(sleep)

    return await dump(request)

# sigsegv-crash-process when None class is assinged
# app.add_error_handler(None, dump)
# app.add_error_handler(ForcedException, HandleNoneMethod)

if __name__ == '__main__':
    app.run(debug=True)
