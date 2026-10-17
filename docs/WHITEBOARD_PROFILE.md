# Правила реализации whiteboard-профиля (SXE / XEP-0284)

Нормативный документ для реализаций **Advanced Whiteboarding** (SVG-доски поверх Shared XML Editing, XEP-0284).
Описывает обязательные и рекомендуемые правила, conformance-классы и чеклист.

## 1. Область и терминология

- Документ описывает два профиля одного application type:
  - **Core** — минимальный профиль (файл `xep-svg-whiteboarding-minimal.xml`);
  - **Full** — расширенный профиль (файл `xep-svg-whiteboarding-extended.xml`).
- Ключевые слова **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, **MAY** трактуются по RFC 2119/BCP 14.
- Профиль **Psi-native** (namespace `http://jabber.org/protocol/sxe`, кастомный `<negotiation>`) — **deprecated**; новые реализации MUST NOT его использовать. Psi будет обновлён к настоящему стандарту.

## 2. Константы

| Назначение | Значение |
|---|---|
| Jingle (ядро) | `urn:xmpp:jingle:1` |
| Jingle application type (доска) | `urn:xmpp:jingle:apps:svg-whiteboard:0` |
| Jingle transport (SXE) | `urn:xmpp:jingle:transports:sxe` |
| SXE (элемент `<sxe>`) | `urn:xmpp:sxe:0` |
| Namespace SVG-документа | `http://www.w3.org/2000/svg` |
| XLink (для `<image>`) | `http://www.w3.org/1999/xlink` |
| HTTP File Upload (Full) | `urn:xmpp:http:upload:0` |

## 3. Conformance-классы

- **Core**: XMPP Core + XEP-0030 + XEP-0166 + XEP-0284 + XEP-0045 + SVG Tiny 1.2.
- **Full**: Core + опциональные расширения (XEP-0115, XEP-0363, XEP-0234, XEP-0353), согласуемые отдельно.

Full-клиент MUST корректно работать с Core-пиром, не требуя наличия расширений.

## 4. Обнаружение

- R4.1 Реализация MUST объявлять feature `urn:xmpp:jingle:1`, `urn:xmpp:sxe:0`, `urn:xmpp:jingle:transports:sxe`, `urn:xmpp:jingle:apps:svg-whiteboard:0`.
- R4.2 Реализация SHOULD объявлять disco-identity категории `collaboration` типа `sxe`.
- R4.3 Полный клиент SHOULD использовать XEP-0115 (Entity Capabilities) для определения возможностей пира.
- R4.4 Запускать сессию MUST только при наличии у пира app-namespace доски и SXE-транспорта.

## 5. Сессия (Jingle)

- R5.1 Управление сессией MUST выполняться по XEP-0166 (`session-initiate`/`session-accept`/`session-terminate`).
- R5.2 `<description>` MUST быть в namespace `urn:xmpp:jingle:apps:svg-whiteboard:0` (в профиле Core без дочерних элементов).
- R5.3 `<transport>` MUST быть в namespace `urn:xmpp:jingle:transports:sxe` и MUST содержать минимум один `<host/>`.
- R5.4 При отказе из-за неподдержки приложения SHOULD использоваться reason `unsupported-applications`.

## 6. Соединение и синхронизация состояния

- R6.1 SXE-полезная нагрузка MUST быть элементом `<sxe xmlns='urn:xmpp:sxe:0'>` внутри `<message>`.
- R6.2 `<sxe>` MUST содержать `session` и `id`; `id` MUST быть уникален в пределах сессии для отправителя.
- R6.3 Присоединение MUST выполняться элементом `<connect/>`.
- R6.4 Передача состояния MUST быть заключена в `<state>` с `<document-begin/>` … `<document-end/>`; `prolog` у `<document-begin/>` содержит XML-пролог как `data:`-URI (RFC 2397).
- R6.5 Во время передачи состояния отправитель MUST NOT отправлять другие `<sxe>`-элементы между `<document-begin/>` и `<document-end/>`.
- R6.6 Получатель MUST NOT применять входящие правки до обработки `<document-end/>`.

## 7. Документ

