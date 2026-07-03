"""
台灣股票分析工具 - 配置模組
"""

import os
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """應用配置"""

    # 應用配置
    APP_NAME: str = "台灣股票分析工具"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    # 伺服器綁定位址：預設僅本機（127.0.0.1），較安全（API 授權預設關閉時
    # 不會直接把服務暴露到整個區網）。需跨機存取時再設 HOST=0.0.0.0。
    HOST: str = "127.0.0.1"

    # 資料庫配置
    DATABASE_URL: str = "postgresql://username:password@localhost:5432/stock_analysis"
    REDIS_URL: str = "redis://localhost:6379/0"

    # 券商API配置
    SHIOAJI_API_KEY: Optional[str] = None
    SHIOAJI_SECRET_KEY: Optional[str] = None
    # 富邦新一代 API（fubon_neo）。保留舊 FUBON_* 欄位是為了相容既有 .env。
    FUBON_ID: Optional[str] = None
    FUBON_PASSWORD: Optional[str] = None
    FUBON_CERT_PATH: Optional[str] = None
    FUBON_CERT_PASSWORD: Optional[str] = None
    FUBON_API_KEY: Optional[str] = None
    FUBON_SECRET_KEY: Optional[str] = None
    FUBON_API_SECRET: Optional[str] = None
    FUBON_ACCOUNT: Optional[str] = None
    FUBON_SERVICE_URL: Optional[str] = None
    FUBON_SERVICE_TOKEN: Optional[str] = None
    FUBON_REQUEST_TIMEOUT: int = 10

    # Yahoo Finance配置
    YAHOO_FINANCE_TIMEOUT: int = 30

    # AI Agent配置
    OPENAI_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None

    # OpenClaw配置
    OPENCLAW_API_URL: str = "http://localhost:8000"
    OPENCLAW_API_KEY: Optional[str] = None

    # Hermes配置
    HERMES_API_URL: str = "http://localhost:8001"
    HERMES_API_KEY: Optional[str] = None

    # 快取配置
    CACHE_TTL: int = 3600
    CACHE_MAX_SIZE: int = 1000

    # 資料更新頻率（秒）
    DATA_UPDATE_INTERVAL: int = 3600
    REAL_TIME_UPDATE_INTERVAL: int = 60

    # 安全配置
    SECRET_KEY: str = "your_secret_key_here"
    API_KEY_HEADER: str = "X-API-Key"
    # API 存取金鑰：留空（None）時不啟用驗證，方便本機開發；
    # 部署時設定 API_KEY 環境變數即會對 /api/v1/* 全面啟用 X-API-Key 驗證。
    API_KEY: Optional[str] = None
    # CORS 允許來源（逗號分隔）。預設僅本機，避免 allow_origins=["*"] 的開放風險。
    CORS_ORIGINS: str = (
        "http://localhost:9999,http://127.0.0.1:9999,"
        "http://localhost:8501,http://127.0.0.1:8501"
    )

    @property
    def cors_origin_list(self) -> list:
        """將逗號分隔的 CORS_ORIGINS 轉為清單。"""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """獲取配置實例"""
    return Settings()


# 股票市場配置
STOCK_MARKET_CONFIG = {
    "taiwan": {
        "name": "台灣股市",
        "exchange": "TWSE",
        "currency": "TWD",
        "timezone": "Asia/Taipei",
        "trading_hours": {"open": "09:00", "close": "13:30"},
    },
    "japan": {
        "name": "日本股市",
        "exchange": "TSE",
        "currency": "JPY",
        "timezone": "Asia/Tokyo",
        "trading_hours": {"open": "09:00", "close": "15:00"},
    },
    "korea": {
        "name": "韓國股市",
        "exchange": "KRX",
        "currency": "KRW",
        "timezone": "Asia/Seoul",
        "trading_hours": {"open": "09:00", "close": "15:30"},
    },
    "usa": {
        "name": "美國股市",
        "exchange": "NYSE/NASDAQ",
        "currency": "USD",
        "timezone": "America/New_York",
        "trading_hours": {"open": "09:30", "close": "16:00"},
    },
}

# 技術指標配置
TECHNICAL_INDICATORS_CONFIG = {
    "moving_averages": {
        "short_term": [5, 10, 20],
        "medium_term": [50, 100],
        "long_term": [200],
    },
    "rsi": {"period": 14, "overbought": 70, "oversold": 30},
    "macd": {"fast_period": 12, "slow_period": 26, "signal_period": 9},
    "kd": {"k_period": 9, "d_period": 3, "j_period": 3},
    "bollinger_bands": {"period": 20, "std_dev": 2},
}

# 估值模型配置
VALUATION_MODELS_CONFIG = {
    "pe_ratio": {"weight": 0.30, "description": "本益比分析"},
    "pb_ratio": {"weight": 0.20, "description": "股價淨值比分析"},
    "dividend_yield": {"weight": 0.20, "description": "股利殖利率分析"},
    "ev_ebitda": {"weight": 0.15, "description": "企業價值/EBITDA分析"},
    "free_cash_flow_yield": {"weight": 0.15, "description": "自由現金流收益率分析"},
}

# 機器學習模型配置
ML_MODELS_CONFIG = {
    "arima": {"order": (1, 1, 1), "seasonal_order": (1, 1, 1, 12)},
    "lstm": {"units": 50, "epochs": 100, "batch_size": 32, "lookback": 60},
    "xgboost": {"n_estimators": 100, "max_depth": 6, "learning_rate": 0.1},
    "transformer": {"d_model": 64, "nhead": 8, "num_layers": 2, "epochs": 50},
}

# 產業分類配置
INDUSTRY_CLASSIFICATION = {
    "technology": ["半導體", "電子零組件", "電腦週邊", "資訊服務"],
    "finance": ["金融業", "銀行", "保險", "證券"],
    "manufacturing": ["鋼鐵", "機械", "汽車", "紡織"],
    "consumer": ["食品", "零售", "觀光", "餐飲"],
    "healthcare": ["生技醫療", "製藥", "醫療器材"],
    "energy": ["油電燃氣", "能源", "綠能"],
    "real_estate": ["營建", "不動產"],
    "telecom": ["電信", "通信網路"],
}

# 風險評估配置
RISK_ASSESSMENT_CONFIG = {
    "volatility_thresholds": {"low": 0.2, "medium": 0.4, "high": 0.6},
    "beta_thresholds": {"defensive": 0.8, "neutral": 1.0, "aggressive": 1.2},
    "liquidity_thresholds": {"low": 1000000, "medium": 5000000, "high": 10000000},
}
