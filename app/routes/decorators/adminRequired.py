from functools import wraps
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.user import User
from app.services.userService import UsersService


def admin_required(fn):
    """
    Dekorator wymagający uprawnień administratora.

    Sprawdza, czy użytkownik jest administratorem przed wykonaniem funkcji.
    Użytkownik musi być uwierzytelniony za pomocą JWT.

    Parametry:\n
    - ``fn`` (function): Funkcja do udekorowania.

    Zwraca:\n
    - ``fn``: Udekorowana funkcja, jeśli użytkownik ma uprawnienia administratora.
    - ``403`` **Forbidden**: Jeśli użytkownik nie ma uprawnień administratora.\n
    """

    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        users_service: UsersService = UsersService()
        user_id: int = int(get_jwt_identity())
        user: User = users_service.get(user_id)

        if not user or user.role != "admin":
            return jsonify({"error": "Brak uprawnień"}), 403

        return fn(*args, **kwargs)

    return wrapper
