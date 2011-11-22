# Copyright (c) 2011, Daniel Crosta
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


from datetime import datetime
import hashlib
import mimetypes
import os, os.path

from werkzeug.wrappers import Request, Response
from werkzeug.exceptions import HTTPException

from keystone import http
from keystone.render import *

# requests for paths ending in these extensions
# will be rejected with status 404
HIDDEN_EXTS = ('.ks', '.py', '.pyc', '.pyo')

class Keystone(object):

    def __init__(self, app_dir=os.getcwd(), static_expires=86400):
        self.app_dir = app_dir
        self.static_expires = 86400
        self.engine = RenderEngine(self)

    def __call__(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch(request)
        return response(environ, start_response)

    def dispatch(self, request):
        try:
            found = self._find(request.path)

            if isinstance(found, Template):
                return self.render_keystone(request, found)
            elif isinstance(found, file):
                return self.render_static(request, found)

            raise http.NotFound()

        except HTTPException, httpe:
            # TODO: error handler hooks
            return httpe.get_response(request.environ)


    def render_keystone(self, request, template):
        response = Response()
        response.headers.set('Content-Type', 'text/html')

        viewglobals = {
            'request': request,
            'http': http,
            'headers': response.headers,
            'cookies': request.cookies,
            'set_cookie': response.set_cookie,
            'delete_cookie': response.delete_cookie,
        }

        try:
            response.response = self.engine.render(template, viewglobals)
        except HTTPException, ex:
            return ex.get_response(request.environ)

        return response

    def render_static(self, request, fileobj):
        if request.method != 'GET':
            raise http.MethodNotAllowed(['GET'])

        content_type, content_encoding = mimetypes.guess_type(fileobj.name)

        stat = os.stat(fileobj.name)
        etag = hashlib.md5(str(stat.st_mtime)).hexdigest()

        response = Response(fileobj)
        response.content_type = content_type
        response.content_length = stat.st_size
        response.add_etag(etag)
        response.last_modified = datetime.utcfromtimestamp(stat.st_mtime)
        response.expires = datetime.utcfromtimestamp(stat.st_mtime + self.static_expires)

        if content_encoding:
            response.content_encoding = content_encoding

        response.make_conditional(request)
        return response

    def _find(self, path):
        if any(path.endswith(ext) for ext in HIDDEN_EXTS):
            return None

        if path.startswith('/'):
            path = path[1:]
        if path == '':
            path = 'index'

        # first: see if an exact match exists
        fspath = os.path.abspath(os.path.join(self.app_dir, path))
        if os.path.exists(fspath):
            return file(fspath, 'r+b')

        # next: see if an exact path match with
        # extension ".ks" exists, and load template
        fspath += '.ks'
        if os.path.exists(fspath):
            return self.engine.get_template(path + '.ks')

        return None

