"""
build_discovery_index.py — Build an index of all saved discovery results.

Reads all discoveries/*.md files and generates discoveries/INDEX.md
summarising keyword → company count → date → applied status.

Usage:
  python scripts/build_discovery_index.py
"""

import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import PROJECT_ROOT, setup_stdout

DISCOVERIES_DIR = os.path.join(PROJECT_ROOT, "discoveries")
INDEX_PATH = os.path.join(DISCOVERIES_DIR, "INDEX.md")


def parse_discovery_file(filepath):
    """Parse a discovery .md file and return summary dict."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    info = {}
    m = re.search(r"^# Discovery: (.+)$", content, re.MULTILINE)
    info["keyword"] = m.group(1).strip() if m else os.path.basename(filepath)

    m = re.search(r"\*\*日期:\*\*\s*(.+)", content)
    info["date"] = m.group(1).strip() if m else "—"

    m = re.search(r"\*\*搜尋模式:\*\*\s*(.+)", content)
    info["mode"] = m.group(1).strip() if m else "—"

    m = re.search(r"\*\*命中公司數:\*\*\s*(\d+)", content)
    info["count"] = int(m.group(1)) if m else 0

    m = re.search(r"\*\*已套用 wikilink:\*\*\s*(.+)", content)
    info["applied"] = (m.group(1).strip() == "是") if m else False

    info["filename"] = os.path.basename(filepath)
    return info


def build_index():
    """Build INDEX.md from all discovery files."""
    if not os.path.isdir(DISCOVERIES_DIR):
        print("No discoveries/ directory found. Run discover.py first.")
        return

    files = sorted(
        [f for f in os.listdir(DISCOVERIES_DIR) if f.endswith(".md") and f != "INDEX.md"],
        reverse=True,  # newest first
    )

    if not files:
        print("No discovery files found.")
        return

    entries = []
    for fname in files:
        fpath = os.path.join(DISCOVERIES_DIR, fname)
        try:
            info = parse_discovery_file(fpath)
            entries.append(info)
        except Exception as e:
            print(f"  Warning: could not parse {fname}: {e}")

    # Build markdown
    lines = []
    lines.append("# Discovery Index")
    lines.append("")
    lines.append(f"> 自動產生於 {datetime.now().strftime('%Y-%m-%d %H:%M')}，共 {len(entries)} 筆搜尋記錄")
    lines.append("> 重新產生：`python scripts/build_discovery_index.py`")
    lines.append("")
    lines.append("| 日期 | 關鍵字 | 公司數 | 模式 | 已套用 | 檔案 |")
    lines.append("|---|---|---|---|---|---|")

    for e in entries:
        applied_str = "✅" if e["applied"] else "○"
        lines.append(
            f"| {e['date']} | {e['keyword']} | {e['count']} | {e['mode']} | {applied_str} | [{e['filename']}]({e['filename']}) |"
        )

    lines.append("")

    # Summary: keywords with >= 5 companies, not yet applied → suggest themes
    pending = [e for e in entries if e["count"] >= 5 and not e["applied"]]
    if pending:
        lines.append("## 建議新增主題（命中 ≥ 5 家、尚未套用）")
        lines.append("")
        for e in pending:
            lines.append(f"- `[[{e['keyword']}]]` — {e['count']} 家公司 ({e['date']})")
        lines.append("")

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"INDEX.md updated: {len(entries)} entries, {len(pending)} pending suggestions")
    return entries


def main():
    setup_stdout()
    entries = build_index()
    if entries:
        print(f"\nSaved: {INDEX_PATH}")


if __name__ == "__main__":
    main()
