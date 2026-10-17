# T011 — native rollout dreamteam 2.0.0

## Раунд и границы

2026-10-16. Исходная migration HEAD: `7749ec25b08c3b11951578bf7855be707655a0f5`;
старый main `34f5ed61e9402ae21947742b82e865916361fe0b`;
upstream `6cdecb34ce10d68400247cd6f71e48bf32e276c8`;
согласованная reconciled base `de9c3d0a73d1c55a2539b1e4bea3fe51d115a39e`.
Автор devops-native-r1 подтвердил clean HEAD этой базы до правок.
T009/T010 и удаление мёртвого Docker workflow сохранены. Max T-ID был T010.

Владелец записи T011 и methodology/config/roles/commands — devops-native-r1;
read-only purpose review — review-native-r1; интеграция и delivery — лид.
Код библиотеки, тесты, lock/pin, зависимости, CI и секреты не меняются.
Исключение, согласованное лидом: pyproject только комментарий CLAUDE→AGENTS;
настройки TOML семантически сохранены.

## Метод переноса

Установлен dreamteam 2.0.0 без upgrade/editable. Реальный initial
`dreamteam update --dry-run .` завершился **rc1** (unsupported legacy CLAUDE).
Raw output/settings/diff не записывались и не выводились; только безопасные
категории/коды. Это ручной native transfer, НЕ успешный автоматический update.
Published `https://opencode.ai/config.json` прочитан: используемые v1 поля
ещё представлены (deprecated), совместимость с OpenCode 1.19.0 сохраняется.

Private ORIGINALS вне очистки author worktree:
`/home/vlakir/.local/share/dreamteam/migration-20261016/chancellery-T011-1912/`.
19 tracked originals, включая ВСЕ 4 tracked файла .claude и CLAUDE.md,
побайтно сверены при копировании; hashes/размеры в originals-manifest.json.
Рендер установленного пакета: rendered/, release-inventory.json — actual 28.
Unknown untracked не копировались; внешняя история и соседние checkout не удалялись.

## Per-file purpose coverage (28/28)

| Файл релиза | Действие и назначение |
|---|---|
| .copier-answers.yml | После review: canonical generated metadata release2.0; личные answers сохранены, manual provenance в этом журнале |
| .gitignore | Сохранён проектный; .worktrees и локальные секреты остаются исключены |
| .opencode/agents/architect.md | Сохранён custom reasoning/human→ADR, убран дубль; анализ требований, readonly/deny question |
| .opencode/agents/backend.md | Native роль, deny question |
| .opencode/agents/designer.md | Native необязательная роль, deny question |
| .opencode/agents/devops.md | Native роль, deny question |
| .opencode/agents/frontend.md | Native роль, deny question |
| .opencode/agents/mobile.md | Native роль, deny question |
| .opencode/agents/reviewer.md | Native независимое readonly ревью, deny question |
| .opencode/agents/tech-lead.md | Native оркестратор, question allow, точная база/проверка worker/shutdown protocol |
| .opencode/agents/tester.md | Native роль, deny question |
| .opencode/ensemble.json | Сохранены mergeOnCleanup:false и promptForModels:false |
| .opencode/team-roles.md | Активный native протокол, human→ADR, память-зеркало, restart и srv gates |
| AGENTS.md | Сохранены проектные правила/API/consumers; canonical native ссылки |
| BACKLOG.md | Очередь сохранена без параллельного бэклога |
| BOARD.md | Сохранены T009/T010; закрытие T011 подготовлено в том же PR, действительно только после final review и srv |
| CHANGELOG.md | Сохранена история; добавляется только T011 |
| CONCEPT.md | Immutable, без изменений |
| DECISIONS.md | Сохранены исторические ADR; добавляется факт ручного переноса T011 |
| README.md | Сохранён API; обновлены только методические ссылки/гейты |
| hooks/pre-push | Сохранён проектный hook, не ослаблен |
| opencode.json | Native plugin/instructions/primary, question deny с исключением лида |
| pyproject.toml | Только canonical comment CLAUDE→AGENTS; Python3.14/контракт/зависимости не меняются |
| scripts/pytest-guard.sh | Сохранён мьютекс и порог; никаких CI изменений |
| specs/design-brief-template.md | Существующая спецификация сохранена, дизайнер native необязателен |
| specs/spec-template.md | Существующая спека и acceptance ритуал сохранены |
| src/main.py | **HIGH ownB:** unwanted generic ADD; не применять к библиотеке |
| tests/test_main.py | **HIGH ownB:** unwanted generic ADD; не применять к библиотеке |

