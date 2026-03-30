# 台灣股票研究資料庫

涵蓋 **1,735 家台灣上市櫃公司**（上市 TWSE + 上櫃 OTC）、橫跨 **99 個產業**的結構化股票研究資料庫。每份報告記錄企業概況、供應鏈位置與主要客戶供應商關係，並透過 **4,900+ 個 Wikilink** 構成可搜尋的知識圖譜。

**Wikilink 圖譜是本資料庫的核心功能。** 搜尋 `[[Apple]]` 可找到 207 家台灣蘋果供應鏈廠商；搜尋 `[[CoWoS]]` 可列出所有參與台積電先進封裝的公司；搜尋 `[[光阻液]]` 則可完整呈現光阻液的上下游廠商分布。

**線上網站：** https://alingowangxr.github.io/My-TW-Coverage/

---

## 快速開始

```bash
pip install yfinance pandas tabulate InquirerPy rich markdown
python tw.py          # 互動式選單 — 所有功能一站入口
```

---

## 操作介面

### `tw.py` — 互動式 CLI（推薦）

所有功能的統一入口，無需記憶腳本名稱或參數。

```bash
python tw.py                         # 啟動互動式選單
python tw.py discover 液冷散熱        # 直接 CLI 模式
python tw.py financials 2330         # 直接 CLI 模式
python tw.py lookup 台積電            # 模糊搜尋公司
python tw.py --help                  # 完整指令說明
```

**互動式選單：**
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

所有操作紀錄儲存於 `logs/tw_operations.log`。

---

### 靜態搜尋網站

涵蓋全部 1,735 份報告的全文搜尋網站，純靜態 HTML，無需後端。

```bash
python scripts/build_site.py                  # 完整建置（約 5 分鐘）
python scripts/build_site.py --no-reports     # 僅索引 + 產業頁（快速預覽）
python -m http.server 8080 --directory site/
# 開啟 http://localhost:8080/
```

**功能特色：**
- **Fuse.js 搜尋** — 依公司名稱、股票代號、技術名稱或材料名稱搜尋
- **產業篩選** — 篩選 99 個產業中的任一類別
- **Wikilink 篩選** — 點擊任一頁面的 `[[CoWoS]]` → 列出所有 CoWoS 相關公司
- **排序** — 依市值、P/E、P/B 或 EV/EBITDA 排序
- **個別報告頁面** — Markdown 轉 HTML，含可點擊 Wikilink、側欄估值指標與相關公司
- **URL 參數支援**：`?q=台積電`、`?s=Semiconductors`、`?wl=CoWoS`

**GitHub Pages：** 推送至 master 分支 → 透過 GitHub Actions 自動部署（詳見 `.github/workflows/build-site.yml`）。

---

### 主題篩選器（`themes/index.html`）

21 個精選供應鏈主題的互動式篩選工具。

```bash
python scripts/build_themes.py   # 重新產生 themes/index.html + themes/data.json
# 然後用瀏覽器開啟 themes/index.html
```

**功能特色：**
- 左側側欄：21 個主題依類別分組（先進封裝、光子、電動車、AI、材料等）
- 公司卡片附上游／中游／下游角色標籤
- 依市值、P/E、P/B、EV/EBITDA 排序
- 供應鏈角色篩選（上游／中游／下游）
- **最多 5 家公司並排比較**（最佳／最差高亮標示）
- **CSV 匯出**比較資料
- 從 `discoveries/INDEX.md` 自動新增 AI 探索主題

---

### Wikilink 網路圖（`network/index.html`）

以 D3.js 力導向演算法繪製的互動式 Wikilink 共現圖。

```bash
python scripts/build_network.py                  # 預設：最少 5 次共現
python scripts/build_network.py --min-weight 10  # 較少但更強的連結
python scripts/build_network.py --top 200        # 僅顯示前 200 個節點
# 開啟 network/index.html
```

**功能特色：**
- 懸停預覽面板 — 顯示公司資訊、估值指標、前 5 大關聯
- **產業篩選**下拉選單 — 聚焦 99 個產業中的任一類別
- **節點類型**核取方塊 — 顯示／隱藏台灣公司、國際公司、技術、材料、應用
- **最短路徑搜尋** — 輸入兩個節點名稱 → 標示供應鏈路徑
- 點擊台灣公司節點 → 開啟完整報告（需在 HTML 中設定 `GITHUB_REPO`）
- 節點大小 ∝ 被提及次數；邊的粗細 ∝ 共現頻率

---

### Obsidian Vault

