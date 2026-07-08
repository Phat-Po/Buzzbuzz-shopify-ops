/**
 * Shopify Extractor
 *
 * 利用 Shopify 內建的 .json endpoint 擷取商品資料。
 * 幾乎所有 Shopify 商店都支援：將商品頁 URL 加上 .json 即可取得結構化資料。
 *
 * 回傳標準化 product data object，欄位對應 product.yaml 的 skeleton 欄位。
 */

/* global BRAND_MAP, buildYaml */

async function extractShopify() {
  const url = window.location.href.split('?')[0]; // 去掉 query string
  const resp = await fetch(url + '.json');

  if (!resp.ok) {
    throw new Error(`Shopify .json endpoint 回傳 HTTP ${resp.status}`);
  }

  const json = await resp.json();
  const p = json.product;

  if (!p) {
    throw new Error('此頁面不是 Shopify 商品頁（找不到 product JSON）');
  }

  // ── 品牌 ──────────────────────────────────────────────
  const hostname = window.location.hostname;
  const brandInfo = BRAND_MAP[hostname] || {};
  const brandJp = brandInfo.brand_jp || p.vendor || '';
  const brandEn = brandInfo.brand_en || p.vendor || '';

  // ── 價格 ──────────────────────────────────────────────
  const firstVariant = (p.variants && p.variants[0]) || {};
  const costJpy = parseInt(firstVariant.price, 10) || 0;

  // ── Variants ──────────────────────────────────────────
  const variants = (p.options || []).map(opt => ({
    option: opt.name,
    values: opt.values || [],
  }));

  // ── 圖片 ──────────────────────────────────────────────
  const images = (p.images || []).map(img => {
    // Shopify 圖片 URL 通常有多種尺寸，取最大的
    return img.src || '';
  });

  // ── URL handle ────────────────────────────────────────
  const urlHandle = generateUrlHandle(brandEn, p.title);

  // ── 組合 ──────────────────────────────────────────────
  return {
    // 基本資訊
    status: 'draft',
    brand_jp: brandJp,
    brand_en: brandEn,
    product_name: p.title || '',
    product_type: mapProductType(p.product_type || ''),
    shopify_category: '',
    shopify_taxonomy_id: '',
    category_attributes: {},
    url_handle: urlHandle,

    // 價格
    cost_jpy: costJpy,
    price_twd: 0,
    price_tw_ref: 0,
    price_gap_note: '',

    // 規格
    variants,
    material: '',
    dimensions: '',
    weight_g: 0,
    country_of_origin: '日本',

    // 標籤
    japan_exclusive: true,
    season: '',
    gender: '',
    style_tags: [],

    // 庫存
    stock_status: 'in_stock',
    sourcing_status: 'available',

    // AI 區段（留空）
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

    // 圖片（URL 列表，實際下載在 popup 端）
    images,

    // 原始資料（給 Claude 參考）
    body_html: p.body_html || '',
    tags_raw: p.tags || '',
    vendor_raw: p.vendor || '',

    // 發布記錄（由 push.py 填）
    published: {
      shopify_id: '',
      shopify_url: '',
      shopify_status: '',
      published_at: '',
    },
  };
}

/**
 * 從品牌英文名 + 商品名稱產生 URL handle（ASCII kebab-case）。
 */
function generateUrlHandle(brandEn, productTitle) {
  if (!brandEn || !productTitle) return '';

  const brandSlug = brandEn.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  const titleSlug = productTitle
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');

  // 限制長度，避免太長的 handle
  const combined = `${brandSlug}-${titleSlug}`;
  return combined.substring(0, 80).replace(/-+$/, '');
}

/**
 * 將 Shopify product_type 對應到 BuzzBuzz 的 9 大類別。
 * 如果無法對應則保留原始值。
 */
function mapProductType(shopifyType) {
  const MAP = {
    'bag': '包袋',
    'bags': '包袋',
    'backpack': '包袋',
    'tote': '包袋',
    'apparel': '潮流服飾',
    'clothing': '潮流服飾',
    'shirt': '潮流服飾',
    'jacket': '潮流服飾',
    'pants': '潮流服飾',
    'shoes': '潮流服飾',
    'sneakers': '潮流服飾',
    'outdoor': '戶外運動',
    'camping': '戶外運動',
    'sports': '戶外運動',
    'toy': '收藏玩具',
    'figure': '收藏玩具',
    'coffee': '咖啡器具',
    'tea': '咖啡器具',
    'kitchen': '廚房生活',
    'kitchenware': '廚房生活',
    'watch': '腕錶配件',
    'accessory': '腕錶配件',
    'accessories': '腕錶配件',
    'beauty': '生活美妝',
    'cosmetics': '生活美妝',
    'skincare': '生活美妝',
    'stationery': '文具選品',
    'pen': '文具選品',
    'notebook': '文具選品',
  };

  if (!shopifyType) return '';

  const lower = shopifyType.toLowerCase().trim();
  for (const [key, value] of Object.entries(MAP)) {
    if (lower.includes(key)) return value;
  }

  return shopifyType; // 保留原始值，操作者可以在 popup 中修改
}
