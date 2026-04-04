from flask import Flask, session, redirect, url_for
import os

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-in-prod')

    from .routes.main import main
    from .routes.campaigns import campaigns
    app.register_blueprint(main)
    app.register_blueprint(campaigns)

    return app
