const productIdInput = document.querySelector('#productId');
const quantityInput = document.querySelector('#quantity');
const applyButton = document.querySelector('#apply');
const restoreButton = document.querySelector('#restore');
const statusBox = document.querySelector('#status');

function setStatus(message) {
  statusBox.textContent = message;
}

async function getActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) throw new Error('没有找到当前标签页。');
  if (!tab.url?.startsWith('https://www.azone-int.co.jp/azonet/item/')) {
    throw new Error('请先打开 Azone 商品页：https://www.azone-int.co.jp/azonet/item/...');
  }
  return tab;
}

async function sendToActiveTab(message) {
  const tab = await getActiveTab();
  try {
    return await chrome.tabs.sendMessage(tab.id, message);
  } catch (error) {
    await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ['content.js'] });
    return chrome.tabs.sendMessage(tab.id, message);
  }
}

async function loadSavedOptions() {
  const saved = await chrome.storage.local.get({ productId: '4573199843124', quantity: '1' });
  productIdInput.value = saved.productId;
  quantityInput.value = saved.quantity;
}

applyButton.addEventListener('click', async () => {
  const productId = productIdInput.value.trim();
  const quantity = quantityInput.value.trim() || '1';
  if (!/^\d{8,}$/.test(productId)) {
    setStatus('请输入正确的商品 ID / JAN 码，例如 4573199843124。');
    return;
  }

  applyButton.disabled = true;
  setStatus('正在应用到当前页面 DOM（不刷新页面）...');
  try {
    await chrome.storage.local.set({ productId, quantity });
    const result = await sendToActiveTab({ type: 'AZONE_APPLY_PRODUCT_ID', productId, quantity });
    setStatus(result.message);
  } catch (error) {
    setStatus(`失败：${error.message}`);
  } finally {
    applyButton.disabled = false;
  }
});

restoreButton.addEventListener('click', async () => {
  restoreButton.disabled = true;
  setStatus('正在恢复本页原始 DOM 值...');
  try {
    const result = await sendToActiveTab({ type: 'AZONE_RESTORE_ORIGINALS' });
    setStatus(result.message);
  } catch (error) {
    setStatus(`失败：${error.message}`);
  } finally {
    restoreButton.disabled = false;
  }
});

loadSavedOptions().catch((error) => setStatus(`初始化失败：${error.message}`));
