"""Pydantic-схемы валидации."""
from __future__ import annotations

import datetime as dt
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------- Справочники ----------

class DepartmentOut(BaseModel):
    id: int
    code: str
    name: str
    parent_id: Optional[int]
    employees_count: int


class PositionOut(BaseModel):
    id: int
    name: str
    category: str


class WorkScheduleOut(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str]


class AbsenceTypeOut(BaseModel):
    id: int
    code: str
    name: str
    short_code: str
    is_paid: int
    color: str


# ---------- Сотрудники ----------

class EmployeeOut(BaseModel):
    id: int
    personnel_number: str
    full_name: str
    department_id: int
    department_name: str
    position_id: int
    position_name: str
    schedule_id: int
    schedule_name: str
    hire_date: dt.date
    phone: Optional[str]
    email: Optional[str]
    is_active: int


# ---------- Отметки ----------

class AttendanceRecordOut(BaseModel):
    id: int
    employee_id: int
    employee_name: str
    personnel_number: str
    department_name: str
    work_date: dt.date
    check_in: Optional[dt.datetime]
    check_out: Optional[dt.datetime]
    late_minutes: int
    early_leave_min: int
    worked_minutes: int
    overtime_min: int
    status: str        # 'on_duty', 'completed', 'absent'
    note: Optional[str]


class CheckInIn(BaseModel):
    employee_id: int
    timestamp: Optional[dt.datetime] = None   # default = CURRENT
    note: Optional[str] = None


class CheckOutIn(BaseModel):
    employee_id: int
    timestamp: Optional[dt.datetime] = None
    note: Optional[str] = None


class CheckResult(BaseModel):
    """Ответ на check-in / check-out."""
    success: bool = True
    record: AttendanceRecordOut
    message: str


# ---------- Отсутствия ----------

class AbsenceIn(BaseModel):
    employee_id: int
    absence_type_id: int
    date_from: dt.date
    date_to: dt.date
    document_number: Optional[str] = Field(default=None, max_length=50)
    note: Optional[str] = None


class AbsenceOut(BaseModel):
    id: int
    employee_id: int
    employee_name: str
    absence_type_id: int
    absence_type_name: str
    absence_type_short_code: str
    absence_type_color: str
    is_paid: int
    date_from: dt.date
    date_to: dt.date
    days_count: int
    document_number: Optional[str]
    note: Optional[str]
    created_at: dt.datetime


# ---------- Табель ----------

class TimesheetCellOut(BaseModel):
    """Ячейка табеля для (employee, день месяца)."""
    day: int                          # 1..31
    code: str                         # П (присутствовал), О (отпуск), Б (больничный), В (выходной/праздник), -- (нет данных)
    color: str
    worked_minutes: int
    late_minutes: int
    is_workday: bool


class TimesheetRowOut(BaseModel):
    employee_id: int
    personnel_number: str
    full_name: str
    department_name: str
    days: List[TimesheetCellOut]
    total_worked_minutes: int
    total_late_minutes: int
    total_overtime_min: int
    total_absent_days: int


class TimesheetOut(BaseModel):
    year: int
    month: int
    days_in_month: int
    rows: List[TimesheetRowOut]
