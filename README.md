# SIMLAB – Виртуелна Хемиска Лабораторија

Образовна веб-апликација изградена со **Flask + PostgreSQL** за симулации на хемиски реакции, управување со елементи, лабораториска опрема и активности на студенти.

---

## Главни функционалности
- Улоги: **Teacher** и **Student** со различни дозволи  
- CRUD за **Elements**, **Lab Equipment**, **Reactions**  
- Автоматско креирање на **Experiments** при додавање реакција  
- Dashboard со статистики и извештаи (basic + advanced SQL)  
- Bcrypt лозинки, Flask sessions, индекси и constraints за интегритет  

---

## Технологии
- Backend: **Python 3.10+, Flask**  
- Database: **PostgreSQL** (`psycopg2`, `RealDictCursor`)  
- Templates: **Jinja2**  
- Auth: **bcrypt**  
- Logging: Python `logging`  

---

## Setup & Run

```bash
git clone https://github.com/MarijaIsailovska/SIMLAB.git
cd SIMLAB
python -m venv venv
source venv/bin/activate   # или venv\Scripts\activate на Windows
pip install -r requirements.txt
```

## Database Highlights
- CHECK ограничувања за валидни атомски броеви, маса и физички својства
- Индекси за брзо пребарување и сортирање (реакции, експерименти, учества)
- UNIQUE constraints за идемпотентност при логирање на активности
- DEFAULT timestamps за автоматско логирање на учества и експерименти

## Author
Изработено од Марија Исаиловска
Факултет за информатички науки и компјутерско инженерство – ФИНКИ
Предмет: Бази на податоци
