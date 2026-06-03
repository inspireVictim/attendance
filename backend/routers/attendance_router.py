"""Ключевые бизнес-алгоритмы фиксации прихода/ухода сотрудника.

Алгоритм check-in:
    1. Загрузить сотрудника и его рабочий график на текущий день недели.
    2. Если запись за дату уже есть с check_in — отказ (повторная отметка).
    3. Рассчитать опоздание: фактическое время минус нормативное начало.
    4. Создать/обновить attendance_records со временем check_in и опозданием.
    5. Вернуть запись клиенту.

Алгоритм check-out:
    1. Загрузить активную запись (check_in != NULL, check_out = NULL).
    2. Если check_in не было — отказ.
    3. Рассчитать: фактически отработанные минуты, ранний уход, переработку.
    4. Обновить запись.
"""
from __future__ import annotations

import datetime as dt
from typing import Optional

from fastapi import APIRouter, HTTPException

from ..database import db_cursor
from ..schemas import AttendanceRecordOut, CheckInIn, CheckOutIn, CheckResult

router = APIRouter(prefix="/api/attendance", tags=["attendance"])


_LIST_SQL = """
SELECT
    a.id, a.employee_id,
    e.full_name        AS employee_name,
    e.personnel_number,
    d.name             AS department_name,
    a.work_date, a.check_in, a.check_out,
    a.late_minutes, a.early_leave_min,
    a.worked_minutes, a.overtime_min, a.note
FROM attendance_records a
JOIN employees   e ON e.id = a.employee_id
JOIN departments d ON d.id = e.department_id
"""


def _status_of(row) -> str:
    if row["check_in"] and row["check_out"]:
        return "completed"
    if row["check_in"]:
        return "on_duty"
    return "absent"


def _augment(row) -> dict:
    d = dict(row)
    d["status"] = _status_of(d)
    return d


def _load_schedule_day(cur, employee_id: int, work_date: dt.date):
    cur.execute(
        """SELECT sd.start_time, sd.end_time, sd.lunch_break_min, sd.is_workday
             FROM employees e
             JOIN schedule_days sd ON sd.schedule_id = e.schedule_id
            WHERE e.id = ? AND sd.weekday = ?""",
        (employee_id, work_date.isoweekday()),
    )
    return cur.fetchone()


def _is_holiday(cur, work_date: dt.date) -> bool:
    cur.execute("SELECT 1 FROM holidays WHERE date = ?", (work_date,))
    return cur.fetchone() is not None


