# Implementation Rules for the Whiteboard Profile (SXE / XEP-0284)

Normative document for implementations of **Advanced Whiteboarding** (an SVG whiteboard over Shared XML Editing, XEP-0284).
It describes the mandatory and recommended rules, the conformance classes and a checklist.

> Russian version: [`WHITEBOARD_PROFILE.md`](WHITEBOARD_PROFILE.md)

## 1. Scope and Terminology

- The document describes two profiles of a single application type:
  - **Core** — the minimal profile (file `xep-svg-whiteboarding-minimal.xml`);
  - **Full** — the extended profile (file `xep-svg-whiteboarding-extended.xml`).
- The keywords **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, **MAY** are to be interpreted as described in RFC 2119/BCP 14.
- The **Psi-native** profile (namespace `http://jabber.org/protocol/sxe`, custom `<negotiation>`) is **deprecated**; new implementations MUST NOT use it. Psi will be updated to this standard.

## 2. Constants

| Purpose | Value |
|---|---|
| Jingle (core) | `urn:xmpp:jingle:1` |
| Jingle application type (whiteboard) | `urn:xmpp:jingle:apps:svg-whiteboard:0` |
| Jingle transport (SXE) | `urn:xmpp:jingle:transports:sxe` |
| SXE (the `<sxe>` element) | `urn:xmpp:sxe:0` |
| SVG document namespace | `http://www.w3.org/2000/svg` |
| XLink (for `<image>`) | `http://www.w3.org/1999/xlink` |
| HTTP File Upload (Full) | `urn:xmpp:http:upload:0` |

## 3. Conformance Classes

- **Core**: XMPP Core + XEP-0030 + XEP-0166 + XEP-0284 + XEP-0045 + SVG Tiny 1.2.
- **Full**: Core + optional extensions (XEP-0115, XEP-0363, XEP-0234, XEP-0353), negotiated separately.

A Full client MUST interoperate correctly with a Core peer without requiring the extensions to be present.

## 4. Discovery

- R4.1 An implementation MUST advertise the features `urn:xmpp:jingle:1`, `urn:xmpp:sxe:0`, `urn:xmpp:jingle:transports:sxe`, `urn:xmpp:jingle:apps:svg-whiteboard:0`.
- R4.2 An implementation SHOULD advertise the disco identity of category `collaboration` and type `sxe`.
- R4.3 A Full client SHOULD use XEP-0115 (Entity Capabilities) to determine the peer's capabilities.
- R4.4 A session MUST be started only if the peer advertises the whiteboard application namespace and the SXE transport.

## 5. Session (Jingle)

- R5.1 Session management MUST be performed per XEP-0166 (`session-initiate`/`session-accept`/`session-terminate`).
- R5.2 `<description>` MUST be in the namespace `urn:xmpp:jingle:apps:svg-whiteboard:0` (in the Core profile with no child elements).
- R5.3 `<transport>` MUST be in the namespace `urn:xmpp:jingle:transports:sxe` and MUST contain at least one `<host/>`.
- R5.4 When refusing because the application is unsupported, the `unsupported-applications` reason SHOULD be used.

## 6. Connecting and State Synchronization

- R6.1 The SXE payload MUST be an `<sxe xmlns='urn:xmpp:sxe:0'>` element inside a `<message>`.
- R6.2 `<sxe>` MUST contain `session` and `id`; `id` MUST be unique within the session for the sender.
- R6.3 Joining MUST be performed with a `<connect/>` element.
- R6.4 Transmission of the state MUST be bracketed by `<state>` with `<document-begin/>` … `<document-end/>`; the `prolog` of `<document-begin/>` contains the XML prolog as a `data:` URI (RFC 2397).
- R6.5 While transmitting the state, the sender MUST NOT send other `<sxe>` elements between `<document-begin/>` and `<document-end/>`.
- R6.6 The receiver MUST NOT apply incoming edits before processing `<document-end/>`.

## 7. Document

