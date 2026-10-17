# Advanced Whiteboarding

Обзор стандарта **Advanced Whiteboarding** — SVG-доски поверх Shared XML Editing (XEP-0284).
Стандарт замещает **XEP-0113: Simple Whiteboarding** и описывает место устаревшего профиля Psi.

## Общая база

Обе версии стандарта — один и тот же Jingle application type
`urn:xmpp:jingle:apps:svg-whiteboard:0` с общим набором стандартов:

- XMPP Core
- XEP-0030 Service Discovery
- XEP-0166 Jingle (управление сессией)
- XEP-0284 Shared XML Editing (записи и правки)
- XEP-0045 Multi-User Chat (host для групповой доски)
- W3C SVG Tiny 1.2 (формат документа)

Различаются только набором **опциональных** расширений. Идентификатор
application type у обоих одинаков, поэтому выбор версии не влияет на
совместимость на уровне namespace.

## Сравнение

| Возможность | Minimal (Core) | Extended (Full) |
|---|---|---|
| Jingle-сессия, SXE, MUC, SVG Tiny | обязательно | обязательно |
| Inline `data:`-изображения | обязательно | обязательно (как fallback) |
| Entity Capabilities (XEP-0115) | — | рекомендуется |
| HTTP File Upload (XEP-0363) для изображений | — | опционально |
| Jingle File Transfer (XEP-0234) | — | опционально |
| Jingle Message Initiation (XEP-0353) | — | опционально |
| Размер документа | минимальный | больше из-за ссылок/расширений |
| Сложность реализации | ниже | выше |

Полный клиент совместим с минимальным пиром: расширения согласуются отдельно,
и при их отсутствии используется поведение Core (в частности, inline `data:`-URI
для изображений).

## Когда что использовать

- **Minimal** — простые клиенты, встраиваемые решения, максимальная
  совместимость и минимальная поверхность реализации.
- **Extended** — полнофункциональные клиенты, где важны экономия трафика на
  изображениях, эффективное обнаружение возможностей и запуск доски из чата.

## Файлы

**Спецификации:**
- [`docs/xep-svg-whiteboarding-minimal.xml`](docs/xep-svg-whiteboarding-minimal.xml) / [`.html`](docs/xep-svg-whiteboarding-minimal.html) — минимальный профиль.
- [`docs/xep-svg-whiteboarding-extended.xml`](docs/xep-svg-whiteboarding-extended.xml) / [`.html`](docs/xep-svg-whiteboarding-extended.html) — расширенный профиль.

**Правила и обзоры:**
- [`docs/WHITEBOARD_PROFILE.md`](docs/WHITEBOARD_PROFILE.md) ([EN](docs/WHITEBOARD_PROFILE.en.md)) — нормативные правила реализации.
- [`docs/SVG_WHITEBOARD_VARIANTS.md`](docs/SVG_WHITEBOARD_VARIANTS.md) ([EN](docs/SVG_WHITEBOARD_VARIANTS.en.md)) — краткий обзор вариантов.

**Историческая справка (устаревший профиль Psi):**
- [`docs/PSI_WHITEBOARDING_VS_XEP0113.md`](docs/PSI_WHITEBOARDING_VS_XEP0113.md) ([EN](docs/PSI_WHITEBOARDING_VS_XEP0113.en.md)) — сравнение старой реализации Psi с XEP-0113.
- [`docs/xep-collaborative-svg-whiteboarding.xml`](docs/xep-collaborative-svg-whiteboarding.xml) / [`.html`](docs/xep-collaborative-svg-whiteboarding.html) — **deprecated** черновик профиля Psi-native.

**Инструменты:**
- [`docs/tools/xep2html.py`](docs/tools/xep2html.py) — конвертер XML → HTML.
