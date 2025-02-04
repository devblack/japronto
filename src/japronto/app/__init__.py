import signal
import asyncio
import traceback
import socket
import sys

from os import set_inheritable as os_set_inheritable, environ as os_environ
from multiprocessing import Process as mult_process
from faulthandler import enable as enablefaulthandler
from uvloop import new_event_loop as uv_new_event_loop
from inspect import iscoroutinefunction

from japronto.router import Router, RouteNotFoundException
from japronto.protocol.cprotocol import Protocol
from japronto.protocol.creaper import Reaper
from japronto import helpers


signames = {
    int(v): v.name for k, v in signal.__dict__.items()
    if isinstance(v, signal.Signals)
}

class Application:
    def __init__(self, *, reaper_settings=None, log_request=None, protocol_factory=None, debug=False):
        self._router = None
        self._loop = None
        self._connections = set()
        self._reaper_settings = reaper_settings or {}
        self._error_handlers = []
        self._log_request = log_request
        self._request_extensions = {}
        self._protocol_factory = protocol_factory or Protocol
        self._debug = debug
        self._on_startup = []
        self._on_cleanup = []

    @property
    def loop(self):
        if not self._loop:
            self._loop = uv_new_event_loop()
        return self._loop

    @property
    def router(self):
        if not self._router:
            self._router = Router()

        return self._router

    @property
    def on_startup(self):
        return self._on_startup

    @property
    def on_cleanup(self):
        return self._on_cleanup


    def __finalize(self):
        self.loop
        self.router

        self._reaper = Reaper(self, **self._reaper_settings)
        self._matcher = self._router.get_matcher()

    def route(self, path: str = '/', methods: list = []):
        '''
        Shorthand route decorator. Avoids need to register
        handlers to the router directly with `app.router.add_route()`.
        '''
        def decorator(handler):
            async def wrapper(*args, **kwargs):
                # check awaitable handler
                if iscoroutinefunction(handler):
                    return await handler(*args, **kwargs)
                return handler(*args, **kwargs)
            self.router.add_route(path, wrapper, methods=methods)
            return wrapper
        return decorator

    def get(self, path: str = '/'):
        return self.route(path, methods=["GET"])

    def post(self, path: str = '/'):
        return self.route(path, methods=["POST"])

    def put(self, path: str = '/'):
        return self.route(path, methods=["PUT"])

    def patch(self, path: str = '/'):
        return self.route(path, methods=["PATCH"])

    def options(self, path: str = '/'):
        return self.route(path, methods=["OPTIONS"])

    def delete(self, path: str = '/'):
        return self.route(path, methods=["DELETE"])

    def protocol_error_handler(self, error):
        print(error)

        error = error.encode('utf-8')

        response = [
            'HTTP/1.0 400 Bad Request\r\n',
            'Content-Type: text/plain; charset=utf-8\r\n',
            'Content-Length: {}\r\n\r\n'.format(len(error))]

        return ''.join(response).encode('utf-8') + error

    def default_request_logger(self, request):
        print(request.transport)
        print(request.remote_addr, request.method, request.path)

    def set_error_handler(self, typ, handler):
        '''
        Shorthand `set_error_handler` decorator for `app.add_error_handler`.
        '''
        if typ is None: raise AssertionError("'typ' Can't be defined as 'None'.")
        def decorator(f):
            return f
        self._error_handlers.append((typ, handler))
        return decorator

    def add_error_handler(self, typ, handler):
        if typ is None: raise AssertionError("'typ' Can't be defined as 'None'.")
        self._error_handlers.append((typ, handler))

    def default_error_handler(self, request, exception):
        if isinstance(exception, RouteNotFoundException):
            return request.Response(code=404, text='Not Found')
        if isinstance(exception, asyncio.CancelledError):
            return request.Response(code=503, text='Service unavailable')

        tb = traceback.format_exception(None, exception, exception.__traceback__)
        tb = ''.join(tb)
        print(tb, file=sys.stderr, end='')
        return request.Response(code=500, text=tb if self._debug else 'Internal Server Error')

    def error_handler(self, request, exception):
        for typ, handler in self._error_handlers:
            if typ is not None and not isinstance(exception, typ):
                continue

            try:
                return handler(request, exception)
            except:
                print('-- Exception in error_handler occured:')
                traceback.print_exc()

            print('-- while handling:')
            traceback.print_exception(None, exception, exception.__traceback__)
            return request.Response(
                code=500, text='Internal Server Error')

        return self.default_error_handler(request, exception)

    def _get_idle_and_busy_connections(self):
        # FIXME if there is buffered data in gather the connections should be
        # considered busy, now it's idle
        return \
            [c for c in self._connections if c.pipeline_empty], \
            [c for c in self._connections if not c.pipeline_empty]

    async def drain(self):
        # TODO idle connections will close connection with half-read requests
        idle, busy = self._get_idle_and_busy_connections()
        for c in idle:
            c.transport.close()
        #       for c in busy_connections:
        #            need to implement something that makes protocol.on_data
        #            start rejecting incoming data
        #            this closes transport unfortunately
        #            sock = c.transport.get_extra_info('socket')
        #            sock.shutdown(socket.SHUT_RD)

        if idle or busy:
            print('Draining connections...')
        else:
            return

        if idle:
            print('{} idle connections closed immediately'.format(len(idle)))
        if busy:
            print('{} connections busy, read-end closed'.format(len(busy)))

        for x in range(5, 0, -1):
            await asyncio.sleep(1)
            idle, busy = self._get_idle_and_busy_connections()
            for c in idle:
                c.transport.close()
            if not busy:
                break
            else:
                print("{} seconds remaining, {} connections still busy".format(x, len(busy)))

        _, busy = self._get_idle_and_busy_connections()
        if busy:
            print('Forcefully killing {} connections'.format(len(busy)))
        for c in busy:
            c.pipeline_cancel()

    def set_req_extension(self, handler, name=None, property=False):
        '''
        Shorthand `set_req_extension` decorator for `app.extend_request`.
        '''
        if not name:
            name = handler.__name__
        def decorator(f):
                # check awaitable handler
                if iscoroutinefunction(f):
                    return await f
                return handler(*args, **kwargs)
            return f
        self._request_extensions[name] = (handler, property)
        return decorator

    def extend_request(self, handler, *, name=None, property=False):
        if not name:
            name = handler.__name__

        self._request_extensions[name] = (handler, property)

    def serve(self, *, sock, host, port, reloader_pid):
        enablefaulthandler()
        self.__finalize()

        loop = self.loop
        asyncio.set_event_loop(loop)

        for prepare in self.on_startup:
            loop.run_until_complete(prepare(self))

        async def start_serving():
            try:
                server = await loop.create_server(lambda: self._protocol_factory(self), sock=sock)
                while True:
                    await asyncio.sleep(3600)
            except asyncio.CancelledError:
                server.close()
                await server.wait_closed()

        def stop_serving():
            for task in helpers.all_tasks(loop):
                task.cancel()

        loop.add_signal_handler(signal.SIGTERM, stop_serving)
        loop.add_signal_handler(signal.SIGINT, stop_serving)

        if reloader_pid:
            from japronto.reloader import ChangeDetector
            detector = ChangeDetector(loop)
            detector.start()

        try:
            loop.run_until_complete(start_serving())
        finally:
            loop.run_until_complete(self.drain())
            self._reaper.stop()
            for finalize in self.on_cleanup:
                loop.run_until_complete(finalize(self))
            loop.close()

            # break reference and cleanup matcher buffer
            del self._matcher

    def _run(self, *, host, port, worker_num=None, reloader_pid=None, debug=None):
        self._debug = debug or self._debug
        if self._debug and self._log_request is None:
            self._log_request = self._debug

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        os_set_inheritable(sock.fileno(), True)

        workers = set()

        terminating = False

        def stop(sig, frame):
            nonlocal terminating
            if reloader_pid and sig == signal.SIGHUP:
                print('Reload request received')
            elif not terminating:
                terminating = True
                print('Termination request received')
            for worker in workers:
                worker.terminate()

        signal.signal(signal.SIGINT, stop)
        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGHUP, stop)

        for _ in range(worker_num or 1):
            print('Starting worker number {} on http://{}:{}'.format(_+1, host, port))
            worker = mult_process(target=self.serve, kwargs=dict(sock=sock, host=host, port=port, reloader_pid=reloader_pid))
            worker.daemon = True
            worker.start()
            workers.add(worker)

        # prevent further operations on socket in parent
        sock.close()

        for worker in workers:
            worker.join()

            if worker.exitcode > 0:
                print('Worker exited with code {}'.format(worker.exitcode))
            elif worker.exitcode < 0:
                print("worker: ", worker)
                try:
                    signame = signames[-worker.exitcode]
                except KeyError:
                    print('Worker crashed with unknown code {}!'.format(worker.exitcode))
                else:
                    print('Worker crashed on signal {}!'.format(signame))

    def run(self, host='0.0.0.0', port=8080, *, worker_num=None, reload=False, debug=False):
        if os_environ.get('_JAPR_IGNORE_RUN'):
            return

        reloader_pid = None
        jarp_var = os_environ.get('_JAPR_RELOADER')
        if reload and jarp_var:
            reloader_pid = int(jarp_var)
        elif reload:
            from japronto.reloader import exec_reloader
            exec_reloader(host=host, port=port, worker_num=worker_num)


        self._run(host=host, port=port, worker_num=worker_num, reloader_pid=reloader_pid, debug=debug)
