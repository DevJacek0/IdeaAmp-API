from datetime import datetime

from sqlalchemy.orm import relationship

from app import db


class User(db.Model):
    """
    Model dla uzytkownika

    Atrybuty:
        id (int): Identyfikator uzytkownika
        first_name (str): Imie uzytkownika
        last_name (str): Nazwisko uzytkownika
        password (str): Haslo uzytkownika
        email (str): Email uzytkownika
        phone_number (str): Numer telefonu uzytkownika
        role (str): Role uzytkownika ("admin", "client")
        balance (float): Saldo uzytkownika
        registered_on (unix timestamp): Data rejestracji uzytkownika
        address_line1 (str): Adres uzytkownika
        city (str): Miasto uzytkownika
        postal_code (str): Kod pocztowy uzytkownika
        country (str): Kraj uzytkownika
        date_of_birth (date): Data urodzenia uzytkownika
        gender (str): Plec uzytkownika ("male", "female", "other")
        avatar_id (int): Identyfikator awatara uzytkownika
        status (str): Status uzytkownika ("active", "inactive", "suspended")
        two_factor_enabled (bool): Czy weryfikacja dwuetapowa jest wlaczona
        points (int): Punkty uzytkownika

    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone_number = db.Column(db.String(15))
    role = db.Column(db.Enum('admin', 'client', name='user_roles'), nullable=False, default='client')
    balance = db.Column(db.DECIMAL(10, 2), nullable=False, default=0.00)
    registered_on = db.Column(db.BigInteger, nullable=False, default=lambda: int(datetime.utcnow().timestamp() * 1000))
    address_line1 = db.Column(db.String(100))
    city = db.Column(db.String(50))
    postal_code = db.Column(db.String(10))
    country = db.Column(db.String(50))

    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.Enum('male', 'female', 'other', name='gender_types'))
    avatar_id = db.Column(db.Integer, db.ForeignKey('attachments.id', ondelete='SET NULL'))

    avatar = relationship("Attachment", foreign_keys=[avatar_id])

    status = db.Column(db.Enum('active', 'inactive', 'suspended', name='user_status'), default='active')

    two_factor_enabled = db.Column(db.Boolean, default=False)

    points = db.Column(db.Integer, default=0)

    def __init__(self, id, first_name, last_name, email, password, role='client', phone_number=None,
                 address_line1=None, city=None, postal_code=None, country=None,
                 date_of_birth=None, gender=None, avatar_id=None, status='active',
                 two_factor_enabled=False, balance=0.00, registered_on=None, points=0):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password
        self.role = role
        self.phone_number = phone_number
        self.balance = balance
        self.address_line1 = address_line1
        self.city = city
        self.postal_code = postal_code
        self.country = country
        self.date_of_birth = date_of_birth
        self.gender = gender
        self.avatar_id = avatar_id
        self.status = status
        self.two_factor_enabled = two_factor_enabled
        self.registered_on = registered_on
        self.points = points

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role}, status={self.status})>"