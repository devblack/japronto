from japronto import Application

app = Application()

# This is a body for reversed_agent property
def reversed_agent(request):
    return request.headers['User-Agent'][::-1]

# This is a body for host_startswith method
# Custom methods and properties always accept request
# object.
def host_startswith(request, prefix):
    return request.headers['Host'].startswith(prefix)

# This view accesses custom method host_startswith
# and a custom property reversed_agent. Both are registered later.
@app.route()
# Finally register the  custom property and method
# By default the names are taken from function names
# unelss you provide `name` keyword parameter.
@app.set_req_extension(reversed_agent, property=True)
def extended_hello(request):
    if not request.host_startswith('api.'):
        text = 'Hello ' + request.reversed_agent
    else:
        text = 'Hello stranger'

    return request.Response(text=text)

# This view registers a callback, such callbacks are executed after handler
# exits and the response is ready to be sent over the wire.
@app.get('/callback')
@app.set_req_extension(host_startswith)
def with_callback(request):
    def cb(r):
        print('Done!')

    request.add_done_callback(cb)
    return request.Response(text='cb')


# Also you can use the old method
#app.extend_request(some_method)

app.run()
