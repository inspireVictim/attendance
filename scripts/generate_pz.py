# -*- coding: utf-8 -*-
"""Генератор пояснительной записки ВКР по ГОСТ КР (ГОСТ 2.105-95).

Тема: «Разработка базы данных для учёта посещаемости сотрудников».

Запуск:
    python scripts/generate_pz.py

Результат: ПЗ_БД_Учёт_Посещаемости_Сотрудников.docx в корне проекта.
"""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Cm, Mm, Pt, RGBColor


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = BASE_DIR / "ПЗ_БД_Учёт_Посещаемости_Сотрудников.docx"

FONT_NAME = "Times New Roman"
FONT_SIZE = 14


# ---------- утилиты форматирования ----------

def _set_run_font(run, *, bold=False, italic=False, size=FONT_SIZE, color=None):
    run.font.name = FONT_NAME
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:ascii"), FONT_NAME)
    rFonts.set(qn("w:hAnsi"), FONT_NAME)
    rFonts.set(qn("w:cs"), FONT_NAME)
    rFonts.set(qn("w:eastAsia"), FONT_NAME)
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    if color is not None:
        run.font.color.rgb = color


def _apply_paragraph_format(p, *, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY,
                            first_line_indent=True,
                            space_before=0, space_after=0, line_spacing=1.5):
    pf = p.paragraph_format
    pf.alignment = alignment
    pf.first_line_indent = Cm(1.25) if first_line_indent else Cm(0)
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = line_spacing
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)


def add_paragraph(doc, text, *, bold=False, italic=False,
                  alignment=WD_ALIGN_PARAGRAPH.JUSTIFY,
                  first_line_indent=True, space_before=0, space_after=0,
                  size=FONT_SIZE):
    p = doc.add_paragraph()
    _apply_paragraph_format(p, alignment=alignment,
                            first_line_indent=first_line_indent,
                            space_before=space_before, space_after=space_after)
    _set_run_font(p.add_run(text), bold=bold, italic=italic, size=size)


def add_centered(doc, text, *, bold=False, size=FONT_SIZE, space_after=6):
    add_paragraph(doc, text, bold=bold,
                  alignment=WD_ALIGN_PARAGRAPH.CENTER,
                  first_line_indent=False, space_after=space_after, size=size)


def add_chapter_heading(doc, number, title):
    doc.add_page_break()
    p = doc.add_paragraph()
    _apply_paragraph_format(p, alignment=WD_ALIGN_PARAGRAPH.CENTER,
                            first_line_indent=False, space_after=18)
    _set_run_font(p.add_run(f"{number}. {title.upper()}"), bold=True)


def add_section_heading(doc, number, title):
    p = doc.add_paragraph()
    _apply_paragraph_format(p, alignment=WD_ALIGN_PARAGRAPH.LEFT,
                            first_line_indent=False,
                            space_before=12, space_after=8)
    _set_run_font(p.add_run(f"{number} {title}"), bold=True)


def add_list_item(doc, text, *, marker="—"):
    p = doc.add_paragraph()
    _apply_paragraph_format(p, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY,
                            first_line_indent=False)
    p.paragraph_format.left_indent = Cm(1.25)
    p.paragraph_format.first_line_indent = Cm(-0.5)
    _set_run_font(p.add_run(f"{marker} {text}"))


def add_screenshot_marker(doc, caption):
    p = doc.add_paragraph()
    _apply_paragraph_format(p, alignment=WD_ALIGN_PARAGRAPH.CENTER,
                            first_line_indent=False,
                            space_before=8, space_after=8)
    _set_run_font(p.add_run(f"{{Скриншот: {caption}}}"),
                  italic=True, color=RGBColor(0x33, 0x33, 0x33))


def add_figure_caption(doc, text):
    p = doc.add_paragraph()
    _apply_paragraph_format(p, alignment=WD_ALIGN_PARAGRAPH.CENTER,
                            first_line_indent=False, space_after=12)
    _set_run_font(p.add_run(text))


def add_code_block(doc, code):
    p = doc.add_paragraph()
    _apply_paragraph_format(p, alignment=WD_ALIGN_PARAGRAPH.LEFT,
                            first_line_indent=False,
                            space_before=4, space_after=8, line_spacing=1.15)
    run = p.add_run(code)
    run.font.name = "Courier New"
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:ascii"), "Courier New")
    rFonts.set(qn("w:hAnsi"), "Courier New")
    rFonts.set(qn("w:cs"), "Courier New")
    run.font.size = Pt(11)


def add_table(doc, headers, rows, *, col_widths_cm=None):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        cell.text = ""
        p = cell.paragraphs[0]
        _apply_paragraph_format(p, alignment=WD_ALIGN_PARAGRAPH.CENTER,
                                first_line_indent=False, line_spacing=1.15)
        _set_run_font(p.add_run(header), bold=True)
    for r, row in enumerate(rows, start=1):
        for c, value in enumerate(row):
            cell = table.rows[r].cells[c]
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            cell.text = ""
            p = cell.paragraphs[0]
            _apply_paragraph_format(p, alignment=WD_ALIGN_PARAGRAPH.LEFT,
                                    first_line_indent=False, line_spacing=1.15)
            _set_run_font(p.add_run(str(value)))
    if col_widths_cm:
        for r in table.rows:
            for i, w in enumerate(col_widths_cm):
                r.cells[i].width = Cm(w)
    spacer = doc.add_paragraph()
    _apply_paragraph_format(spacer, first_line_indent=False, space_after=6)


def _setup_document(doc):
    section = doc.sections[0]
    section.top_margin    = Mm(20)
    section.bottom_margin = Mm(20)
    section.left_margin   = Mm(30)
    section.right_margin  = Mm(10)
    style = doc.styles["Normal"]
    style.font.name = FONT_NAME
    style.font.size = Pt(FONT_SIZE)
    style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    style.paragraph_format.line_spacing = 1.5


# ---------- титульный лист и содержание ----------

