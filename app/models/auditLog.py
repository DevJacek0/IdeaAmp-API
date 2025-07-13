from datetime import datetime

from app import db


class AuditLog(db.Model):
    """
    Model dla logowania akcji

    Atrybuty:
        id (int): Identyfikator logu
        user_id (int): Identyfikator użytkownika
        action (str): Akcja wykonana
        details (dict): Dodatkowe informacje
        created_on (unix timestamp): Czas utworzenia unix timestamp
    """
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(255), nullable=False)
    details = db.Column(db.JSON, nullable=True)
    created_on = db.Column(db.BigInteger, nullable=False, default=lambda: int(datetime.utcnow().timestamp() * 1000))

    def __init__(self, id, user_id, action, details=None, created_on=None):
        self.id = id
        self.user_id = user_id
        self.action = action
        self.details = details
        self.created_on = created_on

    def __repr__(self):
        return f"<AuditLog(id={self.id}, user_id={self.user_id}, action={self.action})>"
