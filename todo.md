# UX 優化 TODO

> 目標：在不破壞現有資料結構與工作流程的前提下，為 My-TW-Coverage 疊加更友善的使用介面與操作體驗。
> 執行原則：優先使用現有資料，不重複建立資料來源，零後端成本。

---

## 優先級排序總覽

| # | 項目 | 預估工作量 | 依賴 | 狀態 |
|---|---|---|---|---|
| 1 | Obsidian Vault 整合 | 0.5 天 | 無 | [x] |
| 2 | Network Graph 強化 | 1 天 | 現有 D3.js | [x] |
| 3 | CLI 互動選單 (`tw.py`) | 1 天 | InquirerPy | [x] |
| 4 | Discover 結果持久化 | 0.5 天 | 無 | [x] |
| 5 | 靜態搜尋網站 | 3-4 天 | Pagefind / GitHub Pages | [x] |
| 6 | Thematic Screener | 2 天 | 財務數據解析 | [x] |

---

## 項目 1 — Obsidian Vault 整合

> 近零工作量，立即獲得圖形視圖、跨文件搜尋、反向連結。`Pilot_Reports/` 的 `[[wikilink]]` 格式天然相容 Obsidian。

### 1.1 建立 Obsidian 設定資料夾

- [ ] 在 repo 根目錄建立 `.obsidian/` 資料夾（加入 `.gitignore` 避免個人設定污染）
- [ ] 建立 `.obsidian/app.json`，預設設定：
  - `"legacyEditor": false`
  - `"defaultViewMode": "preview"`
  - `"newLinkFormat": "shortest"` — wikilink 自動補全用最短名稱
  - `"useMarkdownLinks": false` — 維持 `[[...]]` 格式
- [ ] 建立 `.obsidian/graph.json`，預設 Graph View 設定：
  - 依 sector 資料夾分色（每個 99 個產業資料夾一個顏色群組）
  - 預設 node repel force 調高（1,735 個節點需要更大間距）
  - 過濾掉 `task.md`、`WIKILINKS.md`、`todo.md` 等非報告文件
- [ ] 建立 `.obsidian/workspace.json`，預設佈局：
  - 左側：File explorer（展開 Pilot_Reports/）
  - 右側：Backlinks panel
  - 底部：Search

### 1.2 建立設定腳本

- [ ] 新增 `scripts/setup_obsidian.py`，功能：
  - 自動寫入上述 `.obsidian/` 設定檔
  - 檢查 Obsidian 是否已安裝，若無則輸出下載連結
  - 在 `.gitignore` 追加 `.obsidian/workspace.json`（個人 workspace 不 commit）
  - 輸出「開啟方式」說明：`obsidian://open?vault=My-TW-Coverage`

### 1.3 撰寫使用說明

- [ ] 新增 `docs/obsidian-guide.md`：
  - 安裝步驟（3 步驟）
  - Graph View 使用方式：搜尋 `[[台積電]]` → 查看所有連結公司
  - Quick Switcher（Ctrl+O）：直接跳到任一 ticker
  - Backlinks panel：查看哪些公司引用了某個 wikilink
  - 推薦安裝的社群插件：Dataview（財務篩選）、Excalidraw（供應鏈手繪）

---

## 項目 2 — Network Graph 強化

> 現有 `network/index.html` 已有 D3.js force-directed graph，在此基礎上擴充，不重寫。

### 2.1 節點點擊連回報告

- [ ] 修改 `network/index.html` 的節點 click handler：
  - 若 node 類型為 Taiwan company（紅色）：點擊開啟對應 GitHub repo 的 `.md` 檔案連結
  - 連結格式：`https://github.com/{owner}/{repo}/blob/master/Pilot_Reports/{sector}/{ticker}_{name}.md`
  - 需在 `graph_data.json` 的節點資料中新增 `file_path` 欄位
- [ ] 修改 `scripts/build_network.py`，在 node 資料中加入：
  - `"file_path"`: 相對於 repo 根目錄的報告路徑
  - `"sector"`: 所屬產業資料夾名稱
  - `"ticker"`: 4 位數 ticker 代號

