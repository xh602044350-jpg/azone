const productIdInput = document.querySelector('#productId');
const quantityInput = document.querySelector('#quantity');
const applyButton = document.querySelector('#apply');
const goCartButton = document.querySelector('#goCart');
const checkoutButton = document.querySelector('#checkout');
const restoreButton = document.querySelector('#restore');
const statusBox = document.querySelector('#status');

function setStatus(message) {
  statusBox.textContent = message;
}

async function getActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) throw new Error('没有找到当前标签页。');
  if (!tab.url?.startsWith('https://www.azone-int.co.jp/azonet/')) {
    throw new Error('请先打开 Azone 页面：https://www.azone-int.co.jp/azonet/...');
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


goCartButton.addEventListener('click', async () => {
  goCartButton.disabled = true;
  setStatus('正在跳转购物车...');
  try {
    const tab = await getActiveTab();
    await chrome.tabs.update(tab.id, { url: 'https://www.azone-int.co.jp/azonet/cart' });
    setStatus('已跳转到购物车页面。');
  } catch (error) {
    setStatus(`失败：${error.message}`);
  } finally {
    goCartButton.disabled = false;
  }
});

checkoutButton.addEventListener('click', async () => {
  checkoutButton.disabled = true;
  setStatus('正在点击购物车页面的“レジに進む”按钮...');
  try {
    const result = await sendToActiveTab({ type: 'AZONE_CLICK_CHECKOUT' });
    setStatus(result.message);
  } catch (error) {
    setStatus(`失败：${error.message}`);
  } finally {
    checkoutButton.disabled = false;
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
