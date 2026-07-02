"""
技術分析模組測試
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


class TestTechnicalIndicators:
    """技術指標測試"""

    def setup_method(self):
        """測試前準備"""
        self.df = create_sample_stock_data(100)

    def test_rsi_calculation(self):
        """測試 RSI 計算"""
        from data.stock_data import StockData

        stock_data = StockData()

        rsi = stock_data.calculate_rsi(self.df)

        # RSI 應該在 0-100 之間
        assert all(0 <= r <= 100 for r in rsi.dropna())
        # RSI 長度應該與原始數據相同
        assert len(rsi) == len(self.df)

    def test_macd_calculation(self):
        """測試 MACD 計算"""
        from data.stock_data import StockData

        stock_data = StockData()

        macd = stock_data.calculate_macd(self.df)

        assert "macd_line" in macd
        assert "signal_line" in macd
        assert "histogram" in macd
        assert len(macd["macd_line"]) == len(self.df)

    def test_bollinger_bands(self):
        """測試布林通道計算"""
        from data.stock_data import StockData

        stock_data = StockData()

        bb = stock_data.calculate_bollinger_bands(self.df)

        assert "upper_band" in bb
        assert "middle_band" in bb
        assert "lower_band" in bb

        # 上軌應該大於中軌，中軌應該大於下軌
        # 注意：calculate_bollinger_bands 回傳 dict（值為 Series），需在 Series 上用 .loc
        valid_idx = bb["upper_band"].dropna().index
        assert all(bb["upper_band"].loc[valid_idx] >= bb["middle_band"].loc[valid_idx])
        assert all(bb["middle_band"].loc[valid_idx] >= bb["lower_band"].loc[valid_idx])

    def test_kd_calculation(self):
        """測試 KD 計算"""
        from data.stock_data import StockData

        stock_data = StockData()

        kd = stock_data.calculate_kd(self.df)

        assert "k_values" in kd
        assert "d_values" in kd
        assert "j_values" in kd

        # K 值應該在 0-100 之間
        valid_k = kd["k_values"].dropna()
        assert all(0 <= k <= 100 for k in valid_k)

    def test_atr_calculation(self):
        """測試 ATR 計算"""
        from data.stock_data import StockData

        stock_data = StockData()

        atr = stock_data.calculate_atr(self.df)

        # ATR 應該為正數
        assert all(a >= 0 for a in atr.dropna())

    def test_vwap_calculation(self):
        """測試 VWAP 計算"""
        from data.stock_data import StockData

        stock_data = StockData()

        vwap = stock_data.calculate_vwap(self.df)

        # VWAP 應該為正數
        assert all(v >= 0 for v in vwap.dropna())

    def test_volume_indicators(self):
        """測試成交量指標"""
        from data.stock_data import StockData

        stock_data = StockData()

        vol = stock_data.calculate_volume_indicators(self.df)

        assert "volume_ma" in vol
        assert "volume_ratio" in vol
        assert "obv" in vol


class TestMLFeatures:
    """ML 特徵準備測試"""

    def test_prepare_ml_features(self):
        """測試 ML 特徵準備"""
        from data.stock_data import StockData

        stock_data = StockData()

        df = create_sample_stock_data(200)
        features = stock_data.prepare_ml_features(df)

        # 應該包含所有特徵
        expected_cols = [
            "returns",
            "volatility",
            "ma_5",
            "ma_10",
            "ma_20",
            "ma_50",
            "rsi",
            "macd",
            "macd_signal",
            "macd_histogram",
            "kd_k",
            "kd_d",
            "kd_j",
            "bb_upper",
            "bb_middle",
            "bb_lower",
            "bb_width",
            "bb_percent",
            "volume_ma",
            "volume_ratio",
            "obv",
            "day_of_week",
            "month",
            "quarter",
            "future_return_1d",
            "future_return_5d",
            "future_return_10d",
            "future_return_20d",
        ]

        for col in expected_cols:
            assert col in features.columns, f"缺少特徵: {col}"

        # 不應該有 NaN
        assert not features.isnull().any().any()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
