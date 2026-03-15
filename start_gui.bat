@echo off
setlocal

:: 防止双击后一闪而过：自动在 /k 常驻窗口中重启自身
if /i "%~1" neq "KEEP" (
  start "Azone GUI Launcher" cmd /k "\"%~f0\" KEEP"
  exit /b
)

chcp 65001 >nul
cd /d "%~dp0"
set "LOG_FILE=%~dp0start_gui.log"

call :log "==== 启动时间: %date% %time% ===="
call :log "当前目录: %CD%"

echo [1/4] 检查 Python...
python --version >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
  echo 未找到 Python。请先安装 Python 3.10+ 并勾选 Add python.exe to PATH。
  call :log "错误: python --version 失败"
  goto :end
)

echo [2/4] 安装/检查依赖 Playwright...
python -m pip install -q playwright >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
  echo 依赖安装失败，请检查网络后重试。
  call :log "错误: pip install playwright 失败"
  goto :end
)

echo [3/4] 检查浏览器内核（Chromium）...
python -m playwright install chromium >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
  echo Chromium 安装失败，请检查网络后重试。
  call :log "错误: playwright install chromium 失败"
  goto :end
)

echo [4/4] 启动 GUI...
python gui_app.py >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
  echo GUI 启动失败。常见原因：
  echo - Python 安装不完整
  echo - 缺少 tkinter 组件
  echo - 依赖未正确安装
  call :log "错误: gui_app.py 退出码 %errorlevel%"
) else (
  call :log "GUI 正常退出"
)

:end
echo.
echo 已写入日志: %LOG_FILE%
call :log "==== 结束时间: %date% %time% ===="

:: 使用 cmd /k 打开的窗口会保持，不需要 pause
exit /b

:log
echo [%date% %time%] %~1>> "%LOG_FILE%"
exit /b
