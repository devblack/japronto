# Router

The router is a subsystem responsible for directing incoming requests to
particular handlers based on some conditions, namely the URL path
and HTTP method. It's available under `router` property of an `Application`
instance and presents `add_router` method which takes `path` pattern, `handler`
and optionally one or more `method`s.


  ```python
  # examples/3_router/router.py
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
  # Values of the additional segments will be stored in side `request.match_dict`
  # dictionary with keys taken from {} placeholders. A request to `/params/1/2`
  # would leave `match_dict` set to `{'p1': 1, 'p2': '2'}`.
  @app.get('/params/{p1}/{p2}')
  def params(request):
      return request.Response(text=str(request.match_dict))

  app.run()
  ```

The source code for all the examples can be found in [examples directory](https://github.com/squeaky-pl/japronto/tree/master/examples).

**Next:** [Request object](4_request.md)