### 2.2 懸停預覽 Panel

- [ ] 在 `network/index.html` 右側新增一個 info panel（預設隱藏）：
  - 懸停節點時顯示：公司名、ticker、板塊、產業
  - 從 `graph_data.json` 讀取（需在 build 時帶入摘要資料）
  - 顯示「前 5 大連結節點」（依 edge weight 排序）
  - 底部「查看完整報告 →」連結
- [ ] 修改 `scripts/build_network.py`，在 node 資料中加入：
  - `"sector_en"`: 板塊（英文，來自報告 metadata）
  - `"industry_en"`: 產業（英文，來自報告 metadata）
  - `"summary"`: `業務簡介` 的前 80 個中文字（從 .md 檔案解析）

### 2.3 Sector 篩選器

- [ ] 在 `network/index.html` 工具列新增 Sector 下拉選單：
  - 選項：All + 各產業（從 node 資料動態產生）
  - 選擇後：非該 sector 節點變淡色（opacity 0.1），相關 edges 保持顯示
  - 同時更新右上角 stats（顯示「目前顯示 X / 339 個節點」）
- [ ] 新增 Type 篩選 checkbox 群組（現有 5 種顏色對應 5 種類型）：
  - [x] 台灣公司（紅）
  - [x] 國際公司（藍）
  - [x] 技術/產品（綠）
  - [x] 材料（橘）
  - [x] 應用（紫）

### 2.4 最短路徑功能

- [ ] 在搜尋區新增「路徑查詢」模式：
  - 輸入起點公司名 + 終點公司名
  - 用 BFS/Dijkstra 在 graph_data.json 上計算最短路徑
  - 高亮顯示路徑上的節點與 edges（其餘淡化）
  - 側邊 panel 顯示路徑節點清單（可點擊各節點）
- [ ] 此功能純前端實作（JS），不需後端

### 2.5 圖表效能優化

- [ ] 當前 graph 有 339 nodes / 1,452 edges，在舊電腦上可能卡頓：
  - 初始載入時 edge 只顯示 weight ≥ 2（現有 slider 預設值調整）
  - 節點數量 > 200 時自動降低 particle 效果
  - 加入 WebGL renderer 選項（使用 d3-force + canvas 替代 SVG）作為可選強化

---

## 項目 3 — CLI 互動選單 (`tw.py`)

> 一個統一入口腳本，用互動式選單包裝所有現有 scripts，降低使用者需要記憶指令的負擔。

### 3.1 安裝依賴

- [ ] 在 `requirements.txt` 新增：
  - `InquirerPy>=0.3.4` — 互動式 CLI 選單
  - `rich>=13.0.0` — 美化輸出（表格、進度條、彩色文字）

### 3.2 建立 `tw.py` 主選單

- [ ] 建立 `tw.py` 在 repo 根目錄，主選單結構：

```
My TW Coverage — 主選單
? 請選擇操作：
  > 🔍 搜尋主題 (discover)
    📊 查詢公司 (single ticker info)
    🔄 更新財務 (update_financials)
    ✏️  更新估值 (update_valuation)
    📝 新增報告 (add_ticker)
    🏭 產生主題圖 (build_themes)
    🕸️  重建網路圖 (build_network)
    🔗 重建 Wikilink 索引 (build_wikilink_index)
    ✅ 品質稽核 (audit_batch)
    ❌ 離開
```

### 3.3 各功能互動流程

**搜尋主題 (discover)：**
- [ ] 輸入關鍵字（例：液冷散熱）
- [ ] 詢問：是否啟用 AI 網路搜尋？(--smart) (Y/n)
- [ ] 詢問：是否自動寫入相關報告？(--apply) (Y/n)
- [ ] 顯示結果（rich 表格：ticker / 公司名 / 匹配片段）

