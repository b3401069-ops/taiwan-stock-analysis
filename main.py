"""
台灣股票分析工具 - 主程式
"""
import uvicorn
import json
import math
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
from loguru import logger
import sys

# 導入配置
from config.config import get_settings

# 導入API路由
from api.routes import router as api_router


# 配置日誌
def setup_logging():
    """設置日誌配置"""
    settings = get_settings()
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.LOG_LEVEL
    )
    logger.add(
        "logs/app.log",
        rotation="500 MB",
        retention="10 days",
        compression="zip",
        level=settings.LOG_LEVEL
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用生命週期管理"""
    # 啟動時執行
    logger.info("正在啟動台灣股票分析工具...")
    
    # 初始化資料庫連接
    # 初始化快取連接
    # 初始化券商API連接
    
    # 啟動排程服務
    from services.scheduler import get_scheduler_service
    scheduler = get_scheduler_service()
    scheduler.start()
    
    logger.info("台灣股票分析工具啟動完成")
    
    yield
    
    # 關閉時執行
    logger.info("正在關閉台灣股票分析工具...")
    
    # 停止排程服務
    scheduler.stop()
    
    # 關閉資料庫連接
    # 關閉快取連接
    
    logger.info("台灣股票分析工具已關閉")


class NanSafeJSONResponse(JSONResponse):
    """自定義 JSON 回應，處理 NaN/Inf 值"""
    def render(self, content) -> bytes:
        sanitized = _sanitize_for_json(content)
        return json.dumps(
            sanitized,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            default=str
        ).encode("utf-8")


def _sanitize_for_json(obj):
    """遞迴清理數據中的 NaN/Inf 值"""
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_sanitize_for_json(v) for v in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, (np.floating, np.integer)):
        if isinstance(obj, np.floating) and (np.isnan(obj) or np.isinf(obj)):
            return None
        return float(obj)
    return obj


# 創建FastAPI應用
def create_app() -> FastAPI:
    """創建FastAPI應用實例"""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="台灣股票分析工具 - 支援多券商API、機器學習預測、AI Agent整合",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
        default_response_class=NanSafeJSONResponse
    )
    
    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 在生產環境中應該限制來源
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 添加清理 NaN 的中間件
    @app.middleware("http")
    async def sanitize_response(request, call_next):
        response = await call_next(request)
        # 只處理 JSON 回應
        if response.headers.get("content-type", "").startswith("application/json"):
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            try:
                data = json.loads(body)
                sanitized = _sanitize_for_json(data)
                return NanSafeJSONResponse(content=sanitized, status_code=response.status_code)
            except (json.JSONDecodeError, UnicodeDecodeError):
                return response
        return response

    # 添加API路由
    app.include_router(api_router, prefix="/api/v1")

    # 掛載靜態文件
    import os
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # 添加健康檢查端點
    @app.get("/health")
    async def health_check():
        """健康檢查端點"""
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION
        }
    
    # 添加前端頁面
    @app.get("/app", response_class=HTMLResponse)
    async def frontend():
        """前端頁面"""
        index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        return HTMLResponse(content="<h1>前端文件不存在</h1>")
    
    # 添加聊天頁面
    @app.get("/chat", response_class=HTMLResponse)
    async def chat_page():
        """AI 聊天分析師頁面"""
        chat_path = os.path.join(os.path.dirname(__file__), "static", "chat.html")
        if os.path.exists(chat_path):
            with open(chat_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        return HTMLResponse(content="<h1>聊天頁面不存在</h1>")
    
    # 添加測試頁面
    @app.get("/test", response_class=HTMLResponse)
    async def test_page():
        """API 測試頁面"""
        test_path = os.path.join(os.path.dirname(__file__), "static", "test.html")
        if os.path.exists(test_path):
            with open(test_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        return HTMLResponse(content="<h1>測試頁面不存在</h1>")
    
    # 添加倉位頁面
    @app.get("/portfolio", response_class=HTMLResponse)
    async def portfolio_page():
        """虛擬倉位管理頁面"""
        portfolio_path = os.path.join(os.path.dirname(__file__), "static", "portfolio.html")
        if os.path.exists(portfolio_path):
            with open(portfolio_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        return HTMLResponse(content="<h1>倉位頁面不存在</h1>")
    
    # 添加報告頁面
    @app.get("/report", response_class=HTMLResponse)
    async def report_page():
        """股票研究報告頁面"""
        report_path = os.path.join(os.path.dirname(__file__), "static", "report.html")
        if os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        return HTMLResponse(content="<h1>報告頁面不存在</h1>")
    
    # 添加排程頁面
    @app.get("/scheduler", response_class=HTMLResponse)
    async def scheduler_page():
        """排程管理頁面"""
        scheduler_path = os.path.join(os.path.dirname(__file__), "static", "scheduler.html")
        if os.path.exists(scheduler_path):
            with open(scheduler_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        return HTMLResponse(content="<h1>排程頁面不存在</h1>")
    
    # 添加多因子選股測試頁面
    @app.get("/screener", response_class=HTMLResponse)
    async def screener_page():
        """多因子選股測試頁面"""
        screener_path = os.path.join(os.path.dirname(__file__), "static", "screener_test.html")
        if os.path.exists(screener_path):
            with open(screener_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        return HTMLResponse(content="<h1>多因子選股頁面不存在</h1>")

    # 添加根端點
    @app.get("/")
    async def root():
        """根端點"""
        return {
            "message": "歡迎使用台灣股票分析工具",
            "docs": "/docs",
            "health": "/health",
            "app": "/app",
            "chat": "/chat",
            "test": "/test",
            "portfolio": "/portfolio",
            "report": "/report",
            "scheduler": "/scheduler",
            "screener": "/screener",
            "api": "/api/v1"
        }
    
    return app


# 創建應用實例
app = create_app()


if __name__ == "__main__":
    # 設置日誌
    setup_logging()
    
    # 獲取配置
    settings = get_settings()
    
    # 設定端口（避免常用端口衝突）
    port = 9999
    
    # 自動開啟瀏覽器
    import webbrowser
    import threading
    
    def open_browser():
        """延遲開啟瀏覽器"""
        import time
        time.sleep(2)  # 等待伺服器啟動
        webbrowser.open(f"http://localhost:{port}/app")
        logger.info(f"已開啟瀏覽器: http://localhost:{port}/app")
    
    # 在背景執行緒開啟瀏覽器
    if not settings.DEBUG:  # 非 debug 模式才自動開啟
        threading.Thread(target=open_browser, daemon=True).start()
    
    logger.info(f"啟動台灣股票分析工具...")
    logger.info(f"API 文件: http://localhost:{port}/docs")
    logger.info(f"前端頁面: http://localhost:{port}/app")
    
    # 啟動應用
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )