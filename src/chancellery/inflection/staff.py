"""
Склонение штатных формулировок (T007, заказ «Летописи»).

Штатная формулировка — строка из штатного расписания: должность
(«Старший оператор», «Заместитель командира полка по военно-политической
работе») или подразделение («1 рота ПРТД БпС», «Войсковая часть 12345»).
От произвольной фразы (`PhraseInflector`) она отличается тем, что вокруг
головы стоят не обычные слова, а шифры, сокращения и номера, которые
склонять нельзя ни при каких обстоятельствах.

Почему отдельный движок, а не режим `PhraseInflector`: правила выбора
головы у них несовместимы, а на поведении фраз-движка стоит регрессия
«Дьяка» (эталон 0.3.3, сверка поабзацно). Объединять их — отдельная
задача с обеими приёмками сразу.

Правило, в порядке применения:

1. **Голова** — первое слово с разбором `NOUN` в именительном
   единственном, у которого НЕТ разбора `ADJF` ни в одном из вариантов.
   Проверять только первый разбор нельзя: у «старший» он существительное,
   и наивный алгоритм дал бы «старшего оператор».
2. **Склоняются** голова и стоящие левее неё согласованные определения
   (`ADJF` в именительном). В винительном определения согласуются с
   головой по одушевлённости: «старшего оператора», но «отдельный полк».
3. **Правее головы — символ в символ**: родительный хвост, шифры,
   номера. Меняется только регистр (см. 5).
4. **Аббревиатура узнаётся в лицо** и не склоняется и не понижается:
   латиница (`FPV`, `КТ-У`), смешанный регистр внутри слова (`БпС`,
   `Северо-Восточного`), кричащий капс без известного словарю слова
   длиной от четырёх букв (`ПРТД`, `БПЛА`, `ТЯЖ`, `ДМ`).
5. **Кричащий капс гасится** — кадровик пишет штатку заглавными
   («ОТДЕЛЕНИЕ СВЯЗИ» → «отделения связи»). Слово с одной заглавной в
   начале не трогается: это часть наименования («Южного военного
   округа»).
6. **`ё` не навязывается**: если в исходном слове его нет, в склонённом
   «ё» заменяется на «е» («Инженерно-саперная» → «инженерно-саперной»,
   хотя словарная форма — «сапёрный»).
7. **Фраза без опознанной головы** возвращается как есть, с понижением
   капса обычных слов: «упр» → «упр», «ГБУ» → «ГБУ».
"""

from __future__ import annotations

import functools
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from chancellery.domain import CASE_RUS, Case
from chancellery.inflection.morph import get_analyzer

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pymorphy3.analyzer import Parse

# Знаки, обрамляющие слово: в разборе не участвуют, в выводе сохраняются.
_EDGE_SYMBOLS = '()«»[]",.;:\'’“”'
# Разбиение фразы на слова с сохранением пробелов.
_SPACES = re.compile(r'(\s+)')
# Буквенные части слова (для капса вида «ТЕХ.ОБЕСПЕЧЕНИЯ», «Р-У»).
_LETTERS = re.compile(r'[^\W\d_]+', re.UNICODE)
_LATIN = re.compile(r'[A-Za-z]')
# Капс считается словом, а не сокращением, начиная с этой длины — и только
# если словарь такую лексему знает. «ПРТД» словарю неизвестно (морфология
# лишь угадывает по суффиксу), «РОТА» известно.
_MIN_WORD_LETTERS = 4


def _analyzer_parse(word: str) -> list[Parse]:
    """Разборы слова (кеш на процесс: морфология тяжело создаётся)."""
    return get_analyzer().parse(word)


@functools.lru_cache(maxsize=4096)
def is_abbreviation(word: str) -> bool:
    """
    Опознать сокращение, которое нельзя ни склонять, ни понижать.

    Латиница (`FPV`), смешанный регистр внутри слова (`БпС`,
    `Северо-Восточного`) и кричащий капс, за которым не стоит известного
    словарю слова длиной от четырёх букв (`ПРТД`, `ТЯЖ`, `ДМ`, `Р-У`).
    """
    core = word.strip(_EDGE_SYMBOLS)
    if not core or not _LETTERS.search(core):
        return False
    if _LATIN.search(core):
        return True
    if any(char.isupper() for char in core[1:]) and not core.isupper():
        return True  # БпС, БпЛА, Северо-Восточного — писано так намеренно
    if not core.isupper():
        return False
    # Капс: слово, если хотя бы одна его буквенная часть — известная
    # словарю лексема длиной от четырёх букв («ТЕХ.ОБЕСПЕЧЕНИЯ» → часть
    # «ОБЕСПЕЧЕНИЯ»); иначе сокращение.
    return not any(
        len(part) >= _MIN_WORD_LETTERS and _analyzer_parse(part.lower())[0].is_known
        for part in _LETTERS.findall(core)
    )


def _unshout(word: str) -> str:
    """Погасить капс обычного слова; сокращения и имена не трогать."""
    if is_abbreviation(word):
        return word
    core = word.strip(_EDGE_SYMBOLS)
    # Понижаем только кричащее слово целиком заглавными: одна заглавная в
    # начале — часть наименования («Южного военного округа»), её сохраняем.
    return word.lower() if core.isupper() else word


def _keep_yo(source: str, inflected: str) -> str:
    """Не навязывать «ё», если в исходном слове его не было."""
    if 'ё' in source.lower():
        return inflected
    return inflected.replace('ё', 'е').replace('Ё', 'Е')


