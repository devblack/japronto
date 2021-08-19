from japronto import Application

app = Application()

# Requests with the path set exactly to `/` and whatever method
# will be directed here.
@app.route('/')
def slash(request):
    return request.Response(text='Hello {} /!'.format(request.method))

# Requests with the path set exactly to '/love' and the method
# set exactly to `GET` will be directed here.
@app.get('/love')
def get_love(request):
    return request.Response(text='Got some love')

# Requests with the path set exactly to '/methods' and the method
# set to `POST` or `DELETE` will be directed here.
@app.route('/methods', methods=['POST', 'DELETE'])
def methods(request):
    return request.Response(text=request.method)

# Requests with the path starting with `/params/` segment and followed
# by two additional segments will be directed here.
# Values of the additional segments will be stored inside `request.match_dict`
# dictionary with keys taken from {} placeholders. A request to `/params/1/2`
# would leave `match_dict` set to `{'p1': 1, 'p2': '2'}`.
@app.get('/params/{p1}/{p2}')
def params(request):
    return request.Response(text=str(request.match_dict))

app.run()
