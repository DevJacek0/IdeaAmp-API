from flask import Blueprint, Response, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.transaction import Transaction
from app.models.user import User
from app.services import ReportsService, TransactionService, UsersService

create_invoices_blueprint: Blueprint = Blueprint('create_invoices', __name__, url_prefix='/invoices/create')


@create_invoices_blueprint.route('/<int:transaction_id>', methods=['POST'])
@jwt_required()
def create_invoice(transaction_id) -> tuple[Response, int]:
    """
    Tworzy fakturę na podstawie ID transakcji.

    Metoda: ``POST``\n
    Url zapytania: ``/invoices/create/<transaction-id>``

    Obsługuje żądania POST do tworzenia faktury na podstawie ID transakcji. Użytkownik musi być uwierzytelniony za pomocą JWT.

    Parametry:\n
    - ``transaction_id`` (int): ID transakcji, na podstawie której ma zostać utworzona faktura.

    Zwraca:\n
    - ``200`` **OK**: ID utworzonej faktury w formacie JSON.\n
    - ``400`` **Bad Request**: Jeśli nie udało się utworzyć faktury.\n
    - ``403`` **Forbidden**: Jeśli użytkownik nie ma uprawnień do tworzenia faktury.\n
    - ``404`` **Not Found**: Jeśli transakcja nie została znaleziona.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    transactions_service: TransactionService = TransactionService()
    reports_service: ReportsService = ReportsService()
    users_service: UsersService = UsersService()

    try:
        user_id: int = int(get_jwt_identity())
        user: User = users_service.get(user_id)

        transaction: Transaction = transactions_service.get(transaction_id)
        if not transaction:
            return jsonify({"error": "Transakcja nie została znaleziona"}), 404

        if transaction.user_id != user_id:
            if user.role != "admin":
                return jsonify({"error": "Brak dostępu"}), 403

            user = users_service.get(transaction.user_id)

        invoice_id: int = reports_service.generate_invoice([transaction], user, user_id)

        if not invoice_id:
            return jsonify({"error": "Nie udało sie wygenerować faktury"}), 400

        return jsonify({"invoice_id": invoice_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500