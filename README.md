# Azone 自动下单脚本（Playwright）

这是一个**可配置**的自动下单流程脚本示例，目标站点：
`https://www.azone-int.co.jp/azonet/`

> 请在遵守网站服务条款和当地法律前提下使用。
> 建议开启 `dry_run: true` 先做流程验证，确认选择器无误后再真实提交。

## 功能

- 自动登录
- 打开商品页并加入购物车
- 进入结算并确认下单（可通过 `dry_run` 禁止最终提交）
- 支持设置开售时间点（`target_time`）

## 依赖

- Python 3.10+
- Playwright

安装：

```bash
pip install playwright
playwright install chromium
```

## 使用步骤

1. 复制并修改配置：

```bash
cp config.example.json config.json
```

2. 按网页实际元素更新 `config.json` 中 `selectors`。

3. 先用 `dry_run: true` 运行：

```bash
python auto_order.py --config config.json
```

4. 确认流程正确后将 `dry_run` 改为 `false`。



## GUI 图形界面


## 完全新手：怎么“在这个目录打开终端”

### Windows（推荐）
1. 先用资源管理器打开项目文件夹（你能看到 `README.md`、`gui_app.py` 这些文件）。
2. 在文件夹空白处按住 `Shift` + 鼠标右键。
3. 点击“在此处打开 PowerShell 窗口”（或“在终端中打开”）。
4. 打开后输入下面命令（每行回车一次）：

```bash
python -m pip install playwright
python -m playwright install chromium
python gui_app.py
```

### 看不到图形界面怎么办
- 先双击项目里的 `start_gui.bat`（我已新增），它会在常驻窗口中自动检查 Python/依赖并尝试启动 GUI，不会一闪而过。
- 如果仍启动失败，请把同目录 `start_gui.log` 最后 30 行发我，我可直接定位问题。
- 如果窗口里报错 `No module named tkinter`，说明你的 Python 没装 Tk 组件，需要重装 Python（勾选 tcl/tk 或安装官方完整版）。
- 如果报 `python 不是内部或外部命令`，说明没加 PATH，请重装 Python 并勾选 “Add python.exe to PATH”。

如果你不想在命令行里操作，可以直接使用桌面 GUI：

```bash
python gui_app.py
```

GUI 支持：
- 加载/保存 `config.json`
- 编辑商品链接、账号、开售时间、数量、并行刷新页数
- 勾选 `dry_run` 和 `validate-only`
- 点击按钮直接运行，并在窗口里查看日志

## 快速验证商品页选择器（推荐）

可先只验证商品页关键选择器是否匹配，而不执行登录/下单：

```bash
python auto_order.py --config config.json --validate-only
```

如果输出里某个选择器数量为 `0`，说明当前配置与页面不匹配，需要先更新 `selectors`。

## 关于选择器

`config.example.json` 里的选择器是示例值，站点结构如果变化，需要你自己在浏览器开发者工具中更新这些 CSS 选择器。

## 注意事项

- 建议先手动登录一次确认账号状态正常。
- 若站点启用图形验证码（CAPTCHA）或风控，脚本可能无法自动完成，需人工介入。
- 下单脚本存在误下单风险，请谨慎操作。


## 说明

- 我在当前环境验证了商品页 `https://www.azone-int.co.jp/azonet/item/4573199852218` 可以正常访问，并确认页面显示“在库状況：（準備中）”及“2026年3月19日よる0時予約受付開始”。
- 由于没有你的账号与支付/收货信息，本仓库脚本未进行真实下单提交验证。


## 对你这款商品（4573199852218）的关键结论

- 我能看到该页显示的销售时间信息：文案为“2026年3月19日よる0時予約受付開始”。
- 该商品在未到开售时间前不会出现加购按钮，这是正常现象。
- 脚本已增加“等待加购按钮出现”的轮询逻辑（默认最多 180 秒），更适合 00:00 开售场景。
- 脚本也新增了单地址单件限制校验（默认强制 `quantity = 1`）。

### 新增配置项

- `wait_for_cart_button_seconds`: 到达开售时间后，轮询等待“加入购物车”按钮出现的秒数（默认 `180`）。
- `enforce_single_quantity`: 是否强制 `quantity` 必须为 `1`（默认 `true`，用于“一个地址只能购买一个”的场景）。
- `cart_refresh_initial_interval_ms`: 刚到开售时的初始刷新间隔（毫秒，默认 `300`）。
- `cart_refresh_max_interval_ms`: 退避后的最大刷新间隔（毫秒，默认 `2000`）。
- `cart_refresh_backoff_multiplier`: 每次刷新后的间隔放大倍数（默认 `1.5`）。
- `cart_refresh_max_attempts`: 刷新次数上限（默认 `300`），避免无限刷新。
- `parallel_refresh_pages`: 并行刷新商品页数量（`1` 到 `6`，默认建议 `5`）。
- `multi_page_stagger_ms`: 多页面刷新时每页之间的错峰延迟（毫秒，默认 `80`），避免瞬时同频请求。


## 网站卡顿时的行为

- 脚本**不会无限不停刷新**。
- 达到 `wait_for_cart_button_seconds` 或 `cart_refresh_max_attempts` 任一上限就会停止并报错。
- 刷新间隔采用“指数退避 + 随机抖动”，减少开售高峰对站点的瞬时压力。

## 多页面并行刷新说明

- 支持同时开 `5~6` 个页面并行刷新（建议先用 `5`）。
- 一旦任意页面出现加购按钮，脚本会立刻使用命中页面继续并关闭其余页面。
- 依然受 `wait_for_cart_button_seconds` 与 `cart_refresh_max_attempts` 双上限保护，不会无限刷新。
