Installing Keystone
===================

Keystone is a `Python <http://www.python.org/>`_ application, so you'll need
to have Python installed on your computer. The exact steps to do so will
depend on your operating system, and are documented on `the Python downloads
page <http://www.python.org/download/>`_. Keystone requires Python 2.5 or
greater (and suggests you use the latest 2.x release available). Keystone
does not yet support Python 3.

Once you have Python installed, open the Terminal (Windows users: use
"Command Prompt"), and install Keystone:

.. code-block:: bash

    $ pip install Keystone

If you get a permission error, you may need to re-run the install command
using ``sudo``, which will prompt you for your password.

Even though you haven't yet begun to build your web site, you can actually
run Keystone using the ``keystone`` command, which will start a web server at
`http://localhost:5000/ <http://localhost:5000/>`_.

.. code-block:: bash

    $ keystone
     * Running on http://0.0.0.0:5000/
     * Restarting with reloader

Those two lines indicate that the web server has started and is waiting for
the first request. Each time your browser requests a page, the Keystone web
server will print a line that looks something like this:

.. code-block:: bash

    127.0.0.1 - - [22/Nov/2011 16:55:10] "GET / HTTP/1.1" 404 -

This shows, from left to right, the IP address of the computer that made the
request ("127.0.0.1" is a special value that indicates the computer you're
currently on), the date and time of the request, the request line (which
page the browser is asking for), and the status code of the response.
Normally we want to see a "200" status code, which indicates the request was
successfully served; in this case, "404" indicates that no page matching "/"
was found, which should not be surprising as we have not yet built any pages
for the web site.

But I digress; the fact that we can see these messages in the Terminal, and
that our browser gets a "Not found" message means that Keystone is working,
and we're ready to begin building websites.

