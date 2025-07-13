from sqlalchemy import BigInteger

from app import db
from datetime import datetime

class Car(db.Model):
    """
    Model dla pojazdów

    Atrybuty:
        id (int): Identyfikator pojazdu
        owner_id (int): Identyfikator właściciela
        plate (str): Rejestracja pojazdu
        name (str): Nazwa pojazdu
        battery_capacity (float): Pojemność baterii pojazdu
        max_charging_power (float): Maksymalna moc ładowania pojazdu
        connector_type (str): Typ ładowarki pojazdu
        country_code (str): Kod kraju rejestracji pojazdu (np. 'PL')
        year (int): Rok produkcji pojazdu
        registered_on (unix timestamp): Data rejestracji pojazdu
    """
    __tablename__ = "cars"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    owner_id = db.Column(db.Integer, nullable=False)
    plate = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    battery_capacity = db.Column(db.DECIMAL(5, 2), nullable=False)
    max_charging_power = db.Column(db.DECIMAL(5, 2), nullable=False)
    connector_type = db.Column(db.Enum('Type1', 'Type2', 'CCS', 'CHAdeMO', 'Tesla NACS', name='connector_types'), nullable=False)
    country_code = db.Column(db.String(2), nullable=True)
    year = db.Column(db.Integer, nullable=False)
    registered_on = db.Column(db.BigInteger, nullable=False, default=lambda: int(datetime.utcnow().timestamp() * 1000))

    def __init__(self, id: int, owner_id: int, plate: str, name: str, 
                 battery_capacity: float, max_charging_power: float, 
                 connector_type: str, year: int, country_code: str, 
                 registered_on: BigInteger):
        self.id = id
        self.owner_id = owner_id
        self.plate = plate
        self.name = name
        self.battery_capacity = battery_capacity
        self.max_charging_power = max_charging_power
        self.connector_type = connector_type
        self.country_code = country_code
        self.year = year
        self.registered_on = registered_on
        


    def __repr__(self):
        return f"<Car(id={self.id}, plate={self.plate}, owner_id={self.owner_id})>"
