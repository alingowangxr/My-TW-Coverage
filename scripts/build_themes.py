"""
build_themes.py — Generate thematic investment screens from wikilink graph.

Scans all ticker reports for wikilinks, groups companies by theme (technology,
material, application), and generates markdown pages showing the full value chain
for each theme.

Usage:
  python scripts/build_themes.py              # Rebuild all themes
  python scripts/build_themes.py --list       # List available themes
  python scripts/build_themes.py "CoWoS"      # Rebuild single theme

Output: themes/ folder with one .md per theme.
"""

import json
import os
import re
import sys
from collections import defaultdict
from datetime import date

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "Pilot_Reports")
THEMES_DIR = os.path.join(os.path.dirname(__file__), "..", "themes")


# ─── Financial data extraction ────────────────────────────────────────────────

def _parse_num(s):
    try:
        return float(str(s).replace(",", "").strip())
    except Exception:
        return None


def extract_report_financials(filepath):
    """Extract market_cap, pe_ttm, pb, ev_ebitda, summary from a report."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    result = {}

    mc_m = re.search(r"\*\*市值:\*\*\s*([\d,]+)", content)
    result["market_cap"] = int(mc_m.group(1).replace(",", "")) if mc_m else 0

    # 估值指標 table: header row → separator → values row
    val_m = re.search(
        r"估值指標.*?\n\|[^\n]+\|\n\|[-\s|]+\|\n\|([^\n]+)\|",
        content,
        re.DOTALL,
    )
    if val_m:
        vals = [v.strip() for v in val_m.group(1).split("|") if v.strip()]
        if len(vals) >= 5:
            result["pe_ttm"] = _parse_num(vals[0])
            result["pe_fwd"] = _parse_num(vals[1])
            result["pb"] = _parse_num(vals[3])
            result["ev_ebitda"] = _parse_num(vals[4])

    # Summary (first ~80 chars of description prose)
    desc_m = re.search(r"\*\*企業價值:\*\*[^\n]*\n+(.{1,300})", content, re.DOTALL)
    if desc_m:
        raw = desc_m.group(1).strip()
        raw = re.sub(r"\[\[([^\]]+)\]\]", r"\1", raw)
        raw = re.sub(r"\*+", "", raw)
        raw = re.sub(r"\s+", " ", raw).strip()
        result["summary"] = raw[:80]
    else:
        result["summary"] = ""

    return result


def collect_company_financials():
    """Build {(ticker, company): financials} for all reports."""
    meta = {}
    for sector_dir in os.listdir(REPORTS_DIR):
        sector_path = os.path.join(REPORTS_DIR, sector_dir)
        if not os.path.isdir(sector_path):
            continue
        for f in os.listdir(sector_path):
            m = re.match(r"^(\d{4})_(.+)\.md$", f)
            if not m:
                continue
            ticker, company = m.group(1), m.group(2)
            fp = os.path.join(sector_path, f)
            try:
                fin = extract_report_financials(fp)
                fin["sector"] = sector_dir
                meta[(ticker, company)] = fin
            except Exception:
                pass
    return meta


# ─── Screener HTML template ───────────────────────────────────────────────────

_SCREENER_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Thematic Screener — TW Coverage</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--primary:#1a2744;--accent:#c0392b;--blue:#2980b9;--bg:#f0f2f5;--card:#fff;--border:#e0e4ea;--text:#2c3e50;--muted:#7f8c8d}
body{font-family:-apple-system,'Segoe UI',sans-serif;background:var(--bg);color:var(--text);line-height:1.5;display:flex;flex-direction:column;height:100vh;overflow:hidden}
header{background:var(--primary);color:#fff;padding:0 20px;height:48px;display:flex;align-items:center;gap:14px;flex-shrink:0}
header h1{font-size:15px;font-weight:700;white-space:nowrap}
header .subtitle{font-size:11px;color:#aad}
input,select,button{font-family:inherit}
/* Layout */
.main-layout{display:flex;flex:1;overflow:hidden}
/* Sidebar */
#sidebar{width:220px;background:var(--primary);overflow-y:auto;flex-shrink:0;padding:10px 0}
.theme-item{padding:8px 14px;cursor:pointer;font-size:13px;color:#ccd;border-left:3px solid transparent;transition:.1s}
.theme-item:hover{background:rgba(255,255,255,.07);color:#fff}
.theme-item.active{background:rgba(255,255,255,.12);color:#fff;border-left-color:#3db}
.theme-item .count{float:right;font-size:11px;color:#778;background:rgba(0,0,0,.2);padding:1px 6px;border-radius:3px}
.theme-group{font-size:10px;color:#556;text-transform:uppercase;letter-spacing:.5px;padding:14px 14px 4px;font-weight:700}
/* Main panel */
#main-panel{flex:1;display:flex;flex-direction:column;overflow:hidden}
/* Toolbar */
#toolbar{background:#fff;border-bottom:1px solid var(--border);padding:10px 16px;display:flex;align-items:center;gap:10px;flex-wrap:wrap;flex-shrink:0}
#toolbar select,#toolbar input[type=text]{padding:5px 9px;border:1px solid var(--border);border-radius:4px;font-size:12px;background:#fff}
#toolbar input[type=text]{min-width:160px}
.role-btns button{padding:3px 9px;border:1px solid var(--border);border-radius:3px;font-size:11px;background:#fff;cursor:pointer;color:var(--muted)}
.role-btns button.active{background:var(--blue);color:#fff;border-color:var(--blue)}
#result-count{font-size:12px;color:var(--muted);white-space:nowrap}
/* Cards */
#cards-area{flex:1;overflow-y:auto;padding:16px}
.cards-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px}
.card{background:var(--card);border:1px solid var(--border);border-radius:7px;padding:13px 14px;cursor:pointer;position:relative;transition:box-shadow .15s,transform .1s}
.card:hover{box-shadow:0 3px 12px rgba(0,0,0,.1);transform:translateY(-1px)}
.card.in-compare{border-color:var(--blue);box-shadow:0 0 0 2px rgba(41,128,185,.2)}
.card-top{display:flex;align-items:flex-start;gap:8px;margin-bottom:7px}
.ticker{background:var(--accent);color:#fff;padding:2px 7px;border-radius:3px;font-size:11px;font-weight:700;flex-shrink:0}
.company-name{font-size:14px;font-weight:600;line-height:1.2}
.role-badge{position:absolute;top:10px;right:10px;font-size:9px;padding:1px 5px;border-radius:3px;text-transform:uppercase;letter-spacing:.3px}
.role-upstream{background:#e8f5e9;color:#2e7d32}
.role-midstream{background:#fff8e1;color:#f57f17}
.role-downstream{background:#e3f2fd;color:#1565c0}
.role-related{background:#f3e5f5;color:#6a1b9a}
.sector-tag{font-size:10px;color:var(--muted);background:#f0f2f5;padding:1px 6px;border-radius:3px;margin-bottom:6px;display:inline-block}
.metrics{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:5px}
.metric{font-size:11px;color:var(--muted)}
.metric strong{color:var(--text);font-size:12px}
.card-summary{font-size:11px;color:#666;line-height:1.4;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.add-compare{position:absolute;bottom:10px;right:10px;width:22px;height:22px;border:1px solid var(--border);border-radius:4px;background:#fff;cursor:pointer;font-size:14px;display:flex;align-items:center;justify-content:center;color:var(--muted);opacity:0;transition:.15s}
.card:hover .add-compare{opacity:1}
.card.in-compare .add-compare{opacity:1;background:var(--blue);color:#fff;border-color:var(--blue)}
.no-results{text-align:center;padding:60px 20px;color:var(--muted)}
/* Compare bar */
#compare-bar{background:#fff;border-top:1px solid var(--border);padding:10px 16px;display:flex;align-items:center;gap:12px;flex-shrink:0;display:none}
#compare-bar.visible{display:flex}
.compare-slot{background:var(--bg);border:1px dashed var(--border);border-radius:4px;padding:5px 10px;font-size:12px;display:flex;align-items:center;gap:6px;min-width:120px}
.compare-slot .remove{cursor:pointer;color:var(--accent);font-weight:700;margin-left:4px}
#compare-btn{padding:6px 16px;background:var(--blue);color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:13px;font-weight:600}
#compare-btn:hover{background:#3498db}
#clear-compare{padding:5px 12px;background:#fff;border:1px solid var(--border);border-radius:4px;cursor:pointer;font-size:12px;color:var(--muted)}
/* Modal */
#modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:200;display:none;align-items:center;justify-content:center}
#modal-overlay.visible{display:flex}
#modal{background:#fff;border-radius:10px;width:90vw;max-width:900px;max-height:85vh;overflow:auto;padding:24px}
#modal h2{font-size:17px;font-weight:700;margin-bottom:16px}
.compare-table{width:100%;border-collapse:collapse;font-size:13px}
.compare-table th{background:var(--primary);color:#fff;padding:8px 12px;text-align:center;font-weight:600}
.compare-table th:first-child{text-align:left;min-width:120px}
.compare-table td{padding:7px 12px;border-bottom:1px solid var(--border);text-align:center}
.compare-table td:first-child{text-align:left;font-weight:500;color:var(--muted);font-size:12px}
.compare-table tr:last-child td{border:none}
.best-val{color:#2e7d32;font-weight:700}
.worst-val{color:#c62828;font-weight:700}
#modal-close{float:right;cursor:pointer;font-size:20px;line-height:1;color:var(--muted);margin-top:-4px}
#modal-close:hover{color:var(--text)}
#export-csv{padding:6px 14px;border:1px solid var(--border);border-radius:4px;background:#fff;cursor:pointer;font-size:12px;margin-top:12px}
</style>
</head>
<body>
<header>
  <h1>Thematic Screener</h1>
  <span class="subtitle">主題選股工具 — TW Coverage</span>
  <div style="margin-left:auto;display:flex;gap:10px">
    <a href="../index.html" style="color:#aad;font-size:12px">← 返回首頁</a>
  </div>
</header>

<div class="main-layout">
  <!-- Theme sidebar -->
  <div id="sidebar">__THEME_LIST__</div>

  <!-- Main -->
  <div id="main-panel">
    <div id="toolbar">
      <input type="text" id="search-input" placeholder="搜尋公司名...">
      <select id="sort-sel">
        <option value="mc">市值↓</option>
        <option value="pe">P/E↑</option>
        <option value="pb">P/B↑</option>
        <option value="ev">EV/EBITDA↑</option>
      </select>
      <div class="role-btns" id="role-btns">
        <button data-role="" class="active">全部</button>
        <button data-role="upstream">上游</button>
        <button data-role="midstream">中游</button>
        <button data-role="downstream">下游</button>
        <button data-role="related">相關</button>
      </div>
      <span id="result-count"></span>
    </div>

    <div id="cards-area">
      <div class="cards-grid" id="cards-grid"></div>
      <div id="no-results" class="no-results" style="display:none">沒有符合條件的公司</div>
    </div>

    <div id="compare-bar">
      <span style="font-size:12px;color:var(--muted);white-space:nowrap">比較：</span>
      <div id="compare-slots"></div>
      <button id="compare-btn">開始比較</button>
      <button id="clear-compare">清除</button>
    </div>
  </div>
</div>

<!-- Compare modal -->
<div id="modal-overlay">
  <div id="modal">
    <span id="modal-close">×</span>
    <h2>公司比較</h2>
    <div id="modal-content"></div>
    <button id="export-csv">匯出 CSV</button>
  </div>
</div>

<script>
const DATA = __SCREENER_DATA__;
let activeTheme = Object.keys(DATA.themes)[0] || "";
let activeRole = "";
let compareSet = [];  // max 5

function fmtNum(v,d=2){return v!=null?v.toFixed(d):"—"}
function fmtMc(v){if(!v)return"—";if(v>=1e6)return(v/1e6).toFixed(1)+"T";if(v>=1e3)return(v/1e3).toFixed(0)+"B";return v+"M"}
function roleBadge(role){const m={"upstream":"上游 role-upstream","midstream":"中游 role-midstream","downstream":"下游 role-downstream","related":"相關 role-related"};const c=m[role]||"role-related";return`<span class="role-badge ${c}">${c.split(" ")[0]==="上游"?"上游":c.split(" ")[0]}</span>`}

function getCompanies(){
  const theme=DATA.themes[activeTheme];
  if(!theme)return[];
  let cos=[...theme.companies];
  if(activeRole)cos=cos.filter(c=>c.role===activeRole);
  const q=document.getElementById("search-input").value.trim().toLowerCase();
  if(q)cos=cos.filter(c=>c.name.includes(q)||c.ticker.includes(q));
  const sort=document.getElementById("sort-sel").value;
  cos.sort((a,b)=>{
    if(sort==="mc")return(b.market_cap||0)-(a.market_cap||0);
    if(sort==="pe")return((a.pe_ttm||999))-(b.pe_ttm||999);
    if(sort==="pb")return((a.pb||999))-(b.pb||999);
    if(sort==="ev")return((a.ev_ebitda||999))-(b.ev_ebitda||999);
    return(b.market_cap||0)-(a.market_cap||0);
  });
  return cos;
}

function renderCards(){
  const cos=getCompanies();
  const grid=document.getElementById("cards-grid");
  const noRes=document.getElementById("no-results");
  document.getElementById("result-count").textContent=`${cos.length} 家公司`;
  if(!cos.length){grid.innerHTML="";noRes.style.display="block";return;}
  noRes.style.display="none";
  grid.innerHTML=cos.map(c=>{
    const inComp=compareSet.some(x=>x.ticker===c.ticker);
    return`<div class="card${inComp?" in-compare":""}" id="card-${c.ticker}">
      ${roleBadge(c.role)}
      <div class="card-top">
        <span class="ticker">${c.ticker}</span>
        <span class="company-name">${c.name}</span>
      </div>
      <div><span class="sector-tag">${c.sector||""}</span></div>
      <div class="metrics">
        <div class="metric"><strong>${fmtMc(c.market_cap)}</strong> 市值</div>
        <div class="metric"><strong>${fmtNum(c.pe_ttm)}</strong> P/E</div>
        <div class="metric"><strong>${fmtNum(c.pb)}</strong> P/B</div>
        <div class="metric"><strong>${fmtNum(c.ev_ebitda)}</strong> EV/EBITDA</div>
      </div>
      ${c.summary?`<div class="card-summary">${c.summary}</div>`:""}
      <div class="add-compare" onclick="toggleCompare(event,'${c.ticker}','${c.name}')">${inComp?"✓":"+"}</div>
    </div>`;
  }).join("");
}

function renderThemes(){
  // Already rendered server-side, just highlight active
  document.querySelectorAll(".theme-item").forEach(el=>{
    el.classList.toggle("active",el.dataset.theme===activeTheme);
  });
}

function switchTheme(tag){
  activeTheme=tag;
  activeRole="";
  document.querySelectorAll(".role-btns button").forEach(b=>b.classList.toggle("active",b.dataset.role===""));
  renderThemes();
  renderCards();
}

// Role filter
document.getElementById("role-btns").addEventListener("click",e=>{
  const btn=e.target.closest("button");
  if(!btn)return;
  activeRole=btn.dataset.role;
  document.querySelectorAll(".role-btns button").forEach(b=>b.classList.toggle("active",b===btn));
  renderCards();
});

document.getElementById("search-input").addEventListener("input",renderCards);
document.getElementById("sort-sel").addEventListener("change",renderCards);

// Compare
function toggleCompare(e,ticker,name){
  e.stopPropagation();
  const idx=compareSet.findIndex(x=>x.ticker===ticker);
  if(idx>=0){
    compareSet.splice(idx,1);
  } else {
    if(compareSet.length>=5){alert("最多比較 5 家公司");return;}
    compareSet.push({ticker,name});
  }
  updateCompareBar();
  renderCards();
}

function updateCompareBar(){
  const bar=document.getElementById("compare-bar");
  bar.classList.toggle("visible",compareSet.length>0);
  document.getElementById("compare-slots").innerHTML=compareSet.map(c=>
    `<div class="compare-slot"><span class="ticker" style="font-size:10px">${c.ticker}</span>${c.name}<span class="remove" onclick="removeCompare('${c.ticker}')">×</span></div>`
  ).join("");
}

function removeCompare(ticker){
  compareSet=compareSet.filter(x=>x.ticker!==ticker);
  updateCompareBar();renderCards();
}

document.getElementById("clear-compare").addEventListener("click",()=>{
  compareSet=[];updateCompareBar();renderCards();
});

document.getElementById("compare-btn").addEventListener("click",openModal);

function openModal(){
  if(compareSet.length<2){alert("請至少選擇 2 家公司");return;}
  // Collect data for each company
  const allCos={};
  Object.values(DATA.themes).forEach(t=>t.companies.forEach(c=>{allCos[c.ticker]=c;}));
  const rows=compareSet.map(s=>allCos[s.ticker]||{ticker:s.ticker,name:s.name});

  const metrics=[
    ["市值 (百萬台幣)","market_cap",v=>v?v.toLocaleString():"—",true],
    ["P/E (TTM)","pe_ttm",v=>fmtNum(v),false],
    ["P/B","pb",v=>fmtNum(v),false],
    ["EV/EBITDA","ev_ebitda",v=>fmtNum(v),false],
    ["產業","sector",v=>v||"—",null],
    ["業務摘要","summary",v=>v||"—",null],
  ];

  let html=`<table class="compare-table">
    <tr><th>指標</th>${rows.map(r=>`<th><div class="ticker" style="display:inline-block;margin-bottom:4px">${r.ticker}</div><br>${r.name}</th>`).join("")}</tr>`;

  metrics.forEach(([label,key,fmt,higherBetter])=>{
    const vals=rows.map(r=>r[key]);
    let bestIdx=-1,worstIdx=-1;
    if(higherBetter!==null){
      const nums=vals.map(v=>typeof v==="number"?v:null);
      const valid=nums.filter(v=>v!==null);
      if(valid.length>1){
        const best=higherBetter?Math.max(...valid):Math.min(...valid);
        const worst=higherBetter?Math.min(...valid):Math.max(...valid);
        bestIdx=nums.indexOf(best);worstIdx=nums.indexOf(worst);
      }
    }
    html+=`<tr><td>${label}</td>${vals.map((v,i)=>{
      let cls="";if(i===bestIdx)cls=" class='best-val'";else if(i===worstIdx)cls=" class='worst-val'";
      return`<td${cls}>${fmt(v)}</td>`;
    }).join("")}</tr>`;
  });

  html+="</table>";
  document.getElementById("modal-content").innerHTML=html;
  document.getElementById("modal-overlay").classList.add("visible");
}

document.getElementById("modal-close").addEventListener("click",()=>{
  document.getElementById("modal-overlay").classList.remove("visible");
});
document.getElementById("modal-overlay").addEventListener("click",e=>{
  if(e.target===e.currentTarget)e.currentTarget.classList.remove("visible");
});

// CSV export
document.getElementById("export-csv").addEventListener("click",()=>{
  const allCos={};
  Object.values(DATA.themes).forEach(t=>t.companies.forEach(c=>{allCos[c.ticker]=c;}));
  const rows=compareSet.map(s=>allCos[s.ticker]||{ticker:s.ticker,name:s.name});
  const headers=["Ticker","名稱","產業","市值","P/E","P/B","EV/EBITDA","角色","摘要"];
  const lines=[headers.join(","),...rows.map(r=>[
    r.ticker,`"${r.name||""}"`,`"${r.sector||""}"`,
    r.market_cap||"",fmtNum(r.pe_ttm),fmtNum(r.pb),fmtNum(r.ev_ebitda),
    r.role||"",`"${(r.summary||"").replace(/"/g,"'")}"`
  ].join(","))];
  const blob=new Blob(["\ufeff"+lines.join("\n")],{type:"text/csv;charset=utf-8"});
  const a=document.createElement("a");a.href=URL.createObjectURL(blob);
  a.download=`compare_${new Date().toISOString().slice(0,10)}.csv`;a.click();
});

// Init
renderCards();
</script>
</body>
</html>"""


