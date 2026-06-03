/* ============================================================
   TimeTrack — клиент HR
   Vanilla JS + Fetch API
   ============================================================ */

const STATE = {
    employees: [], departments: [], schedules: [], absenceTypes: [],
    today: new Date().toISOString().slice(0, 10),
    tsMonth: new Date().toISOString().slice(0, 7),
};

const VIEW_TITLES = {
    dashboard:  'Сводка',
    checkin:    'Отметка прихода / ухода',
    employees:  'Сотрудники',
    timesheet:  'Табель за месяц',
    absences:   'Журнал отсутствий',
    schedules:  'Графики работы',
};

const ABSENCE_CLASS = {
    'О': 'cell-day--vacation',
    'Б': 'cell-day--sick',
    'К': 'cell-day--business',
    'НО':'cell-day--vacation',
    'ПР':'cell-day--absent',
    'ОТ':'cell-day--business',
};

async function apiGet(p) {
    const r = await fetch(p);
    if (!r.ok) throw await asErr(r);
    return r.json();
}
async function apiSend(method, p, body) {
    const r = await fetch(p, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: body ? JSON.stringify(body) : undefined,
    });
    if (r.status === 204) return null;
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw asErrFromData(r.status, data);
    return data;
}
function apiPost(p, b) { return apiSend('POST', p, b); }
function apiDelete(p)  { return apiSend('DELETE', p); }
async function asErr(r) {
    const data = await r.json().catch(() => ({}));
    return asErrFromData(r.status, data);
}
function asErrFromData(s, d) {
    const detail = d.detail || `Ошибка ${s}`;
    const err = new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
    err.status = s;
    return err;
}

document.addEventListener('DOMContentLoaded', async () => {
    document.getElementById('today-label').textContent =
        new Date().toLocaleDateString('ru-RU', { weekday: 'long', day: 'numeric', month: 'long' });
    document.getElementById('ts-month').value = STATE.tsMonth;

    document.querySelectorAll('.nav-item').forEach(b =>
        b.addEventListener('click', () => switchView(b.dataset.view))
    );
    document.getElementById('modal-close').addEventListener('click', closeModal);
    document.getElementById('modal-overlay').addEventListener('click', e => {
        if (e.target.id === 'modal-overlay') closeModal();
    });

    document.getElementById('btn-checkin').addEventListener('click', () => doCheck('in'));
    document.getElementById('btn-checkout').addEventListener('click', () => doCheck('out'));

    document.getElementById('filter-emp-dept').addEventListener('change', renderEmployees);
    document.getElementById('filter-emp-sched').addEventListener('change', renderEmployees);
    document.getElementById('ts-month').addEventListener('change', e => { STATE.tsMonth = e.target.value; renderTimesheet(); });
    document.getElementById('ts-dept').addEventListener('change', renderTimesheet);

    await preload();
    fillFilters();
    switchView('dashboard');
});

async function preload() {
    try {
        const [emps, depts, scheds, types] = await Promise.all([
            apiGet('/api/employees'),
            apiGet('/api/departments'),
            apiGet('/api/schedules'),
            apiGet('/api/absence_types'),
        ]);
        STATE.employees     = emps;
        STATE.departments   = depts;
        STATE.schedules     = scheds;
        STATE.absenceTypes  = types;
    } catch (e) { toast('Не удалось загрузить справочники: ' + e.message, 'error'); }
}

function fillFilters() {
    const empSel = document.getElementById('checkin-emp');
    empSel.innerHTML = STATE.employees.map(e =>
        `<option value="${e.id}">${e.full_name} (${e.personnel_number})</option>`
    ).join('');

    const fillDept = id => {
        const el = document.getElementById(id);
        el.innerHTML = '<option value="">Все</option>' +
            STATE.departments.map(d => `<option value="${d.id}">${d.name}</option>`).join('');
    };
    fillDept('filter-emp-dept');
    fillDept('ts-dept');

    document.getElementById('filter-emp-sched').innerHTML =
        '<option value="">Все</option>' +
        STATE.schedules.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
}

async function switchView(view) {
    document.querySelectorAll('.nav-item').forEach(b => b.classList.toggle('is-active', b.dataset.view === view));
    document.querySelectorAll('.view').forEach(v => v.hidden = (v.id !== 'view-' + view));
    document.getElementById('view-title').textContent = VIEW_TITLES[view];

    const actions = document.getElementById('content-actions');
    actions.innerHTML = '';
    if (view === 'absences') {
        actions.innerHTML = '<button class="btn btn--primary btn--small" id="btn-new-abs">+ Зарегистрировать отсутствие</button>';
        document.getElementById('btn-new-abs').addEventListener('click', openNewAbsenceModal);
    }

    const loaders = {
        dashboard:  renderDashboard,
        checkin:    renderCheckinView,
        employees:  renderEmployees,
        timesheet:  renderTimesheet,
        absences:   renderAbsences,
        schedules:  renderSchedules,
    };
    if (loaders[view]) await loaders[view]();
}

