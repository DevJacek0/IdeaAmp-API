import os.path

from flask import Blueprint, jsonify, send_file, Response, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.chargingSession import ChargingSession
from app.models.report import Report
from app.models.user import User
from app.routes.decorators.adminRequired import admin_required
from app.services import ChargingSessionsService, TransactionService, UsersService
from app.routes.decorators.pagination import paginate
from app.services.reportsService import ReportsService
from app.services.attachmentService import AttachmentsService

gets_report_blueprint = Blueprint('reports', __name__, url_prefix="/reports")


@gets_report_blueprint.route("/transactions/<int:report_id>", methods=["GET"])
@jwt_required()
def get_transactions_report(report_id) -> tuple[Response, int]:
    """
    Pobiera raport transakcji.

    Metoda: ``GET``\n
    Url zapytania: ``/reports/transactions/<report_id>``

    Obsługuje żądania GET do pobrania raportu transakcji na podstawie ID raportu. Użytkownik musi być uwierzytelniony za pomocą JWT.

    Parametry:\n
    - ``report_id`` (int): ID raportu do pobrania.

    Zwraca:\n
    - ``200`` **OK**: Plik PDF raportu.\n
    - ``404`` **Not Found**: Jeśli raport lub plik raportu nie został znaleziony.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    reports_service: ReportsService = ReportsService()
    users_service: UsersService = UsersService()
    attachments_service: AttachmentsService = AttachmentsService()

    try:
        user_id: int = int(get_jwt_identity())
        user: User = users_service.get(user_id)
        report: Report = reports_service.get(report_id)

        if not report:
            return jsonify({"error": "Raport nie został znaleziony"}), 404

        if int(report.generated_by) != user_id and user.role != "admin":
            return jsonify({"error": "Brak dostępu"}), 403

        report_pdf = attachments_service.get_file_path(
            rf"attachments/all/reports/transactions/report_{report.pdf_id}.pdf")
        if not os.path.exists(report_pdf):
            return jsonify({"error": "Nie znaleziono pliku raportu"}), 404

        return send_file(report_pdf), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@gets_report_blueprint.route("/sessions/<int:report_id>", methods=["GET"])
@jwt_required()
def get_sessions_report(report_id) -> tuple[Response, int]:
    """
    Pobiera raport sesji ładowania.

    Metoda: ``GET``\n
    Url zapytania: ``/reports/sessions/<report-id>``

    Obsługuje żądania GET do pobrania raportu sesji ładowania na podstawie ID raportu. Użytkownik musi być uwierzytelniony za pomocą JWT.

    Parametry:\n
    - ``report_id`` (int): ID raportu do pobrania.

    Zwraca:\n
    - ``200`` **OK**: Plik PDF raportu.\n
    - ``404`` **Not Found**: Jeśli raport lub plik raportu nie został znaleziony.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    reports_service: ReportsService = ReportsService()
    users_service: UsersService = UsersService()
    attachments_service: AttachmentsService = AttachmentsService()

    try:
        user_id: int = int(get_jwt_identity())
        user: User = users_service.get(user_id)
        report: Report = reports_service.get(report_id)

        if not report:
            return jsonify({"error": "Raport nie został znaleziony"}), 404

        if int(report.generated_by) != user_id and user.role != "admin":
            return jsonify({"error": "Brak dostępu"}), 403

        report_pdf = attachments_service.get_file_path(rf"attachments/all/reports/sessions/report_{report.pdf_id}.pdf")
        if not os.path.exists(report_pdf):
            return jsonify({"error": "Nie znaleziono pliku raportu"}), 404

        return send_file(report_pdf), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@gets_report_blueprint.route("/self", methods=["GET"])
@jwt_required()
@paginate
def get_own_reports() -> tuple[Response, int] | list[dict[str, str | int]]:
    """
    Pobiera własne raporty.

    Metoda: ``GET``\n
    Url zapytania: ``/reports/self``

    Obsługuje żądania GET do pobrania własnych raportów użytkownika. Użytkownik musi być uwierzytelniony za pomocą JWT.

    Zwraca:\n
    - ``200`` **OK**: Lista raportów w formacie JSON.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    reports_service: ReportsService = ReportsService()

    try:
        user_id: int = int(get_jwt_identity())
        reports: list[Report] = reports_service.get_by_user(user_id)

        return [{
            "id": report.id,
            "type": report.type,
            "generated_on": report.generated_on,
            "pdf_id": report.pdf_id
        } for report in reports if report.type.lower() != "invoice"]
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@gets_report_blueprint.route("/all", methods=["GET"])
@jwt_required()
@admin_required
@paginate
def get_all_reports() -> tuple[Response, int] | list[dict[str, str | int]]:
    """
    Pobiera wszystkie raporty.

    Metoda: ``GET``\n
    Url zapytania: ``/reports/all``

    Obsługuje żądania GET do pobrania wszystkich raportów. Użytkownik musi być uwierzytelniony za pomocą JWT
    i posiadać uprawnienia administratora.

    Zwraca:\n
    - ``200`` **OK**: Lista raportów w formacie JSON.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    reports_service: ReportsService = ReportsService()

    try:
        reports: list[Report] = reports_service.get_all()

        return [{
            "id": report.id,
            "generated_by": report.generated_by,
            "type": report.type,
            "generated_on": report.generated_on,
            "pdf_id": report.pdf_id
        } for report in reports if report.type.lower() != "invoice"]
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@gets_report_blueprint.route("/peak-hours", methods=["GET"])
@jwt_required()
@admin_required
def get_peak_hours():
    """
    Pobiera raport godzin ładowania.

    Metoda: ``GET``\n
    Url zapytania: ``/reports/peak-hours``

    Parametry zapytania:\n
    - ``period`` (opcjonalne): ``month`` lub ``24h``

    Obsługuje żądania GET do pobrania raportu godzin ładowania. Użytkownik musi być uwierzytelniony za pomocą JWT
    i posiadać uprawnienia administratora.

    Zwraca:\n
    - ``200`` **OK**: Raport godzin ładowania w formacie JSON.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """
    reports_service: ReportsService = ReportsService()
    charging_sessions_service: ChargingSessionsService = ChargingSessionsService()

    period: str = request.args.get("period")

    if not period or period not in ["month", "24h"]:
        period = "month"

    if period == "month":
        last_month: list[dict[str, User | ChargingSession]] = charging_sessions_service.get_last_month()

        peak_hours_month: list = ReportsService.calculate_peak_hours(last_month)

        return jsonify(reports_service.format_peak_hours(peak_hours_month))
    if period == "24h":
        last_24h_sessions: list[dict[str, User | ChargingSession]] = charging_sessions_service.get_last_24_hours()

        peak_hours_24h: list = ReportsService.calculate_peak_hours(last_24h_sessions)

        return jsonify(reports_service.format_peak_hours(peak_hours_24h))

    return jsonify({"error": "Błędny parametr"}), 400

@gets_report_blueprint.route("/turnover", methods=["GET"])
@jwt_required()
@admin_required
def get_all_turnover():
    """
    Pobiera całkowity obrót.

    Metoda: ``GET``\n
    Url zapytania: ``/reports/turnover``

    Obsługuje żądania GET do pobrania całkowitego obrótu. Użytkownik musi być uwierzytelniony za pomocą JWT
    i posiadać uprawnienia administratora.

    Zwraca:\n
    - ``200`` **OK**: Całkowity obrót w formacie JSON.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.

    """

    transaction_service: TransactionService = TransactionService()

    turnover = transaction_service.get_all_turnover()

    return jsonify({"turnover": turnover})
