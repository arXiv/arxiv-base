import os

from flask import Flask, redirect, request, session, url_for, jsonify
from ..oidc_idp import ArxivOidcIdpClient

import requests

KEYCLOAK_SERVER_URL = os.environ.get('KEYCLOAK_SERVER_URL', 'localhost')
#REALM_NAME = 'arxiv'
#CLIENT_ID = 'arxiv-user'
#CLIENT_SECRET = 'your-client-secret'
#REDIRECT_URI = 'http://localhost:5000/callback'

class ToyFlask(Flask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.secret_key = 'secret'  # Replace with a secure secret key
        self.idp = ArxivOidcIdpClient("http://localhost:5000/callback",
                                      server_url=KEYCLOAK_SERVER_URL)

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

    # Exchange the authorization code for an access token
    token_response = requests.post(
        app.idp.token_url,
        data={
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': app.idp.redirect_uri,
            'client_id': app.idp.client_id,
        }
    )

    if token_response.status_code != 200:
        session.clear()
        return 'Something is wrong'

    # Parse the token response
    token_json = token_response.json()
    access_token = token_json.get('access_token')
    refresh_token = token_json.get('refresh_token')

    # Store tokens in session (for demonstration purposes)
    session['access_token'] = access_token
    session['refresh_token'] = refresh_token

    print(app.idp.validate_token(access_token))
    return 'Login successful!'


@app.route('/logout')
def logout():
    # Clear the session and redirect to home
    session.clear()
    return redirect(url_for('home'))


@app.route('/protected')
def protected():
    access_token = session.get('access_token')
    if not access_token:
        return redirect(app.idp.login_url)

    decoded_token = app.idp.validate_token(access_token)
    if not decoded_token:
        return jsonify({'error': 'Invalid token'}), 401

    return jsonify({'message': 'Token is valid', 'token': decoded_token})


def create_app():
    return app

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
