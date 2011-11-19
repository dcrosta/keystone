import mimetypes
import os, os.path

from werkzeug.wrappers import Request, Response

from keystone.render import *

class Keystone(object):

    def __init__(self, app_dir):
        self.app_dir = app_dir

    def __call__(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch(request)
        return response(environ, start_response)

    def dispatch(self, request):
        response = Response('Not Found', status=404)

        content_type, content_encoding, iterable = self._find(request.path)
        if content_type == 'text/keystone':
            content_type = 'text/html'
            iterable = render_keystone(iterable, jinja)

        if iterable:
            response = Response(iterable)
            response.content_type = content_type

            if content_encoding:
                response.content_encoding = content_encoding

            if all(hasattr(iterable, x) for x in ('seek', 'tell')):
                iterable.seek(0, os.SEEK_END)
                response.content_length = iterable.tell()
                iterable.seek(0, os.SEEK_SET)
            elif hasattr(iterable, 'len'):
                response.content_length = sum(map(len, map(unicode, iterable)))

        return response

    def _find(self, path):
        if path.startswith('/'):
            path = path[1:]
        if path == '':
            path = 'index'

        # first: see if an exact match exists
        fspath = os.path.abspath(os.path.join(self.app_dir, path))
        if os.path.exists(fspath):
            t, e = mimetypes.guess_type(fspath)
            return t, e, file(fspath, 'r+b')

        # next: see if an exact path match with
        # extension ".ks" exists, and load template
        fspath += '.ks'
        if os.path.exists(fspath):
            return 'text/keystone', None, file(fspath, 'r+b')

        return None, None, None



def serve():
    import werkzeug.serving
    import sys

    # TODO: argparser
    host = '0.0.0.0'
    port = 5000
    use_reloader = True
    use_debugger = True
    app_dir = sys.argv[1] if len(sys.argv) == 2 else os.getcwd()
    app_dir = os.path.abspath(app_dir)

    app = Keystone(
        app_dir=app_dir,
    )

    return werkzeug.serving.run_simple(
        host, port, app,
        use_reloader=use_reloader,
        use_debugger=use_debugger,
    )

