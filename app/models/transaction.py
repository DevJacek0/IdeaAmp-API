from app import db
from datetime import datetime


class Transaction(db.Model):
    """
    Model dla transakcji

    Atrybuty:
        id (int) - identyfikator transakcji
        user_id (int) - identyfikator użytkownika
        station_id (int) - identyfikator stacji
        car_id (int) - identyfikator samochodu
        amount (float) - kwota transakcji
        type (str) - typ transakcji (dozwolone wartości: "TopUp", "Payment", "Refund")
        created_on (unix timestamp) - czas utworzenia transakcji
    """
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    station_id = db.Column(db.Integer, db.ForeignKey('stations.id'), nullable=True)
    car_id = db.Column(db.Integer, db.ForeignKey('cars.id'), nullable=True)
    amount = db.Column(db.DECIMAL(10, 2), nullable=False)
    type = db.Column(db.Enum('TopUp', 'Payment', 'Refund', name='transaction_types'), nullable=False)
    created_on = db.Column(db.BigInteger, nullable=False, default=lambda: int(datetime.utcnow().timestamp() * 1000))

    def __init__(self, id: int, user_id: int, station_id: int, car_id: int, amount: float, type: str, created_on=None):
        self.id = id
        self.user_id = user_id
        self.station_id = station_id
        self.car_id = car_id
        self.amount = amount
        self.type = type
        self.created_on = created_on