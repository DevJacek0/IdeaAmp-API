from app.config.base import BaseConfig


class DevelopmentConfig(BaseConfig):
    """
    Ustawienia konfiguracyjne dla środowiska deweloperskiego.
    """

    DEBUG: bool = True
