/**
 * Mont-bell Extractor
 *
 * Mont-bell 不是 Shopify 商店，需要用 DOM selectors 擷取商品資訊。
 *
 * 注意：CSS selectors 需在實際 Mont-bell 商品頁驗證。
 * 此版本使用已知的頁面結構，若 Mont-bell 改版可能需要更新。
 *
 * 已知結構（montbell.com/jp/）：
 *   - title:    h1 或 .product-detail__title
 *   - price:    包含 ¥ 的元素
 *   - images:   img[src*="media-library/content"]
 *   - variants: 顏色/尺寸 select 的 option 值
 *   - specs:    table 中的規格行
 *   - sku:      URL path 中的數字 ID（/detail/1132260）
 */

/* global BRAND_MAP */

async function extractMontbell() {
  const hostname = window.location.hostname;
  const brandInfo = BRAND_MAP[hostname] || { brand_jp: 'Mont-bell', brand_en: 'Mont-bell' };

  // ── 商品名稱 ──────────────────────────────────────────
  const titleEl =
    document.querySelector('.product-detail__title') ||
    document.querySelector('h1') ||
    document.querySelector('[class*="product"][class*="title"]');
  const productName = titleEl ? titleEl.textContent.trim() : '';

  // ── 價格 ──────────────────────────────────────────────
  const priceEl =
    document.querySelector('[class*="price"]') ||
    document.querySelector('[class*="Price"]');
  let costJpy = 0;
  if (priceEl) {
    const priceText = priceEl.textContent.replace(/[^0-9]/g, '');
    costJpy = parseInt(priceText, 10) || 0;
  }

  // ── 圖片 ──────────────────────────────────────────────
  const imgEls = document.querySelectorAll(
    'img[src*="media-library/content"], ' +
    'img[src*="/product/"], ' +
    '.product-detail__image img, ' +
    '[class*="product"][class*="image"] img'
  );
  const images = [...imgEls].map(img => img.src).filter(src => src);

  // 去重
  const uniqueImages = [...new Set(images)];

  // ── Variants（顏色/尺寸） ─────────────────────────────
  const variants = [];
  const selectEls = document.querySelectorAll(
    '.product-detail__variant select, ' +
    '[class*="variant"] select, ' +
    'select[data-option]'
  );

  selectEls.forEach((sel) => {
    const optionName =
      sel.getAttribute('data-option') ||
      sel.getAttribute('aria-label') ||
      sel.getAttribute('name') ||
      '選項';
    const values = [...sel.options]
      .filter(opt => opt.value && !opt.disabled)
      .map(opt => opt.textContent.trim());
    if (values.length > 0) {
      variants.push({ option: optionName, values });
    }
  });

  // 如果沒找到 select，嘗試從 radio/button 群組推測
  if (variants.length === 0) {
    const colorSwatches = document.querySelectorAll(
      '[class*="color"] [class*="swatch"], ' +
      '[class*="swatch"][class*="color"], ' +
      '[class*="Color"] button'
    );
    if (colorSwatches.length > 0) {
      const values = [...colorSwatches]
        .map(el => el.getAttribute('title') || el.getAttribute('aria-label') || el.textContent.trim())
        .filter(Boolean);
      if (values.length > 0) {
        variants.push({ option: 'カラー', values });
      }
    }

    const sizeButtons = document.querySelectorAll(
      '[class*="size"] button, ' +
      '[class*="Size"] button, ' +
      'button[class*="size"]'
    );
    if (sizeButtons.length > 0) {
      const values = [...sizeButtons]
        .map(el => el.textContent.trim())
        .filter(Boolean);
      if (values.length > 0) {
        variants.push({ option: 'サイズ', values });
      }
    }
  }

  // ── 規格 ──────────────────────────────────────────────
  let material = '';
  let dimensions = '';
  let weightG = 0;

  const specRows = document.querySelectorAll(
    '.product-detail__spec tr, ' +
    '[class*="spec"] tr, ' +
    'table[class*="spec"] tr, ' +
    '.product-detail__info tr'
  );

  specRows.forEach((row) => {
    const th = row.querySelector('th');
    const td = row.querySelector('td');
    if (!th || !td) return;

    const label = th.textContent.trim().toLowerCase();
    const value = td.textContent.trim();

    if (label.includes('素材') || label.includes('material') || label.includes('材質')) {
      material = value;
    } else if (label.includes('サイズ') || label.includes('size') || label.includes('尺寸') || label.includes('寸法')) {
      dimensions = value;
    } else if (label.includes('重量') || label.includes('weight') || label.includes('重さ')) {
      const grams = parseInt(value.replace(/[^0-9]/g, ''), 10);
      if (grams > 0) {
        // Mont-bell 重量單位通常是 g，但有些商品用 kg
        weightG = value.toLowerCase().includes('kg') ? grams * 1000 : grams;
      }
    }
  });

  // ── SKU ──────────────────────────────────────────────
  const skuMatch = window.location.pathname.match(/(\d{5,})/);
  const sku = skuMatch ? skuMatch[1] : '';

  // ── URL handle ────────────────────────────────────────
  const urlHandle = sku
    ? `montbell-${sku}`
    : `montbell-${productName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').substring(0, 60)}`;

  return {
    status: 'draft',
    brand_jp: brandInfo.brand_jp,
    brand_en: brandInfo.brand_en,
    product_name: productName,
    product_type: '戶外運動',
    shopify_category: '',
    shopify_taxonomy_id: '',
    category_attributes: {},
    url_handle: urlHandle,

    cost_jpy: costJpy,
    price_twd: 0,
    price_tw_ref: 0,
    price_gap_note: '',

    variants,
    material,
    dimensions,
    weight_g: weightG,
    country_of_origin: '日本',

    japan_exclusive: true,
    season: '',
    gender: '',
    style_tags: [],

    stock_status: 'in_stock',
    sourcing_status: 'available',

    title_zh: '',
    seo_title: '',
    seo_meta: '',
    description_fact: '',
    description_feel: '',
    description_trust: '',
    alt_texts: {},
    faq: [],
    tags: ['curated:popo-select'],
    jsonld_product: '',
    jsonld_faq: '',

    images: uniqueImages,

    body_html: '',
    tags_raw: '',
    vendor_raw: brandInfo.brand_jp,
    _sku: sku,

    published: {
      shopify_id: '',
      shopify_url: '',
      shopify_status: '',
      published_at: '',
    },
  };
}
