from flask import Flask

__version__ = "0.9.0"


def make_flask():
    flask_app = Flask(__name__)
    return flask_app


flask_app = make_flask()
