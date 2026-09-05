"""Общие фикстуры тестов chancellery."""

from __future__ import annotations

import pytest

from chancellery.render.engine import reset_tag_warnings


@pytest.fixture(autouse=True)
def _reset_tag_warnings():
    # Дедуп предупреждений авто-фикса тегов живёт на процесс; чистим перед каждым
    # тестом, чтобы порядок тестов не влиял на caplog-проверки (T026 «Дьяка»).
    reset_tag_warnings()
