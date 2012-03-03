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
from itertools import izip
import hashlib
import mimetypes
import os, os.path
import sys
import urlparse
import warnings

from werkzeug.wrappers import Request, Response
from werkzeug.exceptions import HTTPException

from keystone import http
from keystone.render import *

# requests for paths ending in these extensions
# will be rejected with status 404
HIDDEN_EXTS = ('.ks', '.py', '.pyc', '.pyo')

class Keystone(object):

    def __init__(self, app_dir=os.getcwd(), static_expires=86400):
        self.app_dir = os.path.abspath(app_dir)
        self.static_expires = 86400
        self.engine = RenderEngine(self)

        if self.app_dir not in sys.path:
            sys.path.insert(0, self.app_dir)

        try:
            import startup
        except ImportError:
            pass

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
        response = Response(mimetype='text/html')

        viewlocals = {
            'request': request,
            'http': http,
            'headers': response.headers,
            'set_cookie': response.set_cookie,
            'delete_cookie': response.delete_cookie,
            'return_response': return_response,
            'app_dir': self.app_dir,
        }

        try:
            response.response = self.engine.render(template, viewlocals)
        except HTTPException, ex:
            return ex.get_response(request.environ)
        except:
            raise http.InternalServerError()

        return response

    def render_static(self, request, fileobj):
        if request.method != 'GET':
            raise http.MethodNotAllowed(['GET'])

        content_type, _ = mimetypes.guess_type(fileobj.name)

        stat = os.stat(fileobj.name)
        etag = hashlib.md5(str(stat.st_mtime)).hexdigest()

        response = Response(fileobj, mimetype=content_type)
        response.content_length = stat.st_size
        response.add_etag(etag)
        response.last_modified = datetime.utcfromtimestamp(stat.st_mtime)
        response.expires = datetime.utcfromtimestamp(stat.st_mtime + self.static_expires)

        response.make_conditional(request)
        return response

    def _find(self, path):
        if any(path.endswith(ext) for ext in HIDDEN_EXTS):
            return None

        if path.startswith('/'):
            path = path[1:]
        if path == '':
            path = 'index'

        # use urljoin, since it preserves the trailing /
        # that may be a part of path; since self.app_dir
        # was abspath'd, we must unconditionally add a
        # trailing slash to *it*, since the second arg
        # to urljoin is treated relative to the first
        fspath = urlparse.urljoin(self.app_dir + '/', path)

        # first: see if an exact match exists
        if os.path.isfile(fspath):
            if os.path.basename(fspath).startswith('_'):
                return None
            return file(fspath, 'rb')

        # next: see if an exact path match with
        # extension ".ks" exists, and load template
        fspath += '.ks'
        if os.path.isfile(fspath):
            return self.engine.get_template(path + '.ks')

        # finally: see if a parameterized path matches
        # the request path.
        candidates = []

        pathparts = path.split('/')
        pathdepth = path.count('/')
        for dirpath, dirnames, filenames in os.walk(self.app_dir):
            dirpath = dirpath[len(self.app_dir):]
            depth = dirpath.count('/')
            for dirname in list(dirnames):
                if dirname == pathparts[depth]:
                    continue
                if dirname.startswith('%'):
                    continue
                dirnames.remove(dirname)

            if pathdepth == depth:
                dirpath = dirpath.lstrip('/')
                for filename in filenames:
                    if filename.startswith('%'):
                        candidates.append(os.path.join(dirpath, filename))
                    elif filename.endswith('.ks'):
                        if pathparts[-1] == '' and filename == 'index.ks' or \
                           filename == pathparts[-1] + '.ks':
                            candidates.append(os.path.join(dirpath, filename))
                    elif filename == pathparts[-1]:
                        candidates.append(os.path.join(dirpath, filename))

        if not candidates:
            return None

        scores = self._score_candidates(path, candidates)
        maxscore = max(scores)
        candidates = [c for c, s in izip(candidates, scores) if s == maxscore]

        if len(candidates) > 1:
            # choose the first one alphabetically;
            # this is arbitrary, but consistent
            candidates.sort()
            warnings.warn(
                'Multiple parameterized paths matched: %r, choosing %r' %
                (candidates, candidates[0]))

        winner = candidates[0]
        if not winner.endswith('.ks'):
            # we've matched a static file with a wildcard
            # path, so just return a file object on it
            fspath = os.path.join(self.app_dir, winner)
            return file(fspath, 'rb')

        urlparams = {}
        for pathpart, urlpart in izip(path.split('/'), winner.split('/')):
            if urlpart.startswith('%'):
                name = urlpart[1:]
                if name.endswith('.ks'):
                    name = name[:-3]
                urlparams[name] = pathpart

        template = self.engine.get_template(winner).copy()
        template.urlparams = urlparams
        return template

    def _score_candidates(self, path, candidates):
        """
        When several templates may match a path, we score the
        candidate templates according to this algorithm:

        * Assign one point to each candidate for each path segment
          that matches exactly
        * Assign two points to each candidate if the final path
          segment is the empty string (that is, the path ended in
          a forward slash) and the candidate's final segment is
          "index.ks"

        Returns a list of scores in the same order as candidates.
        """
        pparts = path.split('/')
        scores = []

        for candidate in candidates:
            cparts = candidate.split('/')
            score = 0
            for pathpart, candidatepart in izip(pparts, cparts):
                if candidatepart.endswith('.ks'):
                    candidatepart = candidatepart[:-3]
                if pathpart == candidatepart:
                    score += 1
                elif pathpart == '' and candidatepart == 'index':
                    score += 2
            scores.append(score)

        return scores

