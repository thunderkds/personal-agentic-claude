#!/usr/bin/env python3
"""Write a copy of a static page that outlines tap targets under 44x44 px in red (ux-evaluate B-d).

Usage: python3 tap_probe.py <absolute page path> <absolute out dir>

Prints the probe page's path. Screenshot that page at 375 the same way as the page itself: each
red box is a target under 44 px, and a yellow banner at the top lists them as `name WxH`. The page
itself is never changed. Inline links inside a sentence are not counted (WCAG 2.5.8 exception);
a checkbox or radio inside a label is measured by its label.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROBE_JS = r"""<script>/* tap-probe (ux-evaluate B-d) */
(function () {
  var MIN = 44, SEL = 'a[href],button,input:not([type=hidden]),select,textarea,summary,[role=button],[onclick]';
  function name(el) {
    var t = (el.getAttribute('aria-label') || el.innerText || el.value || el.tagName).trim().replace(/\s+/g, ' ');
    return t.slice(0, 30);
  }
  function target(el) {
    if ((el.type === 'checkbox' || el.type === 'radio') && el.closest('label')) return el.closest('label');
    return el;
  }
  function inline(el) {
    return el.tagName === 'A' && el.parentElement && /^(P|LI|SPAN|TD)$/.test(el.parentElement.tagName)
      && el.parentElement.innerText.trim().length > el.innerText.trim().length;
  }
  function run() {
    var old = document.getElementById('tap-probe-banner'); if (old) old.remove();
    var seen = [], small = [];
    document.querySelectorAll(SEL).forEach(function (el) {
      var t = target(el);
      if (seen.indexOf(t) >= 0 || inline(t)) return;
      seen.push(t);
      var r = t.getBoundingClientRect();
      if (!r.width || !r.height) return;
      if (r.width < MIN || r.height < MIN) {
        t.style.outline = '3px solid #e00';
        small.push(name(t) + ' ' + Math.round(r.width) + 'x' + Math.round(r.height));
      }
    });
    var b = document.createElement('div');
    b.id = 'tap-probe-banner';
    b.style.cssText = 'position:relative;z-index:2147483647;background:#ff0;color:#000;font:12px/1.3 monospace;padding:4px';
    b.textContent = 'tap-probe: ' + small.length + ' under 44px: ' + small.join('; ');
    document.body.insertBefore(b, document.body.firstChild);  // above the page, never over it
  }
  addEventListener('load', run); addEventListener('resize', run); setTimeout(run, 300);
})();
</script>"""


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[1] in ("-h", "--help"):
        print(__doc__.strip())
        return 0
    if len(argv) != 3:
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        return 2
    page, out = Path(argv[1]), Path(argv[2])
    for label, p in (("page", page), ("out dir", out)):
        if not p.is_absolute():
            print(f"tap_probe: the {label} must be an absolute path, got {p}", file=sys.stderr)
            return 2
    if not page.is_file():
        print(f"tap_probe: no such page: {page}", file=sys.stderr)
        return 2
    html = page.read_text(encoding="utf-8")
    base = f'<base href="file://{page.parent}/">'
    lower = html.lower()
    head = lower.find("<head")
    if head >= 0:
        end = html.index(">", head) + 1
        html = html[:end] + base + html[end:]
    else:
        html = base + html
    body_end = html.lower().rfind("</body>")
    html = html[:body_end] + PROBE_JS + html[body_end:] if body_end >= 0 else html + PROBE_JS
    out.mkdir(parents=True, exist_ok=True)
    dest = out / f"{page.stem}-probe.html"
    dest.write_text(html, encoding="utf-8")
    print(dest)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
