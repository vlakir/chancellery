"""
Ручные формы ФИО (`overrides.fio`).

Секция была объявлена в схеме конфигурации и описана пользователю в
scaffold-конфиге «Дьяка», но к сборке контекста подключена не была:
заданные вручную формы молча игнорировались (T002, в «Дьяке» — T028).
Здесь проверяется и сам приоритет, и то, ради чего задача заводилась —
что форма из конфигурации доезжает до готового документа.

Случай взят такой, где движок заведомо даёт ДРУГОЕ: «Бивень» — фамилия-
нарицательное, которую движок по умолчанию оставляет в именительном
(«Бивень Ивану Петровичу»), а кадровик хочет «Бивеню Ивану Петровичу».
Каждый тест сверх ожидаемого результата проверяет, что машинная форма
отличается от ручной, — иначе он был бы зелёным и до починки.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import yaml
from docx import Document
from openpyxl import Workbook

from chancellery import (
    Case,
    Person,
    PetrovichInflector,
    build_context,
    generate_documents,
)

if TYPE_CHECKING:
    from pathlib import Path

_FIO = 'Бивень Иван Петрович'
_KEY = 'бивень иван петрович'
_MANUAL_DATV = 'Бивеню Ивану Петровичу'
_ROLES = {'surname': 'Фамилия', 'name': 'Имя', 'patronymic': 'Отчество'}
_CELLS = {'Фамилия': 'Бивень', 'Имя': 'Иван', 'Отчество': 'Петрович'}


def _context(overrides: dict[str, dict[str, str]]) -> dict[str, object]:
    return build_context(
        Person(cells=dict(_CELLS)),
        roles=dict(_ROLES),
        inflector=PetrovichInflector(),
        fio_overrides=overrides,
    )


def test_manual_form_wins_over_engine() -> None:
    """Заданная вручную форма подставляется вместо машинной."""
    machine = _context({})['ФИО'].inflect(Case.DATV)
    assert machine != _MANUAL_DATV, 'случай выбран неудачно: движок даёт то же самое'

    context = _context({_KEY: {'дт': _MANUAL_DATV}})
    assert context['ФИО'].inflect(Case.DATV) == _MANUAL_DATV


def test_unset_cases_fall_back_to_engine() -> None:
    """Задавать все падежи не обязательно — остальные берёт движок."""
    context = _context({_KEY: {'дт': _MANUAL_DATV}})
    machine = _context({})['ФИО'].inflect(Case.GENT)
    assert context['ФИО'].inflect(Case.GENT) == machine


def test_key_is_normalized() -> None:
    """
    Ключ ищется нормализованным — регистр и лишние пробелы не мешают.

    Нормализацию делает `fio_overrides` из `pipeline` (нижний регистр,
    схлопнутые пробелы); здесь проверяется, что искомый ключ собирается
    из ячеек в том же виде.
    """
    manual = 'Бивенем Иваном Петровичем'
    assert _context({})['ФИО'].inflect(Case.ABLT) != manual

    context = build_context(
        Person(cells={'Фамилия': ' Бивень ', 'Имя': 'Иван', 'Отчество': 'Петрович'}),
        roles=dict(_ROLES),
        inflector=PetrovichInflector(),
        fio_overrides={_KEY: {'тв': manual}},
    )
    assert context['ФИО'].inflect(Case.ABLT) == manual


def test_parts_and_initials_stay_with_engine() -> None:
    """
    Override целого ФИО не задаёт форм частей и инициалов.

    Ключ конфигурации — ФИО целиком, разобрать готовую форму обратно на
    фамилию, имя и отчество нельзя. Поведение задокументировано в README.
    """
    context = _context({_KEY: {'дт': _MANUAL_DATV}})
    machine = _context({})
    assert context['Фамилия'].inflect(Case.DATV) == machine['Фамилия'].inflect(
        Case.DATV
    )
    assert context['Инициалы'].inflect(Case.DATV) == machine['Инициалы'].inflect(
        Case.DATV
    )


def test_without_overrides_nothing_changes() -> None:
    """Пустая секция ничего не меняет — поведение прежних версий."""
    plain = build_context(
        Person(cells=dict(_CELLS)),
        roles=dict(_ROLES),
        inflector=PetrovichInflector(),
    )
    assert _context({})['ФИО'].inflect(Case.DATV) == plain['ФИО'].inflect(Case.DATV)


def test_override_reaches_generated_document(tmp_path: Path) -> None:
    """
    Сквозная проверка: форма из `overrides.fio` доезжает до документа.

    Ровно то, что было сломано: поле разбиралось схемой, но до сборки
    контекста не доходило, и документ получал машинную форму.
    """
    wb = Workbook()
    ws = wb.active
    ws.append(['Фамилия', 'Имя', 'Отчество'])
    ws.append(['Бивень', 'Иван', 'Петрович'])
    table = tmp_path / 'people.xlsx'
    wb.save(str(table))

    template = tmp_path / 'tpl.docx'
    document = Document()
    document.add_paragraph('Выдать {{ ФИО | дт }} под роспись.')
    document.save(str(template))

    config = tmp_path / 'config.yaml'
    config.write_text(
        yaml.safe_dump(
            {'overrides': {'fio': {_FIO: {'дт': _MANUAL_DATV}}}},
            allow_unicode=True,
        ),
        encoding='utf-8',
    )

    written = generate_documents(
        table, template, tmp_path / 'out', config=config, filename='doc.docx'
    )
    body = '\n'.join(p.text for p in Document(str(written[0])).paragraphs)
    assert body == f'Выдать {_MANUAL_DATV} под роспись.'

    # Негативный контроль: без конфигурации в документе стоит машинная форма,
    # то есть тест падал бы на неподключённом поле.
    plain = generate_documents(
        table, template, tmp_path / 'plain', filename='doc.docx'
    )
    plain_body = '\n'.join(p.text for p in Document(str(plain[0])).paragraphs)
    assert plain_body == 'Выдать Бивень Ивану Петровичу под роспись.'
