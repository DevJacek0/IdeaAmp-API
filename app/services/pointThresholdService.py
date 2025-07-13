from typing import List, Optional
from app.models.pointThreshold import PointThreshold
from app.services.service import Service
from sqlalchemy import Column, Integer, DECIMAL, String, TIMESTAMP, Boolean, BigInteger, func


class PointThresholdService(Service):
    def __init__(self):
        """
        Konstruktor klasy PointThresholdService, który inicjalizuje klasę bazową Service.
        """
        super().__init__(
            table_name="point_thresholds",
            load_recipe={
                "identifier": "id",
                "function": self._row_to_threshold
            }
        )

    def _row_to_threshold(self, row: dict) -> PointThreshold:
        return PointThreshold(
            id=row["id"],
            points_required=row["points_required"],
            discount_value=row["discount_value"],
            description=row.get("description"),
            created_on=row["created_on"],
            is_active=row["is_active"]
        )

    def _get_columns(self) -> List[Column]:
        return [
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('points_required', Integer, nullable=False),
            Column('discount_value', DECIMAL(5, 2), nullable=False),
            Column('description', String(255)),
            Column('created_on', BigInteger, nullable=False),
            Column('is_active', Boolean, default=True)
        ]

    def create_threshold(self, points_required: int, discount_value: float, description: str = None) -> Optional[PointThreshold]:
        """
        Tworzy próg punktowy

        Argumenty:
            points_required (int): Wymagana liczba punktów
            discount_value (float): Wartosc znizki
            description (str): Opis

        Zwraca:
            PointThreshold: Prog punktowy
        """
        session = self.Session()
        try:
            next_id = session.query(func.max(PointThreshold.id)).scalar() + 1 if session.query(PointThreshold.id).count()\
                                                                                 > 0 else 1
            threshold = PointThreshold(
                id=next_id,
                points_required=points_required,
                discount_value=discount_value,
                description=description
            )
            session.add(threshold)
            session.commit()
            
            refreshed_threshold = session.merge(threshold)
            self.set(refreshed_threshold.id, refreshed_threshold)
            return refreshed_threshold
        except Exception as e:
            session.rollback()
            print(f"[Error] Błąd podczas tworzenia progu punktowego: {e}")
            return None
        finally:
            session.close()

    def get_available_thresholds(self) -> List[PointThreshold]:
        """
        Zwraca listę aktywnych progów punktowych posortowanych po wymaganej liczbie punktów

        Zwraca:
            List[PointThreshold]: Lista obiektów progu punktowego
        """
        return sorted(
            [t for t in self.get_all() if t.is_active],
            key=lambda x: x.points_required
        )

    def delete_threshold(self, threshold_id: int) -> bool:
        """
        Usuwa próg punktowy

        Argumenty:
            threshold_id (int): ID progu punktowego do usunięcia

        Zwraca:
            bool: True jeśli operacja się powiodła, False w przeciwnym razie
        """
        session = self.Session()
        try:
            threshold = session.query(PointThreshold).get(threshold_id)
            if not threshold:
                return False
            
            session.delete(threshold)
            session.commit()
            
            self.clear(threshold_id)
            return True
        except Exception as e:
            session.rollback()
            print(f"[Error] Błąd podczas usuwania progu punktowego: {e}")
            return False
        finally:
            session.close()

    def deactivate_threshold(self, threshold_id: int) -> bool:
        """
        Dezaktywuje próg punktowy zamiast go usuwać

        Argumenty:
            threshold_id (int): ID progu punktowego do dezaktywacji

        Zwraca:
            bool: True jeśli operacja się powiodła, False w przeciwnym razie

        """
        session = self.Session()
        try:
            threshold = session.query(PointThreshold).get(threshold_id)
            if not threshold:
                return False
            
            threshold.is_active = False
            session.commit()
            
            refreshed_threshold = session.merge(threshold)
            self.set(refreshed_threshold.id, refreshed_threshold)
            return True
        except Exception as e:
            session.rollback()
            print(f"[Error] Błąd podczas dezaktywacji progu punktowego: {e}")
            return False
        finally:
            session.close() 