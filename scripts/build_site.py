"""
build_site.py — Generate static search website from all ticker reports.

Search: Fuse.js (client-side, zero-build, works offline)
SSG:    Hand-written Python builder

Output structure:
  site/
  ├── index.html            # Homepage: search + filter + company cards
  ├── reports/{ticker}.html # Individual report pages (markdown → HTML)
  └── sector/{sector}.html  # Sector listing pages

Wikilinks in reports link back to index.html?wl=ENTITY for live filter.

Usage:
  python scripts/build_site.py                 # Full build
  python scripts/build_site.py --no-reports    # Skip individual pages (faster preview)
  python scripts/build_site.py --sector Semiconductors  # One sector only
"""

import json
import os
import re
import sys
import time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import REPORTS_DIR, PROJECT_ROOT, setup_stdout, parse_number

SITE_DIR = os.path.join(PROJECT_ROOT, "site")

try:
    import markdown as md_lib
    _MD_EXT = ["tables", "fenced_code", "nl2br"]
    HAS_MD = True
except ImportError:
    HAS_MD = False

# ─── Shared CSS ───────────────────────────────────────────────────────────────
_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
:root{--primary:#1a2744;--accent:#c0392b;--blue:#2980b9;--bg:#f0f2f5;--card:#fff;--text:#2c3e50;--muted:#7f8c8d;--border:#e0e4ea}
body{font-family:-apple-system,'Segoe UI',sans-serif;background:var(--bg);color:var(--text);line-height:1.5}
a{color:var(--blue);text-decoration:none}
a:hover{text-decoration:underline}
/* Header */
header{background:var(--primary);color:#fff;padding:0 24px;height:52px;display:flex;align-items:center;gap:16px;position:sticky;top:0;z-index:100;box-shadow:0 2px 8px rgba(0,0,0,.3)}
header .logo{font-size:16px;font-weight:700;white-space:nowrap;color:#fff;text-decoration:none}
header .logo span{color:#e8a;font-size:11px;margin-left:6px;font-weight:400}
header .search-wrap{flex:1;max-width:480px;position:relative}
header .search-wrap input{width:100%;padding:7px 12px 7px 34px;border:1px solid #345;border-radius:6px;background:#243256;color:#fff;font-size:13px;outline:none}
header .search-wrap input::placeholder{color:#889}
header .search-wrap input:focus{border-color:#5af;background:#1e3060}
header .search-icon{position:absolute;left:10px;top:50%;transform:translateY(-50%);color:#667;font-size:13px}
header nav a{color:#aad;font-size:13px;padding:4px 8px;border-radius:4px}
header nav a:hover{background:#243256;color:#fff}
/* Layout */
.container{max-width:1400px;margin:0 auto;padding:20px 24px}
.layout{display:grid;grid-template-columns:220px 1fr;gap:20px;align-items:start}
/* Sidebar */
.sidebar{position:sticky;top:70px}
.sidebar-box{background:var(--card);border-radius:8px;padding:16px;border:1px solid var(--border);margin-bottom:12px}
.sidebar-box h3{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px}
.sidebar-box label{display:flex;align-items:center;gap:7px;font-size:12px;padding:3px 0;cursor:pointer}
.sidebar-box input[type=checkbox]{cursor:pointer;accent-color:var(--blue)}
.sidebar-box select{width:100%;padding:5px 8px;border:1px solid var(--border);border-radius:4px;font-size:12px;background:#fff;cursor:pointer}
/* Toolbar */
.toolbar{display:flex;align-items:center;gap:10px;margin-bottom:14px;flex-wrap:wrap}
.toolbar select{padding:5px 10px;border:1px solid var(--border);border-radius:5px;font-size:12px;background:#fff;cursor:pointer}
.toolbar .count-badge{background:#eef;color:#446;padding:3px 10px;border-radius:12px;font-size:12px}
/* Cards grid */
.cards-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px}
/* Company card */
.card{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:14px 16px;cursor:pointer;transition:box-shadow .15s,transform .1s}
.card:hover{box-shadow:0 4px 16px rgba(0,0,0,.1);transform:translateY(-1px)}
.card-top{display:flex;align-items:center;gap:8px;margin-bottom:8px}
.ticker{background:var(--accent);color:#fff;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:700;flex-shrink:0}
.company-name{font-size:15px;font-weight:600;line-height:1.2}
.sector-tag{font-size:10px;color:var(--muted);background:#eef;padding:1px 6px;border-radius:3px;white-space:nowrap}
.metrics{display:flex;gap:12px;margin:6px 0;flex-wrap:wrap}
.metric{font-size:11px;color:var(--muted)}
.metric strong{color:var(--text);font-size:12px}
.card-summary{font-size:11px;color:#666;line-height:1.4;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.wl-chips{margin-top:8px;display:flex;flex-wrap:wrap;gap:4px}
.wl-chip{font-size:10px;background:#e8f0fe;color:#2563eb;padding:1px 6px;border-radius:3px;cursor:pointer}
.wl-chip:hover{background:#d0e2fd}
/* Pagination */
.pagination{display:flex;gap:6px;align-items:center;margin-top:20px;justify-content:center}
.pagination button{padding:5px 12px;border:1px solid var(--border);border-radius:4px;background:#fff;cursor:pointer;font-size:12px}
.pagination button.active{background:var(--blue);color:#fff;border-color:var(--blue)}
.pagination button:hover:not(.active){background:#f0f4ff}
/* Report page */
.report-layout{display:grid;grid-template-columns:1fr 240px;gap:24px;align-items:start}
.report-content h2{font-size:17px;font-weight:700;margin:20px 0 10px;padding-bottom:6px;border-bottom:2px solid var(--primary);color:var(--primary)}
.report-content h3{font-size:14px;font-weight:600;margin:14px 0 6px;color:#345}
.report-content p{font-size:13px;margin-bottom:10px;line-height:1.65}
.report-content ul,.report-content ol{margin:6px 0 10px 20px;font-size:13px;line-height:1.7}
.report-content table{width:100%;border-collapse:collapse;font-size:12px;margin:10px 0;overflow-x:auto;display:block}
.report-content th{background:var(--primary);color:#fff;padding:6px 10px;text-align:right;white-space:nowrap}
.report-content th:first-child{text-align:left}
.report-content td{padding:5px 10px;border-bottom:1px solid var(--border);text-align:right;white-space:nowrap}
.report-content td:first-child{text-align:left;font-weight:500}
.report-content tr:nth-child(even) td{background:#f8f9fc}
.report-content a.wl{background:#e8f0fe;color:#1a56db;padding:1px 4px;border-radius:3px;font-size:0.95em}
.report-content a.wl:hover{background:#c7d7fd}
.report-meta{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:16px}
.report-meta .meta-item{display:flex;flex-direction:column;margin-bottom:12px}
.report-meta .meta-label{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.4px}
.report-meta .meta-value{font-size:14px;font-weight:600;margin-top:2px}
.report-meta .val-table{width:100%;border-collapse:collapse;margin-top:6px}
.report-meta .val-table td{font-size:12px;padding:3px 0}
.report-meta .val-table td:last-child{font-weight:600;text-align:right}
.toc{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:12px;margin-bottom:12px}
.toc h4{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px}
.toc a{display:block;font-size:12px;padding:3px 0;color:#456;border-left:2px solid transparent;padding-left:8px}
.toc a:hover{border-color:var(--blue);color:var(--blue)}
.related-box{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:12px;margin-top:12px}
.related-box h4{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px}
.related-item{display:flex;align-items:center;gap:8px;padding:4px 0;font-size:12px;border-bottom:1px solid #f0f2f5}
.related-item:last-child{border-bottom:none}
/* Sector page */
.sector-header{background:var(--primary);color:#fff;padding:20px 24px;margin-bottom:20px;border-radius:0 0 8px 8px}
.sector-header h1{font-size:22px;font-weight:700}
.sector-header .subtitle{font-size:13px;color:#aad;margin-top:4px}
/* Utility */
.no-results{text-align:center;padding:60px 20px;color:var(--muted);font-size:14px}
.tag{display:inline-block;padding:2px 8px;border-radius:3px;font-size:11px}
.tag-tech{background:#e0f0ff;color:#1a6ab0}
.tag-mat{background:#fff3e0;color:#b05c00}
.badge-mc{background:#f0f4f8;color:#456;padding:2px 7px;border-radius:3px;font-size:11px}
@media(max-width:768px){
  .layout{grid-template-columns:1fr}
  .sidebar{position:static}
  .report-layout{grid-template-columns:1fr}
  header nav{display:none}
}
"""

# ─── Parsing ──────────────────────────────────────────────────────────────────

def parse_report(filepath):
    """Extract all metadata and content from a report .md file."""
    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read()

    sector = os.path.basename(os.path.dirname(filepath))
    fn = os.path.basename(filepath)
    m = re.match(r"^(\d{4})_(.+)\.md$", fn)
    if not m:
        return None
    ticker, name = m.group(1), m.group(2)

    # Split at 財務概況
    parts = raw.split("## 財務概況")
    content_part = parts[0]
    finance_part = parts[1] if len(parts) > 1 else ""

    # Metadata fields
    def get_field(label, text=content_part):
        mm = re.search(rf"\*\*{re.escape(label)}:\*\*\s*(.+)", text)
        return mm.group(1).strip() if mm else ""

    sector_en = get_field("板塊")
    industry_en = get_field("產業")
    market_cap_str = get_field("市值")
    ev_str = get_field("企業價值")

    mc_m = re.search(r"([\d,]+)", market_cap_str)
    ev_m = re.search(r"([\d,]+)", ev_str)
    market_cap = int(mc_m.group(1).replace(",", "")) if mc_m else 0
    ev_val = int(ev_m.group(1).replace(",", "")) if ev_m else 0

    # Summary
    summary = ""
    desc_m = re.search(r"\*\*企業價值:\*\*[^\n]*\n+(.{1,400})", content_part, re.DOTALL)
    if desc_m:
        raw_s = desc_m.group(1).strip()
        raw_s = re.sub(r"\[\[([^\]]+)\]\]", r"\1", raw_s)
        raw_s = re.sub(r"\*+", "", raw_s)
        raw_s = re.sub(r"\s+", " ", raw_s).strip()
        summary = raw_s[:150]

    # Wikilinks (non-financial)
    wikilinks = list(set(re.findall(r"\[\[([^\]]+)\]\]", content_part)))

    # Valuation from 財務概況
    pe_ttm = pe_fwd = ps = pb = ev_ebitda = None
    val_m = re.search(
        r"估值指標.*?\n\|[^\n]+\|\n\|[-\s|]+\|\n\|([^\n]+)\|",
        finance_part,
        re.DOTALL,
    )
    if val_m:
        vals = [v.strip() for v in val_m.group(1).split("|") if v.strip()]
        if len(vals) >= 5:
            pe_ttm = parse_number(vals[0])
            pe_fwd = parse_number(vals[1])
            ps = parse_number(vals[2])
            pb = parse_number(vals[3])
            ev_ebitda = parse_number(vals[4])

    return {
        "ticker": ticker,
        "name": name,
        "sector": sector,
        "sector_en": sector_en,
        "industry_en": industry_en,
        "market_cap": market_cap,
        "ev": ev_val,
        "pe_ttm": pe_ttm,
        "pe_fwd": pe_fwd,
        "ps": ps,
        "pb": pb,
        "ev_ebitda": ev_ebitda,
        "summary": summary,
        "wikilinks": wikilinks,
        "content": content_part,
        "finance": finance_part,
        "filepath": filepath,
        "file_path": os.path.relpath(filepath, PROJECT_ROOT).replace("\\", "/"),
    }


# ─── HTML helpers ─────────────────────────────────────────────────────────────

def safe_url_name(text):
    """Convert to URL-safe string preserving CJK."""
    return re.sub(r'[<>:"/\\|?*&=#+%\s]', "_", text).strip("_")


def wikilink_to_html(entity, depth=1):
    """Convert [[entity]] to an HTML anchor pointing to index.html with ?wl= param."""
    prefix = "../" * depth
    url_e = safe_url_name(entity)
    return f'<a href="{prefix}index.html?wl={url_e}" class="wl">{entity}</a>'


def md_to_html(text, depth=1):
    """Convert markdown text to HTML, replacing [[wikilinks]] with anchors."""
    # Replace [[X]] with placeholders
    placeholders = {}
    def store_wl(m):
        entity = m.group(1)
        key = f"WL_PLACEHOLDER_{len(placeholders)}_END"
        placeholders[key] = wikilink_to_html(entity, depth)
        return key
    text = re.sub(r"\[\[([^\]]+)\]\]", store_wl, text)

    if HAS_MD:
        html = md_lib.markdown(text, extensions=_MD_EXT)
    else:
        # Minimal fallback markdown
        html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", text, flags=re.MULTILINE)
        html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
        html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
        html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
        html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
        html = "<p>" + re.sub(r"\n\n+", "</p><p>", html) + "</p>"

    # Restore wikilink anchors
    for key, val in placeholders.items():
        html = html.replace(key, val)

    return html


def fmt_mc(val):
    """Format market cap in 百萬台幣 with K/M suffix."""
    if not val:
        return "—"
    if val >= 1_000_000:
        return f"{val/1_000_000:.1f}T"
    if val >= 1_000:
        return f"{val/1_000:.0f}B"
    return f"{val:,}M"


def fmt_num(val, decimals=2):
    if val is None:
        return "—"
    return f"{val:.{decimals}f}"


def base_html(title, body, css_depth=0, extra_head=""):
    prefix = "../" * css_depth
    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} | TW Coverage</title>
<style>{_CSS}</style>
{extra_head}
</head>
<body>
<header>
  <a class="logo" href="{prefix}index.html">TW Coverage <span>1,735 台灣上市公司</span></a>
  <div class="search-wrap">
    <span class="search-icon">🔍</span>
    <input type="text" id="global-search" placeholder="搜尋公司、ticker、技術名稱..." autocomplete="off">
  </div>
  <nav>
    <a href="{prefix}index.html">首頁</a>
  </nav>
</header>
{body}
<script>
// Global search redirects to index with ?q= param
document.getElementById('global-search').addEventListener('keydown', function(e) {{
  if (e.key === 'Enter') {{
    const q = this.value.trim();
    if (q) window.location.href = '{prefix}index.html?q=' + encodeURIComponent(q);
  }}
}});
</script>
</body>
</html>"""


# ─── Index page ───────────────────────────────────────────────────────────────

def generate_index_html(all_reports):
    """Generate homepage with Fuse.js search."""
    # Build compact search JSON
    idx = []
    for r in all_reports:
        idx.append({
            "t": r["ticker"],
            "n": r["name"],
            "s": r["sector"],
            "b": r["sector_en"],
            "i": r["industry_en"],
            "mc": r["market_cap"],
            "pe": r["pe_ttm"],
            "pb": r["pb"],
            "ev": r["ev_ebitda"],
            "sum": r["summary"],
            "wl": " ".join(r["wikilinks"][:30]),  # first 30 wikilinks for search
        })
    companies_json = json.dumps(idx, ensure_ascii=False)

    sectors = sorted(set(r["sector"] for r in all_reports))
    sector_options = "\n".join(f'<option value="{s}">{s}</option>' for s in sectors)

    body = f"""
<div class="container" style="padding-top:24px">
  <!-- Filters bar -->
  <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:16px">
    <select id="sector-filter" style="padding:6px 10px;border:1px solid #dde;border-radius:5px;font-size:13px;min-width:200px">
      <option value="">所有板塊</option>
      {sector_options}
    </select>
    <select id="sort-sel" style="padding:6px 10px;border:1px solid #dde;border-radius:5px;font-size:13px">
      <option value="mc">排序：市值↓</option>
      <option value="pe">排序：P/E↑</option>
      <option value="pb">排序：P/B↑</option>
      <option value="ev">排序：EV/EBITDA↑</option>
      <option value="name">排序：名稱</option>
    </select>
    <span id="count-badge" class="count-badge"></span>
    <span id="wl-filter-tag" style="display:none;background:#e0edff;color:#1a6ab0;padding:3px 10px;border-radius:4px;font-size:12px;cursor:pointer"></span>
  </div>

  <div id="cards-grid" class="cards-grid"></div>
  <div id="no-results" class="no-results" style="display:none">
    <div style="font-size:32px;margin-bottom:12px">🔍</div>
    找不到符合條件的公司
  </div>
  <div class="pagination" id="pagination"></div>
</div>

<script src="https://cdn.jsdelivr.net/npm/fuse.js@7.0.0/dist/fuse.min.js"></script>
<script>
const COMPANIES = {companies_json};
const PAGE_SIZE = 60;
let filteredData = [...COMPANIES];
let currentPage = 1;
let activeWl = "";

const fuse = new Fuse(COMPANIES, {{
  keys: [
    {{name:"t", weight:0.4}},
    {{name:"n", weight:0.4}},
    {{name:"sum", weight:0.1}},
    {{name:"wl", weight:0.1}},
  ],
  threshold: 0.35,
  includeScore: true,
}});

function getParams() {{
  const p = new URLSearchParams(window.location.search);
  return {{ q: p.get("q")||"", sector: p.get("s")||"", wl: p.get("wl")||"" }};
}}

function renderCards() {{
  const grid = document.getElementById("cards-grid");
  const noRes = document.getElementById("no-results");
  const total = filteredData.length;
  const start = (currentPage-1)*PAGE_SIZE;
  const page = filteredData.slice(start, start+PAGE_SIZE);

  document.getElementById("count-badge").textContent = `${{total}} 家公司`;
  if (!total) {{ grid.innerHTML=""; noRes.style.display="block"; renderPagination(0); return; }}
  noRes.style.display="none";

  grid.innerHTML = page.map(r => {{
    const mc = r.mc >= 1e6 ? (r.mc/1e6).toFixed(1)+"T" : r.mc >= 1000 ? (r.mc/1000).toFixed(0)+"B" : r.mc ? r.mc+"M" : "—";
    const pe = r.pe ? r.pe.toFixed(1) : "—";
    const pb = r.pb ? r.pb.toFixed(2) : "—";
    const wlChips = (r.wl||"").split(" ").filter(Boolean).slice(0,6).map(w =>
      `<span class="wl-chip" onclick="filterWl('${{encodeURIComponent(w)}}')">${{w}}</span>`
    ).join("");
    return `<div class="card" onclick="window.location='reports/${{r.t}}.html'">
      <div class="card-top">
        <span class="ticker">${{r.t}}</span>
        <span class="company-name">${{r.n}}</span>
      </div>
      <div style="margin-bottom:6px"><span class="sector-tag">${{r.s||""}}</span> <span style="font-size:10px;color:#aaa">${{r.i||""}}</span></div>
      <div class="metrics">
        <div class="metric"><strong>${{mc}}</strong> 市值</div>
        <div class="metric"><strong>${{pe}}</strong> P/E</div>
        <div class="metric"><strong>${{pb}}</strong> P/B</div>
      </div>
      ${{r.sum ? `<div class="card-summary">${{r.sum}}</div>` : ""}}
      ${{wlChips ? `<div class="wl-chips">${{wlChips}}</div>` : ""}}
    </div>`;
  }}).join("");

  renderPagination(total);
}}

function renderPagination(total) {{
  const pages = Math.ceil(total/PAGE_SIZE);
  const el = document.getElementById("pagination");
  if (pages <= 1) {{ el.innerHTML=""; return; }}
  let html = "";
  for (let i=1; i<=pages; i++) {{
    html += `<button class="${{i===currentPage?"active":""}}" onclick="goPage(${{i}})">${{i}}</button>`;
  }}
  el.innerHTML = html;
}}

function goPage(p) {{ currentPage=p; renderCards(); window.scrollTo(0,0); }}

function applyFilters() {{
  const q = document.getElementById("global-search").value.trim();
  const sector = document.getElementById("sector-filter").value;
  const sort = document.getElementById("sort-sel").value;

  let data;
  if (q) {{
    data = fuse.search(q).map(r => r.item);
  }} else {{
    data = [...COMPANIES];
  }}

  if (sector) data = data.filter(r => r.s === sector);
  if (activeWl) data = data.filter(r => (r.wl||"").includes(activeWl));

  // Sort
  if (!q || sort !== "mc") {{
    data.sort((a,b) => {{
      if (sort==="mc") return (b.mc||0)-(a.mc||0);
      if (sort==="pe") return ((a.pe||999))-(b.pe||999);
      if (sort==="pb") return ((a.pb||999))-(b.pb||999);
      if (sort==="ev") return ((a.ev||999))-(b.ev||999);
      if (sort==="name") return a.n.localeCompare(b.n,"zh");
      return (b.mc||0)-(a.mc||0);
    }});
  }}

  filteredData = data;
  currentPage = 1;
  renderCards();
}}

function filterWl(wl) {{
  activeWl = decodeURIComponent(wl);
  const tag = document.getElementById("wl-filter-tag");
  tag.style.display = "inline";
  tag.textContent = `[[${{activeWl}}]] ×`;
  tag.onclick = () => {{ activeWl=""; tag.style.display="none"; applyFilters(); }};
  // Update URL
  const url = new URL(window.location);
  url.searchParams.set("wl", wl);
  window.history.pushState({{}}, "", url);
  applyFilters();
}}

// Init from URL params
const params = getParams();
if (params.q) {{ document.getElementById("global-search").value = params.q; }}
if (params.sector) {{ document.getElementById("sector-filter").value = params.sector; }}
if (params.wl) {{
  activeWl = decodeURIComponent(params.wl);
  const tag = document.getElementById("wl-filter-tag");
  tag.style.display = "inline";
  tag.textContent = `[[${{activeWl}}]] ×`;
  tag.onclick = () => {{ activeWl=""; tag.style.display="none"; applyFilters(); }};
}}

document.getElementById("global-search").addEventListener("input", applyFilters);
document.getElementById("sector-filter").addEventListener("change", applyFilters);
document.getElementById("sort-sel").addEventListener("change", applyFilters);

applyFilters();
</script>
"""

    return base_html("首頁 — 1,735 台灣上市公司", body)


# ─── Report page ──────────────────────────────────────────────────────────────

def generate_report_html(report, wl_companies):
    """Generate individual company report page."""
    r = report
    content_html = md_to_html(r["content"], depth=1)
    finance_html = md_to_html("## 財務概況\n" + r["finance"], depth=1) if r["finance"] else ""

    # Related companies: share the most wikilinks
    shared = defaultdict(set)
    for wl in r["wikilinks"]:
        for co in wl_companies.get(wl, []):
            if co["ticker"] != r["ticker"]:
                shared[co["ticker"]].add(wl)
    top_related = sorted(shared.items(), key=lambda x: -len(x[1]))[:8]

    related_html = ""
    if top_related:
        items = ""
        for t, wls in top_related:
            items += f'<div class="related-item"><span class="ticker" style="font-size:10px">{t}</span> <a href="{t}.html" style="font-size:12px">{wl_companies.get(list(wls)[0],[{}])[0].get("name","")}</a></div>'
        related_html = f'<div class="related-box"><h4>相關公司</h4>{items}</div>'

    # Wikilink list for sidebar
    wl_list = "".join(
        f'<a href="../index.html?wl={safe_url_name(w)}" class="wl" style="display:inline-block;margin:2px 2px 2px 0;font-size:11px">{w}</a>'
        for w in sorted(r["wikilinks"])[:40]
    )

    sidebar = f"""
<div class="report-meta">
  <div class="meta-item">
    <span class="meta-label">板塊 / 產業</span>
    <span class="meta-value" style="font-size:13px">{r["sector_en"]} / {r["industry_en"]}</span>
  </div>
  <div class="meta-item">
    <span class="meta-label">市值</span>
    <span class="meta-value">{fmt_mc(r["market_cap"])} 百萬台幣</span>
  </div>
  <table class="val-table">
    <tr><td>P/E (TTM)</td><td>{fmt_num(r["pe_ttm"])}</td></tr>
    <tr><td>P/B</td><td>{fmt_num(r["pb"])}</td></tr>
    <tr><td>EV/EBITDA</td><td>{fmt_num(r["ev_ebitda"])}</td></tr>
  </table>
</div>
<div class="toc">
  <h4>目錄</h4>
  <a href="#section-desc">業務簡介</a>
  <a href="#section-supply">供應鏈位置</a>
  <a href="#section-clients">主要客戶及供應商</a>
  <a href="#section-finance">財務概況</a>
</div>
<div class="report-meta" style="margin-top:12px">
  <h4 style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px">Wikilinks ({len(r["wikilinks"])})</h4>
  {wl_list}
</div>
{related_html}"""

    # Inject section IDs
    content_final = re.sub(r'<h2>業務簡介', '<h2 id="section-desc">業務簡介', content_html)
    content_final = re.sub(r'<h2>供應鏈位置', '<h2 id="section-supply">供應鏈位置', content_final)
    content_final = re.sub(r'<h2>主要客戶及供應商', '<h2 id="section-clients">主要客戶及供應商', content_final)
    finance_final = re.sub(r'<h2>財務概況', '<h2 id="section-finance">財務概況', finance_html)

    body = f"""
<div class="container">
  <div style="margin:16px 0 12px;font-size:12px;color:var(--muted)">
    <a href="../index.html">首頁</a> &rsaquo;
    <a href="../sector/{safe_url_name(r["sector"])}.html">{r["sector"]}</a> &rsaquo;
    {r["ticker"]} {r["name"]}
  </div>
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:20px">
    <span class="ticker" style="font-size:16px;padding:4px 12px">{r["ticker"]}</span>
    <h1 style="font-size:22px;font-weight:700">{r["name"]}</h1>
  </div>
  <div class="report-layout">
    <div>
      <div class="report-content">{content_final}{finance_final}</div>
    </div>
    <div>{sidebar}</div>
  </div>
</div>"""

    return base_html(f"{r['ticker']} {r['name']}", body, css_depth=1)


# ─── Sector page ──────────────────────────────────────────────────────────────

def generate_sector_html(sector, reports):
    """Generate sector listing page."""
    reports_sorted = sorted(reports, key=lambda r: -(r["market_cap"] or 0))

    cards = ""
    for r in reports_sorted:
        mc = fmt_mc(r["market_cap"])
        pe = fmt_num(r["pe_ttm"])
        cards += f"""
<div class="card" onclick="window.location='../reports/{r["ticker"]}.html'">
  <div class="card-top">
    <span class="ticker">{r["ticker"]}</span>
    <span class="company-name">{r["name"]}</span>
  </div>
  <div class="metrics">
    <div class="metric"><strong>{mc}</strong> 市值</div>
    <div class="metric"><strong>{pe}</strong> P/E</div>
    <div class="metric"><strong>{fmt_num(r["pb"])}</strong> P/B</div>
  </div>
  {f'<div class="card-summary">{r["summary"]}</div>' if r["summary"] else ""}
</div>"""

    body = f"""
<div class="sector-header">
  <h1>{sector}</h1>
  <div class="subtitle">{len(reports)} 家公司 | 按市值排序</div>
</div>
<div class="container">
  <div style="margin-bottom:12px;font-size:12px;color:var(--muted)">
    <a href="../index.html">← 返回首頁</a>
  </div>
  <div class="cards-grid">{cards}</div>
</div>"""

    return base_html(f"{sector}", body, css_depth=1)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    setup_stdout()
    args = sys.argv[1:]
    skip_reports = "--no-reports" in args
    sector_only = None
    if "--sector" in args:
        i = args.index("--sector")
        if i + 1 < len(args):
            sector_only = args[i + 1]

    os.makedirs(os.path.join(SITE_DIR, "reports"), exist_ok=True)
    os.makedirs(os.path.join(SITE_DIR, "sector"), exist_ok=True)

    # ── Parse all reports ──
    t0 = time.time()
    print("Parsing reports...")
    all_reports = []
    for sector_dir in sorted(os.listdir(REPORTS_DIR)):
        if sector_only and sector_dir != sector_only:
            continue
        sector_path = os.path.join(REPORTS_DIR, sector_dir)
        if not os.path.isdir(sector_path):
            continue
        for f in sorted(os.listdir(sector_path)):
            if not f.endswith(".md") or not re.match(r"^\d{4}_", f):
                continue
            r = parse_report(os.path.join(sector_path, f))
            if r:
                all_reports.append(r)

    print(f"  Parsed {len(all_reports)} reports in {time.time()-t0:.1f}s")

    # Build wikilink → companies map
    wl_companies = defaultdict(list)
    for r in all_reports:
        for wl in r["wikilinks"]:
            wl_companies[wl].append({"ticker": r["ticker"], "name": r["name"]})

    # ── index.html ──
    print("Generating index.html...")
    index_html = generate_index_html(all_reports)
    with open(os.path.join(SITE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)
    print(f"  site/index.html ({len(index_html)//1024}KB)")

    # ── Sector pages ──
    print("Generating sector pages...")
    by_sector = defaultdict(list)
    for r in all_reports:
        by_sector[r["sector"]].append(r)

    for sector, reports in sorted(by_sector.items()):
        html = generate_sector_html(sector, reports)
        safe = safe_url_name(sector)
        with open(os.path.join(SITE_DIR, "sector", f"{safe}.html"), "w", encoding="utf-8") as f:
            f.write(html)
    print(f"  {len(by_sector)} sector pages")

    # ── Individual report pages ──
    if not skip_reports:
        print(f"Generating {len(all_reports)} report pages...")
        for i, r in enumerate(all_reports):
            html = generate_report_html(r, wl_companies)
            with open(os.path.join(SITE_DIR, "reports", f"{r['ticker']}.html"), "w", encoding="utf-8") as f:
                f.write(html)
            if (i + 1) % 200 == 0:
                print(f"  {i+1}/{len(all_reports)}...")
        print(f"  Done: {len(all_reports)} report pages")
    else:
        print("  Skipped report pages (--no-reports)")

    total = time.time() - t0
    print(f"\nBuild complete in {total:.1f}s")
    print(f"Output: {SITE_DIR}/")
    print(f"Serve: python -m http.server 8080 --directory site/")
    print(f"Then open: http://localhost:8080/")


if __name__ == "__main__":
    main()