- R7.1 Корень MUST быть `<svg>` в namespace `http://www.w3.org/2000/svg`; canvas MUST задаваться атрибутом `viewBox`.
- R7.2 SHOULD использоваться SVG Tiny 1.2 (`baseProfile='tiny'`).
- R7.3 Каждый drawable-элемент SHOULD иметь уникальный атрибут `id` (namespace приложения), независимо от SXE `rid`.
- R7.4 Управление порядком (z-order) MUST выполняться через `primary-weight` (и secondary weight по `rid`), а не через придуманные атрибуты.
- R7.5 Группировка MUST использовать `<g>`; при разгруппировке трансформация группы MUST быть скомпонована в трансформации потомков.
- R7.6 Трансформации MUST выражаться SVG-атрибутом `transform` (канонически — `matrix(...)`).
- R7.7 Изображения: Core MUST использовать inline `data:`-URI; Full MAY использовать URL (XEP-0363/XEP-0234) с обязательным fallback на `data:`.
- R7.8 Метаданные (`<title>`, `<desc>`, `<defs>`) MUST NOT трактоваться как drawable-элементы и SHOULD сохраняться.
- R7.9 Текст SHOULD представляться путями (например, штриховым шрифтом); отдельного элемента текста профиль не вводит.

## 8. Правки

- R8.1 Правки MUST выполняться элементами `<new>`/`<set>`/`<remove>` внутри `<state>`.
- R8.2 `<new>` MUST содержать `rid` и `type`; `parent` обязателен везде, кроме корня.
- R8.3 `<set>` и `<remove>` MUST использовать атрибут `target` (НЕ `rid`).
- R8.4 Частичная замена символьных данных SHOULD использовать `replacefrom`/`replacen` вместе с `chdata`.
- R8.5 `rid` удалённых записей MUST NOT переиспользоваться в пределах сессии.
- R8.6 Реализация MUST корректно обрабатывать non-commutative правки (`<set>`) согласно модели версий XEP-0284.

## 9. Расширения (профиль Full)

- R9.1 Расширения MUST быть опциональными и согласуемыми; Core-пир MUST NOT требовать их наличия.
- R9.2 HTTP File Upload (XEP-0363) MUST использоваться только если пир объявляет `urn:xmpp:http:upload:0`.
- R9.3 Jingle File Transfer (XEP-0234) и Jingle Message Initiation (XEP-0353) MAY использоваться как альтернативные каналы/способы запуска.
- R9.4 При недоступности расширения реализация MUST деградировать к соответствующему поведению Core (например, inline `data:`-URI).

## 10. Ошибки, лимиты, безопасность

- R10.1 Изображения SHOULD ограничиваться по размеру и формату.
- R10.2 Документ SHOULD отображаться без загрузки внешних ресурсов (кроме явно разрешённых Full-расширением).
- R10.3 XML-пролог из атрибута `prolog` MUST трактоваться как недоверенный ввод.
- R10.4 Доступ к правкам по умолчанию есть у всех участников; контроль доступа — вне области профиля.
- R10.5 Высокочастотные правки (freehand) SHOULD объединяться (coalescing) для экономии полосы.

## 11. Чеклист conformance

**Core:**
- [ ] Объявлены 4 feature (R4.1) и identity `collaboration/sxe` (R4.2).
- [ ] Jingle-сессия с `<description>` и `<transport>`/`<host>` (R5.1–R5.3).
- [ ] `<connect/>`, передача состояния через `<state>` (R6.3–R6.6).
- [ ] SVG Tiny 1.2, `viewBox`, `id`, `primary-weight` (R7.1–R7.4).
- [ ] Правки `<new>`/`<set target>`/`<remove target>` (R8.1–R8.3).
- [ ] Inline `data:`-изображения (R7.7).

**Full (дополнительно):**
- [ ] Entity Capabilities (R4.3).
- [ ] Upload с fallback (R9.2, R9.4).
- [ ] Jingle FT / JMI по необходимости (R9.3).

## 12. Ссылки

- `xep-svg-whiteboarding-minimal.xml` — минимальная спека.
- `xep-svg-whiteboarding-extended.xml` — расширенная спека.
- `SVG_WHITEBOARD_VARIANTS.md` — краткое описание вариантов.
- `PSI_WHITEBOARDING_VS_XEP0113.md` — сравнение с XEP-0113 и устаревшим профилем Psi.
