# Подробное сравнение реализации whiteboarding в Psi с XEP-0113: Simple Whiteboarding

> **Статус:** описанный здесь профиль Psi-native (`http://jabber.org/protocol/sxe`, кастомный `<negotiation>`, ранняя редакция SXE) — **deprecated**. Новый стандарт, построенный на Jingle (XEP-0166) и XEP-0284, описан в `xep-svg-whiteboarding-minimal.xml` / `xep-svg-whiteboarding-extended.xml`; нормативные правила — в `WHITEBOARD_PROFILE.md`; обзор вариантов и миграции — в `SVG_WHITEBOARD_VARIANTS.md`. Этот документ сохранён как сравнительный анализ и историческая справка.

## Содержание

- [1. Введение](#1-введение)
- [2. Краткий обзор XEP-0113: Simple Whiteboarding](#2-краткий-обзор-xep-0113-simple-whiteboarding)
- [3. Архитектура и компоненты реализации в Psi](#3-архитектура-и-компоненты-реализации-в-psi)
- [4. Протокол SXE (Shared XML Editing) в Psi](#4-протокол-sxe-shared-xml-editing-в-psi)
- [5. Сравнение транспорта и протокола синхронизации](#5-сравнение-транспорта-и-протокола-синхронизации)
- [6. Сравнение формата данных и поддерживаемых элементов](#6-сравнение-формата-данных-и-поддерживаемых-элементов)
- [7. Сравнение операций и команд](#7-сравнение-операций-и-команд)
- [8. Модель идентификаторов и управление состоянием](#8-модель-идентификаторов-и-управление-состоянием)
- [9. Режимы редактирования, UI и функциональность](#9-режимы-редактирования-ui-и-функциональность)
- [10. Особенности генерации графики и оптимизации](#10-особенности-генерации-графики-и-оптимизации)
- [11. Обработка изображений, текста и специальных случаев](#11-обработка-изображений-текста-и-специальных-случаев)
- [12. Обнаружение поддержки (feature discovery) и интеграция с клиентом](#12-обнаружение-поддержки-feature-discovery-и-интеграция-с-клиентом)
- [13. Сводная таблица ключевых отличий](#13-сводная-таблица-ключевых-отличий)
- [14. Выводы и рекомендации для реализации в других клиентах](#14-выводы-и-рекомендации-для-реализации-в-других-клиентах)
- [15. Список использованных файлов исходного кода](#15-список-использованных-файлов-исходного-кода)
- [16. Ссылки](#16-ссылки)

## 1. Введение

Данный документ представляет собой подробное сравнение реализации модуля whiteboarding в Jabber-клиенте Psi с официальным протоколом XEP-0113: Simple Whiteboarding.

Реализация в Psi (расположена в каталоге `whiteboarding/`) существенно отличается от XEP-0113 не только деталями, но и принципиальным подходом к синхронизации коллаборативного редактирования. Если XEP-0113 описывает минималистичный командный протокол поверх XMPP-сообщений, то Psi использует **SXE — Shared XML Editing** (XEP-0284) для совместного редактирования DOM SVG-документа в реальном времени.

> Терминологическая заметка: в исходниках Psi и в некоторых старых обсуждениях аббревиатура SXE иногда раскрывалась как «Simple XML Exchange». Правильное и официальное название протокола — **Shared XML Editing** (XEP-0284), автор — Joonas Govenius, он же автор whiteboarding в Psi.

## 2. Краткий обзор XEP-0113: Simple Whiteboarding

XEP-0113 (v0.2 от 2003-09-07, статус Deferred, тип Informational) определяет предельно простой протокол для обмена рисунками между участниками Jabber-соединения.

**Ключевые положения XEP-0113:**
- Протокол основан на XMPP `<message>` с расширением `<x xmlns="http://jabber.org/protocol/swb">`
- Поддерживаемые элементы: `<path>`, `<move>`, `<delete>`
- Формат пути — сильно упрощённый SVG path с командами только `M`, `m`, `L`, `l` (абсолютные/относительные moveto и lineto)
- Атрибуты `<path>`: `d` (обязательный), `stroke` (опц., по умолчанию `#000000`), `stroke-width` (опц., по умолчанию `1`), `id` (опц.)
- `<move id="..." dx="..." dy="..."/>` — относительное перемещение элемента по его `id`
- `<delete id="..."/>` — удаление элемента по его `id`
- Сценарии: одиночное whiteboard-сообщение, whiteboard-чат сессия (с thread), whiteboard в MUC (groupchat)
- Явная цель — максимальная простота реализации

## 3. Архитектура и компоненты реализации в Psi

Реализация представляет собой модуль whiteboarding, интегрированный с инфраструктурой Psi и использующий SXE для синхронизации. Компоненты (исходные файлы):

| Класс/Модуль | Файл | Назначение |
|---|---|---|
| **WbManager** | [`wbmanager.h`](../psi-whiteboard/wbmanager.h), [`wbmanager.cpp`](../psi-whiteboard/wbmanager.cpp) | Менеджер диалогов доски. Слушает SXE-сессии, создаёт диалоги при согласовании сессии, обрабатывает приглашения, предоставляет API для открытия доски. |
| **WbDlg** | [`wbdlg.h`](../psi-whiteboard/wbdlg.h), [`wbdlg.cpp`](../psi-whiteboard/wbdlg.cpp) | Диалоговое окно сессии доски (`AdvancedWidget`). Содержит `WbWidget`, тулбар с режимами, выбором цвета/заливки/толщины, кнопки сохранения/очистки/завершения сессии. |
| **WbWidget** | [`wbwidget.h`](../psi-whiteboard/wbwidget.h), [`wbwidget.cpp`](../psi-whiteboard/wbwidget.cpp) | Основной виджет визуализации и редактирования. Обрабатывает пользовательский ввод (мышь), создаёт временные элементы при рисовании, управляет режимами редактирования, координирует синхронизацию с SXE. |
| **WbScene** | [`wbscene.h`](../psi-whiteboard/wbscene.h), [`wbscene.cpp`](../psi-whiteboard/wbscene.cpp) | Наследник `QGraphicsScene`. Управляет элементами на сцене, реализует группировку/разгруппировку, управление порядком слоёв, регенерацию трансформаций. |
| **WbItem** | [`wbitem.h`](../psi-whiteboard/wbitem.h), [`wbitem.cpp`](../psi-whiteboard/wbitem.cpp) | Представляет существующий SVG-элемент на сцене (`QGraphicsSvgItem`). Обрабатывает трансформации, контекстное меню, синхронизирует изменения обратно в DOM через SXE. |
| **WbNewItem** | [`wbnewitem.h`](../psi-whiteboard/wbnewitem.h), [`wbnewitem.cpp`](../psi-whiteboard/wbnewitem.cpp) | Базовый класс для временных элементов, создаваемых в процессе рисования (до фиксации в документ). |
| **WbNewPath** | [`wbnewpath.h`](../psi-whiteboard/wbnewpath.h), [`wbnewpath.cpp`](../psi-whiteboard/wbnewpath.cpp) | Временный элемент для свободного рисования (path). Генерирует сглаженные кривые (`QPainterPath::quadTo`), сериализуется в SVG `<path>`. |
| **WbNewImage** | [`wbnewimage.h`](../psi-whiteboard/wbnewimage.h), [`wbnewimage.cpp`](../psi-whiteboard/wbnewimage.cpp) | Временный элемент для вставки изображения. Кодирует изображение в data URI (base64) при сериализации. |

**Ключевая инфраструктура:** используются `SxeSession` и `SxeManager` из отдельного модуля `src/sxe` в дереве исходников Psi (в данной рабочей копии присутствует только модуль `whiteboarding/`; заголовки подключаются как `../sxe/...`). SXE реализует коллаборативное редактирование XML/DOM, а корневым документом является SVG.

**Пустой документ (`EMPTYWB`, объявлен в `wbmanager.cpp`):**
```xml
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg xmlns="http://www.w3.org/2000/svg" version="1.2" viewBox="0 0 600 400" baseProfile="tiny" />
```

## 4. Протокол SXE (Shared XML Editing) в Psi

Этот раздел описывает, как именно устроена синхронизация на уровне XMPP-станз. Понимание этой модели необходимо для корректного сравнения с XEP-0113 и для реализации совместимого клиента.

### 4.1 Обзор и namespace

- **Название:** Shared XML Editing (SXE), стандартизован как XEP-0284. Протокол позволяет нескольким участникам совместно редактировать произвольный XML-документ (в нашем случае — SVG).
- **Протокольный namespace:** `http://jabber.org/protocol/sxe` (в Psi задан макросом `SXENS` в `sxesession.h`).
- **Application feature:** `http://www.w3.org/2000/svg` (макрос `WBNS` в `wbmanager.h`) — обозначает тип редактируемого документа (SVG), а не протокол.
- **Проверка поддержки:** `SxeManager::checkSupport()` требует наличия **обоих** feature: `SXENS` **и** запрошенных application features (то есть `WBNS`).
- **Host:** SXE не требует центрального сервера. В сессии «один-на-один» host’ом выступает инициатор; в MUC host’ом служит сама комната.

### 4.2 Оболочка `<sxe>`

Каждое изменение и каждый переговорный шаг передаются в отдельной станзе `<message>`:

```xml
<message from='kingclaudius@shakespeare.lit/castle'
         to='laertes@shakespeare.lit/castle'>
  <sxe xmlns='http://jabber.org/protocol/sxe'
       session='851ba2' id='4'>
    ...
  </sxe>
</message>
```

- `session` — GUID сессии (общий для всех участников).
- `id` — уникальный идентификатор данной станзы-носителя.
- Внутри `<sxe>` находится либо один `<negotiation>` (переговоры), либо один или несколько редактирующих элементов.

### 4.3 Переговоры сессии

Переговоры ведутся дочерними элементами `<negotiation>`:

| Элемент | Смысл |
|---|---|
| `<invitation><feature>URI</feature>…</invitation>` | Приглашение начать сессию с перечнем требуемых application features |
| `<accept-invitation/>` | Приглашённый принимает приглашение |
| `<decline-invitation><alternative-session>GUID</alternative-session></decline-invitation>` | Отказ; может предлагать существующую сессию |
| `<abort-negotiation/>` | Прерывание незавершённых переговоров |
| `<connect-request/>` | Присоединение к уже существующей сессии |
| `<history-offer/>` | Предложение передать текущее состояние документа |
| `<accept-history/>` | Джойнер принимает предложение состояния |
| `<document-begin prolog='data:…' available-uuid-prefix='…'/>` | Начало передачи состояния; `prolog` содержит XML-пролог (включая DOCTYPE) как `data:`-URI |
| *(редактирующие элементы)* | Снимок документа в виде последовательности `<new>`/`<set>` |
| `<document-end used-sxe-ids='…'/>` | Конец передачи состояния |
| `<left-session/>` | Уведомление об уходе из сессии |

Логика согласования реализована в `SxeManager::processNegotiationMessage()`, `SxeManager::processNegotiationAsParticipant()` и `SxeManager::processNegotiationAsJoiner()`; инициация — в `SxeManager::startNewSession()`, присоединение — в `SxeManager::joinSession()`.

### 4.4 Записи (records) и редактирующие элементы

SXE не передаёт «команды» над SVG напрямую. Он поддерживает набор **записей**, каждая из которых соответствует одному DOM-узлу, и синхронизирует их поля:

| Поле | Смысл |
|---|---|
| `rid` | Record ID — GUID записи (отличается от SVG-атрибута `id`) |
| `type` | Тип узла: `element`, `attr`, `text`, `comment`, `processinginstruction` |
| `version` | Версия записи (0 у созданной) |
| `parent` | `rid` родительской записи |
| `primary-weight` | Вес для упорядочивания сиблингов (больше — выше/позже) |
| `ns` | namespace элемента/атрибута |
| `name` | имя элемента/атрибута |
| `chdata` | символьные данные (текст, значение атрибута, комментарий) |
| `pitarget`, `pidata` | target/data для processing instruction |

Изменения выражаются тремя элементами (файлы `sxenewedit.cpp`, `sxerecordedit.cpp`, `sxeremoveedit.cpp`):

- `<new rid type parent primary-weight [name] [ns] [chdata] [pitarget] [pidata]/>` — создание записи;
- `<set rid version [parent] [primary-weight] [name] [chdata] [replacefrom] [replacen] [pitarget] [pidata]/>` — изменение записи;
- `<remove rid/>` — удаление записи.

Порядок узлов среди сиблингов определяется primary-weight, а при равенстве — **secondary weight** (лексикографическое сравнение `rid`), см. `SxeRecord::operator<()` и `SxeRecord::hasSmallerSecondaryWeight()`.

### 4.5 Пример: рисование пути

Создание красного треугольника на доске — это одна станза SXE с несколькими `<new>`:

```xml
<message from='kingclaudius@shakespeare.lit/castle'
         to='laertes@shakespeare.lit/castle'>
  <sxe xmlns='http://jabber.org/protocol/sxe' session='851ba2' id='8'>
    <new rid='8'  type='element' name='path' parent='0' primary-weight='1'/>
    <new rid='9'  type='attr' name='id'           chdata='e1f2a3b4' parent='8' primary-weight='0'/>
    <new rid='10' type='attr' name='d'            chdata='M 100 100 L 300 100 L 200 300 Z' parent='8' primary-weight='0'/>
    <new rid='11' type='attr' name='stroke'       chdata='#ff0000' parent='8' primary-weight='0'/>
    <new rid='12' type='attr' name='stroke-width' chdata='2'       parent='8' primary-weight='0'/>
  </sxe>
</message>
```

Обратите внимание: «insertNode/setAttribute/removeNode» из `SxeSession` — это клиентский API, а по сети уходят именно `<new>`/`<set>`/`<remove>` с `rid`/`version`/`primary-weight`.

### 4.6 Отношение к XEP-0284

Psi использует **раннюю (ProtoXEP) редакцию** SXE: сессия согласуется кастомными элементами `<negotiation>` внутри `<message>`, а namespace — `http://jabber.org/protocol/sxe`. Позднее XEP-0284 стандартизовал управление сессией через **Jingle (XEP-0166)** с namespace’ами `urn:xmpp:sxe:0` и `urn:xmpp:jingle:transports:sxe`. При этом **модель записей и редактирующих элементов осталась той же**, поэтому клиент на XEP-0284 может обмениваться теми же `<new>`/`<set>`/`<remove>`, но не совместим с переговорами Psi на уровне станз.

### 4.7 Формализованное описание профиля

Описание профиля формализовано в этом же репозитории. Актуальный стандарт (на базе XEP-0284) и устаревший черновик:

- [`xep-svg-whiteboarding-minimal.xml`](xep-svg-whiteboarding-minimal.xml) / [`.html`](xep-svg-whiteboarding-minimal.html) — **актуальный** минимальный профиль;
- [`xep-svg-whiteboarding-extended.xml`](xep-svg-whiteboarding-extended.xml) / [`.html`](xep-svg-whiteboarding-extended.html) — **актуальный** расширенный профиль;
- [`WHITEBOARD_PROFILE.md`](WHITEBOARD_PROFILE.md) — нормативные правила реализации;
- [`SVG_WHITEBOARD_VARIANTS.md`](SVG_WHITEBOARD_VARIANTS.md) — обзор вариантов и миграция;
- [`xep-collaborative-svg-whiteboarding.xml`](xep-collaborative-svg-whiteboarding.xml) / [`.html`](xep-collaborative-svg-whiteboarding.html) — **deprecated** черновик профиля Psi-native;
- [`tools/xep2html.py`](tools/xep2html.py) — конвертер XML → HTML.

## 5. Сравнение транспорта и протокола синхронизации

| Параметр | XEP-0113 | Реализация Psi | Комментарии |
|---|---|---|---|
| **Тип протокола** | Командный, message-based. Расширение `<x xmlns="http://jabber.org/protocol/swb">` внутри `<message>`. | DOM-синхронизация, session-based, поверх SXE. Редактирующие элементы `<new>`/`<set>`/`<remove>` над общим SVG DOM. | Ключевое принципиальное отличие. XEP-0113 — stateless обмен командами, Psi — stateful совместное редактирование документа. |
| **Транспортные пакеты** | Только `<message>` (chat, groupchat). Поддерживает thread для сессии чата. | Тоже `<message>`, но с полезной нагрузкой `<sxe xmlns="http://jabber.org/protocol/sxe">`; переговоры — через `<negotiation>`. | Оба варианта используют `<message>`, но семантика принципиально разная: команда против элемента сессии. |
| **Протокольный namespace** | `http://jabber.org/protocol/swb` | `http://jabber.org/protocol/sxe` (`SXENS`) | Разные протоколы. |
| **Application feature** | Нет (тип задан namespace’ом SWB) | `http://www.w3.org/2000/svg` (`WBNS`) — тип документа | SVG здесь — формат данных, а не протокол. |
| **Модель синхронизации** | Event/command model: отправка команды при действии (path/move/delete). Только дельты. | Records/edits: ведётся общий SVG DOM, синхронизируются записи узлов (создание/изменение/удаление). | Psi хранит полное состояние доски как SVG DOM на всех клиентах. |
| **Управление сессией** | Не специфицировано в XEP. Использует стандартные механики XMPP (thread в chat, room в MUC). | Явное согласование через `SxeManager` элементами `<negotiation>`; приглашения — сигнал `invitationCallback`, который `WbManager::checkInvitation()` превращает в запрос пользователю. | Psi требует negotiated SXE-сессии. |
| **Инициация сессии** | Может быть одиночным сообщением или началом чата (thread). | `WbManager::openWhiteboard()`: проверяет поддержку, при отсутствии диалога предлагает открыть существующий SVG или создаёт `EMPTYWB`, затем вызывает `SxeManager::startNewSession()`. | Более сложная инициация с возможностью загрузки начального документа. |
| **Завершение сессии** | Не специфицировано. | `WbDlg::endSession()` вызывает `SxeSession::endSession()`; уход участника передаётся элементом `<left-session/>` и сигналом `peerLeftSession()`. | Явное управление жизненным циклом сессии. |
| **Feature discovery** | Рекомендуется Service Discovery (XEP-0030), но не детализирован. | `SxeManager::checkSupport()` проверяет `SXENS` **и** `WBNS`; приглашения фильтруются `WbManager::checkInvitation()` по наличию `WBNS`. | Нужны оба feature. |

## 6. Сравнение формата данных и поддерживаемых элементов

| Элемент/Атрибут | XEP-0113 | Реализация Psi | Комментарии |
|---|---|---|---|
| **Корневой элемент** | `<x xmlns="http://jabber.org/protocol/swb">` | `<svg xmlns="http://www.w3.org/2000/svg" version="1.2" viewBox="..." baseProfile="tiny">` | Psi работает непосредственно с SVG DOM, а не с обёрткой SWB. |
| **Поддерживаемые графические элементы** | Только `<path>` | Любые SVG-элементы, присутствующие в DOM: `<path>`, `<image>`, `<g>` и др. | Гораздо шире. Psi — это по сути коллаборативное редактирование SVG. |
| **Path - команды** | Только `M`, `m`, `L`, `l`. Никаких кривых, дуг и т. п. | Генерирует SVG path через `QPainterPath`. При свободном рисовании (`WbNewPath::parseCursorMove()`) используется `quadTo`, что даёт **квадратичные кривые Безье** (`Q`). | Существенное отличие в качестве сглаживания. |
| **Path - формат d** | Строго ограничен грамматикой (только M/m, L/l), описан BNF в XEP-0113. | Полноценный SVG path (может включать `Q`, `C`, `M`, `L` и др.). | Psi не ограничивается подмножеством XEP-0113. |
| **Атрибуты стиля path** | `stroke`, `stroke-width`, `id` (опц.). По умолчанию stroke=#000000, stroke-width=1 | `stroke`, `stroke-width`, `stroke-linecap`, `fill`, `fill-opacity`, `transform`, `id`, `xmlns:xlink` (для image) и др. | Расширенный набор SVG-атрибутов. |
| **Преобразования (transforms)** | Отсутствуют. Перемещение — команда `<move>`. | Полноценные SVG transforms (матрицы). Реализованы в `WbItem::mouseMoveEvent()`, сериализованы в атрибут через `WbItem::regenerateTransform()`, `WbItem::parseSvgTransform()`, `WbItem::toSvgTransform()`. | Кардинальное отличие в модели трансформаций. |
| **ViewBox/геометрия** | Не специфицирована. | Атрибут `viewBox` корневого `<svg>`; меняется через `WbDlg::setGeometry()` и учитывается в `WbWidget::checkForViewBoxChange()`. | Холст имеет явные размеры/viewport. |
| **Изображения** | Не поддерживаются. | Поддерживаются (`Mode::DrawImage`). Сериализация — `WbNewImage::serializeToSvg()`, изображение кодируется как data URI base64. | Существенное расширение функциональности. |
| **Группы** | Не поддерживаются. | Элементы `<g>` с операциями `WbScene::group()` и `WbScene::ungroup()`; группы могут иметь собственные трансформации. | Расширенная функциональность редактирования. |

## 7. Сравнение операций и команд

| Операция | XEP-0113 | Реализация Psi | Детали реализации (символы) |
|---|---|---|---|
| **Добавление элемента** | `<path d="..." stroke="..." stroke-width="..." id="..."/>` | SXE-элементы `<new>` (элемент + атрибуты) добавляются в общий DOM. | `WbNewPath::serializeToSvg()`, `WbNewImage::serializeToSvg()`, `WbNewItem::serializeToSvg()`, `SxeSession::insertNodeAfter()`. Новым элементам присваивается уникальный `id`. |
| **Перемещение** | `<move id="X" dx="n" dy="n"/>` (относительное) | Через SVG transform matrix. Не отдельная команда, а изменение атрибута `transform`. | `WbItem::mouseMoveEvent()` применяет QGraphicsItem-трансформацию, `WbItem::regenerateTransform()` конвертирует её в SVG matrix и вызывает `SxeSession::setAttribute(node, "transform", …)`. |
| **Удаление** | `<delete id="X"/>` | `SxeSession::removeNode()`. | Удаление инициирует `WbWidget::clear()` либо пользовательский ввод; визуальные элементы удаляются по сигналу `nodeToBeRemoved` через `WbWidget::removeWbItem()` и `WbWidget::checkForRemovalOfId()`. |
| **Изменение атрибутов** | Не предусмотрено. Требуется удалить и создать новый элемент. | Любое изменение через `SxeSession::setAttribute()` / `SxeSession::setNodeValue()`. | Примеры: `WbWidget::setSize()` (viewBox), `WbItem::regenerateTransform()` (transform). |
| **Группировка** | Отсутствует. | `WbScene::group()` — создаёт `<g>`, перемещает выделенные узлы внутрь группы, сбрасывает выделение. | `wbscene.cpp` |
| **Разгруппировка** | Отсутствует. | `WbScene::ungroup()` — извлекает детей из `<g>`, комбинирует трансформации группы с дочерними, удаляет группу. | `wbscene.cpp` |
| **Изменение Z-order (слои)** | Отсутствует. | `WbScene::bringForward()`, `WbScene::bringToFront()`, `WbScene::sendBackwards()`, `WbScene::sendToBack()` (общая логика — `WbScene::bring()`). | Перестановка DOM-узлов через `SxeSession::insertNodeBefore()`/`insertNodeAfter()`. |
| **Очистка доски** | Не определена. Предлагается удалять все пути по ID. | `WbWidget::clear()` — удаляет все `WbItem`-узлы из корневого `<svg>`. | `wbwidget.cpp` |
| **Обновление документа (remote/local)** | Обработка входящих `<message>` с SWB-расширением. | Обработка SXE-сигналов: `documentUpdated`, `nodeAdded`, `nodeMoved`, `nodeToBeRemoved`, `chdataChanged`. | Подписки в конструкторе `WbWidget`; обработчики `WbWidget::handleDocumentUpdated()`, `WbWidget::queueNodeInspection()`, `WbWidget::inspectNodes()`. |

## 8. Модель идентификаторов и управление состоянием

| Аспект | XEP-0113 | Реализация Psi | Примечания |
|---|---|---|---|
| **Требовательность к ID** | Атрибут `id` опционален для `<path>`. Без `id` путь нельзя переместить/удалить командами `<move>`/`<delete>`. | Атрибут `id` активно гарантируется для управляемых элементов. | `WbItem::addToScene()`: если у узла нет `id` — генерирует `id = "e" + SxeSession::generateUUID()` и вызывает `SxeSession::setAttribute(node, "id", id)`. |
| **RID vs `id`** | Есть только `id`, задаваемый клиентом. | Два разных идентификатора: SXE `rid` (идентифицирует запись/узел для протокола) и SVG-атрибут `id` (идентификатор для приложения). | Существенное отличие модели. См. раздел 4.4. |
| **Генерация ID** | На усмотрение клиента. Формат не предписан. | UUID-подобный с префиксом `e`. | `SxeSession::generateUUID()`, `WbNewPath::serializeToSvg()`, `WbNewImage::serializeToSvg()`, `WbScene::group()`. |
| **Управление ID-less элементами** | Не рассматривается. | Есть механизмы: `idlessItems_`, слоты `WbWidget::addIds()`, `WbWidget::addToIdLess()`, `WbWidget::checkForRemovalOfId()`. | Система следит за элементами без `id` и пытается добавить его при обновлении документа. |
| **Отслеживание изменений** | Командная модель (дельты). Полная синхронизация состояния не описана. | Полноценная синхронизация DOM: `recentlyRelocatedNodes_`, `WbWidget::queueNodeInspection()`, `WbWidget::inspectNodes()`. | Обеспечивают соответствие визуальных элементов DOM-узлам. |
| **Консистентность состояния** | Легко нарушается при потере сообщений (XMPP best-effort). | SXE синхронизирует записи DOM между участниками (collaborative editing) с учётом версий. | Архитектурное преимущество SXE-подхода. |

## 9. Режимы редактирования, UI и функциональность

XEP-0113 не определяет пользовательский интерфейс — только протокол обмена. Psi предоставляет богатый UI с множеством режимов редактирования.

| Возможность | XEP-0113 | Реализация Psi | Детали |
|---|---|---|---|
| **Режимы редактирования** | Только создание пути (freehand drawing). Другие операции — команды move/delete. | Enum `WbWidget::Mode`: `Select`, `Translate`, `Rotate`, `Scale`, `Scroll`, `Erase`, `DrawPath`, `DrawLine`, `DrawRectangle`, `DrawEllipse`, `DrawCircle`, `DrawPolyline`, `DrawText`, `DrawImage`. | Многие режимы (Line/Rect/Ellipse/Circle/Polyline/Text) в UI закомментированы, но инфраструктура заложена; обработка ввода — в `WbWidget::mousePressEvent()`. |
| **Select/Rubber band** | Нет. | Да. `Mode::Select` с `QGraphicsView::RubberBandDrag`. | `WbWidget::setMode()`. |
| **Translate/Rotate/Scale** | Перемещение только командой move (трансляция). Поворот/масштаб не предусмотрены. | Интерактивные трансформации выбранных элементов. | `WbItem::mouseMoveEvent()`, центр выделения — `WbScene::selectionCenter()`. |
| **Erase** | Эквивалент delete по `id` (выбор элемента не специфицирован). | Режим стирания `Mode::Erase`. | В этом режиме меняется взаимодействие (cross cursor, non-interactive), см. `WbWidget::setMode()`. |
| **Scroll/Pan** | Нет. | `Mode::Scroll` с `ScrollHandDrag`. | Позволяет перемещаться по холсту. |
| **DrawPath (freehand)** | Единственный способ рисования. | Основной режим — генерация сглаженных путей. | `WbWidget::mousePressEvent()`, `WbWidget::mouseMoveEvent()`, `WbWidget::mouseReleaseEvent()`, `WbNewPath`. |
| **DrawImage** | Нет. | Вставка изображений (выбор файла, кодирование в base64). | `Mode::DrawImage`, `WbNewImage`. |
| **UI: выбор цвета** | Нет (только атрибут `stroke` в команде). | Выбор цвета обводки (`act_color_`) и заливки (`act_fill_`). | `WbDlg::setStrokeColor()`, `WbDlg::setFillColor()`. |
| **UI: толщина линии** | Нет. | Группы толщин (thin/medium/thick) с иконками, меню. | `WbDlg::setStrokeWidth()`. |
| **UI: тулбар и меню** | Нет. | Тулбар с действиями save/geometry/clear/end и селекторами цвета/ширины/режима; контекстное меню для элементов. | `WbDlg`, `WbItem::contextMenuEvent()`, `WbItem::constructContextMenu()`. |
| **Сохранение в SVG** | Не определено. | Да, `act_save_` → `WbDlg::save()`. | `wbdlg.cpp` |
| **Изменение геометрии холста** | Нет. | `WbDlg::setGeometry()` — диалог для изменения `viewBox`. | `wbdlg.cpp` |

## 10. Особенности генерации графики и оптимизации

| Аспект | XEP-0113 | Реализация Psi | Комментарии |
|---|---|---|---|
| **Модель рисования freehand** | Ломаные линии: добавление `L` при каждом mouse move; рекомендуется не записывать каждое движение. | Сглаживание квадратичными кривыми Безье: `controlPoint_` чередуется, при наличии используется `quadTo(*controlPoint_, newPos)`. | `WbNewPath::parseCursorMove()`. Даёт более плавные линии, чем чистые ломаные. |
| **Тайминг/интерполяция** | Рекомендация «dropping mouse events whose locations would be accurately interpolated» для экономии karma. | Есть таймер `adding_` и флаг `addVertex_`. | Поля `WbWidget`; баланс между плавностью и размером данных. |
| **Сериализация временных элементов** | Неприменимо (не определено). | `WbNewItem::serializeToSvg()` рендерит элемент через `QSvgGenerator`, парсит результат и добавляет уникальные `id` детям. | Использует Qt SVG generator для получения корректного SVG. |
| **Оптимизация путей при сериализации** | Рекомендуется использовать относительные координаты (`l` вместо `L`) для уменьшения размера. | `WbNewPath::serializeToSvg()` «обрезает» лишние вложенные `<g>` и копирует релевантные атрибуты (`stroke`, `stroke-width`, `stroke-linecap`, `fill`, `fill-opacity`) в сам `<path>`. | Оптимизация структуры SVG, а не минимизация координат. |
| **Размер данных / karma** | Проблема karma (jabberd) явно упомянута; даны советы по оптимизации. | SXE передаёт `<new>`/`<set>`/`<remove>`; для изменений атрибутов (трансформации) это компактно, но path с кривыми может быть больше ломаных `L`-команд. | Компромисс: качество против размера. |

## 11. Обработка изображений, текста и специальных случаев

| Возможность | XEP-0113 | Реализация Psi | Комментарии |
|---|---|---|---|
| **Изображения** | Не предусмотрены. | Поддерживаются (`Mode::DrawImage`). | `WbNewImage::serializeToSvg()`: читает файл, конвертирует в base64, формирует `<image>` с `xmlns:xlink` и `xlink:href="data:image/...;base64,..."`, задаёт `x`, `y`. |
| **Текст** | Нет явной поддержки. Предлагается представлять символы как пути (Hershey fonts). | Частично заложен: `Mode::DrawText` есть в enum, но соответствующий action в UI закомментирован; класса `WbNewText` нет. | Функциональность не реализована, но архитектурно предусмотрена. |
| **Очистка экрана** | Не определена в спецификации. | `WbWidget::clear()` удаляет все `WbItem`-узлы из корневого SVG. | Простое удаление всех управляемых элементов. |
| **Групповая работа (MUC)** | Поддерживается (`type='groupchat'`). | Поддерживается через SXE-сессии; `WbDlg` хранит флаг `groupChat_`. | SXE работает и в 1:1, и в групповых контекстах. |
| **Валидация/безопасность** | Специальных требований безопасности нет. | Стандартные практики Qt/SVG; изображения вставляются как data URI. | Явной фильтрации SVG в коде нет. |

## 12. Обнаружение поддержки (feature discovery) и интеграция с клиентом

| Аспект | XEP-0113 | Реализация Psi | Ссылки |
|---|---|---|---|
| **Протокольный feature** | `http://jabber.org/protocol/swb` | `http://jabber.org/protocol/sxe` (`SXENS`) | `sxesession.h` |
| **Application feature** | — (тип задан namespace’ом SWB) | `http://www.w3.org/2000/svg` (`WBNS`) | `#define WBNS` в `wbmanager.h` |
| **Discovery** | Рекомендуется XEP-0030, детали не специфицированы. | `SxeManager::checkSupport()` проверяет `SXENS` **и** переданные features (среди них `WBNS`). | `wbmanager.cpp` (`WbManager::openWhiteboard()` формирует список features) |
| **Invitation callback** | Не определён. | `SxeManager` эмитит `invitationCallback(Jid, QList<QString>, bool*)`; `WbManager::checkInvitation()` подключается к нему и при наличии `WBNS` предлагает пользователю принять/отклонить. | `WbManager::requestActivated()`, класс `WbRequest` |
| **Интеграция с PsiAccount** | Неприменимо. | `WbManager` принимает `PsiAccount*`, передаёт диалогам; `WbDlg` отображает аккаунт через `AccountLabel`. | `wbmanager.h`, `wbdlg.cpp` |
| **Обработка ухода участника** | Не специфицировано. | SXE-сигнал `peerLeftSession()`; `WbDlg::peerLeftSession()` обновляет заголовок/текст. | `wbmanager.cpp`, `wbdlg.cpp` |

## 13. Сводная таблица ключевых отличий

| Критерий | XEP-0113 | Psi Whiteboarding | Степень отличия |
|---|---|---|---|
| **Подход к синхронизации** | Message-based (команды в `<message>`) | **SXE-based** (Shared XML Editing, совместное редактирование DOM) | **Критическое** |
| **Протокольный namespace** | `http://jabber.org/protocol/swb` | `http://jabber.org/protocol/sxe` | **Критическое** |
| **Application feature** | — | `http://www.w3.org/2000/svg` (`WBNS`) | Существенное |
| **Формат данных** | Только SWB-элементы (path/move/delete) | Полноценный **SVG DOM** | **Критическое** |
| **Геометрия путей** | Только ломаные (M/m, L/l) | Сглаженные **квадратичные кривые Безье** (`quadTo`) | Существенное |
| **Трансформации** | Отдельная команда `move` (только смещение) | **SVG transform matrices** (translate/rotate/scale) | Существенное |
| **Структура документа** | Набор изолированных команд/элементов | Иерархический **SVG DOM** с группировкой (`<g>`) | Существенное |
| **Поддержка изображений** | Нет | **Есть** (data URI base64) | Существенное |
| **Управление слоями (Z-order)** | Нет | **Есть** (bring/send to front/back) | Значительное |
| **Группировка** | Нет | **Есть** (group/ungroup) | Значительное |
| **Режимы редактирования** | Только рисование | Много режимов (select/transform/erase/scroll/draw/image) | Значительное |
| **Модель состояний** | Дельтовая (команды) | **Полное состояние (DOM)** с версионированием записей | Значительное |
| **Требование ID** | Опционально (без ID нельзя оперировать) | **Автоматически генерируется** | Умеренное |
| **Сохранение** | Не определено | **Есть** (экспорт в SVG) | Значительное |
| **Расширяемость** | Намеренно не расширяемый | Высоко расширяемый (база на SVG + DOM) | Принципиальное |

## 14. Выводы и рекомендации для реализации в других клиентах

### 14.1 Ключевой вывод

Реализация whiteboarding в Psi **не является реализацией XEP-0113** в строгом смысле. Она использует иной подход: коллаборативное редактирование SVG DOM через **Shared XML Editing (XEP-0284)** вместо обмена командами SWB в XMPP-сообщениях. Протокольный namespace — `http://jabber.org/protocol/sxe`, тогда как `http://www.w3.org/2000/svg` — это application feature (тип документа).

### 14.2 Когда выбирать подход XEP-0113

Рекомендуется при следующих приоритетах:
- **Максимальная простота** реализации (минимальный объём кода);
- **Совместимость** с другими клиентами, реализующими именно XEP-0113;
- **Минимальные зависимости** (только XMPP, без SXE);
- **Лёгкость** отладки и понимания протокола;
- Работа в очень ограниченных окружениях.

**Особенности реализации по XEP-0113:** использовать сообщения с `<x xmlns="http://jabber.org/protocol/swb">`, обрабатывать только `path`/`move`/`delete` с ограниченным подмножеством SVG path (`M/m`, `L/l`).

### 14.3 Когда выбирать подход Psi (SXE + SVG)

Рекомендуется при следующих приоритетах:
- **Богатая функциональность** (трансформации, группировка, изображения, слои);
- **Качество рисования** (сглаженные кривые);
- **Надёжная синхронизация** состояния документа (DOM-based, с версиями записей);
- **Расширяемость** под будущие нужды (естественный путь к полному SVG);
- **Интерактивное редактирование** (select/rotate/scale/move с визуальным feedback).

### 14.4 Практические рекомендации для реализации

1. **Чётко определить целевую совместимость.** Для взаимодействия с Psi нужно реализовывать профиль SXE (`http://jabber.org/protocol/sxe` + `http://www.w3.org/2000/svg`), а не XEP-0113.
2. **Учесть различие профилей SXE.** Psi использует раннюю схему с `<negotiation>`; современная XEP-0284 использует Jingle и `urn:xmpp:sxe:0`. Редактирующие элементы (`<new>`/`<set>`/`<remove>`) в обоих профилях одинаковы.
3. **Если выбирать путь, близкий к Psi:**
   - использовать коллаборативную синхронизацию DOM (SXE или аналог);
   - хранить документ как SVG;
   - генерировать сглаженные пути (`quadTo`/Bezier) для лучшего UX;
   - автоматически назначать `id` всем элементам;
   - предпочитать трансформации через SVG transform matrices, а не дельты move.
4. **Обработка freehand:** `quadTo` даёт сглаживание без чрезмерного раздувания размера пути по сравнению с очень плотными `L`-точками.
5. **Архитектурный шаблон из Psi:** чёткое разделение временных элементов (`WbNewItem`) при рисовании и зафиксированных (`WbItem`), сериализация через SVG generator — удачное решение.

## 15. Список использованных файлов исходного кода

Для анализа были изучены следующие файлы модуля whiteboarding:

- [`wbmanager.h`](../psi-whiteboard/wbmanager.h), [`wbmanager.cpp`](../psi-whiteboard/wbmanager.cpp) — менеджер сессий и диалогов;
- [`wbdlg.h`](../psi-whiteboard/wbdlg.h), [`wbdlg.cpp`](../psi-whiteboard/wbdlg.cpp) — UI диалогового окна;
- [`wbwidget.h`](../psi-whiteboard/wbwidget.h), [`wbwidget.cpp`](../psi-whiteboard/wbwidget.cpp) — основной виджет и логика редактирования;
- [`wbscene.h`](../psi-whiteboard/wbscene.h), [`wbscene.cpp`](../psi-whiteboard/wbscene.cpp) — сцена, группировка, Z-order;
- [`wbitem.h`](../psi-whiteboard/wbitem.h), [`wbitem.cpp`](../psi-whiteboard/wbitem.cpp) — элементы на сцене, трансформации;
- [`wbnewitem.h`](../psi-whiteboard/wbnewitem.h), [`wbnewitem.cpp`](../psi-whiteboard/wbnewitem.cpp) — базовый класс временных элементов;
- [`wbnewpath.h`](../psi-whiteboard/wbnewpath.h), [`wbnewpath.cpp`](../psi-whiteboard/wbnewpath.cpp) — рисование путей (freehand);
- [`wbnewimage.h`](../psi-whiteboard/wbnewimage.h), [`wbnewimage.cpp`](../psi-whiteboard/wbnewimage.cpp) — вставка изображений;
- [`CMakeLists.txt`](CMakeLists.txt) — сборка модуля;
- документы и правила: [`AGENTS.md`](AGENTS.md), [`CLAUDE.md`](CLAUDE.md), [`.windsurfrules`](.windsurfrules), [`.cursor/rules/*`](.cursor/rules/).

Кроме того, изучались исходники SXE из дерева Psi (`src/sxe/`): `sxemanager.cpp`, `sxesession.h`, `sxerecord.h`/`sxerecord.cpp`, `sxenewedit.cpp`, `sxerecordedit.cpp`, `sxeremoveedit.cpp`. В данной рабочей копии присутствует только модуль `whiteboarding/`, поэтому файлы SXE анализировались по репозиторию Psi.

## 16. Ссылки

1. [XEP-0113: Simple Whiteboarding](https://xmpp.org/extensions/xep-0113.html) — официальная спецификация (v0.2, Deferred, Informational).
2. [XEP-0284: Shared XML Editing (SXE)](https://xmpp.org/extensions/xep-0284.html) — протокол коллаборативного редактирования XML, используемый Psi (namespace `http://jabber.org/protocol/sxe`; стандартизованная редакция — Jingle + `urn:xmpp:sxe:0`).
3. [XEP-0166: Jingle](https://xmpp.org/extensions/xep-0166.html) — управление сессиями в стандартизованной редакции SXE.
4. [XEP-0030: Service Discovery](https://xmpp.org/extensions/xep-0030.html) — обнаружение поддержки.
5. [SVG 1.1 Specification](https://www.w3.org/TR/SVG11/) — формат SVG, используемый реализацией.
6. [Scalable Vector Graphics (SVG) Tiny 1.2](https://www.w3.org/TR/SVGTiny12/) — `baseProfile='tiny'`, используемый в `EMPTYWB`.
7. [`xep-svg-whiteboarding-minimal.xml`](xep-svg-whiteboarding-minimal.xml) / [`xep-svg-whiteboarding-extended.xml`](xep-svg-whiteboarding-extended.xml) — актуальный стандарт SVG-доски поверх SXE (Jingle + XEP-0284).
8. [`WHITEBOARD_PROFILE.md`](WHITEBOARD_PROFILE.md) — нормативные правила реализации; [`SVG_WHITEBOARD_VARIANTS.md`](SVG_WHITEBOARD_VARIANTS.md) — обзор вариантов.
9. [`xep-collaborative-svg-whiteboarding.xml`](xep-collaborative-svg-whiteboarding.xml) — **deprecated** черновик профиля Psi-native.
