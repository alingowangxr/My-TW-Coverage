"""
build_network.py — Generate wikilink network graph data and interactive visualization.

Scans all ticker reports for wikilink co-occurrences and generates:
1. network/graph_data.json — node/edge data for visualization
2. network/index.html — interactive D3.js force-directed graph

Usage:
  python scripts/build_network.py                # Default: min 5 co-occurrences
  python scripts/build_network.py --min-weight 10  # Higher threshold = fewer edges
  python scripts/build_network.py --top 100       # Only top N nodes by mention count
"""

import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import (
    REPORTS_DIR, setup_stdout,
    classify_wikilink, CATEGORY_COLORS, CATEGORY_LABELS,
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NETWORK_DIR = os.path.join(PROJECT_ROOT, "network")


def extract_company_meta(filepath, sector):
    """Extract metadata from a single report file."""
    rel_path = os.path.relpath(filepath, PROJECT_ROOT).replace("\\", "/")
    with open(filepath, "r", encoding="utf-8") as fh:
        content = fh.read().split("## 財務概況")[0]

    sector_en_m = re.search(r"\*\*板塊:\*\*\s*(.+)", content)
    industry_en_m = re.search(r"\*\*產業:\*\*\s*(.+)", content)

    # Extract first ~80 chars of prose after the metadata block
    summary = ""
    desc_m = re.search(r"\*\*企業價值:\*\*[^\n]*\n+(.{1,300})", content, re.DOTALL)
    if desc_m:
        raw = desc_m.group(1).strip()
        raw = re.sub(r"\[\[([^\]]+)\]\]", r"\1", raw)  # strip wikilinks
        raw = re.sub(r"\*+", "", raw)
        raw = re.sub(r"\s+", " ", raw).strip()
        summary = raw[:80]

    return {
        "file_path": rel_path,
        "sector": sector,
        "sector_en": sector_en_m.group(1).strip() if sector_en_m else "",
        "industry_en": industry_en_m.group(1).strip() if industry_en_m else "",
        "summary": summary,
    }


def scan_graph(min_weight=5, top_n=None):
    """Scan all reports and build co-occurrence graph."""
    # Step 1: collect wikilinks per file + metadata for Taiwan companies
    node_counts = defaultdict(int)
    wl_per_file = {}
    company_meta = {}  # Chinese company name -> metadata dict

    for root, dirs, files in os.walk(REPORTS_DIR):
        sector = os.path.basename(root)
        for f in files:
            if not f.endswith(".md"):
                continue
            m = re.match(r"^(\d{4})_(.+)\.md$", f)
            if not m:
                continue
            ticker, company_name = m.group(1), m.group(2)
            filepath = os.path.join(root, f)

            with open(filepath, "r", encoding="utf-8") as fh:
                content = fh.read().split("## 財務概況")[0]
            wls = set(re.findall(r"\[\[([^\]]+)\]\]", content))
            wl_per_file[ticker] = wls
            for wl in wls:
                node_counts[wl] += 1

            # Store metadata keyed by company name (matches wikilink text)
            meta = extract_company_meta(filepath, sector)
            meta["ticker"] = ticker
            company_meta[company_name] = meta

    # Step 2: filter to top N nodes if specified
    if top_n:
        top_nodes = set(
            name for name, _ in sorted(node_counts.items(), key=lambda x: -x[1])[:top_n]
        )
    else:
        top_nodes = set(name for name, count in node_counts.items() if count >= 2)

    # Step 3: count co-occurrences
    edges = defaultdict(int)
    for ticker, wls in wl_per_file.items():
        filtered = sorted(wls & top_nodes)
        for i in range(len(filtered)):
            for j in range(i + 1, len(filtered)):
                edges[(filtered[i], filtered[j])] += 1

    # Step 4: filter edges by weight
    filtered_edges = {k: v for k, v in edges.items() if v >= min_weight}

    # Step 5: only keep nodes that have at least one edge
    active_nodes = set()
    for (a, b) in filtered_edges:
        active_nodes.add(a)
        active_nodes.add(b)

    nodes = []
    for name in active_nodes:
        cat = classify_wikilink(name)
        node = {
            "id": name,
            "count": node_counts[name],
            "category": cat,
            "color": CATEGORY_COLORS[cat],
        }
        # Enrich Taiwan company nodes with report metadata
        if name in company_meta:
            node.update(company_meta[name])
        nodes.append(node)

    edge_list = []
    for (source, target), weight in filtered_edges.items():
        edge_list.append({
            "source": source,
            "target": target,
            "weight": weight,
        })

    return nodes, edge_list


_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="utf-8">
<title>Taiwan Stock Wikilink Network</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#1a1a2e;color:#eee;overflow:hidden}
input,select{background:#2a2a4e;border:1px solid #445;color:#eee;border-radius:4px;font-size:12px}
input[type=text],select{width:100%;padding:4px 7px;margin-top:2px}
input[type=range]{width:100%;margin-top:3px;accent-color:#3498db}
button{background:#2980b9;color:#fff;border:none;border-radius:4px;padding:4px 10px;cursor:pointer;font-size:12px;width:100%;margin-top:4px}
button:hover{background:#3498db}
hr{border:none;border-top:1px solid #333;margin:10px 0}
/* Left panel */
#left-panel{position:fixed;left:0;top:0;width:230px;height:100vh;overflow-y:auto;background:rgba(20,20,40,0.97);border-right:1px solid #333;padding:14px;z-index:20;scrollbar-width:thin}
#left-panel h2{font-size:15px;margin-bottom:10px;color:#aad}
.ctrl-label{font-size:11px;color:#aaa;margin:8px 0 2px;text-transform:uppercase;letter-spacing:.5px}
.weight-row{display:flex;align-items:center;gap:6px}
#weightVal{min-width:24px;text-align:right;font-size:13px;color:#3db}
.checkbox-row{display:flex;align-items:center;gap:6px;margin:3px 0;font-size:12px;cursor:pointer}
.checkbox-row input{width:auto;cursor:pointer}
.dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
/* Path result */
#path-result{font-size:11px;margin-top:6px;color:#9da;max-height:80px;overflow-y:auto;line-height:1.6}
/* Info panel */
#info-panel{position:fixed;right:0;top:0;width:280px;height:100vh;background:rgba(20,20,40,0.97);border-left:1px solid #333;padding:16px;z-index:20;display:none;overflow-y:auto}
#info-panel .ticker-badge{display:inline-block;background:#c0392b;color:#fff;padding:2px 8px;border-radius:3px;font-size:13px;font-weight:bold;margin-bottom:6px}
#info-panel .company-name{font-size:16px;font-weight:bold;margin-bottom:4px;line-height:1.3}
#info-panel .meta-row{font-size:11px;color:#aaa;margin-bottom:2px}
#info-panel .summary{font-size:12px;color:#ccc;margin:8px 0;line-height:1.5;border-left:2px solid #445;padding-left:8px}
#info-panel .section-title{font-size:11px;color:#aaa;text-transform:uppercase;letter-spacing:.5px;margin:10px 0 4px}
#info-panel .neighbor-list{font-size:12px;line-height:1.8}
#info-panel .neighbor-list span{cursor:pointer;color:#7aabdb}
#info-panel .neighbor-list span:hover{text-decoration:underline}
#report-link{display:block;background:#2980b9;color:#fff;text-align:center;padding:6px;border-radius:4px;font-size:12px;text-decoration:none;margin-top:10px}
#report-link:hover{background:#3498db}
#close-info{position:absolute;right:10px;top:10px;cursor:pointer;color:#666;font-size:18px;line-height:1}
#close-info:hover{color:#eee}
/* Legend */
#legend{position:fixed;bottom:10px;left:230px;z-index:10;background:rgba(20,20,40,0.9);padding:8px 12px;border-radius:8px;border:1px solid #333;display:flex;flex-wrap:wrap;gap:4px 14px}
.leg-item{display:flex;align-items:center;gap:5px;font-size:11px}
/* Stats */
#stats{position:fixed;top:10px;right:__STATS_RIGHT__px;z-index:10;background:rgba(20,20,40,0.9);padding:8px 12px;border-radius:8px;border:1px solid #333;font-size:12px;color:#aaa}
svg{width:100vw;height:100vh}
/* Path highlight */
.path-node{stroke:#f1c40f!important;stroke-width:2.5!important}
.path-link{stroke:#f1c40f!important;stroke-opacity:0.9!important}
</style>
</head>
<body>

<div id="left-panel">
  <h2>TW Wikilink Network</h2>

  <div class="ctrl-label">最小 Edge 權重</div>
  <div class="weight-row">
    <input type="range" id="weightSlider" min="1" max="50" value="2">
    <span id="weightVal">2</span>
  </div>

  <div class="ctrl-label">搜尋節點</div>
  <input type="text" id="search" placeholder="e.g. 台積電, CoWoS, NVIDIA">

  <hr>
  <div class="ctrl-label">產業篩選</div>
  <select id="sectorFilter">
    <option value="">全部</option>
  </select>

  <div class="ctrl-label" style="margin-top:10px">類型篩選</div>
  <div id="typeFilters">__TYPE_CHECKBOXES__</div>

  <hr>
  <div class="ctrl-label">供應鏈路徑查詢</div>
  <input type="text" id="pathStart" placeholder="起點：e.g. 台積電">
  <input type="text" id="pathEnd" placeholder="終點：e.g. Apple" style="margin-top:4px">
  <button id="pathBtn">查詢最短路徑</button>
  <button id="clearPathBtn" style="background:#555;margin-top:3px">清除路徑</button>
  <div id="path-result"></div>
</div>

<div id="info-panel">
  <span id="close-info">×</span>
  <div id="info-content"></div>
</div>

<div id="legend">__LEGEND_ITEMS__</div>
<div id="stats"></div>
<svg></svg>

<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
// ─── Config ──────────────────────────────────────────────────────────────────
// Set your GitHub repo URL to enable "Open Report" links, e.g.:
// const GITHUB_REPO = "https://github.com/yourname/My-TW-Coverage";
const GITHUB_REPO = "";

// ─── Data ────────────────────────────────────────────────────────────────────
const fullData = __GRAPH_DATA__;
const width = window.innerWidth, height = window.innerHeight;
const PANEL_LEFT = 230, PANEL_RIGHT = 280;

// ─── State ───────────────────────────────────────────────────────────────────
let simulation, linkG, nodeG, labelG;
let activeMinWeight = 2;
let activeSector = "";
let activeTypes = new Set(["taiwan_company","international_company","technology","material","application"]);
let highlightedPath = null;

// ─── SVG setup ───────────────────────────────────────────────────────────────
const svg = d3.select("svg");
const g = svg.append("g");
svg.call(d3.zoom().scaleExtent([0.05, 12]).on("zoom", e => g.attr("transform", e.transform)));

// ─── Sector dropdown population ──────────────────────────────────────────────
const sectors = [...new Set(fullData.nodes.filter(n => n.sector).map(n => n.sector))].sort();
const sectorSel = document.getElementById("sectorFilter");
sectors.forEach(s => { const o = document.createElement("option"); o.value = s; o.textContent = s; sectorSel.appendChild(o); });

// ─── Render ──────────────────────────────────────────────────────────────────
function render() {
  const links = fullData.links.filter(l => l.weight >= activeMinWeight);
  const activeIds = new Set();
  links.forEach(l => { activeIds.add(l.source.id || l.source); activeIds.add(l.target.id || l.target); });
  const nodes = fullData.nodes.filter(n =>
    activeIds.has(n.id) &&
    activeTypes.has(n.category) &&
    (!activeSector || n.sector === activeSector)
  );
  const nodeIdSet = new Set(nodes.map(n => n.id));
  const visibleLinks = links.filter(l => {
    const s = l.source.id || l.source, t = l.target.id || l.target;
    return nodeIdSet.has(s) && nodeIdSet.has(t);
  });

  document.getElementById("stats").innerHTML = `節點 ${nodes.length} &nbsp;| 邊 ${visibleLinks.length}`;
  g.selectAll("*").remove();

  if (!nodes.length) return;

  const maxCount = d3.max(nodes, d => d.count) || 1;
  const rScale = d3.scaleSqrt().domain([1, maxCount]).range([4, 38]);
  const wScale = d3.scaleLinear().domain([activeMinWeight, d3.max(visibleLinks, l => l.weight) || activeMinWeight]).range([0.5, 4]);
  const oScale = d3.scaleLinear().domain([activeMinWeight, d3.max(visibleLinks, l => l.weight) || activeMinWeight]).range([0.12, 0.55]);

  simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(visibleLinks).id(d => d.id).distance(80).strength(0.3))
    .force("charge", d3.forceManyBody().strength(nodes.length > 300 ? -100 : -150))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collision", d3.forceCollide().radius(d => rScale(d.count) + 2));

  linkG = g.append("g").selectAll("line").data(visibleLinks).join("line")
    .attr("stroke", "#556").attr("stroke-opacity", d => oScale(d.weight))
    .attr("stroke-width", d => wScale(d.weight));

  nodeG = g.append("g").selectAll("circle").data(nodes).join("circle")
    .attr("r", d => rScale(d.count)).attr("fill", d => d.color)
    .attr("stroke", "#fff").attr("stroke-width", 0.5).attr("opacity", 0.9)
    .attr("cursor", "pointer")
    .call(d3.drag().on("start", dragStart).on("drag", dragging).on("end", dragEnd))
    .on("mouseover", (e, d) => { highlightNeighbors(d); showInfoPanel(d, visibleLinks); })
    .on("mouseout", () => { if (!highlightedPath) resetHighlight(); })
    .on("click", (e, d) => { e.stopPropagation(); showInfoPanel(d, visibleLinks, true); });

  labelG = g.append("g").selectAll("text").data(nodes.filter(d => d.count >= 15)).join("text")
    .text(d => d.id).attr("font-size", d => Math.max(8, Math.min(13, rScale(d.count) * 0.65)))
    .attr("fill", "#ccc").attr("text-anchor", "middle").attr("dy", d => rScale(d.count) + 11)
    .style("pointer-events", "none");

  simulation.on("tick", () => {
    linkG.attr("x1", d=>d.source.x).attr("y1", d=>d.source.y).attr("x2", d=>d.target.x).attr("y2", d=>d.target.y);
    nodeG.attr("cx", d=>d.x).attr("cy", d=>d.y);
    labelG.attr("x", d=>d.x).attr("y", d=>d.y);
  });

  // Re-apply path highlight if active
  if (highlightedPath) applyPathHighlight(highlightedPath);
}

// ─── Info Panel ──────────────────────────────────────────────────────────────
function showInfoPanel(d, currentLinks, pinned) {
  const panel = document.getElementById("info-panel");
  const content = document.getElementById("info-content");
  panel.style.display = "block";

  // Top 5 neighbors by weight
  const neighbors = [];
  currentLinks.forEach(l => {
    const s = l.source.id || l.source, t = l.target.id || l.target;
    if (s === d.id) neighbors.push({ id: t, w: l.weight });
    if (t === d.id) neighbors.push({ id: s, w: l.weight });
  });
  neighbors.sort((a, b) => b.w - a.w);
  const top5 = neighbors.slice(0, 5);

  let reportLinkHtml = "";
  if (d.file_path) {
    if (GITHUB_REPO) {
      reportLinkHtml = `<a id="report-link" href="${GITHUB_REPO}/blob/master/${d.file_path}" target="_blank">查看完整報告 →</a>`;
    } else {
      reportLinkHtml = `<div style="font-size:11px;color:#777;margin-top:8px;word-break:break-all">${d.file_path}</div>`;
    }
  }

  const tickerBadge = d.ticker ? `<div class="ticker-badge">${d.ticker}</div>` : "";
  const sectorInfo = (d.sector_en || d.industry_en)
    ? `<div class="meta-row">板塊: ${d.sector_en || ""} &nbsp;/&nbsp; ${d.industry_en || ""}</div>` : "";
  const summaryHtml = d.summary ? `<div class="summary">${d.summary}…</div>` : "";

  const neighborHtml = top5.length
    ? top5.map(n => `<span onclick="focusNode('${n.id}')">${n.id}</span> <small style="color:#555">(${n.w})</small>`).join("<br>")
    : "—";

  content.innerHTML = `
    ${tickerBadge}
    <div class="company-name">${d.id}</div>
    ${sectorInfo}
    <div class="meta-row">提及次數: ${d.count} &nbsp;|&nbsp; 類別: ${d.category}</div>
    ${summaryHtml}
    <div class="section-title">前 5 大關聯節點</div>
    <div class="neighbor-list">${neighborHtml}</div>
    ${reportLinkHtml}
  `;
}

function focusNode(nodeId) {
  const node = fullData.nodes.find(n => n.id === nodeId);
  if (node) {
    highlightNeighbors(node);
    showInfoPanel(node, fullData.links);
  }
}

document.getElementById("close-info").addEventListener("click", () => {
  document.getElementById("info-panel").style.display = "none";
});

svg.on("click", () => {
  resetHighlight();
  document.getElementById("info-panel").style.display = "none";
});

// ─── Highlight ───────────────────────────────────────────────────────────────
function highlightNeighbors(d) {
  if (!nodeG) return;
  const neighbors = new Set([d.id]);
  linkG.each(l => {
    if ((l.source.id||l.source) === d.id) neighbors.add(l.target.id||l.target);
    if ((l.target.id||l.target) === d.id) neighbors.add(l.source.id||l.source);
  });
  nodeG.attr("opacity", n => neighbors.has(n.id) ? 1 : 0.08);
  linkG.attr("stroke-opacity", l => ((l.source.id||l.source)===d.id||(l.target.id||l.target)===d.id) ? 0.75 : 0.02);
  labelG.attr("opacity", n => neighbors.has(n.id) ? 1 : 0.05);
}

function resetHighlight() {
  if (!nodeG) return;
  nodeG.attr("opacity", 0.9).classed("path-node", false);
  linkG.attr("stroke-opacity", d => 0.3).attr("stroke", "#556").classed("path-link", false);
  labelG.attr("opacity", 1);
  highlightedPath = null;
  document.getElementById("path-result").textContent = "";
}

// ─── Shortest Path (BFS) ─────────────────────────────────────────────────────
function buildAdjacency(links) {
  const adj = {};
  links.forEach(l => {
    const s = l.source.id||l.source, t = l.target.id||l.target;
    (adj[s] = adj[s]||[]).push(t);
    (adj[t] = adj[t]||[]).push(s);
  });
  return adj;
}

function bfs(startId, endId, adj) {
  const queue = [[startId]];
  const visited = new Set([startId]);
  while (queue.length) {
    const path = queue.shift();
    const node = path[path.length - 1];
    if (node === endId) return path;
    for (const nb of (adj[node]||[])) {
      if (!visited.has(nb)) { visited.add(nb); queue.push([...path, nb]); }
    }
  }
  return null;
}

function applyPathHighlight(path) {
  if (!nodeG || !path) return;
  const pathSet = new Set(path);
  const pathEdges = new Set();
  for (let i = 0; i < path.length - 1; i++) pathEdges.add(path[i] + "→" + path[i+1]);

  nodeG.attr("opacity", n => pathSet.has(n.id) ? 1 : 0.08)
       .classed("path-node", n => pathSet.has(n.id));
  linkG.attr("stroke", l => {
    const s = l.source.id||l.source, t = l.target.id||l.target;
    return (pathEdges.has(s+"→"+t)||pathEdges.has(t+"→"+s)) ? "#f1c40f" : "#556";
  }).attr("stroke-opacity", l => {
    const s = l.source.id||l.source, t = l.target.id||l.target;
    return (pathEdges.has(s+"→"+t)||pathEdges.has(t+"→"+s)) ? 0.9 : 0.04;
  });
  labelG.attr("opacity", n => pathSet.has(n.id) ? 1 : 0.05);
}

document.getElementById("pathBtn").addEventListener("click", () => {
  const startId = document.getElementById("pathStart").value.trim();
  const endId = document.getElementById("pathEnd").value.trim();
  const resultDiv = document.getElementById("path-result");
  if (!startId || !endId) { resultDiv.textContent = "請輸入起點和終點"; return; }

  const currentLinks = fullData.links.filter(l => l.weight >= activeMinWeight);
  const adj = buildAdjacency(currentLinks);
  const path = bfs(startId, endId, adj);

  if (!path) {
    resultDiv.textContent = `找不到 ${startId} → ${endId} 的路徑`;
    return;
  }
  highlightedPath = path;
  applyPathHighlight(path);
  resultDiv.innerHTML = `路徑 (${path.length} 節點):<br>${path.join(" → ")}`;
});

document.getElementById("clearPathBtn").addEventListener("click", resetHighlight);

// ─── Controls ────────────────────────────────────────────────────────────────
document.getElementById("weightSlider").addEventListener("input", function() {
  activeMinWeight = +this.value;
  document.getElementById("weightVal").textContent = activeMinWeight;
  render();
});

document.getElementById("search").addEventListener("input", function() {
  const q = this.value.toLowerCase().trim();
  if (!q) { resetHighlight(); return; }
  const match = fullData.nodes.find(n => n.id.toLowerCase().includes(q));
  if (match) highlightNeighbors(match);
});

document.getElementById("sectorFilter").addEventListener("change", function() {
  activeSector = this.value;
  render();
});

document.querySelectorAll(".type-cb").forEach(cb => {
  cb.addEventListener("change", function() {
    if (this.checked) activeTypes.add(this.value);
    else activeTypes.delete(this.value);
    render();
  });
});

// ─── Drag ────────────────────────────────────────────────────────────────────
function dragStart(e, d) { if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx=d.x; d.fy=d.y; }
function dragging(e, d) { d.fx=e.x; d.fy=e.y; }
function dragEnd(e, d) { if (!e.active) simulation.alphaTarget(0); d.fx=null; d.fy=null; }

// ─── Init ────────────────────────────────────────────────────────────────────
render();
</script>
</body>
</html>"""


def build_html(nodes, edges):
    """Generate self-contained D3.js interactive network visualization."""
    graph_json = json.dumps({"nodes": nodes, "links": edges}, ensure_ascii=False)

    legend_items = "".join(
        f'<div class="leg-item">'
        f'<div class="dot" style="background:{CATEGORY_COLORS[k]}"></div>'
        f'<span>{CATEGORY_LABELS[k]}</span></div>'
        for k in CATEGORY_COLORS
    )

    type_checkboxes = "".join(
        f'<label class="checkbox-row">'
        f'<input type="checkbox" class="type-cb" value="{k}" checked>'
        f'<div class="dot" style="background:{CATEGORY_COLORS[k]}"></div>'
        f'<span>{CATEGORY_LABELS[k]}</span></label>'
        for k in CATEGORY_COLORS
    )

    html = _HTML_TEMPLATE
    html = html.replace("__GRAPH_DATA__", graph_json)
    html = html.replace("__LEGEND_ITEMS__", legend_items)
    html = html.replace("__TYPE_CHECKBOXES__", type_checkboxes)
    html = html.replace("__STATS_RIGHT__", "292")  # right panel width + margin
    return html


def main():
    setup_stdout()

    args = sys.argv[1:]
    min_weight = 5
    top_n = None

    for i, arg in enumerate(args):
        if arg == "--min-weight" and i + 1 < len(args):
            min_weight = int(args[i + 1])
        elif arg == "--top" and i + 1 < len(args):
            top_n = int(args[i + 1])

    os.makedirs(NETWORK_DIR, exist_ok=True)

    print(f"Scanning wikilink co-occurrences (min weight: {min_weight})...")
    nodes, edges = scan_graph(min_weight=min_weight, top_n=top_n)
    print(f"Graph: {len(nodes)} nodes, {len(edges)} edges")

    # Save JSON data
    graph_data = {"nodes": nodes, "links": edges}
    json_path = os.path.join(NETWORK_DIR, "graph_data.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(graph_data, f, ensure_ascii=False, indent=2)
    print(f"Saved: {json_path}")

    # Generate HTML
    html = build_html(nodes, edges)
    html_path = os.path.join(NETWORK_DIR, "index.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Saved: {html_path}")

    print(f"\nOpen in browser: {html_path}")
    print("Or serve locally: python -m http.server 8000 --directory network/")


if __name__ == "__main__":
    main()
