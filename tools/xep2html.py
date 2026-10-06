#!/usr/bin/env python3
"""Render a XEP-style XML document to standalone HTML.

The project's specification is written in the XEP XML vocabulary
(section1/section2/section3, example, table, ...). Neither xsltproc nor
lxml are available in the build environment, so this small converter
implements the subset of the vocabulary used by the document.

Usage:
    python3 tools/xep2html.py INPUT.xml OUTPUT.html

Model: opencode-go/deepseek-v4.1-flash
"""

import html
import os
import re
import sys
import xml.etree.ElementTree as ET


def parse(path):
    """Parse the XEP XML, skipping the DOCTYPE (which references xep.dtd)."""
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    i = src.find("<!DOCTYPE")
    if i != -1:
        j = src.find("]>", i)
        if j != -1:
            src = src[:i] + src[j + 2 :]
        else:
            j = src.find(">", i)
            src = src[:i] + src[j + 1 :]
    return ET.fromstring(src)


INLINE = {"tt", "em", "strong", "link", "span", "cite", "br"}


def inline(el, *, drop=None):
    """Render mixed content (text + inline children) of el to HTML."""
    out = []
    if el.text:
        out.append(html.escape(el.text))
    for child in el:
        if drop and child.tag in drop:
            pass
        elif child.tag == "tt":
            out.append("<code>%s</code>" % inline(child))
        elif child.tag == "em":
            out.append("<em>%s</em>" % inline(child))
        elif child.tag == "strong":
            out.append("<strong>%s</strong>" % inline(child))
        elif child.tag == "link":
            url = child.get("url", "")
            out.append('<a href="%s">%s</a>' % (html.escape(url, quote=True), inline(child)))
        elif child.tag == "span":
            cls = child.get("class")
            attr = ' class="%s"' % html.escape(cls, quote=True) if cls else ""
            out.append("<span%s>%s</span>" % (attr, inline(child)))
        elif child.tag == "cite":
            out.append("<cite>%s</cite>" % inline(child))
        elif child.tag == "br":
            out.append("<br/>")
        else:
            out.append(inline(child))
        if child.tail:
            out.append(html.escape(child.tail))
    return "".join(out)


def code_block(el):
    return "<pre class=\"code\">%s</pre>" % html.escape(el.text or "")


def example(el):
    caption = el.get("caption", "")
    body = html.escape((el.text or "").strip("\n"))
    cap = '<figcaption>%s</figcaption>' % html.escape(caption) if caption else ""
    return '<figure class="code-example">%s<pre class="prettyprint">%s</pre></figure>' % (cap, body)


def table(el):
    out = ['<table>']
    caption = el.find("caption")
    if caption is not None:
        out.append('<caption>%s</caption>' % inline(caption))
    for tr in el.findall("tr"):
        out.append("<tr>")
        for cell in tr:
            if cell.tag in ("th", "td"):
                out.append("<%s>%s</%s>" % (cell.tag, inline(cell), cell.tag))
        out.append("</tr>")
    out.append("</table>")
    return "".join(out)


def render_list(el, tag):
    out = ["<%s>" % tag]
    for li in el.findall("li"):
        out.append("<li>%s</li>" % inline(li))
    out.append("</%s>" % tag)
    return "".join(out)


def render_dl(el):
    out = ["<dl>"]
    for di in el.findall("di"):
        dt = di.find("dt")
        dd = di.find("dd")
        if dt is not None:
            out.append("<dt>%s</dt>" % inline(dt))
        if dd is not None:
            out.append("<dd>%s</dd>" % inline(dd))
    out.append("</dl>")
    return "".join(out)


def render_block(el, number=None):
    tag = el.tag
    if tag == "p":
        return "<p>%s</p>" % inline(el)
    if tag == "ol":
        return render_list(el, "ol")
    if tag == "ul":
        return render_list(el, "ul")
    if tag == "dl":
        return render_dl(el)
    if tag == "table":
        return table(el)
    if tag == "example":
        return example(el)
    if tag == "code":
        return code_block(el)
    if tag == "note":
        return '<div class="note">%s</div>' % inline(el)
    if tag == "blockquote":
        return "<blockquote>%s</blockquote>" % inline(el)
    # unknown block: render inline content
    return "<p>%s</p>" % inline(el)


def section(el, number):
    topic = el.get("topic", "")
    anchor = el.get("anchor", "")
    level = int(el.tag[-1])  # section1 -> 1
    h = "h%d" % (level + 1)
    out = ['<%s id="%s">%s %s</%s>' % (h, html.escape(anchor, quote=True), number, html.escape(topic), h)]
    for child in el:
        if child.tag.startswith("section"):
            continue
        out.append(render_block(child))
    # nested sections, numbered
    counter = 0
    for child in el:
        if child.tag.startswith("section"):
            counter += 1
            out.append(section(child, "%s.%d" % (number, counter)))
    return "".join(out)


def toc(el, number, items):
    topic = el.get("topic", "")
    anchor = el.get("anchor", "")
    items.append((number, anchor, topic))
    counter = 0
    for child in el:
        if child.tag.startswith("section"):
            counter += 1
            toc(child, "%s.%d" % (number, counter), items)
    return items


