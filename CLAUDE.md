# Claude project instructions
<!-- CODE_BRAIN_ON_EVERY_PROMPT -->
## Code Brain MCP

On every substantive prompt: use `start_task(runIntake=true)` or `neural_sync`, then use the returned routing and memory context. Store the final outcome with `memory_store`.
<!-- CODE_BRAIN_ON_EVERY_PROMPT -->

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

