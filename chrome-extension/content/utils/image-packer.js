/**
 * Image Packer — 從 popup 端 fetch 圖片並包成 ZIP
 *
 * 在 popup context 中執行（不是 content script），因為：
 *   - Popup 有 extension origin（chrome-extension://...），fetch 不受 CORS 限制
 *   - Content script 在 page origin 中，跨域 fetch 圖片會被 CORS 擋
 *
 * 依賴：lib/jszip.min.js（需在 popup.html 中先載入）
 */

/* global JSZip, buildYaml */

/**
 * 下載所有圖片 + product.yaml，打包成 ZIP 並觸發瀏覽器下載。
 *
 * @param {Object} data - structured product data
 * @returns {Promise<void>}
 */
async function packAndDownload(data) {
  if (typeof JSZip === 'undefined') {
    throw new Error('JSZip 未載入，請確認 lib/jszip.min.js 存在');
  }

  const zip = new JSZip();
  const imageFolder = zip.folder('images');

  // ── 加入 product.yaml ──
  const yamlString = buildYaml(data);
  zip.file('product.yaml', yamlString);

  // ── 加入圖片 ──
  const imageUrls = data.images || [];
  if (imageUrls.length === 0) {
    // 沒有圖片也可以下載（只有 YAML）
    const zipBlob = await zip.generateAsync({ type: 'blob' });
    downloadBlob(zipBlob, data);
    return;
  }

  const imageJobs = imageUrls.map(async (url, i) => {
    try {
      const resp = await fetch(url);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

      const blob = await resp.blob();

      // 從 URL 取檔名，或從 Content-Type 推副檔名
      let filename = getFilenameFromUrl(url, i);
      if (!filename.includes('.')) {
        const ext = getExtensionFromMime(blob.type);
        filename = `${filename}.${ext}`;
      }

      imageFolder.file(filename, blob);
      return { ok: true, filename };
    } catch (err) {
      console.warn(`圖片下載失敗 [${i}]: ${url} — ${err.message}`);
      return { ok: false, url, error: err.message };
    }
  });

  const results = await Promise.all(imageJobs);
  const successCount = results.filter(r => r.ok).length;
  const failCount = results.filter(r => !r.ok).length;

  console.log(`圖片下載完成：${successCount} 成功, ${failCount} 失敗`);

  // ── 產生 ZIP 並下載 ──
  const zipBlob = await zip.generateAsync({ type: 'blob' });
  downloadBlob(zipBlob, data);
}

/**
 * 建立 download link 並觸發下載。
 */
function downloadBlob(blob, data) {
  const filename = data.url_handle || 'product';
  const url = URL.createObjectURL(blob);

  // 先嘗試 chrome.downloads API（extension 專用）
  if (typeof chrome !== 'undefined' && chrome.downloads) {
    chrome.downloads.download({
      url,
      filename: `${filename}.zip`,
      saveAs: true,
    }, () => {
      // 延遲 revoke 確保 download 已經開始
      setTimeout(() => URL.revokeObjectURL(url), 3000);
    });
  } else {
    // fallback: 一般 anchor download
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}.zip`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 3000);
  }
}

/**
 * 從 URL 取得檔名。
 */
function getFilenameFromUrl(url, index) {
  try {
    const urlObj = new URL(url);
    const pathname = urlObj.pathname;
    const basename = pathname.split('/').pop();

    // 如果 basename 是空的或沒有副檔名（可能是 Shopify CDN 的 query-param 格式）
    if (basename && basename.includes('.')) {
      return basename;
    }

    // 嘗試從 Shopify 的 ?v= 參數取
    // 例：https://cdn.shopify.com/.../products/123.jpg?v=123
    // 這種情況 pathname 可能以副檔名結尾
    if (pathname.match(/\.(jpg|jpeg|png|webp|gif|bmp)/i)) {
      return pathname.split('/').pop() || `image_${index + 1}`;
    }

    return `image_${String(index + 1).padStart(2, '0')}`;
  } catch {
    return `image_${String(index + 1).padStart(2, '0')}.jpg`;
  }
}

/**
 * 從 MIME type 推測副檔名。
 */
function getExtensionFromMime(mimeType) {
  const MAP = {
    'image/jpeg': 'jpg',
    'image/png': 'png',
    'image/webp': 'webp',
    'image/gif': 'gif',
    'image/bmp': 'bmp',
    'image/svg+xml': 'svg',
    'image/avif': 'avif',
  };
  return MAP[mimeType] || 'jpg';
}
