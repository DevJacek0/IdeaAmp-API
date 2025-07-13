from app import db


class Station(db.Model):
    """
    Model dla stacji

    Atrybuty:
        id (int): Identyfikator stacji
        name (str): Nazwa stacji
        lat (float): Szerokość geograficzna stacji
        lng (float): Długość geograficzna stacji
        address (str): Adres stacji
        image_url (str): URL zdjecia stacji
        status (str): Status stacji
        opening_time (str): Godzina otwarcia stacji
        closing_time (str): Godzina zamkniecia stacji
        price_per_kwh (float): Cena za kWh
    """
    __tablename__ = "stations"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    lat = db.Column(db.DECIMAL(10, 8), nullable=False)
    lng = db.Column(db.DECIMAL(11, 8), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    status = db.Column(db.Enum('active', 'inactive', "maintenance", name='station_status'), nullable=False,
                       default='active')
    opening_time = db.Column(db.Time, nullable=False)
    closing_time = db.Column(db.Time, nullable=False)
    price_per_kwh = db.Column(db.DECIMAL(10, 2), nullable=False)

    def __init__(self, id, name, lat, lng, address, status='active', opening_time=None, closing_time=None,
                 price_per_kwh=None, image_url=None):
        self.id = id
        self.name = name
        self.lat = lat
        self.lng = lng
        self.address = address
        self.image_url = image_url
        self.status = status
        self.opening_time = opening_time
        self.closing_time = closing_time
        self.price_per_kwh = price_per_kwh


    def __repr__(self):
        return f"<Station(id={self.id}, name={self.name}, status={self.status})>"

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'latitude': self.lat,
            'longitude': self.lng,
            'status': self.status
        }
