"""Testes HTTP Flask de autenticação, CSRF, cookie e autorização multiusuário."""
import sqlite3

import pytest
from werkzeug.security import check_password_hash

from app import create_app
from conftest import (add_mock, future_weekday, login_as, new_exam,
                      new_subject, post, run_schedule, set_availability, token)


def test_cadastro_login_senha_hash_e_credenciais_incorretas(client, database):
    assert client.get('/').status_code == 302  # protegido
    assert post(client, '/register', {'email': 'pessoa@example.org', 'password': 'curta'}).status_code == 200
    assert database.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 0
    assert post(client, '/register', {'email': 'pessoa@example.org', 'password': 'senha_segura_123'}).status_code == 302
    row = database.execute('SELECT * FROM users').fetchone()
    assert row['email'] == 'pessoa@example.org'
    assert row['password_hash'] != 'senha_segura_123'
    assert check_password_hash(row['password_hash'], 'senha_segura_123')
    assert post(client, '/register', {'email': 'pessoa@example.org', 'password': 'senha_segura_123'}).status_code == 200
    assert database.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 1
    assert post(client, '/login', {'email': 'pessoa@example.org', 'password': 'errada'}).status_code == 200
    assert client.get('/').status_code == 302
    assert post(client, '/login', {'email': 'pessoa@example.org', 'password': 'senha_segura_123'}).status_code == 302
    assert client.get('/').status_code == 200
    assert post(client, '/logout').status_code == 302
    assert client.get('/').status_code == 302


def test_post_sem_csrf_e_rejeitado_sem_gravar(client, database):
    login_as(client)
    response = client.post('/exams', data={
        'name': 'Não deve entrar', 'exam_date': '2030-01-10',
        'min_score': '0', 'target_percent': '70'})
    assert response.status_code == 400
    assert database.execute('SELECT COUNT(*) FROM exams').fetchone()[0] == 0


def test_cookie_local_http_only_lax_e_nao_secure(client):
    response = client.get('/login')
    cookie = response.headers.get('Set-Cookie', '')
    assert 'HttpOnly' in cookie
    assert 'SameSite=Lax' in cookie
    assert 'Secure' not in cookie


def test_producao_exige_secret_key_e_cookie_seguro(monkeypatch, tmp_path):
    monkeypatch.setenv('RUMO_ENV', 'production')
    monkeypatch.delenv('SECRET_KEY', raising=False)
    monkeypatch.delenv('COOKIE_SECURE', raising=False)
    with pytest.raises(RuntimeError, match='SECRET_KEY'):
        create_app({'DATABASE': str(tmp_path / 'nao_criar.sqlite3')})
    assert not (tmp_path / 'nao_criar.sqlite3').exists()
    monkeypatch.setenv('SECRET_KEY', 'chave-de-producao-ficticia-nao-usar')
    app = create_app({'TESTING': True, 'DATABASE': str(tmp_path / 'producao_teste.sqlite3')})
    assert app.config['SECRET_KEY'] == 'chave-de-producao-ficticia-nao-usar'
    assert app.config['SESSION_COOKIE_SECURE'] is True
    response = app.test_client().get('/login')
    cookie = response.headers.get('Set-Cookie', '')
    assert 'Secure' in cookie and 'HttpOnly' in cookie and 'SameSite=Lax' in cookie


def test_escape_de_html_no_nome_de_concurso(client, database):
    login_as(client)
    name = '<script>alert("teste")</script>'
    new_exam(client, database, name)
    body = client.get('/exams').get_data(as_text=True)
    assert '&lt;script&gt;' in body
    assert name not in body


def test_usuario_b_nao_le_nem_altera_registros_de_a(app, database):
    a = app.test_client()
    b = app.test_client()
    login_as(a, 'a@example.org')
    exam_id = new_exam(a, database)
    subject_id = new_subject(a, database, exam_id)
    assert set_availability(a).status_code == 302
    assert run_schedule(a, exam_id).status_code == 302
    study = database.execute('SELECT id FROM sessions WHERE exam_id=? LIMIT 1', (exam_id,)).fetchone()
    assert study is not None
    study_id = study['id']
    assert add_mock(a, exam_id, {subject_id: (7, 3, 0)}).status_code == 302
    mock_id = database.execute('SELECT id FROM mocks WHERE exam_id=?', (exam_id,)).fetchone()['id']

    login_as(b, 'b@example.org')
    for url in (f'/exams/{exam_id}', f'/subjects/{subject_id}',
                f'/sessions/{study_id}', f'/mocks/{mock_id}',
                f'/mocks?exam_id={exam_id}'):
        assert b.get(url).status_code == 404, url
    assert post(b, f'/exams/{exam_id}/delete').status_code == 404
    assert post(b, f'/subjects/{subject_id}/delete').status_code == 404
    assert post(b, f'/sessions/{study_id}/delete').status_code == 404
    assert post(b, f'/mocks/{mock_id}/delete').status_code == 404
    assert post(b, f'/schedule/generate/{exam_id}', {'confirm': 'yes'}).status_code == 404
    assert post(b, f'/exams/{exam_id}/subjects', {'name': 'Invasão'}).status_code == 404
    assert database.execute('SELECT COUNT(*) FROM exams WHERE id=?', (exam_id,)).fetchone()[0] == 1
    assert database.execute('SELECT COUNT(*) FROM subjects WHERE id=?', (subject_id,)).fetchone()[0] == 1
    assert database.execute('SELECT COUNT(*) FROM mocks WHERE id=?', (mock_id,)).fetchone()[0] == 1
    assert database.execute('SELECT COUNT(*) FROM sessions WHERE id=?', (study_id,)).fetchone()[0] == 1
