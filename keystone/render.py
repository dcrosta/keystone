__all__ = ('RenderEngine', 'InvalidTemplate')

import jinja2
import os, os.path
import sys

class InvalidTemplate(Exception):
    """Indicates that a template has more than one separator."""

class RenderEngine(object):
    def __init__(self, app):
        self.app = app
        self.templates = {}
        self.env = jinja2.Environment(
            loader=jinja2.FunctionLoader(self.get_template))

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
            return lambda viewglobals: viewglobals, ''.join(first)

        safe_app_dir = self.app.app_dir.replace('"', '\\"')
        first.insert(0, 'import sys\n')
        first.insert(1, 'if "%s" not in sys.path: sys.path.append("%s")\n' % (safe_app_dir, safe_app_dir))

        # generate the view function
        viewcode = compile(''.join(first), fileobj.name, 'exec')
        def viewfunc(viewglobals):
            context = viewglobals.copy()
            exec viewcode in {}, context
            return context

        return viewfunc, ''.join(second)

    def refresh_if_needed(self, name):
        """Update the cached modification time, view func,
        and template body for the .ks template at the given
        path relative to the app_dir."""
        filename = os.path.abspath(os.path.join(self.app.app_dir, name))
        mtime = os.stat(filename).st_mtime
        lastmtime, viewfunc, template = self.templates.get(name, (None, None, None))

        if lastmtime is None or mtime > lastmtime:
            lastmtime = mtime
            viewfunc, template = self.parse(file(filename, 'r+b'))
            self.templates[name] = (lastmtime, viewfunc, template)

    def render(self, name, viewglobals):
        """Template rendering entry point."""
        self.refresh_if_needed(name)
        mtime, viewfunc, template = self.templates[name]
        return self.env.get_template(name).generate(**viewfunc(viewglobals))

    def get_template(self, name):
        """Jinja2 template loader function."""
        self.refresh_if_needed(name)
        cached_mtime, _, template = self.templates.get(name, (None, None, None))

        def uptodate():
            self.refresh_if_needed(name)
            mtime, _, _ = self.templates.get(name, (None, None, None))
            return cached_mtime and mtime and mtime <= cached_mtime

        return template, name, uptodate

