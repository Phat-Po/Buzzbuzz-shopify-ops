/**
 * BuzzBuzz Chrome Extension — Popup Controller
 *
 * 流程：
 *   1. 取得目前 active tab
 *   2. 注入 content script（含 extractors + utils）
 *   3. 接收擷取到的結構化商品資料
 *   4. 渲染預覽 + 可編輯欄位
 *   5. 提供「複製 YAML」和「下載 ZIP」按鈕
 */

/* global buildYaml, packAndDownload */

// ── State ──────────────────────────────────────────────────
let productData = null;

// ── DOM refs ──────────────────────────────────────────────
const $status    = document.getElementById('status');
const $statusIcon= document.querySelector('.status__icon');
const $statusText= document.querySelector('.status__text');
const $preview   = document.getElementById('preview');
const $error     = document.getElementById('error');
const $errorText = document.getElementById('error-text');
const $btnCopy   = document.getElementById('btn-copy');
const $btnZip    = document.getElementById('btn-zip');

// ── Entry ─────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  try {
    setStatus('loading', '🔍', '擷取商品資訊中...');

    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) {
      setStatus('error', '⚠️', '無法取得當前分頁');
      return;
    }

    // 注入 content scripts（含 extractors + utils）
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: [
        'content/extractors/shopify.js',
        'content/extractors/montbell.js',
        'content/extractors/converse-tokyo.js',
        'content/utils/brand-map.js',
        'content/utils/yaml-builder.js',
        'content/content.js',
      ],
    });
  } catch (err) {
    setStatus('error', '⚠️', `注入失敗：${err.message}`);
  }
});

// ── 接收 content script 回傳的資料 ──────────────────────────
chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === 'BUZZBUZZ_PRODUCT_DATA') {
    productData = msg.data;
    renderPreview(productData);
    setStatus('success', '✅', '擷取完成');
    $btnCopy.disabled = false;
    $btnZip.disabled = false;
  }

  if (msg.type === 'BUZZBUZZ_ERROR') {
    setStatus('error', '⚠️', msg.message);
    $errorText.textContent = msg.message;
    $error.classList.remove('error--hidden');
  }
});

// ── 按鈕事件 ──────────────────────────────────────────────
$btnCopy.addEventListener('click', async () => {
  if (!productData) return;

  // 把使用者編輯的值合併進 productData
  const data = getEditedData();
  const yamlString = buildYaml(data);

  try {
    await navigator.clipboard.writeText(yamlString);
    flashButton($btnCopy, '✅ 已複製！');
  } catch {
    // fallback: 用 textarea 複製
    const ta = document.createElement('textarea');
    ta.value = yamlString;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    flashButton($btnCopy, '✅ 已複製！');
  }
});

$btnZip.addEventListener('click', async () => {
  if (!productData) return;

  const data = getEditedData();
  setStatus('loading', '📦', '下載圖片中...');

  try {
    await packAndDownload(data);
    setStatus('success', '✅', 'ZIP 下載完成');
    flashButton($btnZip, '✅ 完成！');
  } catch (err) {
    setStatus('error', '⚠️', `下載失敗：${err.message}`);
  }
});

// ── UI helpers ────────────────────────────────────────────

function setStatus(state, icon, text) {
  $status.className = `status status--${state}`;
  $statusIcon.textContent = icon;
  $statusText.textContent = text;
}

function renderPreview(data) {
  document.getElementById('preview-brand').textContent = data.brand_jp || data.brand_en || '';
  document.getElementById('preview-price').textContent =
    data.cost_jpy ? `¥${data.cost_jpy.toLocaleString()}` : '';
  document.getElementById('preview-name').textContent = data.product_name || '';

  // variants summary
  const variantText = (data.variants || [])
    .map(v => `${v.option}: ${v.values.join('/')}`)
    .join(' · ');
  document.getElementById('preview-variants').textContent = variantText || '—';

  // image count
  const imgCount = (data.images || []).length;
  document.getElementById('preview-images').textContent = `${imgCount} 張`;

  // product type
  document.getElementById('preview-type').textContent = data.product_type || '未分類';

  // 填入可編輯欄位
  const typeSelect = document.getElementById('edit-type');
  if (data.product_type) {
    for (const opt of typeSelect.options) {
      if (opt.value === data.product_type) { opt.selected = true; break; }
    }
  }

  document.getElementById('edit-price').value = data.price_twd || '';
  document.getElementById('edit-handle').value = data.url_handle || '';

  $preview.classList.remove('preview--hidden');
}

function getEditedData() {
  return {
    ...productData,
    product_type: document.getElementById('edit-type').value || productData.product_type,
    price_twd: parseInt(document.getElementById('edit-price').value, 10) || productData.price_twd || 0,
    url_handle: document.getElementById('edit-handle').value || productData.url_handle || '',
  };
}

function flashButton(btn, text) {
  const original = btn.textContent;
  btn.textContent = text;
  setTimeout(() => { btn.textContent = original; }, 1500);
}
