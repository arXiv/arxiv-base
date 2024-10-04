import json
import os

from flask import Flask, redirect, request, session, url_for, jsonify
from ..oidc_idp import ArxivOidcIdpClient
from ...user_claims import ArxivUserClaims
from ...auth.decorators import scoped
from ...auth.middleware import AuthMiddleware
from ....base.middleware import wrap
from ...auth import Auth

import requests

KEYCLOAK_SERVER_URL = os.environ.get('KEYCLOAK_SERVER_URL', 'https://keycloak-service-874717964009.us-central1.run.app')
#REALM_NAME = 'arxiv'
#CLIENT_ID = 'smoke-test'
#CLIENT_SECRET = 'your-client-secret'
#REDIRECT_URI = 'http://localhost:5101/callback'

# def _is_admin (session: dict, *args, **kwargs) -> bool:
#     try:
#         uid = session.user.user_id
#     except:
#         return False
#     return db_session.scalar(
#         select(TapirUser)
#         .filter(TapirUser.flag_edit_users == 1)
#         .filter(TapirUser.user_id == uid)) is not None
#
# admin_scoped = scoped(
#     required=None,
#     resource=None,
#     authorizer=_is_admin,
#     unauthorized=None
# )

class ToyFlask(Flask):
    def __init__(self, *args: [], **kwargs: dict):
        super().__init__(*args, **kwargs)
        self.secret_key = 'secret'  # Replace with a secure secret key
        self.idp = ArxivOidcIdpClient("http://localhost:5101/callback",
                                      scope=["openid"],
                                      server_url=KEYCLOAK_SERVER_URL,
                                      client_id="smoke-test"
                                      )

app = ToyFlask(__name__)

@app.route('/')
def home():
    session.clear()
    return redirect('/login')

@app.route('/login')
def login():
    return redirect(app.idp.login_url)


@app.route('/callback')
def callback():
    # Get the authorization code from the callback URL
    code = request.args.get('code')
    user_claims = app.idp.from_code_to_user_claims(code)

    if user_claims is None:
        session.clear()
        return 'Something is wrong'

    print(user_claims._claims)
    session["access_token"] = user_claims.to_arxiv_token_string
    return 'Login successful!'


@app.route('/logout')
def logout():
    # Clear the session and redirect to home
    session.clear()
    return redirect(url_for('home'))


@app.route('/protected')
def protected():
    arxiv_access_token = session.get('access_token')
    if not arxiv_access_token:
        return redirect(app.idp.login_url)
    claims = ArxivUserClaims(json.loads(arxiv_access_token))
    if claims.is_admin:
        return jsonify({'message': 'Token is valid', 'claims': json.dumps(claims._claims)})
    return jsonify({'message': 'Not admin', 'claims': json.dumps(claims._claims)})



def create_app():
    return app

if __name__ == '__main__':
    os.environ['JWT_SECRET'] = 'secret'
    Auth(app)
    wrap(app, [AuthMiddleware])
    app.run(debug=True, host='0.0.0.0', port=5101)
