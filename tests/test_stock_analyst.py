"""
AI 分析引擎測試
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest


# 模擬股票數據
def create_sample_stock_data(days=100):
    """生成模擬股票數據"""
    dates = pd.date_range(end=datetime.now(), periods=days, freq="B")
    np.random.seed(42)

    # 生成價格序列
    base_price = 100
    returns = np.random.normal(0.001, 0.02, days)
    prices = base_price * np.cumprod(1 + returns)

    df = pd.DataFrame(
        {
            "open": prices * (1 + np.random.uniform(-0.01, 0.01, days)),
            "high": prices * (1 + np.random.uniform(0, 0.02, days)),
            "low": prices * (1 - np.random.uniform(0, 0.02, days)),
            "close": prices,
            "volume": np.random.randint(1000000, 10000000, days),
        },
        index=dates,
    )

    return df


class TestStockAnalyst:
    """AI 分析引擎測試"""

    def setup_method(self):
        """測試前準備"""
        self.df = create_sample_stock_data(200)

    def test_trend_analysis(self):
        """測試趨勢分析"""
        from analysis.stock_analyst import StockAnalyst

        analyst = StockAnalyst()

        # 創建模擬技術指標
        tech_indicators = {"rsi": {"value": 55}, "macd": {"signal": "bullish"}}

        result = analyst._analyze_trend(self.df, tech_indicators)

        assert "short_term" in result
        assert "medium_term" in result
        assert "long_term" in result
        assert "score" in result
        assert result["short_term"] in ["up", "down"]
        assert result["medium_term"] in ["up", "down"]

    def test_recommendation_generation(self):
        """測試投資建議生成"""
        from analysis.stock_analyst import StockAnalyst

        analyst = StockAnalyst()

        # 模擬各種輸入
        latest_price = 100.0
        trend_analysis = {"score": 30, "short_term": "up", "medium_term": "up"}
        tech_summary = {"overall_signal": "bullish"}
        ml_summary = {"trend": "up", "expected_return": 0.05}
        tech_indicators = {
            "rsi": {"value": 45},
            "macd": {"signal": "bullish"},
            "bollinger": {"position": "middle"},
        }

        result = analyst._generate_recommendation(
            latest_price, trend_analysis, tech_summary, ml_summary, tech_indicators
        )

        assert "action" in result
        assert "score" in result
        assert "confidence" in result
        assert "risk_level" in result
        assert "reasons" in result
        assert result["action"] in ["buy", "buy_light", "sell", "sell_light", "hold"]

    def test_risk_assessment(self):
        """測試風險評估"""
        from analysis.stock_analyst import StockAnalyst

        analyst = StockAnalyst()

        tech_indicators = {
            "atr": {"value": 2.5},
            "rsi": {"value": 55},
            "trend": {"score": 30},
        }

        result = analyst._assess_risk(self.df, tech_indicators)

        assert "level" in result
        assert "score" in result
        assert "factors" in result
        assert result["level"] in ["high", "medium", "low"]

    def test_target_price_calculation(self):
        """測試目標價計算"""
        from analysis.stock_analyst import StockAnalyst

        analyst = StockAnalyst()

        current = 100.0
        trend = {"score": 50}
        ml = {"expected_return": 0.1}

        target = analyst._calculate_target_price(current, trend, ml)

        assert target > current  # 正報酬率時目標價應該更高

    def test_action_plan_generation(self):
        """測試操作計劃生成"""
        from analysis.stock_analyst import StockAnalyst

        analyst = StockAnalyst()

        recommendation = {
            "action": "buy",
            "target_price": 110,
            "stop_loss": 95,
            "reasons": ["技術指標看多"],
        }
        trend_analysis = {"score": 50}
        risk_assessment = {"level": "medium"}

        result = analyst._generate_action_plan(
            recommendation, trend_analysis, risk_assessment, 100.0, {}
        )

        assert "action" in result
        assert "steps" in result
        assert len(result["steps"]) > 0

    def test_text_summary_generation(self):
        """測試文字摘要生成"""
        from analysis.stock_analyst import StockAnalyst

        analyst = StockAnalyst()

        trend_analysis = {"short_term": "up", "medium_term": "up"}
        recommendation = {
            "action": "buy",
            "target_price": 110,
            "stop_loss": 95,
            "reasons": ["技術指標看多", "ML預測上漲"],
        }
        risk_assessment = {"level": "medium", "factors": ["波動率中等"]}

        result = analyst._generate_text_summary(
            "2330.TW", 100.0, trend_analysis, recommendation, risk_assessment
        )

        assert "2330.TW" in result
        assert "建議買入" in result
        assert "技術指標看多" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