def build_screener_html(themes_data):
    """Generate themes/index.html with embedded data."""
    # Build sidebar theme list HTML
    categories = {
        "先進封裝": ["CoWoS", "HBM", "CPO"],
        "光電化合物半導體": ["矽光子", "VCSEL", "碳化矽", "氮化鎵", "磷化銦"],
        "AI / 資料中心": ["AI 伺服器", "資料中心", "NVIDIA"],
        "電動車 / 車用": ["電動車", "Tesla"],
        "通訊": ["5G", "低軌衛星"],
        "製程與設備": ["EUV"],
        "材料": ["光阻液", "ABF 載板", "矽晶圓"],
        "品牌供應鏈": ["Apple"],
    }

    theme_list_html = ""
    shown = set()
    for cat_name, tags in categories.items():
        available = [t for t in tags if t in themes_data["themes"]]
        if not available:
            continue
        theme_list_html += f'<div class="theme-group">{cat_name}</div>'
        for tag in available:
            count = len(themes_data["themes"][tag]["companies"])
            theme_list_html += (
                f'<div class="theme-item" data-theme="{tag}" onclick="switchTheme(\'{tag}\')">'
                f'{themes_data["themes"][tag]["name"]}'
                f'<span class="count">{count}</span></div>'
            )
            shown.add(tag)

    # Any extra themes not in categories (e.g., AI-discovered)
    extra = [t for t in themes_data["themes"] if t not in shown]
    if extra:
        theme_list_html += '<div class="theme-group">其他</div>'
        for tag in extra:
            count = len(themes_data["themes"][tag]["companies"])
            theme_list_html += (
                f'<div class="theme-item" data-theme="{tag}" onclick="switchTheme(\'{tag}\')">'
                f'{themes_data["themes"][tag]["name"]}'
                f'<span class="count">{count}</span></div>'
            )

    screener_json = json.dumps(themes_data, ensure_ascii=False)
    html = _SCREENER_TEMPLATE
    html = html.replace("__THEME_LIST__", theme_list_html)
    html = html.replace("__SCREENER_DATA__", screener_json)
    return html

