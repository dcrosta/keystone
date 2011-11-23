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


__all__ = ('Template', 'RenderEngine', 'InvalidTemplate')

import jinja2
import os, os.path
import re
import sys

class InvalidTemplate(Exception):
    """Indicates that a template has more than one separator."""

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

class RenderEngine(object):
    def __init__(self, app):
        self.app = app
        self.templates = {}
        self.env = jinja2.Environment(
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

        if not second:
            return Template(
                viewfunc=lambda x: x,
                body=''.join(first))

        safe_app_dir = self.app.app_dir.replace('"', '\\"')
        first.insert(0, 'import sys\n')
        first.insert(1, 'if "%s" not in sys.path: sys.path.append("%s")\n' % (safe_app_dir, safe_app_dir))

        # generate the view function
        viewcode = compile(''.join(first), fileobj.name, 'exec')
        def viewfunc(viewglobals):
            context = viewglobals.copy()
            exec viewcode in {}, context
            return context

        return Template(
            viewfunc=viewfunc,
            body=''.join(second))

        return viewfunc, ''.join(second)

    def refresh_if_needed(self, name):
        """Update the cached modification time, view func,
        and template body for the .ks template at the given
        path relative to the app_dir."""
        filename = os.path.abspath(os.path.join(self.app.app_dir, name))
        mtime = os.stat(filename).st_mtime
        template = self.templates.get(name)

        if template is None or template.mtime < mtime:
            lastmtime = mtime
            template = self.parse(file(filename, 'rb'))
            template.mtime = mtime
            template.name = name
            self.templates[name] = template

    def render(self, template, viewglobals):
        """Template rendering entry point."""
        jinja_template = self.env.get_template(template.name)
        viewglobals.update(template.urlparams)
        return jinja_template.generate(**template.viewfunc(viewglobals))

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

