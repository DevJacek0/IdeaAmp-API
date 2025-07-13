from app.config.base import BaseConfig


class ProductionConfig(BaseConfig):
    """
    Ustawienia konfiguracyjne dla środowiska produkcyjnego.
    """

    DEBUG: bool = False
    SQLALCHEMY_DATABASE_URI: str = "SQLALCHEMY_DATABASE_URI"
