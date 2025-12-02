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


def create_app():
    app = Flask(__name__)

    # ───────────────────────────────────────────────────────
    # LOAD CONFIG
    # ───────────────────────────────────────────────────────
    app_settings = os.getenv("APP_SETTINGS", "project.config.DevelopmentConfig")
    app.config.from_object(app_settings)

    # ───────────────────────────────────────────────────────
    # LOGGER
    # ───────────────────────────────────────────────────────
    logger = get_logger("flask_app", app.config.get("LOG_LEVEL"))
    logger.info(f"Starting app with config: {app_settings}")
    app.logger_instance = logger

    # ───────────────────────────────────────────────────────
    # CORS
    # ───────────────────────────────────────────────────────
    # Các origin mặc định (local + prod)
    default_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://develop.d2u6muixbujakf.amplifyapp.com",
        "https://codeland.khanhjp.site",
    ]

    # Cho phép bổ sung origin qua env FRONTEND_ORIGINS (ngăn cách bằng dấu phẩy)
    extra_origins = os.getenv("FRONTEND_ORIGINS", "")
    if extra_origins:
        default_origins.extend(
            [o.strip() for o in extra_origins.split(",") if o.strip()]
        )

    CORS(
        app,
        resources={r"/api/*": {"origins": default_origins}},
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

    logger.info("Database and extensions initialized")

    # ───────────────────────────────────────────────────────
    # REGISTER BLUEPRINTS VỚI PREFIX /api
    # ───────────────────────────────────────────────────────
    from project.api.auth import auth_blueprint
    from project.api.users import users_blueprint
    from project.api.exercises import exercises_blueprint
    from project.api.scores import scores_blueprint

    app.register_blueprint(auth_blueprint, url_prefix="/api/auth")
    logger.info("Auth blueprint registered at /api/auth")

    app.register_blueprint(users_blueprint, url_prefix="/api/users")
    logger.info("Users blueprint registered at /api/users")

    app.register_blueprint(exercises_blueprint, url_prefix="/api/exercises")
    logger.info("Exercises blueprint registered at /api/exercises")

    app.register_blueprint(scores_blueprint, url_prefix="/api/scores")
    logger.info("Scores blueprint registered at /api/scores")

    # ───────────────────────────────────────────────────────
    # REQUEST LOGGING
    # ───────────────────────────────────────────────────────
    setup_request_logging(app)
    logger.info("Request logging middleware setup completed")

    # ───────────────────────────────────────────────────────
    # SHELL CONTEXT
    # ───────────────────────────────────────────────────────
    @app.shell_context_processor
    def ctx():
        return {"app": app, "db": db}

    logger.info("Application setup completed successfully")
    return app
