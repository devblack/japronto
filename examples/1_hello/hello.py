from japronto import Application

# The Application instance is a fundamental concept.
# It is a parent to all the resources and all the settings
# can be tweaked there.
app = Application()

# Views handle logic, take request as a parameter and
# return the Response object back to the client

# Now a decorator method lets you register your handlers and execute
# them depending on the url path.
@app.get('/')
def hello(request):
    return request.Response(text='Hello world!')

# Finally, start our server and handle requests until termination is
# requested. Enabling debug lets you see request logs and stack traces.
app.run(debug=True)
