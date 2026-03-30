# Taiwan Stock Coverage Database

A structured equity research database covering **1,735 Taiwan-listed companies** (TWSE + OTC) across **99 industry sectors**. Each report maps business overview, supply chain position, and customer/supplier relationships — cross-referenced through **4,900+ wikilinks** that form a searchable knowledge graph.

**The wikilink graph is the core feature.** Searching `[[Apple]]` reveals 207 Taiwanese companies in Apple's supply chain. Searching `[[CoWoS]]` shows every company involved in TSMC's advanced packaging. Searching `[[光阻液]]` maps every photoresist supplier and consumer.

**Live site:** https://alingowangxr.github.io/My-TW-Coverage/

---

## Quick Start

```bash
pip install yfinance pandas tabulate InquirerPy rich markdown
python tw.py          # Interactive menu — all tools in one place
```

---

## User Interfaces

### `tw.py` — Interactive CLI (Recommended)

Unified entry point for all operations. No need to remember script names or arguments.

```bash
python tw.py                         # Launch interactive menu
python tw.py discover 液冷散熱        # Direct CLI mode
python tw.py financials 2330         # Direct CLI mode
python tw.py lookup 台積電            # Fuzzy company search
python tw.py --help                  # Full command reference
```

**Interactive menu:**
```
My TW Coverage | 報告: 1,735 | 批次: 132
? 請選擇操作：
  🔍  搜尋主題 (discover)
  📊  查詢公司 (lookup)
  🔄  更新財務 (update_financials)
  ✏️   更新估值 (update_valuation)
  📝  新增報告 (add_ticker)
  🏭  產生主題圖 (build_themes)
  🕸️   重建網路圖 (build_network)
  🔗  重建 Wikilink 索引
  ✅  品質稽核 (audit)
  ❌  離開
```

All operations log to `logs/tw_operations.log`.

---

### Static Search Website

Full-text searchable website over all 1,735 reports. Zero backend — pure static HTML.

```bash
python scripts/build_site.py                  # Full build (~5 min)
python scripts/build_site.py --no-reports     # Index + sector pages only (fast preview)
python -m http.server 8080 --directory site/
# Open http://localhost:8080/
```

**Features:**
- **Fuse.js search** — search by company name, ticker, technology, or material
- **Sector filter** — filter by any of 99 industry sectors
- **Wikilink filter** — click `[[CoWoS]]` on any page → see all CoWoS-related companies
- **Sort** — by market cap, P/E, P/B, or EV/EBITDA
- **Individual report pages** — markdown converted to HTML with clickable wikilinks, sidebar with valuation metrics and related companies
- **URL parameters**: `?q=台積電`, `?s=Semiconductors`, `?wl=CoWoS`

**GitHub Pages:** push to master → auto-deploys via GitHub Actions (see `.github/workflows/build-site.yml`).

---

### Thematic Screener (`themes/index.html`)

Interactive screener for the 21 curated supply chain themes.

```bash
python scripts/build_themes.py   # Regenerates themes/index.html + themes/data.json
# Then open themes/index.html in browser
```

**Features:**
- Left sidebar: 21 themes grouped by category (advanced packaging, photonics, EV, AI, materials…)
- Company cards with upstream/midstream/downstream role badges
- Sort by market cap, P/E, P/B, EV/EBITDA
- Supply chain role filter (上游/中游/下游)
- **Compare up to 5 companies** side-by-side (best/worst highlighting)
- **CSV export** of comparison data
- AI-discovered themes automatically added from `discoveries/INDEX.md`

---

### Wikilink Network Graph (`network/index.html`)

Interactive D3.js force-directed graph showing wikilink co-occurrences.

```bash
python scripts/build_network.py                # Default: min 5 co-occurrences
python scripts/build_network.py --min-weight 10  # Fewer, stronger edges
python scripts/build_network.py --top 200       # Only top 200 nodes
# Open network/index.html in browser
```

**Features:**
- Hover preview panel — company info, valuation metrics, top 5 connections
- **Sector filter** dropdown — isolate any of 99 sectors
- **Category type** checkboxes — show/hide Taiwan companies, international companies, technologies, materials, applications
- **Shortest path finder** — type two node names → highlights the supply chain path between them
- Click Taiwan company nodes → opens full report (set `GITHUB_REPO` in the HTML)
- Node size ∝ mention count; edge weight ∝ co-occurrence frequency

---

### Obsidian Vault

The `[[wikilink]]` format is natively compatible with Obsidian. One command to set up:

