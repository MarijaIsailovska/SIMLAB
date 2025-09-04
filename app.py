from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
from psycopg2.errors import ForeignKeyViolation
from functools import wraps
from utils.database_manager import DatabaseManager
from utils.auth_manager import AuthManager

app = Flask(__name__)
app.secret_key = 'simlab-secret-key-2024'
app.config['JSON_AS_ASCII'] = False


# ------------------------------
# Helpers / Decorators
# ------------------------------
def require_login(role=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return wrapper
    return decorator


def _render_generic(title, rows):
    headers = list(rows[0].keys()) if rows else []
    return render_template('reports/generic_report.html', title=title, headers=headers, rows=rows)


def _enrich_with_equipment(exp_rows):
    enriched = []
    for row in (exp_rows or []):
        exp = dict(row)
        exp['equipment'] = DatabaseManager.get_experiment_equipment(exp['experiment_id']) or []
        enriched.append(exp)
    return enriched


# ------------------------------
# Home / Auth
# ------------------------------
@app.route('/')
def index():
    return '''
    <h1>🧪 SIMLAB - Виртуелна Хемиска Лабораторија</h1>
    <h3>📊 SQL пристап за Бази на Податоци</h3>
    <ul>
        <li><a href="/users">👥 Прикажи корисници</a></li>
        <li><a href="/elements">🔬 Прикажи хемиски елементи</a></li>
        <li><a href="/equipment">🛠 Прикажи лабораториска опрема</a></li>
        <li><a href="/reports">📈 SQL Извештаи</a></li>
        <li><a href="/test-db">🔍 Тестирај база</a></li>
    </ul>
    '''


@app.route('/test-db')
def test_db():
    if DatabaseManager.test_connection():
        return jsonify({'status': 'success', 'message': 'Успешно поврзување со факултетската база!'})
    return jsonify({'status': 'error', 'message': 'Грешка при поврзување'})


@app.route('/users')
def users():
    users = DatabaseManager.get_all_users()
    if users:
        return jsonify({
            'status': 'success',
            'sql_query': 'SELECT user_id, user_name, user_surname, email, role FROM "User" ORDER BY user_name',
            'count': len(users),
            'data': users
        })
    return jsonify({'status': 'error', 'message': 'Нема корисници'})


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password']
        user = DatabaseManager.authenticate_user(email, password)
        if user and AuthManager.verify_password(password, user['password']):
            session['user_id'] = user['user_id']
            session['user_name'] = user['user_name']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Погрешен email или лозинка')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    teachers = DatabaseManager.get_all_teachers()
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        teacher_id = request.form.get('teacher_id') if role == 'student' else None
        password_hash = AuthManager.hash_password(password)
        user_id = DatabaseManager.register_user(name, surname, email, password_hash, role, teacher_id)
        if user_id:
            return redirect(url_for('login'))
        return render_template('register.html', error='Грешка при регистрација', teachers=teachers)
    return render_template('register.html', teachers=teachers)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# ------------------------------
# Dashboard
# ------------------------------
@app.route('/dashboard')
@require_login()
def dashboard():
    if session['role'] == 'teacher':
        try:
            stats = DatabaseManager.get_teacher_dashboard_statistics(session['user_id'])
        except Exception:
            stats = {'student_count': 0, 'reaction_count': 0, 'experiment_count': 0, 'activity_count': 0}
        return render_template('dashboard_teacher.html', user_name=session['user_name'], stats=stats)
    else:
        try:
            stats = DatabaseManager.get_student_statistics(session['user_id'])
        except Exception:
            stats = {'experiment_count': 0, 'element_count': 0, 'equipment_count': 0, 'reaction_count': 0}
        return render_template('dashboard_student.html', user_name=session['user_name'], stats=stats)


@app.route('/api/dashboard-stats')
@require_login()
def dashboard_stats():
    try:
        if session['role'] == 'student':
            stats = DatabaseManager.get_student_statistics(session['user_id']) or {}
            stats = {
                'student_count': 0,
                'reaction_count': int(stats.get('reaction_count', 0)),
                'experiment_count': int(stats.get('experiment_count', 0)),
                'activity_count': 0
            }
        else:
            stats = DatabaseManager.get_teacher_dashboard_statistics(session['user_id']) or {}
            stats = {
                'student_count': int(stats.get('student_count', 0)),
                'reaction_count': int(stats.get('reaction_count', 0)),
                'experiment_count': int(stats.get('experiment_count', 0)),
                'activity_count': int(stats.get('activity_count', 0))
            }
        return jsonify(stats), 200
    except Exception as e:
        app.logger.exception("dashboard_stats failed")
        return jsonify({'error': f'Серверска грешка: {str(e)}'}), 500


@app.route('/api/debug-dashboard')
@require_login()
def api_debug_dashboard():
    uid = session['user_id']
    role = session.get('role')
    if role == 'teacher':
        stats = DatabaseManager.get_teacher_dashboard_statistics(uid)
    else:
        stats = DatabaseManager.get_student_statistics(uid)
    return jsonify({'session_user_id': uid, 'session_role': role, 'stats': stats}), 200


# ------------------------------
# Elements
# ------------------------------
@app.route('/elements')
@require_login()
def elements():
    elements_data = DatabaseManager.get_all_elements()
    if elements_data:
        return render_template('elements_list.html', elements=elements_data, user_role=session['role'])
    return render_template('elements_list.html', elements=[], error='Нема елементи во базата')


@app.route('/elements/<int:element_id>')
@require_login()
def element_detail(element_id):
    DatabaseManager.track_element_view(session['user_id'], element_id)
    element = DatabaseManager.get_element_by_id(element_id)
    if element:
        return render_template('element_detail.html', element=element, user_role=session['role'])
    return redirect(url_for('elements'))


@app.route('/elements/add', methods=['GET', 'POST'])
@require_login('teacher')
def add_element():
    if request.method == 'POST':
        symbol = request.form['symbol']
        name = request.form['name']
        atomic_number = int(request.form['atomic_number'])
        atomic_weight = float(request.form['atomic_weight'])
        melting_point = float(request.form['melting_point']) if request.form['melting_point'] else None
        boiling_point = float(request.form['boiling_point']) if request.form['boiling_point'] else None
        hazard_type = request.form['hazard_type']
        description = request.form['description']
        teacher_id = session['user_id']
        element_id = DatabaseManager.add_element(
            symbol, name, atomic_number, atomic_weight,
            melting_point, boiling_point, hazard_type, description, teacher_id
        )
        if element_id:
            return redirect(url_for('dashboard'))
        return render_template('add_element.html', error='Грешка при додавање на елементот')
    return render_template('add_element.html')


@app.route('/elements/<int:element_id>/edit', methods=['GET', 'POST'])
@require_login('teacher')
def edit_element(element_id):
    element = DatabaseManager.get_element_by_id(element_id)
    if not element:
        return redirect(url_for('elements'))
    if request.method == 'POST':
        symbol = request.form['symbol']
        name = request.form['name']
        atomic_number = int(request.form['atomic_number'])
        atomic_weight = float(request.form['atomic_weight'])
        melting_point = float(request.form['melting_point']) if request.form['melting_point'] else None
        boiling_point = float(request.form['boiling_point']) if request.form['boiling_point'] else None
        hazard_type = request.form['hazard_type']
        description = request.form['description']
        if DatabaseManager.update_element(
            element_id, symbol, name, atomic_number, atomic_weight,
            melting_point, boiling_point, hazard_type, description
        ):
            return redirect(url_for('elements'))
        return render_template('edit_element.html', element=element, error='Грешка при ажурирање')
    return render_template('edit_element.html', element=element)


# ------------------------------
# Equipment
# ------------------------------
@app.route('/equipment')
@require_login()
def equipment():
    equipment_data = DatabaseManager.get_all_equipment()
    if equipment_data:
        return render_template('equipment_list.html', equipment=equipment_data, user_role=session['role'])
    return render_template('equipment_list.html', equipment=[], error='Нема опрема во базата')


@app.route('/equipment/add', methods=['GET', 'POST'])
@require_login('teacher')
def add_equipment():
    if request.method == 'POST':
        name = request.form['name']
        equipment_type = request.form['type']
        description = request.form['description']
        safety_info = request.form['safety_info']
        teacher_id = session['user_id']
        equipment_id = DatabaseManager.add_lab_equipment(name, equipment_type, description, safety_info, teacher_id)
        if equipment_id:
            return redirect(url_for('dashboard'))
        return render_template('add_equipment.html', error='Грешка при додавање на опремата')
    return render_template('add_equipment.html')


@app.route('/equipment/<int:equipment_id>')
@require_login()
def equipment_detail(equipment_id):
    DatabaseManager.track_equipment_view(session['user_id'], equipment_id)
    equipment_data = DatabaseManager.get_all_equipment()
    equipment = None
    for item in (equipment_data or []):
        if item['equipment_id'] == equipment_id:
            equipment = item
            break
    if equipment:
        return render_template('equipment_detail.html', equipment=equipment, user_role=session['role'])
    return redirect(url_for('equipment'))


@app.route('/equipment/<int:equipment_id>/edit', methods=['GET', 'POST'])
@require_login('teacher')
def edit_equipment(equipment_id):
    equipment = DatabaseManager.get_equipment_by_id(equipment_id)
    if not equipment:
        return redirect(url_for('equipment'))
    if request.method == 'POST':
        name = request.form['name']
        equipment_type = request.form['type']
        description = request.form['description']
        safety_info = request.form['safety_info']
        if DatabaseManager.update_equipment(equipment_id, name, equipment_type, description, safety_info):
            return redirect(url_for('equipment'))
        return render_template('edit_equipment.html', equipment=equipment, error='Грешка при ажурирање')
    return render_template('edit_equipment.html', equipment=equipment)


# ------------------------------
# Reactions
# ------------------------------
@app.route('/reactions')
@require_login()
def reactions():
    reactions_data = DatabaseManager.get_all_reactions()
    return render_template('reactions_list.html', reactions=reactions_data, user_role=session['role'])


@app.route('/reactions/add', methods=['GET', 'POST'])
@require_login('teacher')
def add_reaction():
    if request.method == 'POST':
        try:
            element1_id = int(request.form['element1_id'])
            element2_id = int(request.form['element2_id'])
            product     = (request.form.get('product') or '').strip() or None
            conditions  = (request.form.get('conditions') or '').strip() or None
            temperature = (request.form.get('temperature') or '').strip()
            pressure    = (request.form.get('pressure') or '').strip()
            catalyst    = (request.form.get('catalyst') or '').strip()

            extra = []
            if temperature: extra.append(f"T={temperature}")
            if pressure:    extra.append(f"p={pressure}")
            if catalyst:    extra.append(f"катализатор={catalyst}")
            if extra:
                conditions = (conditions + "; " if conditions else "") + "; ".join(extra)

            experiment_result = (request.form.get('experiment_result') or '').strip() or None
            safety_warning    = (request.form.get('safety_warning') or '').strip() or None
            equipment_ids = [int(x) for x in request.form.getlist('equipment_ids')] or None

            if element1_id == element2_id:
                flash('Одбери два различни елементи.', 'warning')
                return redirect(url_for('add_reaction'))

            res = DatabaseManager.create_reaction_and_experiment(
                teacher_id=session['user_id'],
                element1_id=element1_id,
                element2_id=element2_id,
                product=product,
                conditions=conditions,
                experiment_result=experiment_result,
                safety_warning=safety_warning,
                equipment_ids=equipment_ids
            )
            if not res:
                flash('Неуспешно креирање (провери ID вредности).', 'danger')
                return redirect(url_for('add_reaction'))

            flash('Реакцијата и експериментот се успешно креирани.', 'success')
            return redirect(url_for('reactions'))

        except ForeignKeyViolation:
            flash('Погрешни ID вредности за елементи/наставник/опрема.', 'danger')
            return redirect(url_for('add_reaction'))
        except Exception as ex:
            flash(f'Настана грешка: {ex}', 'danger')
            return redirect(url_for('add_reaction'))

    elements  = DatabaseManager.get_all_elements()
    equipment = DatabaseManager.get_all_equipment()
    return render_template('add_reaction.html', elements=elements, equipment=equipment)


@app.route('/reactions/<int:reaction_id>/edit', methods=['GET', 'POST'])
@require_login('teacher')
def edit_reaction(reaction_id):
    reaction = DatabaseManager.get_reaction_by_id(reaction_id)
    if not reaction:
        return redirect(url_for('reactions'))
    elements = DatabaseManager.get_all_elements()
    if request.method == 'POST':
        element1_id = int(request.form['element1_id'])
        element2_id = int(request.form['element2_id'])
        product = request.form['product']
        conditions = request.form['conditions']
        if DatabaseManager.update_reaction(reaction_id, element1_id, element2_id, product, conditions):
            return redirect(url_for('reactions'))
        return render_template('edit_reaction.html', reaction=reaction, elements=elements, error='Грешка при ажурирање')
    return render_template('edit_reaction.html', reaction=reaction, elements=elements)


@app.route('/reactions/<int:reaction_id>/delete', methods=['POST'])
@require_login('teacher')
def delete_reaction(reaction_id):
    if DatabaseManager.delete_reaction(reaction_id):
        return redirect(url_for('reactions'))
    return redirect(url_for('reactions'))


# ------------------------------
# Laboratory + APIs
# ------------------------------
@app.route('/laboratory')
@require_login()
def laboratory():
    elements = DatabaseManager.get_all_elements()
    if session['role'] == 'teacher':
        return render_template('laboratory.html', elements=elements, user_role=session['role'])
    return render_template('virtual_laboratory.html', elements=elements, user_role=session['role'])


@app.route('/api/simulate-reaction', methods=['POST'])
@require_login()
def simulate_reaction():
    try:
        data = request.get_json(silent=True) or {}
        element1_symbol = (data.get('element1') or '').strip()
        element2_symbol = (data.get('element2') or '').strip()
        if not element1_symbol or not element2_symbol:
            return jsonify({'success': False, 'message': 'Недостигаат параметри (element1/element2)'}), 400

        reactions = DatabaseManager.get_all_reactions() or []
        for reaction in reactions:
            if ((reaction['element1_symbol'] == element1_symbol and reaction['element2_symbol'] == element2_symbol) or
                (reaction['element1_symbol'] == element2_symbol and reaction['element2_symbol'] == element1_symbol)):
                experiment = DatabaseManager.get_experiment_by_reaction(reaction['reaction_id'])
                return jsonify({
                    'success': True,
                    'product': reaction['product'],
                    'conditions': reaction.get('conditions'),
                    'reaction_id': reaction['reaction_id'],
                    'experiment_id': experiment['experiment_id'] if experiment else None,
                    'elements': f"{reaction['element1_name']} + {reaction['element2_name']}"
                }), 200

        return jsonify({
            'success': False,
            'message': f'Реакцијата меѓу {element1_symbol} и {element2_symbol} не е дефинирана во системот.'
        }), 200
    except Exception as e:
        app.logger.exception("simulate_reaction failed")
        return jsonify({'success': False, 'message': f'Серверска грешка: {str(e)}'}), 500


@app.route('/api/check-reaction', methods=['POST'])
@require_login()
def check_reaction():
    data = request.get_json() or {}
    element1_symbol = data.get('element1')
    element2_symbol = data.get('element2')
    reactions = DatabaseManager.get_all_reactions() or []
    for reaction in reactions:
        if ((reaction['element1_symbol'] == element1_symbol and reaction['element2_symbol'] == element2_symbol) or
            (reaction['element1_symbol'] == element2_symbol and reaction['element2_symbol'] == element1_symbol)):
            return jsonify({
                'success': True,
                'product': reaction['product'],
                'conditions': reaction['conditions'],
                'reaction_id': reaction['reaction_id']
            })
    return jsonify({'success': False, 'message': 'Реакцијата не е дефинирана во системот'})


@app.route('/save-experiment', methods=['POST'])
@require_login()
def save_experiment():
    data = request.get_json() or {}
    reaction_id = data.get('reaction_id')
    experiment = DatabaseManager.get_experiment_by_reaction(reaction_id)
    if not experiment:
        if session['role'] != 'teacher':
            return jsonify({'success': False, 'message': 'Не постои експеримент за оваа реакција. Контактирајте го вашиот професор.'})
        result_description = data.get('result', 'Експериментална симулација')
        safety_warning = data.get('safety_warning', 'Стандардни безбедносни мерки')
        experiment_id = DatabaseManager.insert_experiment(session['user_id'], reaction_id, result_description, safety_warning)
    else:
        experiment_id = experiment['experiment_id']
    if experiment_id:
        DatabaseManager.track_experiment_participation(session['user_id'], experiment_id)
        return jsonify({'success': True, 'experiment_id': experiment_id})
    return jsonify({'success': False, 'message': 'Грешка при зачувување'})


# ------------------------------
# Experiments
# ------------------------------
@app.route('/experiments')
@require_login()
def experiments():
    base = DatabaseManager.get_all_experiments()
    experiments = _enrich_with_equipment(base)
    return render_template('experiments_list.html', experiments=experiments, user_role=session['role'])


@app.route('/experiments/<int:experiment_id>')
@require_login()
def experiment_detail(experiment_id):
    experiments_list = DatabaseManager.get_all_experiments()
    experiment = None
    for exp in (experiments_list or []):
        if exp['experiment_id'] == experiment_id:
            experiment = exp
            break
    if not experiment:
        return redirect(url_for('experiments'))
    equipment = DatabaseManager.get_experiment_equipment(experiment_id)
    return render_template('experiment_detail.html', experiment=experiment, equipment=equipment, user_role=session['role'])


# ------------------------------
# Students (teacher view)
# ------------------------------
@app.route('/my_students')
@require_login('teacher')
def my_students():
    teacher_id = session['user_id']
    students_activity = DatabaseManager.get_my_students_activity(teacher_id)
    return render_template('my_students.html', students=students_activity, teacher_name=session['user_name'])


# ------------------------------
# My experiments (by role)
# ------------------------------
@app.route('/my-experiments')
@require_login()
def my_experiments():
    if session['role'] == 'student':
        base = DatabaseManager.get_student_participation_experiments(session['user_id'])
    else:
        base = DatabaseManager.get_user_experiments(session['user_id'])
    experiments = _enrich_with_equipment(base)
    return render_template('my_experiments.html', experiments=experiments, user_name=session['user_name'], user_role=session['role'])


# ------------------------------
# Reports (menu + basic)
# ------------------------------
@app.route('/reports')
@require_login('teacher')
def reports_menu():
    return render_template('reports/menu.html')


@app.route('/reports/equipment-usage')
@require_login('teacher')
def reports_equipment_usage():
    usage_report = DatabaseManager.get_equipment_usage_report()
    if usage_report:
        return jsonify({
            'status': 'success',
            'report_name': 'Извештај за користење на лабораториска опрема',
            'sql_query': '''
                SELECT le.equipment_name, COUNT(ele.experiment_id) AS usage_count
                FROM experimentlabequipment ele
                RIGHT JOIN labequipment le ON ele.equipment_id = le.equipment_id
                GROUP BY le.equipment_name
                ORDER BY usage_count DESC
            ''',
            'count': len(usage_report),
            'data': usage_report
        })
    return jsonify({'status': 'error', 'message': 'Грешка при генерирање на извештај'})


@app.route('/reports/teacher_statistics')
@require_login('teacher')
def reports_teacher_statistics():
    stats = DatabaseManager.get_teacher_statistics()
    return render_template('reports/teacher_statistics.html', statistics=stats)


@app.route('/reports/inactive_students')
@require_login('teacher')
def reports_inactive_students():
    teacher_id = session['user_id']
    students = DatabaseManager.get_students_without_experiments(teacher_id)
    return render_template('reports/inactive_students.html', students=students)


@app.route('/reports/element_views')
@require_login('teacher')
def reports_element_views():
    views_data = DatabaseManager.get_element_views_report()
    return render_template('reports/element_views.html', views=views_data)


@app.route('/reports/detailed_experiments')
@require_login('teacher')
def reports_detailed_experiments():
    teacher_id = session['user_id']
    experiments = DatabaseManager.get_students_experiments_detailed(teacher_id)
    return render_template('reports/detailed_experiments.html', experiments=experiments)


@app.route('/reports/low_activity_students')
@require_login('teacher')
def reports_low_activity_students():
    teacher_id = session['user_id']
    students = DatabaseManager.get_students_with_few_experiments(teacher_id, 3)
    return render_template('reports/low_activity_students.html', students=students)


@app.route('/reports/student_experiments')
@require_login('teacher')
def reports_student_experiments():
    teacher_id = session['user_id']
    experiments = DatabaseManager.get_students_experiments_for_teacher(teacher_id)
    return render_template('reports/student_experiments.html', student_experiments=experiments)


@app.route('/reports/user_activity')
@require_login('teacher')
def reports_user_activity():
    summary = DatabaseManager.get_user_activity_summary()
    return render_template('reports/user_activity.html', summary=summary)


# ------------------------------
# Advanced Reports (SQL)
# ------------------------------
@app.route('/reports/adv/student_experiment_counts')
@require_login('teacher')
def reports_adv_student_experiment_counts():
    sql = """
        SELECT 
            s.student_id,
            u.user_name || ' ' || u.user_surname AS full_name,
            COUNT(up.experiment_id) AS total_experiments
        FROM student s
        JOIN "User" u ON s.student_id = u.user_id
        LEFT JOIN userparticipatesinexperiment up ON s.student_id = up.user_id
        LEFT JOIN experiment e ON up.experiment_id = e.experiment_id
        WHERE s.teacher_id = %s
        GROUP BY s.student_id, full_name
        ORDER BY total_experiments DESC, full_name
    """
    rows = DatabaseManager.execute_query(sql, (session['user_id'],)) or []
    return _render_generic("Студенти и број на извршени експерименти", rows)


@app.route('/reports/adv/equipment_usage')
@require_login('teacher')
def reports_adv_equipment_usage():
    sql = """
        SELECT 
            le.equipment_name,
            COUNT(ele.experiment_id) AS usage_count
        FROM experimentlabequipment ele
        JOIN labequipment le ON ele.equipment_id = le.equipment_id
        GROUP BY le.equipment_name
        ORDER BY usage_count DESC, le.equipment_name
    """
    rows = DatabaseManager.execute_query(sql) or []
    return _render_generic("Користеност на лабораториска опрема", rows)


@app.route('/reports/adv/students_experiments_detailed')
def reports_adv_students_experiments_detailed():
    if 'user_id' not in session or session.get('role') != 'teacher':
        return redirect('/login')

    sql = """
        SELECT 
            s.student_id,
            u.user_name || ' ' || u.user_surname AS full_name,
            e.experiment_id,
            e.result,
            up.participation_timestamp AS participation_time
        FROM student s
        JOIN "User" u ON s.student_id = u.user_id
        JOIN userparticipatesinexperiment up ON s.student_id = up.user_id
        JOIN experiment e ON up.experiment_id = e.experiment_id
        WHERE s.teacher_id = %s
        ORDER BY full_name, participation_time DESC
    """
    rows = DatabaseManager.execute_query(sql, (session['user_id'],)) or []

    # Ако сакаш брзо да провериш дали има глобални податоци без филтер по професор:
    if not rows and request.args.get('all') == '1':
        sql_all = sql.replace("WHERE s.teacher_id = %s", "")
        rows = DatabaseManager.execute_query(sql_all) or []

    return _render_generic("Детален извештај: студенти и експерименти", rows)

@app.route('/reports/adv/experiment_participants')
@require_login('teacher')
def reports_adv_experiment_participants():
    experiment_id = request.args.get('experiment_id', type=int)
    if not experiment_id:
        exps = DatabaseManager.execute_query(
            "SELECT experiment_id, result FROM experiment ORDER BY experiment_id DESC"
        ) or []
        return render_template('reports/experiment_participants.html', experiments=exps)

    sql = """
        SELECT 
            s.student_id,
            u.user_name || ' ' || u.user_surname AS full_name,
            e.experiment_id,
            e.result
        FROM student s
        JOIN "User" u ON s.student_id = u.user_id
        JOIN userparticipatesinexperiment up ON s.student_id = up.user_id
        JOIN experiment e ON up.experiment_id = e.experiment_id
        WHERE s.teacher_id = %s AND e.experiment_id = %s
        ORDER BY u.user_name
    """
    rows = DatabaseManager.execute_query(sql, (session['user_id'], experiment_id)) or []
    return _render_generic(f"Студенти кои го извршиле експеримент #{experiment_id}", rows)


@app.route('/reports/adv/avg_equipment_per_experiment')
@require_login('teacher')
def reports_adv_avg_equipment_per_experiment():
    sql = """
        SELECT 
            COALESCE(AVG(instrument_count), 0) AS average_lab_equipment_per_experiment
        FROM (
            SELECT e.experiment_id, COUNT(ele.equipment_id) AS instrument_count
            FROM experiment e
            LEFT JOIN experimentlabequipment ele ON e.experiment_id = ele.experiment_id
            GROUP BY e.experiment_id
        ) subquery
    """
    rows = DatabaseManager.execute_query(sql) or []
    return _render_generic("Просечен број инструменти по експеримент", rows)


@app.route('/reports/adv/most_used_elements')
@require_login('teacher')
def reports_adv_most_used_elements():
    sql = """
        SELECT 
            el.element_name,
            COUNT(r.reaction_id) AS total_uses
        FROM elements el
        JOIN reaction r 
          ON el.element_id = r.element1_id 
          OR el.element_id = r.element2_id
        GROUP BY el.element_name
        ORDER BY total_uses DESC, el.element_name
    """
    rows = DatabaseManager.execute_query(sql) or []
    return _render_generic("Најчесто користени елементи во експерименти", rows)


@app.route('/reports/adv/most_performed_experiments')
@require_login('teacher')
def reports_adv_most_performed_experiments():
    sql = """
        SELECT 
            e.experiment_id,
            e.result,
            COUNT(up.user_id) AS student_participation
        FROM experiment e
        LEFT JOIN userparticipatesinexperiment up 
               ON e.experiment_id = up.experiment_id
        GROUP BY e.experiment_id, e.result
        ORDER BY student_participination DESC, e.experiment_id
    """
    sql = sql.replace("student_participination", "student_participation")
    rows = DatabaseManager.execute_query(sql) or []
    return _render_generic("Најчесто реализирани експерименти", rows)


@app.route('/reports/adv/never_participated_students')
@require_login('teacher')
def reports_adv_never_participated_students():
    sql = """
        SELECT 
            s.student_id,
            u.user_name || ' ' || u.user_surname AS full_name
        FROM student s
        JOIN "User" u ON s.student_id = u.user_id
        LEFT JOIN userparticipatesinexperiment up ON s.student_id = up.user_id
        WHERE s.teacher_id = %s
          AND up.user_id IS NULL
        ORDER BY full_name
    """
    rows = DatabaseManager.execute_query(sql, (session['user_id'],)) or []
    return _render_generic("Студенти кои никогаш не учествувале во експерименти", rows)


@app.route('/reports/adv/students_below_threshold')
@require_login('teacher')
def reports_adv_students_below_threshold():
    max_exp = request.args.get('max', default=3, type=int)
    sql = """
        SELECT 
            s.student_id,
            u.user_name || ' ' || u.user_surname AS full_name,
            COUNT(up.experiment_id) AS total_experiments
        FROM student s
        JOIN "User" u ON s.student_id = u.user_id
        LEFT JOIN userparticipatesinexperiment up ON s.student_id = up.user_id
        WHERE s.teacher_id = %s
        GROUP BY s.student_id, full_name
        HAVING COUNT(up.experiment_id) < %s
        ORDER BY total_experiments ASC, full_name
    """
    rows = DatabaseManager.execute_query(sql, (session['user_id'], max_exp)) or []
    return _render_generic(f"Студенти со помалку од {max_exp} експерименти", rows)


@app.route('/reports/adv/student_views')
@require_login('teacher')
def reports_adv_student_views():
    sql = """
        SELECT 
            s.student_id,
            u.user_name || ' ' || u.user_surname AS full_name,
            COUNT(DISTINCT ue.element_id)  AS total_elements_viewed,
            COUNT(DISTINCT ul.equipment_id) AS total_lab_equipment_viewed
        FROM student s
        JOIN "User" u ON s.student_id = u.user_id
        LEFT JOIN userviewselement     ue ON s.student_id = ue.user_id
        LEFT JOIN userviewslabequipment ul ON s.student_id = ul.user_id
        WHERE s.teacher_id = %s
        GROUP BY s.student_id, full_name
        ORDER BY total_elements_viewed DESC, total_lab_equipment_viewed DESC
    """
    rows = DatabaseManager.execute_query(sql, (session['user_id'],)) or []
    return _render_generic("Прегледи на елементи и опрема по студент", rows)


# ------------------------------
# Run
# ------------------------------
if __name__ == '__main__':
    app.run(debug=True)
