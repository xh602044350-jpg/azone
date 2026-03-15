#!/usr/bin/env python3
"""Simple GUI runner for Azone auto-order script."""

from __future__ import annotations

import json
import subprocess
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Azone 自动下单 GUI")
        self.config_path = tk.StringVar(value="config.json")

        self.product_url = tk.StringVar()
        self.email = tk.StringVar()
        self.password = tk.StringVar()
        self.target_time = tk.StringVar()
        self.quantity = tk.StringVar(value="1")
        self.dry_run = tk.BooleanVar(value=True)
        self.validate_only = tk.BooleanVar(value=True)
        self.parallel_refresh_pages = tk.StringVar(value="5")

        self._build_ui()

    def _build_ui(self) -> None:
        frm = ttk.Frame(self.root, padding=12)
        frm.grid(sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        frm.columnconfigure(1, weight=1)

        row = 0
        ttk.Label(frm, text="配置文件").grid(row=row, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.config_path).grid(row=row, column=1, sticky="ew", padx=4)
        ttk.Button(frm, text="选择", command=self.choose_config).grid(row=row, column=2)
        ttk.Button(frm, text="加载", command=self.load_config).grid(row=row, column=3, padx=4)

        row += 1
        ttk.Label(frm, text="商品链接").grid(row=row, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.product_url).grid(row=row, column=1, columnspan=3, sticky="ew", padx=4)

        row += 1
        ttk.Label(frm, text="账号邮箱").grid(row=row, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.email).grid(row=row, column=1, columnspan=3, sticky="ew", padx=4)

        row += 1
        ttk.Label(frm, text="账号密码").grid(row=row, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.password, show="*").grid(row=row, column=1, columnspan=3, sticky="ew", padx=4)

        row += 1
        ttk.Label(frm, text="开售时间(可空)").grid(row=row, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.target_time).grid(row=row, column=1, columnspan=3, sticky="ew", padx=4)

        row += 1
        ttk.Label(frm, text="数量").grid(row=row, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.quantity).grid(row=row, column=1, sticky="w", padx=4)
        ttk.Label(frm, text="并行刷新页数(1-6)").grid(row=row, column=2, sticky="e")
        ttk.Entry(frm, textvariable=self.parallel_refresh_pages, width=8).grid(row=row, column=3, sticky="w")

        row += 1
        ttk.Checkbutton(frm, text="dry_run（不提交最终订单）", variable=self.dry_run).grid(row=row, column=0, columnspan=2, sticky="w")
        ttk.Checkbutton(frm, text="validate-only（仅验证选择器）", variable=self.validate_only).grid(row=row, column=2, columnspan=2, sticky="w")

        row += 1
        btns = ttk.Frame(frm)
        btns.grid(row=row, column=0, columnspan=4, sticky="ew", pady=(8, 0))
        ttk.Button(btns, text="保存配置", command=self.save_config).pack(side="left")
        ttk.Button(btns, text="运行脚本", command=self.run_script).pack(side="left", padx=8)

        row += 1
        self.log_text = tk.Text(frm, height=16)
        self.log_text.grid(row=row, column=0, columnspan=4, sticky="nsew", pady=(8, 0))
        frm.rowconfigure(row, weight=1)

    def choose_config(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json"), ("All", "*.*")])
        if path:
            self.config_path.set(path)

    def load_config(self) -> None:
        path = Path(self.config_path.get())
        if not path.exists():
            messagebox.showerror("错误", f"配置文件不存在: {path}")
            return
        data = json.loads(path.read_text(encoding="utf-8"))
        self.product_url.set(data.get("product_url", ""))
        self.email.set(data.get("email", ""))
        self.password.set(data.get("password", ""))
        self.target_time.set(data.get("target_time") or "")
        self.quantity.set(str(data.get("quantity", 1)))
        self.dry_run.set(bool(data.get("dry_run", True)))
        self.parallel_refresh_pages.set(str(data.get("parallel_refresh_pages", 5)))
        self._log(f"已加载配置: {path}")

    def save_config(self) -> None:
        path = Path(self.config_path.get())
        if not path.exists():
            if not messagebox.askyesno("提示", f"配置文件不存在，是否新建？\n{path}"):
                return
            base = Path("config.example.json")
            if base.exists():
                path.write_text(base.read_text(encoding="utf-8"), encoding="utf-8")
            else:
                path.write_text("{}\n", encoding="utf-8")

        data = json.loads(path.read_text(encoding="utf-8"))
        data["product_url"] = self.product_url.get().strip()
        data["email"] = self.email.get().strip()
        data["password"] = self.password.get()
        data["target_time"] = self.target_time.get().strip() or None
        data["quantity"] = int(self.quantity.get())
        data["dry_run"] = bool(self.dry_run.get())
        data["parallel_refresh_pages"] = int(self.parallel_refresh_pages.get())

        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self._log(f"已保存配置: {path}")

    def run_script(self) -> None:
        try:
            self.save_config()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("错误", f"保存配置失败: {exc}")
            return

        cmd = [sys.executable, "auto_order.py", "--config", self.config_path.get()]
        if self.validate_only.get():
            cmd.append("--validate-only")

        self._log("执行命令: " + " ".join(cmd))
        threading.Thread(target=self._run_command, args=(cmd,), daemon=True).start()

    def _run_command(self, cmd: list[str]) -> None:
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if proc.stdout:
                self._log(proc.stdout)
            if proc.stderr:
                self._log(proc.stderr)
            self._log(f"退出码: {proc.returncode}")
        except Exception as exc:  # noqa: BLE001
            self._log(f"执行失败: {exc}")

    def _log(self, message: str) -> None:
        self.log_text.insert("end", message.rstrip() + "\n")
        self.log_text.see("end")


def main() -> None:
    root = tk.Tk()
    App(root)
    root.geometry("900x620")
    root.mainloop()


if __name__ == "__main__":
    main()
