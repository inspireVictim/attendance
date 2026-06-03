"""Формирование табеля рабочего времени за месяц."""
from __future__ import annotations

import calendar
import datetime as dt
from typing import Optional

from fastapi import APIRouter

from ..database import db_cursor
from ..schemas import TimesheetCellOut, TimesheetOut, TimesheetRowOut

router = APIRouter(prefix="/api/timesheet", tags=["timesheet"])


@router.get("", response_model=TimesheetOut)
def get_timesheet(year: int, month: int, department_id: Optional[int] = None):
    """Сборка матричного табеля сотрудник × дни месяца.

    Каждая ячейка получает один из кодов:
        П  — присутствовал
        О, Б, К, НО, ПР, ОТ — соответствующий тип отсутствия
        В  — выходной (по графику)
        Х  — праздник
        -- — нет данных
    """
    if not (1 <= month <= 12):
        from fastapi import HTTPException
        raise HTTPException(400, "Некорректный месяц")
    days_in_month = calendar.monthrange(year, month)[1]
    first_day = dt.date(year, month, 1)
    last_day  = dt.date(year, month, days_in_month)

    with db_cursor() as cur:
        # 1) Список сотрудников
        emp_sql = """
            SELECT e.id, e.personnel_number, e.full_name,
                   e.schedule_id, d.name AS department_name
              FROM employees e
              JOIN departments d ON d.id = e.department_id
             WHERE e.is_active = 1
        """
        params: list = []
        if department_id:
            emp_sql += " AND e.department_id = ?"
            params.append(department_id)
        emp_sql += " ORDER BY d.name, e.full_name"
        cur.execute(emp_sql, params)
        employees = [dict(r) for r in cur.fetchall()]

        # 2) Расписания (день недели → is_workday)
        cur.execute("SELECT schedule_id, weekday, is_workday FROM schedule_days")
        schedule_map = {}
        for r in cur.fetchall():
            schedule_map[(r["schedule_id"], r["weekday"])] = r["is_workday"]

        # 3) Праздники
        cur.execute("SELECT date FROM holidays WHERE date BETWEEN ? AND ?",
                    (first_day, last_day))
        holidays = {dt.date.fromisoformat(r["date"]) for r in cur.fetchall()}

        # 4) Отметки
        cur.execute(
            """SELECT employee_id, work_date, worked_minutes, late_minutes, overtime_min
                 FROM attendance_records
                WHERE work_date BETWEEN ? AND ?""",
            (first_day, last_day),
        )
        att_map = {}
        for r in cur.fetchall():
            att_map[(r["employee_id"], dt.date.fromisoformat(r["work_date"]))] = dict(r)

        # 5) Отсутствия
        cur.execute(
            """SELECT ab.employee_id, ab.date_from, ab.date_to,
                      at.short_code, at.color
                 FROM absences ab
                 JOIN absence_types at ON at.id = ab.absence_type_id
                WHERE ab.date_from <= ? AND ab.date_to >= ?""",
            (last_day, first_day),
        )
        absence_intervals = []
        for r in cur.fetchall():
            ab = dict(r)
            ab["date_from"] = dt.date.fromisoformat(ab["date_from"])
            ab["date_to"]   = dt.date.fromisoformat(ab["date_to"])
            absence_intervals.append(ab)

    rows = []
    for emp in employees:
        cells = []
        total_worked = 0
        total_late = 0
        total_ot = 0
        absent_days = 0
        for d in range(1, days_in_month + 1):
            day_date = dt.date(year, month, d)
            weekday = day_date.isoweekday()

            # 5.1 Праздник?
            if day_date in holidays:
                cells.append(TimesheetCellOut(day=d, code="Х", color="#94A3B8",
                                              worked_minutes=0, late_minutes=0,
                                              is_workday=False))
                continue

            # 5.2 Выходной по графику?
            is_workday = bool(schedule_map.get((emp["schedule_id"], weekday), 1))
            if not is_workday:
                cells.append(TimesheetCellOut(day=d, code="В", color="#CBD5E1",
                                              worked_minutes=0, late_minutes=0,
                                              is_workday=False))
                continue

            # 5.3 Отсутствие?
            absent_info = None
            for ab in absence_intervals:
                if ab["employee_id"] == emp["id"] and ab["date_from"] <= day_date <= ab["date_to"]:
                    absent_info = ab
                    break
            if absent_info:
                cells.append(TimesheetCellOut(
                    day=d, code=absent_info["short_code"], color=absent_info["color"],
                    worked_minutes=0, late_minutes=0, is_workday=True
                ))
                absent_days += 1
                continue

            # 5.4 Отметка?
            att = att_map.get((emp["id"], day_date))
            if att:
                cells.append(TimesheetCellOut(
                    day=d, code="П", color="#10B981",
                    worked_minutes=att["worked_minutes"],
                    late_minutes=att["late_minutes"],
                    is_workday=True,
                ))
                total_worked += att["worked_minutes"]
                total_late   += att["late_minutes"]
                total_ot     += att["overtime_min"]
            else:
                # Рабочий день без отметки и без отсутствия — "—"
                # для прошлых дней — это потенциальный прогул
                if day_date < dt.date.today():
                    cells.append(TimesheetCellOut(day=d, code="—", color="#FCA5A5",
                                                  worked_minutes=0, late_minutes=0,
                                                  is_workday=True))
                else:
                    cells.append(TimesheetCellOut(day=d, code="—", color="#E2E8F0",
                                                  worked_minutes=0, late_minutes=0,
                                                  is_workday=True))

        rows.append(TimesheetRowOut(
            employee_id=emp["id"],
            personnel_number=emp["personnel_number"],
            full_name=emp["full_name"],
            department_name=emp["department_name"],
            days=cells,
            total_worked_minutes=total_worked,
            total_late_minutes=total_late,
            total_overtime_min=total_ot,
            total_absent_days=absent_days,
        ))

    return TimesheetOut(year=year, month=month, days_in_month=days_in_month, rows=rows)
