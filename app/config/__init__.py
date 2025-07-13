import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

load_dotenv(os.path.join(BASE_DIR, ".env"))


def get_config():
    """
    Określa i zwraca odpowiednią konfigurację.

    Funkcja sprawdza zmienną środowiskową FLASK_ENV, aby zdecydować, której konfiguracji użyć.
    Jeśli FLASK_ENV nie jest ustawione, domyślnie używa 'development'.

    :return: Odpowiednia klasa konfiguracji.
    """

    env: str = os.getenv("FLASK_ENV", "development")

    if env == "production":
        from app.config.production import ProductionConfig
        return ProductionConfig
    elif env == "testing":
        from app.config.testing import TestingConfig
        return TestingConfig
    else:
        from app.config.development import DevelopmentConfig
        return DevelopmentConfig