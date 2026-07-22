# Azone 商品 ID 替换助手（Chrome 插件）

这是一个 Chrome 扩展程序，用来在已打开的 Azone 商品页里直接替换加购区域的商品 ID/JAN 码。

目标场景：你打开例如：

```text
https://www.azone-int.co.jp/azonet/item/4573199845111
```

然后在插件弹窗里输入你想要的商品 ID，例如：

```text
4573199843124
```

插件会在**当前页面 DOM 内**把截图中这类位置替换成目标 ID：

- `select name="item_cnt_4573199845111"` → `select name="item_cnt_4573199843124"`
- `button data-jancode="4573199845111"` → `button data-jancode="4573199843124"`
- 如页面里存在指向 `/azonet/item/<商品ID>` 的 `href` 或 `action`，也会同步替换

> 重点：插件不会刷新页面，不会重新加载页面，也不会循环刷新，避免网络卡顿。

## 安装 Chrome 插件

1. 打开 Chrome：`chrome://extensions/`
2. 打开右上角「开发者模式」
3. 点击「加载已解压的扩展程序」
4. 选择本仓库里的 `chrome_extension` 文件夹
5. 打开 Azone 商品页后，点击浏览器右上角插件图标

## 使用方法

1. 打开 Azone 商品页，例如：

```text
https://www.azone-int.co.jp/azonet/item/4573199845111
```

2. 点击插件图标。
3. 在「目标商品 ID / JAN 码」中输入你要替换成的 ID，例如 `4573199843124`。
4. 输入数量，默认 `1`。
5. 点击「替换ID」：只替换当前页面里的 ID/JAN，不刷新页面。
6. 点击「自动添加购物车并去结算」：插件会先替换 ID，再点击商品页的“カート/購物車”按钮；随后会快速进入购物车并自动点击右下角的“レジに進む / 進行結算”按钮。

插件界面只有这两个主要按钮：一个用于替换 ID，另一个用于自动加购并跳转结算。

## 插件做了什么

插件包含三个核心文件：

- `chrome_extension/manifest.json`：Chrome Manifest V3 配置，限制只在 `https://www.azone-int.co.jp/azonet/*` 页面生效。
- `chrome_extension/popup.html` / `popup.js`：提供输入商品 ID 和数量，以及「替换ID」「自动添加购物车并去结算」两个按钮。
- `chrome_extension/content.js`：在当前页面内替换 DOM 属性，点击商品页加购按钮，并在购物车页查找/点击“レジに進む / 進行結算”按钮；替换 ID 时不调用 `location.reload()`，也不执行页面刷新。

## 注意事项

- 请在遵守网站服务条款和当地法律前提下使用。
- 插件只负责替换当前页面里已有的 DOM 属性；如果页面本身没有加购按钮或数量框，插件不会通过刷新去等待它出现。
- 「自动添加购物车并去结算」会按你的点击主动发生页面跳转；为减少等待，插件点击加购后只短暂等待，然后直接进入购物车并高频尝试点击结算按钮。
- 如果 Azone 后续修改了页面结构，可能需要调整 `content.js` 中的匹配规则。

## 旧版脚本说明

仓库中仍保留 `auto_order.py`、`gui_app.py` 和 `config.example.json`，用于之前的 Playwright 自动化方案；但如果你的需求是「Chrome 插件方式」并且「不要刷新和重新加载页面」，请使用 `chrome_extension` 目录中的插件。
