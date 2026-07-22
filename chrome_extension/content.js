(() => {
  if (window.__azoneIdHelperLoaded) return;
  window.__azoneIdHelperLoaded = true;

  const originalValues = new WeakMap();

  function remember(element, attribute) {
    let values = originalValues.get(element);
    if (!values) {
      values = new Map();
      originalValues.set(element, values);
    }
    if (!values.has(attribute)) {
      values.set(attribute, element.getAttribute(attribute));
    }
  }

  function setAttribute(element, attribute, value) {
    remember(element, attribute);
    element.setAttribute(attribute, value);
  }

  function replaceAttributeId(attribute, productId, matcher) {
    let count = 0;
    document.querySelectorAll(`[${attribute}]`).forEach((element) => {
      const current = element.getAttribute(attribute);
      if (!current || !matcher.test(current)) return;
      const next = current.replace(matcher, productId);
      if (next !== current) {
        setAttribute(element, attribute, next);
        count += 1;
      }
    });
    return count;
  }

  function applyQuantity(productId, quantity) {
    const selector = `select[name="item_cnt_${productId}"], input[name="item_cnt_${productId}"], select[name="quantity"], input[name="quantity"]`;
    const field = document.querySelector(selector);
    if (!field) return false;

    if (field.tagName.toLowerCase() === 'select') {
      const option = Array.from(field.options).find((item) => item.value === quantity);
      if (option) field.value = quantity;
    } else {
      field.value = quantity;
    }
    field.dispatchEvent(new Event('input', { bubbles: true }));
    field.dispatchEvent(new Event('change', { bubbles: true }));
    return true;
  }

  function applyProductId(productId, quantity) {
    const janMatcher = /\d{8,}/;
    const itemCountMatcher = /(?<=item_cnt_)\d{8,}/;
    const stats = {
      name: replaceAttributeId('name', productId, itemCountMatcher),
      dataJancode: replaceAttributeId('data-jancode', productId, janMatcher),
      dataItemCode: replaceAttributeId('data-item-code', productId, janMatcher),
      href: replaceAttributeId('href', productId, /(?<=\/azonet\/item\/)\d{8,}/),
      action: replaceAttributeId('action', productId, /(?<=\/azonet\/item\/)\d{8,}/),
      quantitySet: false,
    };
    stats.quantitySet = applyQuantity(productId, quantity);

    const cartButton = document.querySelector(`button[data-jancode="${productId}"], input[data-jancode="${productId}"]`);
    if (cartButton) cartButton.dataset.azoneIdHelperMatched = 'true';

    return stats;
  }


  function findCheckoutButton() {
    const selectors = [
      'a[href*="checkout"]',
      'a[href*="order"]',
      'button[type="submit"]',
      'input[type="submit"]',
      '.btn-danger',
      '.btn-primary',
    ];
    for (const selector of selectors) {
      const element = Array.from(document.querySelectorAll(selector)).find((item) => {
        const label = item.value || item.textContent || item.getAttribute('title') || '';
        return label.includes('レジに進む') || label.includes('注文手続') || label.includes('購入手続');
      });
      if (element) return element;
    }
    return Array.from(document.querySelectorAll('a, button, input[type="button"], input[type="submit"]')).find((item) => {
      const label = item.value || item.textContent || item.getAttribute('title') || '';
      return label.includes('レジに進む');
    });
  }

  function clickCheckout() {
    const button = findCheckoutButton();
    if (!button) {
      return { clicked: false, message: '未找到“レジに進む”按钮。请确认当前页面是购物车页面。' };
    }
    button.click();
    return { clicked: true, message: '已点击“レジに進む”按钮。' };
  }

  function restoreOriginals() {
    let count = 0;
    document.querySelectorAll('*').forEach((element) => {
      const values = originalValues.get(element);
      if (!values) return;
      values.forEach((value, attribute) => {
        if (value === null) element.removeAttribute(attribute);
        else element.setAttribute(attribute, value);
        count += 1;
      });
    });
    return count;
  }

  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (message.type === 'AZONE_APPLY_PRODUCT_ID') {
      const stats = applyProductId(message.productId, message.quantity || '1');
      sendResponse({
        ok: true,
        message: [
          `已应用商品 ID：${message.productId}`,
          `数量：${message.quantity || '1'}${stats.quantitySet ? '（已设置）' : '（未找到数量框）'}`,
          `已替换 name：${stats.name} 个`,
          `已替换 data-jancode：${stats.dataJancode} 个`,
          `已替换 data-item-code：${stats.dataItemCode} 个`,
          `已替换 href/action：${stats.href + stats.action} 个`,
          '页面没有刷新或重新加载。',
        ].join('\n'),
      });
      return true;
    }


    if (message.type === 'AZONE_CLICK_CHECKOUT') {
      const result = clickCheckout();
      sendResponse({ ok: result.clicked, message: result.message });
      return true;
    }

    if (message.type === 'AZONE_RESTORE_ORIGINALS') {
      const count = restoreOriginals();
      sendResponse({ ok: true, message: `已恢复 ${count} 个属性。页面没有刷新或重新加载。` });
      return true;
    }

    return false;
  });
})();
