@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

set "LOG_FILE=%~dp0start_gui.log"
title Azone GUI Launcher

echo.
echo === Azone GUI 启动器 ===
echo 当前目录: %CD%
echo 日志文件: %LOG_FILE%
echo.

call :log "==== 启动时间: %date% %time% ===="
call :log "当前目录: %CD%"

echo [1/4] 检查 Python...
python --version
python --version >> "%LOG_FILE%" 2>&1
if errorlevel 1 goto :python_missing

echo [2/4] 安装/检查依赖 Playwright...
python -m pip install playwright >> "%LOG_FILE%" 2>&1
if errorlevel 1 goto :pip_failed

echo [3/4] 安装/检查 Chromium...
python -m playwright install chromium >> "%LOG_FILE%" 2>&1
if errorlevel 1 goto :chromium_failed

echo [4/4] 启动 GUI...
python gui_app.py >> "%LOG_FILE%" 2>&1
if errorlevel 1 goto :gui_failed

echo GUI 已正常关闭。
call :log "GUI 正常退出"
goto :done

:python_missing
echo.
echo [错误] 未找到 Python。
echo 请安装 Python 3.10+，并勾选 "Add python.exe to PATH"。
call :log "错误: python --version 失败"
goto :done

:pip_failed
echo.
echo [错误] Playwright 依赖安装失败，请检查网络或 Python 环境。
call :log "错误: pip install playwright 失败"
goto :done

:chromium_failed
echo.
echo [错误] Chromium 安装失败，请检查网络后重试。
call :log "错误: playwright install chromium 失败"
goto :done

:gui_failed
echo.
echo [错误] GUI 启动失败。常见原因：
echo - Python 安装不完整
echo - 缺少 tkinter 组件
echo - 环境权限或依赖异常
call :log "错误: gui_app.py 退出码 %errorlevel%"
goto :done

:done
call :log "==== 结束时间: %date% %time% ===="
echo.
echo 详细日志已写入: %LOG_FILE%
echo 按任意键关闭窗口...
pause >nul
exit /b

:log
echo [%date% %time%] %~1>> "%LOG_FILE%"
exit /b