```bash
python scripts/setup_obsidian.py
# Then: obsidian://open?vault=My-TW-Coverage
```

**What you get immediately:**
- **Graph View** (`Ctrl+G`) — 1,735 nodes, color-coded by sector category
- **Quick Switcher** (`Ctrl+O`) — jump to any company by ticker or name
- **Backlinks panel** — open 台積電.md → see 469 companies that reference it
- **Full-text search** (`Ctrl+Shift+F`) — search across all reports

See `docs/obsidian-guide.md` for recommended plugins (Dataview, Excalidraw).

---

## Python Scripts Reference

All scripts support the same **scope syntax**:

| Scope | Example |
|---|---|
| Single ticker | `2330` |
| Multiple tickers | `2330 2317 3034` |
| By batch | `--batch 101` |
| By sector | `--sector Semiconductors` |
| All tickers | *(no args)* |

### Core Scripts

```bash
# Add new company report
python scripts/add_ticker.py 2330 台積電

# Refresh financial tables (3yr annual + 4Q quarterly)
python scripts/update_financials.py [scope]

# Refresh valuation multiples only — P/E, P/B, EV/EBITDA (~3× faster)
python scripts/update_valuation.py [scope]

# Apply enrichment content from JSON
python scripts/update_enrichment.py --data enrichment.json [scope]

# Quality audit (8 validation rules)
python scripts/audit_batch.py [scope] -v
python scripts/audit_batch.py --all -v

# Rebuild WIKILINKS.md cross-reference index
python scripts/build_wikilink_index.py
```

### Discovery & Analysis

```bash
# Find companies related to a buzzword
python scripts/discover.py "液冷散熱"                    # All sectors
python scripts/discover.py "液冷散熱" --smart            # Auto-filter sectors
python scripts/discover.py "液冷散熱" --apply            # Tag [[wikilinks]] in reports
python scripts/discover.py "液冷散熱" --apply --rebuild  # + rebuild themes & network

# Results auto-saved to discoveries/YYYY-MM-DD_{keyword}.md
# Build discovery index
python scripts/build_discovery_index.py   # Regenerates discoveries/INDEX.md

# Generate thematic investment screens
python scripts/build_themes.py             # All 21 themes + index.html + data.json
python scripts/build_themes.py "CoWoS"    # Single theme
python scripts/build_themes.py --list     # List all themes

# Generate wikilink network graph
python scripts/build_network.py

# Generate static search website
python scripts/build_site.py
```

---

## Report Format

Every report follows this structure:

```markdown
# 2330 - [[台積電]]

## 業務簡介
**板塊:** Technology
**產業:** Semiconductors
**市值:** 47,845,508 百萬台幣
**企業價值:** 45,886,629 百萬台幣

[Traditional Chinese description with [[wikilinks]]...]

## 供應鏈位置
**上游 (設備/原料):**
- **設備:** [[ASML]] (EUV), [[Applied Materials]], [[Lam Research]]
- **材料:** [[環球晶]], [[Shin-Etsu]], [[SUMCO]]

**下游應用:**
- **HPC:** [[NVIDIA]] AI GPU, [[AMD]] CPU
- **手機:** [[Apple]] (iPhone A系列), [[Qualcomm]]

## 主要客戶及供應商
### 主要客戶
- [[Apple]], [[NVIDIA]], [[AMD]], [[Qualcomm]], [[Broadcom]]

### 主要供應商
- [[ASML]], [[Tokyo Electron]], [[Applied Materials]]

## 財務概況
### 估值指標
| P/E (TTM) | Forward P/E | P/S (TTM) | P/B | EV/EBITDA |
|-----------|-------------|-----------|-----|-----------|
|     27.32 |       16.73 |     12.56 |8.83 |     17.55 |

### 年度/季度財務數據
[3-year annual + 4-quarter data, 14 metrics each]
```

---

## Token Usage & Cost Guide

### Free — Python Scripts (No Tokens)

Run 100% locally with Python + yfinance. No AI, no API cost.

| Script | Purpose |
|---|---|
| `update_financials.py` | Refresh financial tables from yfinance |
| `update_valuation.py` | Refresh P/E, P/B, EV/EBITDA only (fast) |
| `update_enrichment.py` | Apply pre-prepared enrichment JSON |
| `audit_batch.py` | Quality validation |
| `discover.py` | Keyword scan across all reports |
| `build_themes.py` | Thematic screens + interactive screener |
| `build_network.py` | Network graph |
| `build_site.py` | Static search website |
| `build_wikilink_index.py` | Rebuild WIKILINKS.md |
| `build_discovery_index.py` | Rebuild discoveries/INDEX.md |
| `setup_obsidian.py` | Configure Obsidian vault |
| `tw.py` | Interactive menu wrapper for all above |

