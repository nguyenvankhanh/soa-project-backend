import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_debugtoolbar import DebugToolbarExtension
from flask_cors import CORS
from flask_migrate import Migrate

from project.logger import get_logger
from project.middleware import setup_request_logging

# ───────────────────────────────────────────────────────────
# GLOBAL EXTENSIONS
# ───────────────────────────────────────────────────────────
db = SQLAlchemy()
bcrypt = Bcrypt()
migrate = Migrate()
toolbar = DebugToolbarExtension()


# ───────────────────────────────────────────────────────────
# APP FACTORY
# ───────────────────────────────────────────────────────────
def create_app():
    app = Flask(__name__)

    # Load config
    app_settings = os.getenv("APP_SETTINGS", "project.config.DevelopmentConfig")
    app.config.from_object(app_settings)

    # Logger
    logger = get_logger("flask_app", app.config.get("LOG_LEVEL"))
    logger.info(f"Starting app with config: {app_settings}")

    # ───────────────────────────────────────────────────────
    # CORS (chỉ cho /api/*, origin cụ thể + cho phép credentials)
    # ───────────────────────────────────────────────────────
    frontend_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        # domain Amplify
        "https://develop.d2u6muixbujakf.amplifyapp.com",
        # custom domain đã map vào Amplify
        "https://codeland.khanhjp.site",
    ]

    CORS(
        app,
        resources={r"/api/*": {"origins": frontend_origins}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )

    # ───────────────────────────────────────────────────────
    # INIT EXTENSIONS
    # ───────────────────────────────────────────────────────
    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    toolbar.init_app(app)

    logger.info("DB + extensions initialized")

    # ───────────────────────────────────────────────────────
    # IMPORT & REGISTER BLUEPRINTS
    # ───────────────────────────────────────────────────────
    from project.api.auth import auth_blueprint
    from project.api.users import users_blueprint
    from project.api.exercises import exercises_blueprint
    from project.api.scores import scores_blueprint

    # Thêm prefix /api cho đúng với frontend
    app.register_blueprint(auth_blueprint, url_prefix="/api/auth")
    logger.info("Auth blueprint registered")

    app.register_blueprint(users_blueprint, url_prefix="/api/users")
    logger.info("Users blueprint registered")

    app.register_blueprint(exercises_blueprint, url_prefix="/api/exercises")
    logger.info("Exercises blueprint registered")

    app.register_blueprint(scores_blueprint, url_prefix="/api/scores")
    logger.info("Scores blueprint registered")

    # ───────────────────────────────────────────────────────
    # REQUEST LOGGING
    # ───────────────────────────────────────────────────────
    setup_request_logging(app)
    logger.info("Request logging initialized")

    # Shell context
    @app.shell_context_processor
    def make_shell_context():
        return {"app": app, "db": db}

    return app
