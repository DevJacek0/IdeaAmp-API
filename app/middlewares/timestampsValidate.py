import time
import hmac
from flask import request, jsonify


def validate_request():
    """Globalna walidacja Timestampu. Anty atak Reply."""

    if request.method == "OPTIONS":
        return None

    if "ws" or "scan-qr" in request.url:
        return None

    timestamp = request.headers.get("timestamp")
    if not timestamp:
        return jsonify({"error": "Brak timestampu"}), 403

    try:
        timestamp = int(timestamp)
    except ValueError:
        return jsonify({"error": "Niepoprawny format timestampu"}), 403

    current_time = int(time.time())

    if abs(current_time - timestamp) > 30:
        return jsonify({"error": "Niepoprawny timestamp"}), 403
