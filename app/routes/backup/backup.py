from flask import Blueprint, send_file, jsonify
from flask_jwt_extended import jwt_required
from app.routes.decorators.adminRequired import admin_required
from app.services.backupService import BackupService

backup_blueprint: Blueprint = Blueprint("backup", __name__, url_prefix="/backup")


@backup_blueprint.route("/create", methods=["POST"])
@jwt_required()
@admin_required
def create_backup():
    """
    Tworzy backup bazy danych.

    Metoda: ``POST``\n
    Url zapytania: ``/backup/create``

    Obsługuje żądania POST do tworzenia backupu bazy danych. Użytkownik musi być uwierzytelniony za pomocą JWT
    i posiadać uprawnienia administratora.

    Zwraca:\n
    - ``200`` **OK**: Jeśli backup został pomyślnie utworzony, zwraca plik backupu.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """
    try:
        backup_data = BackupService.create_backup()
        return send_file(backup_data, as_attachment=True), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