def header_block(root):
    header = root.find("header")
    if header is None:
        return "", {}
    title = header.findtext("title", default="").strip()
    abstract = inline(header.find("abstract")) if header.find("abstract") is not None else ""
    meta = {
        "title": title,
        "abstract": abstract,
        "number": header.findtext("number", default="").strip(),
        "status": header.findtext("status", default="").strip(),
        "type": header.findtext("type", default="").strip(),
    }
    rev = header.find("revision")
    if rev is not None:
        meta["version"] = rev.findtext("version", default="").strip()
        meta["date"] = rev.findtext("date", default="").strip()
    deps = [d.text.strip() for d in header.findall("dependencies/spec") if d.text]
    meta["deps"] = deps
    authors = []
    for a in header.findall("author"):
        fn = a.findtext("firstname", default="").strip()
        sn = a.findtext("surname", default="").strip()
        authors.append(("%s %s" % (fn, sn)).strip())
    meta["authors"] = authors
    return title, meta


CSS = """
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
max-width:920px;margin:0 auto;padding:24px;line-height:1.55;color:#222}
h1{font-size:1.9em;border-bottom:2px solid #eee;padding-bottom:8px}
h2{font-size:1.45em;margin-top:1.8em;border-bottom:1px solid #eee;padding-bottom:4px}
h3{font-size:1.2em;margin-top:1.4em}
h4{font-size:1.05em;margin-top:1.2em}
code{background:#f5f5f5;padding:1px 4px;border-radius:3px;font-size:.92em}
pre.code,pre.prettyprint{background:#f6f8fa;border:1px solid #e1e4e8;border-radius:6px;
padding:12px;overflow-x:auto;font-size:.86em;line-height:1.45}
table{border-collapse:collapse;width:100%;margin:14px 0;font-size:.94em}
th,td{border:1px solid #ddd;padding:6px 9px;text-align:left;vertical-align:top}
th{background:#f3f3f3}
.abstract{font-style:italic;color:#555;background:#fafafa;border-left:4px solid #ccc;padding:12px 16px;margin:16px 0}
.docmeta{background:#fafafa;border:1px solid #eee;border-radius:6px;padding:12px 16px;font-size:.92em}
.docmeta dt{font-weight:600;float:left;clear:left;width:9em}
.docmeta dd{margin-left:9.5em}
.toc{background:#fafafa;border:1px solid #eee;border-radius:6px;padding:12px 16px}
.toc ol{list-style:none;padding-left:1em;margin:4px 0}
.toc a{text-decoration:none;color:#1a5fb4}
figure.code-example{margin:16px 0}
figure.code-example figcaption{font-weight:600;margin-bottom:6px;color:#444}
.note{background:#fff8e1;border-left:4px solid #f0c040;padding:10px 14px;margin:14px 0}
a{color:#1a5fb4}
"""


def main():
    if len(sys.argv) != 3:
        sys.stderr.write("usage: xep2html.py INPUT.xml OUTPUT.html\n")
        return 2
    inp, outp = sys.argv[1], sys.argv[2]
    root = parse(inp)
    _title, meta = header_block(root)

    sections = [s for s in root if s.tag.startswith("section")]
    numbers = []
    for i, s in enumerate(sections, start=1):
        toc(s, str(i), numbers)

    parts = []
    parts.append("<!DOCTYPE html>")
    parts.append("<html lang='en'><head><meta charset='utf-8'/>")
    parts.append("<meta name='viewport' content='width=device-width, initial-scale=1.0'/>")
    parts.append("<title>%s</title>" % html.escape(meta.get("title", "")))
    parts.append("<style>%s</style>" % CSS)
    parts.append("</head><body>")
    parts.append("<h1>%s</h1>" % html.escape(meta.get("title", "")))

    if meta.get("abstract"):
        parts.append('<div class="abstract">%s</div>' % meta["abstract"])

    parts.append('<dl class="docmeta">')
    if meta.get("number"):
        parts.append("<dt>Number</dt><dd>%s</dd>" % html.escape(meta["number"]))
    if meta.get("status"):
        parts.append("<dt>Status</dt><dd>%s</dd>" % html.escape(meta["status"]))
    if meta.get("type"):
        parts.append("<dt>Type</dt><dd>%s</dd>" % html.escape(meta["type"]))
    if meta.get("version"):
        parts.append("<dt>Version</dt><dd>%s (%s)</dd>" % (html.escape(meta["version"]), html.escape(meta.get("date", ""))))
    if meta.get("authors"):
        parts.append("<dt>Author</dt><dd>%s</dd>" % html.escape(", ".join(meta["authors"])))
    if meta.get("deps"):
        parts.append("<dt>Dependencies</dt><dd>%s</dd>" % html.escape(", ".join(meta["deps"])))
    parts.append("</dl>")

    parts.append('<nav class="toc"><h2>Table of Contents</h2><ol>')
    for num, anchor, topic in numbers:
        parts.append('<li><a href="#%s">%s %s</a></li>' % (html.escape(anchor, quote=True), num, html.escape(topic)))
    parts.append("</ol></nav>")

    for i, s in enumerate(sections, start=1):
        parts.append(section(s, str(i)))

    parts.append("</body></html>")

    with open(outp, "w", encoding="utf-8") as fh:
        fh.write("\n".join(parts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
