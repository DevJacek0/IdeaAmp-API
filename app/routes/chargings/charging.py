from flask import Blueprint, jsonify, request, Response
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services import ChargingSessionsService

charging_blueprint: Blueprint = Blueprint('charging', __name__, url_prefix="/charging")

@charging_blueprint.route('/stop', methods=['POST'])
@jwt_required()
def stop_charging() -> tuple[Response, int]:
    """
    Zatrzymuje sesję ładowania.

    Metoda: ``POST``\n
    Url zapytania: ``/charging/stop``

    Obsługuje żądania POST do zatrzymania sesji ładowania. Użytkownik musi być uwierzytelniony
    za pomocą JWT. ID sesji musi być podane w treści żądania.

    Parametry żądania:\n
    - ``session_id`` (int): ID sesji ładowania do zatrzymania.

    Zwraca:\n
    - ``200`` **OK**: Wiadomość wskazująca, że sesja ładowania została pomyślnie zatrzymana, wraz ze szczegółami sesji.\n
    - ``400`` **Bad Request**: Jeśli sesja jest nieprawidłowa lub już zatrzymana.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    user_id: int = int(get_jwt_identity())
    data = request.get_json()

    session_id: int = data.get('session_id')

    charging_service: ChargingSessionsService = ChargingSessionsService()
    session = charging_service.get_session_status(session_id)

    if not session or session['user_id'] != user_id:
        return jsonify({
            'error': 'Nieprawidłowa sesja ładowania'
        }), 400

    try:
        success: bool = charging_service.end_charging_session(
            session_id=session_id,
            final_energy=session['current_kwh'],
            final_cost=session['current_cost'],
            reason="user_stopped"
        )

        if not success:
            return jsonify({
                'error': 'Nie można zatrzymać ładowania. Sesja mogła już zostać zakończona.'
            }), 400

        return jsonify({
            'message': 'Ładowanie zatrzymane pomyślnie',
            'data': {
                'session_id': session_id,
                'final_energy': round(float(session['current_kwh']), 2),
                'final_cost': round(float(session['current_cost']), 2),
                'end_reason': 'user_stopped'
            }
        }), 200
    except Exception as e:
        print(f"Błąd podczas zatrzymywania ładowania: {str(e)}")
        return jsonify({
            'error': 'Wystąpił błąd podczas zatrzymywania ładowania'
        }), 500


@charging_blueprint.route('/status/<int:session_id>', methods=['GET'])
@jwt_required()
def get_charging_status(session_id) -> tuple[Response, int]:
    """
    Pobiera status sesji ładowania.

    Metoda: ``GET``\n
    Url zapytania: ``/charging/status/<session-id>``

    Ta funkcja obsługuje żądania GET do pobierania statusu konkretnej sesji ładowania. Użytkownik musi być uwierzytelniony
    za pomocą JWT.

    Parametry zapytania:\n
    - ``session_id`` (int): ID sesji ładowania do pobrania.

    Zwraca:\n
    - ``200`` **OK**: Wiadomość wskazująca pomyślność zapytania, wraz z aktualnym statusem sesji ładowania.\n
    - ``400`` **Bad Request**: Jeśli sesja jest nieprawidłowa.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    user_id: int = int(get_jwt_identity())

    charging_service: ChargingSessionsService = ChargingSessionsService()
    try:
        session = charging_service.get_session_status(session_id)

        if not session or session['user_id'] != user_id:
            return jsonify({
                'error': 'Nieprawidłowa sesja ładowania'
            }), 400

        return jsonify({
            'data': {
                'session_id': session_id,
                'current_kwh': round(float(session['current_kwh']), 2) if session.get('current_kwh') else 0,
                'charging_power': round(float(session['current_power']), 2) if session.get('current_power') else 0,
                'current_cost': round(float(session['current_cost']), 2) if session.get('current_cost') else 0,
                'target_kwh': session.get('target_kwh'),
                'remaining_kwh': round(float(session['target_kwh'] - session['current_kwh']), 2) if session.get(
                    'target_kwh') and session.get('current_kwh') else None,
                'duration': session.get('duration'),
                'status': session.get('charging_status', 'unknown'),
                'price_per_kwh': session.get('price_per_kwh'),
                'started_on': session.get('started_on'),
                'car_id': session.get('car_id') if session.get('car_id') else None,
                'port_info': {
                    'port_id': session.get('port_id'),
                    'max_power': session.get('max_power'),
                    'connector_type': session.get('connector_type')
                }
            }
        }), 200
    except Exception as e:
        print(f"Błąd podczas pobierania statusu ładowania: {str(e)}")
        return jsonify({
            'error': 'Wystąpił błąd podczas pobierania statusu ładowania'
        }), 500
