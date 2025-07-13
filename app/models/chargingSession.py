from datetime import datetime

from app import db


class ChargingSession(db.Model):

    """
    Model dla sesji ładowania

    Atrybuty:
        id (int): Identyfikator sesji ładowania
        user_id (int): Identyfikator użytkownika
        port_id (int): Identyfikator portu ładowania
        car_id (int): Identyfikator samochodu
        started_on (unix timestamp): Czas rozpoczęcia ładowania
        end_on (unix timestamp): Czas zakończenia ładowania
        energy_consumed (float): Zużycie energii
        power_limit (float): Limit moc ładowania
        cost (float): Koszt ładowania
    """
    __tablename__ = "charging_sessions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    port_id = db.Column(db.Integer, nullable=False)
    car_id = db.Column(db.Integer, nullable=True)
    started_on = db.Column(db.BigInteger, nullable=False, default=lambda: int(datetime.utcnow().timestamp() * 1000))
    end_on = db.Column(db.BigInteger, nullable=True)
    energy_consumed = db.Column(db.DECIMAL(10, 2), nullable=True)
    power_limit = db.Column(db.DECIMAL(5, 2), nullable=True)
    cost = db.Column(db.DECIMAL(10, 2), nullable=True)

    def __init__(self, id, user_id, port_id, car_id, started_on=None, end_on=None, energy_consumed=None, power_limit=None, cost=None):
        self.id = id
        self.user_id = user_id
        self.port_id = port_id
        self.car_id = car_id
        self.started_on = started_on
        self.end_on = end_on
        self.energy_consumed = energy_consumed
        self.power_limit = power_limit
        self.cost = cost

    def __repr__(self):
        return f"<ChargingSession(id={self.id}, user_id={self.user_id}, port_id={self.port_id})>"
