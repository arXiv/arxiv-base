"""test app."""

import sys
sys.path.append('./arxiv')

from flask import Flask
from arxiv_users import auth, legacy

app = Flask('test')
legacy.create_all()