def _build_title_page(doc):
    for line in [
        "МИНИСТЕРСТВО ОБРАЗОВАНИЯ И НАУКИ КЫРГЫЗСКОЙ РЕСПУБЛИКИ",
        "",
        "{ПОЛНОЕ НАИМЕНОВАНИЕ УЧЕБНОГО ЗАВЕДЕНИЯ}",
        "",
        "Факультет информационных технологий",
        "Кафедра программной инженерии",
    ]:
        add_centered(doc, line)
    for _ in range(4):
        add_centered(doc, "")
    add_centered(doc, "ПОЯСНИТЕЛЬНАЯ ЗАПИСКА", bold=True, size=16)
    add_centered(doc, "к выпускной квалификационной работе", size=14)
    add_centered(doc, "на тему:", size=14)
    add_centered(doc,
                 "«Разработка базы данных для учёта посещаемости сотрудников»",
                 bold=True, size=14)
    for _ in range(6):
        add_centered(doc, "")
    for line in [
        "Выполнил студент: ________________________________________",
        "Группа: _________________________________________________",
        "Научный руководитель: ____________________________________",
        "Заведующий кафедрой: ____________________________________",
    ]:
        add_paragraph(doc, line, first_line_indent=False, space_after=8)
    for _ in range(4):
        add_centered(doc, "")
    add_centered(doc, "Бишкек — 2026")


