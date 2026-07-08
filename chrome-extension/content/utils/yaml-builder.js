/**
 * YAML Builder — 將 structured product data 轉為 product.yaml 字串
 *
 * 輸出的 YAML 格式對齊 products/_template/product.yaml，確保：
 *   - 欄位順序一致
 *   - 多行文字用 YAML literal block scalar (|)
 *   - 特殊字元被正確 quoting
 *   - AI 區段全部留空（由 Claude 在這個 repo 裡補）
 *
 * 此檔案同時載入於 content script（被注入頁面）和 popup（<script src>）。
 */

/* exported buildYaml */

function buildYaml(data) {
  const L = [];

  // ── Header ──
  L.push('# BuzzBuzz 產品資料檔');
  L.push('# 此檔案由 BuzzBuzz Chrome Extension 自動產生');
  L.push('# AI 區段（title_zh / description_* / seo_* / faq / jsonld_*）留空，');
  L.push('# 請 Claude 在這個 repo 裡補完。');
  L.push('');
  L.push('');

  // ── 基本資訊 ──
  section(L, '基本資訊');
  L.push(kv('status', data.status));
  L.push(kv('brand_jp', data.brand_jp));
  L.push(kv('brand_en', data.brand_en));
  L.push(kv('product_name', data.product_name));
  L.push(kv('product_type', data.product_type));
  L.push(kv('shopify_category', data.shopify_category || ''));
  L.push(kv('shopify_taxonomy_id', data.shopify_taxonomy_id || ''));
  L.push(kvBlock('category_attributes', data.category_attributes || {}));
  L.push(kv('url_handle', data.url_handle));
  L.push('');

  // ── 價格 ──
  section(L, '價格');
  L.push(kv('cost_jpy', data.cost_jpy));
  L.push(kv('price_twd', data.price_twd));
  L.push(kv('price_tw_ref', data.price_tw_ref || 0));
  L.push(kv('price_gap_note', data.price_gap_note || ''));
  L.push('');

  // ── 規格 ──
  section(L, '規格');
  if (data.variants && data.variants.length > 0) {
    L.push('variants:');
    for (const v of data.variants) {
      L.push(`  - option: ${quoteYaml(v.option)}`);
      L.push(`    values: [${v.values.map(quoteYaml).join(', ')}]`);
    }
  } else {
    L.push('variants:');
    L.push('  - option: ""');
    L.push('    values: []');
  }
  L.push(kv('material', data.material));
  L.push(kv('dimensions', data.dimensions));
  L.push(kv('weight_g', data.weight_g));
  L.push(kv('country_of_origin', data.country_of_origin));
  L.push('');

  // ── 標籤與屬性 ──
  section(L, '標籤與屬性');
  L.push(kv('japan_exclusive', data.japan_exclusive));
  L.push(kv('season', data.season || ''));
  L.push(kv('gender', data.gender || ''));
  L.push(kvList('style_tags', data.style_tags || []));
  L.push('');

  // ── 庫存狀態 ──
  section(L, '庫存狀態');
  L.push(kv('stock_status', data.stock_status));
  L.push(kv('sourcing_status', data.sourcing_status));
  L.push('');

  // ── Claude 填寫區分隔線 ──
  L.push('# ============================================');
  L.push('# ▼ 以下由 Claude 填寫（AI 生成繁中內容）');
  L.push('#');
  L.push('# ⚠️ 供應鏈保密：以下所有欄位最終都會出現在 Shopify 商品頁或 metafields，');
  L.push('# 等於是公開資訊。絕對不能寫「向官網下單」「官網缺貨/現貨」「台灣沒有官方或代理通路」');
  L.push('# 這類會洩露進貨來源的句子。');
  L.push('# ============================================');
  L.push('');

  // ── SEO 與頁面標題 ──
  section(L, 'SEO 與頁面標題');
  L.push(kv('title_zh', data.title_zh || ''));
  L.push(kv('seo_title', data.seo_title || ''));
  L.push(kv('seo_meta', data.seo_meta || ''));
  L.push('');

  // ── 商品描述 ──
  section(L, '商品描述（三段式 Fact-Feel-Trust）');
  L.push(kv('description_fact', data.description_fact || ''));
  L.push(kv('description_feel', data.description_feel || ''));
  L.push(kv('description_trust', data.description_trust || ''));
  L.push('');

  // ── 圖片 Alt Text ──
  section(L, '圖片 Alt Text（每張圖都要有）');
  L.push(kvBlock('alt_texts', data.alt_texts || {}));
  L.push('');

  // ── FAQ ──
  section(L, 'FAQ（至少 3 組，AI 搜尋特別喜歡引用 FAQ）');
  L.push(kvList('faq', data.faq || []));
  L.push('');

  // ── Shopify 標籤 ──
  section(L, 'Shopify 標籤');
  L.push(kvList('tags', data.tags || ['curated:popo-select']));
  L.push('');

  // ── 結構化資料 ──
  section(L, '結構化資料（JSON-LD Schema）');
  L.push(kv('jsonld_product', data.jsonld_product || ''));
  L.push(kv('jsonld_faq', data.jsonld_faq || ''));
  L.push('');

  // ── 圖片清單 ──
  section(L, '圖片清單');
  L.push(kvList('images', (data.images || []).map(img => {
    // 如果是完整 URL，取檔名部分
    if (img.startsWith('http')) {
      const url = new URL(img);
      const filename = url.pathname.split('/').pop() || 'image.jpg';
      // 確保有副檔名
      return filename.includes('.') ? `images/${filename}` : `images/${filename}.jpg`;
    }
    return img;
  })));
  L.push('');

  // ── 原始商品描述（給 Claude 參考） ──
  if (data.body_html) {
    L.push('# ────────────────────────────────────────────');
    L.push('# ▼ 原始商品描述（由 Extension 自動擷取，');
    L.push('#   供 Claude 撰寫文案時參考，不會推送到 Shopify）');
    L.push('# ────────────────────────────────────────────');
    L.push(kvMultiline('_body_html', data.body_html));
    L.push('');
  }

  // ── 發布記錄 ──
  L.push('# ============================================');
  L.push('# ▼ 發布記錄（由 scripts/push.py 自動寫入，勿手動編輯）');
  L.push('# ============================================');
  L.push('published:');
  L.push(kv('  shopify_id', (data.published && data.published.shopify_id) || ''));
  L.push(kv('  shopify_url', (data.published && data.published.shopify_url) || ''));
  L.push(kv('  shopify_status', (data.published && data.published.shopify_status) || ''));
  L.push(kv('  published_at', (data.published && data.published_at) || ''));
  L.push('');

  return L.join('\n');
}

