# Учёт посещаемости сотрудников (ВКР)

## Стек
- SQLite 3.35+
- Python 3.10+ / FastAPI / Pydantic 2
- HTML5 / CSS3 / Vanilla JS (Fetch API)

## Запуск
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python -m backend.init_db
uvicorn backend.main:app --port 8005 --reload
```
→ http://localhost:8005/

## Сборка ПЗ
```bash
python scripts/generate_pz.py
```
Результат: `ПЗ_БД_Учёт_Посещаемости_Сотрудников.docx`