**查詢公司：**
- [ ] 輸入 ticker 或公司名（模糊搜尋）
- [ ] 顯示命中清單，選擇後：
  - 顯示該公司的 metadata（板塊、產業、市值、EV）
  - 顯示業務簡介（前 200 字）
  - 詢問：開啟報告？更新財務？更新估值？

**更新財務 / 估值：**
- [ ] 詢問 scope：
  ```
  ? 更新範圍：
    > 單一 ticker（輸入代號）
      多個 ticker（空格分隔）
      整個批次（輸入 batch 編號）
      整個產業（選擇 sector）
      全部 (ALL) ⚠️ 耗時較長
  ```
- [ ] 確認後執行，顯示 rich 進度條

**品質稽核：**
- [ ] 詢問 scope（同上）
- [ ] 結果用 rich 表格顯示：通過 ✅ / 失敗 ❌ + 失敗原因

### 3.4 全域功能

- [ ] 所有操作前顯示目前 repo 狀態摘要（右上角 status bar）：
  - 總報告數、已完成批次、最後更新日期
- [ ] `--help` 顯示完整指令對照表（仍支援直接 CLI 模式，不強制互動）
- [ ] 操作歷史記錄到 `logs/tw_operations.log`（含時間戳、操作類型、scope、結果）

---

## 項目 4 — Discover 結果持久化

> 讓 `discover.py` 的搜尋結果累積成知識庫，而非每次執行完就消失。

### 4.1 Discovery 結果存檔

- [ ] 修改 `scripts/discover.py`，每次執行後自動儲存結果：
  - 路徑：`discoveries/YYYY-MM-DD_{keyword}.md`
  - 格式：
    ```markdown
    # Discovery: {keyword}
    **日期:** YYYY-MM-DD
    **搜尋模式:** smart / basic
    **命中公司數:** N

    ## 相關公司
    | Ticker | 公司名 | 匹配片段 |
    |---|---|---|
    | 6669 | 緯穎 | ...液冷散熱方案... |

    ## AI 研究摘要
    （若使用 --smart 模式則包含）

    ## 建議新增 Wikilinks
    - `[[液冷散熱]]` → 適用於以下 N 份報告
    ```
- [ ] 建立 `discoveries/` 資料夾，加入 `.gitignore`（個人研究結果不 commit）或加入 git（視使用者偏好）

### 4.2 Discovery Index

- [ ] 建立 `scripts/build_discovery_index.py`：
  - 讀取所有 `discoveries/*.md`
  - 產生 `discoveries/INDEX.md`：關鍵字 → 命中公司數 → 日期 的清單
  - 標示哪些關鍵字已被套用（--apply）、哪些尚未

### 4.3 與 Themes 整合

- [ ] 修改 `scripts/build_themes.py`：
  - 讀取 `discoveries/INDEX.md`
  - 若某關鍵字命中數 ≥ 5，自動在 `themes/` 建立對應主題頁面
  - 新主題標記為「AI 發現」（區別於手動定義的主題）

---

## 項目 5 — 靜態搜尋網站

> 將 1,735 份 markdown 報告轉為可搜尋、可瀏覽的靜態網站，部署到 GitHub Pages。零後端成本。

### 5.1 技術選型確認

- [ ] 評估並選擇搜尋方案（二選一）：
  - **方案 A：Pagefind**（推薦）— Rust-based，索引 1,735 份文件約 30 秒，bundle size ~50KB，支援中文
  - **方案 B：Fuse.js** — 純 JS，較小但搜尋品質略遜，適合輕量需求
- [ ] 評估並選擇 SSG（二選一）：
  - **方案 A：手寫 Python builder** — 最輕量，完全控制，`scripts/build_site.py`
  - **方案 B：MkDocs + Material Theme** — 功能完整，支援搜尋，但需要 pip install

### 5.2 建立 `scripts/build_site.py`

- [ ] 解析所有 `.md` 報告，提取 metadata：
  - ticker、公司名、板塊、產業、市值、企業價值
  - 業務簡介前 200 字（摘要）
  - 所有 wikilinks（`[[...]]` 提取）
