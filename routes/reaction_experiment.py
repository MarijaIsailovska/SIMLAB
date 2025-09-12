# SIMLAB/routes/reaction_experiment.py
import logging
from flask import Blueprint, request, jsonify
from utils.database_manager import DatabaseManager


bp = Blueprint("reaction_experiment", __name__, url_prefix="/api")
log = logging.getLogger(__name__)

@bp.post("/reaction-experiment")
def create_rxn_exp():
    data = request.get_json(silent=True) or {}

    # задолжителни полиња
    required = ["teacher_id", "element1_id", "element2_id"]
    missing = [k for k in required if data.get(k) in (None, "", [])]
    if missing:
        return jsonify({"ok": False, "error": f"Недостасува: {', '.join(missing)}"}), 400

    # нормализирај листа од equipment_ids ако ја има
    equipment_ids = data.get("equipment_ids")
    if equipment_ids is not None:
        if not isinstance(equipment_ids, list):
            return jsonify({"ok": False, "error": "equipment_ids мора да е листа од цели броеви"}), 400
        try:
            equipment_ids = [int(x) for x in equipment_ids]
        except Exception:
            return jsonify({"ok": False, "error": "equipment_ids содржи невалидни вредности"}), 400

    try:
        res = DatabaseManager.create_reaction_and_experiment(
            teacher_id=int(data["teacher_id"]),
            element1_id=int(data["element1_id"]),
            element2_id=int(data["element2_id"]),
            product=data.get("product"),
            conditions=data.get("conditions"),
            experiment_result=data.get("experiment_result"),
            safety_warning=data.get("safety_warning"),
            equipment_ids=equipment_ids,
        )
        if not res:
            return jsonify({"ok": False, "error": "Креирањето не успеа"}), 500

        return jsonify({"ok": True, **res}), 201

    except Exception:
        log.exception("create_rxn_exp failed")
        return jsonify({"ok": False, "error": "Внатрешна грешка"}), 500
