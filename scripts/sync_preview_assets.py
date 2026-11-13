#!/usr/bin/env python3
"""Synchronize V12 standalone HTML preview with the independent V13 assets.

The historical single-file HTML embeds JavaScript and CSS; updating the asset
files alone does not change the deployed preview. This utility synchronizes
the embedded motion-social JS, injects idempotent updated CSS, preserves all
other dashboard modules and research data, and validates the result.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "preview/v12/index.html"
SCRIPT = ROOT / "preview/v12/motion_social.js"
CSS = ROOT / "preview/v12/motion_social.css"
STYLE_ID = "v13MotionEnhancements"

def synchronize():
    html = PAGE.read_text(encoding="utf-8")
    javascript = SCRIPT.read_text(encoding="utf-8").strip()
    styles = CSS.read_text(encoding="utf-8").strip()
    if "</script" in javascript.lower() or "</style" in styles.lower():
        raise RuntimeError("Embedded asset contains a closing HTML delimiter")
    expr = re.compile(r'(<script\b[^>]*\bid="v12MotionSocialScript"[^>]*>)(.*?)(</script>)',
                      flags=re.I | re.S)
    if len(expr.findall(html)) != 1:
        raise RuntimeError("Expected precisely one existing motion script marker")
    html = expr.sub(lambda m: m.group(1) + "\n" + javascript + "\n" + m.group(3), html, count=1)
    style_tag = '<style id="' + STYLE_ID + '">\n' + styles + '\n</style>\n'
    style_expr = re.compile(r'<style\b[^>]*\bid="' + STYLE_ID + r'"[^>]*>.*?</style>\s*',
                            flags=re.I | re.S)
    if style_expr.search(html):
        html, n = style_expr.subn(lambda m: style_tag, html, count=1)
        if n != 1:
            raise RuntimeError("Unexpected style replacement count")
    else:
        html, n = re.subn(r"</head\s*>", lambda m: style_tag + m.group(0), html, count=1, flags=re.I)
        if n != 1:
            raise RuntimeError("Missing HTML head closing tag")
    for marker in ("data-v13-kind", "v13-four-filters", "v13Evidence",
                   'id="v12Data"', 'id="archiveData"', 'id="v12FlowSvg"'):
        if marker not in html:
            raise RuntimeError("Required preview element missing: " + marker)
    if html != PAGE.read_text(encoding="utf-8"):
        PAGE.write_text(html, encoding="utf-8")
        print("Updated standalone preview / preserved historical data")
    else:
        print("Standalone preview already synchronized")
    print("V13 JS bytes:",len(javascript),"CSS bytes:",len(styles))
    return 0

if __name__ == "__main__":
    sys.exit(synchronize())
