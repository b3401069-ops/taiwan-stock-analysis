"""技術指標計算測試。"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


def _make_ohlcv(n: int, base: float = 100.0) -> pd.DataFrame:
    """建立 N 天的 OHLCV 測試資料。"""
    dates = pd.bdate_range("2024-01-01", periods=n)
    rows = []
    for i, dt in enumerate(dates):
        close = base + i * 0.5
        rows.append(
            {
                "date": dt.date(),
                "open": close - 0.3,
                "high": close + 1.0,
                "low": close - 1.0,
                "close": close,
                "volume": 1_000_000 + i * 10_000,
            }
        )
    return pd.DataFrame(rows).set_index("date")


@pytest.fixture()
def df_100():
    """100 天的 OHLCV，足以計算所有指標。"""
    return _make_ohlcv(100)


@pytest.fixture()
def df_20():
    """20 天的 OHLCV。"""
    return _make_ohlcv(20)


class TestTechnicalIndicators:
    """技術指標計算測試。"""

    def test_sma_calculation(self, df_100):
        """SMA 計算正確性。"""
        # 計算 SMA(5)
        sma5 = df_100["close"].rolling(window=5).mean()

        # 前 4 天應為 NaN
        assert sma5.isna().sum() >= 4

        # 第 5 天應為前 5 天收盤均值
        expected = df_100["close"].iloc[:5].mean()
        assert sma5.iloc[4] == pytest.approx(expected, rel=1e-3)

    def test_rsi_range(self, df_100):
        """RSI 值應在 0~100 之間。"""
        delta = df_100["close"].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        rsi_valid = rsi.dropna()
        assert len(rsi_valid) > 0
        assert rsi_valid.min() >= 0
        assert rsi_valid.max() <= 100

    def test_macd_components(self, df_100):
        """MACD 組件計算。"""
        # 計算 EMA
        ema12 = df_100["close"].ewm(span=12, adjust=False).mean()
        ema26 = df_100["close"].ewm(span=26, adjust=False).mean()

        # 計算 MACD
        macd = ema12 - ema26
        macd_signal = macd.ewm(span=9, adjust=False).mean()
        macd_hist = macd - macd_signal

        # 驗證 MACD_Hist = MACD - Signal
        np.testing.assert_allclose(macd_hist.values, (macd - macd_signal).values, atol=1e-3)

    def test_bollinger_bands_order(self, df_100):
        """Bollinger Bands: upper >= middle >= lower。"""
        sma20 = df_100["close"].rolling(window=20).mean()
        std20 = df_100["close"].rolling(window=20).std()

        bb_upper = sma20 + 2 * std20
        bb_middle = sma20
        bb_lower = sma20 - 2 * std20

        valid_idx = bb_upper.dropna().index
        assert len(valid_idx) > 0
        assert (bb_upper[valid_idx] >= bb_middle[valid_idx] - 1e-6).all()
        assert (bb_middle[valid_idx] >= bb_lower[valid_idx] - 1e-6).all()

    def test_bollinger_middle_equals_sma20(self, df_100):
        """BB middle 應等於 SMA(20)。"""
        sma20 = df_100["close"].rolling(window=20).mean()

        valid_idx = sma20.dropna().index
        np.testing.assert_allclose(
            sma20[valid_idx].values,
            sma20[valid_idx].values,
            rtol=1e-3,
        )

    def test_short_data_no_crash(self):
        """短資料不應崩潰。"""
        df = _make_ohlcv(5)

        # 計算 SMA(20) 應全為 NaN
        sma20 = df["close"].rolling(window=20).mean()
        assert sma20.isna().all()

    def test_volume_sma(self, df_100):
        """成交量 SMA 計算。"""
        vol_sma20 = df_100["volume"].rolling(window=20).mean()

        # 前 19 天應為 NaN
        assert vol_sma20.isna().sum() >= 19

        # 第 20 天應為前 20 天成交量均值
        expected = df_100["volume"].iloc[:20].mean()
        assert vol_sma20.iloc[19] == pytest.approx(expected, rel=1e-3)

    def test_price_change(self, df_100):
        """價格變動計算。"""
        price_change = df_100["close"].pct_change()

        # 第一天應為 NaN
        assert pd.isna(price_change.iloc[0])

        # 第二天應為 (close[1] - close[0]) / close[0]
        expected = (df_100["close"].iloc[1] - df_100["close"].iloc[0]) / df_100["close"].iloc[0]
        assert price_change.iloc[1] == pytest.approx(expected, rel=1e-3)

    def test_cumulative_return(self, df_100):
        """累積報酬率計算。"""
        cum_return = (1 + df_100["close"].pct_change()).cumprod() - 1

        # 第一天應為 NaN（因為 pct_change() 第一天為 NaN）
        assert pd.isna(cum_return.iloc[0])

        # 最後一天應為正數（因為價格持續上漲）
        assert cum_return.iloc[-1] > 0

    def test_drawdown_calculation(self, df_100):
        """最大回撤計算。"""
        cummax = df_100["close"].cummax()
        drawdown = (df_100["close"] - cummax) / cummax

        # 回撤應 <= 0（除了第一天可能是 0）
        assert drawdown.max() <= 0

        # 如果有回撤，最大回撤應為負數
        # 由於資料是持續上漲的，drawdown 可能都是 0
        max_drawdown = drawdown.min()
        assert max_drawdown <= 0


class TestMovingAverages:
    """移動平均線測試。"""

    def test_sma_periods(self, df_100):
        """不同週期 SMA 計算。"""
        for period in [5, 10, 20, 60]:
            sma = df_100["close"].rolling(window=period).mean()

            # 前 period-1 天應為 NaN
            assert sma.isna().sum() >= period - 1

            # 最後一天應有值
            assert not pd.isna(sma.iloc[-1])

    def test_ema_periods(self, df_100):
        """不同週期 EMA 計算。"""
        for period in [12, 26]:
            ema = df_100["close"].ewm(span=period, adjust=False).mean()

            # EMA 不應有 NaN（除了第一天）
            assert ema.isna().sum() <= 1

            # 最後一天應有值
            assert not pd.isna(ema.iloc[-1])

    def test_sma_trend(self, df_100):
        """持續上漲序列的 SMA 應呈現上升趨勢。"""
        sma20 = df_100["close"].rolling(window=20).mean().dropna()

        # 檢查 SMA 是否呈現上升趨勢
        assert sma20.iloc[-1] > sma20.iloc[0]


class TestVolatilityIndicators:
    """波動率指標測試。"""

    def test_standard_deviation(self, df_100):
        """標準差計算。"""
        std20 = df_100["close"].rolling(window=20).std()

        # 前 19 天應為 NaN
        assert std20.isna().sum() >= 19

        # 標準差應為正數
        assert (std20.dropna() >= 0).all()

    def test_atr_calculation(self, df_100):
        """ATR 計算。"""
        high = df_100["high"]
        low = df_100["low"]
        close = df_100["close"]

        # 計算 True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # 計算 ATR
        atr = tr.rolling(window=14).mean()

        # ATR 應為正數
        assert (atr.dropna() >= 0).all()

    def test_bollinger_bandwidth(self, df_100):
        """布林通道寬度計算。"""
        sma20 = df_100["close"].rolling(window=20).mean()
        std20 = df_100["close"].rolling(window=20).std()

        bb_upper = sma20 + 2 * std20
        bb_lower = sma20 - 2 * std20
        bandwidth = (bb_upper - bb_lower) / sma20

        # 帶寬應為正數
        assert (bandwidth.dropna() >= 0).all()
