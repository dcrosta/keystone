Advanced Topics
===============


Returning Binary Data
---------------------

By default, Keystone assumes a `Content-Type` of ``text/html`` for responses
generated from ``.ks`` views, and requires a valid template section which
must produce UTF-8 output. You can override this behavior on a per-view
basis with :func:`return_response`, which bypasses the template
entirely.

.. code-block:: keystone

    fp = file('/tmp/generated_file.pdf', 'rb')
    header('Content-Type', 'application/pdf')
    return_response(fp)
    ----

The `body` argument to :func:`return_response` may be a string or any
iterable type (list, generator, file object) which yields strings.

.. note::

   As of Keystone |version|, you must still have a template section in your
   ``.ks`` file when using :func:`return_response()`, though it may be
   empty. This may change in a future version of Keystone.

