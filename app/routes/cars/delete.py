from flask import Blueprint, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.car import Car
from app.services.carService import CarsService
from app.services.userService import UsersService

delete_cars_blueprint: Blueprint = Blueprint('delete_cars', __name__, url_prefix="/cars")


@delete_cars_blueprint.route('/delete/<int:car_id>', methods=['DELETE'])
@jwt_required()
def delete_car(car_id) -> tuple[Response, int]:
    """
    Usuwa samochód z bazy danych.

    Metoda: ``DELETE``\n
    Url zapytania: ``/delete/<car-id>``

    Obsługuje żądania DELETE do usunięcia samochodu. Użytkownik musi być
    uwierzytelniony za pomocą JWT. Administratorzy mogą usuwać dowolne samochody, podczas gdy
    zwykli użytkownicy mogą usuwać tylko swoje samochody.

    Parametry zapytania:\n
    - ``car_id`` (int): ID samochodu do usunięcia.

    Zwraca:\n
    - ``200`` **OK**: Jeśli samochód został pomyślnie usunięty.\n
    - ``403`` **Forbidden**: Jeśli użytkownik nie ma uprawnień do usunięcia tego samochodu.\n
    - ``404`` **Not Found**: Jeśli samochód o podanym ID nie został znaleziony.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    try:
        users_service: UsersService = UsersService()
        cars_service: CarsService = CarsService()

        user_id: int = int(get_jwt_identity())
        is_admin: bool = users_service.get(user_id).role == 'admin'

        car: Car = cars_service.get(car_id)
        if not car:
            return jsonify({"error": "Samochód nie został znaleziony"}), 404

        if not is_admin and car.owner_id != user_id:
            return jsonify({"error": "Brak uprawnień"}), 403

        if not cars_service.delete(car_id):
            return jsonify({"error": "Wystąpił błąd podczas usuwania samochodu"}), 500

        return jsonify({
            "message": "Samochód usunięty przez administratora" if is_admin else "Samochód pomyślnie usunięty"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
