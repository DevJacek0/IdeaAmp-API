from app import db
from sqlalchemy.orm import relationship


class Attachment(db.Model):
    """
    Model przechowujacy informacje o plikach

    Atrybuty:
        id (int): id pliku
        path (str): sciezka do pliku
    """
    __tablename__ = "attachments"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    path = db.Column(db.Text, nullable=False)

    users = relationship("User", back_populates="avatar", foreign_keys="[User.avatar_id]")

    def __init__(self, id, path):
        self.id = id
        self.path = path

    def __repr__(self):
        return f"<Attachment(id={self.id}, path={self.path})>"
