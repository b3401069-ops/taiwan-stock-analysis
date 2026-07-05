"""
富邦證券 SDK 獨立服務（唯讀）
在有 fubon_neo SDK 的電腦上執行，提供 HTTP API 給主電腦的分析系統 / OpenClaw 調用
回傳格式：JSON

本服務只提供「查詢」功能（持股、損益、報價、歷史K線），不提供下單。

使用方式:
1. 從富邦官網申請 API 使用權並下載憑證（.pfx）
2. 安裝 SDK: pip install fubon-neo（或使用官網下載的 wheel）
3. 設定環境變數（見檔尾說明或 docs/FUBON_SETUP.md）
4. 執行: python fubon_service.py
"""

import hmac
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Query
from loguru import logger

# 嘗試導入富邦 SDK（官方套件名為 fubon_neo）
try:
    from fubon_neo.sdk import FubonSDK

    FUBON_AVAILABLE = True
except ImportError:
    FUBON_AVAILABLE = False
    logger.warning("fubon_neo 未安裝，請先安裝: pip install fubon-neo")


# ──────────────────────────────────────────────
#  配置（全部由環境變數提供，勿寫死在程式碼）
# ──────────────────────────────────────────────

PERSONAL_ID = os.getenv("FUBON_PERSONAL_ID", "")  # 身分證字號
PASSWORD = os.getenv("FUBON_PASSWORD") or os.getenv(
    "FUBON_LOGIN_PASSWORD", ""
)  # 登入密碼
CERT_PATH = os.getenv("FUBON_CERT_PATH", "")  # 憑證檔（.pfx）完整路徑
CERT_PASS = os.getenv("FUBON_CERT_PASS") or os.getenv(
    "FUBON_CERT_PASSWORD", ""
)  # 憑證密碼（未設定則不帶）
PORT = int(os.getenv("FUBON_SERVICE_PORT", "8081"))
# 服務自身的存取金鑰：本服務會回傳真實持股與損益，強烈建議設定。
# 設定後所有資料端點都要求 X-API-Key 標頭；/health 除外。
SERVICE_API_KEY = os.getenv("FUBON_SERVICE_API_KEY", "")


# ──────────────────────────────────────────────
#  SDK 物件 → JSON 序列化
# ──────────────────────────────────────────────


SENSITIVE_KEY_PARTS = (
    "account",
    "branch",
    "cert",
    "password",
    "personal",
    "token",
    "idno",
)


def to_jsonable(obj: Any, depth: int = 0, seen: Optional[set] = None) -> Any:
    """把 fubon_neo 回傳的物件（Rust/pyo3 物件、巢狀結構）轉成可 JSON 化的型別。

    SDK 物件沒有 __dict__，改走 dir() 取公開屬性；不同 SDK 版本欄位增減
    也能容錯，不需要逐欄位維護對照表。
    """
    if seen is None:
        seen = set()
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, datetime):
        return obj.isoformat()
    if depth >= 4:
        return str(obj)

    obj_id = id(obj)
    if obj_id in seen:
        return str(obj)
    seen.add(obj_id)

    if isinstance(obj, dict):
        return {
            str(k): to_jsonable(v, depth + 1, seen)
            for k, v in obj.items()
            if not any(part in str(k).lower() for part in SENSITIVE_KEY_PARTS)
        }
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v, depth + 1, seen) for v in obj]

    fields: Dict[str, Any] = {}
    for name in dir(obj):
        if name.startswith("_"):
            continue
        if any(part in name.lower() for part in SENSITIVE_KEY_PARTS):
            continue
        try:
            value = getattr(obj, name)
        except Exception:
            continue
        if callable(value):
            continue
        if value is None or isinstance(
            value, (str, int, float, bool, list, tuple, dict, datetime)
        ):
            fields[name] = to_jsonable(value, depth + 1, seen)
    return fields if fields else str(obj)


# ──────────────────────────────────────────────
#  富邦 SDK 封裝（唯讀）
# ──────────────────────────────────────────────


