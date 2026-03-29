"""
tw.py — My TW Coverage 統一操作入口

互動式選單，包裝所有 scripts/ 下的工具。
也可直接傳參數跳過選單：

  python tw.py --help               # 顯示所有指令
  python tw.py discover 液冷散熱    # 直接執行
  python tw.py financials 2330      # 直接執行
"""

import os
import sys
import re
import subprocess
import argparse
import logging
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "scripts")
sys.path.insert(0, SCRIPTS_DIR)
from utils import extract_summary as _extract_summary  # noqa: E402

REPORTS_DIR = os.path.join(PROJECT_ROOT, "Pilot_Reports")
TASK_FILE = os.path.join(PROJECT_ROOT, "task.md")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")

os.makedirs(LOGS_DIR, exist_ok=True)

# ─── Logging ──────────────────────────────────────────────────────────────────
log_path = os.path.join(LOGS_DIR, "tw_operations.log")
logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def log_op(op: str, detail: str = "", result: str = "ok"):
    logging.info(f"{op:25s} | {detail:40s} | {result}")


# ─── Repo stats ───────────────────────────────────────────────────────────────
def get_repo_stats() -> dict:
    stats = {"reports": 0, "batches_done": 0, "last_log": "—"}
    if os.path.isdir(REPORTS_DIR):
        for root, _, files in os.walk(REPORTS_DIR):
            stats["reports"] += sum(1 for f in files if re.match(r"^\d{4}_", f) and f.endswith(".md"))
    if os.path.exists(TASK_FILE):
        with open(TASK_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        stats["batches_done"] = content.count("[x]")
    # Last log entry
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if lines:
            stats["last_log"] = lines[-1].split("|")[0].strip()
    return stats


# ─── Fuzzy company search ─────────────────────────────────────────────────────
def search_companies(query: str) -> list:
    """Return list of (ticker, name, sector) matching query."""
    results = []
    q = query.lower().strip()
    for sector_dir in os.listdir(REPORTS_DIR):
        sector_path = os.path.join(REPORTS_DIR, sector_dir)
        if not os.path.isdir(sector_path):
            continue
        for f in os.listdir(sector_path):
            m = re.match(r"^(\d{4})_(.+)\.md$", f)
            if not m:
                continue
            ticker, name = m.group(1), m.group(2)
            if q in ticker or q in name.lower():
                results.append((ticker, name, sector_dir))
    return sorted(results, key=lambda x: x[0])


def read_company_preview(ticker: str, name: str, sector: str) -> dict:
    """Read metadata and first 200 chars of description."""
    filepath = os.path.join(REPORTS_DIR, sector, f"{ticker}_{name}.md")
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read().split("## 財務概況")[0]
    info = {}
    for field in ["板塊", "產業", "市值", "企業價值"]:
        m = re.search(rf"\*\*{field}:\*\*\s*(.+)", content)
        if m:
            info[field] = m.group(1).strip()
    info["簡介"] = _extract_summary(content, max_chars=200)
    return info


# ─── Script runner ────────────────────────────────────────────────────────────
def run_script(script_name: str, *args, capture=False):
    cmd = [sys.executable, os.path.join(SCRIPTS_DIR, script_name)] + list(args)
    if capture:
        result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True, encoding="utf-8")
        return result.stdout + result.stderr
    else:
        subprocess.run(cmd, cwd=PROJECT_ROOT)
        return ""


# ─── Scope helper ─────────────────────────────────────────────────────────────
def ask_scope(prompt_lib) -> list:
    """Interactively ask for scope and return list of CLI args."""
    choice = prompt_lib.select(
        message="更新範圍：",
        choices=[
            "單一 ticker",
            "多個 ticker（空格分隔）",
            "整個批次（batch 編號）",
            "整個產業（sector 名稱）",
            "全部 ALL ⚠️ 耗時較長",
        ],
    ).execute()

    if choice == "單一 ticker":
        t = prompt_lib.text("Ticker 代號 (4 位數)：").execute().strip()
        return [t] if t else []
    elif choice == "多個 ticker（空格分隔）":
        raw = prompt_lib.text("輸入 tickers (例: 2330 2317 3034)：").execute().strip()
        return raw.split()
    elif choice == "整個批次（batch 編號）":
        num = prompt_lib.text("Batch 編號：").execute().strip()
        return ["--batch", num]
    elif choice == "整個產業（sector 名稱）":
        # List available sectors
        sectors = sorted(os.listdir(REPORTS_DIR)) if os.path.isdir(REPORTS_DIR) else []
        if sectors:
            sector = prompt_lib.fuzzy(message="選擇產業：", choices=sectors).execute()
            return ["--sector", sector]
        return []
    else:
        confirm = prompt_lib.confirm("確定要更新全部報告？").execute()
        return [] if confirm else None


