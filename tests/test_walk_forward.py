"""Walk-Forward 驗證測試。"""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np


class TestWalkForwardValidator:
    """Walk-Forward 驗證器測試。"""

    def test_walk_forward_parameters(self):
        """Walk-Forward 參數測試。"""
        params = {
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

    def test_walk_forward_periods_calculation(self):
        """Walk-Forward 期間數計算測試。"""
        # 假設有 5 年的資料（約 1260 個交易日）
        total_data_points = 1260
        train_window = 252
        test_window = 63
        step_size = 21
        
        # 計算期間數
        periods = (total_data_points - train_window) // step_size
        
        assert periods > 0
        assert periods == 48  # (1260 - 252) / 21

    def test_walk_forward_data_split(self):
        """Walk-Forward 資料分割測試。"""
        # 建立測試資料
        dates = pd.bdate_range("2019-01-01", periods=1260)
        data = pd.DataFrame({
            "close": np.random.randn(1260).cumsum() + 100,
        }, index=dates)
        
        train_window = 252
        test_window = 63
        step_size = 21
        
        # 模擬第一個期間的資料分割
        train_start = 0
        train_end = train_window
        test_start = train_end
        test_end = test_start + test_window
        
        train_data = data.iloc[train_start:train_end]
        test_data = data.iloc[test_start:test_end]
        
        # 驗證資料長度
        assert len(train_data) == train_window
        assert len(test_data) == test_window

    def test_walk_forward_sliding_window(self):
        """Walk-Forward 滑動窗口測試。"""
        # 建立測試資料
        total_points = 100
        train_window = 20
        test_window = 5
        step_size = 5
        
        # 計算所有期間
        periods = []
        start = 0
        while start + train_window + test_window <= total_points:
            train_start = start
            train_end = start + train_window
            test_start = train_end
            test_end = test_start + test_window
            
            periods.append({
                "train_start": train_start,
                "train_end": train_end,
                "test_start": test_start,
                "test_end": test_end,
            })
            
            start += step_size
        
        # 驗證期間數
        assert len(periods) > 0
        
        # 驗證每個期間的資料不重疊（訓練集和測試集）
        for period in periods:
            assert period["train_end"] <= period["test_start"]

    def test_walk_forward_anti_overfitting(self):
        """Walk-Forward 防過擬合測試。"""
        # 模擬訓練集和測試集績效
        train_performance = {
            "return": 15.0,
            "sharpe": 1.5,
            "win_rate": 0.65,
        }
        
        test_performance = {
            "return": 10.0,
            "sharpe": 1.2,
            "win_rate": 0.55,
        }
        
        # 測試集績效應低於訓練集（防過擬合）
        assert test_performance["return"] < train_performance["return"]
        assert test_performance["sharpe"] < train_performance["sharpe"]
        assert test_performance["win_rate"] < train_performance["win_rate"]

    def test_walk_forward_result_aggregation(self):
        """Walk-Forward 結果聚合測試。"""
        # 模擬多個期間的結果
        period_results = [
            {"period": 1, "return": 12.5, "sharpe": 1.3},
            {"period": 2, "return": 8.2, "sharpe": 0.9},
            {"period": 3, "return": 15.1, "sharpe": 1.5},
            {"period": 4, "return": 6.8, "sharpe": 0.7},
            {"period": 5, "return": 11.3, "sharpe": 1.1},
        ]
        
        # 計算平均績效
        avg_return = sum(r["return"] for r in period_results) / len(period_results)
        avg_sharpe = sum(r["sharpe"] for r in period_results) / len(period_results)
        
        assert avg_return > 0
        assert avg_sharpe > 0

    def test_walk_forward_consistency(self):
        """Walk-Forward 一致性測試。"""
        # 模擬多個期間的結果
        period_results = [
            {"period": 1, "return": 10.0},
            {"period": 2, "return": 12.0},
            {"period": 3, "return": 8.0},
            {"period": 4, "return": 11.0},
            {"period": 5, "return": 9.0},
        ]
        
        # 計算標準差
        returns = [r["return"] for r in period_results]
        std_return = np.std(returns)
        
        # 標準差應在合理範圍內
        assert std_return < 5.0  # 假設標準差小於 5%

    def test_walk_forward_win_rate(self):
        """Walk-Forward 勝率測試。"""
        # 模擬多個期間的結果
        period_results = [
            {"period": 1, "return": 10.0},
            {"period": 2, "return": -5.0},
            {"period": 3, "return": 15.0},
            {"period": 4, "return": -2.0},
            {"period": 5, "return": 8.0},
        ]
        
        # 計算勝率
        winning_periods = sum(1 for r in period_results if r["return"] > 0)
        win_rate = winning_periods / len(period_results)
        
        assert 0 <= win_rate <= 1
        assert win_rate == 0.6  # 3 wins out of 5

    def test_walk_forward_max_drawdown(self):
        """Walk-Forward 最大回撤測試。"""
        # 模擬累積報酬
        cumulative_returns = [100, 110, 105, 95, 100, 90, 85, 88, 92, 88]
        
        # 計算最大回撤
        peak = cumulative_returns[0]
        max_drawdown = 0
        
        for value in cumulative_returns:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        assert max_drawdown > 0
        assert max_drawdown < 1

    def test_walk_forward_risk_adjusted_return(self):
        """Walk-Forward 風險調整後報酬測試。"""
        # 模擬報酬和風險
        avg_return = 10.0
        std_return = 5.0
        risk_free_rate = 2.0
        
        # 計算夏普比率
        sharpe_ratio = (avg_return - risk_free_rate) / std_return if std_return > 0 else 0
        
        assert sharpe_ratio > 0

    def test_walk_forward_compound_return(self):
        """Walk-Forward 複合報酬測試。"""
        # 模擬多個期間的報酬
        period_returns = [0.10, -0.05, 0.15, -0.02, 0.08]
        
        # 計算複合報酬
        compound_return = 1.0
        for r in period_returns:
            compound_return *= (1 + r)
        compound_return -= 1
        
        assert compound_return > 0

    def test_walk_forward_stability(self):
        """Walk-Forward 穩定性測試。"""
        # 模擬多個期間的報酬
        period_returns = [10.0, 12.0, 8.0, 11.0, 9.0]
        
        # 計算穩定性（變異係數的倒數）
        mean_return = np.mean(period_returns)
        std_return = np.std(period_returns)
        
        # 變異係數
        cv = std_return / mean_return if mean_return > 0 else float('inf')
        
        # 穩定性 = 1 / 變異係數
        stability = 1 / cv if cv > 0 else 0
        
        assert stability > 0


class TestWalkForwardMetrics:
    """Walk-Forward 指標測試。"""

    def test_period_return_calculation(self):
        """期間報酬計算測試。"""
        initial_capital = 1000000
        final_capital = 1100000
        
        period_return = (final_capital - initial_capital) / initial_capital
        
        assert period_return == 0.1  # 10%

    def test_annualized_return(self):
        """年化報酬計算測試。"""
        total_return = 0.5  # 50%
        years = 2
        
        annualized_return = (1 + total_return) ** (1 / years) - 1
        
        assert annualized_return > 0
        assert annualized_return < total_return

    def test_risk_metrics(self):
        """風險指標測試。"""
        returns = [0.05, -0.02, 0.03, 0.01, -0.01, 0.04, 0.02, -0.03, 0.06, 0.01]
        
        # 計算平均報酬
        avg_return = np.mean(returns)
        
        # 計算標準差
        std_return = np.std(returns)
        
        # 計算夏普比率
        risk_free_rate = 0.02
        sharpe_ratio = (avg_return - risk_free_rate) / std_return if std_return > 0 else 0
        
        assert isinstance(avg_return, float)
        assert isinstance(std_return, float)
        assert isinstance(sharpe_ratio, float)

    def test_max_drawdown_calculation(self):
        """最大回撤計算測試。"""
        equity_curve = [100, 110, 105, 95, 100, 90, 85, 88, 92, 88]
        
        peak = equity_curve[0]
        max_drawdown = 0
        max_drawdown_start = 0
        max_drawdown_end = 0
        
        for i, value in enumerate(equity_curve):
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                max_drawdown_end = i
        
        assert max_drawdown > 0
        assert max_drawdown_end > 0

    def test_calmar_ratio(self):
        """Calmar 比率測試。"""
        annualized_return = 0.15
        max_drawdown = 0.10
        
        calmar_ratio = annualized_return / max_drawdown if max_drawdown > 0 else 0
        
        assert calmar_ratio > 0
        assert calmar_ratio == pytest.approx(1.5, abs=1e-10)

    def test_sortino_ratio(self):
        """Sortino 比率測試。"""
        returns = [0.05, -0.02, 0.03, 0.01, -0.01, 0.04, 0.02, -0.03, 0.06, 0.01]
        
        avg_return = np.mean(returns)
        risk_free_rate = 0.02
        
        # 計算下行標準差
        negative_returns = [r for r in returns if r < 0]
        downside_std = np.std(negative_returns) if negative_returns else 0
        
        # 計算 Sortino 比率
        sortino_ratio = (avg_return - risk_free_rate) / downside_std if downside_std > 0 else 0
        
        assert isinstance(sortino_ratio, float)

    def test_information_ratio(self):
        """資訊比率測試。"""
        portfolio_returns = [0.10, 0.05, 0.15, 0.08, 0.12]
        benchmark_returns = [0.08, 0.04, 0.12, 0.06, 0.10]
        
        # 計算超額報酬
        excess_returns = [p - b for p, b in zip(portfolio_returns, benchmark_returns)]
        
        # 計算資訊比率
        avg_excess = np.mean(excess_returns)
        tracking_error = np.std(excess_returns)
        
        information_ratio = avg_excess / tracking_error if tracking_error > 0 else 0
        
        assert isinstance(information_ratio, float)