`[[wikilink]]` 格式與 Obsidian 原生相容，一行指令完成設定：

```bash
python scripts/setup_obsidian.py
# 然後：obsidian://open?vault=My-TW-Coverage
```

**立即可用的功能：**
- **圖譜檢視**（`Ctrl+G`）— 1,735 個節點，依產業類別色彩標示
- **快速切換**（`Ctrl+O`）— 依股票代號或公司名稱跳轉
- **反向連結面板** — 開啟台積電.md → 查看 469 家有引用的公司
- **全文搜尋**（`Ctrl+Shift+F`）— 跨所有報告搜尋

推薦外掛請參考 `docs/obsidian-guide.md`（Dataview、Excalidraw）。

---

## Python 腳本參考

所有腳本支援相同的**範圍語法**：

| 範圍 | 範例 |
|---|---|
| 單一代號 | `2330` |
| 多個代號 | `2330 2317 3034` |
| 依批次 | `--batch 101` |
| 依產業 | `--sector Semiconductors` |
| 全部代號 | *（不帶參數）* |

### 核心腳本

```bash
# 新增公司報告
python scripts/add_ticker.py 2330 台積電

# 更新財務表格（3 年年報 + 4 季季報）
python scripts/update_financials.py [範圍]

# 僅更新估值倍數 — P/E、P/B、EV/EBITDA（約快 3 倍）
python scripts/update_valuation.py [範圍]

# 套用 JSON 增豐內容
python scripts/update_enrichment.py --data enrichment.json [範圍]

# 品質稽核（8 項驗證規則）
python scripts/audit_batch.py [範圍] -v
python scripts/audit_batch.py --all -v

# 重建 WIKILINKS.md 交叉索引
python scripts/build_wikilink_index.py
```

### 探索與分析

```bash
# 依關鍵詞找相關公司
python scripts/discover.py "液冷散熱"                    # 全產業
python scripts/discover.py "液冷散熱" --smart            # 自動篩選產業
python scripts/discover.py "液冷散熱" --apply            # 在報告中標記 [[wikilink]]
python scripts/discover.py "液冷散熱" --apply --rebuild  # 並重建主題圖與網路圖

# 結果自動儲存至 discoveries/YYYY-MM-DD_{keyword}.md
# 建立探索索引
python scripts/build_discovery_index.py   # 重新產生 discoveries/INDEX.md

# 產生主題投資篩選
python scripts/build_themes.py             # 全部 21 個主題 + index.html + data.json
python scripts/build_themes.py "CoWoS"    # 單一主題
python scripts/build_themes.py --list     # 列出所有主題

# 產生 Wikilink 網路圖
python scripts/build_network.py

# 產生靜態搜尋網站
python scripts/build_site.py
```

---

## 報告格式

每份報告遵循以下結構：

```markdown
# 2330 - [[台積電]]

## 業務簡介
**板塊:** Technology
**產業:** Semiconductors
**市值:** 47,845,508 百萬台幣
**企業價值:** 45,886,629 百萬台幣

[繁體中文業務描述，含 [[wikilink]]...]

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
[3 年年報 + 4 季季報，各 14 項指標]
```

---

## Token 用量與費用說明

### 免費 — Python 腳本（不消耗 Token）

完全在本機以 Python + yfinance 執行，無需 AI，無 API 費用。

| 腳本 | 功能 |
|---|---|
| `update_financials.py` | 從 yfinance 更新財務表格 |
| `update_valuation.py` | 僅更新 P/E、P/B、EV/EBITDA（快速） |
| `update_enrichment.py` | 套用預先準備的增豐 JSON |
| `audit_batch.py` | 品質驗證 |
| `discover.py` | 跨報告關鍵詞掃描 |
| `build_themes.py` | 主題篩選 + 互動式篩選器 |
| `build_network.py` | 網路圖 |
| `build_site.py` | 靜態搜尋網站 |
| `build_wikilink_index.py` | 重建 WIKILINKS.md |
| `build_discovery_index.py` | 重建 discoveries/INDEX.md |
| `setup_obsidian.py` | 設定 Obsidian Vault |
| `tw.py` | 以上所有功能的互動選單入口 |

### 消耗 Token — Claude Code Skill 指令

| 斜線指令 | Token 用量 | 功能說明 |
|---|---|---|
| `/add-ticker 2330 台積電` | 中等 | 產生 .md + 抓取財務 + **AI 研究**業務描述、供應鏈、客戶 |
| `/update-enrichment 2330` | 中等 | **AI 重新研究**並改寫業務內容（保留財務數據） |
| `/discover 液冷散熱` | 低～高 | 掃描資料庫（免費）→ 無結果時 **AI 搜尋網路**並增豐報告 |

