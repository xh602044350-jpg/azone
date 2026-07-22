const productIdInput = document.querySelector('#productId');
const quantityInput = document.querySelector('#quantity');
const replaceIdButton = document.querySelector('#replaceId');
const autoCheckoutButton = document.querySelector('#autoCheckout');
const statusBox = document.querySelector('#status');
const AZONE_ORIGIN = 'https://www.azone-int.co.jp';
const CART_URL = `${AZONE_ORIGIN}/azonet/cart`;

function setStatus(message) {
  statusBox.textContent = message;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function getActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) throw new Error('没有找到当前标签页。');
  if (!tab.url?.startsWith(`${AZONE_ORIGIN}/azonet/`)) {
    throw new Error('请先打开 Azone 页面：https://www.azone-int.co.jp/azonet/...');
  }
  return tab;
}

async function sendToTab(tabId, message) {
  try {
    return await chrome.tabs.sendMessage(tabId, message);
  } catch (error) {
    await chrome.scripting.executeScript({ target: { tabId }, files: ['content.js'] });
    return chrome.tabs.sendMessage(tabId, message);
  }
}

async function sendToActiveTab(message) {
  const tab = await getActiveTab();
  return sendToTab(tab.id, message);
}

async function waitForTabReady(tabId, timeoutMs = 12000) {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    const tab = await chrome.tabs.get(tabId);
    if (tab.status === 'complete') return tab;
    await sleep(250);
  }
  return chrome.tabs.get(tabId);
}

async function goToCartFast(tabId) {
  await sleep(150);
  const tab = await chrome.tabs.get(tabId);
  if (!tab.url?.startsWith(CART_URL)) {
    await chrome.tabs.update(tabId, { url: CART_URL });
  }
  return waitForTabReady(tabId, 1500);
}

async function clickCheckoutFast(tabId, timeoutMs = 2500) {
  const startedAt = Date.now();
  let lastMessage = '';
  while (Date.now() - startedAt < timeoutMs) {
    try {
      const result = await sendToTab(tabId, { type: 'AZONE_CLICK_CHECKOUT' });
      lastMessage = result.message;
      if (result.ok) return result;
    } catch (error) {
      lastMessage = error.message;
    }
    await sleep(100);
  }
  throw new Error(lastMessage || '未找到结算按钮。');
}

function readOptions() {
  const productId = productIdInput.value.trim();
  const quantity = quantityInput.value.trim() || '1';
  if (!/^\d{8,}$/.test(productId)) {
    throw new Error('请输入正确的商品 ID / JAN 码，例如 4573199843124。');
  }
  return { productId, quantity };
}

async function loadSavedOptions() {
  const saved = await chrome.storage.local.get({ productId: '4573199843124', quantity: '1' });
  productIdInput.value = saved.productId;
  quantityInput.value = saved.quantity;
}

replaceIdButton.addEventListener('click', async () => {
  replaceIdButton.disabled = true;
  setStatus('正在替换当前页面 ID（不刷新页面）...');
  try {
    const { productId, quantity } = readOptions();
    await chrome.storage.local.set({ productId, quantity });
    const result = await sendToActiveTab({ type: 'AZONE_APPLY_PRODUCT_ID', productId, quantity });
    setStatus(result.message);
  } catch (error) {
    setStatus(`失败：${error.message}`);
  } finally {
    replaceIdButton.disabled = false;
  }
});

autoCheckoutButton.addEventListener('click', async () => {
  autoCheckoutButton.disabled = true;
  setStatus('正在替换 ID、加入购物车并前往结算...');
  try {
    const tab = await getActiveTab();
    const { productId, quantity } = readOptions();
    await chrome.storage.local.set({ productId, quantity });

    const addResult = await sendToTab(tab.id, {
      type: 'AZONE_APPLY_AND_ADD_TO_CART',
      productId,
      quantity,
    });
    setStatus(`${addResult.message}\n正在快速进入购物车并点击结算...`);

    const cartTab = await goToCartFast(tab.id);
    const checkoutResult = await clickCheckoutFast(cartTab.id);
    setStatus(`${addResult.message}\n${checkoutResult.message}`);
  } catch (error) {
    setStatus(`失败：${error.message}`);
  } finally {
    autoCheckoutButton.disabled = false;
  }
});

loadSavedOptions().catch((error) => setStatus(`初始化失败：${error.message}`));
