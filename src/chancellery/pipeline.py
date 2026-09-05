"""
Высокоуровневый сценарий: таблица + шаблон + конфиг → документы.

Слой поверх `io.excel`, `config`, `render` и `reverse`, собирающий обвязку,
которую иначе пишет каждый потребитель: прочитать таблицу, нормализовать
ручные переопределения конфига, построить контекст на каждую строку,
дать файлам неконфликтующие имена и записать документы.

Код переехал из `cli.py` «Дьяка» 0.3.3 (T001) без правок логики. Там он был
сплетён с прогресс-баром на `rich`; здесь ход работы отдаётся через порт
`ProgressSink`, поэтому ни `rich`, ни любая другая обвязка терминала в
зависимости библиотеки не попадает, а потребитель волен показывать
прогресс, как ему свойственно — полосой в консоли, окном или никак.

Построчной обработки ошибок здесь **нет**: одна упавшая строка роняет весь
прогон. Это поведение «Дьяка», перенесённое как есть; менять его — отдельная
задача, а не побочный эффект переезда.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Protocol, Self

from chancellery.config import load_config
from chancellery.errors import ReverseError
from chancellery.inflection import (
    PetrovichInflector,
    PhraseInflector,
    RankInflector,
    parse_gender,
)
from chancellery.io.excel import read_table
from chancellery.io.naming import unique_filename
from chancellery.render.context import build_context, normalize_lookup_key
from chancellery.render.engine import (
    default_filename_template,
    render_document,
    render_filename,
    reset_tag_warnings,
)
from chancellery.reverse import build_template

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path
    from types import TracebackType

    from chancellery.config import CaseForms, Config
    from chancellery.domain import Gender
    from chancellery.reverse import ReverseReport

logger = logging.getLogger(__name__)


class ProgressSink(Protocol):
    """
    Порт индикатора хода работы: контекст-менеджер со счётчиком документов.

    Библиотека не знает, как потребитель показывает прогресс, но знает две
    вещи, которых нет у потребителя: сколько всего строк в таблице (это
    выясняется уже внутри `generate_documents`) и под каким **именем** лёг
    очередной документ (имя выдаёт `unique_filename`, снаружи его не
    собрать). Поэтому объект создаётся фабрикой от общего числа строк, а
    `advance` получает готовое имя файла.

    Вход в контекст-менеджер отмечает начало прогона, выход — завершение;
    выход с исключением обязан пропустить его дальше, а не подавить.
    """

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    def advance(self, file: str) -> None: ...


class _NullSink:
    """Заглушка порта: потребитель прогресс не заказывал."""

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return

    def advance(self, file: str) -> None:
        del file


def _null_sink(total: int) -> ProgressSink:
    """Фабрика заглушки: число строк никому не показывается."""
    del total
    return _NullSink()


def gender_overrides(cfg: Config) -> dict[str, Gender]:
    """Нормализовать секцию `genders` конфига в `ключ ФИО → Gender`."""
    result: dict[str, Gender] = {}
    for raw_name, raw_value in cfg.genders.items():
        gender = parse_gender(raw_value)
        if gender is not None:
            result[normalize_lookup_key(raw_name)] = gender
        else:
            logger.warning(
                'Неизвестное значение пола «%s» для «%s» в секции `genders` — '
                'игнорирую (ожидается м/ж/муж/жен/male/female)',
                raw_value,
                raw_name,
            )
    return result


def decline_surnames(cfg: Config) -> set[str]:
    """Нормализовать `decline_surnames` в множество ключей."""
    return {normalize_lookup_key(surname) for surname in cfg.decline_surnames}


def position_overrides(cfg: Config) -> dict[str, CaseForms]:
    """Нормализовать `overrides.position` в `ключ должности → падежные формы`."""
    return {
        normalize_lookup_key(text): forms
        for text, forms in cfg.overrides.position.items()
    }


def rank_overrides(cfg: Config) -> dict[str, CaseForms]:
    """Нормализовать `overrides.rank` в `ключ звания → падежные формы`."""
    return {
        normalize_lookup_key(text): forms for text, forms in cfg.overrides.rank.items()
    }


def generate_documents(
    table: Path,
    template: Path,
    out: Path,
    *,
    config: Path | None = None,
    sheet: str | None = None,
    filename: str | None = None,
    progress_factory: Callable[[int], ProgressSink] | None = None,
) -> list[Path]:
    """Сгенерировать по документу на строку таблицы. Вернуть пути файлов."""
    reset_tag_warnings()  # предупреждения авто-фикса тегов — раз на тег за прогон
    cfg = load_config(config)
    data = read_table(table, cfg, sheet)
    out.mkdir(parents=True, exist_ok=True)

    name_template = filename or default_filename_template(data.roles)
    if name_template is None:
        logger.warning(
            'Не заданы filename и не распознаны колонки ФИО — '
            'имена файлов будут порядковыми (Документ_N.docx)',
        )

    inflector = PetrovichInflector()
    position_inflector = PhraseInflector()
    rank_inflector = RankInflector()
    genders = gender_overrides(cfg)
    surnames = decline_surnames(cfg)
    positions = position_overrides(cfg)
    ranks = rank_overrides(cfg)
    used: set[str] = set()
    written: list[Path] = []
    make_progress = progress_factory or _null_sink
    with make_progress(len(data.people)) as progress:
        for line, person in enumerate(data.people, start=1):
            context = build_context(
                person,
                fullname_source=data.fullname_source,
                roles=data.roles,
                inflector=inflector,
                gender_overrides=genders,
                decline_surnames=surnames,
                position_inflector=position_inflector,
                position_overrides=positions,
                rank_inflector=rank_inflector,
                rank_overrides=ranks,
            )
            base = (
                f'Документ_{line}.docx'
                if name_template is None
                else render_filename(name_template, context)
            )
            name = unique_filename(base, used)
            target = out / name
            render_document(template, context, target)
            written.append(target)
            progress.advance(name)

    logger.info('Сгенерировано документов: %d → %s', len(written), out)
    return written


def reverse_template(
    doc: Path,
    table: Path,
    out: Path,
    row: int,
    *,
    config: Path | None = None,
    sheet: str | None = None,
) -> ReverseReport:
    """Построить шаблон из образца и строки `row` (1-based); сохранить в `out`."""
    reset_tag_warnings()
    cfg = load_config(config)
    data = read_table(table, cfg, sheet)
    total = len(data.people)
    if not 1 <= row <= total:
        msg = f'Строка {row} вне диапазона (строк данных в таблице: {total})'
        raise ReverseError(msg)
    document, report = build_template(
        doc,
        data.people[row - 1],
        fullname_source=data.fullname_source,
        roles=data.roles,
        inflector=PetrovichInflector(),
        gender_overrides=gender_overrides(cfg),
        decline_surnames=decline_surnames(cfg),
        position_inflector=PhraseInflector(),
        position_overrides=position_overrides(cfg),
        rank_inflector=RankInflector(),
        rank_overrides=rank_overrides(cfg),
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    document.save(str(out))
    logger.info('Шаблон собран из строки %d → %s', row, out)
    return report
