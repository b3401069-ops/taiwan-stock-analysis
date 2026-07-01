"""共用 fixtures — in-memory DB、mock 資料、測試工具。"""

from __future__ import annotations

import os
import sys
import json
import pandas as pd
import numpy as np
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# 確保專案根目錄在 Python path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def project_root():
    """專案根目錄路徑。"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture()
def sample_ohlcv():
    """建立 100 天的 OHLCV 測試資料。"""
    dates = pd.bdate_range("2024-01-01", periods=100)
    base_price = 100.0
    rows = []
    for i, dt in enumerate(dates):
        close = base_price + i * 0.5 + np.random.normal(0, 0.5)
        rows.append(
            {
                "date": dt.date(),
                "open": close - 0.3 + np.random.normal(0, 0.1),
                "high": close + 1.0 + abs(np.random.normal(0, 0.3)),
                "low": close - 1.0 - abs(np.random.normal(0, 0.3)),
                "close": close,
                "volume": 1_000_000 + i * 10_000 + np.random.randint(-50000, 50000),
            }
        )
    df = pd.DataFrame(rows).set_index("date")
    return df


@pytest.fixture()
def sample_stock_info():
    """建立股票基本資訊測試資料。"""
    return {
        "stock_id": "2330.TW",
        "name": "台積電",
        "market": "上市",
        "industry": "半導體",
        "list_date": "1994-09-05",
    }


@pytest.fixture()
def sample_price_data():
    """建立價格資料測試資料。"""
    return {
        "period": "6mo",
        "data": [
            {"date": "2024-01-02", "open": 580.0, "high": 585.0, "low": 575.0, "close": 582.0, "volume": 25000000},
            {"date": "2024-01-03", "open": 582.0, "high": 590.0, "low": 580.0, "close": 588.0, "volume": 28000000},
            {"date": "2024-01-04", "open": 588.0, "high": 595.0, "low": 586.0, "close": 592.0, "volume": 30000000},
        ],
        "summary": {
            "start_date": "2024-01-02",
            "end_date": "2024-01-04",
            "latest_price": 592.0,
            "highest_price": 595.0,
            "lowest_price": 575.0,
            "average_price": 587.33,
        },
    }


@pytest.fixture()
def sample_industry_ranking():
    """建立產業排名測試資料。"""
    return [
        {
            "rank": 1,
            "industry": "半導體",
            "strength_score": 0.8424,
            "signal": "strong_buy",
            "momentum_20d": "11.22%",
            "momentum_60d": "23.45%",
            "relative_strength": "15.67%",
            "description": "IC 設計、晶圓代工、封測、設備",
        },
        {
            "rank": 2,
            "industry": "AI 概念",
            "strength_score": 0.7035,
            "signal": "strong_buy",
            "momentum_20d": "6.53%",
            "momentum_60d": "18.90%",
            "relative_strength": "12.34%",
            "description": "AI 伺服器、AI 晶片、AI 應用",
        },
    ]


@pytest.fixture()
def sample_concept_ranking():
    """建立概念股排名測試資料。"""
    return [
        {
            "rank": 1,
            "concept": "被動元件",
            "description": "電容、電阻等被動元件",
            "heat_score": 0.8682,
            "trend": "hot",
            "avg_momentum_20d": "31.34%",
            "avg_momentum_60d": "45.67%",
            "avg_volume_ratio": 2.15,
            "total_institutional_flow": "12.34億",
            "stock_count": 3,
        },
        {
            "rank": 2,
            "concept": "ABF 載板",
            "description": "ABF 載板產業，用於先進晶片封裝",
            "heat_score": 0.8285,
            "trend": "hot",
            "avg_momentum_20d": "16.53%",
            "avg_momentum_60d": "28.90%",
            "avg_volume_ratio": 1.85,
            "total_institutional_flow": "8.56億",
            "stock_count": 3,
        },
    ]


@pytest.fixture()
def sample_screener_result():
    """建立多因子選股結果測試資料。"""
    return [
        {
            "rank": 1,
            "stock_id": "2330.TW",
            "stock_name": "台積電",
            "composite_score": 0.7234,
            "details": {
                "current_price": 2450.0,
                "pe_ratio": 18.5,
                "pb_ratio": 5.2,
                "dividend_yield": 2.5,
                "momentum_score": 0.85,
                "value_score": 0.65,
                "quality_score": 0.78,
            },
        },
        {
            "rank": 2,
            "stock_id": "2454.TW",
            "stock_name": "聯發科",
            "composite_score": 0.6891,
            "details": {
                "current_price": 1200.0,
                "pe_ratio": 22.3,
                "pb_ratio": 4.8,
                "dividend_yield": 1.8,
                "momentum_score": 0.72,
                "value_score": 0.58,
                "quality_score": 0.82,
            },
        },
    ]


@pytest.fixture()
def sample_market_regime():
    """建立市場狀態測試資料。"""
    return {
        "regime": "bull",
        "regime_name": "多頭",
        "confidence": 75,
        "suggestion": {
            "action": "積極佈局",
            "reason": "加權指數站上所有均線，成交量放大",
            "position_size": "70-90%",
            "strategy": "積極成長策略",
        },
    }


@pytest.fixture()
def sample_ai_summary():
    """建立 AI 選股摘要測試資料。"""
    return {
        "timestamp": datetime.now().isoformat(),
        "report_type": "AI 選股摘要",
        "executive_summary": "📊 AI 選股摘要報告\n\n【市場狀態】\n目前市場處於多頭狀態，信心水平 75%。",
        "investment_advice": {
            "market_advice": "市場處於多頭格局，可積極佈局",
            "position_size": "70-90%",
            "overall_strategy": "積極成長策略",
            "stock_recommendations": [
                {"rank": 1, "stock_id": "2330.TW", "stock_name": "台積電", "composite_score": 0.7234},
                {"rank": 2, "stock_id": "2454.TW", "stock_name": "聯發科", "composite_score": 0.6891},
            ],
        },
        "risk_warnings": [
            "📊 所有分析僅供參考，不構成投資建議",
            "💰 投資有風險，請謹慎評估",
        ],
    }


@pytest.fixture()
def mock_api_response():
    """建立 mock API 回應。"""
    def _mock_response(success=True, data=None, error=None):
        response = Mock()
        response.status_code = 200 if success else 500
        response.json.return_value = {
            "success": success,
            "data": data or {},
            "error": error,
        }
        return response
    return _mock_response


@pytest.fixture()
def mock_requests_get(mock_api_response):
    """Mock requests.get。"""
    with patch("requests.get") as mock_get:
        mock_get.return_value = mock_api_response()
        yield mock_get


@pytest.fixture()
def mock_requests_post(mock_api_response):
    """Mock requests.post。"""
    with patch("requests.post") as mock_post:
        mock_post.return_value = mock_api_response()
        yield mock_post


@pytest.fixture()
def watchlist_file(tmp_path):
    """建立臨時關注清單檔案。"""
    watchlist = [
        {"stock_id": "2330", "name": "台積電", "added_date": "2024-01-01T00:00:00", "notes": ""},
        {"stock_id": "2317", "name": "鴻海", "added_date": "2024-01-01T00:00:00", "notes": ""},
    ]
    file_path = tmp_path / "watchlist.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(watchlist, f, ensure_ascii=False, indent=2)
    return str(file_path)


@pytest.fixture()
def sample_valuation():
    """建立估值指標測試資料。"""
    return {
        "current_price": 2450.0,
        "pe_ratio": 18.5,
        "pb_ratio": 5.2,
        "dividend_yield": 2.5,
        "ev_ebitda": 12.3,
        "peg_ratio": 1.2,
        "free_cash_flow_yield": 3.8,
        "valuation_rating": "合理",
    }


@pytest.fixture()
def sample_backtest_result():
    """建立回測結果測試資料。"""
    return {
        "stock_id": "2330.TW",
        "strategy_name": "rsi_oversold",
        "total_periods": 20,
        "avg_return": "12.34%",
        "avg_max_drawdown": "-8.56%",
        "avg_win_rate": "65.00%",
        "avg_sharpe_ratio": "1.23",
        "overall_metrics": {
            "compound_return": "45.67%",
            "return_stability": "0.85",
            "risk_adjusted_return": "1.45",
            "positive_periods": 16,
            "negative_periods": 4,
        },
    }


@pytest.fixture()
def sample_walk_forward_result():
    """建立 Walk-Forward 驗證測試資料。"""
    return {
        "stock_id": "2330.TW",
        "strategy_name": "rsi_oversold",
        "total_periods": 20,
        "avg_return": "12.34%",
        "avg_max_drawdown": "-8.56%",
        "avg_win_rate": "65.00%",
        "avg_sharpe_ratio": "1.23",
        "periods": [
            {"period": 1, "return": "15.5%", "max_drawdown": "-5.2%", "win_rate": "70%", "sharpe": "1.45"},
            {"period": 2, "return": "8.2%", "max_drawdown": "-12.1%", "win_rate": "55%", "sharpe": "0.89"},
        ],
    }


@pytest.fixture()
def sample_notification_history():
    """建立通知歷史測試資料。"""
    return [
        {
            "type": "discord",
            "content": "測試訊息",
            "timestamp": datetime.now().isoformat(),
            "success": True,
        },
        {
            "type": "line",
            "content": "股票警報",
            "timestamp": datetime.now().isoformat(),
            "success": True,
        },
    ]


@pytest.fixture()
def sample_factor_weights():
    """建立因子權重測試資料。"""
    return {
        "momentum": 0.2,
        "value": 0.25,
        "quality": 0.25,
        "size": 0.1,
        "liquidity": 0.1,
        "institutional": 0.1,
    }


@pytest.fixture()
def sample_portfolio_position():
    """建立投資組合持倉測試資料。"""
    return {
        "stock_id": "2330.TW",
        "stock_name": "台積電",
        "shares": 1000,
        "avg_price": 2400.0,
        "current_price": 2450.0,
        "market_value": 2450000.0,
        "profit_loss": 50000.0,
        "profit_loss_percent": 2.08,
    }


@pytest.fixture()
def sample_trade_history():
    """建立交易歷史測試資料。"""
    return [
        {
            "trade_id": "T001",
            "stock_id": "2330.TW",
            "stock_name": "台積電",
            "action": "buy",
            "shares": 1000,
            "price": 2400.0,
            "total": 2400000.0,
            "timestamp": "2024-01-15T10:30:00",
        },
        {
            "trade_id": "T002",
            "stock_id": "2330.TW",
            "stock_name": "台積電",
            "action": "sell",
            "shares": 500,
            "price": 2450.0,
            "total": 1225000.0,
            "timestamp": "2024-01-20T14:15:00",
        },
    ]
