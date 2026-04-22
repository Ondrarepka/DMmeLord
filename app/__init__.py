from flask import Flask, session
import os

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-in-prod')

    from .routes.main import main, get_campaigns
    from .routes.campaigns import campaigns
    from .routes.npcs import npcs
    from .routes.locations import locations
    from .routes.sessions import sessions_bp
    from .routes.calendar import calendar
    from .routes.economy import economy
    app.register_blueprint(main)
    app.register_blueprint(campaigns)
    app.register_blueprint(npcs)
    app.register_blueprint(locations)
    app.register_blueprint(sessions_bp)
    app.register_blueprint(calendar)
    app.register_blueprint(economy)

    app.jinja_env.globals['enumerate'] = enumerate

    @app.context_processor
    def inject_globals():
        return {
            'campaigns': get_campaigns(),
            'campaign': session.get('campaign', ''),
        }

    return app