@dataclass(frozen=True, slots=True)
class _Word:
    """Слово фразы: ядро для разбора плюс обрамляющие знаки."""

    prefix: str
    core: str
    suffix: str

    @classmethod
    def split(cls, token: str) -> _Word:
        core = token.strip(_EDGE_SYMBOLS)
        if not core:
            return cls('', token, '')
        start = token.index(core)
        return cls(token[:start], core, token[start + len(core) :])

    def with_core(self, core: str) -> str:
        return f'{self.prefix}{core}{self.suffix}'


def _is_head(word: str) -> bool:
    """Голова: существительное в им. ед., ни в одном разборе не ADJF."""
    parses = _analyzer_parse(word)
    if any(parse.tag.POS == 'ADJF' for parse in parses):
        return False
    return any(
        parse.tag.POS == 'NOUN'
        and parse.tag.case == 'nomn'
        and parse.tag.number == 'sing'
        for parse in parses
    )


def _is_noun_nomn(word: str) -> bool:
    """Запасной признак головы, когда слов без ADJF-разбора не нашлось."""
    return any(
        parse.tag.POS == 'NOUN'
        and parse.tag.case == 'nomn'
        and parse.tag.number == 'sing'
        for parse in _analyzer_parse(word)
    )


def _head_parse(word: str) -> Parse | None:
    """Разбор головы: существительное в именительном единственном."""
    for parse in _analyzer_parse(word):
        if (
            parse.tag.POS == 'NOUN'
            and parse.tag.case == 'nomn'
            and parse.tag.number == 'sing'
        ):
            return parse
    return None


def _adjective_parse(word: str) -> Parse | None:
    """Разбор согласованного определения: прилагательное в именительном."""
    for parse in _analyzer_parse(word):
        if parse.tag.POS == 'ADJF' and parse.tag.case == 'nomn':
            return parse
    return None


def _find_head(words: list[_Word]) -> int | None:
    """Индекс головы среди слов фразы (сокращения головой не бывают)."""
    candidates = [
        index
        for index, word in enumerate(words)
        if word.core and not is_abbreviation(word.core)
    ]
    for index in candidates:
        if _is_head(words[index].core.lower()):
            return index
    for index in candidates:
        if _is_noun_nomn(words[index].core.lower()):
            return index
    return None


def _inflect_parse(parse: Parse, case: Case, grammemes: set[str]) -> str | None:
    """Просклонять разбор к падежу; None, если форма не образуется."""
    inflected = parse.inflect({case.value, *grammemes})
    return inflected.word if inflected is not None else None


def _decline_staff(text: str, case: Case) -> str:
    """Просклонять штатную формулировку к падежу `case`."""
    tokens = _SPACES.split(text)
    words = [_Word.split(token) for token in tokens]
    head = _find_head(words)

    if head is None:
        # Головы нет: только гасим капс обычных слов («упр», «ГБУ»).
        return ''.join(
            word.with_core(_unshout(word.core))
            for token, word in zip(tokens, words, strict=True)
        )

    head_parse = _head_parse(words[head].core.lower())
    animacy = head_parse.tag.animacy if head_parse is not None else None

    result: list[str] = []
    for index, (token, word) in enumerate(zip(tokens, words, strict=True)):
        if not word.core or is_abbreviation(word.core):
            result.append(token)
            continue
        lowered = word.core.lower()
        if index == head and head_parse is not None:
            form = _inflect_parse(head_parse, case, set())
            result.append(word.with_core(_keep_yo(word.core, form or lowered)))
            continue
        if index < head:
            adjective = _adjective_parse(lowered)
            if adjective is not None:
                # В винительном определение согласуется с головой по
                # одушевлённости: «старшего оператора», но «отдельный полк».
                # Только там, где форма без грамматемы неоднозначна, — в
                # мужском роде единственного числа и во множественном;
                # у женского рода «accs+inan» даёт чужую форму.
                ambiguous = adjective.tag.number == 'plur' or (
                    adjective.tag.gender == 'masc' and adjective.tag.number == 'sing'
                )
                grammemes = (
                    {animacy} if case is Case.ACCS and animacy and ambiguous else set()
                )
                form = _inflect_parse(adjective, case, grammemes)
                result.append(word.with_core(_keep_yo(word.core, form or lowered)))
                continue
        result.append(word.with_core(_unshout(word.core)))
    return ''.join(result)


def lemmas(text: str) -> tuple[str, ...]:
    """
    Нормальные формы слов фразы (первый разбор); неразобранные пропущены.

    Нужна потребителю, который ищет фразы по смыслу, а не по написанию:
    «2 роты БпЛА Р-У» и «РОТА FPV КТ» обе содержат «рота».
    """
    found: list[str] = []
    for token in text.split():
        core = token.strip(_EDGE_SYMBOLS)
        if not core or not _LETTERS.search(core):
            continue
        parse = _analyzer_parse(core.lower())[0]
        if parse.is_known:
            found.append(parse.normal_form)
    return tuple(found)


class StaffInflector:
    """Склонение штатной формулировки: голова + определения, хвост заморожен."""

    def inflect(self, text: str, case: Case) -> str:
        """Просклонять `text` к `case`; именительный отдаётся как есть."""
        if not text:
            return text
        if case is Case.NOMN:
            return text
        return _decline_staff(text, case)


@dataclass(frozen=True, slots=True)
class Staff:
    """Склоняемая штатная формулировка: ручной override с приоритетом."""

    text: str
    inflector: StaffInflector
    # Ручные формы для ЭТОГО текста: русское сокращение падежа → форма.
    overrides: Mapping[str, str] = field(default_factory=dict)

    def inflect(self, case: Case) -> str:
        """Форма в падеже `case`: override → движок."""
        override = self.overrides.get(CASE_RUS[case])
        if override is not None:
            return override
        return self.inflector.inflect(self.text, case)

    def __str__(self) -> str:
        return self.text
