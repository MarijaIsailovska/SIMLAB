# routes/virtual_lab.py
from flask import Blueprint, render_template, request, jsonify, session
from utils.database_manager import DatabaseManager  # <-- ако е на друго место, прилагоди

bp = Blueprint("virtual_lab", __name__)

# Паге со симулацијата
@bp.get("/virtual-lab")
def virtual_lab_page():
    elements = DatabaseManager.get_all_elements() or []
    return render_template("virtual_labaratory.html", elements=elements)

# Хелпери
def _find_reaction(e1_id: int, e2_id: int):
    sql = """
      SELECT r.*,
             e1.symbol AS e1_symbol, e1.element_name AS e1_name, e1.hazard_type AS e1_hz,
             e2.symbol AS e2_symbol, e2.element_name AS e2_name, e2.hazard_type AS e2_hz
        FROM reaction r
        JOIN elements e1 ON r.element1_id = e1.element_id
        JOIN elements e2 ON r.element2_id = e2.element_id
       WHERE (r.element1_id = %s AND r.element2_id = %s)
          OR (r.element1_id = %s AND r.element2_id = %s)
       LIMIT 1
    """
    rows = DatabaseManager.execute_query(sql, (e1_id, e2_id, e2_id, e1_id)) or []
    return rows[0] if rows else None

def _get_element(el_id: int):
    return DatabaseManager.get_element_by_id(el_id) or {}

def _hz_factor(hz: str | None) -> float:
    if not hz:
        return 1.0
    hz = hz.lower()
    if "flamm" in hz or "оган" in hz:
        return 1.4
    if "corros" in hz or "кисел" in hz or "короз" in hz:
        return 1.25
    if "toxic" in hz or "токс" in hz:
        return 1.2
    return 1.0

def _simulate_curve(reactivity: float, duration_sec=60):
    amb, k, cool = 25.0, 0.9, 0.05
    t, T = 0, amb
    times, temps = [], []
    while t <= duration_sec:
        times.append(t); temps.append(T)
        dT = k*reactivity - cool*(T - amb)
        T = T + dT
        t += 1
    return times, temps

# API: симулација
@bp.post("/api/simulate-reaction")
def simulate_reaction():
    data = request.get_json(force=True)
    e1 = int(data.get("element1_id"))
    e2 = int(data.get("element2_id"))
    amount = float(data.get("amount") or 1.0)

    rxn = _find_reaction(e1, e2)
    el1 = _get_element(e1)
    el2 = _get_element(e2)

    # едноставен (дидактички) модел за реактивност
    an1 = el1.get("atomic_number") or 10
    an2 = el2.get("atomic_number") or 10
    hz = _hz_factor(el1.get("hazard_type")) * _hz_factor(el2.get("hazard_type")) * (1.1 if rxn else 1.0)
    reactivity = (an1 + an2) / 5.0 * hz * amount

    times, temps = _simulate_curve(reactivity, duration_sec=60)

    return jsonify({
        "ok": True,
        "reaction": {
            "found": bool(rxn),
            "reaction_id": rxn.get("reaction_id") if rxn else None,
            "product": rxn.get("product") if rxn else None,
            "conditions": rxn.get("conditions") if rxn else None,
            "e1": {"id": e1, "symbol": el1.get("symbol"), "name": el1.get("element_name")},
            "e2": {"id": e2, "symbol": el2.get("symbol"), "name": el2.get("element_name")},
        },
        "series": {"time": times, "temperature": temps}
    })

# API: зачувување експеримент + учество
@bp.post("/save-experiment")
def save_experiment():
    """
    Очекува JSON: reaction_id, result, safety_warning
    Креира ред во experiment и логира во userparticipatesinexperiment за тековниот user.
    """
    data = request.get_json(force=True)
    reaction_id = int(data.get("reaction_id"))
    result = data.get("result") or "Виртуелна симулација"
    safety = data.get("safety_warning") or None

    # user од сесија (прилагоди на твојата апликација)
    user = session.get("user") or {}
    user_id = user.get("user_id")

    if not user_id:
        return jsonify({"success": False, "message": "Немаш активна сесија."}), 401

    me = DatabaseManager.get_user_by_id(user_id)  # дава role и teacher_id ако е студент
    if not me:
        return jsonify({"success": False, "message": "Корисникот не е најден."}), 400

    # teacher_id за experiment: ако си teacher -> самиот, ако си student -> неговиот teacher
    teacher_id = me.get("user_id") if me.get("role") == "teacher" else me.get("teacher_id")
    if not teacher_id:
        return jsonify({"success": False, "message": "Недостасува teacher_id за експеримент."}), 400

    exp_id = DatabaseManager.insert_experiment(teacher_id, reaction_id, result, safety)
    if not exp_id:
        return jsonify({"success": False, "message": "Креирањето експеримент не успеа."}), 500

    DatabaseManager.track_experiment_participation(user_id, exp_id)
    return jsonify({"success": True, "experiment_id": exp_id})
