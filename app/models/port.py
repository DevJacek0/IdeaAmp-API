from app import db


class Port(db.Model):
    """
    Model dla portów

    Atrybuty:
        id (int): Identyfikator portu
        station_id (int): Identyfikator stacji
        max_power (float): Maksymalna moc portu
        connector_type (str): Rodzaj ładowarki
        status (str): Status portu
    """
    __tablename__ = "ports"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    station_id = db.Column(db.Integer, db.ForeignKey('stations.id'), nullable=False)
    max_power = db.Column(db.DECIMAL(5, 2), nullable=False)
    connector_type = db.Column(db.Enum('Type1', 'Type2', 'CCS', 'CHAdeMO', 'Tesla NACS', 
                                     name='connector_types'), nullable=False)
    status = db.Column(db.Enum('Available', 'InUse', 'Faulty', 'Maintenance', 
                              name='port_status'), nullable=False)

    def __init__(self, id, station_id, max_power, connector_type, status='Available'):
        self.id = id
        self.station_id = station_id
        self.max_power = max_power
        self.connector_type = connector_type
        self.status = status

    def __repr__(self):
        return f"<Port(id={self.id}, station_id={self.station_id}, status={self.status})>"

    def to_dict(self):
        return {
            'id': self.id,
            'station_id': self.station_id,
            'max_power': self.max_power,
            'connector_type': self.connector_type,
            'status': self.status
        }