- [ ] 為每份報告產生對應的 `site/{ticker}.html`：
  - 標準 HTML 模板（含 header / sidebar / content）
  - Markdown 內容轉 HTML（使用 `python-markdown` 或 `mistune`）
  - wikilink `[[X]]` 轉為站內連結 `<a href="/wikilink/X">`
- [ ] 產生索引頁 `site/index.html`：
  - 搜尋框（Pagefind 整合）
  - 全部 1,735 家公司列表（可依板塊/市值排序）
- [ ] 產生 Wikilink 頁面 `site/wikilink/{entity}.html`：
  - 顯示所有引用該 entity 的公司列表
  - 等同於現有 `WIKILINKS.md` 的互動版
- [ ] 產生 Sector 頁面 `site/sector/{sector}.html`：
  - 顯示該產業所有公司的卡片（ticker、名稱、市值、P/E）
  - 支援欄位排序

### 5.3 搜尋功能

- [ ] 整合 Pagefind：
  - `build_site.py` 執行後自動執行 `pagefind --source site/`
  - 支援搜尋：公司名（中英）、ticker、技術名稱、材料名稱
  - 搜尋結果顯示：公司名、ticker、匹配片段、板塊
- [ ] 新增進階篩選（filter sidebar）：
  - 板塊（Sector）多選
  - 產業（Industry）多選
  - 市值區間（slider）
  - 是否有特定 wikilink（例：只看有 `[[CoWoS]]` 的公司）

### 5.4 GitHub Pages 部署

- [ ] 建立 `.github/workflows/build-site.yml`：
  ```yaml
  on:
    push:
      branches: [master]
      paths:
        - 'Pilot_Reports/**'
        - 'scripts/build_site.py'
  jobs:
    build:
      - pip install requirements
      - python scripts/build_site.py
      - pagefind --source site/
      - Deploy to gh-pages branch
  ```
- [ ] 設定 GitHub Pages 從 `gh-pages` branch 的 `site/` 資料夾提供服務
- [ ] 在 README.md 加入網站連結

### 5.5 網站設計規範

- [ ] 設計系統：
  - 主色：深藍（#1a2744，台股藍）+ 紅（#c0392b，台股紅）
  - 字型：系統字型 stack（避免 CDN 依賴）
  - 響應式：mobile-first，支援手機瀏覽
- [ ] 公司卡片元件：
  - ticker badge（紅底白字）
  - 公司名（大）+ 產業（小灰字）
  - 市值 badge（灰底）
  - P/E、P/B 小標籤
  - hover 顯示業務簡介摘要
- [ ] 報告頁面樣式：
  - 固定側邊 TOC（目錄：業務簡介 / 供應鏈 / 客戶 / 財務）
  - wikilink 藍色超連結
  - 財務表格橫向捲動（mobile 友善）
  - 「相關公司」側欄（共同引用同一 wikilink 的公司）

---

## 項目 6 — Thematic Screener

> 將靜態 `themes/` markdown 升級為互動式選股工具，可排序、比較、過濾。

### 6.1 資料準備

- [ ] 修改 `scripts/build_themes.py`，同時輸出 `themes/data.json`：
  ```json
  {
    "themes": {
      "CoWoS": {
        "companies": [
          {
            "ticker": "2330",
            "name": "台積電",
            "role": "upstream",
            "market_cap": 15000000,
            "pe_ratio": 25.3,
            "pb_ratio": 6.1,
            "ev_ebitda": 18.2,
            "summary": "業務簡介前80字..."
          }
        ]
      }
    }
  }
  ```
- [ ] 解析每份報告的財務 metadata（市值、P/E、P/B、EV/EBITDA），寫入 `themes/data.json`

### 6.2 建立 `themes/index.html`

- [ ] 左側 Theme 清單（21 個主題，顯示公司數量）
- [ ] 右側公司卡片區：
  - 預設顯示所有公司
  - 點擊主題後過濾
