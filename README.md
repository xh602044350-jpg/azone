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
5. 点击「应用到当前页面」。
6. 插件会显示替换了多少个属性，并确认「页面没有刷新或重新加载」。
7. 商品加入购物车后，可点击插件里的「跳转购物车」打开 `https://www.azone-int.co.jp/azonet/cart`。
8. 在购物车页面可点击「点击“レジに進む”」，插件会尝试点击购物车页右下角的结算按钮。

如果想撤销本页 DOM 属性修改，可以点击「恢复本页原始值」。

## 插件做了什么

插件包含三个核心文件：

- `chrome_extension/manifest.json`：Chrome Manifest V3 配置，限制只在 `https://www.azone-int.co.jp/azonet/*` 页面生效。
- `chrome_extension/popup.html` / `popup.js`：提供输入商品 ID 和数量、跳转购物车、点击“レジに進む”的 UI，并把指令发送给当前标签页。
- `chrome_extension/content.js`：在当前页面内替换 DOM 属性，并在购物车页查找/点击“レジに進む”按钮；替换 ID 时不调用 `location.reload()`，也不执行页面刷新。

## 注意事项

- 请在遵守网站服务条款和当地法律前提下使用。
- 插件只负责替换当前页面里已有的 DOM 属性；如果页面本身没有加购按钮或数量框，插件不会通过刷新去等待它出现。
- 「跳转购物车」是你主动点击后的页面跳转；商品 ID 替换本身仍然不会刷新或重新加载页面。
- 如果 Azone 后续修改了页面结构，可能需要调整 `content.js` 中的匹配规则。

## 旧版脚本说明

仓库中仍保留 `auto_order.py`、`gui_app.py` 和 `config.example.json`，用于之前的 Playwright 自动化方案；但如果你的需求是「Chrome 插件方式」并且「不要刷新和重新加载页面」，请使用 `chrome_extension` 目录中的插件。
