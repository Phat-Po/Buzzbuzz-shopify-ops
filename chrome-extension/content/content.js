/**
 * BuzzBuzz Chrome Extension — Content Script
 *
 * 注入到目標商品頁面後執行：
 *   1. 從 hostname 判定站台類型
 *   2. 呼叫對應 extractor
 *   3. 透過 chrome.runtime.sendMessage() 回傳結構化資料
 *
 * 注意：此檔案最後載入（在 extractors + utils 之後），
 * 所以可以直接呼叫 extractShopify / extractMontbell / BRAND_MAP / buildYaml。
 */

(async function main() {
  try {
    const hostname = window.location.hostname;
    const extractor = detectExtractor(hostname);

    if (!extractor) {
      chrome.runtime.sendMessage({
        type: 'BUZZBUZZ_ERROR',
        message: `不支援的網站：${hostname}\n\n目前支援：\n• Shopify 商店（converse.co.jp 等）\n• Mont-bell (montbell.com)`,
      });
      return;
    }

    const data = await extractor();

    if (!data) {
      chrome.runtime.sendMessage({
        type: 'BUZZBUZZ_ERROR',
        message: `無法擷取商品資料：${hostname}\n\n可能原因：\n• 此頁面不是商品頁（例如是首頁或列表頁）\n• 網站不是 Shopify 商店\n• 網站阻擋了 API 請求`,
      });
      return;
    }

    data._source_url = window.location.href;
    data._extracted_at = new Date().toISOString();

    chrome.runtime.sendMessage({
      type: 'BUZZBUZZ_PRODUCT_DATA',
      data,
    });
  } catch (err) {
    chrome.runtime.sendMessage({
      type: 'BUZZBUZZ_ERROR',
      message: `擷取失敗：${err.message}`,
    });
  }
})();

/**
 * 根據 hostname 判斷使用哪個 extractor。
 * 回傳 async function 或 null。
 */
function detectExtractor(hostname) {
  // Converse Tokyo 自訂平台（converse-tokyo.jp）
  if (hostname.includes('converse-tokyo.jp')) {
    return extractConverseTokyo;
  }

  // Shopify 商店（支援 .json endpoint 的站台）
  const shopifyHosts = [
    'converse.co.jp',
    'origami-kai-tea.com',
    'origami-kai.com',
    'humanmade.jp',
    'katomodels.com',
    'e-katomodels2.com',
  ];

  if (shopifyHosts.some(h => hostname.includes(h))) {
    return extractShopify;
  }

  // Mont-bell
  if (hostname.includes('montbell.com')) {
    return extractMontbell;
  }

  // 通用 fallback: 嘗試 Shopify .json endpoint
  return tryGenericShopify;
}

/**
 * 通用 Shopify 嘗試：fetch .json endpoint，成功就當 Shopify 處理，
 * 失敗就回傳 null（不支援）。
 */
async function tryGenericShopify() {
  try {
    const resp = await fetch(window.location.href + '.json');
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const json = await resp.json();
    if (!json.product) throw new Error('Not a Shopify product page');
    return extractShopify();
  } catch (err) {
    console.warn('BuzzBuzz: 通用 Shopify 嘗試失敗', err.message);
    return null;
  }
}
