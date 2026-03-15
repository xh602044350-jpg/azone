#!/usr/bin/env python3
"""A configurable auto-order workflow for https://www.azone-int.co.jp/azonet/.

Use responsibly and only in compliance with the website's terms.
"""

from __future__ import annotations

import argparse
import json
import random
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from playwright.sync_api import BrowserContext, Page, sync_playwright


@dataclass
class WorkflowConfig:
    base_url: str
    login_url: str
    product_url: str
    email: str
    password: str
    selectors: dict[str, str]
    launch_headless: bool = True
    slow_mo_ms: int = 0
    timeout_ms: int = 10_000
    quantity: int = 1
    target_time: str | None = None
    dry_run: bool = False
    wait_for_cart_button_seconds: int = 120
    enforce_single_quantity: bool = True
    cart_refresh_initial_interval_ms: int = 300
    cart_refresh_max_interval_ms: int = 2_000
    cart_refresh_backoff_multiplier: float = 1.5
    cart_refresh_max_attempts: int = 300
    parallel_refresh_pages: int = 1
    multi_page_stagger_ms: int = 80


def load_config(path: Path) -> WorkflowConfig:
    data = json.loads(path.read_text(encoding="utf-8"))
    return WorkflowConfig(
        base_url=data["base_url"],
        login_url=data["login_url"],
        product_url=data["product_url"],
        email=data["email"],
        password=data["password"],
        selectors=data["selectors"],
        launch_headless=data.get("launch_headless", True),
        slow_mo_ms=data.get("slow_mo_ms", 0),
        timeout_ms=data.get("timeout_ms", 10_000),
        quantity=data.get("quantity", 1),
        target_time=data.get("target_time"),
        dry_run=data.get("dry_run", False),
        wait_for_cart_button_seconds=data.get("wait_for_cart_button_seconds", 120),
        enforce_single_quantity=data.get("enforce_single_quantity", True),
        cart_refresh_initial_interval_ms=data.get("cart_refresh_initial_interval_ms", 300),
        cart_refresh_max_interval_ms=data.get("cart_refresh_max_interval_ms", 2_000),
        cart_refresh_backoff_multiplier=data.get("cart_refresh_backoff_multiplier", 1.5),
        cart_refresh_max_attempts=data.get("cart_refresh_max_attempts", 300),
        parallel_refresh_pages=data.get("parallel_refresh_pages", 1),
        multi_page_stagger_ms=data.get("multi_page_stagger_ms", 80),
    )



def validate_business_rules(cfg: WorkflowConfig) -> None:
    if cfg.enforce_single_quantity and cfg.quantity != 1:
        raise ValueError("该商品规则为单地址限购 1 件，请将 quantity 设置为 1。")
    if cfg.cart_refresh_initial_interval_ms <= 0:
        raise ValueError("cart_refresh_initial_interval_ms 必须大于 0。")
    if cfg.cart_refresh_max_interval_ms < cfg.cart_refresh_initial_interval_ms:
        raise ValueError("cart_refresh_max_interval_ms 不能小于 cart_refresh_initial_interval_ms。")
    if cfg.cart_refresh_backoff_multiplier < 1.0:
        raise ValueError("cart_refresh_backoff_multiplier 不能小于 1.0。")
    if cfg.cart_refresh_max_attempts <= 0:
        raise ValueError("cart_refresh_max_attempts 必须大于 0。")
    if not 1 <= cfg.parallel_refresh_pages <= 6:
        raise ValueError("parallel_refresh_pages 必须在 1 到 6 之间。")
    if cfg.multi_page_stagger_ms < 0:
        raise ValueError("multi_page_stagger_ms 不能小于 0。")


def wait_until(target_time: str) -> None:
    target = datetime.fromisoformat(target_time)
    while True:
        now = datetime.now()
        if now >= target:
            return
        seconds_left = (target - now).total_seconds()
        sleep_for = min(seconds_left, 0.25)
        time.sleep(max(sleep_for, 0.01))


def login(page: Page, cfg: WorkflowConfig) -> None:
    s = cfg.selectors
    page.goto(cfg.login_url, wait_until="domcontentloaded")
    assert_selector(page, s["email_input"], "email_input")
    assert_selector(page, s["password_input"], "password_input")
    assert_selector(page, s["login_button"], "login_button")
    page.fill(s["email_input"], cfg.email)
    page.fill(s["password_input"], cfg.password)
    page.click(s["login_button"])
    page.wait_for_load_state("networkidle")


def add_product_to_cart(page: Page, cfg: WorkflowConfig) -> Page:
    s = cfg.selectors
    page.goto(cfg.product_url, wait_until="domcontentloaded")
    active_page = wait_for_selector_after_sale_time(
        page,
        cfg.product_url,
        s["add_to_cart_button"],
        timeout_seconds=cfg.wait_for_cart_button_seconds,
        initial_interval_ms=cfg.cart_refresh_initial_interval_ms,
        max_interval_ms=cfg.cart_refresh_max_interval_ms,
        backoff_multiplier=cfg.cart_refresh_backoff_multiplier,
        max_attempts=cfg.cart_refresh_max_attempts,
        parallel_pages=cfg.parallel_refresh_pages,
        per_page_stagger_ms=cfg.multi_page_stagger_ms,
    )
    if cfg.quantity > 1 and "quantity_input" in s:
        assert_selector(active_page, s["quantity_input"], "quantity_input")
        active_page.fill(s["quantity_input"], str(cfg.quantity))
    active_page.click(s["add_to_cart_button"])
    active_page.wait_for_load_state("networkidle")
    return active_page


