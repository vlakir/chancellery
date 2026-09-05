"""Доменные исключения chancellery."""

from __future__ import annotations


class ChancelleryError(Exception):
    """Базовое исключение chancellery — все ожидаемые ошибки наследуют его."""


class ConfigError(ChancelleryError):
    """Ошибка конфигурации (YAML-файл ручных переопределений)."""


class TableError(ChancelleryError):
    """Ошибка чтения/валидации входной таблицы."""


class TemplateError(ChancelleryError):
    """Ошибка рендера шаблона (базовая): напр. неприменимый фильтр."""


class UndefinedVariableError(TemplateError):
    """Шаблон ссылается на неизвестную переменную (`StrictUndefined`)."""


class ReverseError(ChancelleryError):
    """Ошибка обратной сборки шаблона: образец-документ не читается."""
