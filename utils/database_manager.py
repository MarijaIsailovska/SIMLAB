import psycopg2
from psycopg2.extras import RealDictCursor

class DatabaseManager:
    @staticmethod
    def get_connection():
        # Ова е новиот метод што ќе реши грешката
        return psycopg2.connect(
            host='localhost',
            port=9999,
            database='db_202425z_va_prj_simlab25',
            user='db_202425z_va_prj_simlab25_owner',
            password='c9e5ebb7d332',
            cursor_factory=RealDictCursor
        )

    @staticmethod
    def execute_query(query, params=None):
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print(f"Грешка во execute_query: {e}")
            return None
        
    @staticmethod
    def test_connection():
        try:
            conn = psycopg2.connect(
                host='localhost',
                port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332',
                cursor_factory=RealDictCursor
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            return True
        except:
            return False
    
    @staticmethod
    def get_all_users():
        try:
            conn = psycopg2.connect(
                host='localhost',
                port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332',
                cursor_factory=RealDictCursor
            )
            cursor = conn.cursor()
            cursor.execute('SELECT user_id, user_name, user_surname, email, role FROM "User" ORDER BY user_name')
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print(f"Грешка: {e}")
            return None
        
    @staticmethod
    def get_all_elements():
        try:
            conn = psycopg2.connect(
                host='localhost',
                port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332',
                cursor_factory=RealDictCursor
            )
            cursor = conn.cursor()
            cursor.execute('''
                SELECT element_id, symbol, element_name, atomic_number, 
                    atomic_weight, melting_point, boiling_point,  hazard_type, description_element
                FROM elements
                ORDER BY atomic_number
            ''')
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print(f"Грешка: {e}")
            return None

    @staticmethod
    def get_all_equipment():
        try:
            conn = psycopg2.connect(
                host='localhost',
                port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332',
                cursor_factory=RealDictCursor
            )
            cursor = conn.cursor()
            cursor.execute('''
                SELECT equipment_id, equipment_name, type, description, safety_info
                FROM labequipment
                ORDER BY equipment_name
            ''')
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print(f"Грешка: {e}")
            return None

    @staticmethod
    def get_equipment_usage_report():
        try:
            conn = psycopg2.connect(
                host='localhost',
                port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332',
                cursor_factory=RealDictCursor
            )
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    le.equipment_name,
                    COUNT(ele.experiment_id) AS usage_count
                FROM ExperimentLabEquipment ele
                RIGHT JOIN LabEquipment le ON ele.equipment_id = le.equipment_id
                GROUP BY le.equipment_name, le.equipment_id
                ORDER BY usage_count DESC, le.equipment_name
            ''')
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print(f"Грешка: {e}")
            return []
    @staticmethod
    def authenticate_user(email, password):
        """Автентикација на корисник"""
        try:
            conn = psycopg2.connect(
                host='localhost',
                port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332',
                cursor_factory=RealDictCursor
            )
            cursor = conn.cursor()
            cursor.execute('SELECT user_id, user_name, user_surname, email, role, password FROM "User" WHERE email = %s', (email,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            return dict(user) if user else None
        except Exception as e:
            print(f"Грешка при автентикација: {e}")
            return None

    @staticmethod
    def register_user(name, surname, email, password_hash, role, teacher_id=None):
        """Регистрирај нов корисник"""
        try:
            conn = psycopg2.connect(
                host='localhost',
                port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332'
            )
            cursor = conn.cursor()
            
            # Вметни во User табела
            cursor.execute(
                'INSERT INTO "User" (user_name, user_surname, email, password, role) VALUES (%s, %s, %s, %s, %s) RETURNING user_id',
                (name, surname, email, password_hash, role)
            )
            user_id = cursor.fetchone()[0]
            
            # Ако е студент, вметни во Student табела
            if role == 'student' and teacher_id:
                cursor.execute('INSERT INTO Student (student_id, teacher_id) VALUES (%s, %s)', (user_id, teacher_id))
            # Ако е наставник, вметни во Teacher табела
            elif role == 'teacher':
                cursor.execute('INSERT INTO Teacher (teacher_id) VALUES (%s)', (user_id,))
            
            conn.commit()
            cursor.close()
            conn.close()
            return user_id
        except Exception as e:
            print(f"Грешка при регистрација: {e}")
            return None
    @staticmethod
    def get_all_teachers():
        """Земи ги сите наставници"""
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332',
                cursor_factory=RealDictCursor
            )
            cursor = conn.cursor()
            cursor.execute('''
                SELECT t.teacher_id, u.user_name, u.user_surname 
                FROM Teacher t
                JOIN "User" u ON t.teacher_id = u.user_id
                ORDER BY u.user_name
            ''')
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print(f"Грешка: {e}")
            return []
    @staticmethod
    def add_element(symbol, name, atomic_number, atomic_weight, melting_point, boiling_point, hazard_type, description, teacher_id):
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332'
            )
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO elements (symbol, element_name, atomic_number, atomic_weight, melting_point, boiling_point, hazard_type, description_element, teacher_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING element_id
            ''', (symbol, name, atomic_number, atomic_weight, melting_point, boiling_point, hazard_type, description, teacher_id))
            
            element_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            return element_id
        except Exception as e:
            print(f"Грешка при додавање елемент: {e}")
            return None
        
    @staticmethod
    def track_element_view(user_id, element_id):
        """Track дека корисникот го погледнал елементот"""
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332'
            )
            cursor = conn.cursor()
            # Провери дали веќе постои запис
            cursor.execute('SELECT 1 FROM userviewselement WHERE user_id = %s AND element_id = %s', (user_id, element_id))
            if not cursor.fetchone():
                cursor.execute('INSERT INTO userviewselement (user_id, element_id) VALUES (%s, %s)', (user_id, element_id))
                conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Грешка при tracking: {e}")

    @staticmethod
    def get_element_views_report():
        """Извештај за кој корисник кои елементи ги прегледал"""
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332',
                cursor_factory=RealDictCursor
            )
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    u.user_name || ' ' || u.user_surname AS full_name,
                    u.role,
                    e.symbol,
                    e.element_name,
                    COUNT(*) as view_count
                FROM userviewselement uve
                JOIN "User" u ON uve.user_id = u.user_id
                JOIN elements e ON uve.element_id = e.element_id
                GROUP BY u.user_id, u.user_name, u.user_surname, u.role, e.element_id, e.symbol, e.element_name
                ORDER BY u.user_name, e.symbol
            ''')
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print(f"Грешка: {e}")
            return []

    @staticmethod
    def get_user_activity_summary():
        """Сумарен извештај за активности по корисник"""
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332',
                cursor_factory=RealDictCursor
            )
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    u.user_id,
                    u.user_name || ' ' || u.user_surname AS full_name,
                    u.role,
                    COUNT(DISTINCT uve.element_id) AS elements_viewed,
                    COUNT(DISTINCT uvl.equipment_id) AS equipment_viewed,
                    COUNT(DISTINCT upe.experiment_id) AS experiments_participated
                FROM "User" u
                LEFT JOIN userviewselement uve ON u.user_id = uve.user_id
                LEFT JOIN userviewslabequipment uvl ON u.user_id = uvl.user_id
                LEFT JOIN userparticipatesinexperiment upe ON u.user_id = upe.user_id
                GROUP BY u.user_id, u.user_name, u.user_surname, u.role
                ORDER BY u.user_name
            ''')
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print(f"Грешка: {e}")
            return []
        
    @staticmethod
    def get_element_by_id(element_id):
        """Земи конкретен елемент по ID"""
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332',
                cursor_factory=RealDictCursor
            )
            cursor = conn.cursor()
            cursor.execute('''
                SELECT e.*, u.user_name || ' ' || u.user_surname AS created_by
                FROM elements e
                JOIN "User" u ON e.teacher_id = u.user_id
                WHERE e.element_id = %s
            ''', (element_id,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return dict(result) if result else None
        except Exception as e:
            print(f"Грешка: {e}")
            return None
    @staticmethod
    def get_my_students_activity(teacher_id):
        """Извештај за активности на студентите на конкретен професор"""
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332',
                cursor_factory=RealDictCursor
            )
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    s.student_id,
                    u.user_name || ' ' || u.user_surname AS full_name,
                    COUNT(DISTINCT ue.element_id) AS total_elements_viewed,
                    COUNT(DISTINCT ul.equipment_id) AS total_lab_equipment_viewed
                FROM Student s
                JOIN "User" u ON s.student_id = u.user_id
                LEFT JOIN UserViewsElement ue ON s.student_id = ue.user_id
                LEFT JOIN UserViewsLabEquipment ul ON s.student_id = ul.user_id
                WHERE s.teacher_id = %s
                GROUP BY s.student_id, full_name
                ORDER BY total_elements_viewed DESC, total_lab_equipment_viewed DESC
            ''', (teacher_id,))
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print(f"Грешка: {e}")
            return []
    @staticmethod
    def get_students_with_few_experiments(teacher_id, max_experiments=3):
        """Студенти со помалку од одреден број експерименти"""
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332',
                cursor_factory=RealDictCursor
            )
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    s.student_id,
                    u.user_name || ' ' || u.user_surname AS full_name,
                    COUNT(up.experiment_id) AS total_experiments
                FROM Student s
                JOIN "User" u ON s.student_id = u.user_id
                LEFT JOIN UserParticipatesInExperiment up ON s.student_id = up.user_id
                WHERE s.teacher_id = %s
                GROUP BY s.student_id, full_name
                HAVING COUNT(up.experiment_id) < %s 
                ORDER BY total_experiments ASC
            ''', (teacher_id, max_experiments))
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print(f"Грешка: {e}")
            return []

    @staticmethod
    def get_teacher_statistics():
        """Статистики по професор"""
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332',
                cursor_factory=RealDictCursor
            )
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    t.teacher_id,
                    u.user_name || ' ' || u.user_surname AS full_name,
                    COUNT(DISTINCT s.student_id) AS total_students,
                    COUNT(up.experiment_id) AS total_experiments,
                    ROUND(
                        COUNT(up.experiment_id) * 1.0 / NULLIF(COUNT(DISTINCT s.student_id), 0), 2
                    ) AS avg_experiments_per_student
                FROM Teacher t
                JOIN "User" u ON t.teacher_id = u.user_id
                LEFT JOIN Student s ON t.teacher_id = s.teacher_id
                LEFT JOIN UserParticipatesInExperiment up ON s.student_id = up.user_id
                GROUP BY t.teacher_id, full_name
                ORDER BY avg_experiments_per_student DESC
            ''')
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print(f"Грешка: {e}")
            return []

    @staticmethod
    def get_students_without_experiments(teacher_id):
        """Студенти без експерименти"""
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332',
                cursor_factory=RealDictCursor
            )
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    s.student_id,
                    u.user_name || ' ' || u.user_surname AS full_name
                FROM Student s
                JOIN "User" u ON s.student_id = u.user_id
                LEFT JOIN UserParticipatesInExperiment up ON s.student_id = up.user_id
                WHERE s.teacher_id = %s
                AND up.user_id IS NULL
            ''', (teacher_id,))
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print(f"Грешка: {e}")
            return []

    @staticmethod
    def get_students_experiments_detailed(teacher_id):
        """Детален извештај за студенти и експерименти"""
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332',
                cursor_factory=RealDictCursor
            )
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    s.student_id,
                    u.user_name || ' ' || u.user_surname AS full_name,
                    e.experiment_id,
                    e.result,
                    e.time_stamp AS participation_time
                FROM Student s
                JOIN "User" u ON s.student_id = u.user_id
                JOIN UserParticipatesInExperiment up ON s.student_id = up.user_id
                JOIN Experiment e ON up.experiment_id = e.experiment_id
                WHERE s.teacher_id = %s
                ORDER BY u.user_name, e.time_stamp DESC
            ''', (teacher_id,))
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print(f"Грешка: {e}")
            return []
            
    @staticmethod
    def get_all_experiments():
        """Земи сите експерименти"""
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332',
                cursor_factory=RealDictCursor
            )
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    e.experiment_id,
                    e.result,
                    e.time_stamp,
                    e.safety_warning,
                    r.product,
                    r.conditions,
                    el1.symbol AS element1_symbol,
                    el1.element_name AS element1_name,
                    el2.symbol AS element2_symbol,
                    el2.element_name AS element2_name,
                    u.user_name || ' ' || u.user_surname AS created_by
                FROM experiment e
                JOIN reaction r ON e.reaction_id = r.reaction_id
                JOIN elements el1 ON r.element1_id = el1.element_id
                JOIN elements el2 ON r.element2_id = el2.element_id
                JOIN "User" u ON e.teacher_id = u.user_id
                ORDER BY e.time_stamp DESC
            ''')
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print(f"Грешка: {e}")
            return []

    @staticmethod
    def get_experiment_equipment(experiment_id):
        """Земи ја опремата за конкретен експеримент"""
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332',
                cursor_factory=RealDictCursor
            )
            cursor = conn.cursor()
            cursor.execute('''
                SELECT le.equipment_name, le.type, le.safety_info
                FROM experimentlabequipment ele
                JOIN labequipment le ON ele.equipment_id = le.equipment_id
                WHERE ele.experiment_id = %s
            ''', (experiment_id,))
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print(f"Грешка: {e}")
            return []
    @staticmethod
    def get_element_views_report():
        """Извештај за кој корисник кои елементи ги прегледал"""
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332',
                cursor_factory=RealDictCursor
            )
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    u.user_name || ' ' || u.user_surname AS full_name,
                    u.role,
                    e.symbol,
                    e.element_name,
                    COUNT(*) as view_count
                FROM userviewselement uve
                JOIN "User" u ON uve.user_id = u.user_id
                JOIN elements e ON uve.element_id = e.element_id
                GROUP BY u.user_id, u.user_name, u.user_surname, u.role, e.element_id, e.symbol, e.element_name
                ORDER BY u.user_name, e.symbol
            ''')
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print(f"Грешка: {e}")
            return []
    
    @staticmethod
    def add_lab_equipment(name, equipment_type, description, safety_info, teacher_id):
        """Додај нова лабораториска опрема"""
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332'
            )
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO labequipment (equipment_name, type, description, safety_info, teacher_id)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING equipment_id
            ''', (name, equipment_type, description, safety_info, teacher_id))
            
            equipment_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            return equipment_id
        except Exception as e:
            print(f"Грешка при додавање опрема: {e}")
            return None

    @staticmethod
    def track_equipment_view(user_id, equipment_id):
        """Track дека корисникот ја погледнал опремата"""
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332'
            )
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM userviewslabequipment WHERE user_id = %s AND equipment_id = %s', (user_id, equipment_id))
            if not cursor.fetchone():
                cursor.execute('INSERT INTO userviewslabequipment (user_id, equipment_id) VALUES (%s, %s)', (user_id, equipment_id))
                conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Грешка при tracking: {e}")
    
    @staticmethod
    def update_element(element_id, symbol, name, atomic_number, atomic_weight, melting_point, boiling_point, hazard_type, description):
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332'
            )
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE elements 
                SET symbol = %s, element_name = %s, atomic_number = %s, atomic_weight = %s, 
                    melting_point = %s, boiling_point = %s, hazard_type = %s, description_element = %s
                WHERE element_id = %s
            ''', (symbol, name, atomic_number, atomic_weight, melting_point, boiling_point, hazard_type, description, element_id))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Грешка: {e}")
            return False

    @staticmethod
    def get_equipment_by_id(equipment_id):
        equipment_data = DatabaseManager.get_all_equipment()
        for item in equipment_data:
            if item['equipment_id'] == equipment_id:
                return item
        return None

    @staticmethod
    def update_equipment(equipment_id, name, equipment_type, description, safety_info):
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332'
            )
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE labequipment 
                SET equipment_name = %s, type = %s, description = %s, safety_info = %s
                WHERE equipment_id = %s
            ''', (name, equipment_type, description, safety_info, equipment_id))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Грешка: {e}")
            return False
    
    @staticmethod
    def add_reaction(teacher_id, element1_id, element2_id, product, conditions):
        """Додај нова реакција"""
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332'
            )
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO reaction (teacher_id, element1_id, element2_id, product, conditions)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING reaction_id
            ''', (teacher_id, element1_id, element2_id, product, conditions))
            
            reaction_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            return reaction_id
        except Exception as e:
            print(f"Грешка: {e}")
            return None

    @staticmethod
    def get_all_reactions():
        """Земи ги сите реакции"""
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332',
                cursor_factory=RealDictCursor
            )
            cursor = conn.cursor()
            cursor.execute('''
                SELECT r.*, 
                    e1.symbol as element1_symbol, e1.element_name as element1_name,
                    e2.symbol as element2_symbol, e2.element_name as element2_name,
                    u.user_name || ' ' || u.user_surname as created_by
                FROM reaction r
                JOIN elements e1 ON r.element1_id = e1.element_id
                JOIN elements e2 ON r.element2_id = e2.element_id
                JOIN "User" u ON r.teacher_id = u.user_id
                ORDER BY r.reaction_id DESC
            ''')
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print(f"Грешка: {e}")
            return []

    @staticmethod
    def get_reaction_by_id(reaction_id):
        """Земи реакција по ID"""
        reactions = DatabaseManager.get_all_reactions()
        for reaction in reactions:
            if reaction['reaction_id'] == reaction_id:
                return reaction
        return None

    @staticmethod
    def update_reaction(reaction_id, element1_id, element2_id, product, conditions):
        """Ажурирај реакција"""
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332'
            )
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE reaction 
                SET element1_id = %s, element2_id = %s, product = %s, conditions = %s
                WHERE reaction_id = %s
            ''', (element1_id, element2_id, product, conditions, reaction_id))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Грешка: {e}")
            return False

    @staticmethod
    def delete_reaction(reaction_id):
        """Избриши реакција"""
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332'
            )
            cursor = conn.cursor()
            cursor.execute('DELETE FROM reaction WHERE reaction_id = %s', (reaction_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Грешка: {e}")
            return False

    @staticmethod
    def insert_experiment(teacher_id, reaction_id, result, safety_warning):
        """Додај нов експеримент"""
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332'
            )
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO experiment (teacher_id, reaction_id, result, safety_warning, time_stamp)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                RETURNING experiment_id
            ''', (teacher_id, reaction_id, result, safety_warning))
            
            experiment_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            return experiment_id
        except Exception as e:
            print(f"Грешка: {e}")
            return None

    @staticmethod
    def track_experiment_participation(user_id, experiment_id):
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332'
            )
            cursor = conn.cursor()
            print(f"DEBUG: Додавам user_id={user_id}, experiment_id={experiment_id}")
            cursor.execute('''
                INSERT INTO userparticipatesinexperiment (user_id, experiment_id)
                VALUES (%s, %s)
            ''', (user_id, experiment_id))
            conn.commit()
            cursor.close()
            conn.close()
            print("DEBUG: Успешно додадено учество")
        except Exception as e:
            print(f"DEBUG Грешка при додавање учество: {e}")

    @staticmethod
    def get_user_experiments(user_id):
        """Земи експерименти на корисник"""
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332',
                cursor_factory=RealDictCursor
            )
            cursor = conn.cursor()
            cursor.execute('''
                SELECT e.*, 
                    r.product,
                    r.conditions,
                    el1.symbol as element1_symbol, el1.element_name as element1_name,
                    el2.symbol as element2_symbol, el2.element_name as element2_name,
                    up.participation_timestamp
                FROM experiment e
                JOIN userparticipatesinexperiment up ON e.experiment_id = up.experiment_id
                JOIN reaction r ON e.reaction_id = r.reaction_id
                JOIN elements el1 ON r.element1_id = el1.element_id
                JOIN elements el2 ON r.element2_id = el2.element_id
                WHERE up.user_id = %s
                ORDER BY up.participation_timestamp DESC
            ''', (user_id,))
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print(f"Грешка: {e}")
            return []
    @staticmethod
    def get_user_by_id(user_id):
        """Земи корисник по ID"""
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332',
                cursor_factory=RealDictCursor
            )
            cursor = conn.cursor()
            cursor.execute('''
                SELECT u.*, s.teacher_id
                FROM "User" u
                LEFT JOIN Student s ON u.user_id = s.student_id
                WHERE u.user_id = %s
            ''', (user_id,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return dict(result) if result else None
        except Exception as e:
            print(f"Грешка: {e}")
            return None
    
    # Додајте овие нови методи во DatabaseManager класата (database_manager.py)

    @staticmethod
    def create_reaction_and_experiment(teacher_id, element1_id, element2_id, product, conditions, safety_warning=None):
        """Креирај реакција и автоматски креирај експеримент (за професори)"""
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332'
            )
            cursor = conn.cursor()
            
            # Прво креирај реакција
            cursor.execute('''
                INSERT INTO reaction (teacher_id, element1_id, element2_id, product, conditions)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING reaction_id
            ''', (teacher_id, element1_id, element2_id, product, conditions))
            
            reaction_id = cursor.fetchone()[0]
            
            # Автоматски креирај експеримент за оваа реакција
            cursor.execute('''
                INSERT INTO experiment (teacher_id, reaction_id, result, safety_warning, time_stamp)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                RETURNING experiment_id
            ''', (teacher_id, reaction_id, 
                f'Експеримент за реакција: {product}', 
                safety_warning or 'Стандардни безбедносни мерки'))
            
            experiment_id = cursor.fetchone()[0]
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return {'reaction_id': reaction_id, 'experiment_id': experiment_id}
        except Exception as e:
            print(f"Грешка при креирање реакција и експеримент: {e}")
            return None

    @staticmethod
    def get_experiment_by_reaction(reaction_id):
        """Најди експеримент за дадена реакција"""
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332',
                cursor_factory=RealDictCursor
            )
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM experiment 
                WHERE reaction_id = %s
                ORDER BY time_stamp DESC
                LIMIT 1
            ''', (reaction_id,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return dict(result) if result else None
        except Exception as e:
            print(f"Грешка: {e}")
            return None

    @staticmethod
    def get_students_experiments_for_teacher(teacher_id):
        """Земи експерименти на студенти за конкретен професор"""
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332',
                cursor_factory=RealDictCursor
            )
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    u.user_name || ' ' || u.user_surname AS student_name,
                    s.student_id,
                    e.experiment_id,
                    e.result,
                    e.time_stamp,
                    r.product,
                    el1.symbol as element1_symbol,
                    el2.symbol as element2_symbol,
                    up.participation_timestamp as participation_date
                FROM student s
                JOIN "User" u ON s.student_id = u.user_id
                JOIN userparticipatesinexperiment up ON s.student_id = up.user_id
                JOIN experiment e ON up.experiment_id = e.experiment_id
                JOIN reaction r ON e.reaction_id = r.reaction_id
                JOIN elements el1 ON r.element1_id = el1.element_id
                JOIN elements el2 ON r.element2_id = el2.element_id
                WHERE s.teacher_id = %s
                ORDER BY up.participation_timestamp DESC
            ''', (teacher_id,))
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print(f"Грешка: {e}")
            return []
    
    @staticmethod
    def get_student_statistics(student_id):
        """Земи статистики за студент"""
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332',
                cursor_factory=RealDictCursor
            )
            cursor = conn.cursor()
            
            # Статистики за студентот
            cursor.execute('''
                SELECT 
                    (SELECT COUNT(*) FROM userparticipatesinexperiment WHERE user_id = %s) as experiment_count,
                    (SELECT COUNT(*) FROM userviewselement WHERE user_id = %s) as element_count,
                    (SELECT COUNT(*) FROM userviewslabequipment WHERE user_id = %s) as equipment_count,
                    (SELECT COUNT(DISTINCT r.reaction_id) 
                    FROM userparticipatesinexperiment up
                    JOIN experiment e ON up.experiment_id = e.experiment_id
                    JOIN reaction r ON e.reaction_id = r.reaction_id
                    WHERE up.user_id = %s) as reaction_count
            ''', (student_id, student_id, student_id, student_id))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return dict(result) if result else {'experiment_count': 0, 'element_count': 0, 'equipment_count': 0, 'reaction_count': 0}
        except Exception as e:
            print(f"Грешка: {e}")
            return {'experiment_count': 0, 'element_count': 0, 'equipment_count': 0, 'reaction_count': 0}

    @staticmethod
    def get_teacher_dashboard_statistics(teacher_id):
        """Земи статистики за професорски dashboard"""
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332',
                cursor_factory=RealDictCursor
            )
            cursor = conn.cursor()
            
            # Број на студенти
            cursor.execute('SELECT COUNT(*) as count FROM student WHERE teacher_id = %s', (teacher_id,))
            student_count = cursor.fetchone()['count']
            
            # Број на креирани реакции
            cursor.execute('SELECT COUNT(*) as count FROM reaction WHERE teacher_id = %s', (teacher_id,))
            reaction_count = cursor.fetchone()['count']
            
            # Број на експерименти
            cursor.execute('SELECT COUNT(*) as count FROM experiment WHERE teacher_id = %s', (teacher_id,))
            experiment_count = cursor.fetchone()['count']
            
            # Активности денес (експерименти од студенти денес)
            cursor.execute('''
                SELECT COUNT(*) as count 
                FROM userparticipatesinexperiment up
                JOIN student s ON up.user_id = s.student_id
                WHERE s.teacher_id = %s 
                AND DATE(up.participation_timestamp) = CURRENT_DATE
            ''', (teacher_id,))
            activity_today = cursor.fetchone()['count']
            
            cursor.close()
            conn.close()
            
            return {
                'student_count': student_count,
                'reaction_count': reaction_count,
                'experiment_count': experiment_count,
                'activity_count': activity_today
            }
        except Exception as e:
            print(f"Грешка: {e}")
            return {
                'student_count': 0,
                'reaction_count': 0,
                'experiment_count': 0,
                'activity_count': 0
            }
        
    # Додајте ги овие методи во вашиот DatabaseManager класа (database_manager.py)

    @staticmethod
    def create_reaction_and_experiment(teacher_id, element1_id, element2_id, product, conditions, safety_warning=None):
        """Креирај реакција и автоматски креирај експеримент"""
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332'
            )
            cursor = conn.cursor()
            
            # Прво креирај реакција
            cursor.execute('''
                INSERT INTO reaction (teacher_id, element1_id, element2_id, product, conditions)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING reaction_id
            ''', (teacher_id, element1_id, element2_id, product, conditions))
            
            reaction_id = cursor.fetchone()[0]
            
            # Автоматски креирај експеримент за оваа реакција
            cursor.execute('''
                INSERT INTO experiment (teacher_id, reaction_id, result, safety_warning, time_stamp)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                RETURNING experiment_id
            ''', (teacher_id, reaction_id, 
                f'Експеримент за: {product}', 
                safety_warning or 'Стандардни безбедносни мерки'))
            
            experiment_id = cursor.fetchone()[0]
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"Успешно креирани: Реакција #{reaction_id} и Експеримент #{experiment_id}")
            return {'reaction_id': reaction_id, 'experiment_id': experiment_id}
        except Exception as e:
            print(f"Грешка при креирање реакција и експеримент: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return None

    @staticmethod
    def get_experiment_by_reaction(reaction_id):
        """Најди експеримент за дадена реакција"""
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332',
                cursor_factory=RealDictCursor
            )
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM experiment 
                WHERE reaction_id = %s
                ORDER BY time_stamp DESC
                LIMIT 1
            ''', (reaction_id,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return dict(result) if result else None
        except Exception as e:
            print(f"Грешка при барање експеримент: {e}")
            return None

    @staticmethod
    def get_student_statistics(student_id):
        """Земи статистики за студент"""
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332',
                cursor_factory=RealDictCursor
            )
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    (SELECT COUNT(*) FROM userparticipatesinexperiment WHERE user_id = %s) as experiment_count,
                    (SELECT COUNT(*) FROM userviewselement WHERE user_id = %s) as element_count,
                    (SELECT COUNT(*) FROM userviewslabequipment WHERE user_id = %s) as equipment_count,
                    (SELECT COUNT(DISTINCT r.reaction_id) 
                    FROM userparticipatesinexperiment up
                    JOIN experiment e ON up.experiment_id = e.experiment_id
                    JOIN reaction r ON e.reaction_id = r.reaction_id
                    WHERE up.user_id = %s) as reaction_count
            ''', (student_id, student_id, student_id, student_id))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return dict(result) if result else {'experiment_count': 0, 'element_count': 0, 'equipment_count': 0, 'reaction_count': 0}
        except Exception as e:
            print(f"Грешка при статистики за студент: {e}")
            return {'experiment_count': 0, 'element_count': 0, 'equipment_count': 0, 'reaction_count': 0}

    @staticmethod
    def get_teacher_dashboard_statistics(teacher_id):
        """Земи статистики за професорски dashboard"""
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332',
                cursor_factory=RealDictCursor
            )
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) as count FROM student WHERE teacher_id = %s', (teacher_id,))
            student_count = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM reaction WHERE teacher_id = %s', (teacher_id,))
            reaction_count = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM experiment WHERE teacher_id = %s', (teacher_id,))
            experiment_count = cursor.fetchone()['count']
            
            cursor.execute('''
                SELECT COUNT(*) as count 
                FROM userparticipatesinexperiment up
                JOIN student s ON up.user_id = s.student_id
                WHERE s.teacher_id = %s 
                AND DATE(up.participation_timestamp) = CURRENT_DATE
            ''', (teacher_id,))
            activity_today = cursor.fetchone()['count']
            
            cursor.close()
            conn.close()
            
            return {
                'student_count': student_count,
                'reaction_count': reaction_count,
                'experiment_count': experiment_count,
                'activity_count': activity_today
            }
        except Exception as e:
            print(f"Грешка при dashboard статистики: {e}")
            return {
                'student_count': 0,
                'reaction_count': 0,
                'experiment_count': 0,
                'activity_count': 0
            }

    @staticmethod
    def get_students_experiments_for_teacher(teacher_id):
        """Земи експерименти на студенти за конкретен професор"""
        try:
            conn = psycopg2.connect(
                host='localhost', port=9999,
                database='db_202425z_va_prj_simlab25',
                user='db_202425z_va_prj_simlab25_owner',
                password='c9e5ebb7d332',
                cursor_factory=RealDictCursor
            )
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    u.user_name || ' ' || u.user_surname AS student_name,
                    s.student_id,
                    e.experiment_id,
                    e.result,
                    e.time_stamp,
                    r.product,
                    el1.symbol as element1_symbol,
                    el2.symbol as element2_symbol,
                    up.participation_timestamp as participation_date
                FROM student s
                JOIN "User" u ON s.student_id = u.user_id
                JOIN userparticipatesinexperiment up ON s.student_id = up.user_id
                JOIN experiment e ON up.experiment_id = e.experiment_id
                JOIN reaction r ON e.reaction_id = r.reaction_id
                JOIN elements el1 ON r.element1_id = el1.element_id
                JOIN elements el2 ON r.element2_id = el2.element_id
                WHERE s.teacher_id = %s
                ORDER BY up.participation_timestamp DESC
            ''', (teacher_id,))
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print(f"Грешка: {e}")
            return []
    @staticmethod
    def get_student_participation_experiments(student_id):
        query = '''
            SELECT ep.user_id,
                r.product,
                r.conditions,
                el1.symbol AS element1_symbol,
                el2.symbol AS element2_symbol,
                el1.element_name AS element1_name,
                el2.element_name AS element2_name,
                e.result,
                e.safety_warning,
                e.time_stamp,
                e.experiment_id
            FROM userparticipatesinexperiment ep
            JOIN experiment e ON ep.experiment_id = e.experiment_id
            JOIN reaction r ON e.reaction_id = r.reaction_id
            JOIN elements el1 ON r.element1_id = el1.element_id
            JOIN elements el2 ON r.element2_id = el2.element_id
            WHERE ep.user_id = %s
            ORDER BY e.time_stamp DESC
        '''
        return DatabaseManager.execute_query(query, (student_id,))

    @staticmethod
    def execute_query(query, params=None):
        conn = DatabaseManager.get_connection()
        cur = conn.cursor()
        cur.execute(query, params or ())
        result = cur.fetchall()
        cur.close()
        conn.close()
        return result
