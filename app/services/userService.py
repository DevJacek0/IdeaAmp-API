import time
from typing import Optional, Set

from sqlalchemy import Column, Integer, String, Enum, DECIMAL, TIMESTAMP, func, BigInteger
from werkzeug.security import check_password_hash, generate_password_hash

from app.models.user import User
from app import db
from app.services.service import Service
from app.services.attachmentService import AttachmentsService


class UsersService(Service):
    def __init__(self):
        """
        Konstruktor klasy UsersService, który inicjalizuje klasę bazową Service.
        """
        super().__init__(
            table_name="users",
            load_recipe={
                "identifier": "id",
                "function": self._row_to_user
            }
        )

    def _row_to_user(self, row: dict) -> User:
        return User(
            id=row["id"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            email=row["email"],
            password=row["password"],
            role=row["role"],
            phone_number=row.get("phone_number"),
            balance=row["balance"],
            points=row.get("points", 0),
            registered_on=row["registered_on"],
            address_line1=row.get("address_line1"),
            city=row.get("city"),
            postal_code=row.get("postal_code"),
            country=row.get("country"),
            date_of_birth=row.get("date_of_birth"),
            gender=row.get("gender"),
            avatar_id=row.get("avatar_id"),
            status=row.get("status", "active"),
            two_factor_enabled=row.get("two_factor_enabled", False)
        )

    def _get_columns(self):
        return [
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('first_name', String(50), nullable=False),
            Column('last_name', String(50), nullable=False),
            Column('email', String(100), nullable=False, unique=True),
            Column('password', String(255), nullable=False),
            Column('phone_number', String(15)),
            Column('role', Enum('admin', 'client', name='user_roles'), nullable=False, default='client'),
            Column('balance', DECIMAL(10, 2), nullable=False, default=0.00),
            Column('points', Integer, default=0),
            Column('registered_on', BigInteger, nullable=False, server_default=func.now()),
            Column('address_line1', String(100)),
            Column('city', String(50)),
            Column('postal_code', String(10)),
            Column('country', String(50)),
            Column('date_of_birth', db.Date),
            Column('gender', Enum('male', 'female', 'other', name='gender_types')),
            Column('avatar_id', Integer),
            Column('status', Enum('active', 'inactive', 'suspended', name='user_status'), default='active'),
            Column('two_factor_enabled', db.Boolean, default=False)
        ]

    def get(self, user_id: int):
        """
        Pobiera użytkownika o podanym ID.

        Argumenty:
            user_id (int): ID użytkownika.

        Zwraca:
            User: Obiekt użytkownika lub None, jeśli użytkownik nie został znaleziony.
        """
        return super().get(user_id)

    def get_all(self):
        """
        Pobiera wszystkich użytkowników.

        Zwraca:
            list[User]: Lista obiektów użytkowników.
        """
        return super().get_all()

    def email_exists(self, email: str) -> bool:
        """
        Sprawdza, czy istnieje użytkownik o podanym adresie email.

        Argumenty:
            email (str): Adres email użytkownika.

        Zwraca:
            bool: True, jeśli istnieje użytkownik o podanym adresie email, inaczej False.
        """
        return any(user.email == email for user in self.get_all())

    def authenticate(self, email: str, password: str):
        """
        Autentykuje użytkownika o podanym adresie email i haśle.

        Argumenty:
            email (str): Adres email użytkownika.
            password (str): Hasło użytkownika.

        Zwraca:
            User: Obiekt użytkownika lub None, jeśli autentykacja nie powiodła się.
        """
        user = self.get_by_email(email)
        if not user or not check_password_hash(user.password, password):
            return None
        return user

    def get_by_email(self, email: str):
        """
        Pobiera użytkownika o podanym adresie email.

        Argumenty:
            email (str): Adres email użytkownika.

        Zwraca:
            User: Obiekt użytkownika lub None, jeśli użytkownik nie został znaleziony.
        """
        user = next((u for u in super().get_all() if getattr(u, 'email', '').lower() == email.lower()), None)
        if user:
            session = self.Session()
            try:
                return session.merge(user)
            finally:
                session.close()

    def create(self, first_name: str, last_name: str, email: str, password: str = None,
               role: str = 'client', **kwargs) -> User:
        """
        Tworzy nowego użytkownika.

        Argumenty:
            first_name (str): Imię użytkownika.
            last_name (str): Nazwisko użytkownika.
            email (str): Adres email użytkownika.
            password (str): Hasło użytkownika (opcjonalne).
            role (str): Rola użytkownika (opcjonalne; domyślnie 'client').
            **kwargs: Opcjonalne parametry użytkownika.

        Zwraca:
            User: Obiekt użytkownika.
        """
        session = self.Session()
        try:
            next_id = session.query(func.max(User.id)).scalar() + 1 if session.query(User.id).count() > 0 else 1

            user_data = {
                'id': next_id,
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'password': generate_password_hash(password) if password else None,
                'role': role.lower(),
                'balance': 0.00,
                'points': 0
            }

            optional_fields = [
                'phone_number', 'address_line1', 'city', 'postal_code', 'country',
                'date_of_birth', 'gender', 'avatar_id', 'status', 'two_factor_enabled'
            ]

            for field in optional_fields:
                if field in kwargs:
                    user_data[field] = kwargs[field]

            new_user = User(**user_data)

            session.add(new_user)
            session.commit()

            refreshed_user = session.query(User).get(new_user.id)
            self.set(refreshed_user.id, refreshed_user)
            return refreshed_user
        finally:
            session.close()

    def update(self, user_id: int, **kwargs):
        """
        Aktualizuje dane użytkownika.

        Argumenty:
            user_id (int): ID użytkownika.
            **kwargs: Opcjonalne parametry użytkownika.

        Zwraca:
            User: Obiekt użytkownika.
        """
        session = self.Session()
        try:
            user = session.query(User).get(user_id)
            if not user:
                return None

            if "password" in kwargs:
                kwargs["password"] = generate_password_hash(kwargs["password"])

            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)

            session.commit()

            refreshed_user = session.merge(user)
            self.set(refreshed_user.id, refreshed_user)
            return refreshed_user
        finally:
            session.close()

    def delete(self, user_id: int):
        """
        Usuwa użytkownika.

        Argumenty:
            user_id (int): ID użytkownika.

        Zwraca:
            bool: True jeśli użytkownik został usunięty, False jeśli użytkownik nie został znaleziony.
        """
        session = self.Session()
        attachments_service = AttachmentsService()
        try:
            user = session.query(User).get(user_id)
            if user:
                if user.avatar_id:
                    attachments_service.delete_file(user.avatar_id)

                session.delete(user)
                session.commit()
                self.clear(user_id)
                return True
            return False
        finally:
            session.close()

    def change_password(self, user_id: int, new_password: str):
        """
        Zmienia hasło użytkownika.

        Argumenty:
            user_id (int): ID użytkownika.
            new_password (str): Nowe hasło użytkownika.

        Zwraca:
            bool: True jeśli hasło zostało zmienione, False jeśli użytkownik nie został znaleziony.
        """
        session = self.Session()
        try:
            user = session.query(User).get(user_id)
            if user:
                user.password = generate_password_hash(new_password)
                session.commit()

                refreshed_user = session.merge(user)
                self.set(refreshed_user.id, refreshed_user)
                return True
        finally:
            session.close()

        return False

    def set_reset_code(self, email: str, code: int):
        """
        Ustawia kod resetowania hasła dla użytkownika.

        Argumenty:
            email (str): Adres email użytkownika.
            code (int): Kod resetowania hasła.

        Zwraca:
            None
        """
        cache_key = f"reset_code:{email}"
        Service._global_cache[cache_key] = {"code": code, "expiration": time.time() + 600}  # 10min

    def get_user_avatar(self, user_id):
        """
        Pobiera avatar użytkownika.

        Argumenty:
            user_id (int): ID użytkownika.

        Zwraca:
            User: Obiekt użytkownika lub None, jeśli użytkownik nie został znaleziony.
        """
        session = self.Session()
        try:
            user = session.query(User).get(user_id)
            if user and user.avatar_id:
                return self.get(user.avatar_id)
            return None
        finally:
            session.close()

    def get_reset_code(self, email: str):
        """
        Pobiera kod resetowania hasła dla użytkownika.

        Argumenty:
            email (str): Adres email użytkownika.

        Zwraca:
            int: Kod resetowania hasła lub None, jeśli kod nie został znaleziony.
        """
        cache_key = f"reset_code:{email}"
        reset_data = Service._global_cache.get(cache_key)

        if reset_data:
            if time.time() < reset_data["expiration"]:
                return reset_data["code"]
            else:
                self.delete_reset_code(email)

        return None

    def delete_reset_code(self, email: str):
        """
        Usuwa kod resetowania hasła dla użytkownika.

        Argumenty:
            email (str): Adres email użytkownika.

        Zwraca:
            None
        """
        cache_key = f"reset_code:{email}"
        Service._global_cache.pop(cache_key, None)

    def set_2fa_code(self, email: str, code: int):
        """
        Ustawia kod 2FA dla użytkownika.

        Argumenty:
            email (str): Adres email użytkownika.
            code (int): Kod 2FA.

        Zwraca:
            None
        """
        cache_key = f"2fa_code:{email}"
        Service._global_cache[cache_key] = {"code": code, "expiration": time.time() + 300}  # 5min

    def get_2fa_code(self, email: str):
        """
        Pobiera kod 2FA dla użytkownika.

        Argumenty:
            email (str): Adres email użytkownika.

        Zwraca:
            int: Kod 2FA lub None, jeśli kod nie został znaleziony.
        """
        cache_key = f"2fa_code:{email}"
        data = Service._global_cache.get(cache_key)
        
        if data:
            if time.time() < data["expiration"]:
                return data["code"]
            else:
                self.delete_2fa_code(email)
        return None

    def delete_2fa_code(self, email: str):
        """
        Usuwa kod 2FA dla użytkownika.

        Argumenty:
            email (str): Adres email użytkownika.

        Zwraca:
            None
        """
        cache_key = f"2fa_code:{email}"
        Service._global_cache.pop(cache_key, None)

    def verify_2fa(self, email: str, code: str):
        """
        Sprawdza, czy kod 2FA jest prawidłowy.

        Argumenty:
            email (str): Adres email użytkownika.
            code (str): Kod 2FA.

        Zwraca:
            bool: True, jeśli kod 2FA jest prawidłowy, inaczej False.
        """
        stored_code = self.get_2fa_code(email)
        if not stored_code:
            return False
        return str(stored_code) == str(code)

    def update_balance(self, user_id: int, amount: float) -> bool:
        """
        Aktualizuje saldo użytkownika

        Argumenty:
            user_id (int): ID użytkownika.
            amount (float): Ilość pieniędzy do dodania.

        Zwraca:
            bool: True jeśli saldo zostało zmienione, False jeśli użytkownik nie został znaleziony
        """
        session = self.Session()
        try:
            user = session.query(User).get(user_id)
            if not user:
                return False
            
            user.balance = float(user.balance) + amount
            session.commit()
            
            refreshed_user = session.merge(user)
            self.set(refreshed_user.id, refreshed_user)
            return True
        finally:
            session.close()

    def add_points(self, user_id: int, points: int) -> bool:
        """
        Dodaje punkty do konta użytkownika

        Argumenty:
            user_id (int): ID użytkownika.
            points (int): Ilość punktów do dodania.

        Zwraca:
            bool: True jeśli punkty zostały dodane, False jeśli użytkownik nie został znaleziony
        """
        session = self.Session()
        try:
            user = session.query(User).get(user_id)
            if not user:
                return False

            if user.points is None:
                user.points = 0

            user.points += points
            session.commit()

            refreshed_user = session.merge(user)
            self.set(refreshed_user.id, refreshed_user)
            return True
        except Exception as e:
            session.rollback()
            print(f"[Error] Błąd podczas dodawania punktów: {e}")
            return False
        finally:
            session.close()

    def deduct_points(self, user_id: int, points: int) -> bool:
        """
        Odejmuje punkty z konta użytkownika

        Argumenty:
            user_id (int): ID użytkownika.
            points (int): Ilość punktów do odejmowania.

        Zwraca:
            bool: True jeśli punkty zostały odejmowane, False jeśli użytkownik nie został znaleziony
        """
        session = self.Session()
        try:
            user = session.query(User).get(user_id)
            if not user or user.points < points:
                return False
            
            user.points -= points
            session.commit()
            
            refreshed_user = session.merge(user)
            self.set(refreshed_user.id, refreshed_user)
            return True
        except Exception as e:
            session.rollback()
            print(f"[Error] Błąd podczas odejmowania punktów: {e}")
            return False
        finally:
            session.close()

    def get_user_points(self, user_id: int) -> int:
        """
        Pobiera liczbę punktów użytkownika

        Argumenty:
            user_id (int): ID użytkownika.

        Zwraca:
            int: Liczba punktów
        """
        user = self.get(user_id)
        return user.points if user else 0