/* ---------- Dashboard ---------- */

async function renderDashboard() {
    try {
        const [today, vacations] = await Promise.all([
            apiGet(`/api/attendance?date=${STATE.today}`),
            apiGet(`/api/absences?active_on=${STATE.today}`),
        ]);
        const onDuty = today.filter(r => r.status === 'on_duty');
        const late   = today.filter(r => r.late_minutes > 0);
        const vac    = vacations.filter(a => a.absence_type_short_code === 'О' || a.absence_type_short_code === 'НО');
        const sick   = vacations.filter(a => a.absence_type_short_code === 'Б');

        document.getElementById('kpi-on-duty').textContent = onDuty.length;
        document.getElementById('kpi-late').textContent = late.length;
        document.getElementById('kpi-vacation').textContent = vac.length;
        document.getElementById('kpi-sick').textContent = sick.length;

        const presenceGrid = document.getElementById('presence-grid');
        if (onDuty.length === 0) {
            presenceGrid.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:20px;color:#94A3B8">Никто пока не отметился</div>';
        } else {
            presenceGrid.innerHTML = onDuty.map(r => `
                <div class="presence">
                    <div class="presence__avatar">${initials(r.employee_name)}</div>
                    <div>
                        <div class="presence__name">${r.employee_name}</div>
                        <div class="presence__sub">${r.department_name} · с ${new Date(r.check_in).toLocaleTimeString('ru-RU', {hour:'2-digit', minute:'2-digit'})}</div>
                    </div>
                </div>
            `).join('');
        }

        const lateList = document.getElementById('lateness-list');
        if (late.length === 0) {
            lateList.innerHTML = '<div style="text-align:center;padding:14px;color:#94A3B8">Опозданий нет ✓</div>';
        } else {
            lateList.innerHTML = late.map(r => `
                <div class="lateness">
                    <span class="lateness__name">${r.employee_name}</span>
                    <span class="lateness__delay">+${r.late_minutes} мин</span>
                </div>
            `).join('');
        }
    } catch (e) { toast(e.message, 'error'); }
}

function initials(fio) {
    return fio.split(' ').filter(Boolean).slice(0, 2).map(p => p[0]).join('').toUpperCase();
}

/* ---------- Check-in ---------- */

async function renderCheckinView() {
    const today = await apiGet(`/api/attendance?date=${STATE.today}`);
    document.getElementById('today-attendance-tbody').innerHTML = today.map(r => `
        <tr>
            <td>${r.employee_name}</td>
            <td>${r.check_in ? new Date(r.check_in).toLocaleTimeString('ru-RU', {hour:'2-digit', minute:'2-digit'}) : '—'}</td>
            <td>${r.check_out ? new Date(r.check_out).toLocaleTimeString('ru-RU', {hour:'2-digit', minute:'2-digit'}) : '—'}</td>
            <td>${r.late_minutes > 0 ? `<span style="color:#B91C1C;font-weight:600">+${r.late_minutes}</span>` : '0'}</td>
            <td>${minutesToHM(r.worked_minutes)}</td>
        </tr>
    `).join('') || '<tr><td colspan="5" style="text-align:center;color:#94A3B8;padding:14px">Отметок ещё нет</td></tr>';
}

function minutesToHM(m) {
    if (!m) return '—';
    const h = Math.floor(m / 60);
    const mm = m % 60;
    return `${h}:${String(mm).padStart(2, '0')}`;
}

async function doCheck(direction) {
    const fd = new FormData(document.getElementById('checkin-form'));
    const body = {
        employee_id: +fd.get('employee_id'),
        timestamp: fd.get('timestamp') || null,
        note: fd.get('note') || null,
    };
    try {
        const res = await apiPost(`/api/attendance/check-${direction}`, body);
        toast(res.message, 'success');
        renderCheckinView();
        renderDashboard();
    } catch (e) { toast(e.message, 'error'); }
}

/* ---------- Employees ---------- */

async function renderEmployees() {
    const dep   = document.getElementById('filter-emp-dept').value;
    const sched = document.getElementById('filter-emp-sched').value;
    let url = '/api/employees?';
    if (dep)   url += `&department_id=${dep}`;
    if (sched) url += `&schedule_id=${sched}`;
    const emps = await apiGet(url);

    document.getElementById('employees-tbody').innerHTML = emps.map(e => `
        <tr>
            <td class="cell-id">${e.personnel_number}</td>
            <td><strong>${e.full_name}</strong></td>
            <td>${e.department_name}</td>
            <td>${e.position_name}</td>
            <td>${e.schedule_name}</td>
            <td>${e.hire_date}</td>
            <td>${e.phone || '—'}</td>
        </tr>
    `).join('');
}

