# Advanced Whiteboarding: Profile Variants (Overview)

A brief overview of the two versions of the new **Advanced Whiteboarding** standard (an SVG whiteboard over Shared XML Editing, XEP-0284). The standard supersedes **XEP-0113: Simple Whiteboarding** and describes the place of the deprecated Psi profile.

> Russian version: [`SVG_WHITEBOARD_VARIANTS.md`](SVG_WHITEBOARD_VARIANTS.md)

## Common Basis

Both variants are the same Jingle application type `urn:xmpp:jingle:apps:svg-whiteboard:0` with a common set of standards:

- XMPP Core
- XEP-0030 Service Discovery
- XEP-0166 Jingle (session management)
- XEP-0284 Shared XML Editing (records and edits)
- XEP-0045 Multi-User Chat (host for a group whiteboard)
- W3C SVG Tiny 1.2 (document format)

They differ only in the set of **optional** extensions. The application-type identifier is the same for both, so the choice of version does not affect compatibility at the namespace level.

## Comparison

| Capability | Minimal (Core) | Extended (Full) |
|---|---|---|
| Jingle session, SXE, MUC, SVG Tiny | required | required |
| Inline `data:` images | required | required (as fallback) |
| Entity Capabilities (XEP-0115) | — | recommended |
| HTTP File Upload (XEP-0363) for images | — | optional |
| Jingle File Transfer (XEP-0234) | — | optional |
| Jingle Message Initiation (XEP-0353) | — | optional |
| Document size | minimal | larger due to references/extensions |
| Implementation complexity | lower | higher |

A full client is compatible with a minimal peer: extensions are negotiated separately, and in their absence the Core behavior is used (in particular, an inline `data:` URI for images).

## When to Use Which

- **Minimal** — simple clients, embedded solutions, maximum compatibility and a minimal implementation surface.
- **Extended** — full-featured clients where saving traffic on images, efficient capability discovery and starting a whiteboard from a chat matter.

## Status of the Psi Profile

The old Psi profile (`http://jabber.org/protocol/sxe`, custom `<negotiation>`, an early revision of SXE) is **deprecated**. It is kept only as historical reference (the files `xep-collaborative-svg-whiteboarding.xml` and `PSI_WHITEBOARDING_VS_XEP0113.en.md`). New implementations must use the Jingle session and `urn:xmpp:sxe:0` according to XEP-0284.

## Mapping Psi-native → the New Standard

| Psi-native | New standard |
|---|---|
| `http://jabber.org/protocol/sxe` | `urn:xmpp:sxe:0` |
| `<negotiation>` (custom) | Jingle (XEP-0166) |
| `<invitation>`/`<accept-invitation>` | Jingle `session-initiate`/`session-accept` |
| `<connect-request>`/`<history-offer>`/`<accept-history>` | `<connect/>` + `<state-offer/>`/`<accept-state/>`/`<refuse-state/>` |
| `<document-begin>`/`<document-end>` in `<negotiation>` | inside `<state>` |
| `<set rid=...>`/`<remove rid=...>` | `<set target=...>`/`<remove target=...>` |
| `<left-session>` | Jingle `session-terminate` |
| application feature `http://www.w3.org/2000/svg` | Jingle app type `urn:xmpp:jingle:apps:svg-whiteboard:0` |

## Files

- `xep-svg-whiteboarding-minimal.xml` / `.html` — the minimal spec.
- `xep-svg-whiteboarding-extended.xml` / `.html` — the extended spec.
- `WHITEBOARD_PROFILE.en.md` — the normative implementation rules.
- `xep-collaborative-svg-whiteboarding.xml` — the deprecated draft (deprecated).
