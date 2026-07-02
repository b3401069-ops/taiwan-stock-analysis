"""效能測試 - 測試大量資料處理。"""

from __future__ import annotations

import pytest
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class TestLargeDataProcessing:
    """大量資料處理測試。"""

    @pytest.mark.slow
    def test_large_dataset_creation(self):
        """大型資料集建立測試。"""
        # 建立 10,000 天的資料
        n_days = 10000
        dates = pd.bdate_range("2000-01-01", periods=n_days)
        
        # 建立 OHLCV 資料
        data = pd.DataFrame({
            "open": np.random.randn(n_days).cumsum() + 100,
            "high": np.random.randn(n_days).cumsum() + 102,
            "low": np.random.randn(n_days).cumsum() + 98,
            "close": np.random.randn(n_days).cumsum() + 100,
            "volume": np.random.randint(1000000, 10000000, n_days),
        }, index=dates)
        
        # 驗證資料
        assert len(data) == n_days
        assert len(data.columns) == 5
        
        # 驗證資料類型
        # 注意：np.random.randint 的預設整數型別因平台而異（Windows 為 int32、
        # Linux 為 int64），故以 np.integer 做平台無關的檢查。
        assert np.issubdtype(data["close"].dtype, np.floating)
        assert np.issubdtype(data["volume"].dtype, np.integer)

    @pytest.mark.slow
    def test_technical_indicators_performance(self):
        """技術指標計算效能測試。"""
        # 建立大型資料集
        n_days = 5000
        dates = pd.bdate_range("2000-01-01", periods=n_days)
        close = pd.Series(np.random.randn(n_days).cumsum() + 100, index=dates)
        
        # 測試 SMA 計算效能
        start_time = time.time()
        sma20 = close.rolling(window=20).mean()
        sma50 = close.rolling(window=50).mean()
        sma200 = close.rolling(window=200).mean()
        sma_time = time.time() - start_time
        
        # 測試 RSI 計算效能
        start_time = time.time()
        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        rsi_time = time.time() - start_time
        
        # 驗證結果
        assert len(sma20) == n_days
        assert len(rsi) == n_days
        
        # 驗證效能（每個計算應在 1 秒內完成）
        assert sma_time < 1.0, f"SMA 計算耗時 {sma_time:.2f} 秒"
        assert rsi_time < 1.0, f"RSI 計算耗時 {rsi_time:.2f} 秒"

    @pytest.mark.slow
    def test_screener_performance(self):
        """選股效能測試。"""
        # 模擬全市場選股
        n_stocks = 500
        stocks = [f"stock_{i:04d}" for i in range(n_stocks)]
        
        # 模擬因子計算
        start_time = time.time()
        
        factor_scores = {}
        for stock in stocks:
            factor_scores[stock] = {
                "momentum": np.random.uniform(0, 1),
                "value": np.random.uniform(0, 1),
                "quality": np.random.uniform(0, 1),
                "size": np.random.uniform(0, 1),
                "liquidity": np.random.uniform(0, 1),
                "institutional": np.random.uniform(0, 1),
            }
        
        # 計算綜合分數
        weights = {
            "momentum": 0.2,
            "value": 0.25,
            "quality": 0.25,
            "size": 0.1,
            "liquidity": 0.1,
            "institutional": 0.1,
        }
        
        composite_scores = {}
        for stock, scores in factor_scores.items():
            composite_scores[stock] = sum(scores[f] * weights[f] for f in weights)
        
        # 排名
        ranked_stocks = sorted(composite_scores.items(), key=lambda x: x[1], reverse=True)
        
        screener_time = time.time() - start_time
        
        # 驗證結果
        assert len(ranked_stocks) == n_stocks
        assert ranked_stocks[0][1] >= ranked_stocks[-1][1]
        
        # 驗證效能（應在 5 秒內完成）
        assert screener_time < 5.0, f"選股計算耗時 {screener_time:.2f} 秒"

    @pytest.mark.slow
    def test_backtest_performance(self):
        """回測效能測試。"""
        # 建立大型資料集
        n_days = 2000
        dates = pd.bdate_range("2015-01-01", periods=n_days)
        close = pd.Series(np.random.randn(n_days).cumsum() + 100, index=dates)
        
        # 模擬策略回測
        start_time = time.time()
        
        # 計算策略信號
        sma20 = close.rolling(window=20).mean()
        sma50 = close.rolling(window=50).mean()
        
        positions = []
        for i in range(50, n_days):
            if sma20.iloc[i] > sma50.iloc[i]:
                positions.append(1)
            else:
                positions.append(0)
        
        # 計算報酬
        returns = close.pct_change()
        strategy_returns = []
        for i in range(50, n_days):
            if i < len(returns):
                strategy_returns.append(returns.iloc[i] * positions[i - 50])
        
        # 計算績效
        total_return = sum(strategy_returns)
        win_rate = sum(1 for r in strategy_returns if r > 0) / len(strategy_returns) if strategy_returns else 0
        
        backtest_time = time.time() - start_time
        
        # 驗證結果
        assert len(strategy_returns) > 0
        assert isinstance(total_return, float)
        
        # 驗證效能（應在 2 秒內完成）
        assert backtest_time < 2.0, f"回測計算耗時 {backtest_time:.2f} 秒"

    @pytest.mark.slow
    def test_data_aggregation_performance(self):
        """資料聚合效能測試。"""
        # 建立大型資料集
        n_records = 100000
        dates = pd.bdate_range("2000-01-01", periods=n_records // 252)
        
        # 建立日頻資料
        daily_data = pd.DataFrame({
            "stock_id": np.random.choice(["2330.TW", "2317.TW", "2454.TW"], n_records),
            "date": np.random.choice(dates, n_records),
            "close": np.random.randn(n_records).cumsum() + 100,
            "volume": np.random.randint(1000000, 10000000, n_records),
        })
        
        # 測試聚合效能
        start_time = time.time()
        
        # 按股票和月份聚合
        daily_data["month"] = daily_data["date"].dt.to_period("M")
        monthly_agg = daily_data.groupby(["stock_id", "month"]).agg({
            "close": ["first", "last", "max", "min"],
            "volume": "sum",
        })
        
        agg_time = time.time() - start_time
        
        # 驗證結果
        assert len(monthly_agg) > 0
        
        # 驗證效能（應在 5 秒內完成）
        assert agg_time < 5.0, f"資料聚合耗時 {agg_time:.2f} 秒"

    @pytest.mark.slow
    def test_memory_usage(self):
        """記憶體使用測試。"""
        import sys
        
        # 建立大型資料集
        n_days = 10000
        dates = pd.bdate_range("2000-01-01", periods=n_days)
        
        # 建立 DataFrame
        data = pd.DataFrame({
            "open": np.random.randn(n_days),
            "high": np.random.randn(n_days),
            "low": np.random.randn(n_days),
            "close": np.random.randn(n_days),
            "volume": np.random.randint(1000000, 10000000, n_days),
        }, index=dates)
        
        # 測量記憶體使用
        memory_usage = data.memory_usage(deep=True).sum()
        
        # 驗證記憶體使用（應小於 100MB）
        assert memory_usage < 100 * 1024 * 1024, f"記憶體使用 {memory_usage / 1024 / 1024:.2f} MB"


class TestConcurrency:
    """並發測試。"""

    @pytest.mark.slow
    def test_parallel_processing(self):
        """並行處理測試。"""
        import concurrent.futures
        
        # 建立測試資料
        data_chunks = [
            np.random.randn(1000) for _ in range(10)
        ]
        
        # 定義處理函數
        def process_chunk(chunk):
            return {
                "mean": np.mean(chunk),
                "std": np.std(chunk),
                "min": np.min(chunk),
                "max": np.max(chunk),
            }
        
        # 並行處理
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(process_chunk, data_chunks))
        
        parallel_time = time.time() - start_time
        
        # 驗證結果
        assert len(results) == 10
        for result in results:
            assert "mean" in result
            assert "std" in result
        
        # 驗證效能（應在 2 秒內完成）
        assert parallel_time < 2.0, f"並行處理耗時 {parallel_time:.2f} 秒"

    @pytest.mark.slow
    def test_batch_processing(self):
        """批次處理測試。"""
        # 建立大型資料集
        n_stocks = 100
        stocks = [f"stock_{i:04d}" for i in range(n_stocks)]
        
        # 模擬批次處理
        start_time = time.time()
        
        batch_size = 10
        results = []
        
        for i in range(0, len(stocks), batch_size):
            batch = stocks[i:i + batch_size]
            
            # 處理批次
            batch_results = []
            for stock in batch:
                batch_results.append({
                    "stock_id": stock,
                    "score": np.random.uniform(0, 1),
                })
            
            results.extend(batch_results)
        
        batch_time = time.time() - start_time
        
        # 驗證結果
        assert len(results) == n_stocks
        
        # 驗證效能（應在 1 秒內完成）
        assert batch_time < 1.0, f"批次處理耗時 {batch_time:.2f} 秒"


