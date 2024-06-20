# ``arxiv-auth`` Library

This package provides a Flask add on and other code for working with arxiv
authenticated users in arXiv services.

Housing these components in arxiv-base ensures that users
and sessions are represented and manipulated consistently. The login+logout, user
accounts(TBD), API client registry(TBD), and authenticator(TBD) services all
rely on this package.

# Quick start
For use-cases to check if a request is from an authenticated arxiv user, do the
following:

1. Add arxiv-base to your dependencies
2. Install :class:`arxiv.auth.auth.Auth` onto your application. This adds a
   function called for each request to Flask that adds an instance of
   :class:`arxiv.auth.domain.Session` at ``flask.request.auth`` if the client is
   authenticated.
3. Add to the ``flask.config`` to setup :class:`arxiv_auth.auth.Auth` and
   related classes
   
Here's an example of how you might do #2 and #3:
```
   from flask import Flask
   from arxiv.base import Base
   from arxiv.auth.auth import auth

   app = Flask(__name__)
   Base(app)

   # config settings required to use legacy auth 
   app.config['CLASSIC_SESSION_HASH'] = '{hash_private_secret}'
   app.config['CLASSIC_DB_URI'] = '{your_sqlalchemy_db_uri_to_legacy_db'}
   app.config['SESSION_DURATION'] = 36000
   app.config['CLASSIC_COOKIE_NAME'] = 'tapir_session'

   auth.Auth(app)    # <- Install the Auth to get auth checks and request.auth

   @app.route("/")
   def are_you_logged_in():
       if request.auth is not None:
           return "<p>Hello, You are logged in.</p>"
       else:
           return "<p>Hello unknown client.</p>"
```

# Middleware

In during NG there was middleware for arxiv-auth that could be used in NGINX to
do the authentication there. As of 2023 it is not in use.

See :class:`arxiv.auth.auth.middleware.AuthMiddleware`

If you are not deploying this application in the cloud behind NGINX (and
therefore will not support sessions from the distributed store), you do not
need the auth middleware.
