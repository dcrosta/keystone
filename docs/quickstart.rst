Keystone Quickstart
===================

This quickstart guide is designed for those familiar with Python and web
programming concepts. If you're new to Python or web programming, you may be
interested in :doc:`tutorial`, which introduces these concepts more gently.

Keystone Main Idea
------------------

In Keystone, rather than separating view code from template code, both are
stored and edited together in ``.ks`` files. The Python section comes first
(since the view code executes first), followed by four hyphens as a
separator (``----``), followed by `Jinja <http://jinja.pocoo.org/>`_
template code. Here's a relatively complete example:

.. code-block:: html+jinja

    import db

    from wtforms import *
    from wtforms.validators import *

    class SignupForm(Form):
        username = TextField(validators=[Required()])
        email = TextField(validators=[Email()])
        password = PasswordField(validators=[Length(min=6)])
        confirm_password = PasswordField(validators=[EqualTo('password')])

        def validate_username(form, field):
            if not db.username_available(form.username.data):
                raise ValidationError('Username taken')

    if request.method == 'POST':
        form = SignupForm(request.form)
        if form.validate():
            db.create_user(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data,
            )
    else:
        form = SignupForm()
    ----
    {% macro field_row(field) %}
    <tr>
        <td>{{field.label}}</td>
        <td>{{field}}
            {% if field.errors %}
            <ul class="errors">
                {% for err in field.errors %}
                <li>{{err}}</li>
                {% endfor %}
            </ul>
            {% endif %}
        </td>
    {% endmacro %}
    <!doctype html>
    <html>
        <head>
            <title>My Great Site</title>
            <link rel="stylesheet" href="/static/style.css"/>
        </head>
        <body>
            <div id="main">
                <h1>Sign Up!</h1>
                <form method="POST">
                    <table>
                        {% for field in form %}
                        {{field_row(field)}}
                        {% endfor %}
                        <tr>
                            <td>&nbsp;</td>
                            <td><input type="submit"/></td>
                        </tr>
                    </table>
                </form>
            </div>
        </body>
    </html>

Any static files found within the Keystone application directory are served
verbatim. Files whose detected content type matches ``text/*`` (including
the rendered output of ``.ks`` templates) are served with charset utf-8 and
an appropriate MIME type in the HTTP Content-Type header.

.. note::
   Files with extensions ``.ks``, ``.py``, ``.pyc``, and ``.pyo`` are never
   served as static files by Keystone.


Keystone and Python
-------------------

Keystone compiles and caches Python bytecode for the view section and
executes it for each request. The application directory is added to the
Python import path when Keystone starts up, so any Python modules or
packages defined within the application are available for import.

All Python code in the ``.ks`` file is executed on each request, including
things which would normally be executed only once by the Python virtual
machine, like function and class definitions. Therefore, it is advisable to
avoid defining classes or functions within ``.ks`` files. Instead, most
Python code (particularly anything that may be shared between different
views, such as class and function definitions, database connections, etc)
should be implemented in ordinary Python modules or packages.

When a change in any ``.ks`` file's mtime is detected, cached bytecode is
discarded and the file is re-parsed. Python modules imported by view code
are not re-imported unless the Python process running Keystone is restarted.

When Keystone is started, if ``startup.py`` exists within the application
directory, it is imported. This is where application-level initialization
code should go (for instance, setting up database connection pools). Like
any Python module imported from within Keystone views, the ``startup``
module is imported (and thus executed) only once.


Keystone and Jinja
------------------

All in-scope Python variables, including :doc:`/viewvars` set by Keystone
itself, are passed into the Jinja2 context during rendering. However, it is
not advised to maipulate the :doc:`/viewvars` from within template code, as
this will lead to difficult-to-maintain code.

Keystone implements a special Jinja2 template loader to load templates from
``.ks`` files. In addition, it can load plain HTML files (with extension
``.html``) found within the application directory (e.g. for template
inheritance).

If a view's template extends the template of another view, the parent view's
Python code `is not` executed during the request; thus if you require
certain template variables in a parent template, the child view must set
them itself.

