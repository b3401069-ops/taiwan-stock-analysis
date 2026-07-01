#!/bin/bash
# 台灣股票分析工具 - 啟動腳本
# 同時啟動 FastAPI 主伺服器和 Streamlit 儀表板

echo "=========================================="
echo "台灣股票分析工具 - 啟動中..."
echo "=========================================="

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 檢查 Python 是否安裝
if ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Python 未安裝，請先安裝 Python${NC}"
    exit 1
fi

# 檢查 Streamlit 是否安裝
if ! command -v streamlit &> /dev/null; then
    echo -e "${YELLOW}⚠️  Streamlit 未安裝，正在安裝...${NC}"
    pip install streamlit plotly
fi

# 建立日誌目錄
mkdir -p logs

# 啟動 FastAPI 主伺服器（背景執行）
echo -e "${GREEN}🚀 啟動 FastAPI 主伺服器 (端口 9999)...${NC}"
python main.py > logs/server.log 2>&1 &
SERVER_PID=$!

# 等待伺服器啟動
sleep 3

# 啟動 Streamlit 儀表板（背景執行）
echo -e "${GREEN}🚀 啟動 Streamlit 儀表板 (端口 8501)...${NC}"
streamlit run streamlit_app.py --server.port 8501 --server.headless true > logs/streamlit.log 2>&1 &
STREAMLIT_PID=$!

# 等待 Streamlit 啟動
sleep 3

echo ""
echo "=========================================="
echo -e "${GREEN}✅ 啟動完成！${NC}"
echo "=========================================="
echo ""
echo "📊 存取方式:"
echo "  • 主介面:      http://localhost:9999/app"
echo "  • Streamlit:   http://localhost:9999/dashboard"
echo "  • API 文件:    http://localhost:9999/docs"
echo "  • 直接存取:    http://localhost:8501"
echo ""
echo "📋 常用命令:"
echo "  • CLI 工具:    python cli.py --help"
echo "  • 查看日誌:    tail -f logs/server.log"
echo ""
echo "🛑 停止服務:"
echo "  • 按 Ctrl+C 或執行: kill $SERVER_PID $STREAMLIT_PID"
echo ""

# 捕捉 Ctrl+C 信號
trap "echo -e '${YELLOW}正在停止服務...${NC}'; kill $SERVER_PID $STREAMLIT_PID 2>/dev/null; echo -e '${GREEN}✅ 服務已停止${NC}'; exit 0" INT TERM

# 等待背景程序
wait
