"""Точка входа FastAPI-приложения «Учёт посещаемости»."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import init_schema, seed_data
from .routers import (
    absences_router,
    attendance_router,
    employees_router,
    reference_router,
    timesheet_router,
)

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

app = FastAPI(
    title="Учёт посещаемости — REST API",
    description="ВКР. Система учёта посещаемости сотрудников.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_schema()
    seed_data()


app.include_router(reference_router.router)
app.include_router(employees_router.router)
app.include_router(attendance_router.router)
app.include_router(absences_router.router)
app.include_router(timesheet_router.router)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def root_index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")
