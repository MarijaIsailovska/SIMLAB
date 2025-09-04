# database_manager.py
import psycopg2
from psycopg2.extras import RealDictCursor

class DatabaseManager:
    # ---------- CONNECTION ----------
    @staticmethod
    def get_connection():
        return psycopg2.connect(
            host='localhost',
            port=9999,
            database='db_202425z_va_prj_simlab25',
            user='db_202425z_va_prj_simlab25_owner',
            password='c9e5ebb7d332',
            cursor_factory=RealDictCursor
        )

    # ЕДИНСТВЕНА execute_query (го избришавме дупликатот)
    @staticmethod
    def execute_query(query, params=None):
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute(query, params or ())
            result = cur.fetchall()
            cur.close()
            conn.close()
            return result
        except Exception as e:
            print(f"Грешка во execute_query: {e}")
            return None

    @staticmethod
    def test_connection():
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
            conn.close()
            return True
        except Exception:
            return False

    # ---------- USERS / AUTH ----------
    @staticmethod
    def authenticate_user(email, password):
        """Автентикација (враќа row од \"User\" или None). Password проверката прави ја во сервис/route (bcrypt)."""
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute(
                'SELECT user_id, user_name, user_surname, email, role, password FROM "User" WHERE email = %s',
                (email,)
            )
            user = cur.fetchone()
            cur.close()
            conn.close()
            return dict(user) if user else None
        except Exception as e:
            print(f"Грешка при автентикација: {e}")
            return None

    @staticmethod
    def register_user(name, surname, email, password_hash, role, teacher_id=None):
        """Регистрирај нов корисник. Ако role='student' → внес во student; ако role='teacher' → внес во teacher."""
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()

            # User
            cur.execute(
                'INSERT INTO "User" (user_name, user_surname, email, password, role) '
                'VALUES (%s, %s, %s, %s, %s) RETURNING user_id',
                (name, surname, email, password_hash, role)
            )
            user_id = cur.fetchone()['user_id']

            # Subtype
            if role == 'student' and teacher_id:
                cur.execute('INSERT INTO student (student_id, teacher_id) VALUES (%s, %s)',
                            (user_id, teacher_id))
            elif role == 'teacher':
                cur.execute('INSERT INTO teacher (teacher_id) VALUES (%s)', (user_id,))

            conn.commit()
            cur.close()
            conn.close()
            return user_id
        except Exception as e:
            print(f"Грешка при регистрација: {e}")
            return None

    @staticmethod
    def get_user_by_id(user_id):
        """Земи корисник + teacher_id ако е студент (LEFT JOIN со student во мали букви)."""
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute('''
                SELECT u.*, s.teacher_id
                FROM "User" u
                LEFT JOIN student s ON u.user_id = s.student_id
                WHERE u.user_id = %s
            ''', (user_id,))
            row = cur.fetchone()
            cur.close()
            conn.close()
            return dict(row) if row else None
        except Exception as e:
            print(f"Грешка: {e}")
            return None

    @staticmethod
    def get_all_teachers():
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute('''
                SELECT t.teacher_id, u.user_name, u.user_surname
                FROM teacher t
                JOIN "User" u ON t.teacher_id = u.user_id
                ORDER BY u.user_name
            ''')
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return rows
        except Exception as e:
            print(f"Грешка: {e}")
            return []

    @staticmethod
    def get_all_users():
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute('SELECT user_id, user_name, user_surname, email, role FROM "User" ORDER BY user_name')
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return rows
        except Exception as e:
            print(f"Грешка: {e}")
            return None

    # ---------- ELEMENTS ----------
    @staticmethod
    def get_all_elements():
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute('''
                SELECT element_id, symbol, element_name, atomic_number, 
                       atomic_weight, melting_point, boiling_point, hazard_type, description_element
                FROM elements
                ORDER BY atomic_number
            ''')
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return rows
        except Exception as e:
            print(f"Грешка: {e}")
            return None

    @staticmethod
    def add_element(symbol, name, atomic_number, atomic_weight, melting_point, boiling_point, hazard_type, description, teacher_id):
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO elements (symbol, element_name, atomic_number, atomic_weight, melting_point, boiling_point, hazard_type, description_element, teacher_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING element_id
            ''', (symbol, name, atomic_number, atomic_weight, melting_point, boiling_point, hazard_type, description, teacher_id))
            el_id = cur.fetchone()['element_id']
            conn.commit()
            cur.close()
            conn.close()
            return el_id
        except Exception as e:
            print(f"Грешка при додавање елемент: {e}")
            return None

    @staticmethod
    def update_element(element_id, symbol, name, atomic_number, atomic_weight, melting_point, boiling_point, hazard_type, description):
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute('''
                UPDATE elements 
                SET symbol = %s, element_name = %s, atomic_number = %s, atomic_weight = %s, 
                    melting_point = %s, boiling_point = %s, hazard_type = %s, description_element = %s
                WHERE element_id = %s
            ''', (symbol, name, atomic_number, atomic_weight, melting_point, boiling_point, hazard_type, description, element_id))
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Грешка: {e}")
            return False

    @staticmethod
    def get_element_by_id(element_id):
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute('''
                SELECT e.*, u.user_name || ' ' || u.user_surname AS created_by
                FROM elements e
                JOIN "User" u ON e.teacher_id = u.user_id
                WHERE e.element_id = %s
            ''', (element_id,))
            row = cur.fetchone()
            cur.close()
            conn.close()
            return dict(row) if row else None
        except Exception as e:
            print(f"Грешка: {e}")
            return None

    # ---------- LAB EQUIPMENT ----------
    @staticmethod
    def get_all_equipment():
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute('''
                SELECT equipment_id, equipment_name, type, description, safety_info
                FROM labequipment
                ORDER BY equipment_name
            ''')
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return rows
        except Exception as e:
            print(f"Грешка: {e}")
            return None

    @staticmethod
    def add_lab_equipment(name, equipment_type, description, safety_info, teacher_id):
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO labequipment (equipment_name, type, description, safety_info, teacher_id)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING equipment_id
            ''', (name, equipment_type, description, safety_info, teacher_id))
            eq_id = cur.fetchone()['equipment_id']
            conn.commit()
            cur.close()
            conn.close()
            return eq_id
        except Exception as e:
            print(f"Грешка при додавање опрема: {e}")
            return None

    @staticmethod
    def update_equipment(equipment_id, name, equipment_type, description, safety_info):
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute('''
                UPDATE labequipment 
                SET equipment_name = %s, type = %s, description = %s, safety_info = %s
                WHERE equipment_id = %s
            ''', (name, equipment_type, description, safety_info, equipment_id))
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Грешка: {e}")
            return False

    @staticmethod
    def get_equipment_by_id(equipment_id):
        rows = DatabaseManager.get_all_equipment()
        if not rows:
            return None
        for item in rows:
            if item['equipment_id'] == equipment_id:
                return item
        return None

    # ---------- REACTIONS ----------
    @staticmethod
    def add_reaction(teacher_id, element1_id, element2_id, product, conditions):
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO reaction (teacher_id, element1_id, element2_id, product, conditions)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING reaction_id
            ''', (teacher_id, element1_id, element2_id, product, conditions))
            rid = cur.fetchone()['reaction_id']
            conn.commit()
            cur.close()
            conn.close()
            return rid
        except Exception as e:
            print(f"Грешка: {e}")
            return None

    @staticmethod
    def update_reaction(reaction_id, element1_id, element2_id, product, conditions):
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute('''
                UPDATE reaction 
                SET element1_id = %s, element2_id = %s, product = %s, conditions = %s
                WHERE reaction_id = %s
            ''', (element1_id, element2_id, product, conditions, reaction_id))
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Грешка: {e}")
            return False

    @staticmethod
    def delete_reaction(reaction_id):
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute('DELETE FROM reaction WHERE reaction_id = %s', (reaction_id,))
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Грешка: {e}")
            return False

    @staticmethod
    def get_all_reactions():
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute('''
                SELECT r.*,
                       e1.symbol  AS element1_symbol, e1.element_name AS element1_name,
                       e2.symbol  AS element2_symbol, e2.element_name AS element2_name,
                       u.user_name || ' ' || u.user_surname AS created_by
                FROM reaction r
                JOIN elements e1 ON r.element1_id = e1.element_id
                JOIN elements e2 ON r.element2_id = e2.element_id
                JOIN "User" u   ON r.teacher_id = u.user_id
                ORDER BY r.reaction_id DESC
            ''')
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return rows
        except Exception as e:
            print(f"Грешка: {e}")
            return []

    @staticmethod
    def get_reaction_by_id(reaction_id):
        rows = DatabaseManager.get_all_reactions()
        if not rows:
            return None
        for r in rows:
            if r['reaction_id'] == reaction_id:
                return r
        return None

    # ---------- EXPERIMENTS ----------
    @staticmethod
    def insert_experiment(teacher_id, reaction_id, result, safety_warning):
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO experiment (teacher_id, reaction_id, result, safety_warning, time_stamp)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                RETURNING experiment_id
            ''', (teacher_id, reaction_id, result, safety_warning))
            eid = cur.fetchone()['experiment_id']
            conn.commit()
            cur.close()
            conn.close()
            return eid
        except Exception as e:
            print(f"Грешка: {e}")
            return None

    @staticmethod
    def get_all_experiments():
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute('''
                SELECT e.experiment_id,
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
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return rows
        except Exception as e:
            print(f"Грешка: {e}")
            return []

    @staticmethod
    def get_experiment_equipment(experiment_id):
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute('''
                SELECT le.equipment_name, le.type, le.safety_info
                FROM experimentlabequipment ele
                JOIN labequipment le ON ele.equipment_id = le.equipment_id
                WHERE ele.experiment_id = %s
            ''', (experiment_id,))
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return rows
        except Exception as e:
            print(f"Грешка: {e}")
            return []

    # ---------- PARTICIPATION / VIEWS ----------
    @staticmethod
    def track_experiment_participation(user_id, experiment_id):
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO userparticipatesinexperiment (user_id, experiment_id)
                VALUES (%s, %s)
            ''', (user_id, experiment_id))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Грешка при додавање учество: {e}")

    @staticmethod
    def get_user_experiments(user_id):
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute('''
                SELECT e.*,
                       r.product,
                       r.conditions,
                       el1.symbol AS element1_symbol, el1.element_name AS element1_name,
                       el2.symbol AS element2_symbol, el2.element_name AS element2_name,
                       up.participation_timestamp
                FROM experiment e
                JOIN userparticipatesinexperiment up ON e.experiment_id = up.experiment_id
                JOIN reaction r ON e.reaction_id = r.reaction_id
                JOIN elements el1 ON r.element1_id = el1.element_id
                JOIN elements el2 ON r.element2_id = el2.element_id
                WHERE up.user_id = %s
                ORDER BY up.participation_timestamp DESC
            ''', (user_id,))
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return rows
        except Exception as e:
            print(f"Грешка: {e}")
            return []

    @staticmethod
    def track_element_view(user_id, element_id):
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute('SELECT 1 FROM userviewselement WHERE user_id = %s AND element_id = %s',
                        (user_id, element_id))
            if not cur.fetchone():
                cur.execute('INSERT INTO userviewselement (user_id, element_id) VALUES (%s, %s)',
                            (user_id, element_id))
                conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Грешка при tracking (element): {e}")

    @staticmethod
    def track_equipment_view(user_id, equipment_id):
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute('SELECT 1 FROM userviewslabequipment WHERE user_id = %s AND equipment_id = %s',
                        (user_id, equipment_id))
            if not cur.fetchone():
                cur.execute('INSERT INTO userviewslabequipment (user_id, equipment_id) VALUES (%s, %s)',
                            (user_id, equipment_id))
                conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Грешка при tracking (equipment): {e}")

    # ---------- REPORT EXAMPLES ----------
    @staticmethod
    def get_equipment_usage_report():
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute('''
                SELECT le.equipment_name,
                       COUNT(ele.experiment_id) AS usage_count
                FROM experimentlabequipment ele
                RIGHT JOIN labequipment le ON ele.equipment_id = le.equipment_id
                GROUP BY le.equipment_name, le.equipment_id
                ORDER BY usage_count DESC, le.equipment_name
            ''')
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return rows
        except Exception as e:
            print(f"Грешка: {e}")
            return []

    # ---------- NEW: N:M helper ----------
    @staticmethod
    def add_experiment_equipment(experiment_id, equipment_ids, conn=None, cur=None):
        """Bulk insert во experimentlabequipment; ако нема листа, ништо не прави."""
        if not equipment_ids:
            return
        own = False
        if conn is None or cur is None:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            own = True

        values_sql = ",".join(["(%s,%s)"] * len(equipment_ids))
        params = []
        for eq_id in equipment_ids:
            params.extend([experiment_id, eq_id])

        cur.execute(f'''
            INSERT INTO experimentlabequipment (experiment_id, equipment_id)
            VALUES {values_sql}
            ON CONFLICT DO NOTHING
        ''', params)

        if own:
            conn.commit()
            cur.close()
            conn.close()

    # ---------- NEW: main transactional creator ----------
    @staticmethod
    def create_reaction_and_experiment(
        teacher_id,
        element1_id,
        element2_id,
        product,
        conditions,
        experiment_result,         # опис во проза (НЕ product)
        safety_warning=None,
        equipment_ids=None         # листа од int
    ):
        """Креира Reaction → Experiment (+ опрема) во ЕДНА транскација."""
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()

            # 1) Reaction
            cur.execute('''
                INSERT INTO reaction (teacher_id, element1_id, element2_id, product, conditions)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING reaction_id
            ''', (teacher_id, element1_id, element2_id, product, conditions))
            reaction_id = cur.fetchone()['reaction_id']

            # 2) Ако нема експериментски опис → генерирај од симболи
            if not experiment_result:
                # симболи
                cur.execute('SELECT symbol FROM elements WHERE element_id = %s', (element1_id,))
                s1 = cur.fetchone()['symbol']
                cur.execute('SELECT symbol FROM elements WHERE element_id = %s', (element2_id,))
                s2 = cur.fetchone()['symbol']
                experiment_result = (
                    f"Експеримент со {s1} и {s2} под услови: {conditions or 'стандардни'}. "
                    f"Очекуван производ: {product or 'непознат'}."
                )

            # 3) Experiment
            cur.execute('''
                INSERT INTO experiment (teacher_id, reaction_id, result, safety_warning, time_stamp)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                RETURNING experiment_id
            ''', (teacher_id, reaction_id, experiment_result, safety_warning))
            experiment_id = cur.fetchone()['experiment_id']

            # 4) Equipment links
            if equipment_ids:
                DatabaseManager.add_experiment_equipment(
                    experiment_id=experiment_id,
                    equipment_ids=equipment_ids,
                    conn=conn, cur=cur
                )

            conn.commit()
            cur.close()
            conn.close()
            return {"reaction_id": reaction_id, "experiment_id": experiment_id}

        except Exception as e:
            if conn:
                conn.rollback()
                conn.close()
            print(f"Грешка при креирање реакција+експеримент: {e}")
            return None
