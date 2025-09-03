from flask import Flask, render_template, jsonify, request, session, redirect
from utils.database_manager import DatabaseManager
from utils.auth_manager import AuthManager
import hashlib

app = Flask(__name__)
app.secret_key = 'simlab-secret-key-2024'
app.config['JSON_AS_ASCII'] = False

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
        return jsonify({
            'status': 'success',
            'message': 'Успешно поврзување со факултетската база!'
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Грешка при поврзување'
        })

@app.route('/users')
def users():
    """Прикажи сите корисници"""
    users = DatabaseManager.get_all_users()
    if users:
        return jsonify({
            'status': 'success',
            'sql_query': 'SELECT user_id, user_name, user_surname, email, role FROM "User" ORDER BY user_name',
            'count': len(users),
            'data': users
        })
    return jsonify({'status': 'error', 'message': 'Нема корисници'})

@app.route('/elements')
def elements():
    if 'user_id' not in session:
        return redirect('/login')
    
    elements_data = DatabaseManager.get_all_elements()
    
    if elements_data:
        return render_template('elements_list.html', elements=elements_data, user_role=session['role'])
    else:
        return render_template('elements_list.html', elements=[], error='Нема елементи во базата')

@app.route('/equipment')
def equipment():
    """Прикажи лабораториска опрема"""
    if 'user_id' not in session:
        return redirect('/login')
    
    equipment_data = DatabaseManager.get_all_equipment()
    if equipment_data:
        return render_template('equipment_list.html', equipment=equipment_data, user_role=session['role'])
    else:
        return render_template('equipment_list.html', equipment=[], error='Нема опрема во базата')

@app.route('/reports/equipment-usage')
def equipment_usage_report():
    """SQL Извештаи за опрема"""
    usage_report = DatabaseManager.get_equipment_usage_report()
    if usage_report:
        return jsonify({
            'status': 'success',
            'report_name': 'Извештај за користење на лабораториска опрема',
            'sql_query': '''
                SELECT le.equipment_name, COUNT(ele.experiment_id) AS usage_count
                FROM ExperimentLabEquipment ele
                RIGHT JOIN LabEquipment le ON ele.equipment_id = le.equipment_id
                GROUP BY le.equipment_name
                ORDER BY usage_count DESC
            ''',
            'count': len(usage_report),
            'data': usage_report
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Грешка при генерирање на извештај'
        })

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = DatabaseManager.authenticate_user(email, password)
        if user and AuthManager.verify_password(password, user['password']):
            session['user_id'] = user['user_id']
            session['user_name'] = user['user_name']
            session['role'] = user['role']
            return redirect('/dashboard')
        else:
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
            return redirect('/login')
        else:
            return render_template('register.html', error='Грешка при регистрација', teachers=teachers)
    
    return render_template('register.html', teachers=teachers)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/dashboard')
def dashboard():
    """Dashboard со статистики според улога"""
    if 'user_id' not in session:
        return redirect('/login')
    
    if session['role'] == 'teacher':
        stats = None
        try:
            stats = DatabaseManager.get_teacher_dashboard_statistics(session['user_id'])
        except:
            stats = {'student_count': 0, 'reaction_count': 0, 'experiment_count': 0, 'activity_count': 0}
        
        return render_template('dashboard_teacher.html', 
                             user_name=session['user_name'],
                             stats=stats)
    else:
        stats = None
        try:
            stats = DatabaseManager.get_student_statistics(session['user_id'])
        except:
            stats = {'experiment_count': 0, 'element_count': 0, 'equipment_count': 0, 'reaction_count': 0}
        
        return render_template('dashboard_student.html', 
                             user_name=session['user_name'],
                             stats=stats)

@app.route('/elements/add', methods=['GET', 'POST'])
def add_element():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect('/login')
    
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
        
        element_id = DatabaseManager.add_element(symbol, name, atomic_number, atomic_weight,
                                                melting_point, boiling_point, hazard_type, 
                                                description, teacher_id)
        
        if element_id:
            return redirect('/dashboard')
        else:
            return render_template('add_element.html', error='Грешка при додавање на елементот')
    
    return render_template('add_element.html')

@app.route('/reports')
def reports_menu():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect('/login')
    
    return render_template('reports/menu.html')

@app.route('/reports/low_activity_students')
def low_activity_students():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect('/login')
    
    teacher_id = session['user_id']
    students = DatabaseManager.get_students_with_few_experiments(teacher_id, 3)
    return render_template('reports/low_activity_students.html', students=students)