class FubonService:
    """富邦 SDK 服務封裝：登入、帳務查詢、行情查詢"""

    def __init__(self):
        self.sdk = None
        self.accounts: List[Any] = []
        self.connected = False
        self.marketdata_ready = False
        self._connect()

    def _connect(self):
        """登入富邦 SDK 並初始化行情連線"""
        if not FUBON_AVAILABLE:
            logger.error("fubon_neo 未安裝，服務將以未連接狀態啟動")
            return

        if not PERSONAL_ID or not PASSWORD or not CERT_PATH:
            logger.error(
                "未設定 FUBON_PERSONAL_ID / FUBON_PASSWORD / FUBON_CERT_PATH，"
                "服務將以未連接狀態啟動"
            )
            return

        if not os.path.exists(CERT_PATH):
            logger.error(f"憑證檔不存在: {CERT_PATH}")
            return

        try:
            self.sdk = FubonSDK()
            # 富邦 Neo SDK 登入：身分證字號 + 密碼 + 憑證檔（+ 憑證密碼）
            if CERT_PASS:
                result = self.sdk.login(PERSONAL_ID, PASSWORD, CERT_PATH, CERT_PASS)
            else:
                result = self.sdk.login(PERSONAL_ID, PASSWORD, CERT_PATH)

            if not getattr(result, "is_success", False):
                logger.error(f"富邦 SDK 登入失敗: {getattr(result, 'message', result)}")
                return

            self.accounts = result.data or []
            self.connected = True
            logger.info(f"富邦 SDK 登入成功，共 {len(self.accounts)} 個帳戶")

            # 初始化行情（報價 / 歷史K線需要）
            try:
                self.sdk.init_realtime()
                self.marketdata_ready = True
                logger.info("富邦行情連線初始化完成")
            except Exception as e:
                logger.warning(f"行情初始化失敗（帳務查詢仍可用）: {e}")

        except Exception as e:
            logger.error(f"富邦 SDK 連接失敗: {e}")
            self.connected = False

    # ── 共用 ───────────────────────────────────

    def _get_account(self, index: int = 0):
        if not self.connected:
            raise HTTPException(status_code=503, detail="富邦 SDK 未連接")
        if index < 0 or index >= len(self.accounts):
            raise HTTPException(
                status_code=400,
                detail=f"帳戶索引超出範圍（共 {len(self.accounts)} 個帳戶）",
            )
        return self.accounts[index]

    @staticmethod
    def _unwrap(result) -> Dict:
        """把 SDK 的 Result 物件轉成統一的 JSON 回應"""
        if getattr(result, "is_success", False):
            return {"success": True, "data": to_jsonable(result.data)}
        return {
            "success": False,
            "error": str(getattr(result, "message", "SDK 回傳失敗")),
        }

    @staticmethod
    def _clean_symbol(stock_id: str) -> str:
        """去除 .TW / .TWO 後綴（富邦 SDK 使用純代碼）"""
        return stock_id.replace(".TWO", "").replace(".TW", "").strip()

    # ── 帳務（真實持股） ────────────────────────

    def get_accounts(self) -> Dict:
        """帳戶清單"""
        if not self.connected:
            raise HTTPException(status_code=503, detail="富邦 SDK 未連接")
        return {"success": True, "data": to_jsonable(self.accounts)}

    def get_positions(self, account_index: int = 0) -> Dict:
        """持股庫存"""
        account = self._get_account(account_index)
        try:
            result = self.sdk.accounting.inventories(account)
            return self._unwrap(result)
        except Exception as e:
            logger.error(f"查詢持股失敗: {e}")
            return {"success": False, "error": str(e)}

    def get_unrealized_pnl(self, account_index: int = 0) -> Dict:
        """未實現損益"""
        account = self._get_account(account_index)
        try:
            result = self.sdk.accounting.unrealized_gains_and_loses(account)
            return self._unwrap(result)
        except Exception as e:
            logger.error(f"查詢未實現損益失敗: {e}")
            return {"success": False, "error": str(e)}

    def get_bank_balance(self, account_index: int = 0) -> Dict:
        """交割銀行餘額"""
        account = self._get_account(account_index)
        try:
            result = self.sdk.accounting.bank_remain(account)
            return self._unwrap(result)
        except Exception as e:
            logger.error(f"查詢銀行餘額失敗: {e}")
            return {"success": False, "error": str(e)}

    # ── 行情 ───────────────────────────────────

    def _rest_stock(self):
        if not self.connected:
            raise HTTPException(status_code=503, detail="富邦 SDK 未連接")
        if not self.marketdata_ready:
            raise HTTPException(status_code=503, detail="富邦行情連線未初始化")
        return self.sdk.marketdata.rest_client.stock

    def get_quote(self, stock_id: str) -> Dict:
        """即時報價（REST 快照）"""
        symbol = self._clean_symbol(stock_id)
        try:
            quote = self._rest_stock().intraday.quote(symbol=symbol)
            return {"success": True, "data": to_jsonable(quote)}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"即時報價失敗 {symbol}: {e}")
            return {"success": False, "error": str(e)}

    def get_historical(self, stock_id: str, days: int = 365) -> Dict:
        """歷史日K線"""
        symbol = self._clean_symbol(stock_id)
        try:
            end = datetime.now().strftime("%Y-%m-%d")
            start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            # "from" 是 Python 保留字，須以 dict 解包傳入
            candles = self._rest_stock().historical.candles(
                **{"symbol": symbol, "from": start, "to": end}
            )
            return {"success": True, "data": to_jsonable(candles)}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"歷史資料失敗 {symbol}: {e}")
            return {"success": False, "error": str(e)}

    # ── 綜合：一次取得投資組合全貌 ──────────────

    def get_portfolio_summary(self, account_index: int = 0) -> Dict:
        """持股 + 未實現損益 + 各持股即時報價（給 AI 產生投資建議用）"""
        positions = self.get_positions(account_index)
        pnl = self.get_unrealized_pnl(account_index)

        quotes: Dict[str, Any] = {}
        if positions.get("success") and self.marketdata_ready:
            for item in positions.get("data") or []:
                symbol = None
                if isinstance(item, dict):
                    symbol = item.get("stock_no") or item.get("symbol")
                if not symbol:
                    continue
                quotes[symbol] = self.get_quote(symbol)

        return {
            "success": True,
            "data": {
                "timestamp": datetime.now().isoformat(),
                "positions": positions,
                "unrealized_pnl": pnl,
                "quotes": quotes,
            },
        }