**使用原則：** 大量更新 → Python 腳本；新增代號或更新內容 → 斜線指令。

---

## Wikilink 圖譜

完整索引：**[WIKILINKS.md](WIKILINKS.md)**

**4,900+ 個唯一 Wikilink**，分為四大類：

| 類別 | 形式 | 範例 |
|---|---|---|
| 台灣公司 | 中文 | `[[台積電]]`、`[[鴻海]]`、`[[聯發科]]` |
| 外國公司 | 英文 | `[[NVIDIA]]`、`[[Apple]]`、`[[ASML]]` |
| 技術與產品 | 縮寫／中文 | `[[CoWoS]]`、`[[HBM]]`、`[[矽光子]]`、`[[EUV]]` |
| 材料與基板 | 中文 | `[[光阻液]]`、`[[碳化矽]]`、`[[ABF 載板]]` |

**被引用最多的實體：**

| 實體 | 提及次數 | 意義 |
|---|---|---|
| `[[台積電]]` | 469 | 台灣科技生態系中心晶圓廠 |
| `[[PCB]]` | 263 | 印刷電路板供應鏈深度 |
| `[[NVIDIA]]` | 277 | AI 供應鏈分布 |
| `[[5G]]` | 232 | 5G 基礎建設相關公司 |
| `[[AI 伺服器]]` | 237 | AI 伺服器零組件供應商 |
| `[[電動車]]` | 223 | 電動車零件供應商 |
| `[[Apple]]` | 207 | 蘋果台灣供應商網絡 |

---

## 專案結構

```
My-TW-Coverage/
├── tw.py                          # 統一互動式 CLI 入口
├── CLAUDE.md                      # 品質規範（所有貢獻者的基準）
├── WIKILINKS.md                   # Wikilink 索引（自動產生）
├── task.md                        # 批次定義與進度追蹤
├── requirements.txt               # Python 相依套件
│
├── scripts/
│   ├── utils.py                   # 共用：檔案探索、wikilink 正規化、類別
│   ├── add_ticker.py              # 產生新報告含財務數據
│   ├── update_financials.py       # 更新 3 年年報 + 4 季季報
│   ├── update_valuation.py        # 僅更新估值倍數（快速）
│   ├── update_enrichment.py       # 套用增豐 JSON 至報告
│   ├── audit_batch.py             # 品質稽核（8 項驗證規則）
│   ├── discover.py                # 關鍵詞 → 相關公司（儲存至 discoveries/）
│   ├── build_discovery_index.py   # 重建 discoveries/INDEX.md
│   ├── build_wikilink_index.py    # 重建 WIKILINKS.md
│   ├── build_themes.py            # 主題篩選 + data.json + themes/index.html
│   ├── build_network.py           # D3.js 網路圖（懸停、路徑、篩選）
│   ├── build_site.py              # 靜態搜尋網站（Fuse.js、GitHub Pages）
│   ├── setup_obsidian.py          # 設定 Obsidian Vault 含產業色彩群組
│   └── generators/                # 歷史基礎報告產生器
│
├── Pilot_Reports/                 # 1,735 份代號報告
│   ├── Semiconductors/            # 155 個代號
│   ├── Electronic Components/     # 267 個代號
│   └── ... （99 個產業資料夾）
│
├── network/
│   ├── index.html                 # 強化版 D3.js 圖（懸停面板、路徑搜尋、篩選）
│   └── graph_data.json            # 含公司 metadata 的節點／邊資料
│
├── themes/
│   ├── README.md                  # 主題索引（自動產生）
│   ├── index.html                 # 互動式主題篩選器（比較、CSV 匯出）
│   ├── data.json                  # 含財務數據的篩選器資料（自動產生）
│   ├── CoWoS.md                   # CoWoS 供應鏈（39 家公司）
│   └── ... （21 個主題）
│
├── discoveries/                   # discover.py 自動儲存結果
│   └── INDEX.md                   # 探索索引（執行 build_discovery_index.py）
│
├── docs/
│   └── obsidian-guide.md          # Obsidian 設定與使用說明
│
├── .obsidian/
│   ├── app.json                   # Vault 設定（保留 wikilink 格式）
│   └── graph.json                 # 圖譜檢視：產業色彩群組
│
├── .github/
│   └── workflows/
│       └── build-site.yml         # 推送後自動部署靜態網站至 GitHub Pages
│
└── site/                          # 產生的靜態網站（gitignored，由 CI 建置）
    ├── index.html                 # 首頁含 Fuse.js 搜尋
    ├── reports/{ticker}.html      # 個別公司頁面
    └── sector/{sector}.html       # 產業列表頁面
```