Это не выдуманная CLI omission policy: нежелательные ADD остаются причиной
не применять общий update-plan. Остальные проекты этим не блокируются.

## Custom inventory

| Исходник | Активная замена / сохранение |
|---|---|
| CLAUDE.md | AGENTS.md сохраняет project API, русский язык, consumers/release протокол и scope |
| .claude/agents/architect.md | .opencode/agents/architect.md, весь reasoning и human→ADR |
| .claude/team-roles.md | .opencode/team-roles.md: память-зеркало, restart, необязательный дизайнер |
| .claude/settings.json SessionStart | .opencode/rules/task-context.md в instructions: загрузка канонической задачи без несуществующего dt context |
| .claude/settings.json statusLine + .claude/statusline.sh | /dt-status: краткий статус из BOARD/HEAD; не обещаем прежний GUI indicator/legacy-store |
| Существующие native9roles и ensemble | Сохранены, усилен questiondeny; readonly роли не получают write worktree |

Модели/провайдеры/API Claude, пользовательская память и global config не меняются.
Архив originals не подменяет активный task context. После обновления требуется
согласованный перезапуск клиента; общий сервер посреди работы не перезапускается.

## Проверки и приёмка

Transfer review до deactivation: review-native-r1 дал A PASS и C PASS после
проверки active files/per-file coverage; lead независимо подтвердил 19 originals,
0 byte/hash/size mismatches, директории0700/files0600. После этого удалены только
5 archived tracked legacy файлов своего worktree, сохранена вся git-история.
Исторически в r1 provenance `_commit:2.0.0` сопровождался `_migration_mode`;
это был ручной перенос, не успешный apply CLI. Личные user answers не менялись.
Повторный реальный `dreamteam update --dry-run .` после native provenance:
**rc0**, 1 would change, 25 unchanged, 2 added, 0 removed, 0 conflicts.
Actual ADD: `src/main.py`, `tests/test_main.py`. Ноль конфликтов не означает
безопасность плана: **B HIGH ownB был отмечен как открытый**, plan не применялся.
Одна предлагаемая правка была регенерацией answers с удалением двух нестандартных
ключей provenance. Эти исторические наблюдения r1 не являются итогом r2.
Локальный `uv sync --locked --offline` rc2: отсутствует cached
`pymorphy3-dicts-ru==2.4.417150.4580142`; `--only-dev` rc2: отсутствует
`cryptography==50.0.1`. Python3.14.8 доступен, не скачивался.
OpenCode1.19 `--pure debug config` rc0 (raw config только RAM), git diff --check rc0.
В загруженной effective-конфигурации nine roles и /dt-status доступны;
question allow только tech-lead, deny остальных8. Проверка порядка wildcard
permission rules на загруженном конфиге: architect/reviewer deny для edit,
bash, question, apply_patch, pycharm_apply_patch, pycharm_execute_terminal_command,
team_spawn/team_merge. Это offline config probe, не запуск моделей/серверов.

В own .venv из кэша установлены точные ruff0.16.6/mypy2.3.1 и транзитивные
mypy-extensions1.1.0/pathspec1.1.1/typing-extensions4.16.0/librt0.15.0.
`UV_PYTHON_DOWNLOADS=never VIRTUAL_ENV="$PWD/.venv" uv run --active --offline
--no-sync ruff check .` — rc0; аналогичный `ruff format --check .` — rc0 (54 files).
Аналогичный `mypy src` — rc0 (29 files), **диагностический результат, не locked
gate PASS**: resolver поставил cached ast-serialize0.13.0 вместо locked0.9.0.
Контроль сравнения installed/lock это обнаружил; `uv pip install --offline
--python "$PWD/.venv/bin/python" ast-serialize==0.9.0` — rc1, cache miss.
Никаких неявных downloads/upgrade/project lock edits не было. Итоговый locked
mypy/full gates должен подтвердить srv, локальная блокировка отражена честно.
IDE build недоступен: этот worktree не открыт в IDE; чужой проект не использован.
Полный srv final SHA: ожидается после freeze; промежуточный srv run базы
`66a4eba86da072f735b336503c5cfb0878b55840` — run6, 387 tests, coverage93.75%
(receipt лида), не заменяет прогон итогового коммита.
Checkpoint/teammate done не означают закрытие T011; evidence CI — внешний report
после freeze, без редактирования итогового SHA ради записи его же проверки.