# ──────────────────────────────────────────────
#  存取控制
# ──────────────────────────────────────────────


async def verify_service_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    """驗證 X-API-Key。未設定 FUBON_SERVICE_API_KEY 時放行（僅建議在隔離網路使用）。"""
    if not SERVICE_API_KEY:
        return
    if not x_api_key or not hmac.compare_digest(x_api_key, SERVICE_API_KEY):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


# ──────────────────────────────────────────────
#  FastAPI 應用
# ──────────────────────────────────────────────

app = FastAPI(
    title="富邦證券 SDK 服務（唯讀）",
    description="提供帳戶持股、未實現損益、即時報價、歷史K線；不提供下單",
    version="2.0.0",
)

# 資料端點統一掛 API key 驗證；/health 與 / 不需驗證
router = APIRouter(dependencies=[Depends(verify_service_key)])

# 全局服務實例
fubon_service = FubonService()


@app.get("/")
async def root():
    """根端點"""
    return {
        "service": "富邦證券 SDK 服務（唯讀）",
        "status": "connected" if fubon_service.connected else "disconnected",
        "auth_enabled": bool(SERVICE_API_KEY),
        "endpoints": [
            "/health",
            "/accounts",
            "/positions",
            "/pnl/unrealized",
            "/balance",
            "/portfolio/summary",
            "/quote/{stock_id}",
            "/historical/{stock_id}",
        ],
    }


