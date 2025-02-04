# Response object

Handlers return Response instances to fulfill requests. They can contain status code, headers and almost always a body.
At the moment Response instances are immutable once created, this
restriction will be lifted in a next version.

  ```python
  # examples/5_response/response.py
  import random
  from http.cookies import SimpleCookie
  from japronto.app import Application

  app = Application()

  # Providing just text argument yields a `text/plain` response
  # encoded with `utf8` codec (charset set accordingly)
  @app.get('/text')
  def text(request):
      return request.Response(text='Hello world!')


  # You can override encoding by providing `encoding` attribute.
  @app.get('/encoding')
  def encoding(request):
      return request.Response(text='Já pronto!', encoding='iso-8859-1')


  # You can also set a custom MIME type.
  @app.get('/mime')
  def mime(request):
      return request.Response(
          mime_type="image/svg+xml",
          text="""
          <svg xmlns="http://www.w3.org/2000/svg" version="1.1">
              <line x1="10" y1="10" x2="80" y2="80" stroke="blue" />
          </svg>
          """)


  # Or serve binary data. `Content-Type` set to `application/octet-stream`
  # automatically but you can always provide your own `mime_type`.
  @app.get('/body')
  def body(request):
      return request.Response(body=b'\xde\xad\xbe\xef')


  # There exist a shortcut `json` argument. This automatically encodes the
  # provided object as JSON and servers it with `Content-Type` set to
  # `application/json; charset=utf8`
  @app.get('/json')
  def json(request):
      return request.Response(json={'hello': 'world'})


  # You can change the default 200 status `code` for another
  @app.get('/code')
  def code(request):
      return request.Response(code=random.choice([200, 201, 400, 404, 500]))


  # And of course you can provide custom `headers`.
  @app.get('/headers')
  def headers(request):
      return request.Response(
          text='headers',
          headers={'X-Header': 'Value',
                   'Refresh': '5; url=https://xkcd.com/353/'})


  # Or `cookies` by using Python standard library `http.cookies.SimpleCookie`.
  @app.get('/cookies')
  def cookies(request):
      cookies = SimpleCookie()
      cookies['hello'] = 'world'
      cookies['hello']['domain'] = 'localhost'
      cookies['hello']['path'] = '/'
      cookies['hello']['max-age'] = 3600
      cookies['city'] = 'São Paulo'

      return request.Response(text='cookies', cookies=cookies)

  
  app.run()
  ```

The source code for all the examples can be found in [examples directory](https://github.com/squeaky-pl/japronto/tree/master/examples).


**Next:** [Handling exceptions](6_exceptions.md)
