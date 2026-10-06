# Project agent instructions
<!-- CODE_BRAIN_MANDATORY -->
## Code Brain MCP - Mandatory when loaded

Use Code Brain MCP first for substantive tasks in this project.

- Start with `start_task(runIntake=true)` or `neural_sync`.
- Use `agent_plan` before `agent_code` for chunk and deep work.
- Use `memory_retrieve` at intake and `memory_store` at task end.
- Use `uncertainty_guard` before storing conclusions.
- Disable duplicate MCPs with `get_superseded_mcps`.
<!-- CODE_BRAIN_MANDATORY -->

## Язык общения (Language) — перечитывать всегда

- Область действия: ТОЛЬКО ответы и уточняющие вопросы агента. Код, комментарии в коде,
  документация и сообщения коммитов этим правилом не затрагиваются.
- Все пояснения работы, планы, сводки и уточняющие вопросы агент даёт на русском языке.
- Код, команды, идентификаторы, имена файлов и технические термины — без перевода.

## Git и коммиты

- В проекте ведётся git-репозиторий (инициализирован в корне).
- После каждого осмысленного изменения файлов делать коммит; не оставлять правки без коммита.
- Перед коммитом: `git status` / `git diff`; стейджить только относящиеся к задаче файлы.
- Не коммитить секреты и временные артефакты (`.opencode/` и т.п.).
- Сообщения коммитов — на английском, Conventional Commits.
- В тело коммита добавлять трейлер `Model: opencode-go/deepseek-v4.1-flash` (актуальный ID модели).