# Curated themes with supply chain role hints
# Format: theme_wikilink -> { display_name, description, related_tags }
THEME_DEFINITIONS = {
    # === Advanced Packaging ===
    "CoWoS": {
        "name": "CoWoS 先進封裝",
        "desc": "台積電 Chip-on-Wafer-on-Substrate 2.5D 先進封裝技術，AI 晶片關鍵製程",
        "related": ["HBM", "2.5D 封裝", "3D 封裝", "ABF 載板", "矽中介層"],
    },
    "HBM": {
        "name": "HBM 高頻寬記憶體",
        "desc": "High Bandwidth Memory，AI 加速器必備的高速堆疊記憶體",
        "related": ["CoWoS", "AI 伺服器", "DRAM"],
    },
    "CPO": {
        "name": "CPO 共封裝光學",
        "desc": "Co-Packaged Optics，將光學元件整合於晶片封裝中以突破頻寬瓶頸",
        "related": ["矽光子", "光收發模組", "AI 伺服器", "資料中心"],
    },
    # === Photonics ===
    "矽光子": {
        "name": "矽光子 Silicon Photonics",
        "desc": "以矽基製程整合光學元件，實現高速光互連，下一代資料中心核心技術",
        "related": ["CPO", "EML", "VCSEL", "光收發模組", "資料中心"],
    },
    "VCSEL": {
        "name": "VCSEL 垂直共振腔面射型雷射",
        "desc": "3D 感測、光通訊及 LiDAR 核心光源元件",
        "related": ["矽光子", "光收發模組", "砷化鎵"],
    },
    # === Compound Semiconductors ===
    "碳化矽": {
        "name": "碳化矽 SiC",
        "desc": "第三代半導體材料，耐高壓高溫，電動車逆變器及充電樁關鍵材料",
        "related": ["電動車", "MOSFET", "IGBT", "氮化鎵"],
    },
    "氮化鎵": {
        "name": "氮化鎵 GaN",
        "desc": "第三代半導體材料，高頻高效，5G 基站、快充及衛星通訊核心",
        "related": ["5G", "碳化矽", "磷化銦"],
    },
    "磷化銦": {
        "name": "磷化銦 InP",
        "desc": "III-V 族化合物半導體，光通訊雷射及高速光電元件基板材料",
        "related": ["矽光子", "EML", "光收發模組", "砷化鎵"],
    },
    # === AI / Data Center ===
    "AI 伺服器": {
        "name": "AI 伺服器供應鏈",
        "desc": "AI 訓練與推論伺服器完整供應鏈，從晶片到系統到散熱",
        "related": ["CoWoS", "HBM", "NVIDIA", "CPO", "資料中心"],
    },
    "資料中心": {
        "name": "資料中心供應鏈",
        "desc": "超大規模資料中心基礎設施，涵蓋伺服器、網通、電源、散熱",
        "related": ["AI 伺服器", "CPO", "矽光子", "PCB"],
    },
    # === EV / Automotive ===
    "電動車": {
        "name": "電動車供應鏈",
        "desc": "電動車完整供應鏈，從電池材料到功率元件到車用電子",
        "related": ["碳化矽", "IGBT", "MOSFET", "車用電子"],
    },
    # === Applications ===
    "5G": {
        "name": "5G 通訊供應鏈",
        "desc": "5G 基礎建設與終端應用，涵蓋基站、天線、射頻前端、濾波器",
        "related": ["氮化鎵", "RF", "低軌衛星"],
    },
    "低軌衛星": {
        "name": "低軌衛星 LEO Satellite",
        "desc": "低軌道衛星通訊供應鏈，天線、地面站、射頻模組",
        "related": ["5G", "氮化鎵", "RF"],
    },
    # === Process / Equipment ===
    "EUV": {
        "name": "EUV 極紫外光微影",
        "desc": "先進製程關鍵微影技術，7nm 以下節點必備",
        "related": ["光阻液", "ASML"],
    },
    # === Materials ===
    "光阻液": {
        "name": "光阻液 Photoresist",
        "desc": "半導體微影製程關鍵化學材料",
        "related": ["EUV", "微影"],
    },
    "ABF 載板": {
        "name": "ABF 載板",
        "desc": "Ajinomoto Build-up Film 載板，高階 IC 封裝基板",
        "related": ["CoWoS", "AI 伺服器", "PCB"],
    },
    "矽晶圓": {
        "name": "矽晶圓",
        "desc": "半導體製造最基礎的原材料",
        "related": ["碳化矽", "磊晶"],
    },
    # === Key customers (cross-industry) ===
    "Apple": {
        "name": "Apple 蘋果供應鏈",
        "desc": "蘋果公司台灣供應鏈成員",
        "related": ["台積電", "鴻海"],
    },
    "NVIDIA": {
        "name": "NVIDIA 輝達供應鏈",
        "desc": "NVIDIA GPU 及 AI 平台台灣供應鏈",
        "related": ["CoWoS", "HBM", "AI 伺服器", "台積電"],
    },
    "Tesla": {
        "name": "Tesla 特斯拉供應鏈",
        "desc": "特斯拉電動車台灣供應鏈成員",
        "related": ["電動車", "碳化矽"],
    },
}


