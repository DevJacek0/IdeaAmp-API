import os

from flask import Blueprint, Response, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.report import Report
from app.models.user import User
from app.routes.decorators.adminRequired import admin_required
from app.routes.decorators.pagination import paginate
from app.services import ReportsService, AttachmentsService, UsersService

gets_invoices_blueprint: Blueprint = Blueprint('gets_invoices', __name__, url_prefix='/invoices/')


@gets_invoices_blueprint.route('/<int:invoice_id>', methods=['GET'])
@jwt_required()
def get_invoice(invoice_id) -> tuple[Response, int]:
    """
    Pobiera fakturę.

    Metoda: ``GET``\n
    Url zapytania: ``/invoices/<invoice_id>``

    Obsługuje żądania GET do pobrania faktury na podstawie ID faktury. Użytkownik musi być uwierzytelniony za pomocą JWT.

    Parametry:\n
    - ``invoice_id`` (int): ID faktury do pobrania.

    Zwraca:\n
    - ``200`` **OK**: Plik PDF faktury.\n
    - ``404`` **Not Found**: Jeśli faktura lub plik faktury nie został znaleziony.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    reports_service: ReportsService = ReportsService()
    attachments_service: AttachmentsService = AttachmentsService()
    users_service: UsersService = UsersService()

    try:
        user_id: int = int(get_jwt_identity())
        user: User = users_service.get(user_id)
        invoice: Report = reports_service.get(invoice_id)

        if not invoice:
            return jsonify({"error": "Faktura nie została znaleziona"}), 404

        if invoice.generated_by != user_id and user.role != "admin":
            return jsonify({"error": "Brak dostępu"}), 403

        invoice_pdf = attachments_service.get_file_path(
            rf"attachments/all/invoices/invoice_{invoice.pdf_id}.pdf")
        if not os.path.exists(invoice_pdf):
            return jsonify({"error": "Nie znaleziono pliku faktury"}), 404

        return send_file(invoice_pdf), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@gets_invoices_blueprint.route('/self', methods=['GET'])
@jwt_required()
@paginate
def get_own_invoices() -> tuple[Response, int] | list[dict[str, str | int]]:
    """
    Pobiera własne faktury.

    Metoda: ``GET``\n
    Url zapytania: ``/invoices/self``

    Obsługuje żądania GET do pobrania własnych raportów użytkownika. Użytkownik musi być uwierzytelniony za pomocą JWT.

    Zwraca:\n
    - ``200`` **OK**: Lista raportów w formacie JSON.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    reports_service: ReportsService = ReportsService()

    try:
        user_id: int = int(get_jwt_identity())
        invoices: list[Report] = reports_service.get_by_user(user_id)

        return [{
            "id": invoice.id,
            "generated_on": invoice.generated_on,
            "pdf_id": invoice.pdf_id
        } for invoice in invoices if invoice.type.lower() == "invoice"]
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@gets_invoices_blueprint.route("/all", methods=["GET"])
@jwt_required()
@admin_required
@paginate
def get_all_invoices() -> tuple[Response, int] | list[dict[str, str | int]]:
    """
    Pobiera wszystkie faktury.

    Metoda: ``GET``\n
    Url zapytania: ``/invoices/all``

    Obsługuje żądania GET do pobrania wszystkich faktur. Użytkownik musi być uwierzytelniony za pomocą JWT.

    Zwraca:\n
    - ``200`` **OK**: Lista faktur w formacie JSON.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    reports_service: ReportsService = ReportsService()

    try:
        invoices: list[Report] = reports_service.get_all()

        return [{
            "id": invoice.id,
            "generated_by": invoice.generated_by,
            "generated_on": invoice.generated_on,
            "pdf_id": invoice.pdf_id
        } for invoice in invoices if invoice.type.lower() == "invoice"]
    except Exception as e:
        return jsonify({"error": str(e)}), 500