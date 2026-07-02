"""
富邦證券 SDK 獨立服務
在有 fubon_sdk 的電腦上執行，提供 HTTP API 給 OpenClaw Agent 調用
回傳格式：JSON

使用方式:
1. 在有富邦 SDK 的電腦上執行: python fubon_service.py
2. OpenClaw Agent 透過 HTTP 調用此服務
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

# 嘗試導入富邦 SDK
try:
    from fubon_sdk.constant import MarketType, OrderType, PriceType, TimeInForce
    from fubon_sdk.sdk import FubonSDK

    FUBON_AVAILABLE = True
except ImportError:
    FUBON_AVAILABLE = False
    logger.warning("fubon_sdk 未安裝，請先安裝: pip install fubon-sdk")


# ──────────────────────────────────────────────
#  配置
# ──────────────────────────────────────────────

# 從環境變數讀取配置
import os

API_KEY = os.getenv("FUBON_API_KEY", "")
API_SECRET = os.getenv("FUBON_API_SECRET", "")
ACCOUNT = os.getenv("FUBON_ACCOUNT", "")
PORT = int(os.getenv("FUBON_SERVICE_PORT", "8081"))


# ──────────────────────────────────────────────
#  富邦 SDK 封裝
# ──────────────────────────────────────────────


class FubonService:
    """富邦 SDK 服務封裝"""

    def __init__(self):
        self.sdk = None
        self.connected = False
        self._connect()

    def _connect(self):
        """連接富邦 API"""
        if not FUBON_AVAILABLE:
            logger.error("fubon_sdk 未安裝")
            return

        if not API_KEY or not API_SECRET:
            logger.error("未設定 FUBON_API_KEY 或 FUBON_API_SECRET")
            return

        try:
            self.sdk = FubonSDK()
            self.sdk.login(API_KEY, API_SECRET, ACCOUNT)
            self.connected = True
            logger.info("富邦 SDK 連接成功")
        except Exception as e:
            logger.error(f"富邦 SDK 連接失敗: {e}")
            self.connected = False

    def is_connected(self) -> bool:
        """檢查連接狀態"""
        return self.connected

    def get_realtime_quote(self, stock_id: str) -> Dict:
        """取得即時報價"""
        if not self.is_connected():
            return {
                "success": False,
                "error": "SDK 未連接",
                "data": self._mock_quote(stock_id),
            }

        try:
            quote = self.sdk.get_quote(stock_id)

            result = {
                "stock_id": stock_id,
                "timestamp": datetime.now().isoformat(),
                "price_info": {
                    "current": float(quote.get("price", 0)),
                    "open": float(quote.get("open", 0)),
                    "high": float(quote.get("high", 0)),
                    "low": float(quote.get("low", 0)),
                    "close": float(quote.get("close", 0)),
                    "previous_close": float(quote.get("previous_close", 0)),
                    "change": float(quote.get("change", 0)),
                    "change_percent": float(quote.get("change_percent", 0)),
                },
                "volume_info": {
                    "volume": int(quote.get("volume", 0)),
                    "amount": float(quote.get("amount", 0)),
                    "avg_price": float(quote.get("avg_price", 0)),
                },
                "orderbook": {
                    "bid": [
                        {
                            "price": float(quote.get(f"bid_price_{i}", 0)),
                            "volume": int(quote.get(f"bid_volume_{i}", 0)),
                        }
                        for i in range(1, 6)
                    ],
                    "ask": [
                        {
                            "price": float(quote.get(f"ask_price_{i}", 0)),
                            "volume": int(quote.get(f"ask_volume_{i}", 0)),
                        }
                        for i in range(1, 6)
                    ],
                },
                "source": "fubon_realtime",
            }

            return {"success": True, "data": result}

        except Exception as e:
            logger.error(f"即時報價失敗: {e}")
            return {"success": False, "error": str(e)}

    def get_historical(
        self, stock_id: str, days: int = 365, interval: str = "1d"
    ) -> Dict:
        """取得歷史資料"""
        if not self.is_connected():
            return {"success": False, "error": "SDK 未連接"}

        try:
            from datetime import timedelta

            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            bars = self.sdk.get_bars(stock_id, start_date, end_date, interval)

            data = []
            for bar in bars:
                data.append(
                    {
                        "date": str(bar.get("date", "")),
                        "open": float(bar.get("open", 0)),
                        "high": float(bar.get("high", 0)),
                        "low": float(bar.get("low", 0)),
                        "close": float(bar.get("close", 0)),
                        "volume": int(bar.get("volume", 0)),
                    }
                )

            return {
                "success": True,
                "data": {
                    "stock_id": stock_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "interval": interval,
                    "count": len(data),
                    "data": data,
                    "source": "fubon_historical",
                },
            }

        except Exception as e:
            logger.error(f"歷史資料失敗: {e}")
            return {"success": False, "error": str(e)}

    def get_financial(self, stock_id: str, report_type: str = "ratios") -> Dict:
        """取得財報數據"""
        if not self.is_connected():
            return {"success": False, "error": "SDK 未連接"}

        try:
            if report_type == "income":
                report = self.sdk.get_income_statement(stock_id)
            elif report_type == "balance":
                report = self.sdk.get_balance_sheet(stock_id)
            elif report_type == "cashflow":
                report = self.sdk.get_cash_flow(stock_id)
            elif report_type == "ratios":
                report = self.sdk.get_financial_ratios(stock_id)
            else:
                raise ValueError(f"未知的報表類型: {report_type}")

            return {
                "success": True,
                "data": {
                    "stock_id": stock_id,
                    "report_type": report_type,
                    "period": report.get("period", ""),
                    "data": report.get("data", {}),
                    "source": "fubon_financial",
                },
            }

        except Exception as e:
            logger.error(f"財報失敗: {e}")
            return {"success": False, "error": str(e)}

    def get_institutional(self, stock_id: str) -> Dict:
        """取得三大法人"""
        if not self.is_connected():
            return {"success": False, "error": "SDK 未連接"}

        try:
            data = self.sdk.get_institutional(stock_id)

            return {
                "success": True,
                "data": {
                    "stock_id": stock_id,
                    "date": data.get("date", ""),
                    "foreign_buy": float(data.get("foreign_buy", 0)),
                    "foreign_sell": float(data.get("foreign_sell", 0)),
                    "foreign_net": float(data.get("foreign_net", 0)),
                    "trust_buy": float(data.get("trust_buy", 0)),
                    "trust_sell": float(data.get("trust_sell", 0)),
                    "trust_net": float(data.get("trust_net", 0)),
                    "dealer_buy": float(data.get("dealer_buy", 0)),
                    "dealer_sell": float(data.get("dealer_sell", 0)),
                    "dealer_net": float(data.get("dealer_net", 0)),
                    "source": "fubon_institutional",
                },
            }

        except Exception as e:
            logger.error(f"法人資料失敗: {e}")
            return {"success": False, "error": str(e)}

    def get_margin(self, stock_id: str) -> Dict:
        """取得融資融券"""
        if not self.is_connected():
            return {"success": False, "error": "SDK 未連接"}

        try:
            data = self.sdk.get_margin(stock_id)

            return {
                "success": True,
                "data": {
                    "stock_id": stock_id,
                    "date": data.get("date", ""),
                    "margin_buy": float(data.get("margin_buy", 0)),
                    "margin_sell": float(data.get("margin_sell", 0)),
                    "margin_balance": float(data.get("margin_balance", 0)),
                    "short_buy": float(data.get("short_buy", 0)),
                    "short_sell": float(data.get("short_sell", 0)),
                    "short_balance": float(data.get("short_balance", 0)),
                    "source": "fubon_margin",
                },
            }

        except Exception as e:
            logger.error(f"融資融券失敗: {e}")
            return {"success": False, "error": str(e)}

    def _mock_quote(self, stock_id: str) -> Dict:
        """模擬報價"""
        return {"stock_id": stock_id, "price_info": {"current": 0}, "source": "mock"}


# ──────────────────────────────────────────────
#  FastAPI 應用
# ──────────────────────────────────────────────

app = FastAPI(
    title="富邦證券 SDK 服務",
    description="提供即時報價、歷史資料、財報數據、籌碼面資料",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局服務實例
fubon_service = FubonService()


@app.get("/")
async def root():
    """根端點"""
    return {
        "service": "富邦證券 SDK 服務",
        "status": "connected" if fubon_service.is_connected() else "disconnected",
        "endpoints": [
            "/health",
            "/quote/{stock_id}",
            "/historical/{stock_id}",
            "/financial/{stock_id}",
            "/institutional/{stock_id}",
            "/margin/{stock_id}",
            "/comprehensive/{stock_id}",
        ],
    }


@app.get("/health")
async def health_check():
    """健康檢查"""
    return {
        "status": "healthy",
        "fubon_connected": fubon_service.is_connected(),
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/quote/{stock_id}")
async def get_quote(stock_id: str):
    """取得即時報價"""
    return fubon_service.get_realtime_quote(stock_id)


@app.get("/historical/{stock_id}")
async def get_historical(
    stock_id: str,
    days: int = Query(365, description="歷史天數"),
    interval: str = Query("1d", description="資料間隔 (1m, 5m, 15m, 30m, 1h, 1d)"),
):
    """取得歷史資料"""
    return fubon_service.get_historical(stock_id, days, interval)


@app.get("/financial/{stock_id}")
async def get_financial(
    stock_id: str,
    report_type: str = Query(
        "ratios", description="報表類型 (income, balance, cashflow, ratios)"
    ),
):
    """取得財報數據"""
    return fubon_service.get_financial(stock_id, report_type)


@app.get("/institutional/{stock_id}")
async def get_institutional(stock_id: str):
    """取得三大法人"""
    return fubon_service.get_institutional(stock_id)


@app.get("/margin/{stock_id}")
async def get_margin(stock_id: str):
    """取得融資融券"""
    return fubon_service.get_margin(stock_id)


@app.get("/comprehensive/{stock_id}")
async def get_comprehensive(stock_id: str):
    """取得綜合資料"""
    return {
        "success": True,
        "data": {
            "stock_id": stock_id,
            "timestamp": datetime.now().isoformat(),
            "realtime": fubon_service.get_realtime_quote(stock_id),
            "historical": fubon_service.get_historical(stock_id, days=30),
            "financial": fubon_service.get_financial(stock_id, "ratios"),
            "institutional": fubon_service.get_institutional(stock_id),
            "margin": fubon_service.get_margin(stock_id),
        },
    }


# ──────────────────────────────────────────────
#  啟動服務
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║              富邦證券 SDK 服務                               ║
╠══════════════════════════════════════════════════════════════╣
║  API Key: {API_KEY[:10] if API_KEY else '未設定':<20}                  ║
║  狀態: {'已連接' if fubon_service.is_connected() else '未連接':<20}                      ║
║  端口: {PORT:<20}                      ║
╠══════════════════════════════════════════════════════════════╣
║  API 端點:                                                   ║
║    GET /quote/{{stock_id}}         即時報價                   ║
║    GET /historical/{{stock_id}}    歷史資料                   ║
║    GET /financial/{{stock_id}}     財報數據                   ║
║    GET /institutional/{{stock_id}} 三大法人                   ║
║    GET /margin/{{stock_id}}        融資融券                   ║
║    GET /comprehensive/{{stock_id}} 綜合資料                   ║
╠══════════════════════════════════════════════════════════════╣
║  使用方式:                                                   ║
║    設定環境變數:                                             ║
║      export FUBON_API_KEY=your_key                          ║
║      export FUBON_API_SECRET=your_secret                    ║
║      export FUBON_ACCOUNT=your_account                      ║
║                                                              ║
║    啟動服務:                                                 ║
║      python fubon_service.py                                 ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # 富邦 SDK 服務刻意綁定所有介面，供主機（另一台電腦）透過區網連線；屬設計需求。
    uvicorn.run(app, host="0.0.0.0", port=PORT)  # nosec B104
