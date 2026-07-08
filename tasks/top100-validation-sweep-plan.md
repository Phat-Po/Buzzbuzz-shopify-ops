# top100.yaml 驗證專用掃描計劃

> 狀態：**批次 1-3 完成**（2026-07-08），批次 4 待操作者確認後執行
> 目的：把 `sourcing/top100.yaml` 剩下沒驗證過的品牌，逐批跑過 `validation-signals.md` 的
> 2-of-4 信號驗證，跟 discovery 層完全分開，不要混在一起。

## 這跟 discovery 層有什麼不一樣，為什麼要分開

`sourcing/radar/discovery-terms.json` 是「發現層」：用場景詞（不含品牌名）去搜，讓品牌從
台灣人自己的文字裡冒出來，目的是避免只確認已知清單、找出清單外的新機會。

這份計劃是「驗證層」的另一條路徑：直接拿 `top100.yaml` 現成的 100 個品牌名，逐一跑
2-of-4 信號驗證。這是刻意的、有目的性的搜尋，跟 discovery 的「不預設答案」邏輯不同——
**不要把兩者的搜尋詞或結果混在同一個 rotation 或同一個判斷邏輯裡**，否則會分不清一個品牌
是「台灣人自己討論出來的」還是「我們去查清單才發現的」，兩者的可信度層級不一樣。

執行方式一致（都走 `validation-signals.md` 的 A/B/C/D 四信號），結果一樣寫進
`sourcing/radar/candidates.md`，但每筆記錄的「來源」欄位要標 `top100-sweep`，跟
discovery 來源的候選分清楚。

## 目前進度

已經驗證過、不用重複跑的：

- BEAMS（no.26）— 4/4，強候選
- 吉伊卡哇 Chiikawa（no.71）— 4/4 但 D 受限，只做限定款
- Knot Watch（no.95）— 2/4，降級觀察
- **✅ 批次 1 完成（2026-07-08）：BAO BAO(1)、PLEATS PLEASE(2)、Porter(4)、Human Made(21)、WTAPS(22)、Mont-bell(41)、Snow Peak(42)、Hario(76)** — 全數 4/4 命中（Hario 3/4），詳見 `sourcing/radar/candidates.md`
- **✅ 批次 2 完成（2026-07-08）：Hender Scheme(8)、Aeta(9)、Neighborhood(23)、Needles(25)、Yamatomichi(43)、Shimano(54)、Daiwa(55)、Kalita(77)** — 僅 Neighborhood 4/4 強候選，其餘 1-3/4 多入觀察池，詳見 `sourcing/radar/candidates.md`
- **✅ 批次 3 完成（2026-07-08）：HYKE x Porter(17)、Danton(28)、Nanamica(32)、TNF Purple Label(33)、Arai(51)、Shoei(52)、Pokemon Center Japan 限定(70)、Traveler's Company(99)** — Shoei/Arai 4/4 最強；Danton/Nanamica/TNF Purple Label(A重測後3/4)/Pokemon Center 3/4 候選；HYKE/Traveler's Company 2/4 觀察池，詳見 `sourcing/radar/candidates.md`

剩下 **97 個品牌**沒有跑過任何驗證。

## 批次規則

1. **依 top100.yaml 原本的優先度分層，★★★ 先跑，★★ 次之，★ 最後**——這是清單作者原本就標記
   「高勝率」的品項，優先驗證能最快確認哪些真的靠譜。
2. **每批 8 個品牌**，跟這次 discovery 驗證的節奏一致，每批跑完給操作者看結果再決定要不要
   繼續，不要一次跑完 97 個（單次跑太多，中間發現方法論要調整時已經浪費太多次搜尋）。
3. **同一批內盡量跨品類**，避免一batch全是包袋、下一batch全是戶外，讓每次覆盤都能看到
   不同品類的訊號，比較容易發現品類層級的規律（例如這次發現「戶外/家電類很容易撞到已有代理商」）。
4. 批次順序（★★★ 共 41 個品牌，扣掉已驗證的 BEAMS/Chiikawa）：

   - **批次 1**：BAO BAO ISSEY MIYAKE(1)、PLEATS PLEASE(2)、Yoshida Porter(4)、
     Human Made(21)、WTAPS(22)、Mont-bell(41)、Snow Peak(42)、Hario(76)
   - **批次 2**：Hender Scheme(8)、Aeta(9)、Neighborhood(23)、Needles(25)、
     Yamatomichi 山と道(43)、Shimano 釣具(54)、Daiwa 釣具(55)、Kalita(77)
   - **批次 3**：Hyke x Porter 聯名(17)、Danton(28)、Nanamica(32)、
     TNF Purple Label(33)、Arai 安全帽(51)、Shoei 安全帽(52)、
     Pokemon Center Japan 限定(70)、Traveler's Company(99)
   - **批次 4**：Issey Miyake Homme Plisse(34)、Snow Peak Apparel(38)、
     KATO 鐵道模型(61)、TOMIX 鐵道模型(62)、Medicom Be@rbrick(64)、
     Tamashii Nations 限定(65)、Origami Dripper(78)、Vermicular(83)
   - **批次 5**（剩餘 ★★★）：P-Bandai 限定鋼彈(67)、Gashapon 轉蛋整套(69)、
     Sanrio Japan限定(72)、Blue Bottle Japan限定(80)、柳宗理(84)、
     Seiko Prospex/Presage JDM(92)、Casio G-Shock Japan限定(93)、
     Hobonichi/Midori/Kakimori(100)

   跑完批次 1-5（41 個 ★★★，已扣除已驗證 2 個）後，再決定要不要繼續往 ★★ 打——
   ★★ 有 50 幾個，量體很大，建議先看 ★★★ 的候選命中率，如果命中率偏低，
   可能代表 top100.yaml 本身的優先度標記也不夠準，要重新考慮要不要花力氣驗證 ★★。

## 每個品牌要跑的信號（與 discovery 驗證完全一致，見 `validation-signals.md`）

- 信號 A：`python3 sourcing/radar/check_trends.py "品牌1" "品牌2" ...`（可一次多個一起跑，省成本）
- 信號 B：`site:dcard.tw OR site:ptt.cc OR site:mobile01.com 品牌名`
- 信號 C：`品牌名 推薦 代購` 或 `品牌名 日本必買品牌`，找 top100.yaml 以外的獨立來源
- 信號 D-1／D-2：`蝦皮 台灣 品牌名` + 查日本官網定價，看有無官方通路、毛價差多少
- 信號 D-3：**先不查**，統一等自有物流報價確定後再一次補（見 `validation-signals.md` 的
  D 三層拆解說明），不要每個候選各自套用第三方運費表估算

## 產出

- 結果一律寫進 `sourcing/radar/candidates.md`，格式沿用既有模板，來源欄位標
  `top100-sweep`
- 每批跑完，同步更新這份文件的「目前進度」區塊，往下勾掉已完成的品牌

## 與價差試算（D-2/D-3）的關係

D-2（毛價差）現在就能算，跟物流成本無關，照這份計劃正常跑。
D-3（扣運費關稅後的淨利）要等操作者的自有日本-台灣物流報價確定才能算，
在那之前所有候選的 D-3 欄位一律寫「待定」，**不要用比比昂/樂淘這類第三方轉運商的
公開運費表去估算**，因為那不是實際會用的物流管道，算出來的數字沒有意義、還可能誤導判斷。
