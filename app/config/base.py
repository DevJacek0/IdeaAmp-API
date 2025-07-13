import os

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from flask import jsonify, Flask
from flask_jwt_extended import JWTManager


class BaseConfig:
    """
    Klasa służąca do przechowywania i konfigurowania podstawowych ustawień aplikacji.
    """

    SECRET_KEY: str = os.getenv('SECRET_KEY', 'example')

    SQLALCHEMY_DATABASE_URI: str = os.getenv('DATABASE_URL', 'sqlite:///example.db')
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    SQLALCHEMY_ENGINE_OPTIONS: dict[str, int | bool] = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
        'pool_timeout': 20
    }

    JWT_SECRET_KEY: str = os.getenv('JWT_SECRET_KEY', 'example')
    JWT_ACCESS_TOKEN_EXPIRES: int = 2592000  # 1h
    JWT_REFRESH_TOKEN_EXPIRES: int = 2592000  # 30d
    JWT_ALGORITHM: str = "HS256"

    MAIL_SERVER: str = 'smtp.gmail.com'
    MAIL_PORT: int = 465
    MAIL_USE_TLS: bool = False
    MAIL_USE_SSL: bool = True
    MAIL_USERNAME: str = os.getenv('MAIL_USERNAME', 'MAIL')
    MAIL_PASSWORD: str = os.getenv('MAIL_PASSWORD', 'PASS')
    MAIL_DEFAULT_SENDER: str = os.getenv('MAIL_DEFAULT_SENDER', 'MAIL')

    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

    AI_API_KEY: str = os.getenv('AI_API_KEY', 'KEY')

    @staticmethod
    def configure_database(app: Flask, db: SQLAlchemy) -> None:
        """
        Konfiguruje połączenie z bazą danych dla aplikacji Flask.

        :param app: Instancja aplikacji Flask.
        :param db: Instancja bazy danych SQLAlchemy.
        """

        db.init_app(app)

        if app.config['SQLALCHEMY_DATABASE_URI'].startswith('mysql'):
            def configure_mysql_connection(dbapi_con, con_record):
                cursor = dbapi_con.cursor()
                cursor.execute('SET FOREIGN_KEY_CHECKS=0')
                cursor.execute('SET SESSION wait_timeout=200')
                cursor.close()

            with app.app_context():
                event.listen(db.engine, 'connect', configure_mysql_connection)

        elif app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite'):
            def _fk_pragma_on_connect(dbapi_con, con_record):
                dbapi_con.execute('pragma foreign_keys=ON')

            with app.app_context():
                event.listen(db.engine, 'connect', _fk_pragma_on_connect)

    @staticmethod
    def configure_jwt(app: Flask) -> JWTManager:
        """
        Konfiguruje uwierzytelnianie JWT dla aplikacji Flask.

        :param app: Instancja aplikacji Flask.

        :return: Zainicjowana instancja JWTManager.
        """

        jwt: JWTManager = JWTManager(app)

        @jwt.unauthorized_loader
        def custom_unauthorized_response(callback):
            return jsonify({"error": "Brak tokena uwierzytelniającego. Zaloguj się, aby uzyskać dostęp."}), 401

        @jwt.invalid_token_loader
        def custom_invalid_token_response(callback):
            return jsonify({"error": "Nieprawidłowy token uwierzytelniający."}), 401

        @jwt.expired_token_loader
        def expired_token_response(jwt_header, jwt_payload):
            return jsonify({
                "error": "Token wygasł",
                "message": "Token wygasł. Użyj refresh tokenu aby otrzymać nowy token dostępu."
            }), 401

        return jwt
