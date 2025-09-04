# SIMLAB – Виртуелна Хемиска Лабораторија (Flask + PostgreSQL)

Образовна веб-апликација за симулации на хемиски реакции и следење студентска активност.

## Содржина

1. [Преглед](#1-преглед)
2. [Технологии / Стек](#2-технологии--стек)
3. [Структура на проект](#3-структура-на-проект)
4. [Улоги и дозволи](#4-улоги-и-дозволи)
5. [База на податоци (шема)](#5-база-на-податоци-шема)
6. [Логирање (logging)](#6-логирање-logging)
7. [Рути и функционалности](#7-рути-и-функционалности)
8. [Data-access слој (DatabaseManager)](#8-data-access-слој-databasemanager)
9. [Конфигурација и пуштање](#9-конфигурација-и-пуштање)
10. [Сигурност и приватност](#10-сигурност-и-приватност)
11. [Перформанси и интегритет](#11-перформанси-и-интегритет)
12. [Познати ограничувања](#12-познати-ограничувања)
13. [Тест сценарија за демонстрација](#13-тест-сценарија-за-демонстрација)
14. [Troubleshooting](#14-troubleshooting)
15. [Идни подобрувања](#15-идни-подобрувања)
- [Апендикс A — cURL примери](#апендикс-a--curl-примери)
- [Апендикс B — .env пример](#апендикс-b--env-пример)

## 1) Преглед

SIMLAB е апликација за:
- управување со елементи, лаб. опрема, реакции и експерименти;
- симулација на реакции и логирање на учество на студенти;
- дашборд за наставници со статистики и повеќе извештаи (basic + advanced SQL).

**Слоеви:**
- Flask рути и Jinja2 шаблони
- Data access: `utils/database_manager.py` (SQL, транскации, извештаи)
- Auth: `utils/auth_manager.py` (bcrypt)

**Напомена за тригери:** Во проектот не се користат DB тригери; временските полиња се решени со DEFAULT now() и timestamp од апликацијата.

## 2) Технологии / Стек

- **Backend:** Python 3.x, Flask
- **База:** PostgreSQL (psycopg2, RealDictCursor)
- **View:** Jinja2 templates
- **Сесии/Автентикација:** Flask session + bcrypt

- **Логирање:** Python logging со log.exception(...)

## 3) Структура на проект



## 4) Улоги и дозволи

- **teacher:** CRUD на елементи/опрема/реакции, креирање експерименти, сите извештаи, „моите студенти".
- **student:** преглед елементи/опрема, симулација и зачувување учество, лични статистики и „моите експерименти".

Заштита со декоратор: `@require_login(role=None|'teacher')`.

## 5) База на податоци (шема)

### Главни табели (извадок):

- `"User"(user_id, user_name, user_surname, email, password, role)`
- `student(student_id FK->User, teacher_id FK->User)`
- `teacher(teacher_id FK->User)`
- `elements(..., teacher_id FK->User)`
- `labequipment(..., teacher_id FK->User)`
- `reaction(reaction_id, teacher_id FK, element1_id FK->elements, element2_id FK->elements, product, conditions)`
- `experiment(experiment_id, teacher_id FK, reaction_id FK, result, safety_warning, time_stamp TIMESTAMP DEFAULT now())`
- `experimentlabequipment(experiment_id FK, equipment_id FK)` (N:M)
- `userparticipatesinexperiment(user_id FK, experiment_id FK, participation_timestamp TIMESTAMPTZ DEFAULT now())`
- `userviewselement(user_id FK, element_id FK)`
- `userviewslabequipment(user_id FK, equipment_id FK)`

### Препорачани UNIQUE ограничувања (идемпотентност):

```sql
ALTER TABLE userviewselement
  ADD CONSTRAINT uq_uve UNIQUE (user_id, element_id);

ALTER TABLE userviewslabequipment
  ADD CONSTRAINT uq_uvl UNIQUE (user_id, equipment_id);

ALTER TABLE userparticipatesinexperiment
  ADD CONSTRAINT uq_upe UNIQUE (user_id, experiment_id);
```
## 6) Логирање (logging)

Во `utils/database_manager.py`:
```pythonimport logging```
log = logging.getLogger(name)


## 7) Рути и функционалности

### Аутентикација
- `GET /login` – форма за логирање
- `POST /login` – проверка (email + bcrypt), сетира session
- `GET /register` – форма (студент бира ментор/teacher)
- `POST /register` – креира "User" (+ student или teacher)
- `GET /logout` – чисти сесија

### Дашборд
- `GET /dashboard` –
 - teacher: број студенти/реакции/експерименти/активности денес
 - student: сопствени статистики
- `GET /api/dashboard-stats` – JSON за фронтенд видџети
- `GET /api/debug-dashboard` – помошен JSON (session + stats)

### Елементи
- `GET /elements` – листа
- `GET /elements/<id>` – детали (логира view во userviewselement)
- `GET|POST /elements/add` – teacher
- `GET|POST /elements/<id>/edit` – teacher

### Лаб. опрема
- `GET /equipment`, `GET /equipment/<id>` (логира view)
- `GET|POST /equipment/add`, `GET|POST /equipment/<id>/edit` – teacher

### Реакции и експерименти
- `GET /reactions` – листа со збогатени полиња (симболи/имиња на елементи)
- `GET|POST /reactions/add` – teacher: една транскација → reaction + experiment (+ N:M experimentlabequipment)
- `GET|POST /reactions/<id>/edit` – teacher
- `POST /reactions/<id>/delete` – teacher

### Виртуелна лабораторија (API)
- `GET /laboratory` – teacher/student views
- `POST /api/simulate-reaction`
 - Body: `{"element1":"H","element2":"O"}`
 - Response: `{success, product, conditions, reaction_id, experiment_id, elements}`
- `POST /api/check-reaction` – верификација без experiment_id
- `POST /save-experiment` –
 - ако нема експеримент за реакцијата и корисник е teacher → креира experiment
 - секогаш логира учество во userparticipatesinexperiment за тековниот корисник

### „Мои експерименти"
- `GET /my-experiments` –
 - student: експерименти во кои учествувал
 - teacher: експерименти поврзани со него (преку join со UPE)

### Извештаи – Мену
- `GET /reports` – избор на извештаи (teacher)

### Basic извештаи (templates):
- `GET /reports/teacher_statistics`
- `GET /reports/inactive_students`
- `GET /reports/element_views`
- `GET /reports/detailed_experiments`
- `GET /reports/low_activity_students`
- `GET /reports/student_experiments`
- `GET /reports/user_activity`

### Advanced SQL (generic renderer):
- `GET /reports/adv/student_experiment_counts`
- `GET /reports/adv/equipment_usage`
- `GET /reports/adv/students_experiments_detailed`
- `GET /reports/adv/experiment_participants?experiment_id=<id>`
- `GET /reports/adv/avg_equipment_per_experiment`
- `GET /reports/adv/most_used_elements`
- `GET /reports/adv/most_performed_experiments`
- `GET /reports/adv/never_participated_students`
- `GET /reports/adv/students_below_threshold?max=3`
- `GET /reports/adv/student_views`

## 8) Data-access слој (DatabaseManager)

- Единствен влез за SQL операции (CRUD, извештаи).
- RealDictCursor → редовите се dict (олеснето рендерирање во Jinja/JSON).
- Метод `create_reaction_and_experiment(...)` користи една транскација за конзистентност.
- Track функции (userviewselement, userviewslabequipment, userparticipatesinexperiment) се идемпотентни со горните UNIQUE ограничувања.

## 9) Конфигурација и пуштање

### 9.1 Пререквизити
- Python 3.10+
- PostgreSQL 13+
- Зависности:
bash
pip install -r requirements.txt

### 9.2 Конфигурација
Во кодот има хардкодирани креденцијали во `DatabaseManager.get_connection()`. **Препорака:** користи `.env` + `os.getenv` (пример во Апендикс B). **Никогаш не комитирај реални лозинки.**

### 9.3 Пуштање (локално)
flask run
Отвори: http://127.0.0.1:5000/

## 10) Сигурност и приватност

- **Лозинки:** bcrypt (во AuthManager)
- **Сесии:** Flask secret_key (чувај во ENV)
- **CSRF:** не е активен (за форми со POST препорачливо Flask-WTF)
- **RBAC:** проверка на рути со декоратор `@require_login(role=...)`

## 11) Перформанси и интегритет

- Индекси на сите FK и често користени JOIN колони.
- UNIQUE (user_id, experiment_id) на userparticipatesinexperiment + ON CONFLICT DO NOTHING во insertите.
- Транскации при креирање reaction + experiment (ACID).

## 12) Познати ограничувања

- Хардкодирани DB креденцијали (премести во ENV).
- Нема CSRF за форми.
- Нема миграции (Alembic) — DDL се извршува рачно.
- Нема unit тестови (може да се додадат за DatabaseManager и API).

## 13) Тест сценарија за демонстрација

1. **Регистрација/Логирање** – teacher + student.
2. **Елементи** – додавање (teacher), преглед (student) → проверка на userviewselement.
3. **Опрема** – додавање/преглед → проверка userviewslabequipment.
4. **Реакција+Експеримент** – креирање во една транскација; избор опрема (N:M).
5. **Симулација** `/api/simulate-reaction` + зачувување `/save-experiment` (како student) → userparticipatesinexperiment.
6. **Извештаи** – detailed_experiments, user_activity, teacher_statistics.
7. **Дашборд** – броеви се менуваат после активности.

## 14) Troubleshooting

**Празен „Детален преглед"**
- Проверете има ли редови во userparticipatesinexperiment. Дали `/save-experiment` вратил success=true?
- Препорака: participation_timestamp DEFAULT now() + UNIQUE на (user_id, experiment_id).

**/api/simulate-reaction → success=false**
- Нема дефинирана реакција за симболите → креирај преку `/reactions/add`.

**OperationalError: connection refused**
- Проверете DB host/port/credentials; дали PostgreSQL слуша и шемата постои.

## 15) Идни подобрувања

- ENV конфигурација + Alembic миграции.
- CSRF и rate-limiting за API.
- Role-based UI контроли (disable/hide actions).
- CSV/Excel export на извештаи.
- Unit тестови (pytest) за DatabaseManager и рути.

## Апендикс A — cURL примери

### Simulate reaction
```bash
curl -X POST http://127.0.0.1:5000/api/simulate-reaction \
 -H "Content-Type: application/json" \
 -d '{"element1":"H","element2":"O"}' \
 -b cookiejar.txt -c cookiejar.txt
Апендикс B — .env пример
env# Flask
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=change-me-please

# PostgreSQL
DB_HOST=localhost
DB_PORT=9999
DB_NAME=db_202425z_va_prj_simlab25
DB_USER=db_202425z_va_prj_simlab25_owner
DB_PASS=replace-with-real-password
Пример за користење ENV во DatabaseManager.get_connection():
pythonimport os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', '5432')),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASS'),
        cursor_factory=RealDictCursor
    )