def _calc_late(actual: dt.datetime, work_date: dt.date,
               start_str: str) -> int:
    norm_start = dt.datetime.combine(
        work_date, dt.time.fromisoformat(start_str)
    )
    if actual > norm_start:
        return int((actual - norm_start).total_seconds() // 60)
    return 0


def _calc_close_metrics(check_in: dt.datetime, check_out: dt.datetime,
                        work_date: dt.date,
                        start_str: str, end_str: str, lunch_min: int):
    norm_start = dt.datetime.combine(work_date, dt.time.fromisoformat(start_str))
    norm_end   = dt.datetime.combine(work_date, dt.time.fromisoformat(end_str))

    eff_start = max(check_in, norm_start)
    eff_end   = min(check_out, norm_end)
    worked = 0
    if eff_end > eff_start:
        worked = int((eff_end - eff_start).total_seconds() // 60) - lunch_min
        if worked < 0:
            worked = 0

    early = max(0, int((norm_end - check_out).total_seconds() // 60)) if check_out < norm_end else 0
    ot    = max(0, int((check_out - norm_end).total_seconds() // 60)) if check_out > norm_end else 0
    return worked, early, ot


# ============================================================
# КЛЮЧЕВОЙ АЛГОРИТМ: фиксация прихода
# ============================================================

@router.post("/check-in", response_model=CheckResult, status_code=201)
def check_in(payload: CheckInIn):
    actual = payload.timestamp or dt.datetime.now().replace(microsecond=0)
    work_date = actual.date()

    with db_cursor(commit=True) as cur:
        # 1. Сотрудник существует?
        cur.execute("SELECT id, full_name FROM employees WHERE id = ? AND is_active = 1",
                    (payload.employee_id,))
        emp = cur.fetchone()
        if emp is None:
            raise HTTPException(404, "Сотрудник не найден или деактивирован")

        # 2. Не отмечался ли уже сегодня?
        cur.execute(
            "SELECT id, check_in FROM attendance_records WHERE employee_id = ? AND work_date = ?",
            (payload.employee_id, work_date),
        )
        existing = cur.fetchone()
        if existing and existing["check_in"] is not None:
            raise HTTPException(400, "Приход уже зафиксирован сегодня")

        # 3. График на этот день недели
        sched = _load_schedule_day(cur, payload.employee_id, work_date)
        if sched is None or sched["is_workday"] == 0 or _is_holiday(cur, work_date):
            late = 0
        else:
            late = _calc_late(actual, work_date, sched["start_time"])

        # 4. Запись прихода
        if existing:
            cur.execute(
                "UPDATE attendance_records SET check_in = ?, late_minutes = ?, note = COALESCE(?, note) WHERE id = ?",
                (actual.isoformat(sep=" "), late, payload.note, existing["id"]),
            )
            rec_id = existing["id"]
        else:
            cur.execute(
                """INSERT INTO attendance_records
                   (employee_id, work_date, check_in, late_minutes, note)
                   VALUES (?, ?, ?, ?, ?)""",
                (payload.employee_id, work_date, actual.isoformat(sep=" "), late, payload.note),
            )
            rec_id = cur.lastrowid

        cur.execute(_LIST_SQL + " WHERE a.id = ?", (rec_id,))
        record = _augment(cur.fetchone())
        message = f"Приход зафиксирован: {actual.strftime('%H:%M')}"
        if late > 0:
            message += f" (опоздание {late} мин)"
        return CheckResult(record=record, message=message)


# ============================================================
# КЛЮЧЕВОЙ АЛГОРИТМ: фиксация ухода
# ============================================================

@router.post("/check-out", response_model=CheckResult)
def check_out(payload: CheckOutIn):
    actual = payload.timestamp or dt.datetime.now().replace(microsecond=0)
    work_date = actual.date()

    with db_cursor(commit=True) as cur:
        cur.execute("SELECT id FROM employees WHERE id = ? AND is_active = 1",
                    (payload.employee_id,))
        if cur.fetchone() is None:
            raise HTTPException(404, "Сотрудник не найден или деактивирован")

        cur.execute(
            "SELECT * FROM attendance_records WHERE employee_id = ? AND work_date = ?",
            (payload.employee_id, work_date),
        )
        rec = cur.fetchone()
        if rec is None or rec["check_in"] is None:
            raise HTTPException(400, "Сначала нужно зафиксировать приход")
        if rec["check_out"] is not None:
            raise HTTPException(400, "Уход уже зафиксирован сегодня")

        check_in_dt = dt.datetime.fromisoformat(rec["check_in"])
        if actual < check_in_dt:
            raise HTTPException(400, "Время ухода не может быть раньше прихода")

        sched = _load_schedule_day(cur, payload.employee_id, work_date)
        if sched is None or sched["is_workday"] == 0 or _is_holiday(cur, work_date):
            worked = max(0, int((actual - check_in_dt).total_seconds() // 60))
            early = ot = 0
        else:
            worked, early, ot = _calc_close_metrics(
                check_in_dt, actual, work_date,
                sched["start_time"], sched["end_time"], sched["lunch_break_min"],
            )

        cur.execute(
            """UPDATE attendance_records
                  SET check_out = ?, worked_minutes = ?,
                      early_leave_min = ?, overtime_min = ?,
                      note = COALESCE(?, note)
                WHERE id = ?""",
            (actual.isoformat(sep=" "), worked, early, ot, payload.note, rec["id"]),
        )

        cur.execute(_LIST_SQL + " WHERE a.id = ?", (rec["id"],))
        record = _augment(cur.fetchone())

        hours = worked // 60
        mins  = worked % 60
        msg = f"Уход зафиксирован: {actual.strftime('%H:%M')}. Отработано {hours} ч {mins:02d} мин"
        if ot > 0:
            msg += f", переработка {ot} мин"
        if early > 0:
            msg += f", ранний уход {early} мин"
        return CheckResult(record=record, message=msg)


@router.get("", response_model=list[AttendanceRecordOut])
def list_attendance(date: Optional[dt.date] = None,
                    employee_id: Optional[int] = None,
                    department_id: Optional[int] = None):
    sql = _LIST_SQL + " WHERE 1=1"
    params: list = []
    if date:
        sql += " AND a.work_date = ?"; params.append(date)
    if employee_id:
        sql += " AND a.employee_id = ?"; params.append(employee_id)
    if department_id:
        sql += " AND e.department_id = ?"; params.append(department_id)
    sql += " ORDER BY a.work_date DESC, a.check_in DESC"
    with db_cursor() as cur:
        cur.execute(sql, params)
        return [_augment(r) for r in cur.fetchall()]