class TestScalability:
    """擴展性測試。"""

    @pytest.mark.slow
    def test_data_scaling(self):
        """資料擴展性測試。"""
        # 測試不同規模的資料處理
        sizes = [1000, 5000, 10000]
        times = []
        
        for size in sizes:
            # 建立資料
            dates = pd.bdate_range("2000-01-01", periods=size)
            close = pd.Series(np.random.randn(size).cumsum() + 100, index=dates)
            
            # 測試計算效能
            start_time = time.time()
            
            sma20 = close.rolling(window=20).mean()
            sma50 = close.rolling(window=50).mean()
            
            calc_time = time.time() - start_time
            times.append(calc_time)
        
        # 驗證擴展性（時間應與資料量成正比）
        for i in range(1, len(times)):
            # 計時精度不足（運算過快，耗時量測為 0）時跳過比較，避免除以零
            if times[i - 1] == 0:
                continue
            # 允許一定的誤差
            ratio = times[i] / times[i - 1]
            size_ratio = sizes[i] / sizes[i - 1]

            # 時間比率應接近資料量比率
            assert ratio < size_ratio * 2, f"擴展性不佳: 時間比率 {ratio:.2f}, 資料量比率 {size_ratio:.2f}"

    @pytest.mark.slow
    def test_stock_scaling(self):
        """股票數量擴展性測試。"""
        # 測試不同股票數量的處理
        stock_counts = [10, 50, 100]
        times = []
        
        for n_stocks in stock_counts:
            # 建立模擬資料
            stocks = [f"stock_{i:04d}" for i in range(n_stocks)]
            
            # 測試選股效能
            start_time = time.time()
            
            scores = {}
            for stock in stocks:
                scores[stock] = np.random.uniform(0, 1)
            
            ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            
            calc_time = time.time() - start_time
            times.append(calc_time)
        
        # 驗證擴展性
        for i in range(1, len(times)):
            # 計時精度不足（運算過快，耗時量測為 0）時跳過比較，避免除以零
            if times[i - 1] == 0:
                continue
            ratio = times[i] / times[i - 1]
            stock_ratio = stock_counts[i] / stock_counts[i - 1]

            # 時間比率應接近股票數量比率
            assert ratio < stock_ratio * 2, f"擴展性不佳: 時間比率 {ratio:.2f}, 股票數量比率 {stock_ratio:.2f}"


