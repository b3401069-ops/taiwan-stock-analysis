"""
台灣股票分析工具 - 股票數據處理模組
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from loguru import logger


class StockData:
    """股票數據處理類"""

    def __init__(self):
        self.data_cache = {}

    def calculate_returns(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """計算收益率"""
        try:
            # 計算日收益率
            price_data["daily_return"] = price_data["close"].pct_change()

            # 計算累積收益率
            price_data["cumulative_return"] = (
                1 + price_data["daily_return"]
            ).cumprod() - 1

            # 訡算對數收益率
            price_data["log_return"] = np.log(
                price_data["close"] / price_data["close"].shift(1)
            )

            return price_data

        except Exception as e:
            logger.error(f"計算收益率失敗: {e}")
            raise

    def calculate_volatility(self, price_data: pd.DataFrame, window: int = 20) -> float:
        """計算波動率"""
        try:
            # 訡算日收益率
            returns = price_data["close"].pct_change().dropna()

            # 訡算滾動波動率
            volatility = returns.rolling(window=window).std()

            # 年化波動率
            annualized_volatility = volatility.iloc[-1] * np.sqrt(252)

            return float(annualized_volatility)

        except Exception as e:
            logger.error(f"計算波動率失敗: {e}")
            raise

    def calculate_beta(
        self, stock_returns: pd.DataFrame, market_returns: pd.DataFrame
    ) -> float:
        """計算Beta係數"""
        try:
            # 計算協方差
            covariance = np.cov(stock_returns, market_returns)[0][1]

            # 計算市場方差
            market_variance = np.var(market_returns)

            # 計算Beta
            beta = covariance / market_variance

            return float(beta)

        except Exception as e:
            logger.error(f"計算Beta係數失敗: {e}")
            raise

    def calculate_sharpe_ratio(
        self, returns: pd.Series, risk_free_rate: float = 0.02
    ) -> float:
        """計算夏普比率"""
        try:
            # 計算平均收益率
            mean_return = returns.mean() * 252  # 年化

            # 計算標準差
            std_return = returns.std() * np.sqrt(252)  # 年化

            # 計算夏普比率
            sharpe_ratio = (mean_return - risk_free_rate) / std_return

            return float(sharpe_ratio)

        except Exception as e:
            logger.error(f"計算夏普比率失敗: {e}")
            raise

    def calculate_max_drawdown(self, price_data: pd.DataFrame) -> Dict:
        """計算最大回撤"""
        try:
            # 計算累積最高點
            price_data["peak"] = price_data["close"].expanding(min_periods=1).max()

            # 計算回撤
            price_data["drawdown"] = (
                price_data["close"] - price_data["peak"]
            ) / price_data["peak"]

            # 找出最大回撤
            max_drawdown = price_data["drawdown"].min()
            max_drawdown_date = price_data["drawdown"].idxmin()

            # 找出回撤開始和結束日期
            peak_date = price_data.loc[:max_drawdown_date, "close"].idxmax()

            return {
                "max_drawdown": float(max_drawdown),
                "max_drawdown_date": max_drawdown_date.strftime("%Y-%m-%d"),
                "peak_date": peak_date.strftime("%Y-%m-%d"),
                "drawdown_duration": (max_drawdown_date - peak_date).days,
            }

        except Exception as e:
            logger.error(f"計算最大回撤失敗: {e}")
            raise

    def calculate_rsi(self, price_data: pd.DataFrame, period: int = 14) -> pd.Series:
        """計算RSI指標"""
        try:
            # 計算價格變化
            delta = price_data["close"].diff()

            # 分離上漲和下跌
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

            # 計算RS
            rs = gain / loss

            # 計算RSI
            rsi = 100 - (100 / (1 + rs))

            return rsi

        except Exception as e:
            logger.error(f"計算RSI指標失敗: {e}")
            raise

    def calculate_macd(
        self,
        price_data: pd.DataFrame,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> Dict:
        """計算MACD指標"""
        try:
            # 計算快速EMA
            fast_ema = price_data["close"].ewm(span=fast_period, adjust=False).mean()

            # 計算慢速EMA
            slow_ema = price_data["close"].ewm(span=slow_period, adjust=False).mean()

            # 計算MACD線
            macd_line = fast_ema - slow_ema

            # 計算信號線
            signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()

            # 計算柱狀圖
            histogram = macd_line - signal_line

            return {
                "macd_line": macd_line,
                "signal_line": signal_line,
                "histogram": histogram,
            }

        except Exception as e:
            logger.error(f"計算MACD指標失敗: {e}")
            raise

    def calculate_kd(
        self, price_data: pd.DataFrame, k_period: int = 9, d_period: int = 3
    ) -> Dict:
        """計算KD指標"""
        try:
            # 計算最近N天的最高價和最低價
            low_min = price_data["low"].rolling(window=k_period).min()
            high_max = price_data["high"].rolling(window=k_period).max()

            # 計算RSV
            # 注意：台股常見漲停/跌停整段打平（high == low），此時 high_max - low_min == 0
            # 會產生除零 → NaN/Inf，並經下方遞迴公式往後污染整條 K/D。
            # 因此先把分母為 0 的情況轉為 NaN，再以「前值遞補、開頭補中性值 50」處理。
            price_range = (high_max - low_min).replace(0, np.nan)
            rsv = (price_data["close"] - low_min) / price_range * 100
            rsv = rsv.replace([np.inf, -np.inf], np.nan).ffill().fillna(50)

            # 計算K值
            k_values = pd.Series(index=price_data.index, dtype=float)
            k_values.iloc[0] = 50  # 初始值

            for i in range(1, len(k_values)):
                k_values.iloc[i] = (2 / 3) * k_values.iloc[i - 1] + (1 / 3) * rsv.iloc[
                    i
                ]

            # 計算D值
            d_values = pd.Series(index=price_data.index, dtype=float)
            d_values.iloc[0] = 50  # 初始值

            for i in range(1, len(d_values)):
                d_values.iloc[i] = (2 / 3) * d_values.iloc[i - 1] + (
                    1 / 3
                ) * k_values.iloc[i]

            # 計算J值
            j_values = 3 * k_values - 2 * d_values

            return {"k_values": k_values, "d_values": d_values, "j_values": j_values}

        except Exception as e:
            logger.error(f"計算KD指標失敗: {e}")
            raise

    def calculate_bollinger_bands(
        self, price_data: pd.DataFrame, period: int = 20, std_dev: int = 2
    ) -> Dict:
        """計算布林通道"""
        try:
            # 計算中軌線（移動平均線）
            middle_band = price_data["close"].rolling(window=period).mean()

            # 計算標準差
            std = price_data["close"].rolling(window=period).std()

            # 計算上軌線和下軌線
            upper_band = middle_band + (std * std_dev)
            lower_band = middle_band - (std * std_dev)

            # 訡算布林帶寬度
            bandwidth = (upper_band - lower_band) / middle_band * 100

            # 計算%B指標
            percent_b = (price_data["close"] - lower_band) / (upper_band - lower_band)

            return {
                "upper_band": upper_band,
                "middle_band": middle_band,
                "lower_band": lower_band,
                "bandwidth": bandwidth,
                "percent_b": percent_b,
            }

        except Exception as e:
            logger.error(f"計算布林通道失敗: {e}")
            raise

    def calculate_moving_averages(
        self, price_data: pd.DataFrame, periods: List[int] = [5, 10, 20, 50, 100, 200]
    ) -> Dict:
        """計算移動平均線"""
        try:
            moving_averages = {}

            for period in periods:
                ma = price_data["close"].rolling(window=period).mean()
                moving_averages[f"MA{period}"] = ma

            return moving_averages

        except Exception as e:
            logger.error(f"計算移動平均線失敗: {e}")
            raise

    def calculate_volume_indicators(self, price_data: pd.DataFrame) -> Dict:
        """計算成交量指標"""
        try:
            # 計算成交量移動平均線
            volume_ma = price_data["volume"].rolling(window=20).mean()

            # 訡算成交量比率
            volume_ratio = price_data["volume"] / volume_ma

            # 訡算OBV（能量潮指標）
            obv = pd.Series(index=price_data.index, dtype=float)
            obv.iloc[0] = 0

            for i in range(1, len(obv)):
                if price_data["close"].iloc[i] > price_data["close"].iloc[i - 1]:
                    obv.iloc[i] = obv.iloc[i - 1] + price_data["volume"].iloc[i]
                elif price_data["close"].iloc[i] < price_data["close"].iloc[i - 1]:
                    obv.iloc[i] = obv.iloc[i - 1] - price_data["volume"].iloc[i]
                else:
                    obv.iloc[i] = obv.iloc[i - 1]

            return {"volume_ma": volume_ma, "volume_ratio": volume_ratio, "obv": obv}

        except Exception as e:
            logger.error(f"計算成交量指標失敗: {e}")
            raise

    def prepare_ml_features(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """準備機器學習特徵"""
        try:
            # 複製數據
            df = price_data.copy()

            # 添加技術指標特徵
            df["returns"] = df["close"].pct_change()
            df["volatility"] = df["returns"].rolling(window=20).std()

            # 添加移動平均線
            for period in [5, 10, 20, 50]:
                df[f"ma_{period}"] = df["close"].rolling(window=period).mean()
                df[f"ma_ratio_{period}"] = df["close"] / df[f"ma_{period}"]

            # 添加RSI
            df["rsi"] = self.calculate_rsi(df)

            # 添加MACD
            macd_data = self.calculate_macd(df)
            df["macd"] = macd_data["macd_line"]
            df["macd_signal"] = macd_data["signal_line"]
            df["macd_histogram"] = macd_data["histogram"]

            # 添加KD
            kd_data = self.calculate_kd(df)
            df["kd_k"] = kd_data["k_values"]
            df["kd_d"] = kd_data["d_values"]
            df["kd_j"] = kd_data["j_values"]

            # 添加布林通道
            bb_data = self.calculate_bollinger_bands(df)
            df["bb_upper"] = bb_data["upper_band"]
            df["bb_middle"] = bb_data["middle_band"]
            df["bb_lower"] = bb_data["lower_band"]
            df["bb_width"] = bb_data["bandwidth"]
            df["bb_percent"] = bb_data["percent_b"]

            # 添加成交量特徵
            volume_data = self.calculate_volume_indicators(df)
            df["volume_ma"] = volume_data["volume_ma"]
            df["volume_ratio"] = volume_data["volume_ratio"]
            df["obv"] = volume_data["obv"]

            # 添加時間特徵
            df["day_of_week"] = df.index.dayofweek
            df["month"] = df.index.month
            df["quarter"] = df.index.quarter

            # 添加目標變量（未來N天收益率）
            for days in [1, 5, 10, 20]:
                df[f"future_return_{days}d"] = (
                    df["close"].shift(-days) / df["close"] - 1
                )

            # 删除包含NaN的行
            df = df.dropna()

            return df

        except Exception as e:
            logger.error(f"準備機器學習特徵失敗: {e}")
            raise

    def calculate_atr(self, price_data: pd.DataFrame, period: int = 14) -> pd.Series:
        """計算 ATR（平均真實範圍）"""
        try:
            high = price_data["high"]
            low = price_data["low"]
            close = price_data["close"]

            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

            atr = tr.rolling(window=period).mean()
            return atr

        except Exception as e:
            logger.error(f"計算 ATR 失敗: {e}")
            raise

    def calculate_vwap(self, price_data: pd.DataFrame) -> pd.Series:
        """計算 VWAP（成交量加權平均價）"""
        try:
            typical_price = (
                price_data["high"] + price_data["low"] + price_data["close"]
            ) / 3
            cumulative_tp_vol = (typical_price * price_data["volume"]).cumsum()
            cumulative_vol = price_data["volume"].cumsum()
            vwap = cumulative_tp_vol / cumulative_vol
            return vwap

        except Exception as e:
            logger.error(f"計算 VWAP 失敗: {e}")
            raise

    def split_train_test(self, data: pd.DataFrame, test_size: float = 0.2) -> Dict:
        """分割訓練和測試數據"""
        try:
            # 按時間順序分割
            split_idx = int(len(data) * (1 - test_size))

            train_data = data.iloc[:split_idx]
            test_data = data.iloc[split_idx:]

            return {
                "train": train_data,
                "test": test_data,
                "train_size": len(train_data),
                "test_size": len(test_data),
            }

        except Exception as e:
            logger.error(f"分割訓練和測試數據失敗: {e}")
            raise