// ── YAML 輔助函式 ────────────────────────────────────────

/** 簡單 key: value，自動 quoting */
function kv(key, value) {
  if (value === null || value === undefined) return `${key}: ""`;
  if (typeof value === 'boolean') return `${key}: ${value}`;
  if (typeof value === 'number') return `${key}: ${value}`;
  if (value === '') return `${key}: ""`;
  return `${key}: ${quoteYaml(String(value))}`;
}

/** key: 多行文字（用 YAML literal block scalar | ） */
function kvMultiline(key, value) {
  if (!value) return `${key}: ""`;
  // strip HTML tags for readability in YAML
  const stripped = String(value).replace(/<[^>]*>/g, '').trim();
  if (!stripped) return `${key}: ""`;
  const lines = stripped.split('\n').map(l => l.trim()).filter(l => l);
  return `${key}: |\n  ${lines.join('\n  ')}`;
}

/** 簡單的 key: {} block */
function kvBlock(key, obj) {
  if (!obj || Object.keys(obj).length === 0) return `${key}: {}`;
  const entries = Object.entries(obj).map(([k, v]) => `  ${quoteYaml(k)}: ${quoteYaml(v)}`);
  return `${key}:\n${entries.join('\n')}`;
}

/** key: [...] list */
function kvList(key, arr) {
  if (!arr || arr.length === 0) return `${key}: []`;
  const items = arr.map(item => {
    if (typeof item === 'object' && item !== null) {
      // faq 物件: {q: "...", a: "..."}
      const q = quoteYaml(item.q || '');
      const a = quoteYaml(item.a || '');
      return `  - q: ${q}\n    a: ${a}`;
    }
    return `  - ${quoteYaml(String(item))}`;
  });
  if (items.length === 0) return `${key}: []`;
  const joined = items.join('\n');
  // 如果每個 item 都是物件（含換行），則不用額外換行
  if (joined.includes('\n')) {
    return `${key}:\n${joined}`;
  }
  return `${key}: [${arr.map(i => quoteYaml(String(i))).join(', ')}]`;
}

/** section header comment */
function section(L, title) {
  L.push(`# === ${title} ===`);
}

/**
 * YAML quoting：如果值包含特殊字元（: # { } [ ] , & * ? | - < > = ! % @ ` " '）
 * 就用雙引號包起來，並 escape 內部雙引號。
 */
function quoteYaml(value) {
  if (value === null || value === undefined) return '""';
  const s = String(value);
  if (s === '') return '""';

  // 純數字、boolean 直接回傳
  if (/^(true|false|yes|no)$/i.test(s)) return `"${s}"`;

  const needsQuote = /[-:#{}[\]&*?|><=!%@`"'\n]/.test(s) || s.startsWith(' ') || s.endsWith(' ');
  if (!needsQuote) return s;

  return `"${s.replace(/\\/g, '\\\\').replace(/"/g, '\\"')}"`;
}