class TestResourceUsage:
    """資源使用測試。"""

    @pytest.mark.slow
    def test_cpu_usage(self):
        """CPU 使用測試。"""
        import os
        
        # 測試計算效能
        start_time = time.time()
        
        # 執行計算密集任務
        n = 1000000
        data = np.random.randn(n)
        result = np.mean(data)
        
        calc_time = time.time() - start_time
        
        # 驗證結果
        assert isinstance(result, float)
        
        # 驗證效能（應在 1 秒內完成）
        assert calc_time < 1.0, f"計算耗時 {calc_time:.2f} 秒"

    @pytest.mark.slow
    def test_disk_io(self):
        """磁碟 I/O 測試。"""
        import tempfile
        import os
        
        # 建立測試資料
        n_records = 10000
        data = pd.DataFrame({
            "stock_id": [f"stock_{i:04d}" for i in range(n_records)],
            "close": np.random.randn(n_records).cumsum() + 100,
            "volume": np.random.randint(1000000, 10000000, n_records),
        })
        
        # 測試寫入效能
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            temp_file = f.name
        
        start_time = time.time()
        data.to_csv(temp_file, index=False)
        write_time = time.time() - start_time
        
        # 測試讀取效能
        start_time = time.time()
        loaded_data = pd.read_csv(temp_file)
        read_time = time.time() - start_time
        
        # 清理
        os.unlink(temp_file)
        
        # 驗證結果
        assert len(loaded_data) == n_records
        
        # 驗證效能
        assert write_time < 1.0, f"寫入耗時 {write_time:.2f} 秒"
        assert read_time < 1.0, f"讀取耗時 {read_time:.2f} 秒"