# ─── Menu actions ─────────────────────────────────────────────────────────────
def action_discover(prompt_lib):
    """互動式 discover."""
    keyword = prompt_lib.text("搜尋關鍵字：").execute().strip()
    if not keyword:
        return
    smart = prompt_lib.confirm("啟用 AI 智慧篩選 (--smart)？", default=False).execute()
    apply_wl = prompt_lib.confirm("自動加上 [[wikilink]] 標記 (--apply)？", default=False).execute()
    rebuild = False
    if apply_wl:
        rebuild = prompt_lib.confirm("同時重建主題圖和網路圖 (--rebuild)？", default=False).execute()

    args = [keyword]
    if smart:
        args.append("--smart")
    if apply_wl:
        args.append("--apply")
    if rebuild:
        args.append("--rebuild")

    print()
    run_script("discover.py", *args)
    log_op("discover", f'"{keyword}" smart={smart} apply={apply_wl}')


def action_lookup(prompt_lib):
    """查詢單一公司。"""
    try:
        from rich.console import Console
        from rich.table import Table
        console = Console()
    except ImportError:
        console = None

    query = prompt_lib.text("輸入 ticker 或公司名（支援模糊搜尋）：").execute().strip()
    if not query:
        return
    matches = search_companies(query)
    if not matches:
        print(f"找不到符合 '{query}' 的公司。")
        return

    if len(matches) == 1:
        ticker, name, sector = matches[0]
    else:
        choices = [f"{t} {n} ({s})" for t, n, s in matches[:30]]
        sel = prompt_lib.select(message="選擇公司：", choices=choices).execute()
        idx = choices.index(sel)
        ticker, name, sector = matches[idx]

    info = read_company_preview(ticker, name, sector)
    print()
    if console:
        t = Table(show_header=False, box=None, padding=(0, 1))
        t.add_column(style="bold cyan", min_width=8)
        t.add_column(style="white")
        t.add_row("Ticker", ticker)
        t.add_row("公司名", name)
        t.add_row("板塊", info.get("板塊", "—"))
        t.add_row("產業", info.get("產業", "—"))
        t.add_row("市值", info.get("市值", "—"))
        t.add_row("企業價值", info.get("企業價值", "—"))
        console.print(t)
        if "簡介" in info:
            console.print(f"\n[dim]{info['簡介']}...[/dim]")
    else:
        print(f"Ticker:   {ticker}")
        print(f"公司名:   {name}")
        for k, v in info.items():
            if k != "簡介":
                print(f"{k}:    {v}")
        if "簡介" in info:
            print(f"\n{info['簡介']}...")

    print()
    action = prompt_lib.select(
        message="下一步：",
        choices=["更新財務數據", "更新估值指標", "返回主選單"],
    ).execute()

    if action == "更新財務數據":
        run_script("update_financials.py", ticker)
        log_op("update_financials", ticker)
    elif action == "更新估值指標":
        run_script("update_valuation.py", ticker)
        log_op("update_valuation", ticker)


def action_update_financials(prompt_lib):
    scope = ask_scope(prompt_lib)
    if scope is None:
        return
    print()
    run_script("update_financials.py", *scope)
    log_op("update_financials", " ".join(scope) or "ALL")


def action_update_valuation(prompt_lib):
    scope = ask_scope(prompt_lib)
    if scope is None:
        return
    print()
    run_script("update_valuation.py", *scope)
    log_op("update_valuation", " ".join(scope) or "ALL")


def action_add_ticker(prompt_lib):
    ticker = prompt_lib.text("Ticker 代號 (4 位數)：").execute().strip()
    name = prompt_lib.text("公司中文名稱：").execute().strip()
    if not ticker or not name:
        print("Ticker 和名稱不能為空。")
        return
    print()
    run_script("add_ticker.py", ticker, name)
    log_op("add_ticker", f"{ticker} {name}")


def action_audit(prompt_lib):
    try:
        from rich.console import Console
        console = Console()
    except ImportError:
        console = None

    scope = ask_scope(prompt_lib)
    if scope is None:
        return

    args = scope if scope else ["--all"]
    print()
    if console:
        with console.status("[bold green]稽核中..."):
            output = run_script("audit_batch.py", *args, capture=True)
        console.print(output)
    else:
        run_script("audit_batch.py", *args)
    log_op("audit", " ".join(args) or "ALL")


