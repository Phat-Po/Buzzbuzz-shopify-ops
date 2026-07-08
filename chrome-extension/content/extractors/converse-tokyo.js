/**
 * Converse Tokyo Extractor (converse-tokyo.jp)
 *
 * Converse Japan 自訂電商平台（非 Shopify）。
 * 利用頁面上的 var item_stock JS 變數 + DOM selectors 擷取商品資料。
 *
 * URL pattern: /item/detail/1_4_A2854PSH900_1/01
 *
 * 資料來源：
 *   - item_stock JS var: colors, sizes, stock, base price, swatch images
 *   - meta[property="og:title"]: 商品名稱
 *   - meta[property="og:image"]: 主圖
 *   - .proper_price: 含稅價格
 *   - a.detail__slider_img: 全尺寸圖片
 *   - .specArea: 商品描述/規格
 */

/* global BRAND_MAP */

async function extractConverseTokyo() {
  const hostname = window.location.hostname;
  const brandInfo = BRAND_MAP[hostname] || { brand_jp: 'Converse Tokyo', brand_en: 'Converse Tokyo' };

  // ── 商品名稱 ──────────────────────────────────────────
  const ogTitle = document.querySelector('meta[property="og:title"]')?.content || '';
  const titleTag = document.title || '';
  // og:title 格式: "【TAG】商品名｜CONVERSE TOKYO..."
  const productName = (ogTitle || titleTag).split('｜')[0].trim();

  // ── 價格 ──────────────────────────────────────────────
  const priceEl = document.querySelector('.proper_price');
  let costJpy = 0;
  if (priceEl) {
    costJpy = parseInt(priceEl.textContent.replace(/[^0-9]/g, ''), 10) || 0;
  }

  // ── 解析 item_stock JS 變數 ────────────────────────────
  const itemStock = parseItemStock();

  // ── Variants（顏色 + 尺寸） ────────────────────────────
  const variants = [];

  if (itemStock && itemStock.colors) {
    // 顏色
    const colorNames = itemStock.colors.map(c => c.color_name).filter(Boolean);
    if (colorNames.length > 0) {
      variants.push({ option: 'カラー', values: [...new Set(colorNames)] });
    }

    // 尺寸（取第一個顏色的所有尺寸，通常所有顏色共用相同尺寸表）
    const firstColor = itemStock.colors[0];
    if (firstColor && firstColor.sizes) {
      const sizeNames = firstColor.sizes.map(s => s.size_name).filter(Boolean);
      if (sizeNames.length > 0) {
        variants.push({ option: 'サイズ', values: [...new Set(sizeNames)] });
      }
    }

    // 如果 itemStock 價格和頁面價格不同，用 itemStock 價格（不含稅→換算含稅約 1.1x）
    if (costJpy === 0 && firstColor) {
      const properPrice = parseInt(String(firstColor.color_proper || '').replace(/[^0-9]/g, ''), 10);
      if (properPrice > 0) {
        // color_proper 是不含稅價，加 10% 消費稅
        costJpy = Math.round(properPrice * 1.1);
      }
    }
  }

  // 如果 itemStock 沒抓到，fallback 到 DOM
  if (variants.length === 0) {
    const colorEls = document.querySelectorAll('.color__name');
    const colors = [...colorEls].map(el => el.textContent.trim()).filter(Boolean);
    if (colors.length > 0) {
      variants.push({ option: 'カラー', values: [...new Set(colors)] });
    }

    const sizeButtons = document.querySelectorAll('.add_cart_btn');
    const sizes = [...sizeButtons].map(btn => {
      const sizeEl = btn.closest('.size-list')?.querySelector('.size-name') ||
                     btn.parentElement?.querySelector('[class*="size"]');
      return sizeEl?.textContent?.trim() || '';
    }).filter(Boolean);
    if (sizes.length > 0) {
      variants.push({ option: 'サイズ', values: [...new Set(sizes)] });
    }
  }

  // ── 圖片 ──────────────────────────────────────────────
  const images = [];

  // 主圖：og:image meta
  const ogImage = document.querySelector('meta[property="og:image"]')?.content;
  if (ogImage) {
    images.push(ogImage);
  }

  // 其他圖片：從 slider <a> tags
  const sliderLinks = document.querySelectorAll('a.detail__slider_img');
  sliderLinks.forEach((a) => {
    const href = a.getAttribute('href');
    if (href && !images.includes(href)) {
      // 轉換為絕對 URL
      const absoluteUrl = href.startsWith('http') ? href : `https://${hostname}${href}`;
      if (!images.includes(absoluteUrl)) {
        images.push(absoluteUrl);
      }
    }
  });

  // 從 itemStock 取 swatch 圖片
  if (itemStock && itemStock.colors) {
    itemStock.colors.forEach((c) => {
      if (c.images) {
        const tmp = document.createElement('div');
        tmp.innerHTML = c.images;
        const imgs = tmp.querySelectorAll('img');
        imgs.forEach((img) => {
          const src = img.getAttribute('src');
          if (src) {
            const absoluteUrl = src.startsWith('http') ? src : `https://${hostname}${src}`;
            if (!images.includes(absoluteUrl)) {
              images.push(absoluteUrl);
            }
          }
        });
      }
    });
  }

  // ── SKU ──────────────────────────────────────────────
  const skuMatch = window.location.pathname.match(/A\d+[A-Z]*\d*/i) ||
                   window.location.pathname.match(/([A-Z]+\d{3,})/i);
  const sku = skuMatch ? skuMatch[0] : '';

  // ── 描述 / 規格 ──────────────────────────────────────
  let description = '';

  // 從 .specArea 取規格文字
  const specArea = document.querySelector('.specArea');
  if (specArea) {
    description = specArea.textContent.replace(/\s+/g, ' ').trim();
    // 移除價格數字（避免干擾）
    description = description.replace(/¥[\d,]+/g, '').replace(/（税込）/g, '');
  }

  // 也嘗試取 .textArea 的內容
  const textArea = document.querySelector('.textArea');
  if (textArea && !description) {
    description = textArea.textContent.replace(/\s+/g, ' ').trim();
  }

  // ── 材質（從描述中推測） ──────────────────────────────
  let material = '';
  if (description) {
    // 嘗試匹配材質關鍵詞
    const matMatch = description.match(/(?:素材|material|アッパー|ソール)[：:]\s*(.+?)(?:[。\n]|$)/i);
    if (matMatch) {
      material = matMatch[1].trim();
    }
  }

  // ── URL handle ────────────────────────────────────────
  const urlHandle = sku
    ? `converse-tokyo-${sku.toLowerCase()}`
    : `converse-tokyo-${productName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').substring(0, 60)}`;

  // ── 產品類型（從 URL 或 category 推測） ──────────────────
  let productType = '';
  const catMatch = window.location.pathname.match(/category_id=(\d+)/);
  if (catMatch) {
    // category_id=11 → shoes
    const catMap = { '11': '潮流服飾' };
    productType = catMap[catMatch[1]] || '';
  }

  return {
    status: 'draft',
    brand_jp: brandInfo.brand_jp,
    brand_en: brandInfo.brand_en,
    product_name: productName,
    product_type: productType,
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
    dimensions: '',
    weight_g: 0,
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

    images,

    body_html: description || '',
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

/**
 * 從頁面 script 中解析 var item_stock = {...} JS 物件。
 *
 * 注意：這不是合法 JSON（有 trailing commas, 像 },] 和 },}），
 * 所以不能直接用 JSON.parse。這裡用 Function constructor 安全地
 * evaluate JS expression（相當於 page script 自己執行的 eval）。
 */
function parseItemStock() {
  try {
    const scripts = document.querySelectorAll('script');
    for (const script of scripts) {
      const text = script.textContent || '';
      if (text.includes('var item_stock')) {
        // 使用 Function constructor 評估 JS 表達式
        // 這比 eval 安全：沒有 closure access，只在 global scope 執行
        const fn = new Function(text + '; return item_stock;');
        return fn();
      }
    }
  } catch (err) {
    console.warn('BuzzBuzz: 無法解析 item_stock', err.message);
  }
  return null;
}
