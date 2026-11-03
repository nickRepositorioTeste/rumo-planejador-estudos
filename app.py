"""Rumo: aplicativo acadêmico Flask com SQLite e isolamento por proprietário."""
import os
import sqlite3
import secrets
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from decimal import Decimal
from functools import wraps
from pathlib import Path

from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from validacoes import day_value, integer, number, valid_time

BASE = Path(__file__).resolve().parent
SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS exams (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, name TEXT NOT NULL, position TEXT NOT NULL DEFAULT '', exam_date TEXT NOT NULL, min_score TEXT NOT NULL DEFAULT '0', target_percent TEXT NOT NULL DEFAULT '70');
CREATE TABLE IF NOT EXISTS subjects (id INTEGER PRIMARY KEY, exam_id INTEGER NOT NULL REFERENCES exams(id) ON DELETE CASCADE, name TEXT NOT NULL, questions INTEGER NOT NULL CHECK(questions > 0), points TEXT NOT NULL, penalty TEXT NOT NULL, min_score TEXT NOT NULL, target_percent TEXT NOT NULL, nonzero INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS availability (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, weekday INTEGER NOT NULL CHECK(weekday BETWEEN 0 AND 6), start_time TEXT NOT NULL, end_time TEXT NOT NULL, UNIQUE(user_id,weekday));
CREATE TABLE IF NOT EXISTS blocked (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, day TEXT NOT NULL, UNIQUE(user_id,day));
CREATE TABLE IF NOT EXISTS sessions (id INTEGER PRIMARY KEY, exam_id INTEGER NOT NULL REFERENCES exams(id) ON DELETE CASCADE, subject_id INTEGER REFERENCES subjects(id) ON DELETE SET NULL, start_at TEXT NOT NULL, end_at TEXT NOT NULL, kind TEXT NOT NULL DEFAULT 'Estudo', completed INTEGER NOT NULL DEFAULT 0, actual_minutes INTEGER NOT NULL DEFAULT 0, notes TEXT NOT NULL DEFAULT '', UNIQUE(exam_id,start_at));
CREATE TABLE IF NOT EXISTS mocks (id INTEGER PRIMARY KEY, exam_id INTEGER NOT NULL REFERENCES exams(id) ON DELETE CASCADE, day TEXT NOT NULL, total TEXT NOT NULL, meets_minimum INTEGER NOT NULL, meets_goal INTEGER NOT NULL, min_score_snapshot TEXT NOT NULL, max_score_snapshot TEXT NOT NULL, goal_percent_snapshot TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS mock_results (id INTEGER PRIMARY KEY, mock_id INTEGER NOT NULL REFERENCES mocks(id) ON DELETE CASCADE, subject_name TEXT NOT NULL, correct INTEGER NOT NULL, wrong INTEGER NOT NULL, blank INTEGER NOT NULL, questions INTEGER NOT NULL, points TEXT NOT NULL, penalty TEXT NOT NULL, minimum TEXT NOT NULL, nonzero INTEGER NOT NULL, target_percent TEXT NOT NULL, score TEXT NOT NULL);
"""


def create_app(test_config=None):
    # Produção exige chave persistente; em desenvolvimento local é permitido
    # um segredo efêmero que se perde ao reiniciar o processo.
    production = os.environ.get('RUMO_ENV', 'development').lower() == 'production'
    secret_key = os.environ.get('SECRET_KEY')
    if production and (not secret_key or not secret_key.strip()):
        raise RuntimeError('Em produção, configure SECRET_KEY persistente no ambiente antes de iniciar o Rumo.')

    app = Flask(__name__, instance_path=str(BASE / 'instance'), instance_relative_config=True)
    app.config.update(
        DATABASE=str(BASE / 'instance' / 'rumo.sqlite3'),
        SECRET_KEY=secret_key or secrets.token_hex(32),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=production or os.environ.get('COOKIE_SECURE') == '1',
        MAX_CONTENT_LENGTH=1024 * 1024,
    )
    if test_config:
        app.config.update(test_config)
    if production and (not app.config['SECRET_KEY'] or not app.config['SESSION_COOKIE_SECURE']):
        raise RuntimeError('Produção requer SECRET_KEY e cookie Secure habilitado.')
    Path(app.config['DATABASE']).parent.mkdir(parents=True, exist_ok=True)

    def db():
        if 'db' not in g:
            g.db = sqlite3.connect(app.config['DATABASE'], timeout=15)
            g.db.row_factory = sqlite3.Row
            g.db.execute('PRAGMA foreign_keys=ON')
            g.db.execute('PRAGMA busy_timeout=15000')
        return g.db

    @app.teardown_appcontext
    def close_db(_error):
        con = g.pop('db', None)
        if con is not None:
            con.close()

    with app.app_context():
        db().executescript(SCHEMA)
        db().commit()

    def one(sql, args=()):
        return db().execute(sql, args).fetchone()

    def all_rows(sql, args=()):
        return db().execute(sql, args).fetchall()

    def user_id():
        return session.get('uid')

    def login_required(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not user_id():
                return redirect(url_for('login'))
            return fn(*args, **kwargs)
        return wrapper

    def exam_owned(exam_id):
        value = one('SELECT * FROM exams WHERE id=? AND user_id=?', (exam_id, user_id()))
        if not value:
            abort(404)
        return value

    def subject_owned(subject_id):
        value = one('SELECT subjects.* FROM subjects JOIN exams ON exams.id=subjects.exam_id WHERE subjects.id=? AND exams.user_id=?', (subject_id, user_id()))
        if not value:
            abort(404)
        return value

    def session_owned(session_id):
        value = one('SELECT sessions.* FROM sessions JOIN exams ON exams.id=sessions.exam_id WHERE sessions.id=? AND exams.user_id=?', (session_id, user_id()))
        if not value:
            abort(404)
        return value

    def mock_owned(mock_id):
        value = one('SELECT mocks.* FROM mocks JOIN exams ON exams.id=mocks.exam_id WHERE mocks.id=? AND exams.user_id=?', (mock_id, user_id()))
        if not value:
            abort(404)
        return value

    @app.before_request
    def csrf_check():
        if 'csrf' not in session:
            session['csrf'] = secrets.token_urlsafe(32)
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            if not secrets.compare_digest(str(request.form.get('csrf', '')), session['csrf']):
                abort(400, description='Formulário inválido. Recarregue a página.')

    @app.context_processor
    def inject():
        return dict(csrf=session.get('csrf', ''), logged_in=bool(user_id()), today=date.today().isoformat())

    @app.errorhandler(400)
    @app.errorhandler(404)
    @app.errorhandler(413)
    def error(error):
        return render_template('error.html', message=getattr(error, 'description', 'Recurso indisponível.')), error.code

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            if '@' not in email or len(email) > 200 or len(password) < 8:
                flash('Informe e-mail válido e senha de pelo menos 8 caracteres.', 'error')
            else:
                try:
                    with db():
                        db().execute('INSERT INTO users(email,password_hash) VALUES(?,?)', (email, generate_password_hash(password)))
                    flash('Conta criada. Faça login.', 'success')
                    return redirect(url_for('login'))
                except sqlite3.IntegrityError:
                    flash('E-mail já cadastrado.', 'error')
        return render_template('auth.html', title='Criar conta', register=True)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            candidate = one('SELECT * FROM users WHERE email=?', (email,))
            if candidate and check_password_hash(candidate['password_hash'], request.form.get('password', '')):
                session.clear()
                session['uid'] = candidate['id']
                session['csrf'] = secrets.token_urlsafe(32)
                return redirect(url_for('index'))
            flash('E-mail ou senha incorretos.', 'error')
        return render_template('auth.html', title='Entrar', register=False)

    @app.post('/logout')
    @login_required
    def logout():
        session.clear()
        return redirect(url_for('login'))

    @app.route('/')
    @login_required
    def index():
        exams = all_rows('SELECT * FROM exams WHERE user_id=? ORDER BY exam_date', (user_id(),))
        upcoming = all_rows('SELECT sessions.*,exams.name AS exam_name,subjects.name AS subject_name FROM sessions JOIN exams ON exams.id=sessions.exam_id LEFT JOIN subjects ON subjects.id=sessions.subject_id WHERE exams.user_id=? AND sessions.completed=0 AND sessions.start_at>=? ORDER BY start_at LIMIT 8', (user_id(), datetime.now().isoformat(timespec='minutes')))
        stats = one('SELECT COUNT(*) AS total, COALESCE(SUM(CASE WHEN s.completed=1 THEN s.actual_minutes ELSE 0 END),0) AS done FROM sessions s JOIN exams e ON e.id=s.exam_id WHERE e.user_id=?', (user_id(),))
        mocks = all_rows('SELECT mocks.*,exams.name AS exam_name FROM mocks JOIN exams ON exams.id=mocks.exam_id WHERE exams.user_id=? ORDER BY mocks.day DESC,mocks.id DESC LIMIT 5', (user_id(),))
        return render_template('index.html', exams=exams, upcoming=upcoming, stats=stats, mocks=mocks, date=date)

    @app.route('/exams', methods=['GET', 'POST'])
    @login_required
    def exams():
        if request.method == 'POST':
            try:
                name = request.form.get('name', '').strip()
                if not name or len(name) > 140:
                    raise ValueError('Nome obrigatório (até 140 caracteres).')
                when = day_value(request.form.get('exam_date'))
                minimum = number(request.form.get('min_score', '0'), 'Mínimo geral')
                target = number(request.form.get('target_percent', '70'), 'Meta percentual', 0, 100)
                with db():
                    db().execute('INSERT INTO exams(user_id,name,position,exam_date,min_score,target_percent) VALUES(?,?,?,?,?,?)', (user_id(), name, request.form.get('position', '')[:140], when, str(minimum), str(target)))
                flash('Concurso cadastrado.', 'success')
                return redirect(url_for('exams'))
            except ValueError as exc:
                flash(str(exc), 'error')
        return render_template('exams.html', exams=all_rows('SELECT * FROM exams WHERE user_id=? ORDER BY exam_date', (user_id(),)))

    @app.route('/exams/<int:exam_id>', methods=['GET', 'POST'])
    @login_required
    def exam_detail(exam_id):
        exam = exam_owned(exam_id)
        if request.method == 'POST':
            try:
                name = request.form.get('name', '').strip()
                if not name or len(name) > 140:
                    raise ValueError('Informe um nome de até 140 caracteres.')
                when = day_value(request.form.get('exam_date'))
                minimum = number(request.form.get('min_score', '0'), 'Mínimo geral')
                target = number(request.form.get('target_percent', '70'), 'Meta percentual', 0, 100)
                with db():
                    db().execute('UPDATE exams SET name=?,position=?,exam_date=?,min_score=?,target_percent=? WHERE id=?', (name, request.form.get('position', '')[:140], when, str(minimum), str(target), exam_id))
                flash('Concurso atualizado.', 'success')
                return redirect(url_for('exam_detail', exam_id=exam_id))
            except ValueError as exc:
                flash(str(exc), 'error')
        subjects = all_rows('SELECT * FROM subjects WHERE exam_id=? ORDER BY id', (exam_id,))
        return render_template('exam_detail.html', exam=exam, subjects=subjects)

    @app.post('/exams/<int:exam_id>/delete')
    @login_required
    def delete_exam(exam_id):
        exam_owned(exam_id)
        with db():
            db().execute('DELETE FROM exams WHERE id=?', (exam_id,))
        flash('Concurso e registros relacionados excluídos.', 'success')
        return redirect(url_for('exams'))

    def subject_fields():
        name = request.form.get('name', '').strip()
        if not name or len(name) > 140:
            raise ValueError('Nome da disciplina obrigatório (até 140 caracteres).')
        return (name, integer(request.form.get('questions'), 'Questões', 1), str(number(request.form.get('points'), 'Pontos por acerto', 0)), str(number(request.form.get('penalty', '0'), 'Penalidade', 0)), str(number(request.form.get('min_score', '0'), 'Mínimo por disciplina')), str(number(request.form.get('target_percent', '70'), 'Meta percentual', 0, 100)), int('nonzero' in request.form))

    @app.post('/exams/<int:exam_id>/subjects')
    @login_required
    def add_subject(exam_id):
        exam_owned(exam_id)
        try:
            fields = subject_fields()
            with db():
                db().execute('INSERT INTO subjects(exam_id,name,questions,points,penalty,min_score,target_percent,nonzero) VALUES(?,?,?,?,?,?,?,?)', (exam_id, *fields))
            flash('Disciplina cadastrada.', 'success')
        except ValueError as exc:
            flash(str(exc), 'error')
        return redirect(url_for('exam_detail', exam_id=exam_id))

    @app.route('/subjects/<int:subject_id>', methods=['GET', 'POST'])
    @login_required
    def subject_detail(subject_id):
        subj = subject_owned(subject_id)
        if request.method == 'POST':
            try:
                fields = subject_fields()
                with db():
                    db().execute('UPDATE subjects SET name=?,questions=?,points=?,penalty=?,min_score=?,target_percent=?,nonzero=? WHERE id=?', (*fields, subject_id))
                flash('Disciplina atualizada.', 'success')
                return redirect(url_for('exam_detail', exam_id=subj['exam_id']))
            except ValueError as exc:
                flash(str(exc), 'error')
        return render_template('subject.html', subj=subj)

    @app.post('/subjects/<int:subject_id>/delete')
    @login_required
    def delete_subject(subject_id):
        subj = subject_owned(subject_id)
        with db():
            db().execute('DELETE FROM subjects WHERE id=?', (subject_id,))
        flash('Disciplina excluída; sessões anteriores permanecem sem disciplina vinculada.', 'success')
        return redirect(url_for('exam_detail', exam_id=subj['exam_id']))

    @app.route('/availability', methods=['GET', 'POST'])
    @login_required
    def availability():
        if request.method == 'POST':
            try:
                action = request.form.get('action')
                if action == 'time':
                    start = valid_time(request.form.get('start'))
                    end = valid_time(request.form.get('end'))
                    if end <= start:
                        raise ValueError('O horário final deve ser maior que o inicial.')
                    days = [integer(x, 'Dia') for x in request.form.getlist('weekday')]
                    if not days or any(x > 6 for x in days):
                        raise ValueError('Selecione pelo menos um dia válido.')
                    with db():
                        for wd in set(days):
                            db().execute('INSERT INTO availability(user_id,weekday,start_time,end_time) VALUES(?,?,?,?) ON CONFLICT(user_id,weekday) DO UPDATE SET start_time=excluded.start_time,end_time=excluded.end_time', (user_id(), wd, start, end))
                elif action == 'block':
                    with db():
                        db().execute('INSERT OR IGNORE INTO blocked(user_id,day) VALUES(?,?)', (user_id(), day_value(request.form.get('day'))))
                else:
                    raise ValueError('Ação inválida.')
                flash('Disponibilidade atualizada.', 'success')
                return redirect(url_for('availability'))
            except ValueError as exc:
                flash(str(exc), 'error')
        slots = all_rows('SELECT * FROM availability WHERE user_id=? ORDER BY weekday', (user_id(),))
        blocked = all_rows('SELECT * FROM blocked WHERE user_id=? ORDER BY day', (user_id(),))
        return render_template('availability.html', slots=slots, blocked=blocked, weekdays=['Segunda','Terça','Quarta','Quinta','Sexta','Sábado','Domingo'])

    @app.post('/availability/<int:slot_id>/delete')
    @login_required
    def delete_slot(slot_id):
        with db():
            db().execute('DELETE FROM availability WHERE id=? AND user_id=?', (slot_id, user_id()))
        return redirect(url_for('availability'))

    @app.post('/blocked/<int:blocked_id>/delete')
    @login_required
    def delete_block(blocked_id):
        with db():
            db().execute('DELETE FROM blocked WHERE id=? AND user_id=?', (blocked_id, user_id()))
        return redirect(url_for('availability'))

    def overlapping_session(start_at, end_at, ignore_session_id=None):
        # Intervalos semiabertos: uma sessão que termina às 08:00 não conflita
        # com outra que começa às 08:00. Conferir TODOS os concursos do usuário.
        # Chamadas de gravação devem ocorrer sob BEGIN IMMEDIATE para evitar corrida.
        return one('''
            SELECT s.id FROM sessions AS s
            JOIN exams AS e ON e.id = s.exam_id
            WHERE e.user_id = ? AND s.start_at < ? AND s.end_at > ?
              AND (? IS NULL OR s.id <> ?)
            LIMIT 1
        ''', (user_id(), end_at, start_at, ignore_session_id, ignore_session_id))

    def generate(exam):
        subjects = all_rows('SELECT * FROM subjects WHERE exam_id=? ORDER BY id', (exam['id'],))
        if not subjects:
            raise ValueError('Cadastre ao menos uma disciplina.')
        slots = {s['weekday']: s for s in all_rows('SELECT * FROM availability WHERE user_id=?', (user_id(),))}
        if not slots:
            raise ValueError('Configure sua disponibilidade semanal.')
        blocked = {r['day'] for r in all_rows('SELECT day FROM blocked WHERE user_id=?', (user_id(),))}
        start_day = date.today()
        end_day = date.fromisoformat(exam['exam_date'])
        if end_day <= start_day:
            raise ValueError('A data da prova precisa estar no futuro.')
        # Reusar pesos positivos, inclusive quando valores de pontos forem zero.
        weights = [max(Decimal(1), Decimal(s['points']) * s['questions']) for s in subjects]
        allocated = [0] * len(subjects)
        plans = []
        current = start_day
        while current < end_day:
            if current.isoformat() not in blocked and current.weekday() in slots:
                slot = slots[current.weekday()]
                cursor = datetime.fromisoformat(current.isoformat() + 'T' + slot['start_time'])
                limit = datetime.fromisoformat(current.isoformat() + 'T' + slot['end_time'])
                if current == date.today():
                    cursor = max(cursor, datetime.now().replace(second=0, microsecond=0) + timedelta(minutes=1))
                while (limit - cursor).total_seconds() >= 25 * 60:
                    duration = min(50, int((limit - cursor).total_seconds() // 60))
                    choice = min(range(len(subjects)), key=lambda i: (Decimal(allocated[i]) / weights[i], i))
                    end = cursor + timedelta(minutes=duration)
                    plans.append((exam['id'], subjects[choice]['id'], cursor.isoformat(timespec='minutes'), end.isoformat(timespec='minutes')))
                    allocated[choice] += 1
                    cursor = end + timedelta(minutes=10)
            current += timedelta(days=1)
        if not plans:
            raise ValueError('Não há tempo disponível antes da prova para sessões de pelo menos 25 minutos.')
        return plans

    @app.route('/schedule', methods=['GET'])
    @login_required
    def schedule():
        exams = all_rows('SELECT * FROM exams WHERE user_id=? ORDER BY exam_date', (user_id(),))
        rows = all_rows('SELECT s.*,e.name AS exam_name,sub.name AS subject_name FROM sessions s JOIN exams e ON e.id=s.exam_id LEFT JOIN subjects sub ON sub.id=s.subject_id WHERE e.user_id=? ORDER BY s.start_at,s.id LIMIT 1000', (user_id(),))
        return render_template('schedule.html', exams=exams, rows=rows)

    @app.post('/schedule/generate/<int:exam_id>')
    @login_required
    def regenerate(exam_id):
        exam = exam_owned(exam_id)
        if request.form.get('confirm') != 'yes':
            abort(400, description='Confirme a substituição das sessões futuras pendentes.')
        try:
            planned = generate(exam)
            created = 0
            skipped = 0
            cutoff = datetime.now().isoformat(timespec='minutes')
            with db():
                # O lock de escrita cobre leitura de conflitos, exclusão e inserções.
                # Duas gerações/edições simultâneas não podem validar o mesmo horário.
                db().execute('BEGIN IMMEDIATE')
                # Nunca excluir sessões concluídas nem sessões iniciadas no passado.
                db().execute('DELETE FROM sessions WHERE exam_id=? AND completed=0 AND start_at>=?', (exam_id, cutoff))
                for row in planned:
                    if overlapping_session(row[2], row[3]):
                        skipped += 1
                        continue
                    db().execute('INSERT INTO sessions(exam_id,subject_id,start_at,end_at) VALUES(?,?,?,?)', row)
                    created += 1
                if not created:
                    # Sem horários livres, reverter também a remoção das pendentes.
                    raise ValueError('Não há horários livres: sessões existentes ocupam os blocos disponíveis. Nenhum registro foi alterado.')
            flash(f'Cronograma gerado: {created} sessões. {skipped} blocos ignorados por conflito de horário. Sessões concluídas preservadas.', 'success')
        except (ValueError, sqlite3.Error) as exc:
            flash(f'Não foi possível gerar: {exc}', 'error')
        return redirect(url_for('schedule'))

    @app.route('/sessions/<int:session_id>', methods=['GET', 'POST'])
    @login_required
    def session_detail(session_id):
        study = session_owned(session_id)
        subjects = all_rows('SELECT * FROM subjects WHERE exam_id=?', (study['exam_id'],))
        if request.method == 'POST':
            try:
                start = datetime.fromisoformat(request.form.get('start_at', ''))
                end = datetime.fromisoformat(request.form.get('end_at', ''))
                if start.tzinfo is not None or end.tzinfo is not None:
                    raise ValueError('Informe horários locais sem fuso horário.')
                start = start.replace(second=0, microsecond=0)
                end = end.replace(second=0, microsecond=0)
                if end <= start or (end - start) > timedelta(hours=12):
                    raise ValueError('Período inválido (máximo 12 horas).')
                subject_id = request.form.get('subject_id', '')
                if subject_id and not one('SELECT 1 FROM subjects WHERE id=? AND exam_id=?', (subject_id, study['exam_id'])):
                    raise ValueError('Disciplina inválida.')
                minutes = integer(request.form.get('actual_minutes', 0), 'Minutos realizados')
                if minutes > 1440:
                    raise ValueError('Tempo realizado inválido.')
                start_at = start.isoformat(timespec='minutes')
                end_at = end.isoformat(timespec='minutes')
                with db():
                    db().execute('BEGIN IMMEDIATE')
                    if overlapping_session(start_at, end_at, ignore_session_id=session_id):
                        raise ValueError('Este horário se sobrepõe a outra sessão sua. Escolha um período livre.')
                    db().execute('UPDATE sessions SET start_at=?,end_at=?,subject_id=?,kind=?,completed=?,actual_minutes=?,notes=? WHERE id=?', (start_at, end_at, subject_id or None, request.form.get('kind','Estudo')[:40], int('completed' in request.form), minutes, request.form.get('notes','')[:1000], session_id))
                flash('Sessão atualizada.', 'success')
                return redirect(url_for('schedule'))
            except ValueError as exc:
                flash(str(exc), 'error')
            except sqlite3.IntegrityError:
                flash('Não foi possível salvar a sessão: revise o horário.', 'error')
        return render_template('session.html', study=study, subjects=subjects)

    @app.post('/sessions/<int:session_id>/delete')
    @login_required
    def delete_session(session_id):
        session_owned(session_id)
        with db():
            db().execute('DELETE FROM sessions WHERE id=?', (session_id,))
        return redirect(url_for('schedule'))

    @app.route('/mocks', methods=['GET', 'POST'])
    @login_required
    def mocks():
        exams = all_rows('SELECT * FROM exams WHERE user_id=? ORDER BY exam_date', (user_id(),))
        rows = all_rows('SELECT m.*,e.name AS exam_name FROM mocks m JOIN exams e ON e.id=m.exam_id WHERE e.user_id=? ORDER BY m.day DESC,m.id DESC', (user_id(),))
        selected = request.args.get('exam_id', type=int) or (exams[0]['id'] if exams else None)
        subjects = []
        exam = None
        if selected:
            exam = exam_owned(selected)
            subjects = all_rows('SELECT * FROM subjects WHERE exam_id=? ORDER BY id', (selected,))
        if request.method == 'POST':
            try:
                exam = exam_owned(integer(request.form.get('exam_id'), 'Concurso', 1))
                subjects = all_rows('SELECT * FROM subjects WHERE exam_id=? ORDER BY id', (exam['id'],))
                if not subjects:
                    raise ValueError('O concurso não possui disciplinas.')
                when = day_value(request.form.get('day'))
                total = Decimal(0)
                passed = True
                target_passed = True
                results = []
                max_score = sum(Decimal(s['points']) * s['questions'] for s in subjects)
                for s in subjects:
                    sid = s['id']
                    c = integer(request.form.get(f'correct_{sid}'), 'Acertos')
                    w = integer(request.form.get(f'wrong_{sid}'), 'Erros')
                    b = integer(request.form.get(f'blank_{sid}'), 'Brancos')
                    if c + w + b != s['questions']:
                        raise ValueError(f'{s["name"]}: acertos + erros + brancos precisam ser iguais a {s["questions"]}.')
                    score = c * Decimal(s['points']) - w * Decimal(s['penalty'])
                    total += score
                    passed = passed and score >= Decimal(s['min_score']) and (not s['nonzero'] or c > 0)
                    target_score = Decimal(s['questions']) * Decimal(s['points']) * Decimal(s['target_percent']) / Decimal(100)
                    target_passed = target_passed and score >= target_score
                    results.append((s['name'], c, w, b, s['questions'], s['points'], s['penalty'], s['min_score'], s['nonzero'], s['target_percent'], str(score)))
                passed = passed and total >= Decimal(exam['min_score'])
                target_passed = target_passed and (max_score > 0 and total >= max_score * Decimal(exam['target_percent']) / Decimal(100))
                with db():
                    cur = db().execute('INSERT INTO mocks(exam_id,day,total,meets_minimum,meets_goal,min_score_snapshot,max_score_snapshot,goal_percent_snapshot) VALUES(?,?,?,?,?,?,?,?)', (exam['id'], when, str(total), int(passed), int(target_passed), exam['min_score'], str(max_score), exam['target_percent']))
                    for result in results:
                        db().execute('INSERT INTO mock_results(mock_id,subject_name,correct,wrong,blank,questions,points,penalty,minimum,nonzero,target_percent,score) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)', (cur.lastrowid, *result))
                flash('Simulado registrado. Notas históricas preservam as regras usadas.', 'success')
                return redirect(url_for('mocks'))
            except ValueError as exc:
                flash(str(exc), 'error')
        return render_template('mocks.html', exams=exams, exam=exam, subjects=subjects, rows=rows)

    @app.route('/mocks/<int:mock_id>', methods=['GET', 'POST'])
    @login_required
    def mock_detail(mock_id):
        mock = mock_owned(mock_id)
        results = all_rows('SELECT * FROM mock_results WHERE mock_id=? ORDER BY id', (mock_id,))
        if request.method == 'POST':
            try:
                when = day_value(request.form.get('day'))
                total = Decimal(0)
                meets = True
                goals = True
                changes = []
                for r in results:
                    correct = integer(request.form.get(f'correct_{r["id"]}'), 'Acertos')
                    wrong = integer(request.form.get(f'wrong_{r["id"]}'), 'Erros')
                    blank = integer(request.form.get(f'blank_{r["id"]}'), 'Brancos')
                    if correct + wrong + blank != r['questions']:
                        raise ValueError(f'{r["subject_name"]}: soma diferente do total de questões.')
                    score = correct * Decimal(r['points']) - wrong * Decimal(r['penalty'])
                    total += score
                    meets = meets and score >= Decimal(r['minimum']) and (not r['nonzero'] or correct > 0)
                    goals = goals and score >= Decimal(r['questions']) * Decimal(r['points']) * Decimal(r['target_percent']) / 100
                    changes.append((correct, wrong, blank, str(score), r['id']))
                # Preservar também o limiar geral na edição: gravado como snapshot em novo campo de schema abaixo.
                with db():
                    for values in changes:
                        db().execute('UPDATE mock_results SET correct=?,wrong=?,blank=?,score=? WHERE id=?', values)
                    db().execute('UPDATE mocks SET day=?,total=?,meets_minimum=?,meets_goal=? WHERE id=?', (when, str(total), int(meets and total >= Decimal(mock['min_score_snapshot'])), int(goals and total >= Decimal(mock['max_score_snapshot']) * Decimal(mock['goal_percent_snapshot']) / 100), mock_id))
                flash('Simulado editado usando as regras históricas.', 'success')
                return redirect(url_for('mock_detail', mock_id=mock_id))
            except ValueError as exc:
                flash(str(exc), 'error')
        return render_template('mock_detail.html', mock=mock, results=results)

    @app.post('/mocks/<int:mock_id>/delete')
    @login_required
    def delete_mock(mock_id):
        mock_owned(mock_id)
        with db():
            db().execute('DELETE FROM mocks WHERE id=?', (mock_id,))
        return redirect(url_for('mocks'))

    return app


if __name__ == '__main__':
    create_app().run(debug=False)
