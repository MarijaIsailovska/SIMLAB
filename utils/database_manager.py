# database_manager.py
import os, logging
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values

log = logging.getLogger("simlab.db")
class DatabaseManager:
    # ---------- CONNECTION ----------
    @staticmethod
    def get_connection():
        return psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '9999')),
            database=os.getenv('DB_NAME', 'db_202425z_va_prj_simlab25'),
            user=os.getenv('DB_USER', 'db_202425z_va_prj_simlab25_owner'),
            password=os.getenv('DB_PASS', 'c9e5ebb7d332'),
            cursor_factory=RealDictCursor
        )
    
@contextmanager
def _conn_cur():
    conn = DatabaseManager.get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                yield cur
    finally:
        conn.close()

class DatabaseManager(DatabaseManager):  # extend class with methods
    # ---------- GENERIC EXEC ----------
    @staticmethod
    def execute_query(query, params=None):
        try:
            with _conn_cur() as cur:
                cur.execute(query, params or ())
                return cur.fetchall()
        except Exception:
            log.exception("execute_query failed: %s | params=%s", query, params)
            return None



    @staticmethod
    def test_connection():
        try:
            with _conn_cur() as cur:
                cur.execute("SELECT 1")
            return True
        except Exception:
            log.exception("test_connection failed")
            return False

    # ---------- USERS / AUTH ----------
    @staticmethod
    def authenticate_user(email, password):
        """Fetch user row by email. Password check is done in service layer."""
        try:
            with _conn_cur() as cur:
                cur.execute(
                    'SELECT user_id, user_name, user_surname, email, role, password '
                    'FROM "User" WHERE email = %s',
                    (email,)
                )
                row = cur.fetchone()
                return dict(row) if row else None
        except Exception:
            log.exception("authenticate_user failed (email=%s)", email)
            return None

    @staticmethod
    def register_user(name, surname, email, password_hash, role, teacher_id=None):
        try:
            with _conn_cur() as cur:
                # User
                cur.execute(
                    'INSERT INTO "User" (user_name, user_surname, email, password, role) '
                    'VALUES (%s, %s, %s, %s, %s) RETURNING user_id',
                    (name, surname, email, password_hash, role)
                )
                user_id = cur.fetchone()['user_id']

                # Subtype
                if role == 'student' and teacher_id:
                    cur.execute(
                        'INSERT INTO student (student_id, teacher_id) VALUES (%s, %s)',
                        (user_id, teacher_id)
                    )
                elif role == 'teacher':
                    cur.execute('INSERT INTO teacher (teacher_id) VALUES (%s)', (user_id,))

                return user_id
        except Exception:
            log.exception("register_user failed (email=%s, role=%s)", email, role)
            return None

    @staticmethod
    def get_user_by_id(user_id):
        try:
            with _conn_cur() as cur:
                cur.execute('''
                    SELECT u.*, s.teacher_id
                    FROM "User" u
                    LEFT JOIN student s ON u.user_id = s.student_id
                    WHERE u.user_id = %s
                ''', (user_id,))
                row = cur.fetchone()
                return dict(row) if row else None
        except Exception:
            log.exception("get_user_by_id failed (%s)", user_id)
            return None

    @staticmethod
    def get_all_teachers():
        try:
            with _conn_cur() as cur:
                cur.execute('''
                    SELECT t.teacher_id, u.user_name, u.user_surname
                    FROM teacher t
                    JOIN "User" u ON t.teacher_id = u.user_id
                    ORDER BY u.user_name
                ''')
                return cur.fetchall()
        except Exception:
            log.exception("get_all_teachers failed")
            return []

    @staticmethod
    def get_all_users():
        try:
            with _conn_cur() as cur:
                cur.execute('SELECT user_id, user_name, user_surname, email, role FROM "User" ORDER BY user_name')
                return cur.fetchall()
        except Exception:
            log.exception("get_all_users failed")
            return None

    # ---------- ELEMENTS ----------
    @staticmethod
    def get_all_elements():
        try:
            with _conn_cur() as cur:
                cur.execute('''
                    SELECT element_id, symbol, element_name, atomic_number, 
                           atomic_weight, melting_point, boiling_point, hazard_type, description_element
                    FROM elements
                    ORDER BY atomic_number
                ''')
                return cur.fetchall()
        except Exception:
            log.exception("get_all_elements failed")
            return None
        

    @staticmethod
    def add_element(symbol, name, atomic_number, atomic_weight, melting_point, boiling_point, hazard_type, description, teacher_id):
        try:
            with _conn_cur() as cur:
                cur.execute('''
                    INSERT INTO elements (symbol, element_name, atomic_number, atomic_weight, 
                                          melting_point, boiling_point, hazard_type, description_element, teacher_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING element_id
                ''', (symbol, name, atomic_number, atomic_weight, melting_point, boiling_point, hazard_type, description, teacher_id))
                return cur.fetchone()['element_id']
        except Exception:
            log.exception("add_element failed (symbol=%s, name=%s)", symbol, name)
            return None

    @staticmethod
    def update_element(element_id, symbol, name, atomic_number, atomic_weight, melting_point, boiling_point, hazard_type, description):
        try:
            with _conn_cur() as cur:
                cur.execute('''
                    UPDATE elements 
                    SET symbol = %s, element_name = %s, atomic_number = %s, atomic_weight = %s, 
                        melting_point = %s, boiling_point = %s, hazard_type = %s, description_element = %s
                    WHERE element_id = %s
                ''', (symbol, name, atomic_number, atomic_weight, melting_point, boiling_point, hazard_type, description, element_id))
                return True
        except Exception:
            log.exception("update_element failed (element_id=%s)", element_id)
            return False

    @staticmethod
    def get_element_by_id(element_id):
        try:
            with _conn_cur() as cur:
                cur.execute('''
                    SELECT e.*, u.user_name || ' ' || u.user_surname AS created_by
                    FROM elements e
                    JOIN "User" u ON e.teacher_id = u.user_id
                    WHERE e.element_id = %s
                ''', (element_id,))
                row = cur.fetchone()
                return dict(row) if row else None
        except Exception:
            log.exception("get_element_by_id failed (%s)", element_id)
            return None

    # ---------- LAB EQUIPMENT ----------
    @staticmethod
    def get_all_equipment():
        try:
            with _conn_cur() as cur:
                cur.execute('''
                    SELECT equipment_id, equipment_name, type, description, safety_info
                    FROM labequipment
                    ORDER BY equipment_name
                ''')
                return cur.fetchall()
        except Exception:
            log.exception("get_all_equipment failed")
            return None

    @staticmethod
    def add_lab_equipment(name, equipment_type, description, safety_info, teacher_id):
        try:
            with _conn_cur() as cur:
                cur.execute('''
                    INSERT INTO labequipment (equipment_name, type, description, safety_info, teacher_id)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING equipment_id
                ''', (name, equipment_type, description, safety_info, teacher_id))
                return cur.fetchone()['equipment_id']
        except Exception:
            log.exception("add_lab_equipment failed (name=%s, type=%s)", name, equipment_type)
            return None

    @staticmethod
    def update_equipment(equipment_id, name, equipment_type, description, safety_info):
        try:
            with _conn_cur() as cur:
                cur.execute('''
                    UPDATE labequipment 
                    SET equipment_name = %s, type = %s, description = %s, safety_info = %s
                    WHERE equipment_id = %s
                ''', (name, equipment_type, description, safety_info, equipment_id))
                return True
        except Exception:
            log.exception("update_equipment failed (equipment_id=%s)", equipment_id)
            return False

    @staticmethod
    def get_equipment_by_id(equipment_id):
        try:
            with _conn_cur() as cur:
                cur.execute("""
                    SELECT equipment_id, equipment_name, type, description, safety_info
                    FROM labequipment WHERE equipment_id = %s
                """, (equipment_id,))
                row = cur.fetchone()
                return dict(row) if row else None
        except Exception:
            log.exception("get_equipment_by_id failed (%s)", equipment_id)
            return None


    # ---------- REACTIONS ----------
    @staticmethod
    def add_reaction(teacher_id, element1_id, element2_id, product, conditions):
        try:
            with _conn_cur() as cur:
                cur.execute('''
                    INSERT INTO reaction (teacher_id, element1_id, element2_id, product, conditions)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING reaction_id
                ''', (teacher_id, element1_id, element2_id, product, conditions))
                return cur.fetchone()['reaction_id']
        except Exception:
            log.exception("add_reaction failed")
            return None

    @staticmethod
    def update_reaction(reaction_id, element1_id, element2_id, product, conditions):
        try:
            with _conn_cur() as cur:
                cur.execute('''
                    UPDATE reaction 
                    SET element1_id = %s, element2_id = %s, product = %s, conditions = %s
                    WHERE reaction_id = %s
                ''', (element1_id, element2_id, product, conditions, reaction_id))
                return True
        except Exception:
            log.exception("update_reaction failed (reaction_id=%s)", reaction_id)
            return False

    @staticmethod
    def delete_reaction(reaction_id):
        try:
            with _conn_cur() as cur:
                cur.execute('DELETE FROM reaction WHERE reaction_id = %s', (reaction_id,))
                return True
        except Exception:
            log.exception("delete_reaction failed (reaction_id=%s)", reaction_id)
            return False

    @staticmethod
    def get_all_reactions():
        try:
            with _conn_cur() as cur:
                cur.execute('''
                    SELECT r.*,
                           e1.symbol  AS element1_symbol, e1.element_name AS element1_name,
                           e2.symbol  AS element2_symbol, e2.element_name AS element2_name,
                           u.user_name || ' ' || u.user_surname AS created_by
                    FROM reaction r
                    JOIN elements e1 ON r.element1_id = e1.element_id
                    JOIN elements e2 ON r.element2_id = e2.element_id
                    JOIN "User"  u   ON r.teacher_id = u.user_id
                    ORDER BY r.reaction_id DESC
                ''')
                return cur.fetchall()
        except Exception:
            log.exception("get_all_reactions failed")
            return []

    @staticmethod
    def get_reaction_by_id(reaction_id):
        try:
            with _conn_cur() as cur:
                cur.execute("""
                    SELECT r.*,
                           e1.symbol  AS element1_symbol, e1.element_name AS element1_name,
                           e2.symbol  AS element2_symbol, e2.element_name AS element2_name,
                           u.user_name || ' ' || u.user_surname AS created_by
                    FROM reaction r
                    JOIN elements e1 ON r.element1_id = e1.element_id
                    JOIN elements e2 ON r.element2_id = e2.element_id
                    JOIN "User"  u   ON r.teacher_id = u.user_id
                    WHERE r.reaction_id = %s
                """, (reaction_id,))
                row = cur.fetchone()
                return dict(row) if row else None
        except Exception:
            log.exception("get_reaction_by_id failed (%s)", reaction_id)
            return None
        

    # ---------- EXPERIMENTS ----------
    @staticmethod
    def insert_experiment(teacher_id, reaction_id, result, safety_warning):
        try:
            with _conn_cur() as cur:
                cur.execute('''
                    INSERT INTO experiment (teacher_id, reaction_id, result, safety_warning, time_stamp)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                    RETURNING experiment_id
                ''', (teacher_id, reaction_id, result, safety_warning))
                return cur.fetchone()['experiment_id']
        except Exception:
            log.exception("insert_experiment failed")
            return None

    @staticmethod
    def get_all_experiments():
        try:
            with _conn_cur() as cur:
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
                return cur.fetchall()
        except Exception:
            log.exception("get_all_experiments failed")
            return []

    @staticmethod
    def get_experiment_by_id(experiment_id):
        try:
            with _conn_cur() as cur:
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
                    WHERE e.experiment_id = %s
                ''', (experiment_id,))
                row = cur.fetchone()
                return dict(row) if row else None
        except Exception:
            log.exception("get_experiment_by_id failed (%s)", experiment_id)
            return None

    @staticmethod
    def get_experiment_equipment(experiment_id):
        try:
            with _conn_cur() as cur:
                cur.execute('''
                    SELECT le.equipment_name, le.type, le.safety_info
                    FROM experimentlabequipment ele
                    JOIN labequipment le ON ele.equipment_id = le.equipment_id
                    WHERE ele.experiment_id = %s
                ''', (experiment_id,))
                return cur.fetchall()
        except Exception:
            log.exception("get_experiment_equipment failed (%s)", experiment_id)
            return []


    # ---------- PARTICIPATION / VIEWS ----------
    @staticmethod
    def track_experiment_participation(user_id, experiment_id):
        try:
            with _conn_cur() as cur:
                cur.execute('''
                    INSERT INTO userparticipatesinexperiment (user_id, experiment_id)
                    VALUES (%s, %s)
                ''', (user_id, experiment_id))
        except Exception:
            log.exception("track_experiment_participation failed")

    @staticmethod
    def get_user_experiments(user_id):
        try:
            with _conn_cur() as cur:
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
                return cur.fetchall()
        except Exception:
            log.exception("get_user_experiments failed (%s)", user_id)
            return []

    @staticmethod
    def track_element_view(user_id, element_id):
        try:
            with _conn_cur() as cur:
                cur.execute('''
                    INSERT INTO userviewselement(user_id, element_id)
                    VALUES (%s, %s) ON CONFLICT DO NOTHING
                ''', (user_id, element_id))
        except Exception:
            log.exception("track_element_view failed")

    @staticmethod
    def track_equipment_view(user_id, equipment_id):
        try:
            with _conn_cur() as cur:
                cur.execute('''
                    INSERT INTO userviewslabequipment(user_id, equipment_id)
                    VALUES (%s, %s) ON CONFLICT DO NOTHING
                ''', (user_id, equipment_id))
        except Exception:
            log.exception("track_equipment_view failed")


    # ---------- REPORT EXAMPLES ----------
    @staticmethod
    def get_equipment_usage_report():
        try:
            with _conn_cur() as cur:
                cur.execute('''
                    SELECT le.equipment_name,
                           COUNT(ele.experiment_id) AS usage_count
                    FROM labequipment le
                    LEFT JOIN experimentlabequipment ele ON ele.equipment_id = le.equipment_id
                    GROUP BY le.equipment_name, le.equipment_id
                    ORDER BY usage_count DESC, le.equipment_name
                ''')
                return cur.fetchall()
        except Exception:
            log.exception("get_equipment_usage_report failed")
            return []


    # ---------- NEW: N:M helper ----------
    @staticmethod
    def add_experiment_equipment(experiment_id, equipment_ids, conn=None, cur=None):
        """Bulk insert into experimentlabequipment; idempotent via ON CONFLICT DO NOTHING."""
        if not equipment_ids:
            return
        rows = [(experiment_id, eq_id) for eq_id in equipment_ids]
        try:
            if conn and cur:
                execute_values(cur, """
                    INSERT INTO experimentlabequipment (experiment_id, equipment_id)
                    VALUES %s ON CONFLICT DO NOTHING
                """, rows)
            else:
                with DatabaseManager.get_connection() as c:
                    with c.cursor() as k:
                        execute_values(k, """
                            INSERT INTO experimentlabequipment (experiment_id, equipment_id)
                            VALUES %s ON CONFLICT DO NOTHING
                        """, rows)
        except Exception:
            log.exception("add_experiment_equipment failed (exp=%s)", experiment_id)

    @staticmethod
    def _create_reaction_and_experiment_python(
        teacher_id,
        element1_id,
        element2_id,
        product,
        conditions,
        experiment_result,         # prose description (NOT product)
        safety_warning=None,
        equipment_ids=None
    ):
        """Create Reaction → Experiment (+equipment) in ONE transaction."""
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            with conn:
                with conn.cursor() as cur:
                    # 1) Reaction
                    cur.execute('''
                        INSERT INTO reaction (teacher_id, element1_id, element2_id, product, conditions)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING reaction_id
                    ''', (teacher_id, element1_id, element2_id, product, conditions))
                    reaction_id = cur.fetchone()['reaction_id']

                    # 2) fallback experiment_result if missing
                    if not experiment_result:
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

            return {"reaction_id": reaction_id, "experiment_id": experiment_id}

        except Exception:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
                try:
                    conn.close()
                except Exception:
                    pass
            log.exception("_create_reaction_and_experiment_python failed")
            return None

    # ---------- helpers / views / stats ----------
    @staticmethod
    def get_experiment_by_reaction(reaction_id):
        try:
            with _conn_cur() as cur:
                cur.execute("""
                    SELECT *
                    FROM experiment
                    WHERE reaction_id = %s
                    ORDER BY time_stamp DESC
                    LIMIT 1
                """, (reaction_id,))
                row = cur.fetchone()
                return dict(row) if row else None
        except Exception:
            log.exception("get_experiment_by_reaction failed (%s)", reaction_id)
            return None

    @staticmethod
    def get_student_participation_experiments(student_id):
        try:
            with _conn_cur() as cur:
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
                return cur.fetchall()
        except Exception:
            log.exception("get_student_participation_experiments failed (%s)", student_id)
            return []

    @staticmethod
    def get_student_statistics(student_id):
        try:
            with _conn_cur() as cur:
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
                return dict(row) if row else {
                    'experiment_count': 0, 'element_count': 0, 'equipment_count': 0, 'reaction_count': 0
                }
        except Exception:
            log.exception("get_student_statistics failed (%s)", student_id)
            return {'experiment_count': 0, 'element_count': 0, 'equipment_count': 0, 'reaction_count': 0}

    @staticmethod
    def get_teacher_dashboard_statistics(teacher_id):
        try:
            with _conn_cur() as cur:
                def get_c():
                    row = cur.fetchone()
                    if row is None:
                        return 0
                    try:
                        return int(row['c'])
                    except Exception:
                        return int(row[0])

                cur.execute("""
                    SELECT COUNT(*) AS c
                    FROM student
                    WHERE teacher_id = %s
                """, (teacher_id,))
                student_count = get_c()

                cur.execute("""
                    SELECT COUNT(*) AS c
                    FROM reaction
                    WHERE teacher_id = %s
                """, (teacher_id,))
                reaction_count = get_c()

                cur.execute("""
                    SELECT COUNT(*) AS c
                    FROM experiment
                    WHERE teacher_id = %s
                """, (teacher_id,))
                experiment_count = get_c()

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

                return {
                    'student_count': student_count,
                    'reaction_count': reaction_count,
                    'experiment_count': experiment_count,
                    'activity_count': activity_count
                }
        except Exception:
            log.exception("get_teacher_dashboard_statistics failed (teacher_id=%s)", teacher_id)
            return {'student_count': 0, 'reaction_count': 0, 'experiment_count': 0, 'activity_count': 0}

    @staticmethod
    def get_my_students_activity(teacher_id):
        try:
            with _conn_cur() as cur:
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
                return cur.fetchall()
        except Exception:
            log.exception("get_my_students_activity failed")
            return []

    @staticmethod
    def get_students_without_experiments(teacher_id):
        try:
            with _conn_cur() as cur:
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
                return cur.fetchall()
        except Exception:
            log.exception("get_students_without_experiments failed")
            return []

    @staticmethod
    def get_students_with_few_experiments(teacher_id, max_experiments=3):
        try:
            with _conn_cur() as cur:
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
                return cur.fetchall()
        except Exception:
            log.exception("get_students_with_few_experiments failed")
            return []

    @staticmethod
    def get_element_views_report():
        try:
            with _conn_cur() as cur:
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
                return cur.fetchall()
        except Exception:
            log.exception("get_element_views_report failed")
            return []

    @staticmethod
    def get_teacher_statistics():
        try:
            with _conn_cur() as cur:
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
                return cur.fetchall()
        except Exception:
            log.exception("get_teacher_statistics failed")
            return []

    @staticmethod
    def get_students_experiments_for_teacher(teacher_id):
        try:
            with _conn_cur() as cur:
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
                return cur.fetchall()
        except Exception:
            log.exception("get_students_experiments_for_teacher failed")
            return []

    # Views
    @staticmethod
    def vw_students_experiments_detailed():
        try:
            with _conn_cur() as cur:
                cur.execute('SELECT * FROM vw_students_experiments_detailed')
                return cur.fetchall()
        except Exception:
            log.exception("vw_students_experiments_detailed failed")
            return []

    @staticmethod
    def vw_students_experiments_for_teacher(teacher_id):
        try:
            with _conn_cur() as cur:
                cur.execute('SELECT * FROM vw_students_experiments_for_teacher WHERE teacher_id = %s',
                            (teacher_id,))
                return cur.fetchall()
        except Exception:
            log.exception("vw_students_experiments_for_teacher failed (teacher_id=%s)", teacher_id)
            return []

    # DB function wrapper + fallback
    @staticmethod
    def create_reaction_and_experiment_dbfn(
        teacher_id,
        element1_id,
        element2_id,
        product,
        conditions,
        experiment_result=None,
        safety_warning=None,
        equipment_ids=None
    ):
        try:
            with _conn_cur() as cur:
                cur.execute(
                    '''
                    SELECT * FROM create_reaction_and_experiment_fn(
                        %s, %s, %s, %s, %s, %s, %s, %s::int[]
                    )
                    ''',
                    (
                        teacher_id,
                        element1_id,
                        element2_id,
                        product,
                        conditions,
                        experiment_result,
                        safety_warning,
                        equipment_ids
                    )
                )
                row = cur.fetchone()
                return dict(row) if row else None
        except Exception:
            log.exception("create_reaction_and_experiment_dbfn failed")
            return None

    @staticmethod
    def create_reaction_and_experiment(
        teacher_id,
        element1_id,
        element2_id,
        product,
        conditions,
        experiment_result,
        safety_warning=None,
        equipment_ids=None
    ):
        # Try DB function first
        res = DatabaseManager.create_reaction_and_experiment_dbfn(
            teacher_id, element1_id, element2_id, product, conditions,
            experiment_result, safety_warning, equipment_ids
        )
        if res:
            return res
        # Fallback to Python transaction
        try:
            return DatabaseManager._create_reaction_and_experiment_python(
                teacher_id, element1_id, element2_id, product, conditions,
                experiment_result, safety_warning, equipment_ids
            )
        except Exception:
            log.exception("fallback _create_reaction_and_experiment_python failed")
            return None

    @staticmethod
    def get_students_experiments_detailed(teacher_id: int):
        return DatabaseManager.vw_students_experiments_for_teacher(teacher_id)

    @staticmethod
    def get_user_activity_summary():
        try:
            with _conn_cur() as cur:
                cur.execute('SELECT * FROM vw_user_activity_summary ORDER BY full_name')
                return cur.fetchall()
        except Exception:
            log.exception("get_user_activity_summary view failed; falling back to raw SELECT")
            try:
                with _conn_cur() as cur:
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
                    return cur.fetchall()
            except Exception:
                log.exception("get_user_activity_summary fallback failed")
                return []

    @staticmethod
    def get_reaction_by_symbols(sym1: str, sym2: str):
        try:
            with _conn_cur() as cur:
                cur.execute("""
                    SELECT r.reaction_id, r.product, r.conditions
                    FROM reaction r
                    JOIN elements e1 ON r.element1_id = e1.element_id
                    JOIN elements e2 ON r.element2_id = e2.element_id
                    WHERE (UPPER(e1.symbol) = UPPER(%s) AND UPPER(e2.symbol) = UPPER(%s))
                       OR (UPPER(e1.symbol) = UPPER(%s) AND UPPER(e2.symbol) = UPPER(%s))
                    LIMIT 1
                """, (sym1, sym2, sym2, sym1))
                row = cur.fetchone()
                return dict(row) if row else None
        except Exception:
            log.exception("get_reaction_by_symbols failed (%s, %s)", sym1, sym2)
            return None