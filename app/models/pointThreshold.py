from sqlalchemy import BigInteger

from app import db
from datetime import datetime


class PointThreshold(db.Model):
    """
    Model dla przechowywania informacji o procentach zniżek

    Atrybuty:
        id (int): Identyfikator procentu zniżki
        points_required (int): Liczba punktów wymaganych do uzyskania zniżki
        discount_value (float): Procent zniżki
        description (str): Opis zniżki
        created_on (unix timestamp): Data utworzenia zniżki
        is_active (bool): Czy zniżka jest aktywna

    """
    __tablename__ = "point_thresholds"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    points_required = db.Column(db.Integer, nullable=False)
    discount_value = db.Column(db.DECIMAL(5, 2), nullable=False)
    description = db.Column(db.String(255))
    created_on = db.Column(db.BigInteger, nullable=False, default=lambda: int(datetime.utcnow().timestamp() * 1000))
    is_active = db.Column(db.Boolean, default=True)

    def __init__(self, id: int, points_required: int, discount_value: float, description: str = None,
                 created_on = None, is_active: bool = True):
        self.id = id
        self.points_required = points_required
        self.discount_value = discount_value
        self.description = description
        self.created_on = created_on
        self.is_active = is_active

    def __repr__(self):
        return f"<PointThreshold(id={self.id}, points_required={self.points_required}, discount_value={self.discount_value}, description={self.description})>"