@app.get("/health")
async def health_check():
    """健康檢查"""
    return {
        "status": "healthy",
        "fubon_connected": fubon_service.connected,
        "marketdata_ready": fubon_service.marketdata_ready,
        "accounts": len(fubon_service.accounts),
        "auth_enabled": bool(SERVICE_API_KEY),
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/accounts")
async def get_accounts():
    """帳戶清單"""
    return fubon_service.get_accounts()


@router.get("/positions")
async def get_positions(account_index: int = Query(0, description="帳戶索引")):
    """持股庫存"""
    return fubon_service.get_positions(account_index)


@router.get("/pnl/unrealized")
async def get_unrealized_pnl(account_index: int = Query(0, description="帳戶索引")):
    """未實現損益"""
    return fubon_service.get_unrealized_pnl(account_index)


@router.get("/balance")
async def get_balance(account_index: int = Query(0, description="帳戶索引")):
    """交割銀行餘額"""
    return fubon_service.get_bank_balance(account_index)


@router.get("/portfolio/summary")
async def get_portfolio_summary(
    account_index: int = Query(0, description="帳戶索引"),
):
    """投資組合全貌：持股 + 未實現損益 + 即時報價"""
    return fubon_service.get_portfolio_summary(account_index)


@router.get("/quote/{stock_id}")
async def get_quote(stock_id: str):
    """即時報價"""
    return fubon_service.get_quote(stock_id)


@router.get("/historical/{stock_id}")
async def get_historical(
    stock_id: str,
    days: int = Query(365, ge=1, le=1825, description="歷史天數"),
):
    """歷史日K線"""
    return fubon_service.get_historical(stock_id, days)


app.include_router(router)


# ──────────────────────────────────────────────
#  啟動服務
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║              富邦證券 SDK 服務（唯讀 v2）                     ║
╠══════════════════════════════════════════════════════════════╣
║  SDK 狀態: {"已連接" if fubon_service.connected else "未連接":<10}                                     ║
║  行情狀態: {"就緒" if fubon_service.marketdata_ready else "未就緒":<10}                                     ║
║  存取驗證: {"已啟用" if SERVICE_API_KEY else "未啟用（建議設定 FUBON_SERVICE_API_KEY）":<10}  ║
║  端口: {PORT}                                                  ║
╠══════════════════════════════════════════════════════════════╣
║  API 端點:                                                   ║
║    GET /health               健康檢查（免驗證）              ║
║    GET /accounts             帳戶清單                        ║
║    GET /positions            持股庫存                        ║
║    GET /pnl/unrealized       未實現損益                      ║
║    GET /balance              交割銀行餘額                    ║
║    GET /portfolio/summary    持股+損益+報價 綜合             ║
║    GET /quote/{{stock_id}}     即時報價                       ║
║    GET /historical/{{stock_id}} 歷史K線                       ║
╠══════════════════════════════════════════════════════════════╣
║  環境變數:                                                   ║
║    FUBON_PERSONAL_ID     身分證字號                          ║
║    FUBON_PASSWORD        登入密碼                            ║
║    FUBON_CERT_PATH       憑證檔(.pfx)路徑                    ║
║    FUBON_CERT_PASS       憑證密碼（選填）                    ║
║    FUBON_SERVICE_API_KEY 服務存取金鑰（強烈建議）            ║
║    FUBON_SERVICE_PORT    服務端口（預設 8081）               ║
╚══════════════════════════════════════════════════════════════╝
    """)

    if not SERVICE_API_KEY:
        logger.warning(
            "未設定 FUBON_SERVICE_API_KEY！此服務會回傳真實持股與損益，"
            "任何能連到此端口的裝置都能讀取。請設定金鑰並搭配防火牆限制來源 IP。"
        )

    # 富邦 SDK 服務刻意綁定所有介面，供主機（另一台電腦）透過區網連線；屬設計需求。
    # 請務必設定 FUBON_SERVICE_API_KEY 並以防火牆限制來源。
    uvicorn.run(app, host="0.0.0.0", port=PORT)  # nosec B104
