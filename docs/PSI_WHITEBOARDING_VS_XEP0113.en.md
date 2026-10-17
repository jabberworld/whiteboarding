# Detailed Comparison of the Psi Whiteboarding Implementation with XEP-0113: Simple Whiteboarding

> **Status:** the Psi-native profile described here (`http://jabber.org/protocol/sxe`, custom `<negotiation>`, an early revision of SXE) is **deprecated**. The new **Advanced Whiteboarding** standard, built on Jingle (XEP-0166) and XEP-0284 (superseding XEP-0113), is described in `xep-svg-whiteboarding-minimal.xml` / `xep-svg-whiteboarding-extended.xml`; the normative rules are in `WHITEBOARD_PROFILE.en.md`; an overview of the variants and migration is in `SVG_WHITEBOARD_VARIANTS.en.md`. This document is kept as a comparative analysis and historical reference.

> Russian version: [`PSI_WHITEBOARDING_VS_XEP0113.md`](PSI_WHITEBOARDING_VS_XEP0113.md)

## Table of Contents

- [1. Introduction](#1-introduction)
- [2. Brief Overview of XEP-0113: Simple Whiteboarding](#2-brief-overview-of-xep-0113-simple-whiteboarding)
- [3. Architecture and Components of the Psi Implementation](#3-architecture-and-components-of-the-psi-implementation)
- [4. The SXE (Shared XML Editing) Protocol in Psi](#4-the-sxe-shared-xml-editing-protocol-in-psi)
- [5. Comparison of Transport and Synchronization Protocol](#5-comparison-of-transport-and-synchronization-protocol)
- [6. Comparison of Data Format and Supported Elements](#6-comparison-of-data-format-and-supported-elements)
- [7. Comparison of Operations and Commands](#7-comparison-of-operations-and-commands)
- [8. Identifier Model and State Management](#8-identifier-model-and-state-management)
- [9. Editing Modes, UI and Functionality](#9-editing-modes-ui-and-functionality)
- [10. Graphics Generation and Optimization Details](#10-graphics-generation-and-optimization-details)
- [11. Handling Images, Text and Special Cases](#11-handling-images-text-and-special-cases)
- [12. Capability Discovery (Feature Discovery) and Client Integration](#12-capability-discovery-feature-discovery-and-client-integration)
- [13. Summary Table of Key Differences](#13-summary-table-of-key-differences)
- [14. Conclusions and Recommendations for Other Clients](#14-conclusions-and-recommendations-for-other-clients)
- [15. List of Source Files Used](#15-list-of-source-files-used)
- [16. References](#16-references)

## 1. Introduction

This document is a detailed comparison of the whiteboarding module implementation in the Psi Jabber client with the official XEP-0113: Simple Whiteboarding protocol.

The Psi implementation (located in the `whiteboarding/` directory) differs substantially from XEP-0113 not only in details, but in its fundamental approach to synchronizing collaborative editing. Whereas XEP-0113 describes a minimalist command protocol over XMPP messages, Psi uses **SXE — Shared XML Editing** (XEP-0284) for real-time collaborative editing of an SVG DOM document.

> Terminology note: in the Psi sources and in some older discussions the abbreviation SXE was sometimes expanded as "Simple XML Exchange". The correct and official name of the protocol is **Shared XML Editing** (XEP-0284), authored by Joonas Govenius, who is also the author of whiteboarding in Psi.

## 2. Brief Overview of XEP-0113: Simple Whiteboarding

XEP-0113 (v0.2 of 2003-09-07, status Deferred, type Informational) defines an extremely simple protocol for exchanging drawings between participants of a Jabber connection.

**Key points of XEP-0113:**
- The protocol is based on XMPP `<message>` with the extension `<x xmlns="http://jabber.org/protocol/swb">`
- Supported elements: `<path>`, `<move>`, `<delete>`
- The path format is a heavily simplified SVG path with only the commands `M`, `m`, `L`, `l` (absolute/relative moveto and lineto)
- Attributes of `<path>`: `d` (required), `stroke` (optional, default `#000000`), `stroke-width` (optional, default `1`), `id` (optional)
- `<move id="..." dx="..." dy="..."/>` — relative movement of an element by its `id`
- `<delete id="..."/>` — deletion of an element by its `id`
- Scenarios: a single whiteboard message, a whiteboard chat session (with a thread), a whiteboard in a MUC (groupchat)
- The explicit goal is maximum simplicity of implementation

## 3. Architecture and Components of the Psi Implementation

The implementation is a whiteboarding module integrated with the Psi infrastructure and using SXE for synchronization. Components (source files):

| Class/Module | File | Purpose |
|---|---|---|
| **WbManager** | [`wbmanager.h`](../psi-whiteboard/wbmanager.h), [`wbmanager.cpp`](../psi-whiteboard/wbmanager.cpp) | Manager of whiteboard dialogs. Listens for SXE sessions, creates dialogs when a session is negotiated, handles invitations, and provides an API for opening a whiteboard. |
| **WbDlg** | [`wbdlg.h`](../psi-whiteboard/wbdlg.h), [`wbdlg.cpp`](../psi-whiteboard/wbdlg.cpp) | The dialog window of a whiteboard session (`AdvancedWidget`). Contains `WbWidget`, a toolbar with modes, stroke/fill/width selectors, and buttons to save/clear/end the session. |
| **WbWidget** | [`wbwidget.h`](../psi-whiteboard/wbwidget.h), [`wbwidget.cpp`](../psi-whiteboard/wbwidget.cpp) | The main visualization and editing widget. Handles user input (mouse), creates temporary items while drawing, manages editing modes, and coordinates synchronization with SXE. |
| **WbScene** | [`wbscene.h`](../psi-whiteboard/wbscene.h), [`wbscene.cpp`](../psi-whiteboard/wbscene.cpp) | A `QGraphicsScene` subclass. Manages the items on the scene, implements grouping/ungrouping, layer ordering, and regeneration of transforms. |
| **WbItem** | [`wbitem.h`](../psi-whiteboard/wbitem.h), [`wbitem.cpp`](../psi-whiteboard/wbitem.cpp) | Represents an existing SVG element on the scene (`QGraphicsSvgItem`). Handles transforms, the context menu, and synchronizes changes back to the DOM via SXE. |
| **WbNewItem** | [`wbnewitem.h`](../psi-whiteboard/wbnewitem.h), [`wbnewitem.cpp`](../psi-whiteboard/wbnewitem.cpp) | Base class for the temporary items created while drawing (before they are committed to the document). |
| **WbNewPath** | [`wbnewpath.h`](../psi-whiteboard/wbnewpath.h), [`wbnewpath.cpp`](../psi-whiteboard/wbnewpath.cpp) | Temporary item for freehand drawing (path). Generates smoothed curves (`QPainterPath::quadTo`) and serializes to SVG `<path>`. |
| **WbNewImage** | [`wbnewimage.h`](../psi-whiteboard/wbnewimage.h), [`wbnewimage.cpp`](../psi-whiteboard/wbnewimage.cpp) | Temporary item for inserting an image. Encodes the image as a `data:` URI (base64) on serialization. |

**Key infrastructure:** `SxeSession` and `SxeManager` from a separate `src/sxe` module in the Psi source tree are used (this working copy contains only the `whiteboarding/` module; the headers are included as `../sxe/...`). SXE implements collaborative editing of XML/DOM, and the root document is SVG.

**The empty document (`EMPTYWB`, declared in `wbmanager.cpp`):**
```xml
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg xmlns="http://www.w3.org/2000/svg" version="1.2" viewBox="0 0 600 400" baseProfile="tiny" />
```

## 4. The SXE (Shared XML Editing) Protocol in Psi

This section describes how synchronization is structured at the level of XMPP stanzas. Understanding this model is necessary for a correct comparison with XEP-0113 and for implementing a compatible client.

### 4.1 Overview and Namespace

- **Name:** Shared XML Editing (SXE), standardized as XEP-0284. The protocol lets several participants collaboratively edit an arbitrary XML document (in our case, SVG).
- **Protocol namespace:** `http://jabber.org/protocol/sxe` (defined in Psi by the macro `SXENS` in `sxesession.h`).
- **Application feature:** `http://www.w3.org/2000/svg` (the macro `WBNS` in `wbmanager.h`) — denotes the type of the edited document (SVG), not the protocol.
- **Support check:** `SxeManager::checkSupport()` requires **both** features: `SXENS` **and** the requested application features (that is, `WBNS`).
- **Host:** SXE does not require a central server. In a one-to-one session the host is the initiator; in a MUC the host is the room itself.

### 4.2 The `<sxe>` Envelope

Every change and every negotiation step is carried in a separate `<message>` stanza:

```xml
<message from='kingclaudius@shakespeare.lit/castle'
         to='laertes@shakespeare.lit/castle'>
  <sxe xmlns='http://jabber.org/protocol/sxe'
       session='851ba2' id='4'>
    ...
  </sxe>
</message>
```

- `session` — the session GUID (shared by all participants).
- `id` — the unique identifier of this carrier stanza.
- Inside `<sxe>` there is either a single `<negotiation>` (negotiation) or one or more editing elements.

### 4.3 Session Negotiation

Negotiation is carried out by the child elements of `<negotiation>`:

| Element | Meaning |
|---|---|
| `<invitation><feature>URI</feature>…</invitation>` | Invitation to start a session with a list of required application features |
| `<accept-invitation/>` | The invitee accepts the invitation |
| `<decline-invitation><alternative-session>GUID</alternative-session></decline-invitation>` | Refusal; may propose an existing session |
| `<abort-negotiation/>` | Aborts an unfinished negotiation |
| `<connect-request/>` | Joining an already existing session |
| `<history-offer/>` | Offer to transfer the current document state |
| `<accept-history/>` | The joiner accepts the offer of the state |
| `<document-begin prolog='data:…' available-uuid-prefix='…'/>` | Start of the state transfer; `prolog` contains the XML prolog (including the DOCTYPE) as a `data:` URI |
| *(editing elements)* | A document snapshot as a sequence of `<new>`/`<set>` |
| `<document-end used-sxe-ids='…'/>` | End of the state transfer |
| `<left-session/>` | Notification of leaving the session |

The negotiation logic is implemented in `SxeManager::processNegotiationMessage()`, `SxeManager::processNegotiationAsParticipant()` and `SxeManager::processNegotiationAsJoiner()`; initiation is in `SxeManager::startNewSession()`, and joining is in `SxeManager::joinSession()`.

### 4.4 Records and Editing Elements

SXE does not send "commands" over SVG directly. It maintains a set of **records**, each corresponding to a single DOM node, and synchronizes their fields:

| Field | Meaning |
|---|---|
| `rid` | Record ID — the GUID of the record (distinct from the SVG `id` attribute) |
| `type` | Node type: `element`, `attr`, `text`, `comment`, `processinginstruction` |
| `version` | The record's version (0 when created) |
| `parent` | `rid` of the parent record |
| `primary-weight` | Weight for ordering siblings (greater — higher/later) |
| `ns` | Namespace of the element/attribute |
| `name` | Name of the element/attribute |
| `chdata` | Character data (text, attribute value, comment) |
| `pitarget`, `pidata` | target/data for a processing instruction |

Changes are expressed by three elements (files `sxenewedit.cpp`, `sxerecordedit.cpp`, `sxeremoveedit.cpp`):

- `<new rid type parent primary-weight [name] [ns] [chdata] [pitarget] [pidata]/>` — create a record;
- `<set rid version [parent] [primary-weight] [name] [chdata] [replacefrom] [replacen] [pitarget] [pidata]/>` — change a record;
- `<remove rid/>` — remove a record.

The ordering of nodes among siblings is determined by `primary-weight` and, on ties, by the **secondary weight** (lexicographic comparison of `rid`), see `SxeRecord::operator<()` and `SxeRecord::hasSmallerSecondaryWeight()`.

### 4.5 Example: Drawing a Path

Creating a red triangle on the whiteboard is a single SXE stanza with several `<new>`:

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

Note: `insertNode/setAttribute/removeNode` from `SxeSession` is a client API, whereas what goes over the wire is exactly `<new>`/`<set>`/`<remove>` with `rid`/`version`/`primary-weight`.

### 4.6 Relationship to XEP-0284

Psi uses an **early (ProtoXEP) revision** of SXE: the session is negotiated with custom `<negotiation>` elements inside `<message>`, and the namespace is `http://jabber.org/protocol/sxe`. Later, XEP-0284 standardized session management via **Jingle (XEP-0166)** with the namespaces `urn:xmpp:sxe:0` and `urn:xmpp:jingle:transports:sxe`. At the same time, the **record and editing-element model remained the same**, so a client on XEP-0284 can exchange the same `<new>`/`<set>`/`<remove>`, but is not compatible with Psi's negotiation at the stanza level.

### 4.7 Formalized Description of the Profile

A description of the profile is formalized in this same repository. The current standard (based on XEP-0284) and the deprecated draft:

- [`xep-svg-whiteboarding-minimal.xml`](xep-svg-whiteboarding-minimal.xml) / [`.html`](xep-svg-whiteboarding-minimal.html) — the **current** minimal profile;
- [`xep-svg-whiteboarding-extended.xml`](xep-svg-whiteboarding-extended.xml) / [`.html`](xep-svg-whiteboarding-extended.html) — the **current** extended profile;
- [`WHITEBOARD_PROFILE.en.md`](WHITEBOARD_PROFILE.en.md) — the normative implementation rules;
- [`SVG_WHITEBOARD_VARIANTS.en.md`](SVG_WHITEBOARD_VARIANTS.en.md) — overview of the variants and migration;
- [`xep-collaborative-svg-whiteboarding.xml`](xep-collaborative-svg-whiteboarding.xml) / [`.html`](xep-collaborative-svg-whiteboarding.html) — the **deprecated** draft of the Psi-native profile;
- [`tools/xep2html.py`](tools/xep2html.py) — the XML → HTML converter.

## 5. Comparison of Transport and Synchronization Protocol

| Parameter | XEP-0113 | Psi implementation | Comments |
|---|---|---|---|
| **Protocol type** | Command-based, message-based. The extension `<x xmlns="http://jabber.org/protocol/swb">` inside `<message>`. | DOM synchronization, session-based, over SXE. Editing elements `<new>`/`<set>`/`<remove>` over a shared SVG DOM. | The key fundamental difference. XEP-0113 is a stateless exchange of commands; Psi is stateful collaborative editing of a document. |
| **Transport packets** | Only `<message>` (chat, groupchat). Supports a thread for a chat session. | Also `<message>`, but with an `<sxe xmlns="http://jabber.org/protocol/sxe">` payload; negotiation via `<negotiation>`. | Both use `<message>`, but the semantics are fundamentally different: a command versus a session element. |
| **Protocol namespace** | `http://jabber.org/protocol/swb` | `http://jabber.org/protocol/sxe` (`SXENS`) | Different protocols. |
| **Application feature** | None (the type is defined by the SWB namespace) | `http://www.w3.org/2000/svg` (`WBNS`) — the document type | Here SVG is the data format, not the protocol. |
| **Synchronization model** | Event/command model: send a command on an action (path/move/delete). Deltas only. | Records/edits: a shared SVG DOM is maintained, and node records are synchronized (create/change/delete). | Psi stores the full state of the whiteboard as an SVG DOM on all clients. |
| **Session management** | Not specified in the XEP. Uses standard XMPP mechanisms (a thread in chat, a room in MUC). | Explicit negotiation via `SxeManager` with `<negotiation>` elements; invitations are the `invitationCallback` signal, which `WbManager::checkInvitation()` turns into a user prompt. | Psi requires a negotiated SXE session. |
| **Session initiation** | May be a single message or the start of a chat (thread). | `WbManager::openWhiteboard()`: checks support, and if there is no dialog offers to open an existing SVG or creates `EMPTYWB`, then calls `SxeManager::startNewSession()`. | A more complex initiation with the possibility of loading an initial document. |
| **Session termination** | Not specified. | `WbDlg::endSession()` calls `SxeSession::endSession()`; a participant leaving is signaled by a `<left-session/>` element and the `peerLeftSession()` signal. | Explicit lifecycle management of the session. |
| **Feature discovery** | Service Discovery (XEP-0030) is recommended, but not detailed. | `SxeManager::checkSupport()` checks `SXENS` **and** `WBNS`; invitations are filtered by `WbManager::checkInvitation()` on the presence of `WBNS`. | Both features are needed. |

## 6. Comparison of Data Format and Supported Elements

| Element/Attribute | XEP-0113 | Psi implementation | Comments |
|---|---|---|---|
| **Root element** | `<x xmlns="http://jabber.org/protocol/swb">` | `<svg xmlns="http://www.w3.org/2000/svg" version="1.2" viewBox="..." baseProfile="tiny">` | Psi works directly with the SVG DOM, not an SWB wrapper. |
| **Supported graphics elements** | Only `<path>` | Any SVG elements present in the DOM: `<path>`, `<image>`, `<g>`, etc. | Much broader. Psi is essentially collaborative SVG editing. |
| **Path commands** | Only `M`, `m`, `L`, `l`. No curves, arcs, etc. | Generates an SVG path via `QPainterPath`. During freehand drawing (`WbNewPath::parseCursorMove()`) `quadTo` is used, producing **quadratic Bezier curves** (`Q`). | A substantial difference in smoothing quality. |
| **Path `d` format** | Strictly limited by the grammar (only M/m, L/l), with a BNF described in XEP-0113. | A full SVG path (may include `Q`, `C`, `M`, `L`, etc.). | Psi is not limited to the XEP-0113 subset. |
| **Path style attributes** | `stroke`, `stroke-width`, `id` (optional). Defaults: stroke=#000000, stroke-width=1 | `stroke`, `stroke-width`, `stroke-linecap`, `fill`, `fill-opacity`, `transform`, `id`, `xmlns:xlink` (for image), etc. | An extended set of SVG attributes. |
| **Transforms** | None. Movement is the `<move>` command. | Full SVG transforms (matrices). Implemented in `WbItem::mouseMoveEvent()`, serialized to the attribute via `WbItem::regenerateTransform()`, `WbItem::parseSvgTransform()`, `WbItem::toSvgTransform()`. | A cardinal difference in the transform model. |
| **ViewBox/geometry** | Not specified. | The `viewBox` attribute of the root `<svg>`; changed via `WbDlg::setGeometry()` and taken into account in `WbWidget::checkForViewBoxChange()`. | The canvas has explicit dimensions/viewport. |
| **Images** | Not supported. | Supported (`Mode::DrawImage`). Serialization in `WbNewImage::serializeToSvg()`; the image is encoded as a base64 `data:` URI. | A substantial functional extension. |
| **Groups** | Not supported. | `<g>` elements with the operations `WbScene::group()` and `WbScene::ungroup()`; groups may have their own transforms. | Extended editing functionality. |

## 7. Comparison of Operations and Commands

| Operation | XEP-0113 | Psi implementation | Implementation details (symbols) |
|---|---|---|---|
| **Adding an element** | `<path d="..." stroke="..." stroke-width="..." id="..."/>` | SXE `<new>` elements (element + attributes) are added to the shared DOM. | `WbNewPath::serializeToSvg()`, `WbNewImage::serializeToSvg()`, `WbNewItem::serializeToSvg()`, `SxeSession::insertNodeAfter()`. New elements are assigned a unique `id`. |
| **Movement** | `<move id="X" dx="n" dy="n"/>` (relative) | Via an SVG transform matrix. Not a separate command, but a change of the `transform` attribute. | `WbItem::mouseMoveEvent()` applies a QGraphicsItem transform; `WbItem::regenerateTransform()` converts it to an SVG matrix and calls `SxeSession::setAttribute(node, "transform", …)`. |
| **Deletion** | `<delete id="X"/>` | `SxeSession::removeNode()`. | Deletion is initiated by `WbWidget::clear()` or by user input; visual items are removed on the `nodeToBeRemoved` signal via `WbWidget::removeWbItem()` and `WbWidget::checkForRemovalOfId()`. |
| **Changing attributes** | Not provided for. Requires deleting and creating a new element. | Any change via `SxeSession::setAttribute()` / `SxeSession::setNodeValue()`. | Examples: `WbWidget::setSize()` (viewBox), `WbItem::regenerateTransform()` (transform). |
| **Grouping** | Absent. | `WbScene::group()` — creates a `<g>`, moves the selected nodes inside the group, resets the selection. | `wbscene.cpp` |
| **Ungrouping** | Absent. | `WbScene::ungroup()` — extracts the children from the `<g>`, combines the group's transforms with the children's, and removes the group. | `wbscene.cpp` |
| **Changing the Z-order (layers)** | Absent. | `WbScene::bringForward()`, `WbScene::bringToFront()`, `WbScene::sendBackwards()`, `WbScene::sendToBack()` (common logic in `WbScene::bring()`). | Reordering DOM nodes via `SxeSession::insertNodeBefore()`/`insertNodeAfter()`. |
| **Clearing the whiteboard** | Not defined. Suggesting deleting all paths by ID. | `WbWidget::clear()` — removes all `WbItem` nodes from the root `<svg>`. | `wbwidget.cpp` |
| **Document update (remote/local)** | Handling incoming `<message>` with the SWB extension. | Handling SXE signals: `documentUpdated`, `nodeAdded`, `nodeMoved`, `nodeToBeRemoved`, `chdataChanged`. | Subscriptions in the `WbWidget` constructor; handlers `WbWidget::handleDocumentUpdated()`, `WbWidget::queueNodeInspection()`, `WbWidget::inspectNodes()`. |

## 8. Identifier Model and State Management

| Aspect | XEP-0113 | Psi implementation | Notes |
|---|---|---|---|
| **ID requirement** | The `id` attribute is optional for `<path>`. Without an `id` a path cannot be moved/deleted by the `<move>`/`<delete>` commands. | The `id` attribute is actively guaranteed for managed elements. | `WbItem::addToScene()`: if a node has no `id`, it generates `id = "e" + SxeSession::generateUUID()` and calls `SxeSession::setAttribute(node, "id", id)`. |
| **RID vs `id`** | Only `id`, set by the client. | Two different identifiers: the SXE `rid` (identifies the record/node for the protocol) and the SVG `id` attribute (an identifier for the application). | A substantial difference in the model. See Section 4.4. |
| **ID generation** | Up to the client. The format is not prescribed. | UUID-like with the prefix `e`. | `SxeSession::generateUUID()`, `WbNewPath::serializeToSvg()`, `WbNewImage::serializeToSvg()`, `WbScene::group()`. |
| **Handling ID-less elements** | Not considered. | There are mechanisms: `idlessItems_`, the slots `WbWidget::addIds()`, `WbWidget::addToIdLess()`, `WbWidget::checkForRemovalOfId()`. | The system tracks elements without an `id` and tries to add one when the document is updated. |
| **Change tracking** | Command model (deltas). Full state synchronization is not described. | Full DOM synchronization: `recentlyRelocatedNodes_`, `WbWidget::queueNodeInspection()`, `WbWidget::inspectNodes()`. | They keep the visual elements in correspondence with the DOM nodes. |
| **State consistency** | Easily disrupted when messages are lost (XMPP best-effort). | SXE synchronizes DOM records between participants (collaborative editing) with versioning. | An architectural advantage of the SXE approach. |

## 9. Editing Modes, UI and Functionality

XEP-0113 does not define a user interface — only the exchange protocol. Psi provides a rich UI with many editing modes.

| Capability | XEP-0113 | Psi implementation | Details |
|---|---|---|---|
| **Editing modes** | Creating a path only (freehand drawing). Other operations are the move/delete commands. | Enum `WbWidget::Mode`: `Select`, `Translate`, `Rotate`, `Scale`, `Scroll`, `Erase`, `DrawPath`, `DrawLine`, `DrawRectangle`, `DrawEllipse`, `DrawCircle`, `DrawPolyline`, `DrawText`, `DrawImage`. | Many modes (Line/Rect/Ellipse/Circle/Polyline/Text) are commented out in the UI, but the infrastructure exists; input handling is in `WbWidget::mousePressEvent()`. |
| **Select/Rubber band** | No. | Yes. `Mode::Select` with `QGraphicsView::RubberBandDrag`. | `WbWidget::setMode()`. |
| **Translate/Rotate/Scale** | Movement only, via the move command (translation). No rotation/scaling. | Interactive transforms of the selected elements. | `WbItem::mouseMoveEvent()`, the selection center is `WbScene::selectionCenter()`. |
| **Erase** | Equivalent to delete by `id` (element selection is not specified). | The erase mode `Mode::Erase`. | In this mode the interaction changes (cross cursor, non-interactive), see `WbWidget::setMode()`. |
| **Scroll/Pan** | No. | `Mode::Scroll` with `ScrollHandDrag`. | Allows panning around the canvas. |
| **DrawPath (freehand)** | The only way to draw. | The main mode — generation of smoothed paths. | `WbWidget::mousePressEvent()`, `WbWidget::mouseMoveEvent()`, `WbWidget::mouseReleaseEvent()`, `WbNewPath`. |
| **DrawImage** | No. | Inserting images (file selection, base64 encoding). | `Mode::DrawImage`, `WbNewImage`. |
| **UI: color selection** | No (only the `stroke` attribute in the command). | Selection of the stroke color (`act_color_`) and fill color (`act_fill_`). | `WbDlg::setStrokeColor()`, `WbDlg::setFillColor()`. |
| **UI: line width** | No. | Width groups (thin/medium/thick) with icons and a menu. | `WbDlg::setStrokeWidth()`. |
| **UI: toolbar and menu** | No. | A toolbar with save/geometry/clear/end actions and color/width/mode selectors; a context menu for elements. | `WbDlg`, `WbItem::contextMenuEvent()`, `WbItem::constructContextMenu()`. |
| **Saving to SVG** | Not defined. | Yes, `act_save_` → `WbDlg::save()`. | `wbdlg.cpp` |
| **Changing the canvas geometry** | No. | `WbDlg::setGeometry()` — a dialog for changing the `viewBox`. | `wbdlg.cpp` |

## 10. Graphics Generation and Optimization Details

| Aspect | XEP-0113 | Psi implementation | Comments |
|---|---|---|---|
| **Freehand drawing model** | Polylines: appending `L` on every mouse move; it is recommended not to record every movement. | Smoothing with quadratic Bezier curves: `controlPoint_` alternates, and when present `quadTo(*controlPoint_, newPos)` is used. | `WbNewPath::parseCursorMove()`. Produces smoother lines than pure polylines. |
| **Timing/interpolation** | The recommendation "dropping mouse events whose locations would be accurately interpolated" to save karma. | There is an `adding_` timer and an `addVertex_` flag. | Fields of `WbWidget`; a balance between smoothness and data size. |
| **Serialization of temporary items** | Not applicable (not defined). | `WbNewItem::serializeToSvg()` renders the item via `QSvgGenerator`, parses the result and adds unique `id`s to the children. | Uses the Qt SVG generator to obtain valid SVG. |
| **Path optimization on serialization** | Relative coordinates (`l` instead of `L`) are recommended to reduce size. | `WbNewPath::serializeToSvg()` "trims" redundant nested `<g>` and copies the relevant attributes (`stroke`, `stroke-width`, `stroke-linecap`, `fill`, `fill-opacity`) onto the `<path>` itself. | Optimization of the SVG structure, not minimization of coordinates. |
| **Data size / karma** | The karma problem (jabberd) is explicitly mentioned; optimization advice is given. | SXE sends `<new>`/`<set>`/`<remove>`; for attribute changes (transforms) this is compact, but a path with curves may be larger than polyline `L` commands. | A trade-off: quality versus size. |

## 11. Handling Images, Text and Special Cases

| Capability | XEP-0113 | Psi implementation | Comments |
|---|---|---|---|
| **Images** | Not provided for. | Supported (`Mode::DrawImage`). | `WbNewImage::serializeToSvg()`: reads the file, converts to base64, builds an `<image>` with `xmlns:xlink` and `xlink:href="data:image/...;base64,..."`, and sets `x`, `y`. |
| **Text** | No explicit support. Representing characters as paths (Hershey fonts) is suggested. | Partially provided for: `Mode::DrawText` is in the enum, but the corresponding UI action is commented out; there is no `WbNewText` class. | The functionality is not implemented, but is architecturally anticipated. |
| **Clearing the screen** | Not defined in the specification. | `WbWidget::clear()` removes all `WbItem` nodes from the root SVG. | A simple removal of all managed elements. |
| **Group work (MUC)** | Supported (`type='groupchat'`). | Supported via SXE sessions; `WbDlg` keeps the `groupChat_` flag. | SXE works in both 1:1 and group contexts. |
| **Validation/security** | No special security requirements. | Standard Qt/SVG practices; images are inserted as `data:` URIs. | There is no explicit SVG filtering in the code. |

## 12. Capability Discovery (Feature Discovery) and Client Integration

| Aspect | XEP-0113 | Psi implementation | References |
|---|---|---|---|
| **Protocol feature** | `http://jabber.org/protocol/swb` | `http://jabber.org/protocol/sxe` (`SXENS`) | `sxesession.h` |
| **Application feature** | — (the type is defined by the SWB namespace) | `http://www.w3.org/2000/svg` (`WBNS`) | `#define WBNS` in `wbmanager.h` |
| **Discovery** | XEP-0030 is recommended; the details are not specified. | `SxeManager::checkSupport()` checks `SXENS` **and** the passed features (among them `WBNS`). | `wbmanager.cpp` (`WbManager::openWhiteboard()` builds the feature list) |
| **Invitation callback** | Not defined. | `SxeManager` emits `invitationCallback(Jid, QList<QString>, bool*)`; `WbManager::checkInvitation()` connects to it and, on the presence of `WBNS`, prompts the user to accept/decline. | `WbManager::requestActivated()`, the `WbRequest` class |
| **Integration with PsiAccount** | Not applicable. | `WbManager` receives a `PsiAccount*` and passes it to the dialogs; `WbDlg` displays the account via `AccountLabel`. | `wbmanager.h`, `wbdlg.cpp` |
| **Handling a participant leaving** | Not specified. | The SXE signal `peerLeftSession()`; `WbDlg::peerLeftSession()` updates the title/text. | `wbmanager.cpp`, `wbdlg.cpp` |

## 13. Summary Table of Key Differences

| Criterion | XEP-0113 | Psi Whiteboarding | Degree of difference |
|---|---|---|---|
| **Synchronization approach** | Message-based (commands in `<message>`) | **SXE-based** (Shared XML Editing, collaborative DOM editing) | **Critical** |
| **Protocol namespace** | `http://jabber.org/protocol/swb` | `http://jabber.org/protocol/sxe` | **Critical** |
| **Application feature** | — | `http://www.w3.org/2000/svg` (`WBNS`) | Substantial |
| **Data format** | Only SWB elements (path/move/delete) | A full **SVG DOM** | **Critical** |
| **Path geometry** | Polylines only (M/m, L/l) | Smoothed **quadratic Bezier curves** (`quadTo`) | Substantial |
| **Transforms** | A separate `move` command (displacement only) | **SVG transform matrices** (translate/rotate/scale) | Substantial |
| **Document structure** | A set of isolated commands/elements | A hierarchical **SVG DOM** with grouping (`<g>`) | Substantial |
| **Image support** | No | **Yes** (base64 `data:` URI) | Substantial |
| **Layer (Z-order) management** | No | **Yes** (bring/send to front/back) | Significant |
| **Grouping** | No | **Yes** (group/ungroup) | Significant |
| **Editing modes** | Drawing only | Many modes (select/transform/erase/scroll/draw/image) | Significant |
| **State model** | Delta-based (commands) | **Full state (DOM)** with record versioning | Significant |
| **ID requirement** | Optional (without an ID, operations are impossible) | **Automatically generated** | Moderate |
| **Saving** | Not defined | **Yes** (export to SVG) | Significant |
| **Extensibility** | Intentionally non-extensible | Highly extensible (based on SVG + DOM) | Fundamental |

## 14. Conclusions and Recommendations for Other Clients

### 14.1 Key Conclusion

The Psi whiteboarding implementation **is not an implementation of XEP-0113** in the strict sense. It uses a different approach: collaborative editing of an SVG DOM via **Shared XML Editing (XEP-0284)** instead of exchanging SWB commands in XMPP messages. The protocol namespace is `http://jabber.org/protocol/sxe`, whereas `http://www.w3.org/2000/svg` is an application feature (the document type).

### 14.2 When to Choose the XEP-0113 Approach

Recommended for the following priorities:
- **Maximum simplicity** of implementation (a minimal amount of code);
- **Compatibility** with other clients that implement XEP-0113;
- **Minimal dependencies** (XMPP only, without SXE);
- **Ease** of debugging and understanding the protocol;
- Operation in very constrained environments.

**Implementation specifics per XEP-0113:** use messages with `<x xmlns="http://jabber.org/protocol/swb">`, and handle only `path`/`move`/`delete` with the restricted SVG path subset (`M/m`, `L/l`).

### 14.3 When to Choose the Psi Approach (SXE + SVG)

Recommended for the following priorities:
- **Rich functionality** (transforms, grouping, images, layers);
- **Drawing quality** (smoothed curves);
- **Reliable synchronization** of document state (DOM-based, with record versions);
- **Extensibility** for future needs (a natural path to full SVG);
- **Interactive editing** (select/rotate/scale/move with visual feedback).

### 14.4 Practical Recommendations for Implementation

1. **Clearly define the target compatibility.** To interoperate with Psi, one must implement the SXE profile (`http://jabber.org/protocol/sxe` + `http://www.w3.org/2000/svg`), not XEP-0113.
2. **Account for the difference in SXE profiles.** Psi uses the early scheme with `<negotiation>`; the modern XEP-0284 uses Jingle and `urn:xmpp:sxe:0`. The editing elements (`<new>`/`<set>`/`<remove>`) are the same in both profiles.
3. **If choosing a path close to Psi:**
   - use collaborative DOM synchronization (SXE or an equivalent);
   - store the document as SVG;
   - generate smoothed paths (`quadTo`/Bezier) for a better UX;
   - automatically assign an `id` to all elements;
   - prefer transforms via SVG transform matrices rather than move deltas.
4. **Freehand handling:** `quadTo` gives smoothing without excessively bloating the path size compared with very dense `L` points.
5. **Architectural pattern from Psi:** a clear separation of temporary items (`WbNewItem`) during drawing from committed ones (`WbItem`), and serialization via the SVG generator, is a good solution.

## 15. List of Source Files Used

The following files of the whiteboarding module were studied for the analysis:

- [`wbmanager.h`](../psi-whiteboard/wbmanager.h), [`wbmanager.cpp`](../psi-whiteboard/wbmanager.cpp) — the session and dialog manager;
- [`wbdlg.h`](../psi-whiteboard/wbdlg.h), [`wbdlg.cpp`](../psi-whiteboard/wbdlg.cpp) — the dialog window UI;
- [`wbwidget.h`](../psi-whiteboard/wbwidget.h), [`wbwidget.cpp`](../psi-whiteboard/wbwidget.cpp) — the main widget and editing logic;
- [`wbscene.h`](../psi-whiteboard/wbscene.h), [`wbscene.cpp`](../psi-whiteboard/wbscene.cpp) — the scene, grouping, Z-order;
- [`wbitem.h`](../psi-whiteboard/wbitem.h), [`wbitem.cpp`](../psi-whiteboard/wbitem.cpp) — the items on the scene, transforms;
- [`wbnewitem.h`](../psi-whiteboard/wbnewitem.h), [`wbnewitem.cpp`](../psi-whiteboard/wbnewitem.cpp) — the base class of temporary items;
- [`wbnewpath.h`](../psi-whiteboard/wbnewpath.h), [`wbnewpath.cpp`](../psi-whiteboard/wbnewpath.cpp) — path drawing (freehand);
- [`wbnewimage.h`](../psi-whiteboard/wbnewimage.h), [`wbnewimage.cpp`](../psi-whiteboard/wbnewimage.cpp) — image insertion;
- [`CMakeLists.txt`](CMakeLists.txt) — the module build;
- documents and rules: [`AGENTS.md`](AGENTS.md), [`CLAUDE.md`](CLAUDE.md), [`.windsurfrules`](.windsurfrules), [`.cursor/rules/*`](.cursor/rules/).

In addition, the SXE sources from the Psi tree (`src/sxe/`) were studied: `sxemanager.cpp`, `sxesession.h`, `sxerecord.h`/`sxerecord.cpp`, `sxenewedit.cpp`, `sxerecordedit.cpp`, `sxeremoveedit.cpp`. This working copy contains only the `whiteboarding/` module, so the SXE files were analyzed from the Psi repository.

## 16. References

1. [XEP-0113: Simple Whiteboarding](https://xmpp.org/extensions/xep-0113.html) — the official specification (v0.2, Deferred, Informational).
2. [XEP-0284: Shared XML Editing (SXE)](https://xmpp.org/extensions/xep-0284.html) — the collaborative XML editing protocol used by Psi (namespace `http://jabber.org/protocol/sxe`; the standardized revision is Jingle + `urn:xmpp:sxe:0`).
3. [XEP-0166: Jingle](https://xmpp.org/extensions/xep-0166.html) — session management in the standardized revision of SXE.
4. [XEP-0030: Service Discovery](https://xmpp.org/extensions/xep-0030.html) — capability discovery.
5. [SVG 1.1 Specification](https://www.w3.org/TR/SVG11/) — the SVG format used by the implementation.
6. [Scalable Vector Graphics (SVG) Tiny 1.2](https://www.w3.org/TR/SVGTiny12/) — `baseProfile='tiny'`, used in `EMPTYWB`.
7. [`xep-svg-whiteboarding-minimal.xml`](xep-svg-whiteboarding-minimal.xml) / [`xep-svg-whiteboarding-extended.xml`](xep-svg-whiteboarding-extended.xml) — the current **Advanced Whiteboarding** standard (an SVG whiteboard over SXE, Jingle + XEP-0284).
8. [`WHITEBOARD_PROFILE.en.md`](WHITEBOARD_PROFILE.en.md) — the normative implementation rules; [`SVG_WHITEBOARD_VARIANTS.en.md`](SVG_WHITEBOARD_VARIANTS.en.md) — overview of the variants.
9. [`xep-collaborative-svg-whiteboarding.xml`](xep-collaborative-svg-whiteboarding.xml) — the **deprecated** draft of the Psi-native profile.
