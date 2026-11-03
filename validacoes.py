"""Validações puras compartilhadas pelas rotas do Rumo.

Extraídas sem alterações de lógica do módulo app.py (Prompt 2).
"""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation


def number(value, title, min_value=None, max_value=None):
    try:
        result = Decimal(str(value).replace(',', '.'))
    except (InvalidOperation, ValueError):
        raise ValueError(f'{title}: número inválido')
    if not result.is_finite() or (min_value is not None and result < min_value) or (max_value is not None and result > max_value):
        raise ValueError(f'{title}: valor fora dos limites')
    return result

def integer(value, title, minimum=0):
    try:
        n = int(value)
    except (ValueError, TypeError):
        raise ValueError(f'{title}: informe um número inteiro')
    if n < minimum:
        raise ValueError(f'{title}: valor inválido')
    return n

def day_value(value):
    try:
        return date.fromisoformat(value).isoformat()
    except (ValueError, TypeError):
        raise ValueError('Data inválida')

def valid_time(s):
    try:
        return datetime.strptime(s, '%H:%M').strftime('%H:%M')
    except (TypeError, ValueError):
        raise ValueError('Horário inválido (HH:MM).')
