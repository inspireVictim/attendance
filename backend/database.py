"""Управление подключением к SQLite и инициализация схемы."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR.parent / "data" / "attendance.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    # без detect_types — TIMESTAMP/DATE возвращаем как строки и парсим Pydantic'ом
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def db_cursor(commit: bool = False):
    conn = get_connection()
    try:
        cur = conn.cursor()
        yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_schema() -> None:
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn = get_connection()
    try:
        conn.executescript(sql)
        conn.commit()
    finally:
        conn.close()


def seed_data() -> None:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM departments")
        if cur.fetchone()[0] > 0:
            return

        # 1. Отделы (иерархия)
        cur.executemany(
            "INSERT INTO departments (code, name, parent_id) VALUES (?, ?, ?)",
            [
                ("hq",       "Управление",               None),
                ("hr",       "Отдел кадров",             1),
                ("it",       "ИТ-отдел",                 1),
                ("dev",      "Разработка",               3),
                ("ops",      "Эксплуатация",             3),
                ("acc",      "Бухгалтерия",              1),
            ],
        )

        # 2. Должности
        cur.executemany(
            "INSERT INTO positions (name, category) VALUES (?, ?)",
            [
                ("Генеральный директор",  "management"),
                ("Начальник отдела",      "management"),
                ("HR-менеджер",           "specialist"),
                ("Главный бухгалтер",     "management"),
                ("Бухгалтер",             "specialist"),
                ("Senior разработчик",    "specialist"),
                ("Middle разработчик",    "specialist"),
                ("Системный администратор","specialist"),
                ("DevOps-инженер",        "specialist"),
            ],
        )

        # 3. Графики работы
        cur.executemany(
            "INSERT INTO work_schedules (code, name, description) VALUES (?, ?, ?)",
            [
                ("standard", "Стандартный 5/2 (09:00–18:00)",
                 "Пн-Пт 09:00–18:00 с обедом 60 мин, выходные Сб-Вс"),
                ("shift",    "Сменный 2/2 (08:00–20:00)",
                 "Через два дня смены по 12 часов"),
                ("flex",     "Гибкий (40 ч/нед)",
                 "Гибкое начало 08:00–10:00, длительность 8 ч"),
            ],
        )

        # 4. Расписание дней для каждого графика
        # standard (id=1): Пн-Пт 09:00-18:00, обед 60; Сб-Вс выходной
        cur.executemany(
            """INSERT INTO schedule_days
               (schedule_id, weekday, start_time, end_time, lunch_break_min, is_workday)
               VALUES (?, ?, ?, ?, ?, ?)""",
            [
                (1, 1, "09:00", "18:00", 60, 1),
                (1, 2, "09:00", "18:00", 60, 1),
                (1, 3, "09:00", "18:00", 60, 1),
                (1, 4, "09:00", "18:00", 60, 1),
                (1, 5, "09:00", "18:00", 60, 1),
                (1, 6, "00:00", "00:01",  0, 0),
                (1, 7, "00:00", "00:01",  0, 0),

                # flex (id=3): Пн-Пт 10:00-19:00, обед 60
                (3, 1, "10:00", "19:00", 60, 1),
                (3, 2, "10:00", "19:00", 60, 1),
                (3, 3, "10:00", "19:00", 60, 1),
                (3, 4, "10:00", "19:00", 60, 1),
                (3, 5, "10:00", "19:00", 60, 1),
                (3, 6, "00:00", "00:01",  0, 0),
                (3, 7, "00:00", "00:01",  0, 0),

                # shift (id=2): Пн, Ср, Пт смена 08-20
                (2, 1, "08:00", "20:00",  60, 1),
                (2, 2, "00:00", "00:01",  0, 0),
                (2, 3, "08:00", "20:00",  60, 1),
                (2, 4, "00:00", "00:01",  0, 0),
                (2, 5, "08:00", "20:00",  60, 1),
                (2, 6, "00:00", "00:01",  0, 0),
                (2, 7, "00:00", "00:01",  0, 0),
            ],
        )

        # 5. Типы отсутствий
        cur.executemany(
            "INSERT INTO absence_types (code, name, short_code, is_paid, color) VALUES (?, ?, ?, ?, ?)",
            [
                ("vacation",    "Отпуск ежегодный",   "О",  1, "#10B981"),
                ("sick",        "Больничный",         "Б",  1, "#EF4444"),
                ("business",    "Командировка",       "К",  1, "#3B82F6"),
                ("unpaid",      "Отпуск за свой счёт","НО", 0, "#A855F7"),
                ("absence",     "Прогул",             "ПР", 0, "#7F1D1D"),
                ("dayoff",      "Отгул",              "ОТ", 0, "#F59E0B"),
            ],
        )

        # 6. Праздничные дни КР 2026
        cur.executemany(
            "INSERT INTO holidays (date, name) VALUES (?, ?)",
            [
                ("2026-01-01", "Новый год"),
                ("2026-01-07", "Рождество"),
                ("2026-02-23", "День защитника Отечества"),
                ("2026-03-08", "Международный женский день"),
                ("2026-05-01", "Праздник труда"),
                ("2026-05-05", "День Конституции"),
                ("2026-05-09", "День Победы"),
                ("2026-08-31", "День независимости"),
            ],
        )

        # 7. Сотрудники
        cur.executemany(
            """INSERT INTO employees
               (personnel_number, full_name, department_id, position_id, schedule_id,
                hire_date, phone, email)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                ("E-001", "Иванов Сергей Викторович",   1, 1, 1, "2020-01-15",
                 "+996700110001", "ivanov@company.kg"),
                ("E-002", "Петрова Анна Сергеевна",     2, 3, 1, "2021-03-01",
                 "+996700110002", "petrova@company.kg"),
                ("E-003", "Кузнецов Дмитрий Олегович",  4, 6, 3, "2022-04-10",
                 "+996700110003", "kuznetsov@company.kg"),
                ("E-004", "Беков Тимур Эркинович",      4, 7, 3, "2023-05-20",
                 "+996700110004", "bekov@company.kg"),
                ("E-005", "Турсунов Алмаз Жакыпович",   5, 8, 2, "2022-08-01",
                 "+996700110005", "tursunov@company.kg"),
                ("E-006", "Эркинов Айбек Каныбекович",  5, 9, 2, "2024-02-15",
                 "+996700110006", "erkinov@company.kg"),
                ("E-007", "Алиева Жаныл Касымовна",     6, 4, 1, "2019-09-10",
                 "+996700110007", "alieva@company.kg"),
                ("E-008", "Кадырова Айгерим Маратовна", 6, 5, 1, "2023-07-15",
                 "+996700110008", "kadyrova@company.kg"),
                ("E-009", "Жапаров Нурлан Талантович",  3, 2, 1, "2021-11-01",
                 "+996700110009", "japarov@company.kg"),
                ("E-010", "Орлова Мария Викторовна",    2, 3, 1, "2024-01-20",
                 "+996700110010", "orlova@company.kg"),
            ],
        )

        # 8. Отметки за последние дни (включая сегодня — 2026-06-03)
        # формат: (employee_id, date, in, out)
        attend = [
            # Понедельник 01.06
            (1, "2026-06-01", "2026-06-01 08:55", "2026-06-01 18:05"),
            (2, "2026-06-01", "2026-06-01 09:08", "2026-06-01 18:00"),
            (3, "2026-06-01", "2026-06-01 10:02", "2026-06-01 19:15"),
            (4, "2026-06-01", "2026-06-01 10:18", "2026-06-01 19:30"),
            (7, "2026-06-01", "2026-06-01 09:00", "2026-06-01 18:00"),
            (8, "2026-06-01", "2026-06-01 09:15", "2026-06-01 17:55"),
            (9, "2026-06-01", "2026-06-01 08:50", "2026-06-01 18:10"),
            (10,"2026-06-01", "2026-06-01 09:25", "2026-06-01 18:00"),
            # Вторник 02.06
            (1, "2026-06-02", "2026-06-02 08:58", "2026-06-02 18:00"),
            (2, "2026-06-02", "2026-06-02 09:00", "2026-06-02 18:00"),
            (3, "2026-06-02", "2026-06-02 10:00", "2026-06-02 19:00"),
            (4, "2026-06-02", "2026-06-02 09:55", "2026-06-02 18:45"),
            (7, "2026-06-02", "2026-06-02 09:02", "2026-06-02 18:00"),
            (8, "2026-06-02", "2026-06-02 09:00", "2026-06-02 18:00"),
            (9, "2026-06-02", "2026-06-02 09:00", "2026-06-02 18:00"),
            (10,"2026-06-02", "2026-06-02 09:00", "2026-06-02 18:00"),
            # Среда 03.06 — сегодня; кто-то ещё на работе (нет check_out)
            (1, "2026-06-03", "2026-06-03 08:54", None),
            (2, "2026-06-03", "2026-06-03 09:05", None),
            (3, "2026-06-03", "2026-06-03 10:12", None),
            (5, "2026-06-03", "2026-06-03 08:00", None),   # сменный график — рабочий день
            (7, "2026-06-03", "2026-06-03 09:00", None),
            (9, "2026-06-03", "2026-06-03 09:01", None),
            (10,"2026-06-03", "2026-06-03 09:08", None),
        ]
        for emp_id, wd, ci, co in attend:
            # Считаем дельты в Python по тому же алгоритму, что и в бэке
            late, early, worked, ot = _compute_metrics(cur, emp_id, wd, ci, co)
            cur.execute(
                """INSERT INTO attendance_records
                   (employee_id, work_date, check_in, check_out,
                    late_minutes, early_leave_min, worked_minutes, overtime_min)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (emp_id, wd, ci, co, late, early, worked, ot),
            )

        # 9. Отсутствия
        cur.executemany(
            """INSERT INTO absences
               (employee_id, absence_type_id, date_from, date_to, document_number, note)
               VALUES (?, ?, ?, ?, ?, ?)""",
            [
                # Беков — командировка
                (4, 3, "2026-06-03", "2026-06-05", "ПР-145", "Командировка в Алматы"),
                # Турсунов в отпуске? Нет, он на работе.
                # Эркинов — больничный
                (6, 2, "2026-06-02", "2026-06-04", "Л-2204", "Больничный лист, ОРВИ"),
                # Кадырова — отпуск с июня
                (8, 1, "2026-06-15", "2026-06-28", "ПР-160", "Очередной отпуск"),
            ],
        )

        conn.commit()
    finally:
        conn.close()


def _compute_metrics(cur, employee_id: int, work_date: str,
                     check_in: str | None, check_out: str | None):
    """Вычисление опозданий, переработок и отработанных минут для seed."""
    import datetime as dt
    cur.execute("SELECT schedule_id FROM employees WHERE id = ?", (employee_id,))
    sched_id = cur.fetchone()["schedule_id"]
    wd = dt.date.fromisoformat(work_date).isoweekday()
    cur.execute(
        "SELECT start_time, end_time, lunch_break_min, is_workday FROM schedule_days WHERE schedule_id = ? AND weekday = ?",
        (sched_id, wd),
    )
    row = cur.fetchone()
    if row is None or row["is_workday"] == 0:
        # выходной — нет нормативов
        return (0, 0, _minutes_between(check_in, check_out), 0)

    norm_start = dt.datetime.fromisoformat(f"{work_date} {row['start_time']}")
    norm_end   = dt.datetime.fromisoformat(f"{work_date} {row['end_time']}")
    lunch      = row["lunch_break_min"]

    late = early = worked = ot = 0
    if check_in:
        ci = dt.datetime.fromisoformat(check_in)
        if ci > norm_start:
            late = int((ci - norm_start).total_seconds() // 60)
    if check_out and check_in:
        co = dt.datetime.fromisoformat(check_out)
        # отработано = max(co, norm_end) - max(ci, norm_start) - lunch
        eff_start = max(dt.datetime.fromisoformat(check_in), norm_start)
        eff_end   = min(co, norm_end)
        if eff_end > eff_start:
            worked = int((eff_end - eff_start).total_seconds() // 60) - lunch
            if worked < 0:
                worked = 0
        if co < norm_end:
            early = int((norm_end - co).total_seconds() // 60)
        if co > norm_end:
            ot = int((co - norm_end).total_seconds() // 60)
    return (late, early, worked, ot)


def _minutes_between(a: str | None, b: str | None) -> int:
    if not a or not b:
        return 0
    import datetime as dt
    return max(0, int((dt.datetime.fromisoformat(b) - dt.datetime.fromisoformat(a)).total_seconds() // 60))


if __name__ == "__main__":
    init_schema()
    seed_data()
    print(f"База данных создана: {DB_PATH}")
