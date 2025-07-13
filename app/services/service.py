from sqlalchemy import MetaData, Table, Column, Integer, select, inspect
from sqlalchemy.orm import sessionmaker
from typing import Callable, Dict, Any
from app import db
from flask import current_app


class Service:
    """
    Klasa służąca do przechowywania i konfigurowania podstawowych ustawień zarządzania cachem oraz bazą danych.
    """

    _global_cache = {}

    def __init__(self, table_name: str, load_recipe: Dict[str, Callable[[Dict[str, Any]], Any]]):
        """
        Konstruktor klasy Service.

        Argumenty:
            table_name (str): Nazwa tabeli w bazie danych.
            load_recipe (Dict[str, Callable[[Dict[str, Any]], Any]]): Przepis do wczytywania danych z tabeli.
        """
        self._table_name = table_name
        self._load_recipe = load_recipe

        with current_app.app_context():
            self.metadata = MetaData()
            if not inspect(db.engine).has_table(self._table_name):
                try:
                    self._create_table()
                except Exception as e:
                    print(f"[Error] Failed to create table {self._table_name}: {e}")
            self.table = Table(self._table_name, self.metadata, autoload_with=db.engine)

        self.Session = sessionmaker(bind=db.engine)

        if self._table_name not in Service._global_cache:
            Service._global_cache[self._table_name] = {}
            self.load()

    def load(self):
        """
        Wczytuje dane z tabeli w bazie danych i ustawia je w cache.
        """
        session = self.Session()
        try:
            query = select(self.table)
            results = session.execute(query).fetchall()

            for row in results:
                data_dict = {column.name: value for column, value in zip(self.table.columns, row)}
                obj = self._load_recipe['function'](data_dict)
                identifier = data_dict[self._load_recipe['identifier']]
                Service._global_cache[self._table_name][identifier] = obj

            print(f"[Database] Loaded {len(results)} entries from table {self._table_name}!")
        except Exception as e:
            print(f"[Error] Failed to load data from table {self._table_name}: {e}")
        finally:
            session.close()

    def _create_table(self):
        """
        Metoda do tworzenia tabeli w bazie danych.
        """
        if not hasattr(self, '_get_columns') or not callable(getattr(self, '_get_columns')):
            raise NotImplementedError(
                f"Class '{self.__class__.__name__}' must implement the '_get_columns' method. "
                f"if the table '{self._table_name}' does not exist."
            )

        columns = self._get_columns()
        if self._table_name in self.metadata.tables:
            return

        if not any(col.primary_key for col in columns):
            columns.insert(0, Column('id', Integer, primary_key=True, autoincrement=True))

        table = Table(self._table_name, self.metadata, *columns)

        self.metadata.create_all(db.engine)

    def set(self, id, obj):
        """
        Metoda do ustawiania obiektu w cache.

        Argumenty:
            id (int): Identyfikator obiektu.
            obj (Any): Obiekt do ustawienia.
        """
        Service._global_cache[self._table_name][id] = obj

    def has(self, id):
        """
        Metoda do sprawdzania czy obiekt jest w cache.

        Argumenty:
            id (int): Identyfikator obiektu.

        Zwraca:
            bool: True jesli obiekt jest w cache, False w przeciwnym przypadku.
        """
        return id in Service._global_cache[self._table_name]

    def clear(self, id):
        """
        Metoda do czyszczenia obiektu z cache.

        Argumenty:
            id (int): Identyfikator obiektu.
        """
        if id in Service._global_cache[self._table_name]:
            del Service._global_cache[self._table_name][id]

    def get(self, id):
        """
        Metoda do pobierania obiektu z cache.

        Argumenty:
            id (int): Identyfikator obiektu.

        Zwraca:
            Any: Obiekt z cache.
        """
        return Service._global_cache[self._table_name].get(id)

    def get_all(self):
        """
        Metoda do pobierania wszystkich obiektów z cache.

        Zwraca:
            List[Any]: Lista obiektów z cache.
        """
        return list(Service._global_cache[self._table_name].values())

    @staticmethod
    def cache_get(key):
        """
        Metoda statyczna do pobierania obiektów z kluczami z cache.

        Argumenty:
            key (str): Klucz obiektu w cache.

        Zwraca:
            Any: Obiekt z cache.
        """
        return Service._global_cache.get(key)

    @staticmethod
    def cache_set(key, value):
        """
        Metoda statyczna do ustawiania obiektów z kluczami w cache.

        Argumenty:
            key (str): Klucz obiektu w cache.
            value (Any): Obiekt do ustawienia.
        """
        Service._global_cache[key] = value