"""Справочники: отделы, должности, графики, типы отсутствий."""
from __future__ import annotations

from fastapi import APIRouter

from ..database import db_cursor
from ..schemas import (
    AbsenceTypeOut, DepartmentOut, PositionOut, WorkScheduleOut,
)

router = APIRouter(prefix="/api", tags=["references"])


@router.get("/departments", response_model=list[DepartmentOut])
def list_departments():
    with db_cursor() as cur:
        cur.execute("""
            SELECT d.id, d.code, d.name, d.parent_id,
                   (SELECT COUNT(*) FROM employees e
                     WHERE e.department_id = d.id AND e.is_active = 1) AS employees_count
              FROM departments d
             ORDER BY d.code
        """)
        return [dict(r) for r in cur.fetchall()]


@router.get("/positions", response_model=list[PositionOut])
def list_positions():
    with db_cursor() as cur:
        cur.execute("SELECT * FROM positions ORDER BY name")
        return [dict(r) for r in cur.fetchall()]


@router.get("/schedules", response_model=list[WorkScheduleOut])
def list_schedules():
    with db_cursor() as cur:
        cur.execute("SELECT * FROM work_schedules ORDER BY id")
        return [dict(r) for r in cur.fetchall()]


@router.get("/absence_types", response_model=list[AbsenceTypeOut])
def list_absence_types():
    with db_cursor() as cur:
        cur.execute("SELECT * FROM absence_types ORDER BY id")
        return [dict(r) for r in cur.fetchall()]