@app.route('/reports/teacher_statistics')
def teacher_statistics():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect('/login')
    
    stats = DatabaseManager.get_teacher_statistics()
    return render_template('reports/teacher_statistics.html', statistics=stats)

@app.route('/reports/inactive_students')
def inactive_students():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect('/login')
    
    teacher_id = session['user_id']
    students = DatabaseManager.get_students_without_experiments(teacher_id)
    return render_template('reports/inactive_students.html', students=students)

@app.route('/reports/detailed_experiments')
def detailed_experiments():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect('/login')
    
    teacher_id = session['user_id']
    experiments = DatabaseManager.get_students_experiments_detailed(teacher_id)
    return render_template('reports/detailed_experiments.html', experiments=experiments)

@app.route('/elements/<int:element_id>')
def element_detail(element_id):
    if 'user_id' not in session:
        return redirect('/login')
    
    DatabaseManager.track_element_view(session['user_id'], element_id)
    
    element = DatabaseManager.get_element_by_id(element_id)
    if element:
        return render_template('element_detail.html', element=element, user_role=session['role'])
    else:
        return redirect('/elements')

@app.route('/my_students')
def my_students():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect('/login')
    
    teacher_id = session['user_id']
    students_activity = DatabaseManager.get_my_students_activity(teacher_id)
    
    return render_template('my_students.html', 
                         students=students_activity, 
                         teacher_name=session['user_name'])

@app.route('/experiments')
def experiments():
    if 'user_id' not in session:
        return redirect('/login')
    
    experiments_data = DatabaseManager.get_all_experiments()
    return render_template('experiments_list.html', experiments=experiments_data, user_role=session['role'])

@app.route('/experiments/<int:experiment_id>')
def experiment_detail(experiment_id):
    if 'user_id' not in session:
        return redirect('/login')
    
    experiments = DatabaseManager.get_all_experiments()
    experiment = None
    for exp in experiments:
        if exp['experiment_id'] == experiment_id:
            experiment = exp
            break
    
    if not experiment:
        return redirect('/experiments')
    
    equipment = DatabaseManager.get_experiment_equipment(experiment_id)
    
    return render_template('experiment_detail.html', 
                         experiment=experiment, 
                         equipment=equipment, 
                         user_role=session['role'])

@app.route('/reports/element_views')
def element_views_report():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect('/login')
    
    views_data = DatabaseManager.get_element_views_report()
    return render_template('reports/element_views.html', views=views_data)

@app.route('/equipment/add', methods=['GET', 'POST'])
def add_equipment():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect('/login')
    
    if request.method == 'POST':
        name = request.form['name']
        equipment_type = request.form['type']
        description = request.form['description']
        safety_info = request.form['safety_info']
        teacher_id = session['user_id']
        
        equipment_id = DatabaseManager.add_lab_equipment(name, equipment_type, description, 
                                                        safety_info, teacher_id)
        
        if equipment_id:
            return redirect('/dashboard')
        else:
            return render_template('add_equipment.html', error='Грешка при додавање на опремата')
    
    return render_template('add_equipment.html')

@app.route('/equipment/<int:equipment_id>')
def equipment_detail(equipment_id):
    if 'user_id' not in session:
        return redirect('/login')
    
    DatabaseManager.track_equipment_view(session['user_id'], equipment_id)
    
    equipment_data = DatabaseManager.get_all_equipment()
    equipment = None
    for item in equipment_data:
        if item['equipment_id'] == equipment_id:
            equipment = item
            break
    
    if equipment:
        return render_template('equipment_detail.html', equipment=equipment, user_role=session['role'])
    else:
        return redirect('/equipment')

