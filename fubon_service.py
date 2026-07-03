"""
富邦新一代 API SDK 獨立服務。

在已安裝富邦官方 Python SDK 的電腦上執行，提供 HTTP API 給主系統 /
OpenClaw Agent 調用。官方範例使用套件名稱為 ``fubon_neo``。
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

try:
    from fubon_neo.constant import BSAction, MarketType, OrderType, PriceType, TimeInForce
    from fubon_neo.sdk import FubonSDK, Order

    FUBON_AVAILABLE = True
except ImportError:
    FUBON_AVAILABLE = False
    logger.warning("fubon_neo 未安裝，請先安裝富邦官方 Python SDK wheel/installer")


# ──────────────────────────────────────────────
#  配置
# ──────────────────────────────────────────────

# 官方範例：sdk.login("身分證字號", "登入密碼", "./憑證.pfx", "憑證密碼")
FUBON_ID = os.getenv("FUBON_ID") or os.getenv("FUBON_ACCOUNT", "")
FUBON_PASSWORD = os.getenv("FUBON_PASSWORD", "")
FUBON_CERT_PATH = os.getenv("FUBON_CERT_PATH", "")
FUBON_CERT_PASSWORD = os.getenv("FUBON_CERT_PASSWORD", "")

PORT = int(os.getenv("FUBON_SERVICE_PORT", "6666"))
SERVICE_TOKEN = os.getenv("FUBON_SERVICE_TOKEN", "")
ENABLE_REAL_ORDER = os.getenv("FUBON_ENABLE_REAL_ORDER", "false").lower() == "true"


class FubonService:
    """富邦官方 fubon_neo SDK 服務封裝。"""

    def __init__(self):
        self.sdk = None
        self.rest_stock = None
        self.login_response = None
        self.account_obj = None
        self.accounts = []
        self.connected = False
        self._connect()

    def _connect(self):
        """連接富邦新一代 API。"""
        if not FUBON_AVAILABLE:
            logger.error("fubon_neo 未安裝")
            return

        missing = [
            name
            for name, value in {
                "FUBON_ID/FUBON_ACCOUNT": FUBON_ID,
                "FUBON_PASSWORD": FUBON_PASSWORD,
                "FUBON_CERT_PATH": FUBON_CERT_PATH,
                "FUBON_CERT_PASSWORD": FUBON_CERT_PASSWORD,
            }.items()
            if not value
        ]
        if missing:
            logger.error(f"未設定富邦登入必要環境變數: {', '.join(missing)}")
            return

        try:
            self.sdk = FubonSDK()
            self.login_response = self.sdk.login(
                FUBON_ID,
                FUBON_PASSWORD,
                FUBON_CERT_PATH,
                FUBON_CERT_PASSWORD,
            )
            self.accounts = self._normalize_accounts(self.login_response)
            self.account_obj = self._first_account_object(self.login_response)
            self.rest_stock = self.sdk.marketdata.rest_client.stock
            self.connected = True
            logger.info("富邦新一代 API SDK 連接成功")
        except Exception as e:
            logger.error(f"富邦 SDK 連接失敗: {e}")
            self.connected = False

    def is_connected(self) -> bool:
        return self.connected

    def get_accounts(self) -> Dict:
        """取得登入後可用帳戶。"""
        if not self.is_connected():
            return {"success": False, "error": "SDK 未連接", "data": []}

        return {
            "success": True,
            "data": self.accounts,
            "count": len(self.accounts),
            "source": "fubon_neo_accounts",
        }

    def get_realtime_quote(self, stock_id: str) -> Dict:
        """使用官方 REST API 取得即時報價。"""
        if not self.is_connected():
            return {"success": False, "error": "SDK 未連接", "data": self._mock_quote(stock_id)}

        symbol = self._clean_stock_id(stock_id)
        try:
            quote = self.rest_stock.intraday.quote(symbol=symbol)
            return {
                "success": True,
                "data": {
                    "stock_id": symbol,
                    "timestamp": datetime.now().isoformat(),
                    "raw": self._to_plain_data(quote),
                    "source": "fubon_neo_intraday_quote",
                },
            }
        except Exception as e:
            logger.error(f"即時報價失敗: {e}")
            return {"success": False, "error": str(e), "stock_id": symbol}

    def get_ticker(self, stock_id: str) -> Dict:
        """使用官方 REST API 取得股票資訊。"""
        if not self.is_connected():
            return {"success": False, "error": "SDK 未連接"}

        symbol = self._clean_stock_id(stock_id)
        try:
            result = self.rest_stock.intraday.ticker(symbol=symbol)
            return {
                "success": True,
                "data": self._to_plain_data(result),
                "source": "fubon_neo_intraday_ticker",
            }
        except Exception as e:
            logger.error(f"股票資訊查詢失敗: {e}")
            return {"success": False, "error": str(e), "stock_id": symbol}

    def get_historical(self, stock_id: str, days: int = 365, interval: str = "1d") -> Dict:
        """取得歷史 K 線。

        官方範例：
        restStock.historical.candles(symbol="2330", from="2023-07-26", to="2024-01-30")
        """
        if not self.is_connected():
            return {"success": False, "error": "SDK 未連接"}

        symbol = self._clean_stock_id(stock_id)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        try:
            result = self.rest_stock.historical.candles(
                **{
                    "symbol": symbol,
                    "from": start_date.isoformat(),
                    "to": end_date.isoformat(),
                }
            )
            return {
                "success": True,
                "data": {
                    "stock_id": symbol,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "interval": interval,
                    "raw": self._to_plain_data(result),
                    "source": "fubon_neo_historical_candles",
                },
            }
        except Exception as e:
            logger.error(f"歷史資料失敗: {e}")
            return {"success": False, "error": str(e), "stock_id": symbol}

    def get_inventories(self) -> Dict:
        """庫存查詢。"""
        if not self.is_connected() or self.account_obj is None:
            return {"success": False, "error": "SDK 未連接或沒有可用帳戶"}

        try:
            result = self.sdk.accounting.inventories(self.account_obj)
            return {
                "success": bool(getattr(result, "is_success", True)),
                "data": self._to_plain_data(getattr(result, "data", result)),
                "message": getattr(result, "message", ""),
                "source": "fubon_neo_accounting_inventories",
            }
        except Exception as e:
            logger.error(f"庫存查詢失敗: {e}")
            return {"success": False, "error": str(e)}

    def get_bank_remain(self) -> Dict:
        """銀行餘額查詢。"""
        if not self.is_connected() or self.account_obj is None:
            return {"success": False, "error": "SDK 未連接或沒有可用帳戶"}

        try:
            result = self.sdk.accounting.bank_remain(self.account_obj)
            return {
                "success": bool(getattr(result, "is_success", True)),
                "data": self._to_plain_data(getattr(result, "data", result)),
                "message": getattr(result, "message", ""),
                "source": "fubon_neo_accounting_bank_remain",
            }
        except Exception as e:
            logger.error(f"銀行餘額查詢失敗: {e}")
            return {"success": False, "error": str(e)}

    def get_financial(self, stock_id: str, report_type: str = "ratios") -> Dict:
        """富邦官方範例未提供財報查詢，明確回報不支援。"""
        return {
            "success": False,
            "error": "富邦官方 Python 範例未提供財報查詢；請改用 repo 既有 financial_fetcher/TWSE/FinMind",
            "stock_id": self._clean_stock_id(stock_id),
            "report_type": report_type,
        }

    def get_institutional(self, stock_id: str) -> Dict:
        """富邦官方範例未提供三大法人查詢，明確回報不支援。"""
        return {
            "success": False,
            "error": "富邦官方 Python 範例未提供三大法人查詢；請改用 TWSE endpoint",
            "stock_id": self._clean_stock_id(stock_id),
        }

    def get_margin(self, stock_id: str) -> Dict:
        """官方範例提供的是資券配額查詢，不是融資融券統計。"""
        if not self.is_connected() or self.account_obj is None:
            return {"success": False, "error": "SDK 未連接或沒有可用帳戶"}

        symbol = self._clean_stock_id(stock_id)
        try:
            result = self.sdk.stock.margin_quota(self.account_obj, symbol)
            return {
                "success": bool(getattr(result, "is_success", True)),
                "data": self._to_plain_data(getattr(result, "data", result)),
                "message": getattr(result, "message", ""),
                "stock_id": symbol,
                "source": "fubon_neo_margin_quota",
            }
        except Exception as e:
            logger.error(f"資券配額查詢失敗: {e}")
            return {"success": False, "error": str(e), "stock_id": symbol}

    def place_order(
        self,
        stock_id: str,
        action: str,
        quantity: int,
        price: float,
        dry_run: bool = True,
    ) -> Dict:
        """建立官方 Order 物件；預設 dry-run，不送真實委託。"""
        symbol = self._clean_stock_id(stock_id)
        action = action.lower().strip()
        if action not in {"buy", "sell"}:
            return {"success": False, "error": "action must be buy or sell"}
        if quantity <= 0:
            return {"success": False, "error": "quantity must be greater than 0"}
        if price <= 0:
            return {"success": False, "error": "price must be greater than 0"}

        order_payload = {
            "buy_sell": "BSAction.Buy" if action == "buy" else "BSAction.Sell",
            "symbol": symbol,
            "price": price,
            "quantity": quantity,
            "market_type": "MarketType.Common",
            "price_type": "PriceType.Limit",
            "time_in_force": "TimeInForce.ROD",
            "order_type": "OrderType.Stock",
            "user_def": None,
            "timestamp": datetime.now().isoformat(),
        }

        if dry_run:
            return {
                "success": True,
                "data": {**order_payload, "status": "dry_run"},
                "message": "dry_run=true，已依官方 Order 格式試算，未送出真實委託",
            }

        if not ENABLE_REAL_ORDER:
            return {
                "success": False,
                "error": "真實下單目前已鎖定。查詢功能可用；下單需先確認一般限價單 enum 與風控後再開啟。",
                "data": order_payload,
            }

        return {
            "success": False,
            "error": "真實下單 adapter 尚未啟用；目前只支援 dry_run=true。",
            "data": order_payload,
        }

    def _mock_quote(self, stock_id: str) -> Dict:
        return {"stock_id": stock_id, "price_info": {"current": 0}, "source": "mock"}

    def _clean_stock_id(self, stock_id: str) -> str:
        return stock_id.replace(".TW", "").replace(".TWO", "").strip()

    def _first_account_object(self, login_result: Any) -> Any:
        data = getattr(login_result, "data", None)
        if isinstance(data, list) and data:
            return data[0]
        return None

    def _normalize_accounts(self, login_result: Any) -> list:
        data = getattr(login_result, "data", login_result)
        if isinstance(data, dict):
            data = data.get("accounts", data.get("data", data))
        if not isinstance(data, list):
            data = [data]
        return [self._to_plain_data(item) for item in data if item]

    def _to_plain_data(self, value: Any) -> Any:
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        if isinstance(value, list):
            return [self._to_plain_data(item) for item in value]
        if isinstance(value, dict):
            return {key: self._to_plain_data(val) for key, val in value.items()}
        if hasattr(value, "dict"):
            return self._to_plain_data(value.dict())
        if hasattr(value, "__dict__"):
            return {
                key: self._to_plain_data(val)
                for key, val in vars(value).items()
                if not key.startswith("_")
            }
        return str(value)


app = FastAPI(
    title="富邦新一代 API SDK 服務",
    description="提供富邦新一代 API 查詢與 dry-run 下單服務",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fubon_service = FubonService()


def verify_service_token(
    x_fubon_service_token: str = Header(default="", alias="X-Fubon-Service-Token")
):
    """可選的簡單服務 token；未設定 FUBON_SERVICE_TOKEN 時不啟用。"""
    if SERVICE_TOKEN and x_fubon_service_token != SERVICE_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid Fubon service token")


@app.get("/")
async def root():
    return {
        "service": "富邦新一代 API SDK 服務",
        "status": "connected" if fubon_service.is_connected() else "disconnected",
        "endpoints": [
            "/health",
            "/accounts",
            "/quote/{stock_id}",
            "/ticker/{stock_id}",
            "/historical/{stock_id}",
            "/inventories",
            "/bank-remain",
            "/margin/{stock_id}",
            "/comprehensive/{stock_id}",
            "/order",
        ],
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "fubon_connected": fubon_service.is_connected(),
        "sdk": "fubon_neo",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/accounts")
async def get_accounts(_=Depends(verify_service_token)):
    return fubon_service.get_accounts()


@app.get("/quote/{stock_id}")
async def get_quote(stock_id: str, _=Depends(verify_service_token)):
    return fubon_service.get_realtime_quote(stock_id)


@app.get("/ticker/{stock_id}")
async def get_ticker(stock_id: str, _=Depends(verify_service_token)):
    return fubon_service.get_ticker(stock_id)


@app.get("/historical/{stock_id}")
async def get_historical(
    stock_id: str,
    days: int = Query(365, description="歷史天數"),
    interval: str = Query("1d", description="保留參數；官方日 K 查詢不使用此值"),
    _=Depends(verify_service_token),
):
    return fubon_service.get_historical(stock_id, days, interval)


@app.get("/inventories")
async def get_inventories(_=Depends(verify_service_token)):
    return fubon_service.get_inventories()


@app.get("/bank-remain")
async def get_bank_remain(_=Depends(verify_service_token)):
    return fubon_service.get_bank_remain()


@app.get("/financial/{stock_id}")
async def get_financial(
    stock_id: str,
    report_type: str = Query("ratios", description="報表類型"),
    _=Depends(verify_service_token),
):
    return fubon_service.get_financial(stock_id, report_type)


@app.get("/institutional/{stock_id}")
async def get_institutional(stock_id: str, _=Depends(verify_service_token)):
    return fubon_service.get_institutional(stock_id)


@app.get("/margin/{stock_id}")
async def get_margin(stock_id: str, _=Depends(verify_service_token)):
    return fubon_service.get_margin(stock_id)


@app.get("/comprehensive/{stock_id}")
async def get_comprehensive(stock_id: str, _=Depends(verify_service_token)):
    return {
        "success": True,
        "data": {
            "stock_id": fubon_service._clean_stock_id(stock_id),
            "timestamp": datetime.now().isoformat(),
            "ticker": fubon_service.get_ticker(stock_id),
            "realtime": fubon_service.get_realtime_quote(stock_id),
            "historical": fubon_service.get_historical(stock_id, days=30),
            "inventories": fubon_service.get_inventories(),
            "bank_remain": fubon_service.get_bank_remain(),
            "margin_quota": fubon_service.get_margin(stock_id),
        },
    }


@app.post("/order")
async def place_order(
    stock_id: str,
    action: str,
    quantity: int,
    price: float,
    dry_run: bool = Query(True, description="預設只模擬下單，false 才送真實委託"),
    _=Depends(verify_service_token),
):
    return fubon_service.place_order(stock_id, action, quantity, price, dry_run)


if __name__ == "__main__":
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║              富邦新一代 API SDK 服務                         ║
╠══════════════════════════════════════════════════════════════╣
║  Login ID: {FUBON_ID[:10] if FUBON_ID else '未設定':<20}                  ║
║  狀態: {'已連接' if fubon_service.is_connected() else '未連接':<20}                      ║
║  端口: {PORT:<20}                      ║
╠══════════════════════════════════════════════════════════════╣
║  API 端點:                                                   ║
║    GET /quote/{{stock_id}}         即時報價                   ║
║    GET /ticker/{{stock_id}}        股票資訊                   ║
║    GET /historical/{{stock_id}}    歷史 K 線                  ║
║    GET /inventories               庫存查詢                   ║
║    GET /bank-remain               銀行餘額                   ║
║    GET /margin/{{stock_id}}        資券配額                   ║
║    GET /comprehensive/{{stock_id}} 綜合資料                   ║
║    POST /order                    下單（預設 dry_run）       ║
╠══════════════════════════════════════════════════════════════╣
║  使用方式:                                                   ║
║    export FUBON_ID=your_id                                  ║
║    export FUBON_PASSWORD=your_password                      ║
║    export FUBON_CERT_PATH=./your_cert.pfx                   ║
║    export FUBON_CERT_PASSWORD=your_cert_password            ║
║    export FUBON_SERVICE_TOKEN=optional_token                ║
╚══════════════════════════════════════════════════════════════╝
    """)
    uvicorn.run(app, host="0.0.0.0", port=PORT)  # nosec B104
