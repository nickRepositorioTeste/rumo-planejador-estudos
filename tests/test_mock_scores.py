"""Notas Decimal, penalidade, validação, comparação com metas e snapshot."""
from datetime import date

from conftest import add_mock, login_as, new_exam, new_subject, post


def test_simulado_penalidade_brancos_e_precisao_decimal(client, database):
    login_as(client)
    eid = new_exam(client, database, min_score='0', target_percent='30')
    sid = new_subject(client, database, eid, questions='10', points='2', penalty='0.5')
    assert add_mock(client, eid, {sid: (7, 2, 1)}).status_code == 302
    row = database.execute('SELECT * FROM mocks WHERE exam_id=?', (eid,)).fetchone()
    assert row is not None
    assert row['total'] == '13.0'  # 7*2 - 2*0.5
    assert row['meets_minimum'] == 1
    r = database.execute('SELECT * FROM mock_results WHERE mock_id=?', (row['id'],)).fetchone()
    assert (r['correct'], r['wrong'], r['blank'], r['score']) == (7, 2, 1, '13.0')


def test_nota_negativa_nao_e_truncada(client, database):
    login_as(client)
    eid = new_exam(client, database)
    sid = new_subject(client, database, eid, questions='10', points='1', penalty='1')
    add_mock(client, eid, {sid: (2, 8, 0)})
    assert database.execute('SELECT total FROM mocks').fetchone()['total'] == '-6'


def test_minimo_exigido_e_meta_pessoal_sao_independentes(client, database):
    login_as(client)
    eid = new_exam(client, database, min_score='8', target_percent='100')
    sid = new_subject(client, database, eid, questions='10', points='1',
                      min_score='8', target_percent='100')
    add_mock(client, eid, {sid: (9, 1, 0)})
    mock = database.execute('SELECT * FROM mocks').fetchone()
    assert mock['total'] == '9'
    assert mock['meets_minimum'] == 1
    assert mock['meets_goal'] == 0
    displayed = client.get('/mocks').get_data(as_text=True)
    assert 'Atingidos' in displayed
    assert 'Não atingida' in displayed


def test_simulado_invalido_nao_persiste_nenhuma_linha(client, database):
    login_as(client)
    eid = new_exam(client, database)
    first = new_subject(client, database, eid, name='Português', questions='10')
    second = new_subject(client, database, eid, name='Matemática', questions='5')
    response = add_mock(client, eid, {first: (7, 3, 0), second: (6, 0, 0)})
    assert response.status_code == 200
    assert database.execute('SELECT COUNT(*) FROM mocks').fetchone()[0] == 0
    assert database.execute('SELECT COUNT(*) FROM mock_results').fetchone()[0] == 0
    response = add_mock(client, eid, {first: (-1, 11, 0), second: (3, 2, 0)})
    assert response.status_code == 200
    assert database.execute('SELECT COUNT(*) FROM mocks').fetchone()[0] == 0


def test_snapshot_conserva_nota_antiga_e_edicao_usa_regras_antigas(client, database):
    login_as(client)
    eid = new_exam(client, database, min_score='3', target_percent='70')
    sid = new_subject(client, database, eid, name='Direito', questions='10',
                      points='2', penalty='1', min_score='3', target_percent='70')
    assert add_mock(client, eid, {sid: (6, 4, 0)}).status_code == 302
    old = database.execute('SELECT * FROM mocks').fetchone()
    mock_id = old['id']
    assert old['total'] == '8'
    assert post(client, f'/subjects/{sid}', {
        'name': 'Direito', 'questions': '10', 'points': '100',
        'penalty': '0', 'min_score': '100', 'target_percent': '100',
    }).status_code == 302
    assert post(client, f'/exams/{eid}', {
        'name': 'Mudou regra', 'position': '',
        'exam_date': database.execute('SELECT exam_date FROM exams WHERE id=?', (eid,)).fetchone()[0],
        'min_score': '999', 'target_percent': '100',
    }).status_code == 302
    assert database.execute('SELECT total FROM mocks WHERE id=?', (mock_id,)).fetchone()[0] == '8'
    r = database.execute('SELECT * FROM mock_results WHERE mock_id=?', (mock_id,)).fetchone()
    assert r['points'] == '2' and r['penalty'] == '1'
    response = post(client, f'/mocks/{mock_id}', {
        'day': date.today().isoformat(), f'correct_{r["id"]}': '7',
        f'wrong_{r["id"]}': '3', f'blank_{r["id"]}': '0',
    })
    assert response.status_code == 302
    assert database.execute('SELECT total FROM mocks WHERE id=?', (mock_id,)).fetchone()[0] == '11'
    assert post(client, f'/mocks/{mock_id}/delete').status_code == 302
    assert database.execute('SELECT COUNT(*) FROM mocks').fetchone()[0] == 0
    assert database.execute('SELECT COUNT(*) FROM mock_results').fetchone()[0] == 0