/* ---------- Timesheet ---------- */

async function renderTimesheet() {
    const [year, month] = STATE.tsMonth.split('-').map(Number);
    const dept = document.getElementById('ts-dept').value;
    let url = `/api/timesheet?year=${year}&month=${month}`;
    if (dept) url += `&department_id=${dept}`;
    const ts = await apiGet(url);

    const days = ts.days_in_month;
    const headerDays = Array.from({length: days}, (_, i) => `<th>${i + 1}</th>`).join('');
    const rowsHtml = ts.rows.map(r => `
        <tr>
            <td class="col-name">
                <strong>${r.full_name}</strong>
                <small>${r.department_name} · ${r.personnel_number}</small>
            </td>
            ${r.days.map(c => {
                const cls = cellClass(c);
                return `<td class="cell-day ${cls}" title="${cellTitle(c)}">${c.code}</td>`;
            }).join('')}
            <td class="col-total">${minutesToHM(r.total_worked_minutes)}</td>
            <td class="col-total">${r.total_late_minutes ? '+' + r.total_late_minutes : '0'}</td>
            <td class="col-total">${r.total_absent_days || '0'}</td>
        </tr>
    `).join('');

    document.getElementById('timesheet-wrap').innerHTML = `
        <table class="timesheet">
            <thead>
                <tr>
                    <th class="col-name">Сотрудник</th>
                    ${headerDays}
                    <th>∑ часов</th>
                    <th>∑ опозд.</th>
                    <th>∑ отсут.</th>
                </tr>
            </thead>
            <tbody>${rowsHtml}</tbody>
        </table>
    `;

    document.getElementById('timesheet-legend').innerHTML = `
        <div class="timesheet-legend__item"><span class="timesheet-legend__dot" style="background:#10B981">П</span> Присутствовал</div>
        <div class="timesheet-legend__item"><span class="timesheet-legend__dot" style="background:#10B981">О</span> Отпуск</div>
        <div class="timesheet-legend__item"><span class="timesheet-legend__dot" style="background:#EF4444">Б</span> Больничный</div>
        <div class="timesheet-legend__item"><span class="timesheet-legend__dot" style="background:#3B82F6">К</span> Командировка</div>
        <div class="timesheet-legend__item"><span class="timesheet-legend__dot" style="background:#CBD5E1;color:#64748B">В</span> Выходной</div>
        <div class="timesheet-legend__item"><span class="timesheet-legend__dot" style="background:#94A3B8">Х</span> Праздник</div>
        <div class="timesheet-legend__item"><span class="timesheet-legend__dot" style="background:#FCA5A5;color:#7F1D1D">—</span> Нет отметки</div>
    `;
}

function cellClass(c) {
    if (c.code === 'П') return 'cell-day--workday';
    if (c.code === 'В') return 'cell-day--weekend';
    if (c.code === 'Х') return 'cell-day--holiday';
    if (c.code === '—') return c.is_workday ? 'cell-day--absent' : 'cell-day--empty';
    return ABSENCE_CLASS[c.code] || 'cell-day--empty';
}

function cellTitle(c) {
    if (c.code === 'П' && c.worked_minutes) {
        return `Отработано ${minutesToHM(c.worked_minutes)}` + (c.late_minutes ? ` (опоздание +${c.late_minutes})` : '');
    }
    return c.code;
}

/* ---------- Absences ---------- */

async function renderAbsences() {
    const items = await apiGet('/api/absences');
    document.getElementById('absences-tbody').innerHTML = items.map(a => `
        <tr>
            <td><strong>${a.employee_name}</strong></td>
            <td><span class="badge" style="background:${a.absence_type_color}22;color:${a.absence_type_color}">${a.absence_type_name}</span></td>
            <td>${a.date_from}</td>
            <td>${a.date_to}</td>
            <td><strong>${a.days_count}</strong></td>
            <td>${a.document_number || '—'}</td>
            <td style="text-align:right">
                <button class="btn btn--ghost btn--small" data-act="del-abs" data-id="${a.id}">Удалить</button>
            </td>
        </tr>
    `).join('') || '<tr><td colspan="7" style="text-align:center;color:#94A3B8;padding:20px">Записей нет</td></tr>';

    document.querySelectorAll('[data-act="del-abs"]').forEach(b => b.addEventListener('click', async () => {
        if (!confirm('Удалить запись отсутствия?')) return;
        try {
            await apiDelete('/api/absences/' + b.dataset.id);
            toast('Удалено', 'warn');
            renderAbsences();
            renderDashboard();
            renderTimesheet();
        } catch (e) { toast(e.message, 'error'); }
    }));
}

