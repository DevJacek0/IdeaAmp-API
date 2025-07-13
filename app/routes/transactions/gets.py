from flask import Blueprint, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.transaction import Transaction
from app.routes.decorators.adminRequired import admin_required
from app.routes.decorators.pagination import paginate
from app.services.transactionService import TransactionService

gets_transactions_blueprint: Blueprint = Blueprint("gets_transactions", __name__, url_prefix="/transactions")


@gets_transactions_blueprint.route("/self/get-all", methods=["GET"])
@jwt_required()
@paginate
def get_self_all_transactions() -> list[dict[str, str | int]] | tuple[Response, int]:
    """
    Pobiera wszystkie transakcje użytkownika.

    Metoda: ``GET``\n
    Url zapytania: ``/transactions/self/get-all``

    Obsługuje żądania GET do pobrania wszystkich transakcji zalogowanego użytkownika. Użytkownik musi być uwierzytelniony za pomocą JWT.

    Zwraca:\n
    - ``200`` **OK**: Lista transakcji użytkownika w formacie JSON.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    user_id: int = int(get_jwt_identity())
    transaction_service: TransactionService = TransactionService()

    try:
        transactions: list[Transaction] = transaction_service.get_user_transactions(user_id)

        return [
            {
                "id": transaction.id,
                "user_id": transaction.user_id,
                "car_id": transaction.car_id,
                "station_id": transaction.station_id,
                "amount": str(transaction.amount),
                "type": transaction.type,
                "created_on": transaction.created_on
            }
            for transaction in transactions
        ]
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@gets_transactions_blueprint.route("/get-all", methods=["GET"])
@jwt_required()
@admin_required
@paginate
def get_all_transactions() -> list[dict[str, str | int]] | tuple[Response, int]:
    """
    Pobiera wszystkie transakcje.

    Metoda: ``GET``\n
    Url zapytania: ``/transactions/get-all``

    Obsługuje żądania GET do pobrania wszystkich transakcji. Użytkownik musi być uwierzytelniony za pomocą JWT i posiadać uprawnienia administratora.

    Zwraca:\n
    - ``200`` **OK**: Lista wszystkich transakcji w formacie JSON.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    transaction_service: TransactionService = TransactionService()
    try:
        transactions: list[Transaction] = transaction_service.get_all()

        return [
            {
                "id": transaction.id,
                "user_id": transaction.user_id,
                "car_id": transaction.car_id,
                "station_id": transaction.station_id,
                "amount": str(transaction.amount),
                "type": transaction.type,
                "created_on": transaction.created_on
            }
            for transaction in transactions
        ]
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@gets_transactions_blueprint.route("/<int:transaction_id>", methods=["GET"])
@jwt_required()
def get_transaction(transaction_id) -> tuple[Response, int]:
    """
    Pobiera transakcję na podstawie ID.

    Metoda: ``GET``\n
    Url zapytania: ``/transactions/<transaction-id>``

    Obsługuje żądania GET do pobrania transakcji na podstawie ID. Użytkownik musi być uwierzytelniony za pomocą JWT.

    Parametry:\n
    - ``transaction_id`` (int): ID transakcji do pobrania.

    Zwraca:\n
    - ``200`` **OK**: Szczegóły transakcji w formacie JSON.\n
    - ``403`` **Forbidden**: Jeśli użytkownik nie ma dostępu do transakcji.\n
    - ``404`` **Not Found**: Jeśli transakcja nie została znaleziona.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    transaction_service: TransactionService = TransactionService()
    transaction: Transaction = transaction_service.get(transaction_id)
    if not transaction:
        return jsonify({"error": "Nie znaleziono transakcji"}), 404

    user_id: int = int(get_jwt_identity())
    if transaction.user_id != user_id:
        return jsonify({"error": "Brak dostępu"}), 403

    return jsonify({
        "id": transaction.id,
        "user_id": transaction.user_id,
        "car_id": transaction.car_id,
        "station_id": transaction.station_id,
        "amount": str(transaction.amount),
        "type": transaction.type,
        "created_on": transaction.created_on
    }), 200