def scan_wikilinks():
    """Scan all reports, return {wikilink: [(ticker, company, sector, context)]}."""
    wl_map = defaultdict(list)

    for sector_dir in os.listdir(REPORTS_DIR):
        sector_path = os.path.join(REPORTS_DIR, sector_dir)
        if not os.path.isdir(sector_path):
            continue
        for f in os.listdir(sector_path):
            if not f.endswith(".md"):
                continue
            m = re.match(r"^(\d{4})_(.+)\.md$", f)
            if not m:
                continue
            ticker, company = m.group(1), m.group(2)
            filepath = os.path.join(sector_path, f)
            with open(filepath, "r", encoding="utf-8") as fh:
                content = fh.read()

            # Split content into sections for context
            sections = {
                "desc": "",
                "supply_chain": "",
                "customers": "",
            }
            parts = re.split(r"## ", content)
            for part in parts:
                if part.startswith("業務簡介"):
                    sections["desc"] = part
                elif part.startswith("供應鏈位置"):
                    sections["supply_chain"] = part
                elif part.startswith("主要客戶及供應商"):
                    sections["customers"] = part

            # Find all wikilinks in non-financial sections
            text = sections["desc"] + sections["supply_chain"] + sections["customers"]
            for wl in set(re.findall(r"\[\[([^\]]+)\]\]", text)):
                # Determine role from context
                role = "related"
                if wl in sections["supply_chain"]:
                    if "上游" in sections["supply_chain"].split(wl)[0][-100:]:
                        role = "upstream"
                    elif "下游" in sections["supply_chain"].split(wl)[0][-100:]:
                        role = "downstream"
                    elif "中游" in sections["supply_chain"].split(wl)[0][-100:]:
                        role = "midstream"

                wl_map[wl].append(
                    {
                        "ticker": ticker,
                        "company": company,
                        "sector": sector_dir,
                        "role": role,
                    }
                )

    return wl_map


