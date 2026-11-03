"""Verificação isolada da correção 01, sem instalar Flask.

Executa as funções verdadeiras, extraídas via AST de app.py, com substitutos
apenas para request/flash/redirect e conexões SQLite temporárias. Isto NÃO é
um teste de integração HTTP/Flask, nem substitui a etapa do Prompt 3.

Comando (na raiz do projeto):
    python docs/evidencias/verificar_correcao_01.py
"""
import ast
import sqlite3
import tempfile
import threading
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'app.py'
module = ast.parse(SOURCE.read_text(encoding='utf-8'))
schema = next(node.value.value for node in module.body if isinstance(node, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == 'SCHEMA' for t in node.targets))
app_factory = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == 'create_app')
inner_names = ('overlapping_session', 'generate', 'regenerate', 'session_detail', 'integer')
functions = []
for node in app_factory.body:
    if isinstance(node, ast.FunctionDef) and node.name in inner_names:
        node.decorator_list = []
        functions.append(node)
assert len(functions) == len(inner_names), 'Funções esperadas não encontradas no projeto'

with tempfile.TemporaryDirectory(prefix='rumo_correcao01_') as folder:
    db_path = Path(folder) / 'isolado.sqlite3'
    setup = sqlite3.connect(db_path)
    setup.executescript(schema)
    setup.execute('INSERT INTO users (id,email,password_hash) VALUES (1,?,?),(2,?,?)',
                  ('u1@example.test', 'hash', 'u2@example.test', 'hash'))
    tomorrow = date.today() + timedelta(days=1)
    exam_day = date.today() + timedelta(days=2)
    for i, uid in [(1, 1), (2, 1), (3, 2)]:
        setup.execute('INSERT INTO exams (id,user_id,name,exam_date) VALUES (?,?,?,?)',
                      (i, uid, 'Concurso fictício', exam_day.isoformat()))
    setup.execute('INSERT INTO subjects (id,exam_id,name,questions,points,penalty,min_score,target_percent) VALUES (1,1,?,?,?,?,?,?)',
                  ('Português', 20, '1', '0', '0', '70'))
    setup.execute('INSERT INTO availability(user_id,weekday,start_time,end_time) VALUES (1,?,?,?)',
                  (tomorrow.weekday(), '08:00', '11:00'))
    def put_session(exam, start, end, completed=0):
        return setup.execute('INSERT INTO sessions(exam_id,subject_id,start_at,end_at,completed,notes) VALUES (?,NULL,?,?,?,?)',
                             (exam, f'{tomorrow.isoformat()}T{start}', f'{tomorrow.isoformat()}T{end}', completed, 'histórico')).lastrowid
    completed_id = put_session(1, '08:20', '08:40', 1)
    other_exam_id = put_session(2, '09:00', '09:50')
    other_user_id = put_session(3, '10:00', '10:50')
    pending_id = put_session(1, '10:00', '10:50')
    setup.commit()
    setup.close()

    local = threading.local()
    all_flashes = []
    req = SimpleNamespace(form={'confirm': 'yes'}, method='POST')
    def db():
        if not hasattr(local, 'conn'):
            local.conn = sqlite3.connect(db_path, timeout=10)
            local.conn.row_factory = sqlite3.Row
            local.conn.execute('PRAGMA foreign_keys = ON')
        return local.conn
    def one(sql, args=()):
        return db().execute(sql, args).fetchone()
    def all_rows(sql, args=()):
        return db().execute(sql, args).fetchall()
    def user_id():
        return 1
    def exam_owned(exam_id):
        return one('SELECT * FROM exams WHERE id=? AND user_id=1', (exam_id,))
    def session_owned(session_id):
        return one('SELECT s.* FROM sessions s JOIN exams e ON e.id=s.exam_id WHERE s.id=? AND e.user_id=1', (session_id,))
    def flash(msg, category):
        all_flashes.append((msg, category))
    def url_for(endpoint, **kwargs):
        return endpoint
    def redirect(path):
        return path
    ns = dict(db=db, one=one, all_rows=all_rows, user_id=user_id,
              exam_owned=exam_owned, session_owned=session_owned,
              request=req, flash=flash, url_for=url_for, redirect=redirect,
              render_template=lambda *args, **kwargs: 'template simulada',
              datetime=datetime, date=date, timedelta=timedelta, Decimal=Decimal,
              sqlite3=sqlite3)
    isolated = ast.Module(body=functions, type_ignores=[])
    ast.fix_missing_locations(isolated)
    exec(compile(isolated, str(SOURCE), 'exec'), ns)
    conflict = ns['overlapping_session']
    to_iso = lambda hhmm: f'{tomorrow.isoformat()}T{hhmm}'

    assert conflict(to_iso('08:00'), to_iso('08:50')) is not None
    assert conflict(to_iso('09:50'), to_iso('10:00')) is None  # limites se encostam
    assert conflict(to_iso('10:00'), to_iso('10:50'), ignore_session_id=pending_id) is None  # só outro usuário
    print('OK: conflito parcial, limite contíguo e isolamento entre usuários')

    ns['regenerate'](1)
    assert all_flashes[-1][1] == 'success', all_flashes[-1]
    entries = all_rows('SELECT id,start_at,end_at,completed FROM sessions WHERE exam_id=1 ORDER BY start_at')
    assert len(entries) == 2 and sum(not x['completed'] for x in entries) == 1, entries
    assert next(x for x in entries if x['completed'])['id'] == completed_id
    assert next(x for x in entries if not x['completed'])['start_at'] == to_iso('10:00')
    # SQLite pode reutilizar o identificador de uma linha excluída.
    # Verificar conteúdo e contagem, não identidade de ID da pendente regenerada.
    print('OK: regeneração preserva concluída e respeita sessões de outros concursos')

    ns['regenerate'](1)
    entries_again = all_rows('SELECT id,start_at,completed FROM sessions WHERE exam_id=1')
    assert len(entries_again) == 2
    assert sum(x['completed'] for x in entries_again) == 1
    print('OK: regeneração repetida não duplica registros')

    # Duas conexões SQLite reais: verifica se o lock serializa regenerações.
    barrier = threading.Barrier(3)
    failures = []
    def concurrent_regeneration():
        try:
            barrier.wait(timeout=5)
            ns['regenerate'](1)
        except Exception as exc:
            failures.append(repr(exc))
        finally:
            if hasattr(local, 'conn'):
                local.conn.close()
                del local.conn
    threads = [threading.Thread(target=concurrent_regeneration) for _ in range(2)]
    for thread in threads:
        thread.start()
    barrier.wait(timeout=5)
    for thread in threads:
        thread.join(timeout=15)
    assert all(not thread.is_alive() for thread in threads), 'Threads não encerradas'
    assert not failures, failures
    entries_again = all_rows('SELECT id,start_at,completed FROM sessions WHERE exam_id=1')
    assert len(entries_again) == 2 and sum(x['completed'] for x in entries_again) == 1
    print('OK: duas regenerações concorrentes, em conexões independentes, sem duplicatas')

    pending = next(x for x in entries_again if not x['completed'])
    sid = pending['id']
    req.form = {
        'start_at': to_iso('09:10'), 'end_at': to_iso('09:40'),
        'subject_id': '', 'kind': 'Estudo', 'actual_minutes': '0', 'notes': 'tentar sobreposição'
    }
    ns['session_detail'](sid)
    assert all_flashes[-1][1] == 'error' and 'sobrepõe' in all_flashes[-1][0], all_flashes[-1]
    assert one('SELECT start_at FROM sessions WHERE id=?', (sid,))['start_at'] == to_iso('10:00')
    print('OK: edição com sobreposição rejeitada e horário original preservado')

    req.form.update(start_at=to_iso('09:50'), end_at=to_iso('10:20'))
    ns['session_detail'](sid)
    assert all_flashes[-1][1] == 'success', all_flashes[-1]
    assert one('SELECT start_at FROM sessions WHERE id=?', (sid,))['start_at'] == to_iso('09:50')
    print('OK: sessão adjacente é permitida (sem sobreposição)')

    # Criar cenário sem blocos livres. A transação precisa reverter a exclusão.
    db().execute('INSERT INTO sessions(exam_id,subject_id,start_at,end_at) VALUES (2,NULL,?,?)',
                 (to_iso('10:00'), to_iso('10:50')))
    db().commit()
    before = [tuple(x) for x in all_rows('SELECT id,start_at,end_at,completed FROM sessions WHERE exam_id=1 ORDER BY id')]
    req.form = {'confirm': 'yes'}
    ns['regenerate'](1)
    assert all_flashes[-1][1] == 'error' and 'Não há horários livres' in all_flashes[-1][0], all_flashes[-1]
    after = [tuple(x) for x in all_rows('SELECT id,start_at,end_at,completed FROM sessions WHERE exam_id=1 ORDER BY id')]
    assert before == after
    print('OK: geração sem horários livres reverte exclusões e conserva dados anteriores')

    db().close()

print('RESULTADO: 7 verificações isoladas concluídas sem falha (não são testes HTTP/pytest).')
