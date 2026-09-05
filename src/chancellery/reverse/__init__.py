"""
Обратная генерация шаблона из готового документа (`chancellery reverse`, T007).

Зеркальная forward-пути подсистема: на вход — заполненный образец-docx и
строка данных, на выход — docx-шаблон с jinja-тегами `{{ Заголовок }}` плюс
отчёт о том, что заменено уверенно, а что осталось статикой. Фаза 1 —
точные (именительные) совпадения; склонение и round-trip verify — дальше.
"""

from __future__ import annotations

from chancellery.reverse.engine import build_template
from chancellery.reverse.report import (
    Finding,
    FindingKind,
    ReverseReport,
    format_report,
)

__all__ = [
    'Finding',
    'FindingKind',
    'ReverseReport',
    'build_template',
    'format_report',
]