@app.route('/elements/<int:element_id>/edit', methods=['GET', 'POST'])
def edit_element(element_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect('/login')
    
    element = DatabaseManager.get_element_by_id(element_id)
    if not element:
        return redirect('/elements')
    
    if request.method == 'POST':
        symbol = request.form['symbol']
        name = request.form['name']
        atomic_number = int(request.form['atomic_number'])
        atomic_weight = float(request.form['atomic_weight'])
        melting_point = float(request.form['melting_point']) if request.form['melting_point'] else None
        boiling_point = float(request.form['boiling_point']) if request.form['boiling_point'] else None
        hazard_type = request.form['hazard_type']
        description = request.form['description']
        
        if DatabaseManager.update_element(element_id, symbol, name, atomic_number, atomic_weight, 
                                         melting_point, boiling_point, hazard_type, description):
            return redirect('/elements')
        else:
            return render_template('edit_element.html', element=element, error='Грешка при ажурирање')
    
    return render_template('edit_element.html', element=element)

@app.route('/equipment/<int:equipment_id>/edit', methods=['GET', 'POST'])
def edit_equipment(equipment_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect('/login')
    
    equipment = DatabaseManager.get_equipment_by_id(equipment_id)
    if not equipment:
        return redirect('/equipment')
    
    if request.method == 'POST':
        name = request.form['name']
        equipment_type = request.form['type']
        description = request.form['description']
        safety_info = request.form['safety_info']
        
        if DatabaseManager.update_equipment(equipment_id, name, equipment_type, description, safety_info):
            return redirect('/equipment')
        else:
            return render_template('edit_equipment.html', equipment=equipment, error='Грешка при ажурирање')
    
    return render_template('edit_equipment.html', equipment=equipment)

@app.route('/reactions')
def reactions():
    """Прикажи сите реакции"""
    if 'user_id' not in session:
        return redirect('/login')
    
    reactions_data = DatabaseManager.get_all_reactions()
    return render_template('reactions_list.html', reactions=reactions_data, user_role=session['role'])

@app.route('/reactions/add', methods=['GET', 'POST'])
def add_reaction():
    """Додавање реакција со автоматско креирање експеримент"""
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect('/login')
    
    elements = DatabaseManager.get_all_elements()
    
    if request.method == 'POST':
        element1_id = int(request.form['element1_id'])
        element2_id = int(request.form['element2_id'])
        product = request.form['product']
        conditions = request.form['conditions']
        safety_warning = request.form.get('safety_warning', 'Стандардни безбедносни мерки')
        teacher_id = session['user_id']
        
        result = DatabaseManager.create_reaction_and_experiment(
            teacher_id, element1_id, element2_id, product, conditions, safety_warning
        )
        
        if result:
            return redirect('/reactions')
        else:
            return render_template('add_reaction.html', 
                                 elements=elements, 
                                 error='Грешка при додавање реакција и експеримент')
    
    return render_template('add_reaction.html', elements=elements)

@app.route('/laboratory')
def laboratory():
    """Виртуелна лабораторија - различни темплејти според улога"""
    if 'user_id' not in session:
        return redirect('/login')
    
    elements = DatabaseManager.get_all_elements()
    
    if session['role'] == 'teacher':
        return render_template('laboratory.html', 
                             elements=elements, 
                             user_role=session['role'])
    else:
        return render_template('virtual_laboratory.html', 
                             elements=elements, 
                             user_role=session['role'])

@app.route('/api/simulate-reaction', methods=['POST'])
def simulate_reaction():
    """API за симулација на реакција"""
    if 'user_id' not in session:
        return jsonify({'error': 'Неавторизиран пристап'})
    
    data = request.get_json()
    element1_symbol = data.get('element1')
    element2_symbol = data.get('element2')
    
    reactions = DatabaseManager.get_all_reactions()
    for reaction in reactions:
        if ((reaction['element1_symbol'] == element1_symbol and reaction['element2_symbol'] == element2_symbol) or
            (reaction['element1_symbol'] == element2_symbol and reaction['element2_symbol'] == element1_symbol)):
            
            experiment = DatabaseManager.get_experiment_by_reaction(reaction['reaction_id'])
            
            return jsonify({
                'success': True,
                'product': reaction['product'],
                'conditions': reaction['conditions'],
                'reaction_id': reaction['reaction_id'],
                'experiment_id': experiment['experiment_id'] if experiment else None,
                'elements': f"{reaction['element1_name']} + {reaction['element2_name']}"
            })
    
    return jsonify({
        'success': False,
        'message': f'Реакцијата меѓу {element1_symbol} и {element2_symbol} не е дефинирана во системот.'
    })

@app.route('/api/check-reaction', methods=['POST'])
def check_reaction():
    """API за проверка на реакција"""
    if 'user_id' not in session:
        return jsonify({'error': 'Неавторизиран пристап'})
    
    data = request.get_json()
    element1_symbol = data.get('element1')
    element2_symbol = data.get('element2')
    
    reactions = DatabaseManager.get_all_reactions()
    for reaction in reactions:
        if ((reaction['element1_symbol'] == element1_symbol and reaction['element2_symbol'] == element2_symbol) or
            (reaction['element1_symbol'] == element2_symbol and reaction['element2_symbol'] == element1_symbol)):
            return jsonify({
                'success': True,
                'product': reaction['product'],
                'conditions': reaction['conditions'],
                'reaction_id': reaction['reaction_id']
            })
    
    return jsonify({
        'success': False,
        'message': 'Реакцијата не е дефинирана во системот'
    })

@app.route('/reactions/<int:reaction_id>/edit', methods=['GET', 'POST'])
def edit_reaction(reaction_id):
    """Едитирај реакција - само за професори"""
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect('/login')
    
    reaction = DatabaseManager.get_reaction_by_id(reaction_id)
    if not reaction:
        return redirect('/reactions')
    
    elements = DatabaseManager.get_all_elements()
    
    if request.method == 'POST':
        element1_id = int(request.form['element1_id'])
        element2_id = int(request.form['element2_id'])
        product = request.form['product']
        conditions = request.form['conditions']
        
        if DatabaseManager.update_reaction(reaction_id, element1_id, element2_id, product, conditions):
            return redirect('/reactions')
        else:
            return render_template('edit_reaction.html', reaction=reaction, elements=elements, 
                                  error='Грешка при ажурирање')
    
    return render_template('edit_reaction.html', reaction=reaction, elements=elements)

@app.route('/reactions/<int:reaction_id>/delete', methods=['POST'])
def delete_reaction(reaction_id):
    """Избриши реакција - само за професори"""
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect('/login')
    
    if DatabaseManager.delete_reaction(reaction_id):
        return redirect('/reactions')
    else:
        return redirect('/reactions')

@app.route('/save-experiment', methods=['POST'])
def save_experiment():
    """Зачувување на учество во експеримент"""
    if 'user_id' not in session:
        return jsonify({'error': 'Неавторизиран пристап'})
    
    data = request.get_json()
    reaction_id = data.get('reaction_id')
    
    experiment = DatabaseManager.get_experiment_by_reaction(reaction_id)
    
    if not experiment:
        if session['role'] != 'teacher':
            return jsonify({
                'success': False, 
                'message': 'Не постои експеримент за оваа реакција. Контактирајте го вашиот професор.'
            })
        
        result_description = data.get('result', 'Експериментална симулација')
        safety_warning = data.get('safety_warning', 'Стандардни безбедносни мерки')
        
        experiment_id = DatabaseManager.insert_experiment(
            session['user_id'], 
            reaction_id, 
            result_description, 
            safety_warning
        )
    else:
        experiment_id = experiment['experiment_id']
    
    if experiment_id:
        DatabaseManager.track_experiment_participation(session['user_id'], experiment_id)
        return jsonify({'success': True, 'experiment_id': experiment_id})
    else:
        return jsonify({'success': False, 'message': 'Грешка при зачувување'})

@app.route('/reports/student_experiments')
def student_experiments_report():
    """Извештај за експерименти на студенти"""
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect('/login')
    
    teacher_id = session['user_id']
    experiments = DatabaseManager.get_students_experiments_for_teacher(teacher_id)
    
    return render_template('reports/student_experiments.html', 
                         student_experiments=experiments)

@app.route('/my-experiments')
def my_experiments():
    """Приказ на експерименти според улога"""
    if 'user_id' not in session:
        return redirect('/login')
    
    if session['role'] == 'student':
        # 🔑 земи експерименти каде студентот учествувал
        experiments = DatabaseManager.get_student_participation_experiments(session['user_id'])
    else:
        # 🔑 земи експерименти креирани од професорот
        experiments = DatabaseManager.get_user_experiments(session['user_id'])
    
    return render_template('my_experiments.html', 
                         experiments=experiments, 
                         user_name=session['user_name'],
                         user_role=session['role'])


@app.route('/api/dashboard-stats')
def dashboard_stats():
    """API endpoint за статистики на dashboard"""
    if 'user_id' not in session:
        return jsonify({'error': 'Неавторизиран пристап'})
    
    if session['role'] == 'student':
        stats = DatabaseManager.get_student_statistics(session['user_id'])
    else:
        stats = DatabaseManager.get_teacher_dashboard_statistics(session['user_id'])
    
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=True)