### Consumes Tokens — Claude Code Skills

| Slash Command | Token Usage | What it does |
|---|---|---|
| `/add-ticker 2330 台積電` | Medium | Generate .md + fetch financials + **AI researches** business desc, supply chain, customers |
| `/update-enrichment 2330` | Medium | **AI re-researches** and rewrites business content (preserves financials) |
| `/discover 液冷散熱` | Low–High | Scans database (free) → if no results, **AI searches web** and enriches reports |

**Rule of thumb:** bulk updates → Python scripts. New tickers or content refresh → slash commands.

---

## Wikilink Graph

Full index: **[WIKILINKS.md](WIKILINKS.md)**

**4,900+ unique wikilinks** across three categories:

| Category | Form | Examples |
|---|---|---|
| Taiwan companies | Chinese | `[[台積電]]`, `[[鴻海]]`, `[[聯發科]]` |
| Foreign companies | English | `[[NVIDIA]]`, `[[Apple]]`, `[[ASML]]` |
| Technologies & products | Acronym/Chinese | `[[CoWoS]]`, `[[HBM]]`, `[[矽光子]]`, `[[EUV]]` |
| Materials & substrates | Chinese | `[[光阻液]]`, `[[碳化矽]]`, `[[ABF 載板]]` |

**Top referenced entities:**

| Entity | Mentions | Signal |
|---|---|---|
| `[[台積電]]` | 469 | Foundry at the center of Taiwan's tech ecosystem |
| `[[PCB]]` | 263 | Printed circuit board supply chain depth |
| `[[NVIDIA]]` | 277 | AI supply chain mapping |
| `[[5G]]` | 232 | 5G infrastructure companies |
| `[[AI 伺服器]]` | 237 | AI server component suppliers |
| `[[電動車]]` | 223 | EV part suppliers |
| `[[Apple]]` | 207 | Apple's Taiwanese supplier network |

---

## Project Structure

```
My-TW-Coverage/
├── tw.py                          # Unified interactive CLI entry point
├── CLAUDE.md                      # Quality rules (ground truth for all contributors)
├── WIKILINKS.md                   # Wikilink index (auto-generated)
├── task.md                        # Batch definitions & progress tracking
├── todo.md                        # UX improvement roadmap
├── requirements.txt               # Python dependencies
│
├── scripts/
│   ├── utils.py                   # Shared: file discovery, wikilink normalization, categories
│   ├── add_ticker.py              # Generate new report with financials
│   ├── update_financials.py       # Refresh 3yr annual + 4Q financial tables
│   ├── update_valuation.py        # Refresh valuation multiples only (fast)
│   ├── update_enrichment.py       # Apply enrichment JSON to reports
│   ├── audit_batch.py             # Quality audit (8 validation rules)
│   ├── discover.py                # Buzzword → related companies (saves to discoveries/)
│   ├── build_discovery_index.py   # Rebuild discoveries/INDEX.md
│   ├── build_wikilink_index.py    # Rebuild WIKILINKS.md
│   ├── build_themes.py            # Thematic screens + data.json + themes/index.html
│   ├── build_network.py           # D3.js network graph (enhanced: hover, path, filter)
│   ├── build_site.py              # Static search website (Fuse.js, GitHub Pages)
│   ├── setup_obsidian.py          # Configure Obsidian vault with sector color groups
│   └── generators/                # Historical base report generators
│
├── Pilot_Reports/                 # 1,735 ticker reports
│   ├── Semiconductors/            # 155 tickers
│   ├── Electronic Components/     # 267 tickers
│   └── ... (99 sector folders)
│
├── network/
│   ├── index.html                 # Enhanced D3.js graph (hover panel, path finder, filters)
│   └── graph_data.json            # Node/edge data with company metadata
│
├── themes/
│   ├── README.md                  # Theme index (auto-generated)
│   ├── index.html                 # Interactive Thematic Screener (comparison, CSV export)
│   ├── data.json                  # Screener data with financials (auto-generated)
│   ├── CoWoS.md                   # CoWoS supply chain (39 companies)
│   └── ... (21 themes)
│
├── discoveries/                   # Auto-saved discover.py results
│   └── INDEX.md                   # Discovery index (run build_discovery_index.py)
│
├── docs/
│   └── obsidian-guide.md          # Obsidian setup & usage guide
│
├── .obsidian/
│   ├── app.json                   # Vault settings (wikilink format preserved)
│   └── graph.json                 # Graph View: sector color groups (run setup_obsidian.py)
│
├── .github/
│   └── workflows/
│       └── build-site.yml         # Auto-deploy static site to GitHub Pages on push
│
└── site/                          # Generated static website (gitignored, built by CI)
    ├── index.html                 # Homepage with Fuse.js search
    ├── reports/{ticker}.html      # Individual company pages
    └── sector/{sector}.html       # Sector listing pages
```

