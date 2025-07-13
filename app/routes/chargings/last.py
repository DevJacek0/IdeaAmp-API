from flask import Blueprint, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.chargingSession import ChargingSession
from app.services import ChargingSessionsService

last_charging_blueprint: Blueprint = Blueprint('last_charging', __name__, url_prefix="/charging")


@last_charging_blueprint.route('/last', methods=['GET'])
@jwt_required()
def get_last_charging() -> tuple[Response, int]:
    """
    Pobiera ostatnią zakończoną sesję ładowania użytkownika.

    Metoda: ``GET``\n
    Url zapytania: ``/charging/last``

    Obsługuje żądania GET do pobierania ostatniej zakończonej sesji ładowania użytkownika. Użytkownik musi być
    uwierzytelniony za pomocą JWT.

    Zwraca:\n
    - ``200`` **OK**: Informacja o powodzeniu zapytania, wraz ze szczegółami ostatniej zakończonej sesji ładowania.\n
    - ``404`` **Not Found**: Jeśli nie znaleziono żadnych sesji ładowania lub zakończonych sesji ładowania.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    user_id: int = int(get_jwt_identity())
    charging_service: ChargingSessionsService = ChargingSessionsService()

    try:
        user_sessions: list[ChargingSession] = charging_service.get_by_user(user_id)

        if not user_sessions:
            return jsonify({
                'error': 'Nie znaleziono żadnych sesji ładowania'
            }), 404

        completed_sessions: list[ChargingSession] = [s for s in user_sessions if s.end_on is not None]
        if not completed_sessions:
            return jsonify({
                'error': 'Nie znaleziono zakończonych sesji ładowania'
            }), 404

        last_session: ChargingSession = max(completed_sessions, key=lambda x: x.end_on)

        return jsonify({
            'data': {
                'session_id': last_session.id,
                'started_on': last_session.started_on,
                'ended_on': last_session.end_on,
                'energy_consumed': float(last_session.energy_consumed) if last_session.energy_consumed else 0,
                'cost': float(last_session.cost) if last_session.cost else 0,
                'port_id': last_session.port_id,
                'car_id': last_session.car_id,
                'power_limit': float(last_session.power_limit) if last_session.power_limit else None
            }
        }), 200

    except Exception as e:
        print(f"Błąd podczas pobierania ostatniej sesji ładowania: {str(e)}")
        return jsonify({
            'error': 'Wystąpił błąd podczas pobierania ostatniej sesji ładowania'
        }), 500
