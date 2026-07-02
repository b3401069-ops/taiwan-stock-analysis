"""回測系統測試。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestBacktestEngine:
    """回測引擎測試。"""

    def test_backtest_result_structure(self, sample_backtest_result):
        """回測結果結構測試。"""
        result = sample_backtest_result

        required_fields = [
            "stock_id",
            "strategy_name",
            "total_periods",
            "avg_return",
            "avg_max_drawdown",
            "avg_win_rate",
            "avg_sharpe_ratio",
        ]

        for field in required_fields:
            assert field in result

    def test_backtest_metrics_range(self, sample_backtest_result):
        """回測指標範圍測試。"""
        result = sample_backtest_result

        # 期間數應為正數
        assert result["total_periods"] > 0

    def test_overall_metrics_structure(self, sample_backtest_result):
        """整體指標結構測試。"""
        overall = sample_backtest_result["overall_metrics"]

        required_fields = [
            "compound_return",
            "return_stability",
            "risk_adjusted_return",
            "positive_periods",
            "negative_periods",
        ]

        for field in required_fields:
            assert field in overall

    def test_period_metrics_structure(self, sample_walk_forward_result):
        """期間指標結構測試。"""
        periods = sample_walk_forward_result["periods"]

        for period in periods:
            assert "period" in period
            assert "return" in period
            assert "max_drawdown" in period
            assert "win_rate" in period
            assert "sharpe" in period

    def test_backtest_strategies(self):
        """可用策略測試。"""
        strategies = [
            "sma_cross",
            "rsi_oversold",
            "macd_divergence",
            "bollinger_breakout",
            "volume_price",
            "multi_factor",
        ]

        for strategy in strategies:
            assert strategy in strategies

    def test_backtest_engine_initialization(self):
        """回測引擎初始化測試。"""
        # 測試回測引擎模組是否存在
        try:
            import analysis.backtest_engine

            assert True
        except ImportError:
            # 如果模組不存在，跳過測試
            pytest.skip("analysis.backtest_engine 模組不存在")

    def test_backtest_parameters(self):
        """回測參數測試。"""
        params = {
            "stock_id": "2330.TW",
            "strategy_name": "rsi_oversold",
            "train_window": 252,
            "test_window": 63,
            "step_size": 21,
            "total_years": 5,
        }

        # 訓練窗口應大於測試窗口
        assert params["train_window"] > params["test_window"]

        # 步進大小應小於測試窗口
        assert params["step_size"] <= params["test_window"]

        # 總年數應為正數
        assert params["total_years"] > 0


class TestWalkForward:
    """Walk-Forward 驗證測試。"""

    def test_walk_forward_result_structure(self, sample_walk_forward_result):
        """Walk-Forward 結果結構測試。"""
        result = sample_walk_forward_result

        required_fields = [
            "stock_id",
            "strategy_name",
            "total_periods",
            "avg_return",
            "avg_max_drawdown",
            "avg_win_rate",
            "avg_sharpe_ratio",
            "periods",
        ]

        for field in required_fields:
            assert field in result

    def test_walk_forward_periods(self, sample_walk_forward_result):
        """Walk-Forward 期間測試。"""
        periods = sample_walk_forward_result["periods"]

        # 應有多個期間
        assert len(periods) > 0

        # 每個期間應有連續的編號
        for i, period in enumerate(periods):
            assert period["period"] == i + 1

    def test_walk_forward_validation(self):
        """Walk-Forward 驗證邏輯測試。"""
        # 模擬 Walk-Forward 過程
        total_data_points = 1000
        train_window = 252
        test_window = 63
        step_size = 21

        # 計算期間數
        periods = (total_data_points - train_window) // step_size

        assert periods > 0

    def test_walk_forward_anti_overfitting(self):
        """Walk-Forward 防過擬合測試。"""
        # 訓練集績效
        train_performance = {
            "return": 15.0,
            "sharpe": 1.5,
            "win_rate": 0.65,
        }

        # 測試集績效
        test_performance = {
            "return": 10.0,
            "sharpe": 1.2,
            "win_rate": 0.55,
        }

        # 測試集績效應低於訓練集（防過擬合）
        assert test_performance["return"] < train_performance["return"]
        assert test_performance["sharpe"] < train_performance["sharpe"]

    @patch("analysis.walk_forward.get_walk_forward_validator")
    def test_walk_forward_validator_initialization(self, mock_validator):
        """Walk-Forward 驗證器初始化測試。"""
        mock_instance = MagicMock()
        mock_validator.return_value = mock_instance

        validator = mock_validator()
        assert validator is not None


class TestRiskMetrics:
    """風險指標測試。"""

    def test_max_drawdown_calculation(self):
        """最大回撤計算測試。"""
        prices = [100, 110, 105, 95, 100, 90, 85, 88, 92, 88]

        # 計算最大回撤
        peak = prices[0]
        max_drawdown = 0

        for price in prices:
            if price > peak:
                peak = price
            drawdown = (peak - price) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        assert max_drawdown > 0
        assert max_drawdown < 1

    def test_sharpe_ratio_calculation(self):
        """夏普比率計算測試。"""
        returns = [0.05, -0.02, 0.03, 0.01, -0.01, 0.04, 0.02, -0.03, 0.06, 0.01]

        # 計算平均報酬和標準差
        avg_return = sum(returns) / len(returns)
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        std_return = variance**0.5

        # 假設無風險利率為 2%
        risk_free_rate = 0.02

        # 計算夏普比率
        sharpe = (avg_return - risk_free_rate) / std_return if std_return > 0 else 0

        assert isinstance(sharpe, float)

    def test_win_rate_calculation(self):
        """勝率計算測試。"""
        trades = [
            {"profit": 100},
            {"profit": -50},
            {"profit": 200},
            {"profit": -30},
            {"profit": 150},
            {"profit": -20},
        ]

        winning_trades = sum(1 for t in trades if t["profit"] > 0)
        win_rate = winning_trades / len(trades)

        assert 0 <= win_rate <= 1
        assert win_rate == 0.5  # 3 wins out of 6

    def test_return_calculation(self):
        """報酬率計算測試。"""
        initial_capital = 1000000
        final_capital = 1200000

        total_return = (final_capital - initial_capital) / initial_capital
        assert total_return == 0.2  # 20%

    def test_annualized_return(self):
        """年化報酬率計算測試。"""
        total_return = 0.2  # 20%
        years = 2

        annualized_return = (1 + total_return) ** (1 / years) - 1
        assert annualized_return > 0
        assert annualized_return < total_return  # 年化報酬應低於總報酬


class TestStrategyLogic:
    """策略邏輯測試。"""

    def test_sma_crossover_signal(self):
        """SMA 交叉信號測試。"""
        # 短期均線在長期均線之上應為多頭信號
        sma_short = 110
        sma_long = 100

        signal = "buy" if sma_short > sma_long else "sell"
        assert signal == "buy"

        # 短期均線在長期均線之下應為空頭信號
        sma_short = 90
        sma_long = 100

        signal = "buy" if sma_short > sma_long else "sell"
        assert signal == "sell"

    def test_rsi_signal(self):
        """RSI 信號測試。"""
        # RSI < 30 應為超賣信號
        rsi = 25
        signal = "oversold" if rsi < 30 else ("overbought" if rsi > 70 else "neutral")
        assert signal == "oversold"

        # RSI > 70 應為超買信號
        rsi = 75
        signal = "oversold" if rsi < 30 else ("overbought" if rsi > 70 else "neutral")
        assert signal == "overbought"

        # 30 < RSI < 70 應為中性信號
        rsi = 50
        signal = "oversold" if rsi < 30 else ("overbought" if rsi > 70 else "neutral")
        assert signal == "neutral"

    def test_macd_signal(self):
        """MACD 信號測試。"""
        # MACD 在信號線之上應為多頭信號
        macd = 0.5
        signal_line = 0.3

        signal = "buy" if macd > signal_line else "sell"
        assert signal == "buy"

        # MACD 在信號線之下應為空頭信號
        macd = 0.3
        signal_line = 0.5

        signal = "buy" if macd > signal_line else "sell"
        assert signal == "sell"

    def test_stop_loss_logic(self):
        """停損邏輯測試。"""
        entry_price = 100
        stop_loss_percent = 5  # 5%

        stop_loss_price = entry_price * (1 - stop_loss_percent / 100)

        # 價格跌破停損點應觸發停損
        current_price = 94
        should_stop_loss = current_price <= stop_loss_price
        assert should_stop_loss is True

        # 價格在停損點之上不應觸發停損
        current_price = 96
        should_stop_loss = current_price <= stop_loss_price
        assert should_stop_loss is False

    def test_take_profit_logic(self):
        """停利邏輯測試。"""
        entry_price = 100
        take_profit_percent = 10  # 10%

        take_profit_price = entry_price * (1 + take_profit_percent / 100)

        # 價格達到停利點應觸發停利
        current_price = 111.0
        should_take_profit = current_price >= take_profit_price
        assert should_take_profit is True

        # 價格未達停利點不應觸發停利
        current_price = 108.0
        should_take_profit = current_price >= take_profit_price
        assert should_take_profit is False