def build_theme_page(theme_tag, theme_def, wl_map):
    """Build a single theme markdown page."""
    entries = wl_map.get(theme_tag, [])
    if not entries:
        return None

    lines = []
    lines.append(f"# {theme_def['name']}")
    lines.append("")
    lines.append(f"> {theme_def['desc']}")
    lines.append("")
    lines.append(f"**涵蓋公司數:** {len(entries)}")
    lines.append("")

    # Related themes
    related = theme_def.get("related", [])
    related_with_counts = []
    for r in related:
        count = len(wl_map.get(r, []))
        if count > 0:
            related_with_counts.append(f"[[{r}]] ({count})")
    if related_with_counts:
        lines.append(f"**相關主題:** {' | '.join(related_with_counts)}")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Group by role
    upstream = [e for e in entries if e["role"] == "upstream"]
    midstream = [e for e in entries if e["role"] == "midstream"]
    downstream = [e for e in entries if e["role"] == "downstream"]
    other = [e for e in entries if e["role"] == "related"]

    def format_entries(entries):
        # Group by sector
        by_sector = defaultdict(list)
        for e in entries:
            by_sector[e["sector"]].append(e)
        result = []
        for sector in sorted(by_sector.keys()):
            items = sorted(by_sector[sector], key=lambda x: x["ticker"])
            for item in items:
                result.append(
                    f"- **{item['ticker']} {item['company']}** ({sector})"
                )
        return result

    if upstream:
        lines.append(f"## 上游 ({len(upstream)})")
        lines.append("")
        lines.extend(format_entries(upstream))
        lines.append("")

    if midstream:
        lines.append(f"## 中游 ({len(midstream)})")
        lines.append("")
        lines.extend(format_entries(midstream))
        lines.append("")

    if downstream:
        lines.append(f"## 下游 ({len(downstream)})")
        lines.append("")
        lines.extend(format_entries(downstream))
        lines.append("")

    if other:
        lines.append(f"## 相關公司 ({len(other)})")
        lines.append("")
        lines.extend(format_entries(other))
        lines.append("")

    return "\n".join(lines)