---

## Quality Standards

Every report validates against 8 rules (full specification in `CLAUDE.md`):

1. **Wikilinks are specific proper nouns** — no generic terms like 供應商 or 大廠
2. **Ticker-company identity verified** — filename is ground truth, never assumed
3. **Minimum 8 wikilinks per report**
4. **Financial tables untouched** — `## 財務概況` never modified during enrichment
5. **All content in Traditional Chinese** — no English prose
6. **No placeholders** in completed reports
7. **Complete metadata** — 板塊, 產業, 市值, 企業價值 all populated
8. **Segmented supply chain** — upstream/midstream/downstream, broken out by category

Current audit: **1,733/1,733 (100%)** pass all checks.

---

## Data Sources

- **Financial data**: [yfinance](https://github.com/ranaroussi/yfinance) (Yahoo Finance Taiwan)
- **Business content**: MOPS filings (公開資訊觀測站), investor conference transcripts (法說會), annual reports (年報), company IR pages
- **Supply chain data**: Industry reports, news, company disclosures

## Limitations

- Financial data depends on yfinance — some OTC stocks may have gaps
- Business descriptions reflect enrichment date — they don't auto-update
- New technologies or companies need manual wikilink addition
- Content is Traditional Chinese — English readers will need translation

## License

MIT. See [LICENSE](LICENSE).

Financial data sourced from Yahoo Finance via yfinance. Business descriptions are original research.

## Attribution

This repository is forked from [Timeverse/My-TW-Coverage](https://github.com/Timeverse/My-TW-Coverage). Original work by Timeverse, used and modified under the MIT License.

### Enhancements Over Original

The following features were added in this fork:

#### New Tools & Interfaces
- **`tw.py` — Interactive CLI**: Unified entry point with an interactive menu covering all operations; no need to remember script names or arguments.
- **Static Search Website** (`scripts/build_site.py`): Fuse.js full-text search, sector filter, wikilink filter, valuation sort, individual report pages, and auto-deploy to GitHub Pages via CI.
- **Thematic Screener** (`scripts/build_themes.py`): 21 curated supply chain themes with interactive HTML screener — side-by-side company comparison (up to 5), CSV export, and role badges (上游/中游/下游).
- **Wikilink Network Graph** (`scripts/build_network.py`): D3.js force-directed graph with hover preview, sector filter, category type filter, and shortest-path finder between any two companies.
- **Obsidian Integration** (`scripts/setup_obsidian.py`): One-command vault setup with sector color groups for Graph View.
- **`/discover` skill**: Reverse search — enter a buzzword (e.g. 液冷散熱) to find related companies across all reports; falls back to web research and auto-enriches reports if no local results found.

#### Data Enhancements
- **Valuation multiples** added to all 1,735 tickers: P/E (TTM), Forward P/E, P/S, P/B, EV/EBITDA with period dates.
- **`update_valuation.py`**: Fast valuation-only refresh (~3× faster than full financials update).
- **WIKILINKS.md**: Auto-generated index of 4,900+ unique wikilinks, categorized by Taiwan companies, foreign companies, technologies, and materials.
- **Wikilink standardization**: Merged 313 English aliases to canonical Chinese forms; added 768 missing wikilinks across 298 files; normalized write pipeline to prevent future duplicates.

#### Quality & Reliability
- Achieved **1,733/1,733 (100%) audit pass** across all 8 quality rules.
- Fixed NaN values in financial tables across 778 files.
- Fixed financial table formatting (column order, alignment, separator widths).
- Fixed CAPEX and G&A derivation when Yahoo Finance fields are missing.
- Shared utility consolidation (`scripts/utils.py`) — eliminated duplicate file reads and logic across scripts.
- GitHub Actions CI (`build-site.yml`) for automatic static site deployment on push.