# --- ДОДАДИ ВО КЛАСАТА DatabaseManager ---

    @staticmethod
    def get_experiment_by_reaction(reaction_id):
        """Врати го најновиот експеримент за дадена реакција (или None)."""
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT *
                FROM experiment
                WHERE reaction_id = %s
                ORDER BY time_stamp DESC
                LIMIT 1
            """, (reaction_id,))
            row = cur.fetchone()
            cur.close(); conn.close()
            return dict(row) if row else None
        except Exception as e:
            print(f"Грешка get_experiment_by_reaction: {e}")
            return None


    @staticmethod
    def add_experiment_equipment(experiment_id, equipment_ids, conn=None, cur=None):
        """Додај повеќе записи во N:M табелата experimentlabequipment."""
        own_conn = own_cur = False
        try:
            if conn is None or cur is None:
                conn = DatabaseManager.get_connection(); own_conn = True
                cur = conn.cursor(); own_cur = True

            if equipment_ids:
                cur.executemany(
                    "INSERT INTO experimentlabequipment (experiment_id, equipment_id) VALUES (%s, %s)",
                    [(experiment_id, eq_id) for eq_id in equipment_ids]
                )

            if own_conn:
                conn.commit()
            return True
        except Exception as e:
            if own_conn and conn:
                conn.rollback()
            print(f"Грешка add_experiment_equipment: {e}")
            return False
        finally:
            if own_cur:
                cur.close()
            if own_conn and conn:
                conn.close()


    @staticmethod
    def create_reaction_and_experiment(
        teacher_id,
        element1_id,
        element2_id,
        product,
        conditions,
        experiment_result=None,
        safety_warning=None,
        equipment_ids=None
    ):
        """
        Креирај реакција + експеримент во една транскација.
        experiment_result е опис во проза (не е исто со product).
        equipment_ids е листа од INT (опционално).
        """
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()

            # 1) Reaction
            cur.execute("""
                INSERT INTO reaction (teacher_id, element1_id, element2_id, product, conditions)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING reaction_id
            """, (teacher_id, element1_id, element2_id, product, conditions))
            reaction_id = cur.fetchone()[0]

            # 2) Experiment
            if not experiment_result:
                experiment_result = f"Експеримент за: {product or 'непознат производ'}"

            cur.execute("""
                INSERT INTO experiment (teacher_id, reaction_id, result, safety_warning, time_stamp)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                RETURNING experiment_id
            """, (teacher_id, reaction_id, experiment_result, safety_warning or 'Стандардни безбедносни мерки'))
            experiment_id = cur.fetchone()[0]

            # 3) Опрема (ако има)
            if equipment_ids:
                cur.executemany(
                    "INSERT INTO experimentlabequipment (experiment_id, equipment_id) VALUES (%s, %s)",
                    [(experiment_id, eq_id) for eq_id in equipment_ids]
                )

            conn.commit()
            cur.close(); conn.close()
            return {'reaction_id': reaction_id, 'experiment_id': experiment_id}

        except Exception as e:
            if conn: conn.rollback()
            print(f"Грешка create_reaction_and_experiment: {e}")
            return None
        finally:
            if conn:
                try: conn.close()
                except: pass
    
    @staticmethod
    def get_student_participation_experiments(student_id):
        """Експерименти во кои студентот учествувал (со детали за реакцијата)."""
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT
                    e.experiment_id,
                    e.result,
                    e.safety_warning,
                    e.time_stamp,
                    r.product,
                    r.conditions,
                    el1.symbol AS element1_symbol,
                    el1.element_name AS element1_name,
                    el2.symbol AS element2_symbol,
                    el2.element_name AS element2_name
                FROM userparticipatesinexperiment up
                JOIN experiment e ON up.experiment_id = e.experiment_id
                JOIN reaction  r  ON e.reaction_id = r.reaction_id
                JOIN elements el1 ON r.element1_id = el1.element_id
                JOIN elements el2 ON r.element2_id = el2.element_id
                WHERE up.user_id = %s
                ORDER BY e.time_stamp DESC
            """, (student_id,))
            rows = cur.fetchall()
            cur.close(); conn.close()
            return rows
        except Exception as e:
            print(f"Грешка get_student_participation_experiments: {e}")
            return []
    @staticmethod
    def get_student_statistics(student_id):
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM userparticipatesinexperiment WHERE user_id = %s) AS experiment_count,
                    (SELECT COUNT(*) FROM userviewselement             WHERE user_id = %s) AS element_count,
                    (SELECT COUNT(*) FROM userviewslabequipment        WHERE user_id = %s) AS equipment_count,
                    (
                        SELECT COUNT(DISTINCT e.reaction_id)
                        FROM userparticipatesinexperiment up
                        JOIN experiment e ON up.experiment_id = e.experiment_id
                        WHERE up.user_id = %s
                    ) AS reaction_count
            """, (student_id, student_id, student_id, student_id))
            row = cur.fetchone()
            cur.close(); conn.close()
            return dict(row) if row else {
                'experiment_count': 0, 'element_count': 0, 'equipment_count': 0, 'reaction_count': 0
            }
        except Exception as e:
            print(f"Грешка get_student_statistics: {e}")
            return {'experiment_count': 0, 'element_count': 0, 'equipment_count': 0, 'reaction_count': 0}

    @staticmethod
    def get_teacher_dashboard_statistics(teacher_id):
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()

            def get_c():
                row = cur.fetchone()
                if row is None:
                    return 0
                try:
                    return int(row['c'])   # RealDictRow
                except Exception:
                    return int(row[0])     # tuple fallback

            # 1) број на студенти
            cur.execute("""
                SELECT COUNT(*) AS c
                FROM student
                WHERE teacher_id = %s
            """, (teacher_id,))
            student_count = get_c()

            # 2) број на реакции на овој професор
            cur.execute("""
                SELECT COUNT(*) AS c
                FROM reaction
                WHERE teacher_id = %s
            """, (teacher_id,))
            reaction_count = get_c()

            # 3) број на експерименти креирани од овој професор
            cur.execute("""
                SELECT COUNT(*) AS c
                FROM experiment
                WHERE teacher_id = %s
            """, (teacher_id,))
            experiment_count = get_c()

            # 4) активности денес — прво пробај participation_timestamp; ако ја нема колоната, падни на e.time_stamp
            try:
                cur.execute("""
                    SELECT COUNT(*) AS c
                    FROM userparticipatesinexperiment up
                    JOIN student s ON up.user_id = s.student_id
                    WHERE s.teacher_id = %s
                    AND up.participation_timestamp::date = CURRENT_DATE
                """, (teacher_id,))
                activity_count = get_c()
            except Exception:
                cur.execute("""
                    SELECT COUNT(*) AS c
                    FROM userparticipatesinexperiment up
                    JOIN student   s ON up.user_id       = s.student_id
                    JOIN experiment e ON up.experiment_id = e.experiment_id
                    WHERE s.teacher_id = %s
                    AND e.time_stamp::date = CURRENT_DATE
                """, (teacher_id,))
                activity_count = get_c()

            cur.close(); conn.close()
            return {
                'student_count': student_count,
                'reaction_count': reaction_count,
                'experiment_count': experiment_count,
                'activity_count': activity_count
            }
        except Exception as e:
            print("Грешка get_teacher_dashboard_statistics:", e)
            try:
                cur.close(); conn.close()
            except Exception:
                pass
            return {'student_count': 0, 'reaction_count': 0, 'experiment_count': 0, 'activity_count': 0}

    @staticmethod
    def get_my_students_activity(teacher_id):
        """Активност на студентите на конкретен професор: прегледани елементи/опрема."""
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    s.student_id,
                    (u.user_name || ' ' || u.user_surname) AS full_name,
                    COALESCE(COUNT(DISTINCT uve.element_id), 0)      AS total_elements_viewed,
                    COALESCE(COUNT(DISTINCT uvl.equipment_id), 0)    AS total_lab_equipment_viewed
                FROM student s
                JOIN "User" u ON s.student_id = u.user_id
                LEFT JOIN userviewselement      uve ON s.student_id = uve.user_id
                LEFT JOIN userviewslabequipment uvl ON s.student_id = uvl.user_id
                WHERE s.teacher_id = %s
                GROUP BY s.student_id, full_name
                ORDER BY total_elements_viewed DESC, total_lab_equipment_viewed DESC
            """, (teacher_id,))
            rows = cur.fetchall()
            cur.close(); conn.close()
            return rows
        except Exception as e:
            print(f"Грешка get_my_students_activity: {e}")
            return []
        
    @staticmethod
    def get_students_without_experiments(teacher_id):
        """Студенти на конкретен професор кои немаат ниту еден експеримент."""
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    s.student_id,
                    (u.user_name || ' ' || u.user_surname) AS full_name
                FROM student s
                JOIN "User" u ON s.student_id = u.user_id
                LEFT JOIN userparticipatesinexperiment up ON s.student_id = up.user_id
                WHERE s.teacher_id = %s
                AND up.user_id IS NULL
                ORDER BY full_name
            """, (teacher_id,))
            rows = cur.fetchall()
            cur.close(); conn.close()
            return rows
        except Exception as e:
            print(f"Грешка get_students_without_experiments: {e}")
            return []


    @staticmethod
    def get_students_with_few_experiments(teacher_id, max_experiments=3):
        """Студенти со помалку од max_experiments експерименти."""
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    s.student_id,
                    (u.user_name || ' ' || u.user_surname) AS full_name,
                    COUNT(up.experiment_id) AS total_experiments
                FROM student s
                JOIN "User" u ON s.student_id = u.user_id
                LEFT JOIN userparticipatesinexperiment up ON s.student_id = up.user_id
                WHERE s.teacher_id = %s
                GROUP BY s.student_id, full_name
                HAVING COUNT(up.experiment_id) < %s
                ORDER BY total_experiments ASC, full_name
            """, (teacher_id, max_experiments))
            rows = cur.fetchall()
            cur.close(); conn.close()
            return rows
        except Exception as e:
            print(f"Грешка get_students_with_few_experiments: {e}")
            return []


    @staticmethod
    def get_students_experiments_detailed(teacher_id):
        """Детален извештај за студентите на професорот и нивните експерименти."""
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    s.student_id,
                    (u.user_name || ' ' || u.user_surname) AS full_name,
                    e.experiment_id,
                    e.result,
                    e.time_stamp AS participation_time
                FROM student s
                JOIN "User" u ON s.student_id = u.user_id
                JOIN userparticipatesinexperiment up ON s.student_id = up.user_id
                JOIN experiment e ON up.experiment_id = e.experiment_id
                WHERE s.teacher_id = %s
                ORDER BY u.user_name, e.time_stamp DESC
            """, (teacher_id,))
            rows = cur.fetchall()
            cur.close(); conn.close()
            return rows
        except Exception as e:
            print(f"Грешка get_students_experiments_detailed: {e}")
            return []


    @staticmethod
    def get_element_views_report():
        """Кој корисник кои елементи ги прегледал (агрегиран извештај)."""
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    (u.user_name || ' ' || u.user_surname) AS full_name,
                    u.role,
                    e.symbol,
                    e.element_name,
                    COUNT(*) AS view_count
                FROM userviewselement uve
                JOIN "User" u ON uve.user_id = u.user_id
                JOIN elements e ON uve.element_id = e.element_id
                GROUP BY u.user_id, u.user_name, u.user_surname, u.role, 
                        e.element_id, e.symbol, e.element_name
                ORDER BY u.user_name, e.symbol
            """)
            rows = cur.fetchall()
            cur.close(); conn.close()
            return rows
        except Exception as e:
            print(f"Грешка get_element_views_report: {e}")
            return []


    @staticmethod
    def get_teacher_statistics():
        """Статистики за сите професори (вкупно студенти/експерименти и просек по студент)."""
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    t.teacher_id,
                    (u.user_name || ' ' || u.user_surname) AS full_name,
                    COUNT(DISTINCT s.student_id) AS total_students,
                    COUNT(up.experiment_id)      AS total_experiments,
                    ROUND(
                        COUNT(up.experiment_id) * 1.0 / NULLIF(COUNT(DISTINCT s.student_id), 0), 2
                    ) AS avg_experiments_per_student
                FROM teacher t
                JOIN "User" u ON t.teacher_id = u.user_id
                LEFT JOIN student s ON t.teacher_id = s.teacher_id
                LEFT JOIN userparticipatesinexperiment up ON s.student_id = up.user_id
                GROUP BY t.teacher_id, full_name
                ORDER BY avg_experiments_per_student DESC, full_name
            """)
            rows = cur.fetchall()
            cur.close(); conn.close()
            return rows
        except Exception as e:
            print(f"Грешка get_teacher_statistics: {e}")
            return []


    @staticmethod
    def get_students_experiments_for_teacher(teacher_id):
        """Експерименти изведени од студентите на даден професор (за извештаи)."""
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    (u.user_name || ' ' || u.user_surname) AS student_name,
                    s.student_id,
                    e.experiment_id,
                    e.result,
                    e.time_stamp,
                    r.product,
                    el1.symbol AS element1_symbol,
                    el2.symbol AS element2_symbol,
                    up.participation_timestamp AS participation_date
                FROM student s
                JOIN "User" u ON s.student_id = u.user_id
                JOIN userparticipatesinexperiment up ON s.student_id = up.user_id
                JOIN experiment e ON up.experiment_id = e.experiment_id
                JOIN reaction  r ON e.reaction_id   = r.reaction_id
                JOIN elements el1 ON r.element1_id = el1.element_id
                JOIN elements el2 ON r.element2_id = el2.element_id
                WHERE s.teacher_id = %s
                ORDER BY up.participation_timestamp DESC, student_name
            """, (teacher_id,))
            rows = cur.fetchall()
            cur.close(); conn.close()
            return rows
        except Exception as e:
            print(f"Грешка get_students_experiments_for_teacher: {e}")
            return []


    @staticmethod
    def get_user_activity_summary():
        """Сумарен извештај за активности по корисник (елементи/опрема/експерименти)."""
        try:
            conn = DatabaseManager.get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    u.user_id,
                    (u.user_name || ' ' || u.user_surname) AS full_name,
                    u.role,
                    COUNT(DISTINCT uve.element_id)     AS elements_viewed,
                    COUNT(DISTINCT uvl.equipment_id)   AS equipment_viewed,
                    COUNT(DISTINCT upe.experiment_id)  AS experiments_participated
                FROM "User" u
                LEFT JOIN userviewselement           uve ON u.user_id = uve.user_id
                LEFT JOIN userviewslabequipment      uvl ON u.user_id = uvl.user_id
                LEFT JOIN userparticipatesinexperiment upe ON u.user_id = upe.user_id
                GROUP BY u.user_id, full_name, u.role
                ORDER BY full_name
            """)
            rows = cur.fetchall()
            cur.close(); conn.close()
            return rows
        except Exception as e:
            print(f"Грешка get_user_activity_summary: {e}")
            return []