def build_index(themes_built):
    """Build themes/README.md index."""
    lines = []
    lines.append("# Thematic Investment Screens")
    lines.append("")
    lines.append("> Auto-generated supply chain maps for thematic investing.")
    lines.append("> Regenerate: `python scripts/build_themes.py`")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Group by category
    categories = {
        "先進封裝": ["CoWoS", "HBM", "CPO"],
        "光電與化合物半導體": ["矽光子", "VCSEL", "碳化矽", "氮化鎵", "磷化銦"],
        "AI / 資料中心": ["AI 伺服器", "資料中心", "NVIDIA"],
        "電動車 / 車用": ["電動車", "Tesla"],
        "通訊": ["5G", "低軌衛星"],
        "製程與設備": ["EUV"],
        "材料": ["光阻液", "ABF 載板", "矽晶圓"],
        "品牌供應鏈": ["Apple", "NVIDIA", "Tesla"],
    }

    for cat_name, tags in categories.items():
        lines.append(f"## {cat_name}")
        lines.append("")
        for tag in tags:
            if tag in themes_built:
                count = themes_built[tag]
                safe_name = tag.replace(" ", "_").replace("/", "_")
                lines.append(f"- [{tag}]({safe_name}.md) — {count} 家公司")
        lines.append("")

    return "\n".join(lines)


