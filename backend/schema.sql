-- =====================================================
-- БАЗА ДАННЫХ "Учёт посещаемости сотрудников"
-- СУБД: SQLite 3.35+    Кодировка: UTF-8
-- Схема в 3НФ
-- =====================================================

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA encoding     = 'UTF-8';

-- -------- 1. СПРАВОЧНИКИ -----------------------------

CREATE TABLE IF NOT EXISTS departments (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    code   TEXT    NOT NULL UNIQUE,
    name   TEXT    NOT NULL,
    parent_id INTEGER,
    FOREIGN KEY (parent_id) REFERENCES departments (id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS positions (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT    NOT NULL UNIQUE,
    category TEXT    NOT NULL DEFAULT 'specialist'
             CHECK (category IN ('management', 'specialist', 'worker', 'service'))
);

CREATE TABLE IF NOT EXISTS work_schedules (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT    NOT NULL UNIQUE,
    name        TEXT    NOT NULL,
    description TEXT
);

-- Шаблон рабочего дня в графике (день недели = 1..7, понедельник = 1)
CREATE TABLE IF NOT EXISTS schedule_days (
    schedule_id INTEGER NOT NULL,
    weekday     INTEGER NOT NULL CHECK (weekday BETWEEN 1 AND 7),
    start_time  TEXT    NOT NULL,
    end_time    TEXT    NOT NULL,
    lunch_break_min INTEGER NOT NULL DEFAULT 60 CHECK (lunch_break_min >= 0),
    is_workday  INTEGER NOT NULL DEFAULT 1 CHECK (is_workday IN (0, 1)),
    PRIMARY KEY (schedule_id, weekday),
    CHECK (is_workday = 0 OR end_time > start_time),
    FOREIGN KEY (schedule_id) REFERENCES work_schedules (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS absence_types (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    code         TEXT    NOT NULL UNIQUE,
    name         TEXT    NOT NULL,
    short_code   TEXT    NOT NULL UNIQUE,  -- двухбуквенный код для табеля (О, Б, К, П)
    is_paid      INTEGER NOT NULL DEFAULT 1 CHECK (is_paid IN (0, 1)),
    color        TEXT    NOT NULL DEFAULT '#64748B'
);

CREATE TABLE IF NOT EXISTS holidays (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    date  DATE    NOT NULL UNIQUE,
    name  TEXT    NOT NULL
);

-- -------- 2. СОТРУДНИКИ ------------------------------

CREATE TABLE IF NOT EXISTS employees (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    personnel_number TEXT   NOT NULL UNIQUE,        -- табельный номер
    full_name       TEXT    NOT NULL,
    department_id   INTEGER NOT NULL,
    position_id     INTEGER NOT NULL,
    schedule_id     INTEGER NOT NULL,
    hire_date       DATE    NOT NULL,
    phone           TEXT    CHECK (phone IS NULL OR phone GLOB '+[0-9]*'),
    email           TEXT    UNIQUE CHECK (email IS NULL OR email LIKE '_%@_%._%'),
    is_active       INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    FOREIGN KEY (department_id) REFERENCES departments      (id) ON DELETE RESTRICT,
    FOREIGN KEY (position_id)   REFERENCES positions        (id) ON DELETE RESTRICT,
    FOREIGN KEY (schedule_id)   REFERENCES work_schedules   (id) ON DELETE RESTRICT
);

-- -------- 3. ОТМЕТКИ ВХОДА/ВЫХОДА ---------------------

CREATE TABLE IF NOT EXISTS attendance_records (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id     INTEGER NOT NULL,
    work_date       DATE    NOT NULL,
    check_in        TIMESTAMP,
    check_out       TIMESTAMP,
    late_minutes    INTEGER NOT NULL DEFAULT 0 CHECK (late_minutes >= 0),
    early_leave_min INTEGER NOT NULL DEFAULT 0 CHECK (early_leave_min >= 0),
    worked_minutes  INTEGER NOT NULL DEFAULT 0 CHECK (worked_minutes >= 0),
    overtime_min    INTEGER NOT NULL DEFAULT 0 CHECK (overtime_min >= 0),
    note            TEXT,
    UNIQUE (employee_id, work_date),
    CHECK (check_out IS NULL OR check_in IS NULL OR check_out >= check_in),
    FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE RESTRICT
);

-- -------- 4. ОТСУТСТВИЯ ------------------------------

CREATE TABLE IF NOT EXISTS absences (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id     INTEGER NOT NULL,
    absence_type_id INTEGER NOT NULL,
    date_from       DATE    NOT NULL,
    date_to         DATE    NOT NULL,
    document_number TEXT,                                -- № приказа/больничного
    note            TEXT,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (date_to >= date_from),
    FOREIGN KEY (employee_id)     REFERENCES employees     (id) ON DELETE RESTRICT,
    FOREIGN KEY (absence_type_id) REFERENCES absence_types (id) ON DELETE RESTRICT
);

-- -------- 5. ИНДЕКСЫ ---------------------------------

CREATE INDEX IF NOT EXISTS idx_employees_dept   ON employees           (department_id);
CREATE INDEX IF NOT EXISTS idx_employees_sched  ON employees           (schedule_id);
CREATE INDEX IF NOT EXISTS idx_attend_date      ON attendance_records  (work_date);
CREATE INDEX IF NOT EXISTS idx_attend_emp_date  ON attendance_records  (employee_id, work_date);
CREATE INDEX IF NOT EXISTS idx_absences_emp     ON absences            (employee_id);
CREATE INDEX IF NOT EXISTS idx_absences_period  ON absences            (date_from, date_to);

-- -------- 6. ТРИГГЕРЫ ЦЕЛОСТНОСТИ ---------------------

-- Запрет одновременных отсутствий с пересечением периодов у одного сотрудника
DROP TRIGGER IF EXISTS trg_absence_no_overlap;
CREATE TRIGGER trg_absence_no_overlap
BEFORE INSERT ON absences
FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN EXISTS (
            SELECT 1 FROM absences a
             WHERE a.employee_id = NEW.employee_id
               AND a.date_from  <= NEW.date_to
               AND a.date_to    >= NEW.date_from
        )
        THEN RAISE(ABORT, 'У сотрудника уже зарегистрировано отсутствие на этот период')
    END;
END;
