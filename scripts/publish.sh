#!/usr/bin/env bash
#
# Публикация «Канцелярии» на PyPI.
#
# Токены читаются из `.secrets` (файл под git-ignore). Ожидаемый формат —
# в `.secrets.example`.
#
# Использование:
#   scripts/publish.sh           # боевой PyPI (переменная PYPI_TOKEN)
#   scripts/publish.sh --test    # TestPyPI (переменная PYPI_TEST_TOKEN)
#
# Перед публикацией скрипт сам гоняет четыре гейта проекта: выложить в
# индекс версию, не прошедшую проверки, нельзя — выпуск с PyPI не
# отзывается, номер версии сгорает навсегда.

set -euo pipefail

SECRETS_FILE=".secrets"

if [[ ! -f "$SECRETS_FILE" ]]; then
    echo "ОШИБКА: $SECRETS_FILE не найден." >&2
    echo "        Скопируйте .secrets.example в .secrets и впишите токен." >&2
    exit 1
fi

# Подхватить секреты (экспортируется всё, что объявлено в файле)
set -a
# shellcheck source=.secrets.example disable=SC1091
. "$SECRETS_FILE"
set +a

USE_TEST=false
if [[ "${1:-}" == "--test" ]]; then
    USE_TEST=true
fi

if "$USE_TEST"; then
    if [[ -z "${PYPI_TEST_TOKEN:-}" || "$PYPI_TEST_TOKEN" == "pypi-REPLACE-ME" ]]; then
        echo "ОШИБКА: PYPI_TEST_TOKEN отсутствует или не заполнен в $SECRETS_FILE" >&2
        exit 1
    fi
    TOKEN="$PYPI_TEST_TOKEN"
    PUBLISH_URL="https://test.pypi.org/legacy/"
    echo "→ Цель: TestPyPI"
else
    if [[ -z "${PYPI_TOKEN:-}" || "$PYPI_TOKEN" == "pypi-REPLACE-ME" ]]; then
        echo "ОШИБКА: PYPI_TOKEN отсутствует или не заполнен в $SECRETS_FILE" >&2
        exit 1
    fi
    TOKEN="$PYPI_TOKEN"
    PUBLISH_URL=""
    echo "→ Цель: PyPI (боевой)"
fi

VERSION=$(uv version --short)
echo "→ Версия пакета: $VERSION"

echo "→ Гейты проекта..."
uv run ruff check .
uv run ruff format --check .
uv run mypy src
scripts/pytest-guard.sh --cov=src --cov-report=term-missing --cov-fail-under=80

echo "→ Сборка колеса и архива исходников..."
rm -rf dist/
uv build

echo "→ Проверка артефактов через twine..."
uv run twine check dist/*

echo "→ Загрузка..."
if "$USE_TEST"; then
    UV_PUBLISH_TOKEN="$TOKEN" uv publish --publish-url "$PUBLISH_URL"
else
    UV_PUBLISH_TOKEN="$TOKEN" uv publish
fi

echo ""
echo "✓ Опубликовано."
if "$USE_TEST"; then
    echo ""
    echo "Проверить (TestPyPI):"
    echo "  uv pip install --index https://test.pypi.org/simple/ \\"
    echo "      --extra-index-url https://pypi.org/simple/ chancellery==$VERSION"
else
    echo ""
    echo "Проверить (индексация занимает минуту-две):"
    echo "  uv pip install chancellery==$VERSION"
fi
