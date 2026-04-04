from flask import Flask, session, redirect, url_for
import os

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-in-prod')

    from .routes.main import main
    from .routes.campaigns import campaigns
    from .routes.npcs import npcs
    from .routes.locations import locations
    app.register_blueprint(main)
    app.register_blueprint(campaigns)
    app.register_blueprint(npcs)
    app.register_blueprint(locations)

    app.jinja_env.globals['enumerate'] = enumerate

    return app
