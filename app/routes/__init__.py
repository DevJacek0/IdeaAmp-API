from flask import Flask, Blueprint

# Importy użytkowników
from app.routes.users.auth import auth_user_blueprint
from app.routes.users.avatar import avatar_users_blueprint
from app.routes.users.create import create_users_blueprint
from app.routes.users.gets import gets_users_blueprint
from app.routes.users.update import update_users_blueprint
from app.routes.users.password import password_users_blueprint
from app.routes.users.delete import delete_users_blueprint
from app.routes.users.twoFactor import two_factor_users_blueprint
from app.routes.users.loginHistory import login_history_blueprint

# Importy samochodów
from app.routes.cars.gets import gets_cars_blueprint
from app.routes.cars.create import create_cars_blueprint
from app.routes.cars.update import update_cars_blueprint
from app.routes.cars.delete import delete_cars_blueprint

# Importy stacji
from app.routes.stations.gets import gets_stations_blueprint
from app.routes.stations.create import create_stations_blueprint
from app.routes.stations.update import update_stations_blueprint
from app.routes.stations.delete import delete_stations_blueprint

# Importy portów
from app.routes.ports.gets import gets_ports_blueprint
from app.routes.ports.create import create_ports_blueprint
from app.routes.ports.update import update_ports_blueprint
from app.routes.ports.delete import delete_ports_blueprint

# Importy ładowania
from app.routes.chargings.charging import charging_blueprint
from app.routes.chargings.last import last_charging_blueprint
from app.routes.chargings.station import station_chargings_blueprint

# Importy FAQ
from app.routes.faq.create import create_faq_blueprint
from app.routes.faq.delete import delete_faq_blueprint
from app.routes.faq.gets import gets_faq_blueprint
from app.routes.faq.update import update_faq_blueprint

# Importy transakcji
from app.routes.transactions.create import create_transactions_blueprint
from app.routes.transactions.gets import gets_transactions_blueprint

# Importy zniżek
from app.routes.discounts.create import create_discounts_blueprint
from app.routes.discounts.gets import gets_discounts_blueprint
from app.routes.discounts.update import update_discounts_blueprint
from app.routes.discounts.delete import delete_discounts_blueprint
from app.routes.discounts.apply import apply_discounts_blueprint

# Importy raportów
from app.routes.reports.create import create_reports_blueprint
from app.routes.reports.gets import gets_report_blueprint

# Importy faktur
from app.routes.invoices.create import create_invoices_blueprint
from app.routes.invoices.gets import gets_invoices_blueprint

# Importy logów
from app.routes.auditLogs.gets import gets_logs_blueprint

# Importy powiadomień
from app.routes.notifications.ai.create import create_notifications_ai_blueprint

# Importy punktów
from app.routes.points.thresholds import points_blueprint

# Importy websocketów
from app.routes.websockets.charging import charging_socket_blueprint

#Importy backupu
from app.routes.backup.backup import backup_blueprint

def register_blueprints(app: Flask) -> None:
    """
    Rejestruje wszystkie blueprinty w aplikacji Flask.

    Funkcja tworzy listę wszystkich blueprintów, które mają być zarejestrowane w aplikacji,
    a następnie iteruje przez tę listę, rejestrując każdy blueprint w aplikacji Flask.

    :param app: Instancja aplikacji Flask, w której mają być zarejestrowane blueprinty.
    """

    blueprints: list[Blueprint] = [
        # Użytkownicy
        auth_user_blueprint, create_users_blueprint, gets_users_blueprint, update_users_blueprint,
        password_users_blueprint, delete_users_blueprint, avatar_users_blueprint, two_factor_users_blueprint,
        login_history_blueprint,

        # Samochody
        gets_cars_blueprint, create_cars_blueprint, update_cars_blueprint, delete_cars_blueprint,

        # Stacje
        gets_stations_blueprint, create_stations_blueprint, update_stations_blueprint, delete_stations_blueprint,

        # Porty
        gets_ports_blueprint,
        create_ports_blueprint,
        update_ports_blueprint,
        delete_ports_blueprint,

        # Ładowanie
        charging_socket_blueprint, charging_blueprint, last_charging_blueprint,
        station_chargings_blueprint,

        # FAQ
        create_faq_blueprint, delete_faq_blueprint, gets_faq_blueprint, update_faq_blueprint,

        # Transakcje
        gets_transactions_blueprint,
        create_transactions_blueprint,

        # Zniżki
        create_discounts_blueprint, gets_discounts_blueprint, delete_discounts_blueprint,
        apply_discounts_blueprint, update_discounts_blueprint,

        # Raporty
        create_reports_blueprint,
        gets_report_blueprint,

        # Faktury
        create_invoices_blueprint,
        gets_invoices_blueprint,

        # Logi
        gets_logs_blueprint,

        # Powiadomienia
        create_notifications_ai_blueprint,

        # Punkty
        points_blueprint,

        # Backup
        backup_blueprint
    ]

    for blueprint in blueprints:
        app.register_blueprint(blueprint)
