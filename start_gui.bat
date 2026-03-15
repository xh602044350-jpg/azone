@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo [1/4] 当前目录: %CD%
echo [2/4] 检查 Python...
python --version
if errorlevel 1 (
  echo.
  echo 未找到 Python。请先安装 Python 3.10+，并勾选 "Add python.exe to PATH"。
  pause
  exit /b 1
)

echo [3/4] 安装/检查依赖 Playwright...
python -m pip install -q playwright
if errorlevel 1 (
  echo.
  echo 依赖安装失败，请检查网络后重试。
  pause
  exit /b 1
)

echo [4/4] 启动 GUI...
python gui_app.py
if errorlevel 1 (
  echo.
  echo GUI 启动失败。常见原因：
  echo - Python 安装不完整
  echo - 缺少 tkinter 组件
  echo - 依赖未正确安装
)

echo.
echo 程序已结束。
pause