- R7.1 The root MUST be `<svg>` in the namespace `http://www.w3.org/2000/svg`; the canvas MUST be defined by the `viewBox` attribute.
- R7.2 SVG Tiny 1.2 SHOULD be used (`baseProfile='tiny'`).
- R7.3 Every drawable element SHOULD carry a unique `id` attribute (in the application namespace), independent of the SXE `rid`.
- R7.4 Ordering (z-order) MUST be controlled through `primary-weight` (and the secondary weight via `rid`), not through invented attributes.
- R7.5 Grouping MUST use `<g>`; when ungrouping, the group's transform MUST be composed into the children's transforms.
- R7.6 Transformations MUST be expressed with the SVG `transform` attribute (canonically `matrix(...)`).
- R7.7 Images: Core MUST use an inline `data:` URI; Full MAY use a URL (XEP-0363/XEP-0234) with a mandatory fallback to `data:`.
- R7.8 Metadata (`<title>`, `<desc>`, `<defs>`) MUST NOT be treated as drawable elements and SHOULD be preserved.
- R7.9 Text SHOULD be represented as paths (for example, with a stroke font); the profile introduces no separate text element.

## 8. Edits

- R8.1 Edits MUST be performed with the `<new>`/`<set>`/`<remove>` elements inside `<state>`.
- R8.2 `<new>` MUST contain `rid` and `type`; `parent` is mandatory everywhere except for the root.
- R8.3 `<set>` and `<remove>` MUST use the `target` attribute (NOT `rid`).
- R8.4 Partial replacement of character data SHOULD use `replacefrom`/`replacen` together with `chdata`.
- R8.5 The `rid` of removed records MUST NOT be reused within the session.
- R8.6 An implementation MUST handle non-commutative edits (`<set>`) correctly according to the XEP-0284 versioning model.

## 9. Extensions (Full Profile)

- R9.1 Extensions MUST be optional and negotiated; a Core peer MUST NOT be required to have them.
- R9.2 HTTP File Upload (XEP-0363) MUST be used only if the peer advertises `urn:xmpp:http:upload:0`.
- R9.3 Jingle File Transfer (XEP-0234) and Jingle Message Initiation (XEP-0353) MAY be used as alternative channels/ways of initiation.
- R9.4 When an extension is unavailable, an implementation MUST degrade to the corresponding Core behavior (for example, an inline `data:` URI).

## 10. Errors, Limits, Security

- R10.1 Images SHOULD be limited in size and format.
- R10.2 The document SHOULD be rendered without fetching external resources (except those explicitly allowed by a Full extension).
- R10.3 The XML prolog from the `prolog` attribute MUST be treated as untrusted input.
- R10.4 Edit access is available to all participants by default; access control is outside the profile's scope.
- R10.5 High-frequency edits (freehand) SHOULD be coalesced to save bandwidth.

## 11. Conformance Checklist

**Core:**
- [ ] The 4 features are advertised (R4.1) and the `collaboration/sxe` identity (R4.2).
- [ ] Jingle session with `<description>` and `<transport>`/`<host>` (R5.1–R5.3).
- [ ] `<connect/>`, state transmission via `<state>` (R6.3–R6.6).
- [ ] SVG Tiny 1.2, `viewBox`, `id`, `primary-weight` (R7.1–R7.4).
- [ ] Edits `<new>`/`<set target>`/`<remove target>` (R8.1–R8.3).
- [ ] Inline `data:` images (R7.7).

**Full (in addition):**
- [ ] Entity Capabilities (R4.3).
- [ ] Upload with fallback (R9.2, R9.4).
- [ ] Jingle FT / JMI as needed (R9.3).

## 12. References

- `xep-svg-whiteboarding-minimal.xml` — the minimal spec.
- `xep-svg-whiteboarding-extended.xml` — the extended spec.
- `SVG_WHITEBOARD_VARIANTS.en.md` — brief overview of the variants.
- `PSI_WHITEBOARDING_VS_XEP0113.en.md` — comparison with XEP-0113 and the deprecated Psi profile.
