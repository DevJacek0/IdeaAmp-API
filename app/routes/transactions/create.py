from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.car import Car
from app.models.station import Station
from app.models.transaction import Transaction
from app.routes.decorators.adminRequired import admin_required
from app.services import CarsService, StationService
from app.services.transactionService import TransactionService

create_transactions_blueprint: Blueprint = Blueprint("create_transactions", __name__, url_prefix="/transactions")


@create_transactions_blueprint.route("/create", methods=["POST"])
@jwt_required()
@admin_required
def create_transaction() -> tuple[Response, int]:
    """
    Tworzy nową transakcję.

    Metoda: ``POST``\n
    Url zapytania: ``/transactions/create``

    Obsługuje żądania POST do tworzenia nowej transakcji. Użytkownik musi być uwierzytelniony za pomocą JWT
    i posiadać uprawnienia administratora.

    Wymagane dane:\n
    - ``user_id`` (int): ID użytkownika.\n
    - ``amount`` (float): Kwota transakcji (musi być większa niż 0).\n
    - ``type`` (str): Typ transakcji (dozwolone wartości: "TopUp", "Payment", "Refund").

    Opcjonalne dane:\n
    - ``car_id`` (int, opcjonalnie): ID samochodu.\n
    - ``station_id`` (int, opcjonalnie): ID stacji.

    Zwraca:\n
    - ``201`` **Created**: Jeśli transakcja została pomyślnie utworzona, zwraca szczegóły transakcji.\n
    - ``400`` **Bad Request**: Jeśli dane żądania są niepoprawne.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił nieoczekiwany błąd podczas tworzenia transakcji.
    """

    transaction_service: TransactionService = TransactionService()
    car_service: CarsService = CarsService()
    station_service: StationService = StationService()
    try:
        data = request.get_json()

        required_fields: list[str] = ["user_id", "amount", "type"]
        if not data or not all(field in data for field in required_fields):
            return jsonify({"error": f"Nieprawidłowe dane. Wymagane pola: {', '.join(required_fields)}"}), 400

        user_id: int = int(data["user_id"])
        amount: float = float(data["amount"])
        car_id: str | int = data.get("car_id")
        station_id: str | int = data.get("station_id")
        type: str = data["type"]

        if car_id is not None:
            try:
                car_id = int(car_id)
                car: Car = car_service.get(car_id)
                if not car:
                    return jsonify({"error": "Nie znaleziono samochodu"}), 400
            except (ValueError, TypeError):
                return jsonify({"error": "Nieprawidłowy identyfikator samochodu"}), 400

        if station_id is not None:
            try:
                station_id = int(station_id)
                station: Station = station_service.get(station_id)
                if not station:
                    return jsonify({"error": "Nie znaleziono stacji"}), 400
            except (ValueError, TypeError):
                return jsonify({"error": "Nieprawidłowy identyfikator stacji"}), 400

        if amount <= 0:
            return jsonify({"error": "Kwota musi być większa niż 0"}), 400

        valid_types: list[str] = ["TopUp", "Payment", "Refund"]
        if type not in valid_types:
            return jsonify({"error": f"Nieprawidłowy typ transakcji. Dozwolone wartości: {', '.join(valid_types)}"}), 400

        transaction: Transaction = transaction_service.create_transaction(
            user_id=user_id,
            amount=amount,
            type=type,
            station_id=station_id,
            car_id=car_id,
        )

        return jsonify({
            "id": transaction.id,
            "user_id": transaction.user_id,
            "car_id": transaction.car_id,
            "station_id": transaction.station_id,
            "amount": str(transaction.amount),
            "type": transaction.type,
            "created_on": transaction.created_on
        }), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500 