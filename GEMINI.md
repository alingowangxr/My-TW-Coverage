# Taiwan Stock Coverage Database - Project Context

## Project Overview
A structured equity research database covering **1,735 Taiwan-listed companies** (TWSE + OTC) across 99 industry sectors. The core mechanism is a **wikilink graph** (`[[...]]`) that maps relationships between companies, technologies, and materials, creating a searchable supply chain knowledge base.

- **Primary Stack:** Python (yfinance, pandas, tabulate), Markdown.
- **Key Feature:** 4,900+ unique wikilinks identifying specific proper nouns (e.g., `[[CoWoS]]`, `[[NVIDIA]]`, `[[光阻液]]`).

## Architecture & Structure

### Data Repository
- `Pilot_Reports/`: 1,735 reports organized by 99 industry folders.
  - Filename Pattern: `XXXX_公司名.md` (e.g., `2330_台積電.md`).
- `themes/`: Auto-generated thematic supply chain screens (e.g., `AI_伺服器.md`).
- `network/`: Interactive D3.js visualization of the wikilink graph.
- `WIKILINKS.md`: Master index of all entities in the graph.

### Tooling (scripts/)
- `add_ticker.py`: Generates base reports with financial data.
- `update_financials.py`: Refreshes 3-year annual and 4-quarter financial tables via yfinance.
- `update_valuation.py`: High-speed refresh for P/E, P/B, and price data only.
- `update_enrichment.py`: Applies researched business content (desc, supply chain, customers).
- `audit_batch.py`: Validates reports against quality rules.
- `discover.py`: Buzzword search across the entire database.
- `build_themes.py` & `build_network.py`: Generates downstream visual/thematic assets.

## Core Workflows

### 1. Research & Enrichment
- **Manual/Scripted:** Prepare JSON enrichment data and use `scripts/update_enrichment.py`.
- **AI-Powered:** Use Claude Code skills (e.g., `/add-ticker`, `/update-enrichment`) to perform web research and generate Traditional Chinese content.

### 2. Data Maintenance
- **Financial Updates:** Run `python scripts/update_financials.py` periodically to keep tables current.
- **Index Rebuild:** After content changes, run `python scripts/build_wikilink_index.py`.

### 3. Quality Validation
- **Audit Rule:** Every report must pass `python scripts/audit_batch.py`.
- **Golden Rules:**
  - Wikilinks MUST be specific proper nouns (no generic terms like `[[供應商]]`).
  - Filenames are the ground truth for ticker-company mapping.
  - Minimum 8 wikilinks per report.
  - Financial tables are sacred (never manually edit).

## Development Conventions

- **Language:** All business content must be in **Traditional Chinese**.
- **Metadata:** Reports must contain complete metadata blocks (Sector, Industry, Market Cap, EV).
- **Supply Chain:** Must be segmented into Upstream/Midstream/Downstream with specific company mappings.
- **Units:** Monetary values in **百萬台幣** (Million NTD).

## Key Files for Reference
- `CLAUDE.md`: Detailed quality standards and "Golden Rules".
- `README.md`: High-level project documentation and quick start.
- `task.md`: Progress tracking and batch definitions.
- `requirements.txt`: Python dependency list.
