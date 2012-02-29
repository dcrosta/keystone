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
import re
import time
import unittest
from inspect import iscode, isfunction, getargspec
from StringIO import StringIO

from keystone.render import Template
from keystone.render import InvalidTemplate
from keystone.render import TemplateNotFound
from keystone.render import RenderEngine


def dedent(string, joiner='\n'):
    """
    De-indent a string. Used by ParserTest to let nicely-formatted
    triple-quoted strings be used for defining templates. Based on
    DocTestParser._min_indent.
    """
    string = string.strip('\r\n')
    INDENT_RE = re.compile('^([ ]*)(?=\S)', re.MULTILINE)
    min_indent = min(len(indent) for indent in INDENT_RE.findall(string))
    return joiner.join(line[min_indent:] for line in string.splitlines())

class MockApp(object):
    def __init__(self, app_dir=None):
        self.app_dir = app_dir

def template_fileobj(string, name='madeup'):
    """
    Create a file-like object with 'name' attribute (on real files
    this is the file name; for tests we can just use something
    made up) suitable for use with RenderEngine.parse() and friends.
    """
    out = StringIO(dedent(string))
    out.name = name
    return out


class TemplateTest(unittest.TestCase):

    def test_copy(self):
        t = Template(
            viewfunc=lambda x: x,
            body='body',
            mtime=1234,
            name='name',
        )
        copy = t.copy()

        # template copies should be identical except for urlparams
        self.assertTrue(t.viewfunc is copy.viewfunc, 'viewfunc changed in copy()')
        self.assertTrue(t.body is copy.body, 'body changed in copy()')
        self.assertTrue(t.mtime is copy.mtime, 'mtime changed in copy()')
        self.assertTrue(t.name is copy.name, 'name changed in copy()')
        self.assertTrue(t.urlparams is not copy.urlparams, 'urlparams did not change in copy()')
        self.assertTrue(copy.urlparams == {}, 'urlparams is not empty in copy()')

        # template copies should not have urlparams set
        t.urlparams = {'a': 1, 'b': 2}
        copy = t.copy()

        self.assertTrue(t.viewfunc is copy.viewfunc, 'viewfunc changed in copy()')
        self.assertTrue(t.body is copy.body, 'body changed in copy()')
        self.assertTrue(t.mtime is copy.mtime, 'mtime changed in copy()')
        self.assertTrue(t.name is copy.name, 'name changed in copy()')
        self.assertTrue(t.urlparams is not copy.urlparams, 'urlparams did not change in copy()')
        self.assertTrue(copy.urlparams == {}, 'urlparams is not empty in copy()')


class ParserTest(unittest.TestCase):

    def test_split(self):
        templatefp = template_fileobj("""
        # this is python
        ----
        <strong>this is HTML</strong>
        """)

        engine = RenderEngine(MockApp())
        template = engine.parse(templatefp)
        viewfunc, body = template.viewfunc, template.body

        self.assertTrue(isfunction(viewfunc), 'viewfunc is not a function')
        self.assertEquals(len(getargspec(viewfunc)[0]), 1, 'viewfunc should take only 1 argument')
        self.assertTrue(getargspec(viewfunc)[1] is None, 'viewfunc should take no varargs')
        self.assertTrue(getargspec(viewfunc)[2] is None, 'viewfunc should take no kwargs')
        self.assertTrue(getargspec(viewfunc)[3] is None, 'viewfunc should have no defaults')

        self.assertEquals(body, '<strong>this is HTML</strong>\n', 'template body is incorrect')

    def test_no_split(self):
        templatefp = template_fileobj("""
        <strong>this is HTML</strong>
        """)

        engine = RenderEngine(MockApp())
        template = engine.parse(templatefp)
        viewfunc, body = template.viewfunc, template.body

        self.assertEquals(1, viewfunc(1), 'viewfunc should be an identity function')

        self.assertEquals(body, '<strong>this is HTML</strong>\n', 'template body is incorrect')

    def test_two_splits(self):
        templatefp = template_fileobj("""
        # this is python
        ----
        <strong>this is HTML</strong>
        ----
        # this is an error
        """)

        engine = RenderEngine(MockApp())
        self.assertRaises(InvalidTemplate, engine.parse, templatefp)

    def test_viewfunc(self):
        # the viewfunc is essentially "do some stuff, then return locals()",
        # so we just want to ensure that things we expect in the output dict
        # are there
        templatefp = template_fileobj("""
        x = 1
        y = 'abc'
        ----
        <strong>this is HTML</strong>
        """)

        engine = RenderEngine(MockApp())
        template = engine.parse(templatefp)

        returned_locals = template.viewfunc({})
        self.assertEquals({'x': 1, 'y': 'abc'}, returned_locals)

        # also make sure that injected variables are returned
        returned_locals = template.viewfunc({'injected': 'anything'})
        self.assertEquals({'x': 1, 'y': 'abc', 'injected': 'anything'}, returned_locals)

        # unless we delete things
        templatefp = template_fileobj("""
        x = 1
        y = 'abc'
        del injected
        del y
        ----
        <strong>this is HTML</strong>
        """)

        template = engine.parse(templatefp)

        returned_locals = template.viewfunc({'injected': 'anything'})
        self.assertEquals({'x': 1}, returned_locals)


