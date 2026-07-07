# sourcing/radar — 台灣選品雷達（輕量版）

參考 `20260509__tool__amazon-store-health-dashboard/04_选品雷达` 的 big-pool 累積邏輯，
為 BuzzBuzz（單人、預購制、零庫存 dropshipping）大幅簡化：只做「發現」與「驗證」兩層，
不做 Amazon 版的 watchlist/radar/selection 三層治理與 launchd 排程。

## 為什麼拆成兩層

- **只搜品牌名會有偏差**：如果搜尋詞都來自 `top100.yaml`，只會不斷確認已經相信的東西，
  發現不了清單外的新機會，而且 top100.yaml 本身是單一 PDF 來源，權威性未經驗證。
- **所以先發現，後驗證，兩件事不能合併**：發現階段用「場景詞/意圖詞」搜（不含品牌名），
  品牌名從搜尋結果的文章內容裡提取；驗證階段對每個候選品牌做多方交叉確認，
  不管它是不是本來就在 top100.yaml 裡。

## 檔案

| 檔案 | 用途 |
|---|---|
| `discovery-terms.json` | 場景/意圖詞 × 台灣平台 site: 搜尋語法輪替清單，`rotation_index` 記錄跑到哪 |
| `pool.jsonl` | 累積型原始線索池，只增不減。每次執行前讀取既有 `brand+product` 組合去重，只寫入沒見過的 |
| `validation-signals.md` | 4 個獨立驗證信號族（Google Trends TW / 台灣社群討論 / 第三方清單交叉比對 / 蝦皮樂天市場證據）與 2-of-4 收斂規則 |
| `candidates.md` | 通過驗證（命中 ≥2 信號族）的候選清單，供人工決定是否進 `products/` 開始上稿 |

## 執行方式

不用背景排程，人工觸發：跟 Claude 說「跑一次選品雷達」，Claude 用 WebSearch 工具依
`discovery-terms.json` 的 rotation 跑一批搜尋，把新發現（去重後）寫進 `pool.jsonl`，
`rotation_index` 往後移。累積到一定量後，挑有興趣的候選丟進 `validation-signals.md`
的流程做多方驗證，通過的記錄進 `candidates.md`。

## 與 top100.yaml 的關係

`top100.yaml` 不再被當作真理，只是候選來源之一（`sourcing.source: top100`）。
不管品牌是從 top100 來的還是 discovery 自然發現的，都要走同一套驗證流程才能進
`candidates.md`。

top100.yaml 剩餘品牌的系統性驗證（不透過 discovery，直接拿品牌名去查 2-of-4 信號）
是獨立的另一條流程，見 `tasks/top100-validation-sweep-plan.md`——刻意跟這裡的
discovery 流程分開規劃，避免「發現層」和「驗證層」的搜尋詞和判斷邏輯混在一起。
