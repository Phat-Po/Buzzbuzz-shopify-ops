# BuzzBuzz 日本選物店 — Status

## ▲ Current

---

## 2026-07-08 | top100 驗證批次 4 完成（8 品牌），Vermicular 4/4 最強

**Done this session:**
- 跑完 `top100-validation-sweep-plan.md` 批次 4 的 8 個 ★★★ 品牌全信號驗證：
  Issey Miyake Homme Plisse(34)、Snow Peak Apparel(38)、KATO 鐵道模型(61)、
  TOMIX 鐵道模型(62)、Medicom Be@rbrick(64)、Tamashii Nations 限定(65)、
  Origami Dripper(78)、Vermicular(83)
- 結果寫入 `sourcing/radar/candidates.md`（8 筆詳細記錄 + 更新 overview 總覽表）
- 同步更新 `tasks/top100-validation-sweep-plan.md` 進度

**Current state:**
四批累計 32 個 ★★★ 品牌已驗證。本批可推進 2（KATO/Origami）、有條件候選 5、
觀察池 1（Snow Peak Apparel 2/4 偏弱）。Vermicular 為全 top100 熱度最高品牌（43.6）。
剩餘 ★★★ 品牌：批次 5 最後 8 個（P-Bandai、Gashapon、Sanrio、Blue Bottle、柳宗理、
Seiko、G-Shock、Hobonichi），操作者已確認先暫停、commit 後再決定。

**Next steps:**
1. 操作者決定是否繼續批次 5（最後一批 ★★★）
2. 若要繼續：P-Bandai 限定鋼彈(67)、Gashapon 轉蛋整套(69)、Sanrio Japan限定(72)、
   Blue Bottle Japan限定(80)、柳宗理(84)、Seiko Prospex/Presage JDM(92)、
   Casio G-Shock Japan限定(93)、Hobonichi/Midori/Kakimori(100)
3. 自有物流報價確定後，回頭補所有候選的 D-3 淨利試算
4. ★★★ 全跑完後，評估命中率決定是否繼續 ★★（50+品牌）

**Decisions / notes:**
- 信號 A 關鍵詞匹配問題再次出現：多數品牌的英文正式名稱在台灣 Google Trends 幾無資料
  （如「Tamashii Nations」avg 3.1 vs 台灣人實際搜的「魂商店」），未來批次應先用台灣
  慣用詞測試、再用英文正式名補測，雙重確認
- KATO 鐵道模型是少數「台灣無獨家代理」的 ★★★ 品牌，代購無代理商抗議風險，值得優先推進
- Be@rbrick/Tamashii Nations 這類「日本限定抽選」品項的共同門檻是取得日本抽選資格
  （需日本地址/電話/信用卡），營運上需要日本買手配合

---

## 2026-07-08 | Category 卡片下拉選單確認為平台限制，無法用 API 自動化

**Done this session:**
- 找到 Admin 商品頁「Category」卡片（Color/Target gender/Age group 下拉選單）真正的
  機制：`shopify` 保留 namespace + `list.metaobject_reference` 型別，要先用
  `standardMetafieldDefinitionEnable` mutation 啟用
- 對 CONVERSE TOKYO 啟用了 Color/Target gender/Age group 三個標準欄位
- 確認背後的選項值第三方 app token 讀不到也寫不進去——這是 Shopify 平台限制，已寫進
  AGENTS.md

**Current state:**
Category 卡片現在會顯示三個可填的下拉選單，但值需操作者自己在 Admin 手動點選。
Upper material 沒有官方 standard template。此事到此為止——已確認是平台限制。

**Next steps:**
1. 操作者有空時自己去 Admin 手動填 Color/Target gender/Age group（每個產品約 2 分鐘）
2. 繼續往下跑選品

**Decisions / notes:**
- Category 卡片下拉選單「不可 API 自動化」是確認過的平台限制，不是 bug

## ■ Milestones

- 2026-07-08 top100 驗證批次 4 完成（8 品牌）：Vermicular 4/4 最強、KATO/Origami 可推進、其餘 5 有條件候選 | ✅ done
- 2026-07-08 top100 驗證批次 3 完成（8 品牌）：Shoei/Arai 4/4 最強、TNF Purple Label A 信號關鍵詞修正後 3/4 候選 | ✅ done
- 2026-07-08 Category 屬性打通 + url_handle/SEO/metafields 收尾：`push.py` 新增通用機制自動查 TaxonomyValue GID 寫入分類屬性 | ✅ done
- 2026-07-08 push.py 補完圖片/變體上傳（`productSet` 取代已棄用的三段式 mutation）、供應鏈保密規則收斂、tags 簡化 | ✅ done
- 2026-07-08 選品雷達上線（`sourcing/radar/` discovery+validation 兩層方法論）+ 打通 Shopify OAuth + 第一個產品成功推送 Shopify DRAFT | ✅ done
- 2026-07-07 項目重新定位：從 ERP 改為本地 CLI 上稿工具，建立 products/YAML 模板、三個 CLI 腳本、Top100 選品清單 | ✅ done

## ▼ Archive

- 2026-07-07 MVP-0: FastAPI + SQLite web dashboard (已廢棄，保留在 git history)