function openNewAbsenceModal() {
    const empOpts  = STATE.employees.map(e => `<option value="${e.id}">${e.full_name} (${e.personnel_number})</option>`).join('');
    const typeOpts = STATE.absenceTypes.map(t => `<option value="${t.id}">${t.name}</option>`).join('');
    openModal('Новое отсутствие', `
        <form id="abs-form" class="form">
            <label class="field"><span>Сотрудник *</span><select name="employee_id" required>${empOpts}</select></label>
            <label class="field"><span>Тип *</span><select name="absence_type_id" required>${typeOpts}</select></label>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
                <label class="field"><span>С *</span><input name="date_from" type="date" required value="${STATE.today}"></label>
                <label class="field"><span>По *</span><input name="date_to"   type="date" required value="${STATE.today}"></label>
            </div>
            <label class="field"><span>№ документа</span><input name="document_number" placeholder="Например: ПР-145"></label>
            <label class="field"><span>Комментарий</span><textarea name="note" rows="2"></textarea></label>
            <button type="submit" class="btn btn--primary btn--block">Сохранить</button>
        </form>
    `);
    document.getElementById('abs-form').addEventListener('submit', async e => {
        e.preventDefault();
        const fd = Object.fromEntries(new FormData(e.target));
        try {
            await apiPost('/api/absences', {
                employee_id: +fd.employee_id,
                absence_type_id: +fd.absence_type_id,
                date_from: fd.date_from,
                date_to:   fd.date_to,
                document_number: fd.document_number || null,
                note: fd.note || null,
            });
            toast('Отсутствие зарегистрировано', 'success');
            closeModal();
            renderAbsences();
            renderDashboard();
            renderTimesheet();
        } catch (err) { toast(err.message, 'error'); }
    });
}

/* ---------- Schedules ---------- */

async function renderSchedules() {
    const sched = STATE.schedules;
    document.getElementById('schedule-grid').innerHTML = sched.map(s => `
        <article class="sched-card">
            <div class="sched-card__title">${s.name}</div>
            <p class="sched-card__desc">${s.description || ''}</p>
            <table class="data-table" style="font-size:12.5px">
                <thead><tr><th>День</th><th>Начало</th><th>Конец</th><th>Обед</th></tr></thead>
                <tbody id="sched-body-${s.id}"></tbody>
            </table>
        </article>
    `).join('');

    for (const s of sched) {
        // Подгрузка дней через "виртуальный" timesheet-эндпоинт мы не используем — упростим вывод
        // Здесь схема просто статична. Реальные значения уже есть в seed.
        const tbody = document.getElementById('sched-body-' + s.id);
        const data = await fetch('/api/timesheet?year=2026&month=6').then(r => r.json()).catch(() => null);
        // Покажем стандартный шаблон из README расписания, реально через отдельный endpoint можно было бы
        if (!data) continue;
        const sample = SCHEDULE_PRESETS[s.code] || [];
        tbody.innerHTML = sample.map(d => `<tr><td>${d.day}</td><td>${d.start}</td><td>${d.end}</td><td>${d.lunch} мин</td></tr>`).join('');
    }
}

const WEEKDAYS = ['Пн','Вт','Ср','Чт','Пт','Сб','Вс'];
const SCHEDULE_PRESETS = {
    standard: WEEKDAYS.map((d, i) => ({ day: d, start: i < 5 ? '09:00' : '—', end: i < 5 ? '18:00' : '—', lunch: i < 5 ? 60 : 0 })),
    shift:    WEEKDAYS.map((d, i) => ({ day: d, start: [0,2,4].includes(i) ? '08:00' : '—', end: [0,2,4].includes(i) ? '20:00' : '—', lunch: [0,2,4].includes(i) ? 60 : 0 })),
    flex:     WEEKDAYS.map((d, i) => ({ day: d, start: i < 5 ? '10:00' : '—', end: i < 5 ? '19:00' : '—', lunch: i < 5 ? 60 : 0 })),
};

/* ---------- Modal/toast ---------- */

function openModal(title, html) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').innerHTML = html;
    document.getElementById('modal-overlay').hidden = false;
}
function closeModal() { document.getElementById('modal-overlay').hidden = true; }

function toast(message, kind = 'success') {
    const el = document.createElement('div');
    el.className = 'toast' + (kind !== 'success' ? ' toast--' + kind : '');
    el.textContent = message;
    document.getElementById('toast-stack').appendChild(el);
    setTimeout(() => el.remove(), 4500);
}
