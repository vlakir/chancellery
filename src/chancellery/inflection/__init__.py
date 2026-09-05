"""
Подсистема склонения (T002+).

T002: ФИО через `petrovich` (`PetrovichInflector`, `Fio`, `NamePart`,
`Initials`) + автоопределение пола (`detect_gender`). T024: универсальный
фраз-движок (`PhraseInflector`, `Phrase`) склоняет ЛЮБУЮ текстовую колонку
(модель «склонение по умолчанию») — за тем же портом `Declinable`, общий
`MorphAnalyzer` из `morph.py`. T016 фаза B: звания (`RankInflector`, `Rank`)
— голова склоняется, генитивный хвост замирает (спец-ветка).
"""

from __future__ import annotations

from chancellery.inflection.fio import Fio, Initials, NamePart
from chancellery.inflection.gender import (
    GenderResolution,
    GenderSource,
    detect_gender,
    parse_gender,
    resolve_gender,
)
from chancellery.inflection.petrovich_fio import PetrovichInflector, is_known_surname
from chancellery.inflection.phrase import Phrase, PhraseInflector
from chancellery.inflection.ports import Declinable
from chancellery.inflection.rank import Rank, RankInflector

__all__ = [
    'Declinable',
    'Fio',
    'GenderResolution',
    'GenderSource',
    'Initials',
    'NamePart',
    'PetrovichInflector',
    'Phrase',
    'PhraseInflector',
    'Rank',
    'RankInflector',
    'detect_gender',
    'is_known_surname',
    'parse_gender',
    'resolve_gender',
]
