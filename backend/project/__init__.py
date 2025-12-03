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
toolbar = DebugToolbarExtension()
migrate = Migrate()
bcrypt = Bcrypt()
db = SQLAlchemy()


def _build_cors_origins():
    """
    Tạo danh sách origin được phép CORS.

    - Có sẵn: localhost (dev), Amplify domain, custom domain.
    - Có thể bổ sung thêm bằng env CORS_EXTRA_ORIGINS (phân tách bằng dấu phẩy).
    """
    origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        # frontend Amplify
        "https://develop.d2u6muixbujakf.amplifyapp.com",
        # custom domain bạn vừa add
        "https://codeland.khanhjp.site",
    ]

    extra = os.getenv("CORS_EXTRA_ORIGINS")
    if extra:
        origins.extend(o.strip() for o in extra.split(",") if o.strip())

    return origins


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
    logger.info(f"Starting application with config: {app_settings}")
    logger.info(f"Starting application with Log Level: {app.config.get('LOG_LEVEL')}")

    # middleware setup_request_logging hiện đang dùng app.logger_instance
    app.logger_instance = logger

    # ───────────────────────────────────────────────────────
    # ENABLE CORS (chỉ cho các route /api/*)
    # ───────────────────────────────────────────────────────
    CORS(
        app,
        resources={r"/api/*": {"origins": _build_cors_origins()}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )

    # ───────────────────────────────────────────────────────
    # ATTACH EXTENSIONS
    # ───────────────────────────────────────────────────────
    db.init_app(app)
    toolbar.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)

    logger.info("Database and extensions initialized")

    # ───────────────────────────────────────────────────────
    # REGISTER BLUEPRINTS
    # (giữ đúng prefix /api/... cho khớp frontend)
    # ───────────────────────────────────────────────────────
    from project.api.users import users_blueprint
    from project.api.auth import auth_blueprint
    from project.api.exercises import exercises_blueprint
    from project.api.scores import scores_blueprint

    app.register_blueprint(users_blueprint, url_prefix="/api/users")
    logger.info("Users blueprint registered")

    app.register_blueprint(auth_blueprint, url_prefix="/api/auth")
    logger.info("Auth blueprint registered")

    app.register_blueprint(exercises_blueprint, url_prefix="/api/exercises")
    logger.info("Exercises blueprint registered")

    app.register_blueprint(scores_blueprint, url_prefix="/api/scores")
    logger.info("Scores blueprint registered")

    # ───────────────────────────────────────────────────────
    # REQUEST LOGGING
    # ───────────────────────────────────────────────────────
    setup_request_logging(app)
    logger.info("Request logging middleware setup completed")

    # shell context cho flask shell
    app.shell_context_processor(lambda: {"app": app, "db": db})

    logger.info("Application setup completed successfully")
    return app