def action_build_themes():
    print()
    run_script("build_themes.py")
    log_op("build_themes", "all")


def action_build_network():
    print()
    run_script("build_network.py")
    log_op("build_network", "all")


def action_build_wikilinks():
    print()
    run_script("build_wikilink_index.py")
    log_op("build_wikilink_index", "all")


# ─── Main interactive menu ────────────────────────────────────────────────────
def interactive_menu():
    try:
        from InquirerPy import inquirer
    except ImportError:
        print("需要 InquirerPy：pip install InquirerPy")
        sys.exit(1)

    try:
        from rich.console import Console
        from rich.panel import Panel
        console = Console()
    except ImportError:
        console = None

    # Status bar
    stats = get_repo_stats()
    if console:
        console.print(
            Panel(
                f"[bold]My TW Coverage[/bold]  "
                f"報告 [cyan]{stats['reports']}[/cyan]  |  "
                f"完成批次 [cyan]{stats['batches_done']}[/cyan]  |  "
                f"最後操作 [dim]{stats['last_log']}[/dim]",
                style="bold blue",
                expand=False,
            )
        )
    else:
        print(f"\nMy TW Coverage | 報告: {stats['reports']} | 批次: {stats['batches_done']}")

    MENU_CHOICES = [
        "🔍  搜尋主題 (discover)",
        "📊  查詢公司 (lookup)",
        "🔄  更新財務 (update_financials)",
        "✏️   更新估值 (update_valuation)",
        "📝  新增報告 (add_ticker)",
        "🏭  產生主題圖 (build_themes)",
        "🕸️   重建網路圖 (build_network)",
        "🔗  重建 Wikilink 索引 (build_wikilink_index)",
        "✅  品質稽核 (audit)",
        "❌  離開",
    ]

    while True:
        choice = inquirer.select(message="請選擇操作：", choices=MENU_CHOICES).execute()

        if "discover" in choice:
            action_discover(inquirer)
        elif "lookup" in choice:
            action_lookup(inquirer)
        elif "update_financials" in choice:
            action_update_financials(inquirer)
        elif "update_valuation" in choice:
            action_update_valuation(inquirer)
        elif "add_ticker" in choice:
            action_add_ticker(inquirer)
        elif "build_themes" in choice:
            action_build_themes()
        elif "build_network" in choice:
            action_build_network()
        elif "build_wikilink_index" in choice:
            action_build_wikilinks()
        elif "audit" in choice:
            action_audit(inquirer)
        elif "離開" in choice:
            print("Bye.")
            break


# ─── Direct CLI mode ──────────────────────────────────────────────────────────
def cli_mode():
    parser = argparse.ArgumentParser(
        description="My TW Coverage — 直接 CLI 模式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
指令對照表:
  discover <keyword> [--smart] [--apply] [--rebuild]
  lookup <ticker_or_name>
  financials [ticker...] [--batch N] [--sector S]
  valuation  [ticker...] [--batch N] [--sector S]
  add <ticker> <name>
  themes
  network
  wikilinks
  audit [ticker...] [--batch N] [--all]
""",
    )
    parser.add_argument("command", nargs="?", help="指令名稱")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="指令參數")
    parsed = parser.parse_args()

    cmd = parsed.command
    args = parsed.args or []

    dispatch = {
        "discover": ("discover.py", args),
        "financials": ("update_financials.py", args),
        "valuation": ("update_valuation.py", args),
        "add": ("add_ticker.py", args),
        "themes": ("build_themes.py", []),
        "network": ("build_network.py", []),
        "wikilinks": ("build_wikilink_index.py", []),
        "audit": ("audit_batch.py", args if args else ["--all"]),
    }

    if cmd == "lookup":
        query = " ".join(args)
        matches = search_companies(query)
        if not matches:
            print(f"找不到 '{query}'")
        for t, n, s in matches[:20]:
            print(f"  {t}  {n}  ({s})")
        return

    if cmd in dispatch:
        script, script_args = dispatch[cmd]
        run_script(script, *script_args)
        log_op(cmd, " ".join(str(a) for a in script_args))
    else:
        parser.print_help()


# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    # If arguments given, use CLI mode; otherwise launch interactive menu
    if len(sys.argv) > 1:
        cli_mode()
    else:
        interactive_menu()
