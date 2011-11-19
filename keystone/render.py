__all__ = ('Template', 'RenderEngine', 'InvalidTemplate')

import jinja2
import os, os.path
import re
import sys

class InvalidTemplate(Exception):
    """Indicates that a template has more than one separator."""

class Template(object):
    """Holds a template body, viewfunc, mtime, and valid methods."""

    def __init__(self, viewfunc, body, valid_methods):
        self.viewfunc = viewfunc
        self.body = body
        self.valid_methods = valid_methods
        self.mtime = None
        self.name = None

class RenderEngine(object):
    def __init__(self, app):
        self.app = app
        self.templates = {}
        self.env = jinja2.Environment(
            loader=jinja2.FunctionLoader(self.get_template_body))

    def _parse_methods(self, fileobj, viewlines):
        valid_methods = set(['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'HEAD'])
        methodscomment = re.compile(r'^# Methods: ([A-Za-z, ]+)')
        for line in viewlines:
            match = methodscomment.match(line.lstrip())
            if match:
                methods = match.group(1)
                methods = [m.strip() for m in methods.split(',')]
                for method in methods:
                    if method not in valid_methods:
                        warnings.warn('Invalid method "%s" in %s' % (method, fileobj.name))
                return [m for m in methods if m in valid_methods]

        return ['GET']

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
                viewfunc=None,
                body=''.join(first),
                valid_methods=['GET'])

        valid_methods = self._parse_methods(fileobj, first)

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
            body=''.join(second),
            valid_methods=valid_methods)

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
            template = self.parse(file(filename, 'r+b'))
            template.mtime = mtime
            template.name = name
            self.templates[name] = template

    def valid_methods(self, name):
        self.refresh_if_needed(name)
        template = self.templates[name]
        return template.valid_methods

    def render(self, template, viewglobals):
        """Template rendering entry point."""
        jinja_template = self.env.get_template(template.name)
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

