from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.chargingSession import ChargingSession
from app.models.transaction import Transaction
from app.models.user import User
from app.routes.decorators.adminRequired import admin_required
from app.services import UsersService, ReportsService, TransactionService, ChargingSessionsService

create_reports_blueprint = Blueprint('create_reports', __name__, url_prefix='/reports/create')


@create_reports_blueprint.route('/transactions/self', methods=['POST'])
@jwt_required()
def create_own_transactions_report() -> tuple[Response, int]:
    """
    Tworzy raport własnych transakcji.

    Metoda: ``POST``\n
    Url zapytania: ``/reports/create/transactions/self``

    Obsługuje żądania POST do wygenerowania raportu własnych transakcji. Użytkownik musi być uwierzytelniony za pomocą JWT.

    Wymagane dane:\n
    - ``from_timestamp`` (int): Początkowy znacznik czasu.\n
    - ``to_timestamp`` (int): Końcowy znacznik czasu.

    Zwraca:\n
    - ``200`` **OK**: Jeśli raport został pomyślnie wygenerowany, zwraca ID raportu.\n
    - ``400`` **Bad Request**: Jeśli dane żądania są niepoprawne.\n
    - ``404`` **Not Found**: Jeśli użytkownik nie został znaleziony.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    users_service: UsersService = UsersService()
    transactions_service: TransactionService = TransactionService()
    reports_service: ReportsService = ReportsService()

    try:
        user_id: int = int(get_jwt_identity())
        user: User = users_service.get(user_id)

        if not user:
            return jsonify({"error": "Użytkownik nie został znaleziony"}), 404

        data = request.get_json()

        required_fields: list[str] = ["from_timestamp", "to_timestamp"]
        validation_errors: dict[str, str] = {}

        if not data:
            return jsonify({"error": "Niepoprawne dane żądania"}), 400

        for field in required_fields:
            value = data.get(field, "").strip() if isinstance(data.get(field), str) else data.get(field)
            if value is None:
                validation_errors[field] = "Pole nie może być puste"
            elif not isinstance(value, int):
                validation_errors[field] = "Znacznik czasu musi być liczbą"

        if validation_errors:
            return jsonify({"error": validation_errors}), 400

        transactions: list[dict[str, User | Transaction]] = transactions_service.get_between(data["from_timestamp"],
                                                                                             data["to_timestamp"],
                                                                                             user_id)
        report_id: int = reports_service.generate_transactions_report(transactions, data["from_timestamp"],
                                                                      data["to_timestamp"], user_id)

        if not report_id:
            return jsonify({"error": "Nie udało sie wygenerować raportu"}), 400

        return jsonify({"report_id": report_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@create_reports_blueprint.route('/transactions/all', methods=['POST'])
@jwt_required()
@admin_required
def create_all_transactions_report() -> tuple[Response, int]:
    """
    Tworzy raport wszystkich transakcji.

    Metoda: ``POST``\n
    Url zapytania: ``/reports/create/transactions/all``

    Obsługuje żądania POST do wygenerowania raportu wszystkich transakcji. Użytkownik musi być uwierzytelniony za pomocą JWT
    i posiadać uprawnienia administratora.

    Wymagane dane:\n
    - ``from_timestamp`` (int): Początkowy znacznik czasu.\n
    - ``to_timestamp`` (int): Końcowy znacznik czasu.

    Zwraca:\n
    - ``200`` **OK**: Jeśli raport został pomyślnie wygenerowany, zwraca ID raportu.\n
    - ``400`` **Bad Request**: Jeśli dane żądania są niepoprawne.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    transactions_service: TransactionService = TransactionService()
    reports_service: ReportsService = ReportsService()

    try:
        user_id: int = int(get_jwt_identity())

        data = request.get_json()

        required_fields: list[str] = ["from_timestamp", "to_timestamp"]
        validation_errors: dict[str, str] = {}

        if not data:
            return jsonify({"error": "Niepoprawne dane żądania"}), 400

        for field in required_fields:
            value = data.get(field, "").strip() if isinstance(data.get(field), str) else data.get(field)
            if value is None:
                validation_errors[field] = "Pole nie może być puste"
            elif not isinstance(value, int):
                validation_errors[field] = "Zakres czasowy musi być liczbą"

        if validation_errors:
            return jsonify({"error": validation_errors}), 400

        transactions: list[dict[str, User | Transaction]] = transactions_service.get_between(data["from_timestamp"],
                                                                                             data["to_timestamp"])
        report_id: int = reports_service.generate_transactions_report(transactions, data["from_timestamp"],
                                                                      data["to_timestamp"], user_id)

        if not report_id:
            return jsonify({"error": "Nie udało się wygenerować raportu"}), 400

        return jsonify({"report_id": report_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@create_reports_blueprint.route('/sessions/self', methods=['POST'])
@jwt_required()
def create_own_sessions_report() -> tuple[Response, int]:
    """
    Tworzy raport własnych sesji ładowania.

    Metoda: ``POST``\n
    Url zapytania: ``/reports/create/sessions/self``

    Obsługuje żądania POST do wygenerowania raportu własnych sesji ładowania. Użytkownik musi być uwierzytelniony za pomocą JWT.

    Wymagane dane:\n
    - ``from_timestamp`` (int): Początkowy znacznik czasu.\n
    - ``to_timestamp`` (int): Końcowy znacznik czasu.

    Zwraca:\n
    - ``200`` **OK**: Jeśli raport został pomyślnie wygenerowany, zwraca ID raportu.\n
    - ``400`` **Bad Request**: Jeśli dane żądania są niepoprawne.\n
    - ``404`` **Not Found**: Jeśli użytkownik nie został znaleziony.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    users_service: UsersService = UsersService()
    charging_service: ChargingSessionsService = ChargingSessionsService()
    reports_service: ReportsService = ReportsService()

    try:
        user_id: int = int(get_jwt_identity())
        user: User = users_service.get(user_id)

        if not user:
            return jsonify({"error": "Użytkownik nie został znaleziony"}), 404

        data = request.get_json()

        required_fields: list[str] = ["from_timestamp", "to_timestamp"]
        validation_errors: dict[str, str] = {}

        if not data:
            return jsonify({"error": "Niepoprawne dane żądania"}), 400

        for field in required_fields:
            value = data.get(field, "").strip() if isinstance(data.get(field), str) else data.get(field)
            if value is None:
                validation_errors[field] = "Pole nie może być puste"
            elif not isinstance(value, int):
                validation_errors[field] = "Zakres czasowy musi być liczbą"

        if validation_errors:
            return jsonify({"error": validation_errors}), 400

        sessions: list[dict[str, User | ChargingSession]] = charging_service.get_between(data["from_timestamp"],
                                                                                         data["to_timestamp"], user_id)
        report_id: int = reports_service.generate_sessions_report(sessions, data["from_timestamp"],
                                                                  data["to_timestamp"], user_id)

        if not report_id:
            return jsonify({"error": "Nie udało sie wygenerować raportu"}), 400

        return jsonify({"report_id": report_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@create_reports_blueprint.route('/sessions/all', methods=['POST'])
@jwt_required()
@admin_required
def create_all_sessions_report() -> tuple[Response, int]:
    """
    Tworzy raport wszystkich sesji ładowania.

    Metoda: ``POST``\n
    Url zapytania: ``/reports/create/sessions/all``

    Obsługuje żądania POST do wygenerowania raportu wszystkich sesji ładowania. Użytkownik musi być uwierzytelniony za pomocą JWT
    i posiadać uprawnienia administratora.

    Wymagane dane:\n
    - ``from_timestamp`` (int): Początkowy znacznik czasu.\n
    - ``to_timestamp`` (int): Końcowy znacznik czasu.

    Zwraca:\n
    - ``200`` **OK**: Jeśli raport został pomyślnie wygenerowany, zwraca ID raportu.\n
    - ``400`` **Bad Request**: Jeśli dane żądania są niepoprawne.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """
    
    charging_service: ChargingSessionsService = ChargingSessionsService()
    reports_service: ReportsService = ReportsService()

    try:
        user_id: int = int(get_jwt_identity())

        data = request.get_json()

        required_fields: list[str] = ["from_timestamp", "to_timestamp"]
        validation_errors: dict[str, str] = {}

        if not data:
            return jsonify({"error": "Niepoprawne dane żądania"}), 400

        for field in required_fields:
            value = data.get(field, "").strip() if isinstance(data.get(field), str) else data.get(field)
            if value is None:
                validation_errors[field] = "Pole nie może być puste"
            elif not isinstance(value, int):
                validation_errors[field] = "Zakres czasowy musi być liczbą"

        if validation_errors:
            return jsonify({"error": validation_errors}), 400

        sessions: list[dict[str, User | ChargingSession]] = charging_service.get_between(data["from_timestamp"],
                                                                                         data["to_timestamp"])
        report_id: int = reports_service.generate_sessions_report(sessions, data["from_timestamp"],
                                                                  data["to_timestamp"], user_id)

        if not report_id:
            return jsonify({"error": "Nie udało się wygenerować raportu"}), 400

        return jsonify({"report_id": report_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
