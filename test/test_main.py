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

from __future__ import with_statement

import os
import os.path
import shutil
import sys
import unittest
from inspect import getargspec
from werkzeug.datastructures import Headers
from werkzeug.wrappers import Request
from werkzeug.wrappers import BaseResponse
from werkzeug.test import Client
from werkzeug.test import EnvironBuilder

import util

from keystone import http
from keystone.main import Keystone
from keystone.render import Template

def wsgi_environ(method, url, data=None, content_type=None, headers={}):
    hdrs = Headers(headers)
    b = EnvironBuilder(method=method, path=url, headers=hdrs)
    return b.get_environ()

class KeystoneTest(unittest.TestCase):

    def setUp(self):
        here = os.path.abspath(os.path.dirname(__file__))
        self.app_dir = os.path.join(here, 'app_dir')

        shutil.rmtree(self.app_dir, ignore_errors=True)
        os.makedirs(self.app_dir)

    def tearDown(self):
        shutil.rmtree(self.app_dir, ignore_errors=True)
        if 'startup' in sys.modules:
            del sys.modules['startup']

    def test_app_is_wsgi(self):
        app = Keystone(self.app_dir)

        self.assertTrue(callable(app), 'Keystone object should be callable')
        self.assertEqual(len(getargspec(app.__call__)[0]), 3, 'Keystone should take 2 arguments')
        self.assertTrue(getargspec(app.__call__)[1] is None, 'viewfunc should take no varargs')
        self.assertTrue(getargspec(app.__call__)[2] is None, 'viewfunc should take no kwargs')
        self.assertTrue(getargspec(app.__call__)[3] is None, 'viewfunc should have no defaults')

        # test that a simple call gets a valid response
        client = Client(app, BaseResponse)
        response = client.get('/')

        self.assertEqual(response.status_code, 404, 'WSGI call did not get 404 for request to empty app')

    def test_dispatch(self):
        index = os.path.join(self.app_dir, 'index.ks')
        static = os.path.join(self.app_dir, 'base.css')

        app = Keystone(self.app_dir)
        req = Request(wsgi_environ('GET', '/'))

        response = app.dispatch(req)
        self.assertTrue(isinstance(response, BaseResponse), 'dispatch on missing did not return a Response')
        self.assertEqual(response.status_code, 404, 'missing did not get a 404 HTTPException (got %d)' % response.status_code)

        changer = util.MtimeChanger()

        with changer.change_times(file(index, 'w')) as fp:
            fp.write('raise Exception("blah")\n----\n<strong>this is HTML</strong>\n')

        response = app.dispatch(req)
        self.assertTrue(isinstance(response, BaseResponse), 'dispatch on exception did not return a Response')
        self.assertEqual(response.status_code, 500, 'error did not get a 500 HTTPException (got %d)' % response.status_code)

        with changer.change_times(file(index, 'w')) as fp:
            fp.write('raise http.SeeOther("/foo")\n----\n<strong>this is HTML</strong>\n')

        response = app.dispatch(req)
        self.assertTrue(isinstance(response, BaseResponse), 'dispatch on HTTPException did not return a Response')
        self.assertEqual(response.status_code, 303, 'redirect (see other) did not get a 303 HTTPException (got %d)' % response.status_code)

        with changer.change_times(file(index, 'w')) as fp:
            fp.write('<strong>this is HTML</strong>\n')

        response = app.dispatch(req)
        self.assertTrue(isinstance(response, BaseResponse), 'dispatch on html-only template did not return a Response')
        self.assertEqual(response.status_code, 200, 'dispatch to template did not get a 200 status (got %d)' % response.status_code)

        with changer.change_times(file(index, 'w')) as fp:
            fp.write('# this is python\n----\n<strong>this is HTML</strong>\n')

        response = app.dispatch(req)
        self.assertTrue(isinstance(response, BaseResponse), 'dispatch on mixed template did not return a Response')
        self.assertEqual(response.status_code, 200, 'dispatch to template did not get a 200 status (got %d)' % response.status_code)

        with changer.change_times(file(static, 'w')) as fp:
            fp.write('* { background-color: white }\n')

        req = Request(wsgi_environ('GET', '/base.css'))
        response = app.dispatch(req)
        self.assertTrue(isinstance(response, BaseResponse), 'dispatch on static did not return a Response')
        self.assertEqual(response.status_code, 200, 'dispatch to static did not get a 200 status (got %d)' % response.status_code)

    def test_render_static(self):
        static = os.path.join(self.app_dir, 'base.css')

        with file(static, 'w') as fp:
            fp.write('* { background-color: white }\n')

        app = Keystone(self.app_dir)
        req = Request(wsgi_environ('POST', '/base.css'))

        fileobj = file(static, 'rb')
        self.assertRaises(http.MethodNotAllowed, app.render_static, req, fileobj)

        req = Request(wsgi_environ('GET', '/base.css'))
        fileobj.seek(0, 0)
        response = app.render_static(req, fileobj)
        self.assertEqual(response.data, '* { background-color: white }\n')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_length, 30)
        self.assertEqual(response.mimetype, 'text/css')
        self.assertTrue('ETag' in response.headers)
        self.assertTrue('Last-Modified' in response.headers)
        self.assertTrue('Expires' in response.headers)

        last_modified = response.headers['Last-Modified']

        req = Request(wsgi_environ('GET', '/base.css', headers={'If-Modified-Since': last_modified}))
        response = app.render_static(req, fileobj)
        self.assertEqual(response.data, '')
        self.assertEqual(response.status_code, 304)

    def test_render_keystone(self):
        changer = util.MtimeChanger()
        index = os.path.join(self.app_dir, 'index.ks')

        with file(index, 'w') as fp:
            fp.write('# this is python\n----\n<strong>this is HTML</strong>\n')

        app = Keystone(self.app_dir)
        template = app.engine.get_template(index)

        req = Request(wsgi_environ('GET', '/'))
        response = app.render_keystone(req, template)

        self.assertEqual(response.data, '<strong>this is HTML</strong>')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'text/html')
        self.assertTrue('Content-Length' not in response.headers)
        self.assertTrue('ETag' not in response.headers)
        self.assertTrue('Last-Modified' not in response.headers)
        self.assertTrue('Expires' not in response.headers)
        self.assertTrue('Cache-Control' not in response.headers)
        self.assertTrue('Set-Cookie' not in response.headers)

        for method in ('GET', 'POST', 'HEAD', 'OPTIONS', 'PUT', 'DELETE'):
            # none of these should raise
            req = Request(wsgi_environ(method, '/'))
            app.render_keystone(req, template)


        with changer.change_times(file(index, 'w')) as fp:
            fp.write('return_response("hello, world")\n----\n<strong>this is HTML</strong>\n')

        req = Request(wsgi_environ('GET', '/'))
        template = app.engine.get_template(index)
        response = app.render_keystone(req, template)

        self.assertEqual(response.data, 'hello, world')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'text/html')
        self.assertTrue('Content-Length' not in response.headers)
        self.assertTrue('ETag' not in response.headers)
        self.assertTrue('Last-Modified' not in response.headers)
        self.assertTrue('Expires' not in response.headers)
        self.assertTrue('Cache-Control' not in response.headers)
        self.assertTrue('Set-Cookie' not in response.headers)

    def test_cookies(self):
        changer = util.MtimeChanger()
        index = os.path.join(self.app_dir, 'index.ks')
        app = Keystone(self.app_dir)

        with file(index, 'w') as fp:
            fp.write('set_cookie("name", "value")\n----\n<strong>this is HTML</strong>\n')

        req = Request(wsgi_environ('GET', '/'))
        template = app.engine.get_template(index)
        response = app.render_keystone(req, template)
        self.assertEqual(response.headers['Set-Cookie'], 'name=value; Path=/')

        with changer.change_times(file(index, 'w')) as fp:
            fp.write('delete_cookie("name")\n----\n<strong>this is HTML</strong>\n')

        req = Request(wsgi_environ('GET', '/'))
        template = app.engine.get_template(index)
        response = app.render_keystone(req, template)
        self.assertEqual(response.headers['Set-Cookie'], 'name=; expires=Thu, 01-Jan-1970 00:00:00 GMT; Max-Age=0; Path=/')

    def test_headers(self):
        index = os.path.join(self.app_dir, 'index.ks')
        app = Keystone(self.app_dir)

        with file(index, 'w') as fp:
            fp.write('headers.set("X-Key", "value")\n----\n<strong>this is HTML</strong>\n')

        req = Request(wsgi_environ('GET', '/'))
        template = app.engine.get_template(index)
        response = app.render_keystone(req, template)
        self.assertTrue('X-Key' in response.headers)
        self.assertEqual(response.headers['X-Key'], 'value')

    def test_find(self):
        app_contents = {
            'index.ks': 'index',
            'pageA.ks': 'pageA',
            '%widlcard.ks': '----\n{{wildcard}}',
            'file.txt': 'file 1',
            '_base.html': 'hello',
            'something.py': '# blah',
            'something.pyc': '# blah',
            'something.pyo': '# blah',
            '.dotfile': 'dotfile',
            'subdir': {
                'index.ks': 'subdir index',
                'pageA.ks': 'subdir pageA',
                'file.txt': 'file 2',
            },
            '%wildcard': {
                'index.ks': '----\n{{wildcard}} index',
                'pageA.ks': '----\n{{wildcard}} pageA',
                '%wildcard2.ks': '----\n{{wildcard}} {{wildcard2}}',
                'file.txt': 'wildcard file',
            },
            'baddir': {
                '%wildcardA.ks': '----\n{{wildcardA}} A',
                '%wildcardB.ks': '----\n{{wildcardB}} B',
            },
            'static': {
                'file.txt': 'file 3'
            }
        }

        def write_files(root_path, tree):
            for filename, contents in tree.iteritems():
                if isinstance(contents, dict):
                    subdir = os.path.join(root_path, filename)
                    os.makedirs(subdir)
                    write_files(subdir, contents)
                else:
                    with file(os.path.join(root_path, filename), 'w') as fp:
                        fp.write(contents)

        write_files(self.app_dir, app_contents)

        cases = [
            {'path': '/', 'type': Template, 'body': 'index'},
            {'path': '/index', 'type': Template, 'body': 'index'},
            {'path': '/index.ks', 'type': type(None)},

            {'path': '/something.py', 'type': type(None)},
            {'path': '/something.pyc', 'type': type(None)},
            {'path': '/something.pyo', 'type': type(None)},
            {'path': '/_base.html', 'type': type(None)},
            {'path': '/.dotfile', 'type': type(None)},

            {'path': '/pageA', 'type': Template, 'body': 'pageA'},

            {'path': '/somePage', 'type': Template, 'body': '{{wildcard}}'},
            {'path': '/anotherPage', 'type': Template, 'body': '{{wildcard}}'},

            {'path': '/file.txt', 'type': file, 'contents': 'file 1'},

            # TODO: not sure that this is what we should be returning
            # here. options are:
            #
            #  1. return None (404)
            #  2. return the same as /subdir/
            #  3. redirect to /subdir/
            {'path': '/subdir', 'type': Template, 'body': '{{wildcard}}'},

            {'path': '/subdir/', 'type': Template, 'body': 'subdir index'},
            {'path': '/subdir/index', 'type': Template, 'body': 'subdir index'},
            {'path': '/subdir/index/', 'type': type(None)},

            {'path': '/subdir/pageA', 'type': Template, 'body': 'subdir pageA'},
            {'path': '/subdir/file.txt', 'type': file, 'contents': 'file 2'},

            {'path': '/anydir', 'type': Template, 'body': '{{wildcard}}'},

            {'path': '/anydir/', 'type': Template, 'body': '{{wildcard}} index'},
            {'path': '/anydir/index', 'type': Template, 'body': '{{wildcard}} index'},
            {'path': '/anydir/pageA', 'type': Template, 'body': '{{wildcard}} pageA'},

            {'path': '/anydir/pagename', 'type': Template, 'body': '{{wildcard}} {{wildcard2}}'},
            {'path': '/anydir/pagename/', 'type': type(None)},

            {'path': '/anydir/file.txt', 'type': file, 'contents': 'wildcard file'},
            {'path': '/other/file.txt', 'type': file, 'contents': 'wildcard file'},

            {'path': '/baddir/foo', 'type': Template, 'body': '{{wildcardA}} A', 'warns': True},
        ]

        app = Keystone(self.app_dir)
        for testcase in cases:
            path = testcase['path']
            with util.WarningCatcher(UserWarning) as wc:
                found = app._find(path)
                if 'warns' in testcase:
                    self.assertTrue(wc.has_warning(UserWarning), '_find(%r) should have warned about multiple matches' % path)

            self.assertEqual(type(found), testcase['type'], '_find(%r) returned %s, expected %s' % (path, type(found), testcase['type']))

            if isinstance(found, Template):
                self.assertEqual(found.body, testcase['body'], '_find(%r).body is %r, expected %r' % (path, found.body, testcase['body']))
            elif isinstance(found, file):
                contents = found.read()
                self.assertEqual(contents, testcase['contents'], '_find(%r).read() is %r, expected %r' % (path, contents, testcase['contents']))

    def test_score_candidates(self):
        cases = [
            ('foo', ['%x.ks', 'foo.ks'], [0, 1]),
            ('bar', ['%x.ks', '%y.ks'], [0, 0]),
            ('baz', ['baz.ks'], [1]),
            ('foo/bar', ['%y/%x.ks', 'foo/%x.ks', '%y/bar.ks'], [0, 1, 1]),
            ('foo/', ['%y/%x.ks', 'foo/%x.ks', '%y/index.ks'], [0, 1, 2]),
            ('foo/baz', ['%x/%y.ks', 'foo/%y.ks', '%x/baz', '%x/baz.ks'], [0, 1, 1, 1]),
        ]

        app = Keystone()
        for path, candidates, expected in cases:
            scores = app._score_candidates(path, candidates)
            self.assertEqual(scores, expected, 'wrong scores for %r: %r, expected %r' % (path, scores, expected))

    def test_startup_module(self):
        startup = os.path.join(self.app_dir, 'startup.py')
        with file(startup, 'w') as fp:
            fp.write('# do nothing\n')

        Keystone(self.app_dir)

        self.assertTrue('startup' in sys.modules, 'startup.py was not loaded')
        self.assertEqual(sys.modules['startup'].__file__, startup, 'wrong startup.py was loaded')
