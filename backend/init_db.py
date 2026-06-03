"""Точка входа: ресет/инициализация БД учёта посещаемости.

Запуск из корня проекта:
    python -m backend.init_db
"""
from __future__ import annotations

from backend.database import init_schema, seed_data, DB_PATH


def main() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"Старая база удалена: {DB_PATH}")
    init_schema()
    seed_data()
    size_kb = DB_PATH.stat().st_size / 1024
    print(f"База создана и заполнена: {DB_PATH} ({size_kb:.1f} КБ)")


if __name__ == "__main__":
    main()
