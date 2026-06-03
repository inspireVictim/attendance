"""Сотрудники."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException

from ..database import db_cursor
from ..schemas import EmployeeOut

router = APIRouter(prefix="/api/employees", tags=["employees"])


_LIST_SQL = """
SELECT
    e.id, e.personnel_number, e.full_name,
    e.department_id, d.name AS department_name,
    e.position_id,   p.name AS position_name,
    e.schedule_id,   s.name AS schedule_name,
    e.hire_date, e.phone, e.email, e.is_active
FROM employees e
JOIN departments    d ON d.id = e.department_id
JOIN positions      p ON p.id = e.position_id
JOIN work_schedules s ON s.id = e.schedule_id
WHERE e.is_active = 1
"""


@router.get("", response_model=list[EmployeeOut])
def list_employees(department_id: Optional[int] = None,
                   schedule_id:   Optional[int] = None):
    sql = _LIST_SQL
    params: list = []
    if department_id:
        sql += " AND e.department_id = ?"
        params.append(department_id)
    if schedule_id:
        sql += " AND e.schedule_id = ?"
        params.append(schedule_id)
    sql += " ORDER BY e.full_name"
    with db_cursor() as cur:
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]


@router.get("/{employee_id}", response_model=EmployeeOut)
def get_employee(employee_id: int):
    with db_cursor() as cur:
        cur.execute(_LIST_SQL + " AND e.id = ?", (employee_id,))
        row = cur.fetchone()
        if row is None:
            raise HTTPException(404, "Сотрудник не найден")
        return dict(row)