## Уточнение приёмки и metadata — r2, 2026-10-17

Новый автор devops-native-r2 начал в отдельном clean worktree с точной базы
`66a4eba86da072f735b336503c5cfb0878b55840`; исходный HEAD и пустой status
проверены до правок. Исполнение: `task_mvckt5cx_01es_z3dr64`, независимый
read-only review: `task_mvckt5d4_01et_xvu4pb`. Ownership этого раунда:
только generated answers и собственные записи T011; бизнес-код, тесты, CI,
зависимости, lock и пользовательская конфигурация не меняются.

Последнее прямое уточнение Владимира: приёмке подлежит содержательный **ручной
перенос методики и непрерывность контекста**, с полной purpose mapping,
сохранёнными источниками, независимым review и гейтами. Требование считать
generic seed ADD2 самостоятельным запретом закрытия этой ручной задачи было
расширением scope со стороны контроллера, а не решением человека. Исторические
ownB/rc/counts выше сохранены, но это не актуальный человеческий acceptance.
Канонические тесты/ADR dreamteam этим уточнением не меняются.

По advice read-only review удалены **только** неподдерживаемые generated keys
`_migration_mode` и `_migration_evidence`: actual render не сохраняет их и
предлагал лишний MODIFY. `_commit`, `_src_path` и все личные answers неизменны.
Полная provenance ручного переноса остаётся здесь и в T011 ADR; удаление двух
ключей не превращает перенос в автоматический CLI apply и не маскирует план.

Обычный общий update по-прежнему не применяется: известные generic
`src/main.py` и `tests/test_main.py` к библиотеке не относятся. Это ограничение
CLI, не реализованная omission API и не доказательство полного CLI no-op.
Повторяемость проверяется двумя actual full dry-run подряд на неизменных входах:
требуется 0 содержательных methodology MODIFY и только эти известные ADD2.

Лид независимо выполнил два actual full `dreamteam update --dry-run .` в
worktree r2 на одинаковых входах. Оба: **rc0, 0 would change, 26 unchanged,
2 added, 0 removed, 0 conflicts**; единственные ADD — `src/main.py` и
`tests/test_main.py`. Набор изменяемых YAML keys пуст. Между вызовами и после
них git diff/status совпали; SHA256 двух RAM outputs одинаковый:
`ef4bbf93cfe4cde1a40278dea6d3df529832904351b0d339cfc21baa793873c4`.
Это receipt независимого запуска лида, не собственный запуск автора r2;
raw output и личные answers в журнал не выводились. Содержательные методические
правки больше не предлагаются; общий CLI план всё ещё **не no-op** из-за ADD2.

Локальные проверки автора r2 в собственной новой `.venv`, Python3.14.8 из кэша,
`UV_PYTHON_DOWNLOADS=never`: `uv sync --active --locked --offline` — rc2,
cache miss `cryptography==50.0.1`. Установлен отдельно точный cached ruff0.16.6:
`uv run --active --offline --no-sync ruff check .` и `ruff format --check .`
— оба rc0 (54 файла). Установка точного locked mypy2.3.1 с ast-serialize0.9.0,
librt0.15.0, mypy-extensions1.1.0, pathspec1.1.1, typing-extensions4.16.0 —
rc1, cache miss ast-serialize0.9.0. Locked mypy не запускался; диагностической
подмены версий в r2 нет. Full/locked gate остаётся за srv итогового SHA.

Попытка narrow grep установленного исходника для проверки формата output
отклонена permission; чтение не повторялось и не обходилось. Отдельный actual
CLI RAM subprocess разрешён лидом явно; receipt выше относится именно к CLI,
не к чтению отвергнутого исходника. Global/runtime/source edits не выполнялись.

Запись Done в BOARD подготовлена для того же итогового PR, но вступает в силу
только после независимого final review и полного зелёного srv run **итогового**
SHA, а затем слияния лидом. До этого ни checkpoint, ни статус исполнителя done
не означают приёмку. Ссылку на итоговый run лид фиксирует во внешнем PR report
после freeze, без self-hash цикла редактирования этого журнала.
