# examples/8_template/template.py
from japronto import Application
from jinja2 import Template

# Create the japronto application
app = Application()

# A view can read HTML from a file
@app.get()
def index(request):
    with open('index.html') as html_file:
        return request.Response(text=html_file.read(), mime_type='text/html')


# A view could also return a raw HTML string
@app.get('/example')
def example(request):
    return request.Response(text='<h1>Some HTML!</h1>', mime_type='text/html')


template = Template('<h1>Hello {{ name }}!</h1>')

# A view could also return a rendered jinja2 template
@app.get('/jinja2')
def jinja(request):
    return request.Response(text=template.render(name='World'), mime_type='text/html')

# Start the server
app.run(debug=True)

