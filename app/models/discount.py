from sqlalchemy import BigInteger

from app import db
from datetime import datetime


class Discount(db.Model):
    """
    Model dla rabatów

    Atrybuty:
        id (int): Identyfikator rabatu
        code (str): Kod rabatu
        value (float): Wartość rabatu
        expiry_on (int): Data wygaśnięcia rabatu
        usage_count (int): Liczba użycia rabatu
        max_uses (int): Maksymalna liczba użycia rabatu
    """
    __tablename__ = "discounts"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(50), nullable=False, unique=True)
    value = db.Column(db.DECIMAL(5, 2), nullable=False)
    expiry_on = db.Column(db.BigInteger, nullable=True)
    usage_count = db.Column(db.Integer, nullable=False, default=0)
    max_uses = db.Column(db.Integer, nullable=True)

    def __init__(self, id: int, code: str, value: float, expiry_on: float, max_uses: int = None, usage_count: int = 0):
        self.id = id
        self.code = code
        self.value = value
        self.expiry_on = expiry_on
        self.max_uses = max_uses
        self.usage_count = usage_count

    def is_valid(self) -> bool:
        current_timestamp = int(datetime.utcnow().timestamp() * 1000)
        if self.expiry_on and current_timestamp > self.expiry_on:
            return False
        if self.max_uses is not None and self.usage_count >= self.max_uses:
            return False
        return True
