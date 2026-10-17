# Advanced Whiteboarding: варианты профиля (краткое описание)

> English version: [`SVG_WHITEBOARD_VARIANTS.en.md`](SVG_WHITEBOARD_VARIANTS.en.md)

Краткий обзор двух версий нового стандарта **Advanced Whiteboarding** (SVG-доска
поверх Shared XML Editing, XEP-0284). Стандарт замещает **XEP-0113: Simple
Whiteboarding** и описывает место устаревшего профиля Psi.

## Общая база

Оба варианта — один и тот же Jingle application type
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

## Статус профиля Psi

Старый профиль Psi (`http://jabber.org/protocol/sxe`, кастомный `<negotiation>`,
ранняя редакция SXE) — **deprecated**. Он сохранён только как историческая
справка (файл `xep-collaborative-svg-whiteboarding.xml` и
`PSI_WHITEBOARDING_VS_XEP0113.md`). Новые реализации должны использовать
Jingle-сессию и `urn:xmpp:sxe:0` согласно XEP-0284.

## Соответствие Psi-native → новый стандарт

| Psi-native | Новый стандарт |
|---|---|
| `http://jabber.org/protocol/sxe` | `urn:xmpp:sxe:0` |
| `<negotiation>` (кастомно) | Jingle (XEP-0166) |
| `<invitation>`/`<accept-invitation>` | Jingle `session-initiate`/`session-accept` |
| `<connect-request>`/`<history-offer>`/`<accept-history>` | `<connect/>` + `<state-offer/>`/`<accept-state/>`/`<refuse-state/>` |
| `<document-begin>`/`<document-end>` в `<negotiation>` | внутри `<state>` |
| `<set rid=...>`/`<remove rid=...>` | `<set target=...>`/`<remove target=...>` |
| `<left-session>` | Jingle `session-terminate` |
| application feature `http://www.w3.org/2000/svg` | Jingle app type `urn:xmpp:jingle:apps:svg-whiteboard:0` |

## Файлы

- `xep-svg-whiteboarding-minimal.xml` / `.html` — минимальная спека.
- `xep-svg-whiteboarding-extended.xml` / `.html` — расширенная спека.
- `WHITEBOARD_PROFILE.md` — нормативные правила реализации.
- `xep-collaborative-svg-whiteboarding.xml` — устаревший черновик (deprecated).
