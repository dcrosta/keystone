# Keystone Is...

* An easy-to learn Python web framework
* That puts templates first
* That builds on [high](http://werkzeug.pocoo.org) [quality](http://jinja.pocoo.org) components
* That will only take minutes to learn
* That encourages best practices

## Keystone in 30 seconds or less

    $ mkdir helloworld
    $ cat << EOF > helloworld/index.ks
    name = 'World'
    ----
    <!doctype html>
    <html>
      <head>
        <title>Welcome to Keystone</title>
      </head>
      <body>
        <p>Hello, {{name}}</p>
      </body>
    </html>
    EOF
    $ keystone helloworld
    $ open http://localhost:5000/

![helloworld.png](http://f.cl.ly/items/2r400y3r2x3P3F1x3u22/helloworld.png)

----

![buildstatus](https://secure.travis-ci.org/dcrosta/keystone.png) at
[Travis-CI](http://travis-ci.org/#!/dcrosta/keystone)
