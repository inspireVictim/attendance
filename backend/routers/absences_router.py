"""Отсутствия: отпуска, больничные, командировки."""
from __future__ import annotations

import datetime as dt
from typing import Optional

from fastapi import APIRouter, HTTPException

from ..database import db_cursor
from ..schemas import AbsenceIn, AbsenceOut

router = APIRouter(prefix="/api/absences", tags=["absences"])


_LIST_SQL = """
SELECT
    ab.id, ab.employee_id, e.full_name AS employee_name,
    ab.absence_type_id,
    at.name        AS absence_type_name,
    at.short_code  AS absence_type_short_code,
    at.color       AS absence_type_color,
    at.is_paid,
    ab.date_from, ab.date_to,
    (julianday(ab.date_to) - julianday(ab.date_from) + 1) AS days_count,
    ab.document_number, ab.note, ab.created_at
FROM absences ab
JOIN employees     e  ON e.id  = ab.employee_id
JOIN absence_types at ON at.id = ab.absence_type_id
"""


@router.get("", response_model=list[AbsenceOut])
def list_absences(active_on: Optional[dt.date] = None,
                  employee_id: Optional[int] = None):
    sql = _LIST_SQL + " WHERE 1=1"
    params: list = []
    if active_on:
        sql += " AND ab.date_from <= ? AND ab.date_to >= ?"
        params += [active_on, active_on]
    if employee_id:
        sql += " AND ab.employee_id = ?"
        params.append(employee_id)
    sql += " ORDER BY ab.date_from DESC"
    with db_cursor() as cur:
        cur.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
        for r in rows:
            r["days_count"] = int(r["days_count"])
        return rows


@router.post("", response_model=AbsenceOut, status_code=201)
def create_absence(payload: AbsenceIn):
    with db_cursor(commit=True) as cur:
        try:
            cur.execute(
                """INSERT INTO absences
                   (employee_id, absence_type_id, date_from, date_to, document_number, note)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (payload.employee_id, payload.absence_type_id,
                 payload.date_from, payload.date_to,
                 payload.document_number, payload.note),
            )
        except Exception as exc:
            msg = str(exc)
            if "уже зарегистрировано отсутствие" in msg:
                raise HTTPException(400, "У сотрудника пересекается период с уже зарегистрированным отсутствием")
            raise HTTPException(400, f"Не удалось создать запись: {exc}")
        new_id = cur.lastrowid
        cur.execute(_LIST_SQL + " WHERE ab.id = ?", (new_id,))
        row = dict(cur.fetchone())
        row["days_count"] = int(row["days_count"])
        return row


@router.delete("/{absence_id}", status_code=204)
def delete_absence(absence_id: int):
    with db_cursor(commit=True) as cur:
        cur.execute("DELETE FROM absences WHERE id = ?", (absence_id,))
        if cur.rowcount == 0:
            raise HTTPException(404, "Запись отсутствия не найдена")
