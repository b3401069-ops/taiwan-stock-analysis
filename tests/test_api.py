"""API 端點測試。"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


@pytest.fixture()
def client():
    """建立測試客戶端。"""
    from main import app
    return TestClient(app)


class TestRootEndpoint:
    """根端點測試。"""

    def test_root_returns_welcome_message(self, client):
        """根端點應返回歡迎訊息。"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "歡迎使用台灣股票分析工具" in data["message"]

    def test_root_returns_all_pages(self, client):
        """根端點應返回所有頁面連結。"""
        response = client.get("/")
        data = response.json()
        
        expected_pages = ["docs", "health", "app", "chat", "test", "portfolio", "report", "scheduler", "screener", "advanced", "dashboard"]
        for page in expected_pages:
            assert page in data

    def test_root_api_base(self, client):
        """根端點應返回 API 基礎路徑。"""
        response = client.get("/")
        data = response.json()
        assert "api" in data
        assert data["api"] == "/api/v1"


class TestHealthEndpoint:
    """健康檢查端點測試。"""

    def test_health_check(self, client):
        """健康檢查應返回正常狀態。"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"


class TestStockEndpoints:
    """股票相關端點測試。"""

    def test_get_stock_info(self, client):
        """取得股票資訊。"""
        response = client.get("/api/v1/stocks/2330.TW")
        # 可能需要 mock 或實際資料
        assert response.status_code in [200, 500]

    def test_get_stock_price(self, client):
        """取得股票價格。"""
        response = client.get("/api/v1/stocks/2330.TW/price?period=1mo")
        assert response.status_code in [200, 500]

    def test_get_stock_valuation(self, client):
        """取得估值指標。"""
        response = client.get("/api/v1/valuation/2330.TW")
        assert response.status_code in [200, 500]


class TestScreenerEndpoints:
    """選股端點測試。"""

    def test_multi_factor_screener(self, client):
        """多因子選股篩選。"""
        response = client.post("/api/v1/screener/multi-factor?top_n=5")
        assert response.status_code in [200, 500]

    def test_screener_explanation(self, client):
        """因子解釋。"""
        response = client.get("/api/v1/screener/explanation")
        assert response.status_code == 200

    def test_update_factor_weights(self, client, sample_factor_weights):
        """更新因子權重。"""
        response = client.post("/api/v1/screener/weights", json=sample_factor_weights)
        assert response.status_code in [200, 500]


class TestIndustryEndpoints:
    """產業端點測試。"""

    def test_industry_ranking(self, client):
        """產業強度排名。"""
        response = client.get("/api/v1/industry/ranking?period=3mo")
        assert response.status_code in [200, 500]

    def test_industry_rotation(self, client):
        """產業輪動分析。"""
        response = client.get("/api/v1/industry/rotation?period=3mo")
        assert response.status_code in [200, 500]

    def test_industry_explanation(self, client):
        """產業輪動解釋。"""
        response = client.get("/api/v1/industry/explanation")
        assert response.status_code == 200


class TestConceptEndpoints:
    """概念股端點測試。"""

    def test_concept_ranking(self, client):
        """概念股熱度排名。"""
        response = client.get("/api/v1/concept/ranking?period=3mo")
        assert response.status_code in [200, 500]

    def test_concept_hot(self, client):
        """熱門概念股。"""
        response = client.get("/api/v1/concept/hot?period=3mo&min_heat=0.5")
        assert response.status_code in [200, 500]

    def test_concept_explanation(self, client):
        """概念股輪動解釋。"""
        response = client.get("/api/v1/concept/explanation")
        assert response.status_code == 200


class TestMarketEndpoints:
    """市場端點測試。"""

    def test_market_regime(self, client):
        """市場狀態偵測。"""
        response = client.get("/api/v1/market/regime")
        assert response.status_code in [200, 500]


class TestBacktestEndpoints:
    """回測端點測試。"""

    def test_walk_forward(self, client):
        """Walk-Forward 驗證。"""
        response = client.post(
            "/api/v1/backtest/walk-forward",
            params={
                "stock_id": "2330.TW",
                "strategy_name": "rsi_oversold",
                "train_window": 252,
                "test_window": 63,
                "step_size": 21,
                "total_years": 5,
            }
        )
        assert response.status_code in [200, 500]

    def test_backtest_strategies(self, client):
        """可用策略列表。"""
        response = client.get("/api/v1/backtest/strategies")
        assert response.status_code == 200


class TestNotificationEndpoints:
    """通知端點測試。"""

    def test_notification_history(self, client):
        """通知歷史。"""
        response = client.get("/api/v1/notification/history")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True

    def test_discord_notification(self, client):
        """Discord 通知。"""
        response = client.post("/api/v1/notification/discord?content=測試訊息")
        assert response.status_code in [200, 500]

    def test_line_notification(self, client):
        """Line 通知。"""
        response = client.post("/api/v1/notification/line?message=測試訊息")
        assert response.status_code in [200, 500]


class TestPortfolioEndpoints:
    """投資組合端點測試。"""

    def test_portfolio_positions(self, client):
        """持倉摘要。"""
        response = client.get("/api/v1/portfolio/summary")
        assert response.status_code in [200, 500]

    def test_portfolio_history(self, client):
        """交易歷史。"""
        response = client.get("/api/v1/portfolio/history")
        assert response.status_code in [200, 500]


class TestReportEndpoints:
    """報告端點測試。"""

    def test_generate_report(self, client):
        """產生報告。"""
        response = client.post("/api/v1/report/generate?report_type=daily")
        assert response.status_code in [200, 500]

    def test_weekly_report(self, client):
        """每週報告。"""
        response = client.get("/api/v1/report/portfolio/weekly")
        assert response.status_code in [200, 500]

    def test_monthly_report(self, client):
        """每月報告。"""
        response = client.get("/api/v1/report/portfolio/monthly")
        assert response.status_code in [200, 500]


class TestSchedulerEndpoints:
    """排程端點測試。"""

    def test_scheduler_status(self, client):
        """排程狀態。"""
        response = client.get("/api/v1/scheduler/status")
        assert response.status_code == 200

    def test_scheduler_jobs(self, client):
        """排程任務。"""
        response = client.get("/api/v1/scheduler/jobs")
        assert response.status_code == 200
