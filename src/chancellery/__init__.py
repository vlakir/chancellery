"""
Канцелярия — русское склонение и сборка служебных документов.

Библиотека умеет две вещи, нужные любому генератору русских служебных
документов: **склонять по падежам** ФИО, должности и звания (с
автоопределением рода и согласованием слов во фразе) и **собирать готовый
`docx`** по шаблону с русской разметкой, где падеж задаётся местом
подстановки, а не данными.

Три уровня, от готового сценария к слоям:

1. `generate_documents` / `reverse_template` — сценарий целиком: таблица +
   шаблон + конфиг → документы (и обратно: документ + строка → шаблон).
2. `read_table`, `build_context`, `render_document`, `check_table` — слои,
   если сценарий не подходит (источник данных не таблица, свой цикл,
   своя обработка ошибок). Ручные переопределения из конфигурации
   приводят к виду, который ждут слои, `gender_overrides`,
   `decline_surnames`, `position_overrides` и `rank_overrides`.
3. `Fio`, `Phrase`, `Rank` и склонятели — сам движок склонения, если
   документы не нужны вовсе.

**То, что перечислено в `__all__`, и есть контракт библиотеки.** Всё
остальное — внутреннее устройство, которое меняется без предупреждения.
Русские имена тегов шаблона и падежных фильтров (`{{ ФИО | дт }}`,
`{{ Фамилия }}`, `{{ Инициалы }}`) — тоже часть контракта: на них завязаны
бланки, размеченные пользователями.
"""

from __future__ import annotations

from chancellery.check import CheckReport, Issue, IssueKind, check_table
from chancellery.check import format_report as format_check_report
from chancellery.columns import normalize_header, split_fullname
from chancellery.config import CaseForms, Config, Overrides, Role, load_config
from chancellery.domain import CASE_RUS, RUS_CASE, Case, Gender, Person, Table
from chancellery.errors import (
    ChancelleryError,
    ConfigError,
    ReverseError,
    TableError,
    TemplateError,
    UndefinedVariableError,
)
from chancellery.inflection import (
    Declinable,
    Fio,
    GenderResolution,
    GenderSource,
    Initials,
    NamePart,
    PetrovichInflector,
    Phrase,
    PhraseInflector,
    Rank,
    RankInflector,
    Staff,
    StaffInflector,
    detect_gender,
    is_abbreviation,
    is_known_surname,
    lemmas,
    parse_gender,
    resolve_gender,
)
from chancellery.io.excel import read_table
from chancellery.io.naming import unique_filename
from chancellery.pipeline import (
    ProgressSink,
    decline_surnames,
    fio_overrides,
    gender_overrides,
    generate_documents,
    position_overrides,
    rank_overrides,
    reverse_template,
)
from chancellery.render.context import build_context, normalize_lookup_key
from chancellery.render.engine import (
    default_filename_template,
    render_document,
    render_filename,
    render_to_document,
    reset_tag_warnings,
)
from chancellery.reverse import Finding, FindingKind, ReverseReport, build_template
from chancellery.reverse import format_report as format_reverse_report

__all__ = [
    'CASE_RUS',
    'RUS_CASE',
    'Case',
    'CaseForms',
    'ChancelleryError',
    'CheckReport',
    'Config',
    'ConfigError',
    'Declinable',
    'Finding',
    'FindingKind',
    'Fio',
    'Gender',
    'GenderResolution',
    'GenderSource',
    'Initials',
    'Issue',
    'IssueKind',
    'NamePart',
    'Overrides',
    'Person',
    'PetrovichInflector',
    'Phrase',
    'PhraseInflector',
    'ProgressSink',
    'Rank',
    'RankInflector',
    'ReverseError',
    'ReverseReport',
    'Role',
    'Staff',
    'StaffInflector',
    'Table',
    'TableError',
    'TemplateError',
    'UndefinedVariableError',
    'build_context',
    'build_template',
    'check_table',
    'decline_surnames',
    'default_filename_template',
    'detect_gender',
    'fio_overrides',
    'format_check_report',
    'format_reverse_report',
    'gender_overrides',
    'generate_documents',
    'is_abbreviation',
    'is_known_surname',
    'lemmas',
    'load_config',
    'normalize_header',
    'normalize_lookup_key',
    'parse_gender',
    'position_overrides',
    'rank_overrides',
    'read_table',
    'render_document',
    'render_filename',
    'render_to_document',
    'reset_tag_warnings',
    'resolve_gender',
    'reverse_template',
    'split_fullname',
    'unique_filename',
]
