# Submitting the Whiteboard Profile to the XSF

> Russian version: [`XSF_SUBMISSION.md`](XSF_SUBMISSION.md)

How to turn the profile in this repository into an XMPP Extension Protocol. The process facts are taken from XEP-0001, XEP-0143 and the editor documentation in the `xsf/xeps` repository (`docs/PROCESSING.md`, `docs/TRIAGING.md`).

## 1. What to submit

The work is split by layer into two submissions:

1. **One ProtoXEP, "SVG Whiteboarding"** (shortname `svg-whiteboard`, Standards Track, approver Council). It defines the Jingle application type and everything specific to whiteboards:
   - one-to-one sessions (Jingle, XEP-0353 proposals, editing rights through `senders`);
   - group chat whiteboards (an SXE session with the room as host);
   - the SVG document rules (root, namespaces, items, transforms, images, text);
   - security and privacy considerations.

   The namespace stays `urn:xmpp:jingle:apps:svg-whiteboard:0`, because Psi 1.6 already ships it. The submission should ask the Editor to keep it.
2. **A revision of XEP-0284 to 0.2**, made with the consent of its authors. It carries the points that concern Shared XML Editing in general:
   - the SXE session is the Jingle `sid`;
   - message delivery and XEP-0334 hints;
   - state transfer with current versions only;
   - the `ns` field;
   - Jingle `senders`;
   - payload on Jingle connections and protected payload;
   - group chat clarifications;
   - real Security Considerations and editorial fixes.

Everything defined in XEP-0284 stays there, and everything specific to SVG goes into the new document. Neither submission has to wait for the other.

XEP-0284 is Experimental (version 0.1.4). XEP-0113, Simple Whiteboarding, is Deferred; the new document may state that it supersedes XEP-0113.

## 2. What must change in the draft first

- **Legal notice:** XEP-0001 requires exactly the notices of the XSF IPR Policy. Replace the custom `<legal>` block with `&LEGALNOTICE;`. On submission, ownership of the text passes to the XSF.
- **Authors:** XEP-0001 requires first name, last name, email and JID for every author, so the placeholder author must be replaced with real ones.
- **One document:** merge the minimal and extended profiles. The extended text is a strict superset of the minimal one, so it can become the document, with its extensions marked as optional.
- **Header:** `<number>xxxx</number>`, `<status>ProtoXEP</status>`, shortname `svg-whiteboard`, and a single revision with version `0.0.1`. The Editor checks the last two before merging.
- **Sections:** the XEP template marks these as required: Security Considerations, Privacy Considerations, Accessibility Considerations, IANA Considerations, XMPP Registrar Considerations, and XML Schema (for protocol specifications). Business Rules and Implementation Notes are optional.
- **File:** a single file `inbox/svg-whiteboard.xml`; its name must not start with `xep-`.

## 3. Steps

### Before submitting

1. Agree with the Psi maintainer on co-authorship, and with the authors of XEP-0284 on the planned revision. A competing proposal would be the worst outcome.
2. Collect interop evidence. Two independent implementations (Psi and another.im) should have run the same session (proposal, state transfer, edits, ending), and the result should be noted in the submission or on the list.
3. Every author reads the XSF IPR Policy. Submitting a document means agreeing to it.

### ProtoXEP

1. Fork `github.com/xsf/xeps` and create a branch.
2. Copy the prepared document to `inbox/svg-whiteboard.xml`. Change no other file.
3. Validate and render it with the repository's own tools (`xmllint`, `xsltproc`):

   ```sh
   xmllint --nonet --noout --noent --loaddtd --valid inbox/svg-whiteboard.xml
   xsltproc --path . --param htmlbase "'../'" xep.xsl inbox/svg-whiteboard.xml > /tmp/svg-whiteboard.html
   ```

4. Make one commit and open a pull request titled `ProtoXEP: SVG Whiteboarding`.
5. The Editor checks the format, merges the PR and publishes the proposal under `xmpp.org/extensions/inbox/`, then announces it on standards@xmpp.org and asks the Council to accept it. Post your own short mail to standards@ with the motivation and the interop evidence.
6. Within 14 days the Council chair polls the members. If nobody objects, the Editor assigns a number, sets the status to Experimental, publishes version 0.1 and announces it.
7. If there are objections, address the feedback, revise the proposal and submit it again (a new PR updating the file in `inbox/`).

### Revision of XEP-0284

1. Discuss the change on standards@ with the XEP-0284 authors in copy.
2. Open a pull request against `xep-0284.xml` alone, titled `XEP-0284: …`. Add a revision block with version `0.2.0`; a substantive change bumps the minor number.
3. Because the change comes from someone other than the authors, the Editor labels it "Needs Author" and merges it once an author has explicitly agreed. If the Council considers the authors unresponsive, it may add another author.
4. For an Experimental XEP no Council vote is needed. A substantive revision restarts the 12-month clock after which an inactive XEP becomes Deferred.

## 4. Order

1. Merge the open profile PRs here.
2. Run the interop test between the two implementations.
3. Make the edits listed in section 2.
4. Get the agreement of the co-authors.
5. Submit the ProtoXEP, and in parallel discuss the XEP-0284 revision and open its PR.
