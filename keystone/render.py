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


__all__ = ('return_response', 'template_filter', 'Template',
           'RenderEngine', 'InvalidTemplate')

import compiler
from compiler.ast import Import, From
import jinja2
import os, os.path

class InvalidTemplate(Exception):
    """Indicates that a template has more than one separator."""

class StopViewFunc(Exception):
    """Raised by return_response() to prevent templat rendering."""
    def __init__(self, body):
        self.body = body

def return_response(body):
    """Passed into viewlocals to allow view code to immediately
    respond, bypassing templates (e.g. to return binary content
    from a file or database).
    """
    raise StopViewFunc(body)

def template_filter(func):
    """Register a Jinja2 filter function. The name of the function
    will become the name of the filter in the template environment.
    """
    # by the time this is called (from within Python modules in the
    # application, the RenderEngine, and thus the Jinja Environment,
    # have already been created
    jinja_env.filters[func.__name__] = func
    return func

class Template(object):
    """Holds a template body, viewfunc, mtime, and valid methods."""

    def __init__(self, viewfunc, body, mtime=None, name=None):
        self.viewfunc = viewfunc
        self.body = body
        self.mtime = mtime
        self.name = name
        self.urlparams = {}

    def copy(self):
        return Template(self.viewfunc, self.body, self.mtime, self.name)

jinja_env = None
class RenderEngine(object):
    def __init__(self, app):
        self.app = app
        self.templates = {}

        global jinja_env
        jinja_env = jinja2.Environment(
            loader=jinja2.FunctionLoader(self.get_template_body))

    def parse(self, fileobj):
        """Parse a .ks file into a view callable and a template
        string. If there is no separator ("----") then the first
        part is treated as the template, and the view callable is
        a no-op.
        """
        first, second = [], []
        active = first

        for lineno, line in enumerate(fileobj):
            if line.strip() == '----':
                if active is second:
                    raise InvalidTemplate(
                        'Line %d: separator already seen on line %d' % (lineno, len(first)))
                active = second
            else:
                active.append(line)

        if active is first:
            return Template(
                viewfunc=lambda x: x,
                body=''.join(first))

        viewcode, viewglobals = self.compile(''.join(first), fileobj.name)
        def viewfunc(viewlocals):
            exec viewcode in viewglobals, viewlocals
            return viewlocals

        return Template(
            viewfunc=viewfunc,
            body=''.join(second))

    def compile(self, viewcode_str, filename):
        """Compile the view code and return a code object
        and dictionary of globals needed by the code object.
        """
        viewcode = compile(viewcode_str, filename, 'exec')

        # scan top-level code only for "import foo" and
        # "from foo import *" and "from foo import bar, baz"
        viewglobals = {'__builtins__': __builtins__}
        for stmt in compiler.parse(viewcode_str).node:
            if isinstance(stmt, Import):
                modname, asname = stmt.names[0]
                if asname is None:
                    asname = modname
                viewglobals[asname] = __import__(modname)
            elif isinstance(stmt, From):
                fromlist = [x[0] for x in stmt.names]
                module = __import__(stmt.modname, {}, {}, fromlist)
                for name, asname in stmt.names:
                    if name == '*':
                        for starname in getattr(module, '__all__', dir(module)):
                            viewglobals[starname] = getattr(module, starname)
                    else:
                        if asname is None:
                            asname = name
                        viewglobals[asname] = getattr(module, name)

        return viewcode, viewglobals

    def refresh_if_needed(self, name):
        """Update the cached modification time, view func,
        and template body for the .ks template at the given
        path relative to the app_dir."""
        filename = os.path.abspath(os.path.join(self.app.app_dir, name))
        mtime = os.stat(filename).st_mtime
        template = self.templates.get(name)

        if template is None or template.mtime < mtime:
            template = self.parse(file(filename, 'rb'))
            template.mtime = mtime
            template.name = name
            self.templates[name] = template

    def render(self, template, viewlocals):
        """Template rendering entry point."""
        jinja_template = jinja_env.get_template(template.name)
        viewlocals.update(template.urlparams)
        try:
            return jinja_template.generate(**template.viewfunc(viewlocals))
        except StopViewFunc, stop:
            return stop.body

    def get_template(self, name):
        self.refresh_if_needed(name)
        return self.templates.get(name)

    def get_template_body(self, name):
        """Jinja2 template loader function."""
        self.refresh_if_needed(name)
        template = self.templates[name]
        cached_mtime = template.mtime

        def uptodate():
            self.refresh_if_needed(name)
            template = self.templates[name]
            return template and template.mtime and cached_mtime and template.mtime <= cached_mtime

        return template.body, name, uptodate

