from functools import wraps
from flask import request, jsonify
from math import ceil


def paginate(fn):
    """
    Dekorator paginacji.

    Dodaje funkcjonalność paginacji do udekorowanej funkcji. Obsługuje parametry zapytania
    ``page`` i ``per_page`` w celu określenia numeru strony i liczby elementów na stronę.

    Parametry zapytania:\n
    - ``page`` (int): Numer strony (domyślnie 1).\n
    - ``per_page`` (int): Liczba elementów na stronę (domyślnie 10, maksymalnie 100).
    - ``order`` (str): Kierunek sortowania (domyślnie 'desc').

    Zwraca:\n
    - ``200`` **OK**: Wynik paginacji w formacie JSON, zawierający elementy i informacje o paginacji.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """
    
    @wraps(fn)
    def wrapper(*args, **kwargs):
        page: int = request.args.get('page', 1, type=int)
        per_page: int = request.args.get('per_page', 10, type=int)
        order: str = request.args.get('order', 'desc', type=str).lower()

        if per_page > 100:
            per_page = 100

        if page < 1:
            page = 1

        result = fn(*args, **kwargs)

        if isinstance(result, list):
            reverse_order = order == 'desc'
            result.sort(key=lambda x: x['id'], reverse=reverse_order)
            total_items: int = len(result)
            total_pages: int = ceil(total_items / per_page)

            if page > total_pages > 0:
                page = total_pages

            start_idx: int = (page - 1) * per_page
            end_idx: int = start_idx + per_page
            paginated_items: list = result[start_idx:end_idx]

            return jsonify({
                "items": paginated_items,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
            }), 200

        return result

    return wrapper