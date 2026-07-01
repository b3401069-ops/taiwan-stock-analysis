@echo off
REM 台灣股票分析工具 - 啟動腳本 (Windows)
REM 同時啟動 FastAPI 主伺服器和 Streamlit 儀表板

echo ==========================================
echo 台灣股票分析工具 - 啟動中...
echo ==========================================

REM 檢查 Python 是否安裝
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 未安裝，請先安裝 Python
    pause
    exit /b 1
)

REM 檢查 Streamlit 是否安裝
streamlit --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Streamlit 未安裝，正在安裝...
    pip install streamlit plotly
)

REM 建立日誌目錄
if not exist logs mkdir logs

REM 啟動 FastAPI 主伺服器（背景執行）
echo 🚀 啟動 FastAPI 主伺服器 (端口 9999)...
start /B python main.py > logs\server.log 2>&1

REM 等待伺服器啟動
timeout /t 3 /nobreak >nul

REM 啟動 Streamlit 儀表板（背景執行）
echo 🚀 啟動 Streamlit 儀表板 (端口 8501)...
start /B streamlit run streamlit_app.py --server.port 8501 --server.headless true > logs\streamlit.log 2>&1

REM 等待 Streamlit 啟動
timeout /t 3 /nobreak >nul

echo.
echo ==========================================
echo ✅ 啟動完成！
echo ==========================================
echo.
echo 📊 存取方式:
echo   • 主介面:      http://localhost:9999/app
echo   • Streamlit:   http://localhost:9999/dashboard
echo   • API 文件:    http://localhost:9999/docs
echo   • 直接存取:    http://localhost:8501
echo.
echo 📋 常用命令:
echo   • CLI 工具:    python cli.py --help
echo   • 查看日誌:    type logs\server.log
echo.
echo 🛑 停止服務:
echo   • 按 Ctrl+C 或關閉此視窗
echo.

REM 開啟瀏覽器
start http://localhost:9999/app

pause