def load_discovery_themes():
    """Load keywords from discoveries/INDEX.md that qualify as new themes.
    A keyword qualifies if: count >= 5 AND not already in THEME_DEFINITIONS.
    Returns dict of {keyword: {"name": ..., "desc": ..., "related": [], "source": "discovery"}}.
    """
    discoveries_dir = os.path.join(os.path.dirname(__file__), "..", "discoveries")
    index_path = os.path.join(discoveries_dir, "INDEX.md")
    if not os.path.exists(index_path):
        return {}

    new_themes = {}
    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Parse table rows: | date | keyword | count | mode | applied | file |
    for m in re.finditer(r"\|\s*[\d-]+\s*\|\s*(.+?)\s*\|\s*(\d+)\s*\|", content):
        keyword = m.group(1).strip()
        count = int(m.group(2))
        if count >= 5 and keyword not in THEME_DEFINITIONS:
            new_themes[keyword] = {
                "name": f"{keyword}（AI 發現）",
                "desc": f"由 discover.py 自動發現，共 {count} 家台灣上市公司相關。",
                "related": [],
                "source": "discovery",
            }
    return new_themes


def main():
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    os.makedirs(THEMES_DIR, exist_ok=True)

    args = sys.argv[1:]

    if "--list" in args:
        for tag, defn in sorted(THEME_DEFINITIONS.items()):
            print(f"  {tag}: {defn['name']}")
        return

    print("Scanning wikilinks across all reports...")
    wl_map = scan_wikilinks()
    print(f"Found {len(wl_map)} unique wikilinks.\n")

    # Collect financial data for all companies (used in screener)
    print("Collecting company financials...")
    company_financials = collect_company_financials()
    print(f"  Loaded financials for {len(company_financials)} companies\n")

    # Load discovery-sourced themes
    discovery_themes = load_discovery_themes()
    if discovery_themes:
        print(f"Loaded {len(discovery_themes)} themes from discoveries/INDEX.md")

    # Merge: THEME_DEFINITIONS takes precedence
    all_themes = {**THEME_DEFINITIONS, **discovery_themes}

    # Filter to requested theme or build all
    if args and args[0] != "--list":
        themes_to_build = {args[0]: all_themes.get(args[0])}
        if not themes_to_build[args[0]]:
            print(f"Theme '{args[0]}' not found. Use --list to see available themes.")
            return
    else:
        themes_to_build = all_themes

    themes_built = {}
    for tag, defn in themes_to_build.items():
        page = build_theme_page(tag, defn, wl_map)
        if page:
            safe_name = tag.replace(" ", "_").replace("/", "_")
            filepath = os.path.join(THEMES_DIR, f"{safe_name}.md")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(page)
            count = len(wl_map.get(tag, []))
            themes_built[tag] = count
            source_tag = " [AI發現]" if defn.get("source") == "discovery" else ""
            print(f"  {tag}: {count} companies -> {safe_name}.md{source_tag}")

    # Build index
    index = build_index(themes_built)
    with open(os.path.join(THEMES_DIR, "README.md"), "w", encoding="utf-8") as f:
        f.write(index)

    # Build themes/data.json (for external consumers, e.g. static site)
    screener_data = {"generated": str(date.today()), "themes": {}}
    for tag, defn in themes_to_build.items():
        entries = wl_map.get(tag, [])
        if not entries:
            continue
        companies = []
        for e in entries:
            fin = company_financials.get((e["ticker"], e["company"]), {})
            companies.append({
                "ticker": e["ticker"],
                "name": e["company"],
                "sector": e["sector"],
                "role": e["role"],
                "market_cap": fin.get("market_cap", 0),
                "pe_ttm": fin.get("pe_ttm"),
                "pb": fin.get("pb"),
                "ev_ebitda": fin.get("ev_ebitda"),
                "summary": fin.get("summary", ""),
            })
        screener_data["themes"][tag] = {
            "name": defn["name"],
            "desc": defn.get("desc", ""),
            "companies": companies,
        }

    data_path = os.path.join(THEMES_DIR, "data.json")
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(screener_data, f, ensure_ascii=False, indent=2)
    print(f"Saved: themes/data.json ({len(screener_data['themes'])} themes)")

    # Build themes/index.html (interactive screener)
    screener_html = build_screener_html(screener_data)
    html_path = os.path.join(THEMES_DIR, "index.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(screener_html)
    print(f"Saved: themes/index.html")

    print(f"\nDone. Generated {len(themes_built)} theme pages in themes/")


if __name__ == "__main__":
    main()