---

## 品質標準

每份報告依 8 項規則進行驗證（完整規範詳見 `CLAUDE.md`）：

1. **Wikilink 必須是具體專有名詞** — 不得使用「供應商」、「大廠」等通稱
2. **代號與公司名稱必須核實** — 檔名為基準，不得假設
3. **每份報告至少 8 個 Wikilink**
4. **財務表格不得異動** — 增豐過程中不修改 `## 財務概況`
5. **全部內容以繁體中文撰寫** — 不得出現英文段落
6. **完成報告不得有佔位符**
7. **Metadata 必須完整** — 板塊、產業、市值、企業價值均需填寫
8. **供應鏈必須分層** — 上游／中游／下游，依類別細分

目前稽核結果：**1,733/1,733（100%）** 全數通過。

---

## 資料來源

- **財務數據**：[yfinance](https://github.com/ranaroussi/yfinance)（Yahoo Finance 台灣）
- **業務內容**：公開資訊觀測站（MOPS）申報、法說會逐字稿、年報、公司 IR 頁面
- **供應鏈資料**：產業報告、新聞、公司公開揭露

## 限制說明

- 財務數據依賴 yfinance，部分上櫃股票可能有資料缺口
- 業務描述反映增豐當下的資訊，不會自動更新
- 新興技術或公司需手動新增 Wikilink
- 內容為繁體中文，英文讀者需自行翻譯

## 授權

MIT 授權。詳見 [LICENSE](LICENSE)。

財務數據來源為 Yahoo Finance（透過 yfinance）。業務描述為原創研究成果。

## 致謝

本專案 fork 自 [Timeverse/My-TW-Coverage](https://github.com/Timeverse/My-TW-Coverage)，原始作品由 Timeverse 創作，依 MIT 授權使用與修改。

### 相較原作的強化內容

本 fork 新增了以下功能：

#### 新工具與操作介面
- **`tw.py` — 互動式 CLI**：涵蓋所有操作的統一入口，附互動選單，無需記憶腳本名稱或參數。
- **靜態搜尋網站**（`scripts/build_site.py`）：Fuse.js 全文搜尋、產業篩選、Wikilink 篩選、估值排序、個別報告頁面，並透過 CI 自動部署至 GitHub Pages。
- **主題篩選器**（`scripts/build_themes.py`）：21 個精選供應鏈主題，互動式 HTML 篩選器，支援最多 5 家公司並排比較、CSV 匯出與角色標籤（上游／中游／下游）。
- **Wikilink 網路圖**（`scripts/build_network.py`）：D3.js 力導向圖，含懸停預覽、產業篩選、節點類型篩選與任兩節點間最短路徑搜尋。
- **Obsidian 整合**（`scripts/setup_obsidian.py`）：一行指令完成 Vault 設定，含圖譜檢視產業色彩群組。
- **`/discover` skill**：反向搜尋 — 輸入關鍵詞（如「液冷散熱」）即可找到相關公司；若本地無結果，自動進行網路研究並增豐報告。

#### 資料強化
- **估值倍數**全面新增至 1,735 個代號：P/E (TTM)、Forward P/E、P/S、P/B、EV/EBITDA，含期間日期。
- **`update_valuation.py`**：快速僅更新估值倍數（比完整財務更新快約 3 倍）。
- **WIKILINKS.md**：自動產生的 4,900+ 個唯一 Wikilink 索引，依台灣公司、外國公司、技術與材料分類。
- **Wikilink 標準化**：合併 313 個英文別名為中文正式名稱；跨 298 個檔案補充 768 個缺失 Wikilink；正規化寫入流程以防止未來重複。

#### 品質與可靠性
- 達成 **1,733/1,733（100%）稽核全數通過**，涵蓋全部 8 項品質規則。
- 修復 778 個財務表格中的 NaN 值。
- 修復財務表格格式問題（欄位順序、對齊、分隔線寬度）。
- 修復 Yahoo Finance 缺少欄位時的 CAPEX 與 G&A 推算邏輯。
- 共用工具整合（`scripts/utils.py`）— 消除各腳本間重複的檔案讀取與邏輯。
- GitHub Actions CI（`build-site.yml`）— 推送後自動部署靜態網站。