- [ ] 工具列：
  - 排序選單：市值 / P/E / P/B / EV/EBITDA（升降序）
  - 供應鏈角色篩選：上游 / 中游 / 下游（checkbox）
  - 關鍵字搜尋（過濾公司名）

### 6.3 公司比較功能

- [ ] 每張卡片右上角「+ 加入比較」按鈕
- [ ] 底部固定比較欄（選中 2-5 家後顯示）
- [ ] 點擊「比較」按鈕開啟比較 modal：
  - 表格格式：指標（列）× 公司（欄）
  - 指標：市值、P/E、P/B、EV/EBITDA、業務摘要
  - 最低值高亮綠色、最高值高亮紅色
  - 匯出為 CSV 按鈕

### 6.4 整合進靜態網站

- [ ] `themes/index.html` 整合進項目 5 的靜態網站（`site/themes/`）
- [ ] 主頁增加「主題選股」入口卡片

---

## 通用技術規範

### 依賴管理

- [ ] 更新 `requirements.txt`，依用途分組：
  ```
  # Core (always needed)
  yfinance>=0.2.0
  pandas>=2.0.0
  tabulate>=0.9.0

  # CLI UX (項目 3)
  InquirerPy>=0.3.4
  rich>=13.0.0

  # Site Builder (項目 5)
  markdown>=3.5.0
  # pagefind: installed via npm or binary download
  ```

### 新增資料夾結構

```
My-TW-Coverage/
├── tw.py                    # 新增：CLI 互動入口 (項目 3)
├── todo.md                  # 此文件
├── discoveries/             # 新增：Discover 結果存檔 (項目 4)
│   └── INDEX.md
├── site/                    # 新增：靜態網站輸出 (項目 5，加入 .gitignore)
├── docs/                    # 新增：使用說明文件
│   └── obsidian-guide.md
├── logs/                    # 新增：操作日誌 (項目 3)
├── .obsidian/               # 新增：Obsidian 設定 (項目 1)
├── .github/workflows/       # 新增：CI/CD (項目 5)
│   └── build-site.yml
└── scripts/
    ├── setup_obsidian.py    # 新增 (項目 1)
    ├── build_site.py        # 新增 (項目 5)
    └── build_discovery_index.py  # 新增 (項目 4)
```

### .gitignore 新增項目

- [ ] `site/` — 靜態網站輸出（由 CI 產生）
- [ ] `logs/` — 操作日誌
- [ ] `.obsidian/workspace.json` — 個人 Obsidian 工作區
- [ ] `discoveries/` — 視使用者決定是否 commit

---

## 執行順序建議

```
Week 1
├── [1.1-1.3] Obsidian 整合  ── 立即有 Graph View + 搜尋
└── [2.1-2.3] Network Graph 強化  ── 節點連回報告 + Sector 篩選

Week 2
├── [3.1-3.4] tw.py CLI 互動選單  ── 日常操作介面
└── [4.1-4.3] Discover 持久化  ── 搜尋結果累積

Week 3-4
└── [5.1-5.5] 靜態搜尋網站  ── 對外分享、GitHub Pages

Week 5+
└── [6.1-6.4] Thematic Screener  ── 最高分析價值功能
```

---

## 驗收標準

每個項目完成後應滿足：

| 項目 | 驗收標準 |
|---|---|
| Obsidian 整合 | 執行 `setup_obsidian.py` 後可直接用 Obsidian 開啟 vault，Graph View 正確顯示 wikilink 連結 |
| Network Graph | 點擊節點可開啟對應報告；Sector 篩選正確過濾節點 |
| tw.py | 執行 `python tw.py` 出現選單；所有選項功能與直接執行 scripts 結果一致 |
| Discover 持久化 | 執行 discover 後在 `discoveries/` 有對應 `.md` 檔案 |
| 靜態網站 | Push 到 master 後 GitHub Actions 自動部署；Pagefind 搜尋可找到任一公司名或技術名稱 |
| Thematic Screener | 可依 P/E 排序 CoWoS 相關公司；比較功能可對比 3 家以上公司財務指標 |
