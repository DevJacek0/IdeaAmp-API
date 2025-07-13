from app.config.base import BaseConfig


class TestingConfig(BaseConfig):
    """
    Ustawienia konfiguracyjne dla środowiska testowego.
    """

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
