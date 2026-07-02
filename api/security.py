"""
台灣股票分析工具 - API 授權

採「選擇性啟用」策略：
- 未設定 settings.API_KEY 時（預設 None），不做任何驗證，維持本機開發便利。
- 一旦設定 API_KEY（例如部署時的環境變數），/api/v1/* 全部端點都會要求
  相符的 X-API-Key 標頭，否則回傳 401。
"""
import hmac
from typing import Optional

from fastapi import Header, HTTPException, Request, status

from config.config import get_settings
from utils.helpers import validate_stock_id


async def validate_path_stock_id(request: Request):
    """在進入路由函式（及其 try/except）之前，先驗證路徑中的 stock_id。

    掛在 router 層即可一次涵蓋所有含 {stock_id} 的端點，回傳乾淨的 400；
    對沒有 stock_id 路徑參數的端點則自動略過。
    """
    sid = request.path_params.get("stock_id")
    if sid is not None and not validate_stock_id(sid):
        raise HTTPException(status_code=400, detail=f"無效的股票代碼格式: {sid}")


async def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
    """驗證 X-API-Key 標頭。未設定 API_KEY 時直接放行。"""
    settings = get_settings()

    # 未設定金鑰 → 不啟用驗證（本機開發預設行為）
    if not settings.API_KEY:
        return

    # 以固定時間比較避免時序側通道
    if not x_api_key or not hmac.compare_digest(x_api_key, settings.API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": settings.API_KEY_HEADER},
        )
