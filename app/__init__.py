
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_sock import Sock
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.config import get_config
from app.config.base import BaseConfig
from app.middlewares.timestampsValidate import validate_request
from app.schedulers.checkUnusedChargers import init_check_chargers

db: SQLAlchemy = SQLAlchemy()
jwt: JWTManager = JWTManager()
mail: Mail = Mail()
migrate: Migrate = Migrate()
sock: Sock = Sock()
scheduler: BackgroundScheduler = BackgroundScheduler()


def create_app() -> Flask:
    """
    Tworzy i konfiguruje aplikację Flask.

    Inicjalizuje nową instancję aplikacji, konfiguruje ją z niezbędnymi rozszerzeniami i
    ustawieniami oraz przygotowuje komponenty niezbędne do uruchomienia aplikacji.

    :return: Skonfigurowana instancja aplikacji gotowa do uruchomienia.
    """

    app: Flask = Flask(__name__, static_folder='attachments', static_url_path='/attachments')
    app.config.from_object(get_config())

    limiter = Limiter(app = app, key_func=get_remote_address, default_limits=["200000 per day", "50000 per hour"])


    mail.init_app(app)

    BaseConfig.configure_database(app, db)

    jwt.init_app(app)
    CORS(app)

    migrate.init_app(app, db)
    sock.init_app(app)

    BaseConfig.configure_jwt(app)

    with app.app_context():
        from app.routes import register_blueprints

        app.before_request(validate_request)
        app.limiter = limiter
        init_check_chargers(scheduler)


    if not scheduler.running:
        scheduler.start()

    register_blueprints(app)

    return app
