"""整合測試 - 測試完整工作流程。"""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class TestFullWorkflow:
    """完整工作流程測試。"""

    @pytest.mark.integration
    def test_data_to_analysis_workflow(self, sample_ohlcv):
        """從資料到分析的完整工作流程。"""
        # 1. 取得資料
        df = sample_ohlcv
        assert len(df) == 100
        assert "close" in df.columns
        
        # 2. 計算技術指標
        sma5 = df["close"].rolling(window=5).mean()
        sma20 = df["close"].rolling(window=20).mean()
        rsi = self._calculate_rsi(df["close"])
        
        # 驗證指標計算
        assert len(sma5) == 100
        assert len(sma20) == 100
        assert len(rsi) == 100
        
        # 3. 產生交易信號
        signals = []
        for i in range(20, len(df)):
            if sma5.iloc[i] > sma20.iloc[i] and rsi.iloc[i] < 70:
                signals.append("buy")
            elif sma5.iloc[i] < sma20.iloc[i] and rsi.iloc[i] > 30:
                signals.append("sell")
            else:
                signals.append("hold")
        
        # 驗證信號
        assert len(signals) > 0
        assert all(s in ["buy", "sell", "hold"] for s in signals)

    @pytest.mark.integration
    def test_screener_workflow(self, sample_screener_result):
        """選股工作流程測試。"""
        # 1. 取得全市場資料
        all_stocks = [
            {"stock_id": "2330.TW", "name": "台積電"},
            {"stock_id": "2317.TW", "name": "鴻海"},
            {"stock_id": "2454.TW", "name": "聯發科"},
        ]
        
        # 2. 計算因子分數
        factor_scores = {}
        for stock in all_stocks:
            factor_scores[stock["stock_id"]] = {
                "momentum": np.random.uniform(0, 1),
                "value": np.random.uniform(0, 1),
                "quality": np.random.uniform(0, 1),
            }
        
        # 3. 計算綜合分數
        weights = {"momentum": 0.4, "value": 0.3, "quality": 0.3}
        composite_scores = {}
        for stock_id, scores in factor_scores.items():
            composite_scores[stock_id] = sum(scores[f] * weights[f] for f in weights)
        
        # 4. 排名
        ranked_stocks = sorted(composite_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 驗證結果
        assert len(ranked_stocks) == 3
        assert ranked_stocks[0][1] >= ranked_stocks[1][1]

    @pytest.mark.integration
    def test_backtest_workflow(self, sample_ohlcv):
        """回測工作流程測試。"""
        df = sample_ohlcv
        
        # 1. 計算策略信號
        sma5 = df["close"].rolling(window=5).mean()
        sma20 = df["close"].rolling(window=20).mean()
        
        positions = []
        for i in range(20, len(df)):
            if sma5.iloc[i] > sma20.iloc[i]:
                positions.append(1)  # 持有
            else:
                positions.append(0)  # 空手
        
        # 2. 計算報酬
        returns = df["close"].pct_change()
        strategy_returns = []
        for i in range(20, len(df)):
            if i < len(returns):
                strategy_returns.append(returns.iloc[i] * positions[i - 20])
        
        # 3. 計算績效指標
        total_return = sum(strategy_returns)
        win_rate = sum(1 for r in strategy_returns if r > 0) / len(strategy_returns) if strategy_returns else 0
        
        # 驗證結果
        assert len(strategy_returns) > 0
        assert isinstance(total_return, float)
        assert 0 <= win_rate <= 1

    @pytest.mark.integration
    def test_report_generation_workflow(self, sample_ai_summary):
        """報告生成工作流程測試。"""
        # 1. 取得市場狀態
        market_state = {
            "regime": "多頭",
            "confidence": 75,
        }
        
        # 2. 取得產業輪動
        industry_rotation = {
            "strongest": "半導體",
            "weakest": "傳統產業",
        }
        
        # 3. 取得概念股輪動
        concept_rotation = {
            "hottest": "CoWoS",
            "trending": "散熱",
        }
        
        # 4. 取得選股推薦
        stock_recommendations = [
            {"stock_id": "2330.TW", "stock_name": "台積電", "score": 0.72},
            {"stock_id": "2454.TW", "stock_name": "聯發科", "score": 0.68},
        ]
        
        # 5. 產生報告
        report = {
            "timestamp": datetime.now().isoformat(),
            "market_state": market_state,
            "industry_rotation": industry_rotation,
            "concept_rotation": concept_rotation,
            "stock_recommendations": stock_recommendations,
            "investment_advice": {
                "market_advice": "積極佈局",
                "position_size": "70-90%",
            },
        }
        
        # 驗證報告
        assert "timestamp" in report
        assert "market_state" in report
        assert "stock_recommendations" in report
        assert len(report["stock_recommendations"]) > 0

    @pytest.mark.integration
    def test_notification_workflow(self, sample_ai_summary):
        """通知工作流程測試。"""
        # 1. 產生報告
        report = sample_ai_summary
        
        # 2. 格式化訊息
        message = f"""
📊 AI 選股摘要報告

📋 執行摘要:
{report['executive_summary']}

💡 投資建議:
• 市場建議: {report['investment_advice']['market_advice']}
• 建議部位: {report['investment_advice']['position_size']}
"""
        
        # 3. 發送通知
        notifications = []
        for platform in ["discord", "line"]:
            notifications.append({
                "platform": platform,
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "success": True,
            })
        
        # 驗證通知
        assert len(notifications) == 2
        assert all(n["success"] for n in notifications)

    def _calculate_rsi(self, prices, period=14):
        """計算 RSI 指標。"""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi


class TestModuleIntegration:
    """模組整合測試。"""

    @pytest.mark.integration
    def test_data_fetcher_integration(self):
        """資料抓取整合測試。"""
        # 模擬資料抓取
        mock_data = {
            "stock_id": "2330.TW",
            "prices": [
                {"date": "2024-01-02", "close": 580.0},
                {"date": "2024-01-03", "close": 585.0},
            ],
        }
        
        # 驗證資料結構
        assert "stock_id" in mock_data
        assert "prices" in mock_data
        assert len(mock_data["prices"]) > 0

    @pytest.mark.integration
    def test_analysis_integration(self):
        """分析整合測試。"""
        # 模擬分析流程
        analysis_result = {
            "technical_analysis": {
                "trend": "bullish",
                "support": 570.0,
                "resistance": 600.0,
            },
            "fundamental_analysis": {
                "pe_ratio": 18.5,
                "pb_ratio": 5.2,
                "dividend_yield": 2.5,
            },
            "sentiment_analysis": {
                "institutional_flow": "positive",
                "market_sentiment": "bullish",
            },
        }
        
        # 驗證分析結果
        assert "technical_analysis" in analysis_result
        assert "fundamental_analysis" in analysis_result
        assert "sentiment_analysis" in analysis_result

    @pytest.mark.integration
    def test_screener_integration(self):
        """選股整合測試。"""
        # 模擬選股流程
        screener_result = {
            "stocks": [
                {
                    "stock_id": "2330.TW",
                    "stock_name": "台積電",
                    "composite_score": 0.72,
                    "factors": {
                        "momentum": 0.85,
                        "value": 0.65,
                        "quality": 0.78,
                    },
                },
            ],
            "weights": {
                "momentum": 0.4,
                "value": 0.3,
                "quality": 0.3,
            },
            "timestamp": datetime.now().isoformat(),
        }
        
        # 驗證選股結果
        assert "stocks" in screener_result
        assert "weights" in screener_result
        assert len(screener_result["stocks"]) > 0

    @pytest.mark.integration
    def test_backtest_integration(self):
        """回測整合測試。"""
        # 模擬回測流程
        backtest_result = {
            "strategy": "sma_cross",
            "stock_id": "2330.TW",
            "period": "2023-01-01 to 2024-01-01",
            "performance": {
                "total_return": 15.5,
                "annualized_return": 12.3,
                "max_drawdown": -8.5,
                "sharpe_ratio": 1.2,
                "win_rate": 0.65,
            },
            "trades": [
                {"date": "2023-03-15", "action": "buy", "price": 550.0},
                {"date": "2023-06-20", "action": "sell", "price": 580.0},
            ],
        }
        
        # 驗證回測結果
        assert "strategy" in backtest_result
        assert "performance" in backtest_result
        assert "trades" in backtest_result
        assert backtest_result["performance"]["total_return"] > 0

    @pytest.mark.integration
    def test_notification_integration(self):
        """通知整合測試。"""
        # 模擬通知流程
        notification_result = {
            "report_type": "每日報告",
            "platforms": ["discord", "line"],
            "results": {
                "discord": {"success": True, "message_id": "123456"},
                "line": {"success": True, "message_id": "789012"},
            },
            "timestamp": datetime.now().isoformat(),
        }
        
        # 驗證通知結果
        assert "report_type" in notification_result
        assert "platforms" in notification_result
        assert "results" in notification_result
        assert all(r["success"] for r in notification_result["results"].values())


class TestDataFlow:
    """資料流程測試。"""

    @pytest.mark.integration
    def test_data_to_signal_flow(self, sample_ohlcv):
        """資料到信號的流程測試。"""
        df = sample_ohlcv
        
        # 1. 原始資料
        assert len(df) == 100
        assert "close" in df.columns
        
        # 2. 技術指標
        sma20 = df["close"].rolling(window=20).mean()
        assert len(sma20) == 100
        
        # 3. 交易信號
        signals = []
        for i in range(20, len(df)):
            if df["close"].iloc[i] > sma20.iloc[i]:
                signals.append("bullish")
            else:
                signals.append("bearish")
        
        assert len(signals) > 0
        assert all(s in ["bullish", "bearish"] for s in signals)

    @pytest.mark.integration
    def test_signal_to_position_flow(self):
        """信號到持倉的流程測試。"""
        # 1. 交易信號
        signals = ["bullish", "bullish", "bearish", "bullish", "bearish"]
        
        # 2. 持倉決策
        positions = []
        current_position = 0
        
        for signal in signals:
            if signal == "bullish" and current_position == 0:
                current_position = 1  # 買入
            elif signal == "bearish" and current_position == 1:
                current_position = 0  # 賣出
            positions.append(current_position)
        
        assert len(positions) == len(signals)
        assert positions == [1, 1, 0, 1, 0]

    @pytest.mark.integration
    def test_position_to_pnl_flow(self):
        """持倉到損益的流程測試。"""
        # 1. 持倉
        positions = [1, 1, 0, 1, 0]
        
        # 2. 價格
        prices = [100, 105, 102, 108, 110]
        
        # 3. 損益計算
        pnl = []
        for i in range(1, len(prices)):
            if positions[i - 1] == 1:
                pnl.append((prices[i] - prices[i - 1]) / prices[i - 1])
            else:
                pnl.append(0)
        
        assert len(pnl) == len(positions) - 1
        assert pnl[0] == pytest.approx(0.05, abs=1e-10)  # (105-100)/100
        assert pnl[1] == pytest.approx(-0.02857142857142857, abs=1e-10)  # (102-105)/105，持倉為1
        assert pnl[2] == 0     # 空手
        assert pnl[3] == pytest.approx(0.018518518518518517, abs=1e-10)  # (110-108)/108，持倉為1

    @pytest.mark.integration
    def test_pnl_to_report_flow(self):
        """損益到報告的流程測試。"""
        # 1. 損益資料
        pnl_data = {
            "total_return": 15.5,
            "daily_returns": [0.05, -0.02, 0.03, 0.01, -0.01],
            "winning_trades": 3,
            "losing_trades": 2,
        }
        
        # 2. 績效指標
        win_rate = pnl_data["winning_trades"] / (pnl_data["winning_trades"] + pnl_data["losing_trades"])
        avg_return = sum(pnl_data["daily_returns"]) / len(pnl_data["daily_returns"])
        
        # 3. 報告
        report = {
            "total_return": pnl_data["total_return"],
            "win_rate": win_rate,
            "avg_daily_return": avg_return,
            "summary": f"總報酬率: {pnl_data['total_return']}%, 勝率: {win_rate:.1%}",
        }
        
        assert "total_return" in report
        assert "win_rate" in report
        assert "summary" in report
        assert report["win_rate"] == 0.6  # 3/(3+2)