def checkout(page: Page, cfg: WorkflowConfig) -> None:
    s = cfg.selectors
    if cfg.dry_run:
        print("[DRY RUN] 跳过真实下单提交，只执行到确认页面。")
        return

    assert_selector(page, s["go_to_checkout_button"], "go_to_checkout_button")
    page.click(s["go_to_checkout_button"])
    page.wait_for_load_state("networkidle")

    if "agree_terms_checkbox" in s:
        assert_selector(page, s["agree_terms_checkbox"], "agree_terms_checkbox")
        page.check(s["agree_terms_checkbox"])

    assert_selector(page, s["confirm_order_button"], "confirm_order_button")
    page.click(s["confirm_order_button"])
    page.wait_for_load_state("networkidle")
    print("下单流程已提交，请立即人工确认订单状态。")



def wait_for_selector_after_sale_time(
    page: Page,
    product_url: str,
    selector: str,
    timeout_seconds: int,
    initial_interval_ms: int,
    max_interval_ms: int,
    backoff_multiplier: float,
    max_attempts: int,
    parallel_pages: int,
    per_page_stagger_ms: int,
) -> Page:
    deadline = datetime.now() + timedelta(seconds=timeout_seconds)
    attempt = 0
    interval_seconds = initial_interval_ms / 1000
    max_interval_seconds = max_interval_ms / 1000

    pages = [page]
    for _ in range(parallel_pages - 1):
        extra_page = page.context.new_page()
        extra_page.goto(product_url, wait_until="domcontentloaded")
        pages.append(extra_page)

    print(f"并行刷新页数量: {len(pages)}")

    while datetime.now() < deadline and attempt < max_attempts:
        for idx, candidate in enumerate(pages, start=1):
            if candidate.locator(selector).count() > 0:
                print(f"加购按钮已出现，刷新次数: {attempt}，命中页: {idx}")
                for p in pages:
                    if p != candidate:
                        p.close()
                return candidate

        attempt += 1
        for idx, candidate in enumerate(pages, start=1):
            try:
                candidate.reload(wait_until="domcontentloaded")
            except Exception as exc:  # noqa: BLE001
                print(f"第 {attempt} 次刷新异常(页 {idx})，将退避后重试: {exc}")

            if per_page_stagger_ms > 0:
                time.sleep(per_page_stagger_ms / 1000)

        sleep_seconds = min(interval_seconds, max_interval_seconds)
        jitter = random.uniform(0, min(0.2, sleep_seconds * 0.3))
        time.sleep(sleep_seconds + jitter)
        interval_seconds = min(interval_seconds * backoff_multiplier, max_interval_seconds)

    for p in pages:
        if not p.is_closed():
            p.close()
    raise RuntimeError(
        "等待加购按钮超时或达到最大刷新次数。\n"
        f"商品页：{product_url}\n"
        f"选择器：{selector}\n"
        f"已刷新：{attempt} 次\n"
        f"等待上限：{timeout_seconds} 秒，刷新上限：{max_attempts} 次"
    )


def assert_selector(page: Page, selector: str, selector_name: str) -> None:
    if page.locator(selector).count() == 0:
        raise RuntimeError(
            f"未找到选择器 {selector_name}: {selector}\n"
            "请先在浏览器开发者工具确认页面元素，再更新配置文件中的 selectors。"
        )


def validate_product_page(page: Page, cfg: WorkflowConfig) -> None:
    print(f"验证商品页: {cfg.product_url}")
    page.goto(cfg.product_url, wait_until="networkidle")
    for key in ("add_to_cart_button", "quantity_input", "go_to_checkout_button"):
        selector = cfg.selectors.get(key)
        if not selector:
            print(f"[SKIP] 未配置 {key}")
            continue
        count = page.locator(selector).count()
        print(f"[{key}] {selector} -> {count} 个元素")


def build_context(cfg: WorkflowConfig) -> BrowserContext:
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=cfg.launch_headless, slow_mo=cfg.slow_mo_ms)
    context = browser.new_context(base_url=cfg.base_url)

    original_close = context.close

    def close_with_browser() -> None:
        original_close()
        browser.close()
        playwright.stop()

    context.close = close_with_browser  # type: ignore[method-assign]
    return context


def run(cfg: WorkflowConfig, *, validate_only: bool = False) -> None:
    validate_business_rules(cfg)
    if cfg.target_time:
        print(f"等待到目标时间: {cfg.target_time}")
        wait_until(cfg.target_time)

    context = build_context(cfg)
    context.set_default_timeout(cfg.timeout_ms)
    page = context.new_page()

    try:
        if validate_only:
            validate_product_page(page, cfg)
            return
        login(page, cfg)
        page = add_product_to_cart(page, cfg)
        checkout(page, cfg)
    finally:
        context.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Azone 自动下单脚本（Playwright）")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.example.json"),
        help="配置文件路径（JSON）。",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="仅验证商品页关键选择器，不执行登录/下单流程。",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)
    run(cfg, validate_only=args.validate_only)


if __name__ == "__main__":
    main()
