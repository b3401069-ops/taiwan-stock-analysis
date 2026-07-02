"""
台灣股票分析工具 - 技術分析模組
"""

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from loguru import logger

from data.data_fetcher import DataFetcher

# 導入數據處理模組
from data.stock_data import StockData


class TechnicalAnalysis:
    """技術分析類"""

    def __init__(self):
        self.stock_data = StockData()
        self.data_fetcher = DataFetcher()

    async def analyze(
        self, stock_id: str, indicators: Optional[List[str]] = None
    ) -> Dict:
        """執行技術分析"""
        try:
            # 獲取價格數據
            price_data = await self.data_fetcher.get_stock_price(stock_id, "1y")

            # 轉換為DataFrame
            df = pd.DataFrame(price_data["data"])
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)

            # 默認分析所有指標
            if indicators is None:
                indicators = ["sma", "ema", "rsi", "macd", "kd", "bollinger", "volume"]

            analysis_result = {
                "stock_id": stock_id,
                "timestamp": pd.Timestamp.now().isoformat(),
                "indicators": {},
                "signals": {},
                "summary": {},
            }

            # 計算各個技術指標
            for indicator in indicators:
                if indicator == "sma":
                    analysis_result["indicators"]["sma"] = self._calculate_sma(df)
                elif indicator == "ema":
                    analysis_result["indicators"]["ema"] = self._calculate_ema(df)
                elif indicator == "rsi":
                    analysis_result["indicators"]["rsi"] = self._calculate_rsi(df)
                elif indicator == "macd":
                    analysis_result["indicators"]["macd"] = self._calculate_macd(df)
                elif indicator == "kd":
                    analysis_result["indicators"]["kd"] = self._calculate_kd(df)
                elif indicator == "bollinger":
                    analysis_result["indicators"]["bollinger"] = (
                        self._calculate_bollinger(df)
                    )
                elif indicator == "volume":
                    analysis_result["indicators"]["volume"] = self._calculate_volume(df)

            # 生成交易信號
            analysis_result["signals"] = self._generate_signals(
                df, analysis_result["indicators"]
            )

            # 生成分析摘要
            analysis_result["summary"] = self._generate_summary(
                analysis_result["indicators"], analysis_result["signals"]
            )

            return analysis_result

        except Exception as e:
            logger.error(f"技術分析失敗: {e}")
            raise

    def _calculate_sma(self, df: pd.DataFrame) -> Dict:
        """計算簡單移動平均線"""
        try:
            periods = [5, 10, 20, 50, 100, 200]
            sma_data = {}

            for period in periods:
                sma = df["close"].rolling(window=period).mean()
                sma_data[f"sma_{period}"] = {
                    "values": sma.tolist(),
                    "latest": float(sma.iloc[-1]) if not sma.empty else None,
                    "trend": (
                        "up"
                        if sma.iloc[-1] > sma.iloc[-2]
                        else "down" if sma.iloc[-1] < sma.iloc[-2] else "neutral"
                    ),
                }

            # 計算黃金交叉和死亡交叉
            if len(df) >= 200:
                sma_50 = df["close"].rolling(window=50).mean()
                sma_200 = df["close"].rolling(window=200).mean()

                # 檢查最近的交叉
                recent_cross = None
                for i in range(-10, 0):
                    if (
                        sma_50.iloc[i] > sma_200.iloc[i]
                        and sma_50.iloc[i - 1] <= sma_200.iloc[i - 1]
                    ):
                        recent_cross = {
                            "type": "golden_cross",
                            "date": df.index[i].strftime("%Y-%m-%d"),
                        }
                        break
                    elif (
                        sma_50.iloc[i] < sma_200.iloc[i]
                        and sma_50.iloc[i - 1] >= sma_200.iloc[i - 1]
                    ):
                        recent_cross = {
                            "type": "death_cross",
                            "date": df.index[i].strftime("%Y-%m-%d"),
                        }
                        break

                sma_data["cross_analysis"] = {
                    "sma_50": float(sma_50.iloc[-1]),
                    "sma_200": float(sma_200.iloc[-1]),
                    "recent_cross": recent_cross,
                }

            return sma_data

        except Exception as e:
            logger.error(f"計算SMA失敗: {e}")
            raise

    def _calculate_ema(self, df: pd.DataFrame) -> Dict:
        """計算指數移動平均線"""
        try:
            periods = [5, 10, 20, 50, 100, 200]
            ema_data = {}

            for period in periods:
                ema = df["close"].ewm(span=period, adjust=False).mean()
                ema_data[f"ema_{period}"] = {
                    "values": ema.tolist(),
                    "latest": float(ema.iloc[-1]) if not ema.empty else None,
                    "trend": (
                        "up"
                        if ema.iloc[-1] > ema.iloc[-2]
                        else "down" if ema.iloc[-1] < ema.iloc[-2] else "neutral"
                    ),
                }

            return ema_data

        except Exception as e:
            logger.error(f"計算EMA失敗: {e}")
            raise

    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> Dict:
        """計算RSI指標"""
        try:
            rsi = self.stock_data.calculate_rsi(df, period)

            # 計算RSI的統計數據
            rsi_values = rsi.dropna()

            rsi_data = {
                "values": rsi.tolist(),
                "latest": float(rsi.iloc[-1]) if not rsi.empty else None,
                "period": period,
                "overbought": 70,
                "oversold": 30,
                "statistics": {
                    "mean": float(rsi_values.mean()),
                    "std": float(rsi_values.std()),
                    "min": float(rsi_values.min()),
                    "max": float(rsi_values.max()),
                    "current_zone": (
                        "overbought"
                        if rsi.iloc[-1] > 70
                        else "oversold" if rsi.iloc[-1] < 30 else "neutral"
                    ),
                },
            }

            return rsi_data

        except Exception as e:
            logger.error(f"計算RSI失敗: {e}")
            raise

    def _calculate_macd(self, df: pd.DataFrame) -> Dict:
        """計算MACD指標"""
        try:
            macd_data = self.stock_data.calculate_macd(df)

            # 獲取最新值
            latest_macd = float(macd_data["macd_line"].iloc[-1])
            latest_signal = float(macd_data["signal_line"].iloc[-1])
            latest_histogram = float(macd_data["histogram"].iloc[-1])

            # 判斷信號
            signal = "neutral"
            if (
                latest_macd > latest_signal
                and macd_data["macd_line"].iloc[-2] <= macd_data["signal_line"].iloc[-2]
            ):
                signal = "bullish"
            elif (
                latest_macd < latest_signal
                and macd_data["macd_line"].iloc[-2] >= macd_data["signal_line"].iloc[-2]
            ):
                signal = "bearish"

            return {
                "macd_line": macd_data["macd_line"].tolist(),
                "signal_line": macd_data["signal_line"].tolist(),
                "histogram": macd_data["histogram"].tolist(),
                "latest": {
                    "macd": latest_macd,
                    "signal": latest_signal,
                    "histogram": latest_histogram,
                },
                "signal": signal,
            }

        except Exception as e:
            logger.error(f"計算MACD失敗: {e}")
            raise

    def _calculate_kd(self, df: pd.DataFrame) -> Dict:
        """計算KD指標"""
        try:
            kd_data = self.stock_data.calculate_kd(df)

            # 獲取最新值
            latest_k = float(kd_data["k_values"].iloc[-1])
            latest_d = float(kd_data["d_values"].iloc[-1])
            latest_j = float(kd_data["j_values"].iloc[-1])

            # 判斷信號
            signal = "neutral"
            if (
                latest_k > latest_d
                and kd_data["k_values"].iloc[-2] <= kd_data["d_values"].iloc[-2]
            ):
                signal = "bullish"
            elif (
                latest_k < latest_d
                and kd_data["k_values"].iloc[-2] >= kd_data["d_values"].iloc[-2]
            ):
                signal = "bearish"

            # 判斷超買超賣
            zone = "neutral"
            if latest_k > 80 and latest_d > 80:
                zone = "overbought"
            elif latest_k < 20 and latest_d < 20:
                zone = "oversold"

            return {
                "k_values": kd_data["k_values"].tolist(),
                "d_values": kd_data["d_values"].tolist(),
                "j_values": kd_data["j_values"].tolist(),
                "latest": {"k": latest_k, "d": latest_d, "j": latest_j},
                "signal": signal,
                "zone": zone,
            }

        except Exception as e:
            logger.error(f"計算KD失敗: {e}")
            raise

    def _calculate_bollinger(self, df: pd.DataFrame) -> Dict:
        """計算布林通道"""
        try:
            bb_data = self.stock_data.calculate_bollinger_bands(df)

            # 獲取最新值
            latest_price = float(df["close"].iloc[-1])
            latest_upper = float(bb_data["upper_band"].iloc[-1])
            latest_middle = float(bb_data["middle_band"].iloc[-1])
            latest_lower = float(bb_data["lower_band"].iloc[-1])
            latest_bandwidth = float(bb_data["bandwidth"].iloc[-1])
            latest_percent_b = float(bb_data["percent_b"].iloc[-1])

            # 判斷價格位置
            position = "middle"
            if latest_price > latest_upper:
                position = "above_upper"
            elif latest_price < latest_lower:
                position = "below_lower"
            elif latest_price > latest_middle:
                position = "upper_half"
            else:
                position = "lower_half"

            # 判斷波動性
            volatility = "normal"
            if latest_bandwidth > 10:
                volatility = "high"
            elif latest_bandwidth < 5:
                volatility = "low"

            return {
                "upper_band": bb_data["upper_band"].tolist(),
                "middle_band": bb_data["middle_band"].tolist(),
                "lower_band": bb_data["lower_band"].tolist(),
                "bandwidth": bb_data["bandwidth"].tolist(),
                "percent_b": bb_data["percent_b"].tolist(),
                "latest": {
                    "price": latest_price,
                    "upper": latest_upper,
                    "middle": latest_middle,
                    "lower": latest_lower,
                    "bandwidth": latest_bandwidth,
                    "percent_b": latest_percent_b,
                },
                "position": position,
                "volatility": volatility,
            }

        except Exception as e:
            logger.error(f"計算布林通道失敗: {e}")
            raise

    def _calculate_volume(self, df: pd.DataFrame) -> Dict:
        """計算成交量指標"""
        try:
            volume_data = self.stock_data.calculate_volume_indicators(df)

            # 獲取最新值
            latest_volume = float(df["volume"].iloc[-1])
            latest_volume_ma = float(volume_data["volume_ma"].iloc[-1])
            latest_volume_ratio = float(volume_data["volume_ratio"].iloc[-1])
            latest_obv = float(volume_data["obv"].iloc[-1])

            # 判斷成交量趨勢
            volume_trend = "neutral"
            if latest_volume_ratio > 1.5:
                volume_trend = "high"
            elif latest_volume_ratio < 0.5:
                volume_trend = "low"

            return {
                "volume_ma": volume_data["volume_ma"].tolist(),
                "volume_ratio": volume_data["volume_ratio"].tolist(),
                "obv": volume_data["obv"].tolist(),
                "latest": {
                    "volume": latest_volume,
                    "volume_ma": latest_volume_ma,
                    "volume_ratio": latest_volume_ratio,
                    "obv": latest_obv,
                },
                "trend": volume_trend,
            }

        except Exception as e:
            logger.error(f"計算成交量指標失敗: {e}")
            raise

    def _generate_signals(self, df: pd.DataFrame, indicators: Dict) -> Dict:
        """生成交易信號"""
        try:
            signals = {
                "buy_signals": [],
                "sell_signals": [],
                "neutral_signals": [],
                "overall_signal": "neutral",
                "confidence": 0.5,
            }

            buy_count = 0
            sell_count = 0
            neutral_count = 0

            # 分析RSI信號
            if "rsi" in indicators:
                rsi = indicators["rsi"]
                if rsi["latest"] < 30:
                    signals["buy_signals"].append(
                        {
                            "indicator": "RSI",
                            "reason": "RSI超賣",
                            "value": rsi["latest"],
                        }
                    )
                    buy_count += 1
                elif rsi["latest"] > 70:
                    signals["sell_signals"].append(
                        {
                            "indicator": "RSI",
                            "reason": "RSI超買",
                            "value": rsi["latest"],
                        }
                    )
                    sell_count += 1
                else:
                    signals["neutral_signals"].append(
                        {
                            "indicator": "RSI",
                            "reason": "RSI中性",
                            "value": rsi["latest"],
                        }
                    )
                    neutral_count += 1

            # 分析MACD信號
            if "macd" in indicators:
                macd = indicators["macd"]
                if macd["signal"] == "bullish":
                    signals["buy_signals"].append(
                        {
                            "indicator": "MACD",
                            "reason": "MACD金叉",
                            "value": macd["latest"]["macd"],
                        }
                    )
                    buy_count += 1
                elif macd["signal"] == "bearish":
                    signals["sell_signals"].append(
                        {
                            "indicator": "MACD",
                            "reason": "MACD死叉",
                            "value": macd["latest"]["macd"],
                        }
                    )
                    sell_count += 1
                else:
                    signals["neutral_signals"].append(
                        {
                            "indicator": "MACD",
                            "reason": "MACD中性",
                            "value": macd["latest"]["macd"],
                        }
                    )
                    neutral_count += 1

            # 分析KD信號
            if "kd" in indicators:
                kd = indicators["kd"]
                if kd["signal"] == "bullish":
                    signals["buy_signals"].append(
                        {
                            "indicator": "KD",
                            "reason": "KD金叉",
                            "value": kd["latest"]["k"],
                        }
                    )
                    buy_count += 1
                elif kd["signal"] == "bearish":
                    signals["sell_signals"].append(
                        {
                            "indicator": "KD",
                            "reason": "KD死叉",
                            "value": kd["latest"]["k"],
                        }
                    )
                    sell_count += 1
                else:
                    signals["neutral_signals"].append(
                        {
                            "indicator": "KD",
                            "reason": "KD中性",
                            "value": kd["latest"]["k"],
                        }
                    )
                    neutral_count += 1

            # 分析布林通道信號
            if "bollinger" in indicators:
                bb = indicators["bollinger"]
                if bb["position"] == "below_lower":
                    signals["buy_signals"].append(
                        {
                            "indicator": "Bollinger",
                            "reason": "價格跌破下軌",
                            "value": bb["latest"]["price"],
                        }
                    )
                    buy_count += 1
                elif bb["position"] == "above_upper":
                    signals["sell_signals"].append(
                        {
                            "indicator": "Bollinger",
                            "reason": "價格突破上軌",
                            "value": bb["latest"]["price"],
                        }
                    )
                    sell_count += 1
                else:
                    signals["neutral_signals"].append(
                        {
                            "indicator": "Bollinger",
                            "reason": "價格在通道內",
                            "value": bb["latest"]["price"],
                        }
                    )
                    neutral_count += 1

            # 計算總體信號
            total_signals = buy_count + sell_count + neutral_count
            if total_signals > 0:
                buy_ratio = buy_count / total_signals
                sell_ratio = sell_count / total_signals

                if buy_ratio > 0.6:
                    signals["overall_signal"] = "buy"
                    signals["confidence"] = buy_ratio
                elif sell_ratio > 0.6:
                    signals["overall_signal"] = "sell"
                    signals["confidence"] = sell_ratio
                else:
                    signals["overall_signal"] = "neutral"
                    signals["confidence"] = max(buy_ratio, sell_ratio)

            return signals

        except Exception as e:
            logger.error(f"生成交易信號失敗: {e}")
            raise

    def _generate_summary(self, indicators: Dict, signals: Dict) -> Dict:
        """生成分析摘要"""
        try:
            summary = {
                "trend": "neutral",
                "strength": "moderate",
                "key_levels": {},
                "recommendation": "hold",
                "risk_level": "medium",
            }

            # 分析趨勢
            if "sma" in indicators:
                sma = indicators["sma"]
                if "cross_analysis" in sma:
                    cross = sma["cross_analysis"]
                    if cross["recent_cross"]:
                        if cross["recent_cross"]["type"] == "golden_cross":
                            summary["trend"] = "bullish"
                            summary["strength"] = "strong"
                        elif cross["recent_cross"]["type"] == "death_cross":
                            summary["trend"] = "bearish"
                            summary["strength"] = "strong"

            # 分析信號強度
            if signals["overall_signal"] == "buy":
                summary["recommendation"] = "buy"
                summary["risk_level"] = (
                    "low" if signals["confidence"] > 0.8 else "medium"
                )
            elif signals["overall_signal"] == "sell":
                summary["recommendation"] = "sell"
                summary["risk_level"] = (
                    "high" if signals["confidence"] > 0.8 else "medium"
                )

            # 設定關鍵價位
            if "bollinger" in indicators:
                bb = indicators["bollinger"]
                summary["key_levels"] = {
                    "resistance": bb["latest"]["upper"],
                    "support": bb["latest"]["lower"],
                    "pivot": bb["latest"]["middle"],
                }

            return summary

        except Exception as e:
            logger.error(f"生成分析摘要失敗: {e}")
            raise