class CompilerTest(unittest.TestCase):
    """
    The goal is not to thoroughly test the compile() built-in
    method, but to ensure that certain aspects of its behavior
    which Keystone relies upon work as expected.
    """

    def test_basic(self):
        viewcode_str = dedent("""
        x = 1
        y = 2
        """)

        engine = RenderEngine(MockApp())
        viewcode, viewglobals = engine.compile(viewcode_str, 'filename')

        self.assertTrue('__builtins__' in viewglobals, 'view globals did not contain builtins')
        self.assertTrue(iscode(viewcode), 'viewcode was not a code object')

    def test_invalid_syntax(self):
        viewcode_str = dedent("""
        x = 1
        y =
        """)

        engine = RenderEngine(MockApp())
        self.assertRaises(SyntaxError, engine.compile, viewcode_str, 'filename')

    def test_import_detection(self):
        import sys
        import keystone.http

        engine = RenderEngine(MockApp())

        viewcode_str = dedent("""
        import sys
        """)
        viewcode, viewglobals = engine.compile(viewcode_str, 'filename')
        self.assertTrue('sys' in viewglobals, 'view globals did not contain imported modules')
        self.assertTrue(viewglobals['sys'] is sys, 'view globals got a different version of sys')

        viewcode_str = dedent("""
        from sys import version_info
        """)
        viewcode, viewglobals = engine.compile(viewcode_str, 'filename')
        self.assertTrue('version_info' in viewglobals, 'view globals did not contain from foo imported modules')
        self.assertTrue(viewglobals['version_info'] is sys.version_info, 'view globals got a different version of version_info')

        viewcode_str = dedent("""
        from sys import version_info as vi
        """)
        viewcode, viewglobals = engine.compile(viewcode_str, 'filename')
        self.assertTrue('vi' in viewglobals, 'view globals did not contain from foo import as\'d modules')
        self.assertTrue(viewglobals['vi'] is sys.version_info, 'view globals got a different version of vi')

        viewcode_str = dedent("""
        from keystone.http import *
        """)
        viewcode, viewglobals = engine.compile(viewcode_str, 'filename')
        for name in keystone.http.__all__:
            self.assertTrue(name in viewglobals, 'view globals did not contain from foo import * (%s)')


    def test_non_existent_import_doesnt_fail_during_compile(self):
        viewcode_str = dedent("""
        import froobulator
        """)

        engine = RenderEngine(MockApp())
        viewcode, viewglobals = engine.compile(viewcode_str, 'filename')

        # this passes if no exception is raised
        #
        # however, this will pass for the wrong reasons if a module
        # named "froobulator" is on sys.path. I'm OK with that.

class TestRenderEngine(unittest.TestCase):
    """
    This tests the rendering-related (as opposed to compilation or parsing)
    functions of RenderEngine.
    """

    def setUp(self):
        here = os.path.abspath(os.path.dirname(__file__))
        self.app_dir = os.path.join(here, 'app_dir')

        shutil.rmtree(self.app_dir, ignore_errors=True)
        os.makedirs(self.app_dir)

    def tearDown(self):
        shutil.rmtree(self.app_dir, ignore_errors=True)

    def test_get_template(self):
        with file(os.path.join(self.app_dir, 'tmpl.ks'), 'w') as fp:
            fp.write(dedent("""
            # this is python
            ----
            <strong>this is HTML</strong>
            """))

        engine = RenderEngine(MockApp(self.app_dir))
        template = engine.get_template('tmpl.ks')

        self.assertTrue(isinstance(template, Template), 'template is not a Template')
        self.assertEquals(template.name, 'tmpl.ks', 'template name is wrong')
        self.assertTrue(template is engine.get_template('tmpl.ks'), 'templates are not identical')

        self.assertRaises(TemplateNotFound, engine.get_template, 'missing.ks')

    def test_refresh_on_file_modification(self):
        engine = RenderEngine(MockApp(self.app_dir))
        filename = os.path.join(self.app_dir, 'tmpl.ks')

        with file(filename, 'w') as fp:
            fp.write(dedent("""
            # this is python
            ----
            <strong>this is HTML</strong>
            """))

        template1 = engine.get_template('tmpl.ks')

        # modify the atime and mtime on the file if
        # possible, otherwise just wait a bit and
        # then write to the file again
        if callable(getattr(os, 'utime')):
            os.utime(filename, (time.time() + 2, time.time() + 2))
        else:
            time.sleep(1)
            with file(os.path.join(self.app_dir, 'tmpl.ks'), 'w') as fp:
                fp.write(dedent("""
                # this is python
                ----
                <strong>this is HTML</strong>
                """))

        template2 = engine.get_template('tmpl.ks')

        self.assertTrue(template1 is not template2, 'template should not be the same after file changes')

    def test_full_render(self):
        engine = RenderEngine(MockApp(self.app_dir))
        filename = os.path.join(self.app_dir, 'tmpl.ks')

        with file(filename, 'w') as fp:
            fp.write(dedent("""
            <strong>this is {{name}}</strong>
            """))

        t = engine.get_template('tmpl.ks')
        output = engine.render(t, {'name': 'HTML'})
        if callable(getattr(output, 'next', None)):
            output = '\n'.join(output)

        self.assertEquals('<strong>this is HTML</strong>', output)

