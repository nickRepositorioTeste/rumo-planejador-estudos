"""Fixtures: Flask real e SQLite REAL em arquivo temporário, nunca instance/."""
from datetime import date, timedelta
from contextlib import closing
import sqlite3

import pytest

from app import create_app


@pytest.fixture
def app(tmp_path, monkeypatch):
    # Impede que variáveis do servidor local contaminem a suíte.
    monkeypatch.delenv('RUMO_ENV', raising=False)
    monkeypatch.delenv('COOKIE_SECURE', raising=False)
    monkeypatch.delenv('SECRET_KEY', raising=False)
    flask_app = create_app({
        'TESTING': True,
        'DATABASE': str(tmp_path / 'teste_rumo.sqlite3'),
        'SECRET_KEY': 'secret-local-so-para-testes-automaticos',
        'SESSION_COOKIE_SECURE': False,
    })
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def database(app):
    """Permite inspecionar somente o banco temporário do próprio teste."""
    with closing(sqlite3.connect(app.config['DATABASE'])) as connection:
        connection.row_factory = sqlite3.Row
        yield connection


def token(client):
    """Obtém o CSRF real produzido pela sessão Flask."""
    with client.session_transaction() as sess:
        csrf = sess.get('csrf')
    if not csrf:
        client.get('/login')
        with client.session_transaction() as sess:
            csrf = sess['csrf']
    return csrf


def post(client, path, data=None, **kwargs):
    payload = dict(data or {})
    payload['csrf'] = token(client)
    return client.post(path, data=payload, **kwargs)


def login_as(client, email='teste@example.org', password='senha_segura_123'):
    response = post(client, '/register', {'email': email, 'password': password})
    assert response.status_code == 302
    response = post(client, '/login', {'email': email, 'password': password})
    assert response.status_code == 302
    with client.session_transaction() as sess:
        assert sess.get('uid')
        return sess['uid']


def future_weekday(weekday):
    """Próxima ocorrência estritamente futura, independente da data atual."""
    day = date.today() + timedelta(days=1)
    while day.weekday() != weekday:
        day += timedelta(days=1)
    return day


def new_exam(client, database, name='Concurso de Teste', day=None,
             min_score='0', target_percent='70'):
    day = day or future_weekday(2) + timedelta(days=1)
    response = post(client, '/exams', {
        'name': name, 'position': 'Analista de TI', 'exam_date': day.isoformat(),
        'min_score': min_score, 'target_percent': target_percent,
    })
    assert response.status_code == 302
    row = database.execute('SELECT id FROM exams WHERE name=? ORDER BY id DESC', (name,)).fetchone()
    assert row is not None
    return row['id']


def new_subject(client, database, exam_id, name='Português', questions='10',
                points='1', penalty='0', min_score='0', target_percent='70', nonzero=False):
    data = {'name': name, 'questions': questions, 'points': points,
            'penalty': penalty, 'min_score': min_score,
            'target_percent': target_percent}
    if nonzero:
        data['nonzero'] = 'on'
    response = post(client, f'/exams/{exam_id}/subjects', data)
    assert response.status_code == 302
    row = database.execute('SELECT id FROM subjects WHERE exam_id=? AND name=? ORDER BY id DESC', (exam_id, name)).fetchone()
    assert row is not None
    return row['id']


def set_availability(client, weekday=2, start='07:00', end='11:00'):
    return post(client, '/availability', {
        'action': 'time', 'weekday': str(weekday),
        'start': start, 'end': end,
    })


def run_schedule(client, exam_id):
    return post(client, f'/schedule/generate/{exam_id}', {'confirm': 'yes'})


def add_mock(client, exam_id, subject_counts, day=None):
    """subject_counts: {subject_id: (acertos, erros, brancos)}"""
    data = {'exam_id': str(exam_id), 'day': (day or date.today()).isoformat()}
    for sid, (correct, wrong, blank) in subject_counts.items():
        data.update({f'correct_{sid}': str(correct), f'wrong_{sid}': str(wrong),
                     f'blank_{sid}': str(blank)})
    return post(client, '/mocks', data)
