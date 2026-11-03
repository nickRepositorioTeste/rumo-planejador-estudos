"""CRUD, disponibilidade, geração, integridade, persistência e concorrência reais."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
import sqlite3
import threading

from conftest import (future_weekday, login_as, new_exam, new_subject,
                      post, run_schedule, set_availability)
from app import create_app


def test_crud_concurso_disciplina_e_cascata(client, database):
    login_as(client)
    eid = new_exam(client, database, name='Prova Inicial')
    sid = new_subject(client, database, eid, name='Português')
    assert 'Prova Inicial' in client.get('/exams').get_data(as_text=True)
    assert 'Português' in client.get(f'/exams/{eid}').get_data(as_text=True)
    assert post(client, f'/exams/{eid}', {
        'name': 'Prova Editada', 'position': 'TI',
        'exam_date': (future_weekday(2) + timedelta(days=1)).isoformat(),
        'min_score': '5', 'target_percent': '75',
    }).status_code == 302
    assert database.execute('SELECT name FROM exams WHERE id=?', (eid,)).fetchone()[0] == 'Prova Editada'
    assert post(client, f'/subjects/{sid}', {
        'name': 'Português Editado', 'questions': '20',
        'points': '2', 'penalty': '0.25', 'min_score': '7',
        'target_percent': '80', 'nonzero': 'on',
    }).status_code == 302
    updated = database.execute('SELECT * FROM subjects WHERE id=?', (sid,)).fetchone()
    assert (updated['name'], updated['questions'], updated['points'], updated['nonzero']) == ('Português Editado', 20, '2', 1)
    assert post(client, f'/subjects/{sid}/delete').status_code == 302
    assert database.execute('SELECT COUNT(*) FROM subjects WHERE id=?', (sid,)).fetchone()[0] == 0
    new_subject(client, database, eid, name='Matemática')
    assert post(client, f'/exams/{eid}/delete').status_code == 302
    assert database.execute('SELECT COUNT(*) FROM exams WHERE id=?', (eid,)).fetchone()[0] == 0
    assert database.execute('SELECT COUNT(*) FROM subjects WHERE exam_id=?', (eid,)).fetchone()[0] == 0


def test_erros_de_formulario_nao_persistem_parcialmente(client, database):
    login_as(client)
    assert post(client, '/exams', {
        'name': 'Data inválida', 'exam_date': '2026-99-99',
        'min_score': '0', 'target_percent': '70',
    }).status_code == 200
    assert post(client, '/exams', {
        'name': 'Percentual inválido', 'exam_date': '2030-01-01',
        'min_score': '0', 'target_percent': '150',
    }).status_code == 200
    assert database.execute('SELECT COUNT(*) FROM exams').fetchone()[0] == 0
    eid = new_exam(client, database)
    assert post(client, f'/exams/{eid}/subjects', {
        'name': 'Erro', 'questions': '0', 'points': '1',
        'penalty': '0', 'min_score': '0', 'target_percent': '70',
    }).status_code == 302
    assert database.execute('SELECT COUNT(*) FROM subjects').fetchone()[0] == 0


def test_disponibilidade_ultima_hora_bloqueios_e_edicao(client, database):
    login_as(client)
    next_wed = future_weekday(2)
    eid = new_exam(client, database, day=next_wed + timedelta(days=8))
    new_subject(client, database, eid)
    assert set_availability(client, weekday=2, start='07:00', end='12:00').status_code == 302
    assert set_availability(client, weekday=2, start='07:00', end='11:00').status_code == 302
    slots = database.execute('SELECT * FROM availability').fetchall()
    assert len(slots) == 1 and slots[0]['end_time'] == '11:00'
    assert post(client, '/availability', {'action': 'block', 'day': next_wed.isoformat()}).status_code == 302
    assert run_schedule(client, eid).status_code == 302
    results = database.execute('SELECT * FROM sessions WHERE exam_id=?', (eid,)).fetchall()
    assert results, 'deve haver pelo menos outra quarta disponível'
    assert all(row['start_at'][:10] != next_wed.isoformat() for row in results)
    assert all(row['end_at'][11:] <= '11:00' for row in results)
    assert all(row['start_at'][:10] < (next_wed + timedelta(days=8)).isoformat() for row in results)


def test_fim_igual_ou_anterior_ao_inicio_e_rejeitado(client, database):
    login_as(client)
    for end in ('07:00', '06:00'):
        assert post(client, '/availability', {
            'action': 'time', 'weekday': '2', 'start': '07:00', 'end': end,
        }).status_code == 200
    assert database.execute('SELECT COUNT(*) FROM availability').fetchone()[0] == 0


def test_prova_passada_e_sem_disponibilidade_nao_geram(client, database):
    login_as(client)
    eid = new_exam(client, database)
    new_subject(client, database, eid)
    assert run_schedule(client, eid).status_code == 302
    assert database.execute('SELECT COUNT(*) FROM sessions').fetchone()[0] == 0
    previous_day = date.today() - timedelta(days=1)
    past_id = new_exam(client, database, name='Passada', day=previous_day)
    new_subject(client, database, past_id)
    set_availability(client)
    assert run_schedule(client, past_id).status_code == 302
    assert database.execute('SELECT COUNT(*) FROM sessions').fetchone()[0] == 0


def test_regenerar_nao_duplica_e_preserva_sessoes_concluidas(client, database):
    login_as(client)
    eid = new_exam(client, database)
    sid = new_subject(client, database, eid)
    set_availability(client, start='07:00', end='09:00')
    assert run_schedule(client, eid).status_code == 302
    first = [dict(row) for row in database.execute('SELECT * FROM sessions WHERE exam_id=? ORDER BY start_at', (eid,))]
    assert len(first) >= 2
    assert post(client, f'/sessions/{first[0]["id"]}', {
        'start_at': first[0]['start_at'], 'end_at': first[0]['end_at'],
        'subject_id': str(sid), 'kind': 'Estudo', 'actual_minutes': '35',
        'notes': 'Concluído com estudo real de exemplo', 'completed': 'on',
    }).status_code == 302
    assert run_schedule(client, eid).status_code == 302
    after = [dict(row) for row in database.execute('SELECT * FROM sessions WHERE exam_id=? ORDER BY start_at', (eid,))]
    completed = [x for x in after if x['completed']]
    assert len(completed) == 1
    assert completed[0]['id'] == first[0]['id']
    assert completed[0]['actual_minutes'] == 35
    assert completed[0]['notes'] == 'Concluído com estudo real de exemplo'
    assert run_schedule(client, eid).status_code == 302
    final = list(database.execute('SELECT * FROM sessions WHERE exam_id=? ORDER BY start_at', (eid,)))
    assert len(final) == len(after)
    assert len({r['start_at'] for r in final}) == len(final)
    assert all(a['end_at'] <= b['start_at'] for a,b in zip(final, final[1:]))


def test_edicao_de_sessao_com_conflito_nao_altera_dados(client, database):
    login_as(client)
    eid = new_exam(client, database)
    sid = new_subject(client, database, eid)
    set_availability(client, start='07:00', end='09:00')
    run_schedule(client, eid)
    rows = [dict(x) for x in database.execute('SELECT * FROM sessions ORDER BY start_at')]
    assert len(rows) >= 2
    other = rows[1]
    response = post(client, f'/sessions/{other["id"]}', {
        'start_at': rows[0]['start_at'], 'end_at': rows[0]['end_at'],
        'subject_id': str(sid), 'kind': 'Estudo', 'actual_minutes': '0',
    })
    assert response.status_code == 200
    persisted = database.execute('SELECT * FROM sessions WHERE id=?', (other['id'],)).fetchone()
    assert persisted['start_at'] == other['start_at']
    assert persisted['end_at'] == other['end_at']
    assert post(client, f'/sessions/{other["id"]}/delete').status_code == 302
    assert database.execute('SELECT COUNT(*) FROM sessions WHERE id=?', (other['id'],)).fetchone()[0] == 0


def test_cronogramas_de_concursos_distintos_nao_se_sobrepoem(client, database):
    login_as(client)
    first = new_exam(client, database, 'A')
    second = new_exam(client, database, 'B')
    new_subject(client, database, first)
    new_subject(client, database, second)
    set_availability(client, start='07:00', end='09:00')
    run_schedule(client, first)
    run_schedule(client, second)
    rows = list(database.execute('SELECT * FROM sessions ORDER BY start_at'))
    assert len(rows) >= 2
    assert all(a['end_at'] <= b['start_at'] for a,b in zip(rows, rows[1:]))


def test_dados_persistem_apos_reabrir_app_mesmo_banco(app, client, database):
    login_as(client)
    eid = new_exam(client, database, 'Persistente')
    second_app = create_app({'TESTING': True, 'DATABASE': app.config['DATABASE'],
                             'SECRET_KEY': 'secret-local-so-para-testes-automaticos'})
    second_client = second_app.test_client()
    assert post(second_client, '/login', {
        'email': 'teste@example.org', 'password': 'senha_segura_123'
    }).status_code == 302
    assert 'Persistente' in second_client.get('/exams').get_data(as_text=True)
    assert database.execute('SELECT COUNT(*) FROM exams WHERE id=?', (eid,)).fetchone()[0] == 1


def test_geracoes_simultaneas_com_clientes_e_conexoes_independentes(app, database):
    a = app.test_client()
    b = app.test_client()
    login_as(a, 'concorrencia@example.org')
    eid = new_exam(a, database)
    new_subject(a, database, eid)
    set_availability(a, start='07:00', end='09:00')
    assert post(b, '/login', {'email': 'concorrencia@example.org', 'password': 'senha_segura_123'}).status_code == 302
    gate = threading.Barrier(2)

    def generate_on(client):
        # Cada cliente tem sua sessão, sua requisição Flask e sua conexão SQLite.
        from conftest import token
        csrf = token(client)
        gate.wait(timeout=8)
        resp = client.post(f'/schedule/generate/{eid}', data={'csrf': csrf, 'confirm': 'yes'})
        return resp.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = [pool.submit(generate_on, x) for x in (a, b)]
        statuses = [j.result(timeout=20) for j in jobs]
    assert statuses == [302, 302]
    rows = list(database.execute('SELECT * FROM sessions ORDER BY start_at'))
    assert rows
    assert len({row['start_at'] for row in rows}) == len(rows)
    assert all(left['end_at'] <= right['start_at'] for left, right in zip(rows, rows[1:]))
