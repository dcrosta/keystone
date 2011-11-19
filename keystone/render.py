import os

import jinja2

cache = {}


def jinja(filename, template, context):
    template = jinja2.Template(''.join(template))
    template.filename = filename
    return template.generate(context)

def render_keystone(fileobj, adapter):
    filename = fileobj.name
    mtime = os.stat(filename).st_mtime
    expiry, viewfunc, template = cache.get(filename, (None, None, None))

    if expiry is None or mtime > expiry:
        print "reparsing"
        expiry = mtime
        viewfunc, template = parse_ks(fileobj)
        cache[filename] = (expiry, viewfunc, template)

    context = viewfunc()
    return adapter(filename, template, context)

class InvalidTemplate(Exception): pass

def parse_ks(fileobj):
    first, second = [], []
    active = first

    for line in fileobj:
        if line.strip() == '----':
            if active is second:
                raise InvalidTemplate('too many pages')
            active = second
        else:
            active.append(line)

    if not second:
        return lambda: {}, first

    # fix line numbers in template, for error reporting
    for line in first:
        second.insert(0, '\n')

    # and one more for the separator
    second.insert(0, '\n')

    # generate the view function
    viewcode = compile(''.join(first), fileobj.name, 'exec')
    def viewfunc():
        context = {}
        viewglobals = {}
        exec viewcode in viewglobals, context
        return context

    return viewfunc, second