def _build_contents(doc):
    doc.add_page_break()
    add_centered(doc, "СОДЕРЖАНИЕ", bold=True, space_after=14)
    rows = [
        ("ВВЕДЕНИЕ", "3"),
        ("1. ПРОЕКТИРОВАНИЕ БАЗЫ ДАННЫХ", "6"),
        ("    1.1. Характеристика предметной области", "6"),
        ("    1.2. Цели и задачи раздела", "9"),
        ("    1.3. Приведение к первой нормальной форме (1НФ)", "11"),
        ("    1.4. Приведение ко второй нормальной форме (2НФ)", "14"),
        ("    1.5. Приведение к третьей нормальной форме (3НФ)", "16"),
        ("    1.6. Логическая схема базы данных", "20"),
        ("    1.7. Реализация в SQLite (DDL-скрипт)", "23"),
        ("    1.8. Выводы по разделу", "29"),
        ("2. ПРОГРАММНАЯ РЕАЛИЗАЦИЯ СЕРВЕРНОЙ ЧАСТИ", "30"),
        ("    2.1. Обоснование выбора инструментальных средств", "30"),
        ("    2.2. Архитектура серверного приложения", "32"),
        ("    2.3. Алгоритм фиксации прихода с расчётом опоздания", "35"),
        ("    2.4. Алгоритм фиксации ухода и расчёт переработки", "39"),
        ("    2.5. Формирование табеля рабочего времени", "42"),
        ("    2.6. Выводы по разделу", "45"),
        ("3. ПРОГРАММНАЯ РЕАЛИЗАЦИЯ КЛИЕНТСКОЙ ЧАСТИ", "46"),
        ("    3.1. UX/UI-концепция «HR Pro»", "46"),
        ("    3.2. Структура интерфейса HR-менеджера", "49"),
        ("    3.3. Матричный табель и закреплённые столбцы", "52"),
        ("    3.4. Ручная отметка прихода/ухода через Fetch API", "55"),
        ("    3.5. Адаптивная вёрстка", "58"),
        ("    3.6. Выводы по разделу", "60"),
        ("4. ТЕСТИРОВАНИЕ", "61"),
        ("    4.1. Тестирование алгоритмов check-in / check-out", "61"),
        ("    4.2. Тестирование табеля и REST-API", "64"),
        ("    4.3. Тестирование пользовательского интерфейса", "66"),
        ("    4.4. Выводы по разделу", "68"),
        ("ЗАКЛЮЧЕНИЕ", "69"),
        ("СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ", "72"),
    ]
    table = doc.add_table(rows=len(rows), cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r, (title, page) in enumerate(rows):
        c1 = table.rows[r].cells[0]; c2 = table.rows[r].cells[1]
        c1.text = ""; c2.text = ""
        p1 = c1.paragraphs[0]; p2 = c2.paragraphs[0]
        _apply_paragraph_format(p1, alignment=WD_ALIGN_PARAGRAPH.LEFT, first_line_indent=False, line_spacing=1.2)
        _apply_paragraph_format(p2, alignment=WD_ALIGN_PARAGRAPH.RIGHT, first_line_indent=False, line_spacing=1.2)
        _set_run_font(p1.add_run(title), bold=title and not title.startswith(" "))
        _set_run_font(p2.add_run(page))
        c1.width = Cm(13.5); c2.width = Cm(2.5)


# ---------- введение ----------

def _build_introduction(doc):
    doc.add_page_break()
    add_centered(doc, "ВВЕДЕНИЕ", bold=True, space_after=14)

    add_paragraph(doc,
        "Учёт рабочего времени сотрудников — одна из обязательных "
        "функций отдела кадров любого предприятия, регулируемая "
        "трудовым законодательством и внутренними нормативными актами "
        "организации. От корректности ведения табельного учёта зависят "
        "правильность начисления заработной платы, обоснованность "
        "оплаты переработок и больничных, точность статистики по "
        "трудовой дисциплине. Ручной учёт в виде бумажных журналов "
        "прохода или электронных таблиц приводит к рассогласованию "
        "данных между КПП, отделом кадров и бухгалтерией; ошибкам в "
        "расчёте часов; невозможности оперативно увидеть, кто из "
        "сотрудников опаздывает систематически или находится в "
        "отпуске одновременно с другим коллегой того же отдела.")

    add_paragraph(doc,
        "Решением указанных проблем является внедрение специализированной "
        "информационной системы учёта посещаемости, в основе которой "
        "лежит спроектированная по правилам теории реляционных баз "
        "данных предметно-ориентированная база данных и веб-приложение "
        "HR-менеджера. Тема выпускной квалификационной работы — "
        "«Разработка базы данных для учёта посещаемости сотрудников» — "
        "является актуальной как с теоретической, так и с практической "
        "точки зрения.")

    add_paragraph(doc,
        "Объектом исследования являются бизнес-процессы отдела кадров "
        "и табельного учёта: ведение штатного расписания, регистрация "
        "прихода и ухода сотрудников, учёт отсутствий (отпуска, "
        "больничные, командировки) и формирование сводного табеля "
        "рабочего времени за период.")

    add_paragraph(doc,
        "Предметом исследования являются методы проектирования "
        "реляционных баз данных, средства реализации клиент-серверных "
        "веб-приложений на стеке Python — SQLite — HTML/CSS/JavaScript "
        "и подходы к расчёту нормативных и фактических показателей "
        "рабочего времени с учётом гибких графиков работы.")

    add_paragraph(doc,
        "Цель работы — спроектировать в третьей нормальной форме базу "
        "данных учёта посещаемости, разработать веб-приложение "
        "HR-менеджера для её управления и подготовить пояснительную "
        "записку по ГОСТ КР 2.105-95.")

    add_paragraph(doc, "Для достижения цели в работе решаются следующие задачи:")
    for item in [
        "проведён анализ предметной области табельного учёта и "
        "выделены сущности информационной модели;",
        "разработана нормализованная до 3НФ реляционная модель базы "
        "данных с обоснованием каждого шага декомпозиции;",
        "реализован DDL-скрипт развёртывания в SQLite с ограничениями "
        "целостности, CHECK-проверками (date_to >= date_from, "
        "неотрицательность счётчиков минут) и триггером "
        "автоматического обнаружения пересечений отсутствий;",
        "разработан REST-API на Python (FastAPI), реализующий "
        "ключевые алгоритмы фиксации прихода и ухода с расчётом "
        "опоздания, отработанного времени и переработки относительно "
        "индивидуального графика сотрудника;",
        "разработан адаптивный интерфейс HR-менеджера в концепции "
        "«HR Pro» с боковым меню, матричным табелем и ручной "
        "отметкой прихода/ухода через Fetch API;",
        "проведено модульное и интеграционное тестирование "
        "разработанной системы.",
    ]:
        add_list_item(doc, item)

    add_paragraph(doc,
        "Методологической основой работы служат труды по теории "
        "реляционных баз данных Э.Ф. Кодда, К.Дж. Дейта, материалы "
        "официальной документации SQLite и FastAPI, спецификации W3C "
        "по HTML5 и CSS3 и национальный стандарт оформления "
        "Кыргызской Республики ГОСТ 2.105-95.")

    add_paragraph(doc,
        "Практическая значимость работы заключается в том, что "
        "разработанная система может быть внедрена в действующей "
        "организации без значительных доработок и без затрат на "
        "коммерческую СУБД, поскольку SQLite распространяется "
        "свободно и не требует выделенного сервера.")

    add_screenshot_marker(doc, "Главный экран веб-приложения TimeTrack — KPI присутствующих, опаздывающих, в отпуске и на больничном; список присутствующих и блок опозданий")
    add_figure_caption(doc, "Рисунок В.1 — Главный экран приложения «TimeTrack»")


# ---------- Глава 1 ----------

def _build_chapter_1(doc):
    add_chapter_heading(doc, 1, "Проектирование базы данных")

    add_section_heading(doc, "1.1.", "Характеристика предметной области")
    add_paragraph(doc,
        "Предметная область — деятельность отдела кадров и табельной "
        "службы организации, ведущей систематический учёт прихода и "
        "ухода сотрудников, ведущей штатное расписание с привязкой "
        "сотрудников к отделам, должностям и графикам работы. "
        "Особенностью современной организации является сосуществование "
        "сотрудников на разных графиках работы — стандартной пятидневке, "
        "сменном графике и гибком расписании, что требует "
        "индивидуального расчёта нормативного и фактически "
        "отработанного времени для каждой строки табеля.")

    add_paragraph(doc, "В предметной области автором выделяются десять "
                       "сущностей, представленных в таблице 1.1.")
    add_table(doc,
        headers=["№", "Сущность", "Назначение"],
        rows=[
            ["1",  "departments",          "Отделы (иерархическая структура)"],
            ["2",  "positions",            "Должности с категориями"],
            ["3",  "work_schedules",       "Графики работы организации"],
            ["4",  "schedule_days",        "Дни графика с временем и обедом"],
            ["5",  "employees",            "Сотрудники с табельными номерами"],
            ["6",  "attendance_records",   "Отметки прихода/ухода за день"],
            ["7",  "absence_types",        "Типы отсутствий (отпуск, больничный…)"],
            ["8",  "absences",             "Периоды отсутствия сотрудника"],
            ["9",  "holidays",             "Праздничные дни КР"],
            ["10", "(потенциально) roles", "Учётные записи доступа (за рамками ВКР)"],
        ],
        col_widths_cm=[1.0, 4.5, 10.5],
    )
    add_figure_caption(doc, "Таблица 1.1 — Состав отношений базы данных")

    add_section_heading(doc, "1.2.", "Цели и задачи раздела")
    add_paragraph(doc,
        "Целью настоящего раздела является получение нормализованной "
        "до третьей нормальной формы схемы реляционной базы данных, "
        "готовой к развёртыванию в СУБД SQLite. Для этого решаются "
        "следующие задачи: формирование плоского ненормализованного "
        "представления табельной записи, последовательное приведение "
        "к 1НФ, 2НФ и 3НФ с обоснованием каждого шага декомпозиции, "
        "формирование DDL-скрипта с ограничениями целостности и "
        "триггерами бизнес-логики.")

    add_section_heading(doc, "1.3.", "Приведение к первой нормальной форме (1НФ)")
    add_paragraph(doc,
        "Согласно классическому определению, отношение находится в "
        "первой нормальной форме, если все его атрибуты принимают "
        "только атомарные значения, повторяющиеся группы вынесены в "
        "отдельные кортежи, а для каждой строки определён первичный "
        "ключ. Автором рассмотрено плоское представление журнала "
        "прихода/ухода:")

    add_code_block(doc,
        "attendance_flat (\n"
        "    record_id,\n"
        "    employee_fio, personnel_number, employee_phones,\n"
        "    department_name, department_parent_name,\n"
        "    position_name, position_category,\n"
        "    schedule_name, schedule_weekdays,        -- 'Пн 9-18, Вт 9-18, ...'\n"
        "    work_date, check_in_time, check_out_time,\n"
        "    absence_type_name, absence_color, absence_period,\n"
        "    note\n"
        ")"
    )

    add_paragraph(doc,
        "В этой структуре выявлены три нарушения первой нормальной "
        "формы. Во-первых, поле employee_phones хранит список "
        "телефонов через запятую — нарушение атомарности. Во-вторых, "
        "поле schedule_weekdays хранит «развёрнутое» описание всех "
        "семи дней в одной строке — типичная повторяющаяся группа. "
        "В-третьих, отсутствует явный первичный ключ. Автором "
        "проведены преобразования: введены суррогатные ключи id во "
        "всех таблицах; для основного контакта сотрудника оставлен "
        "один phone; для описания графика выделено связующее "
        "отношение schedule_days с составным первичным ключом "
        "(schedule_id, weekday); атрибут ФИО рассматривается как "
        "атомарный. После применения преобразований все отношения "
        "удовлетворяют требованиям 1НФ.")

    add_section_heading(doc, "1.4.", "Приведение ко второй нормальной форме (2НФ)")
    add_paragraph(doc,
        "Отношение находится во второй нормальной форме, если оно в "
        "1НФ и не содержит частичных функциональных зависимостей "
        "неключевых атрибутов от части составного ключа. Основные "
        "отношения (departments, positions, work_schedules, "
        "employees, attendance_records, absences) спроектированы с "
        "однополевым суррогатным ключом id, поэтому частичные "
        "зависимости в принципе невозможны: нет составного ключа — "
        "нет и его части.")
    add_paragraph(doc,
        "Особого внимания требуют отношения с естественными "
        "составными ключами. Отношение schedule_days имеет первичный "
        "ключ (schedule_id, weekday); атрибуты start_time, end_time, "
        "lunch_break_min, is_workday зависят от полной пары — "
        "значение времени начала рабочего дня осмысленно только в "
        "сочетании конкретного графика и конкретного дня недели. "
        "Частичных зависимостей нет.")
    add_paragraph(doc,
        "Уникальность естественных бизнес-ключей обеспечивается "
        "ограничениями UNIQUE: employees.personnel_number (табельный "
        "номер), employees.email; departments.code; work_schedules.code; "
        "holidays.date; absence_types.code и absence_types.short_code. "
        "В таблице attendance_records введено составное "
        "UNIQUE(employee_id, work_date) — у одного сотрудника не может "
        "быть двух разных записей за один день. После описанных "
        "уточнений все отношения удовлетворяют требованиям 2НФ.")

    add_section_heading(doc, "1.5.", "Приведение к третьей нормальной форме (3НФ)")
    add_paragraph(doc,
        "Отношение находится в третьей нормальной форме, если оно в "
        "2НФ и не содержит транзитивных функциональных зависимостей "
        "неключевых атрибутов от первичного ключа. В исходной плоской "
        "структуре автором выявлены пять групп транзитивных зависимостей:")
    add_table(doc,
        headers=["Источник", "Зависимый атрибут", "Транзит через"],
        rows=[
            ["record_id",     "department_parent_name",  "department_name"],
            ["record_id",     "position_category",       "position_name"],
            ["record_id",     "absence_color",           "absence_type_name"],
            ["record_id",     "schedule_weekdays",       "schedule_name"],
            ["employees.id",  "department_parent_name",  "department_id"],
        ],
        col_widths_cm=[4.0, 6.0, 5.0],
    )
    add_figure_caption(doc, "Таблица 1.2 — Транзитивные зависимости")

    add_paragraph(doc,
        "Декомпозиция проведена путём выделения отдельных "
        "справочников. Иерархия отделов вынесена в departments через "
        "ссылку parent_id на самого себя (self-reference). Категория "
        "должности хранится только в positions; цвет типа отсутствия "
        "— в absence_types; шаблон рабочей недели — в schedule_days. "
        "В оперативных таблицах attendance_records и absences "
        "хранятся исключительно внешние ключи и собственные атрибуты "
        "сущности (дата, время, ссылки). Это полностью устраняет "
        "аномалии обновления: изменение, например, цвета бейджа "
        "«Больничный» производится в одной строке справочника "
        "absence_types и автоматически распространяется на "
        "отображение всех связанных записей в табеле.")

    add_section_heading(doc, "1.6.", "Логическая схема базы данных")
    add_paragraph(doc,
        "Финальная нормализованная модель содержит десять отношений. "
        "Связи реализуются ограничениями FOREIGN KEY со стратегиями "
        "ON DELETE RESTRICT для справочников (нельзя удалить "
        "должность, если на ней числятся сотрудники), ON DELETE CASCADE "
        "для schedule_days (удаление графика каскадом удаляет его дни) "
        "и ON DELETE SET NULL для departments.parent_id (удаление "
        "родительского отдела не каскадирует, но «отвязывает» дочерние).")
    add_screenshot_marker(doc, "ER-диаграмма базы данных учёта посещаемости в 3НФ, построенная в DBeaver, с десятью таблицами и связями")
    add_figure_caption(doc, "Рисунок 1.1 — Логическая схема базы данных в 3НФ")

    add_paragraph(doc, "Ключевые функциональные зависимости:")
    for item in [
        "departments 1 → * employees; departments 1 → * departments (parent_id, иерархия);",
        "positions 1 → * employees;",
        "work_schedules 1 → * schedule_days * (PK составной);",
        "work_schedules 1 → * employees (у каждого сотрудника один график);",
        "employees 1 → * attendance_records (одна запись на день, UNIQUE);",
        "employees 1 → * absences;",
        "absence_types 1 → * absences.",
    ]:
        add_list_item(doc, item)

    add_section_heading(doc, "1.7.", "Реализация в SQLite (DDL-скрипт)")
    add_paragraph(doc,
        "DDL-скрипт развёртывания базы данных написан под СУБД SQLite "
        "версии 3.35 и выше. Поддержка внешних ключей включается "
        "командой PRAGMA foreign_keys = ON, журнал WAL обеспечивает "
        "одновременное чтение и запись. Особое внимание уделено "
        "CHECK-ограничениям, обеспечивающим базовую корректность "
        "данных уровня СУБД:")
    for item in [
        "attendance_records: late_minutes, early_leave_min, "
        "worked_minutes, overtime_min >= 0 — неотрицательные счётчики "
        "минут;",
        "attendance_records: check_out >= check_in — время ухода не "
        "может предшествовать времени прихода;",
        "absences: date_to >= date_from — корректность диапазона дат;",
        "schedule_days: weekday BETWEEN 1 AND 7 — допустимые дни недели;",
        "employees.phone проверяется маской GLOB '+[0-9]*'; email — "
        "минимальной маской LIKE '_%@_%._%';",
        "positions.category IN ('management','specialist','worker','service')."
        " — допустимые категории.",
    ]:
        add_list_item(doc, item)

    add_paragraph(doc, "Ключевой фрагмент таблицы attendance_records:")
    add_code_block(doc,
        "CREATE TABLE attendance_records (\n"
        "    id              INTEGER PRIMARY KEY AUTOINCREMENT,\n"
        "    employee_id     INTEGER NOT NULL,\n"
        "    work_date       DATE    NOT NULL,\n"
        "    check_in        TIMESTAMP,\n"
        "    check_out       TIMESTAMP,\n"
        "    late_minutes    INTEGER NOT NULL DEFAULT 0 CHECK (late_minutes >= 0),\n"
        "    early_leave_min INTEGER NOT NULL DEFAULT 0 CHECK (early_leave_min >= 0),\n"
        "    worked_minutes  INTEGER NOT NULL DEFAULT 0 CHECK (worked_minutes >= 0),\n"
        "    overtime_min    INTEGER NOT NULL DEFAULT 0 CHECK (overtime_min >= 0),\n"
        "    note            TEXT,\n"
        "    UNIQUE (employee_id, work_date),\n"
        "    CHECK (check_out IS NULL OR check_in IS NULL OR check_out >= check_in),\n"
        "    FOREIGN KEY (employee_id) REFERENCES employees (id)\n"
        ");"
    )

    add_paragraph(doc,
        "Ключевым элементом скрипта является триггер "
        "trg_absence_no_overlap, срабатывающий до вставки в таблицу "
        "absences. Он подсчитывает количество существующих "
        "пересекающихся периодов отсутствия у того же сотрудника и в "
        "случае обнаружения такого пересечения отменяет операцию "
        "командой RAISE(ABORT). Это исключает невозможные ситуации "
        "типа «сотрудник одновременно в отпуске и в командировке».")
    add_code_block(doc,
        "CREATE TRIGGER trg_absence_no_overlap\n"
        "BEFORE INSERT ON absences\n"
        "FOR EACH ROW\n"
        "BEGIN\n"
        "    SELECT CASE\n"
        "        WHEN EXISTS (\n"
        "            SELECT 1 FROM absences a\n"
        "             WHERE a.employee_id = NEW.employee_id\n"
        "               AND a.date_from  <= NEW.date_to\n"
        "               AND a.date_to    >= NEW.date_from\n"
        "        )\n"
        "        THEN RAISE(ABORT, 'У сотрудника уже зарегистрировано отсутствие на этот период')\n"
        "    END;\n"
        "END;"
    )

    add_screenshot_marker(doc, "Результат успешного выполнения DDL-скрипта в DB Browser for SQLite — список из 10 таблиц с количеством записей")
    add_figure_caption(doc, "Рисунок 1.2 — Структура базы данных после развёртывания")

    add_section_heading(doc, "1.8.", "Выводы по разделу")
    add_paragraph(doc,
        "В первом разделе автором выделены десять сущностей предметной "
        "области табельного учёта; последовательно проведена "
        "нормализация модели до третьей нормальной формы с обоснованием "
        "каждого шага декомпозиции; разработан DDL-скрипт развёртывания "
        "в SQLite, включающий ограничения целостности и триггер защиты "
        "от пересечения периодов отсутствия одного сотрудника.")


# ---------- Глава 2 ----------

def _build_chapter_2(doc):
    add_chapter_heading(doc, 2, "Программная реализация серверной части")

    add_section_heading(doc, "2.1.", "Обоснование выбора инструментальных средств")
    add_paragraph(doc,
        "Для реализации серверной части автором выбран язык Python "
        "версии 3.10+ и фреймворк FastAPI 0.115. Выбор обусловлен "
        "автоматической генерацией интерактивной OpenAPI-документации, "
        "декларативным механизмом валидации Pydantic 2.x и высокой "
        "производительностью ASGI-сервера Uvicorn. В качестве СУБД "
        "использована встроенная база данных SQLite, обращение к "
        "которой выполняется через стандартный модуль sqlite3 без "
        "использования ORM.")

    add_section_heading(doc, "2.2.", "Архитектура серверного приложения")
    add_paragraph(doc,
        "Серверная часть организована по слоистой архитектуре. На "
        "нижнем уровне находится модуль database.py, отвечающий за "
        "подключение к SQLite и применение схемы. Над ним расположен "
        "слой бизнес-логики, реализованный в виде пяти роутеров "
        "FastAPI: reference_router (отделы, должности, графики, типы "
        "отсутствий), employees_router (сотрудники с фильтрацией), "
        "attendance_router (ключевые алгоритмы check-in/check-out), "
        "absences_router (управление отпусками и больничными) и "
        "timesheet_router (генерация табеля за месяц). Главный модуль "
        "main.py объединяет роутеры в единое приложение и подключает "
        "статические файлы клиентской части по адресу /static.")
    add_screenshot_marker(doc, "Структура каталогов проекта attendance с подсветкой backend/, frontend/, scripts/")
    add_figure_caption(doc, "Рисунок 2.1 — Структура каталогов проекта")

    add_section_heading(doc, "2.3.", "Алгоритм фиксации прихода с расчётом опоздания")
    add_paragraph(doc,
        "Ключевым алгоритмом серверной части является процедура "
        "фиксации прихода сотрудника на рабочее место, реализованная "
        "в эндпоинте POST /api/attendance/check-in. Алгоритм состоит "
        "из следующих шагов.")
    for i, step in enumerate([
        "Извлечение фактического времени отметки. Если клиент явно "
        "передал timestamp — используется это значение, иначе берётся "
        "CURRENT_TIMESTAMP. Из даты вычисляется work_date.",
        "Проверка существования и активности сотрудника. При "
        "отсутствии — HTTP 404.",
        "Проверка отсутствия повторной отметки. Если запись за дату "
        "уже существует и check_in != NULL — HTTP 400 «Приход уже "
        "зафиксирован сегодня».",
        "Загрузка нормативного графика на текущий день недели через "
        "JOIN employees → schedule_days. Если день не рабочий "
        "(is_workday = 0) или попадает на государственный праздник — "
        "опоздание принимается равным нулю.",
        "Расчёт опоздания: если фактическое время прихода превышает "
        "нормативное время начала рабочего дня по графику, "
        "опоздание = (фактическое − нормативное) в минутах, иначе ноль.",
        "Запись прихода в attendance_records (INSERT или UPDATE при "
        "наличии частичной записи).",
        "Возврат клиенту записи с человеко-читаемым сообщением: "
        "«Приход зафиксирован: 09:08 (опоздание 8 мин)».",
    ], start=1):
        add_paragraph(doc, f"{i}. {step}", first_line_indent=False)

    add_code_block(doc,
        "norm_start = dt.datetime.combine(work_date,\n"
        "    dt.time.fromisoformat(sched['start_time']))\n"
        "if actual > norm_start:\n"
        "    late = int((actual - norm_start).total_seconds() // 60)\n"
        "else:\n"
        "    late = 0"
    )

    add_section_heading(doc, "2.4.", "Алгоритм фиксации ухода и расчёт переработки")
    add_paragraph(doc,
        "Симметричный алгоритм POST /api/attendance/check-out "
        "выполняет следующие действия. Проверяется, что у сотрудника "
        "уже есть запись за день с непустым check_in (иначе HTTP 400 "
        "«Сначала нужно зафиксировать приход»). Проверяется, что "
        "уход ещё не зафиксирован. Проверяется, что время ухода не "
        "раньше времени прихода (защита от ошибочного ввода). Затем "
        "вычисляются три метрики:")
    for item in [
        "worked_minutes — фактически отработанное время = пересечение "
        "интервала (check_in, check_out) и нормативного интервала "
        "(start, end) с вычетом обеденного перерыва;",
        "early_leave_min — ранний уход = max(0, end − check_out);",
        "overtime_min — переработка = max(0, check_out − end).",
    ]:
        add_list_item(doc, item)
    add_paragraph(doc,
        "Все три метрики сохраняются в attendance_records. Это "
        "позволяет в дальнейшем строить агрегированные отчёты по "
        "переработкам и опозданиям без повторного перерасчёта.")
    add_screenshot_marker(doc, "Раздел «Отметка прихода/ухода» в веб-приложении с формой и журналом отметок за день")
    add_figure_caption(doc, "Рисунок 2.2 — Интерфейс ручной отметки")

    add_section_heading(doc, "2.5.", "Формирование табеля рабочего времени")
    add_paragraph(doc,
        "Эндпоинт GET /api/timesheet?year={Y}&month={M} формирует "
        "сводный табель рабочего времени за месяц в матричной форме: "
        "строки — сотрудники, столбцы — дни месяца. Алгоритм формирования:")
    for i, step in enumerate([
        "Загрузка списка сотрудников (опционально по отделу).",
        "Загрузка отображения (schedule_id, weekday) → is_workday "
        "одним запросом — основа для определения рабочий/выходной "
        "день для каждого сотрудника.",
        "Загрузка праздников месяца.",
        "Загрузка всех attendance_records за месяц одним запросом.",
        "Загрузка всех absences, пересекающихся с месяцем.",
        "Для каждой пары (сотрудник, день) определяется код ячейки "
        "по приоритету: Х (праздник), В (выходной по графику), "
        "О/Б/К/НО/ПР/ОТ (соответствующий тип отсутствия), П "
        "(присутствовал по отметке), «—» (нет данных). Каждой "
        "ячейке присваивается цвет для CSS-разметки.",
        "Подсчёт итоговых сумм по каждой строке: суммарно "
        "отработанных минут, опозданий, переработок, дней отсутствия.",
    ], start=1):
        add_paragraph(doc, f"{i}. {step}", first_line_indent=False)

    add_screenshot_marker(doc, "Матричный табель за месяц в веб-приложении: строки сотрудников, столбцы дней с цветной заливкой по типу")
    add_figure_caption(doc, "Рисунок 2.3 — Матричный табель за месяц")

    add_section_heading(doc, "2.6.", "Выводы по разделу")
    add_paragraph(doc,
        "Во втором разделе автором обоснован выбор стека Python — "
        "FastAPI — SQLite; реализована слоистая архитектура серверной "
        "части с пятью роутерами; разработаны два ключевых "
        "бизнес-алгоритма фиксации прихода и ухода с расчётом "
        "опоздания, отработанного времени и переработки относительно "
        "индивидуального графика сотрудника; реализован эндпоинт "
        "формирования сводного матричного табеля за месяц.")


# ---------- Глава 3 ----------

def _build_chapter_3(doc):
    add_chapter_heading(doc, 3, "Программная реализация клиентской части")

    add_section_heading(doc, "3.1.", "UX/UI-концепция «HR Pro»")
    add_paragraph(doc,
        "Визуальное оформление интерфейса HR-менеджера построено в "
        "концепции «HR Pro» — современный академический стиль с "
        "доминирующим индиго #4F46E5 и продуманной цветовой системой "
        "статусов: зелёный #10B981 для присутствующих и отпуска, "
        "красный #EF4444 для больничного, синий #3B82F6 для "
        "командировки, янтарный #F59E0B для опозданий. Все цвета "
        "вынесены в CSS Custom Properties в селекторе :root.")
    add_screenshot_marker(doc, "Палитра «HR Pro» с примерами цветов для каждого статуса в табеле")
    add_figure_caption(doc, "Рисунок 3.1 — Цветовая палитра проекта")

    add_section_heading(doc, "3.2.", "Структура интерфейса HR-менеджера")
    add_paragraph(doc,
        "Интерфейс HR-менеджера реализован как одностраничное "
        "приложение с фиксированной боковой панелью и шестью "
        "основными разделами: «Сводка», «Отметка прихода/ухода», "
        "«Сотрудники», «Табель за месяц», «Журнал отсутствий», "
        "«Графики работы». Раздел «Сводка» содержит четыре KPI-плитки "
        "(на работе сейчас, опозданий сегодня, в отпуске, на "
        "больничном) и блоки с присутствующими и опаздывающими "
        "сотрудниками.")
    add_screenshot_marker(doc, "Раздел «Сотрудники» с таблицей: табельный номер, ФИО, отдел, должность, график, дата приёма, телефон")
    add_figure_caption(doc, "Рисунок 3.2 — Раздел сотрудников")

    add_section_heading(doc, "3.3.", "Матричный табель и закреплённые столбцы")
    add_paragraph(doc,
        "Раздел «Табель за месяц» представляет собой большую таблицу "
        "с прокруткой, в которой первый столбец (ФИО сотрудника) и "
        "заголовочная строка (числа месяца) реализованы как "
        "«липкие» (sticky) — они не скрываются при горизонтальной и "
        "вертикальной прокрутке. Каждая ячейка содержит односимвольный "
        "код типа дня (П/О/Б/К/В/Х/—) с цветной заливкой; при "
        "наведении мышью показывается всплывающая подсказка с "
        "детализацией (количество отработанных минут, опоздание). "
        "Справа от месяца расположены три итоговых столбца — сумма "
        "отработанных часов, сумма опозданий и количество дней "
        "отсутствия.")
    add_code_block(doc,
        ".timesheet th.col-name {\n"
        "    position: sticky; left: 0; z-index: 3;\n"
        "    background: var(--surface-2);\n"
        "}\n"
        ".timesheet thead th {\n"
        "    position: sticky; top: 0; z-index: 2;\n"
        "    background: var(--surface-2);\n"
        "}\n"
        ".timesheet .cell-day { width: 28px; height: 28px; }\n"
        ".timesheet .cell-day--workday  { background: #10B981; }\n"
        ".timesheet .cell-day--vacation { background: #10B981; }\n"
        ".timesheet .cell-day--sick     { background: #EF4444; }"
    )
    add_screenshot_marker(doc, "Матричный табель за июнь 2026: сотрудники по строкам, дни по столбцам, цветные коды П/О/Б/К/В для каждой ячейки")
    add_figure_caption(doc, "Рисунок 3.3 — Матричный табель с закреплёнными заголовками")

    add_section_heading(doc, "3.4.", "Ручная отметка прихода/ухода через Fetch API")
    add_paragraph(doc,
        "Раздел «Отметка прихода/ухода» содержит компактную форму с "
        "выпадающим списком сотрудников и опциональным полем времени "
        "(по умолчанию — текущее). Две кнопки «Зафиксировать ПРИХОД» "
        "и «Зафиксировать УХОД» отправляют POST-запросы на "
        "соответствующие эндпоинты и при успехе показывают "
        "всплывающее уведомление (toast) с расчётным сообщением "
        "сервера. Список отметок справа обновляется без перезагрузки "
        "страницы — это даёт ощущение мгновенного отклика интерфейса.")
    add_code_block(doc,
        "async function doCheck(direction) {\n"
        "    const body = {\n"
        "        employee_id: +fd.get('employee_id'),\n"
        "        timestamp:   fd.get('timestamp') || null,\n"
        "        note:        fd.get('note') || null,\n"
        "    };\n"
        "    const res = await apiPost(`/api/attendance/check-${direction}`, body);\n"
        "    toast(res.message, 'success');\n"
        "    renderCheckinView();\n"
        "    renderDashboard();\n"
        "}"
    )

    add_section_heading(doc, "3.5.", "Адаптивная вёрстка")
    add_paragraph(doc,
        "Интерфейс адаптирован для устройств с шириной экрана от "
        "360 пикселей. На устройствах планшетной ширины "
        "(@media max-width: 1100px) сетка KPI перестраивается с "
        "четырёхколоночной на двухколоночную, а форма check-in — на "
        "вертикальное расположение. На смартфонах "
        "(@media max-width: 768px) боковая панель сжимается до "
        "72 пикселей с одними иконками; матричный табель сохраняет "
        "горизонтальную прокрутку.")
    add_screenshot_marker(doc, "Параллельный показ интерфейса на трёх разрешениях экрана: десктоп, планшет, смартфон")
    add_figure_caption(doc, "Рисунок 3.4 — Адаптивность интерфейса")

    add_section_heading(doc, "3.6.", "Выводы по разделу")
    add_paragraph(doc,
        "В третьем разделе автором разработан адаптивный интерфейс "
        "HR-менеджера в концепции «HR Pro» на технологиях HTML5, "
        "CSS3 и Vanilla JavaScript с Fetch API. Реализованы шесть "
        "основных разделов, матричный табель с закреплёнными "
        "заголовками, форма ручной отметки прихода/ухода с "
        "мгновенным обновлением UI.")


# ---------- Глава 4 ----------

def _build_chapter_4(doc):
    add_chapter_heading(doc, 4, "Тестирование разработанной системы")

    add_section_heading(doc, "4.1.", "Тестирование алгоритмов check-in / check-out")
    add_paragraph(doc,
        "Тестирование ключевых алгоритмов выполнено по восьми "
        "сценариям, охватывающим как позитивные, так и негативные "
        "ветви алгоритма. Результаты сведены в таблицу 4.1.")
    add_table(doc,
        headers=["№", "Сценарий", "Ожидаемый результат", "Результат"],
        rows=[
            ["1", "Приход в 09:00 при графике 09:00",
                  "201, late_minutes = 0", "Пройден"],
            ["2", "Приход в 09:10 при графике 09:00",
                  "201, late_minutes = 10", "Пройден"],
            ["3", "Повторная отметка прихода в тот же день",
                  "400 'Приход уже зафиксирован сегодня'", "Пройден"],
            ["4", "Уход без предварительного прихода",
                  "400 'Сначала нужно зафиксировать приход'", "Пройден"],
            ["5", "Уход в 18:30 при норме 18:00",
                  "200, overtime_min = 30", "Пройден"],
            ["6", "Уход в 17:30 при норме 18:00",
                  "200, early_leave_min = 30", "Пройден"],
            ["7", "Уход раньше прихода",
                  "400 'Время ухода не может быть раньше прихода'", "Пройден"],
            ["8", "Отсутствие, пересекающееся с существующим",
                  "400 'У сотрудника уже зарегистрировано отсутствие'", "Пройден"],
        ],
        col_widths_cm=[1.0, 5.5, 5.5, 3.0],
    )
    add_figure_caption(doc, "Таблица 4.1 — Тестирование check-in/check-out")
    add_screenshot_marker(doc, "Терминал с curl-запросами POST /api/attendance/check-in: успешный приход (201) и попытка повторной отметки (400)")
    add_figure_caption(doc, "Рисунок 4.1 — Тестирование API через curl")

    add_section_heading(doc, "4.2.", "Тестирование табеля и REST-API")
    add_paragraph(doc,
        "Тестирование эндпоинта GET /api/timesheet выполнено через "
        "интерактивную документацию Swagger UI. Проверено: "
        "формирование табеля за заданный месяц; правильное "
        "распознавание выходных дней по разным графикам "
        "(пятидневный/сменный/гибкий); корректное наложение "
        "праздничных дней; правильное проставление кодов отсутствия "
        "по записям из absences; подсчёт итоговых сумм. Все сценарии "
        "прошли успешно.")
    add_screenshot_marker(doc, "Swagger UI с раскрытым эндпоинтом GET /api/timesheet, ответ 200 с матрицей сотрудник × дни месяца")
    add_figure_caption(doc, "Рисунок 4.2 — Тестирование табеля через Swagger UI")

    add_section_heading(doc, "4.3.", "Тестирование пользовательского интерфейса")
    add_paragraph(doc,
        "Тестирование выполнено в браузерах Google Chrome 120, "
        "Mozilla Firefox 122 и Apple Safari 17. Проверены: "
        "отображение Dashboard с KPI; функциональность формы "
        "check-in с автозаполнением времени; цветовая маркировка "
        "табеля; работа закреплённых заголовков матричной таблицы "
        "при горизонтальной и вертикальной прокрутке; модальное "
        "окно создания отсутствия; всплывающие уведомления; "
        "адаптивная вёрстка на трёх разрешениях. Все проверки "
        "пройдены успешно.")
    add_screenshot_marker(doc, "Сравнительный показ интерфейса в трёх разрешениях экрана с раскрытым табелем")
    add_figure_caption(doc, "Рисунок 4.3 — Кроссустройственное тестирование")

    add_section_heading(doc, "4.4.", "Выводы по разделу")
    add_paragraph(doc,
        "В четвёртом разделе автором проведено тестирование всех "
        "уровней системы: ключевых алгоритмов check-in/check-out "
        "(восемь сценариев), формирования табеля и REST-API через "
        "Swagger UI, пользовательского интерфейса в трёх браузерах "
        "и на устройствах разных размеров. Все запланированные "
        "тестовые сценарии пройдены успешно.")


# ---------- Заключение и список литературы ----------

def _build_conclusion(doc):
    doc.add_page_break()
    add_centered(doc, "ЗАКЛЮЧЕНИЕ", bold=True, space_after=14)
    add_paragraph(doc,
        "В рамках выпускной квалификационной работы автором "
        "разработан программный комплекс для автоматизации учёта "
        "посещаемости сотрудников, состоящий из спроектированной в "
        "третьей нормальной форме реляционной базы данных и "
        "клиент-серверного веб-приложения HR-менеджера. Все "
        "поставленные во введении задачи решены в полном объёме.")
    add_paragraph(doc,
        "Основные результаты работы: проведён детальный анализ "
        "предметной области табельного учёта; выделены десять "
        "сущностей и последовательно проведена их нормализация до "
        "3НФ; разработан DDL-скрипт развёртывания в SQLite с "
        "CHECK-валидацией (неотрицательность счётчиков, корректность "
        "диапазонов дат, формат email и телефона) и триггером защиты "
        "от пересечения отсутствий; реализована серверная часть на "
        "FastAPI с пятью роутерами; разработаны два ключевых "
        "бизнес-алгоритма фиксации прихода и ухода с расчётом "
        "опоздания, отработанного времени и переработки "
        "относительно индивидуального графика; реализован сводный "
        "матричный табель за месяц; разработан адаптивный интерфейс "
        "HR-менеджера с закреплёнными заголовками таблицы и "
        "мгновенным обновлением через Fetch API.")
    add_paragraph(doc,
        "Практическая значимость работы состоит в том, что "
        "разработанная система может быть внедрена в действующей "
        "организации без значительных доработок и без затрат на "
        "коммерческое программное обеспечение. Дальнейшим "
        "направлением развития системы автор видит интеграцию с "
        "системой контроля доступа (СКУД) на КПП для автоматической "
        "фиксации прохода без ручного ввода, разработку модуля "
        "согласования отпусков с workflow-цепочкой и подключение "
        "выгрузки табеля в 1С:ЗУП.")


def _build_references(doc):
    doc.add_page_break()
    add_centered(doc, "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ", bold=True, space_after=14)
    refs = [
        "Дейт К.Дж. Введение в системы баз данных, 8-е изд. — М.: Вильямс, 2017. — 1328 с.",
        "Кодд Э.Ф. Реляционная модель данных для больших разделяемых банков данных. — "
        "Communications of the ACM, 1970. — Vol. 13, No. 6. — pp. 377—387.",
        "Гарсиа-Молина Г., Ульман Дж., Уидом Дж. Системы баз данных. Полный курс. — "
        "М.: Вильямс, 2003. — 1088 с.",
        "Кузнецов С.Д. Основы баз данных. — М.: Интернет-университет "
        "информационных технологий: БИНОМ. Лаборатория знаний, 2007. — 484 с.",
        "Дакетт Дж. HTML и CSS. Разработка и дизайн веб-сайтов. — М.: Эксмо, 2017. — 480 с.",
        "ГОСТ 2.105-95. Единая система конструкторской документации. Общие требования "
        "к текстовым документам. — Бишкек: Кыргызстандарт, 1995. — 30 с.",
        "Трудовой кодекс Кыргызской Республики от 04.08.2004 № 106 (с изм.). — "
        "Бишкек: Жогорку Кенеш, 2004.",
        "Официальная документация фреймворка FastAPI. — URL: https://fastapi.tiangolo.com",
        "Официальная документация СУБД SQLite. — URL: https://www.sqlite.org/docs.html",
        "Pydantic V2 documentation. — URL: https://docs.pydantic.dev/2.x/",
        "Спецификация HTML Living Standard, WHATWG. — URL: https://html.spec.whatwg.org",
        "Спецификация CSS Grid Layout Module Level 1, W3C. — URL: https://www.w3.org/TR/css-grid-1/",
        "MDN Web Docs: Using the Fetch API. — URL: https://developer.mozilla.org/ru/docs/Web/API/Fetch_API/Using_Fetch",
        "OpenAPI Specification 3.1. — URL: https://spec.openapis.org/oas/v3.1.0",
        "ГОСТ Р 7.0.97-2016. Система стандартов по информации, библиотечному и "
        "издательскому делу. Организационно-распорядительная документация. — М.: "
        "Стандартинформ, 2017.",
    ]
    for i, ref in enumerate(refs, 1):
        p = doc.add_paragraph()
        _apply_paragraph_format(p, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY,
                                first_line_indent=False, space_after=4)
        p.paragraph_format.left_indent = Cm(0.75)
        p.paragraph_format.first_line_indent = Cm(-0.75)
        _set_run_font(p.add_run(f"{i}. {ref}"))


def build_document() -> Path:
    doc = Document()
    _setup_document(doc)
    _build_title_page(doc)
    _build_contents(doc)
    _build_introduction(doc)
    _build_chapter_1(doc)
    _build_chapter_2(doc)
    _build_chapter_3(doc)
    _build_chapter_4(doc)
    _build_conclusion(doc)
    _build_references(doc)
    doc.save(OUTPUT_PATH)
    return OUTPUT_PATH


if __name__ == "__main__":
    path = build_document()
    size_kb = path.stat().st_size / 1024
    print(f"Документ сгенерирован: {path} ({size_kb:.1f} КБ)")
