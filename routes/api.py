from flask import Blueprint, request, jsonify
from utils.database_manager import DatabaseManager
import logging

log = logging.getLogger(__name__)
api_bp = Blueprint("api_bp", __name__)

@api_bp.post("/api/simulate-reaction")
def simulate_reaction():
    try:
        payload = request.get_json(silent=True) or {}
        sym1 = (payload.get("element1") or "").strip()
        sym2 = (payload.get("element2") or "").strip()

        if not sym1 or not sym2:
            return jsonify(success=False, message="Недостасуваат елементи."), 400
        if sym1.upper() == sym2.upper():
            return jsonify(success=False, message="Ист елемент од двете страни не е дозволено."), 200

        rxn = DatabaseManager.get_reaction_by_symbols(sym1, sym2)
        if not rxn:
            return jsonify(success=False, message="Нема дефинирана реакција за оваа комбинација."), 200

        return jsonify(
            success=True,
            reaction_id=rxn["reaction_id"],
            product=rxn["product"],
            conditions=rxn.get("conditions"),
            elements=f"{sym1}+{sym2}",
        ), 200

    except Exception:
        log.exception("/api/simulate-reaction failed")
        # важно: враќаме JSON дури и на грешка, не HTML
        return jsonify(success=False, message="Внатрешна серверска грешка."), 500
