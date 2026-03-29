# Obsidian 使用指南

> 本 repo 的 1,735 份報告使用 `[[wikilink]]` 格式，與 Obsidian 天然相容。
> 執行一次設定腳本即可開始使用圖形視圖、跨文件搜尋與反向連結。

---

## 快速開始（3 步驟）

### 步驟 1：安裝 Obsidian
前往 [obsidian.md](https://obsidian.md) 下載並安裝（免費）。

### 步驟 2：執行設定腳本
```bash
python scripts/setup_obsidian.py
```
這會建立 `.obsidian/graph.json`（依產業分色），並更新 `.gitignore`。

### 步驟 3：開啟 Vault
- 在 Obsidian 中選擇「Open folder as vault」
- 指向此 repo 的根目錄：`My-TW-Coverage/`
- 或直接執行：`obsidian://open?vault=My-TW-Coverage`

---

## 主要功能

### Graph View（圖形視圖）
**快捷鍵：** `Ctrl+G`（Windows）/ `Cmd+G`（Mac）

圖形視圖將所有 `[[wikilink]]` 渲染為節點連結圖。顏色代表產業分類：
| 顏色 | 分類 |
|---|---|
| 藍色 | 科技半導體 |
| 綠色 | 金融保險 |
| 橘色 | 工業製造 |
| 深橘 | 材料化工 |
| 青色 | 醫療生技 |
| 紫色 | 能源電力 |
| 紅色 | 消費零售 |

**使用技巧：**
- 搜尋框輸入 `CoWoS` → 高亮所有相關公司節點
- 搜尋框輸入 `[[台積電]]` → 查看 TSMC 的所有供應鏈連結
- 滾輪縮放，拖曳平移

### Quick Switcher（快速切換）
**快捷鍵：** `Ctrl+O`

直接搜尋公司名稱或 ticker 代號跳到報告：
- 輸入 `2330` → 開啟台積電報告
- 輸入 `聯發科` → 開啟聯發科報告
- 輸入 `CoWoS` → 跳到任何包含此 wikilink 的文件

### Backlinks Panel（反向連結）
**快捷鍵：** `Ctrl+Shift+B`

開啟任一公司報告後，右側 Backlinks panel 會顯示**所有引用該公司的其他報告**。

**例：** 開啟 `台積電` 報告 → Backlinks 顯示 500+ 家公司（所有台積電供應商/客戶）

### Search（全文搜尋）
**快捷鍵：** `Ctrl+Shift+F`

搜尋任意關鍵字，結果顯示所有包含該詞的報告：
- `液冷散熱` → 所有散熱相關公司
- `Apple` → 所有蘋果供應鏈公司
- `磷化銦` → 所有 InP 相關公司

---

## 推薦社群插件

在 Obsidian 設定 → Community Plugins 中搜尋安裝：

### Dataview（財務篩選）
允許用 SQL-like 語法跨文件查詢，例如：
```dataview
TABLE 市值, 產業
FROM "Pilot_Reports/Semiconductors"
SORT 市值 DESC
```

### Excalidraw（手繪供應鏈圖）
在 Obsidian 中直接繪製供應鏈關係圖，支援嵌入 wikilink。

### Advanced Tables
讓財務數據表格更易閱讀與排序。

---

## 注意事項

- `.obsidian/workspace.json` 已加入 `.gitignore`，個人佈局不會影響他人
- Graph View 在 1,735 個節點下首次載入可能需要 10-30 秒，屬正常現象
- 修改任何 `.md` 報告後，Obsidian 會自動更新索引（無需重啟）
