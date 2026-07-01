"""
台灣股票分析工具 - 市場狀態偵測
判斷目前市場是牛市、熊市、盤整還是危機
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta
from loguru import logger
from enum import Enum
import yfinance as yf


class MarketRegime(Enum):
    """市場狀態枚舉"""
    BULL = "bull"           # 牛市
    BEAR = "bear"           # 熊市
    SIDEWAYS = "sideways"   # 盤整
    CRISIS = "crisis"       # 危機


class MarketRegimeDetector:
    """市場狀態偵測器"""

    def __init__(self):
        """初始化市場狀態偵測器"""
        self.regime_history = []
        
        # 參數設定
        self.params = {
            # 均線參數
            "sma_short": 20,
            "sma_long": 60,
            
            # RSI 參數
            "rsi_period": 14,
            "rsi_bull_threshold": 50,
            "rsi_bear_threshold": 50,
            
            # 波動率參數
            "volatility_period": 20,
            "volatility_crisis_threshold": 0.03,  # 3% 日波動率
            
            # 回撤參數
            "drawdown_threshold": -0.10,  # -10% 回撤
            
            # 市場寬度參數
            "breadth_threshold": 0.6,  # 60% 股票上漲
        }

    def detect_regime(self, stock_id: str = "^TWII", period: str = "1y") -> Dict:
        """
        偵測市場狀態
        
        Args:
            stock_id: 股票代碼（預設台灣加權指數）
            period: 資料期間
            
        Returns:
            市場狀態分析結果
        """
        try:
            # 取得歷史資料
            ticker = yf.Ticker(stock_id)
            df = ticker.history(period=period)
            
            if df.empty:
                return {"success": False, "error": "無法取得歷史資料"}
            
            # 計算技術指標
            df = self._calculate_indicators(df)
            
            # 偵測市場狀態
            regime = self._analyze_regime(df)
            
            # 計算信心水平
            confidence = self._calculate_confidence(df, regime)
            
            # 生成建議
            suggestion = self._generate_suggestion(regime, df)
            
            # 記錄歷史
            self.regime_history.append({
                "date": datetime.now().isoformat(),
                "regime": regime.value,
                "confidence": confidence
            })
            
            return {
                "success": True,
                "data": {
                    "regime": regime.value,
                    "regime_name": self._get_regime_name(regime),
                    "confidence": confidence,
                    "suggestion": suggestion,
                    "indicators": self._get_indicator_summary(df),
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"市場狀態偵測失敗: {e}")
            return {"success": False, "error": str(e)}

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """計算技術指標"""
        try:
            # 均線
            df["sma_short"] = df["Close"].rolling(window=self.params["sma_short"]).mean()
            df["sma_long"] = df["Close"].rolling(window=self.params["sma_long"]).mean()
            
            # RSI
            delta = df["Close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=self.params["rsi_period"]).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.params["rsi_period"]).mean()
            rs = gain / loss
            df["rsi"] = 100 - (100 / (1 + rs))
            
            # 波動率
            df["returns"] = df["Close"].pct_change()
            df["volatility"] = df["returns"].rolling(window=self.params["volatility_period"]).std()
            
            # 回撤
            df["cummax"] = df["Close"].cummax()
            df["drawdown"] = (df["Close"] - df["cummax"]) / df["cummax"]
            
            # 動量
            df["momentum_20"] = df["Close"].pct_change(periods=20)
            df["momentum_60"] = df["Close"].pct_change(periods=60)
            
            # MACD
            exp1 = df["Close"].ewm(span=12, adjust=False).mean()
            exp2 = df["Close"].ewm(span=26, adjust=False).mean()
            df["macd"] = exp1 - exp2
            df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
            df["macd_hist"] = df["macd"] - df["macd_signal"]
            
            return df
            
        except Exception as e:
            logger.error(f"計算指標失敗: {e}")
            return df

    def _analyze_regime(self, df: pd.DataFrame) -> MarketRegime:
        """分析市場狀態"""
        try:
            # 取得最新資料
            latest = df.iloc[-1]
            
            # 計算各項指標分數
            scores = {
                "trend": self._calculate_trend_score(df),
                "momentum": self._calculate_momentum_score(df),
                "volatility": self._calculate_volatility_score(df),
                "breadth": self._calculate_breadth_score(df)
            }
            
            # 加權總分
            weights = {
                "trend": 0.35,
                "momentum": 0.25,
                "volatility": 0.20,
                "breadth": 0.20
            }
            
            total_score = sum(scores[k] * weights[k] for k in scores)
            
            # 判斷市場狀態
            if total_score >= 0.6:
                return MarketRegime.BULL
            elif total_score <= -0.6:
                return MarketRegime.BEAR
            elif latest.get("drawdown", 0) < self.params["drawdown_threshold"]:
                return MarketRegime.CRISIS
            else:
                return MarketRegime.SIDEWAYS
                
        except Exception as e:
            logger.error(f"分析市場狀態失敗: {e}")
            return MarketRegime.SIDEWAYS

    def _calculate_trend_score(self, df: pd.DataFrame) -> float:
        """計算趨勢分數 (-1 到 1)"""
        try:
            latest = df.iloc[-1]
            score = 0.0
            
            # 均線排列
            if latest["sma_short"] > latest["sma_long"]:
                score += 0.5  # 多頭排列
            else:
                score -= 0.5  # 空頭排列
            
            # 價格在均線之上
            if latest["Close"] > latest["sma_short"]:
                score += 0.3
            else:
                score -= 0.3
            
            # 均線斜率
            sma_short_slope = (df["sma_short"].iloc[-1] - df["sma_short"].iloc[-5]) / df["sma_short"].iloc[-5]
            if sma_short_slope > 0:
                score += 0.2
            else:
                score -= 0.2
            
            return np.clip(score, -1, 1)
            
        except Exception as e:
            logger.error(f"計算趨勢分數失敗: {e}")
            return 0.0

    def _calculate_momentum_score(self, df: pd.DataFrame) -> float:
        """計算動量分數 (-1 到 1)"""
        try:
            latest = df.iloc[-1]
            score = 0.0
            
            # 20 日動量
            momentum_20 = latest.get("momentum_20", 0)
            if momentum_20 > 0.05:
                score += 0.4
            elif momentum_20 > 0:
                score += 0.2
            elif momentum_20 > -0.05:
                score -= 0.2
            else:
                score -= 0.4
            
            # 60 日動量
            momentum_60 = latest.get("momentum_60", 0)
            if momentum_60 > 0.10:
                score += 0.3
            elif momentum_60 > 0:
                score += 0.15
            elif momentum_60 > -0.10:
                score -= 0.15
            else:
                score -= 0.3
            
            # RSI
            rsi = latest.get("rsi", 50)
            if rsi > 60:
                score += 0.3
            elif rsi > 50:
                score += 0.15
            elif rsi > 40:
                score -= 0.15
            else:
                score -= 0.3
            
            return np.clip(score, -1, 1)
            
        except Exception as e:
            logger.error(f"計算動量分數失敗: {e}")
            return 0.0

    def _calculate_volatility_score(self, df: pd.DataFrame) -> float:
        """計算波動率分數 (-1 到 1)"""
        try:
            latest = df.iloc[-1]
            volatility = latest.get("volatility", 0)
            
            # 低波動率 = 正分，高波動率 = 負分
            if volatility < 0.01:
                return 0.8  # 非常低波動
            elif volatility < 0.02:
                return 0.4  # 低波動
            elif volatility < 0.03:
                return 0.0  # 正常波動
            elif volatility < 0.04:
                return -0.4  # 高波動
            else:
                return -0.8  # 非常高波動
                
        except Exception as e:
            logger.error(f"計算波動率分數失敗: {e}")
            return 0.0

    def _calculate_breadth_score(self, df: pd.DataFrame) -> float:
        """計算市場寬度分數 (-1 到 1)"""
        try:
            # 簡化版本：使用 RSI 分佈
            rsi = df["rsi"].iloc[-20:]  # 最近 20 天
            
            # 計算 RSI > 50 的比例
            bullish_ratio = (rsi > 50).mean()
            
            if bullish_ratio > 0.7:
                return 0.8  # 強勢市場
            elif bullish_ratio > 0.5:
                return 0.3  # 偏多
            elif bullish_ratio > 0.3:
                return -0.3  # 偏空
            else:
                return -0.8  # 弱勢市場
                
        except Exception as e:
            logger.error(f"計算市場寬度分數失敗: {e}")
            return 0.0

    def _calculate_confidence(self, df: pd.DataFrame, regime: MarketRegime) -> int:
        """計算信心水平 (0-100)"""
        try:
            # 基礎信心
            confidence = 50
            
            # 趨勢一致性
            trend_score = self._calculate_trend_score(df)
            momentum_score = self._calculate_momentum_score(df)
            
            # 指標一致性
            if (trend_score > 0 and momentum_score > 0) or \
               (trend_score < 0 and momentum_score < 0):
                confidence += 20  # 指標一致
            
            # 波動率影響
            volatility = df["volatility"].iloc[-1]
            if volatility < 0.02:
                confidence += 10  # 低波動，信心較高
            elif volatility > 0.04:
                confidence -= 10  # 高波動，信心較低
            
            # 回撤影響
            drawdown = df["drawdown"].iloc[-1]
            if drawdown > -0.05:
                confidence += 10  # 小回撤
            elif drawdown < -0.15:
                confidence -= 20  # 大回撤
            
            return np.clip(confidence, 0, 100)
            
        except Exception as e:
            logger.error(f"計算信心水平失敗: {e}")
            return 50

    def _generate_suggestion(self, regime: MarketRegime, df: pd.DataFrame) -> Dict:
        """生成投資建議"""
        try:
            latest = df.iloc[-1]
            
            if regime == MarketRegime.BULL:
                return {
                    "action": "積極買入",
                    "position_size": "70-90%",
                    "strategy": "順勢交易，追蹤趨勢",
                    "risk_level": "中",
                    "reason": "市場處於多頭格局，可積極佈局"
                }
            
            elif regime == MarketRegime.BEAR:
                return {
                    "action": "減碼觀望",
                    "position_size": "20-40%",
                    "strategy": "防禦為主，選擇性買入",
                    "risk_level": "高",
                    "reason": "市場處於空頭格局，應降低曝險"
                }
            
            elif regime == MarketRegime.CRISIS:
                return {
                    "action": "停損出場",
                    "position_size": "0-20%",
                    "strategy": "保留現金，等待機會",
                    "risk_level": "極高",
                    "reason": "市場出現危機訊號，應優先保護資金"
                }
            
            else:  # SIDEWAYS
                return {
                    "action": "區間操作",
                    "position_size": "40-60%",
                    "strategy": "高拋低吸，選擇強勢股",
                    "risk_level": "中",
                    "reason": "市場盤整，適合區間操作"
                }
                
        except Exception as e:
            logger.error(f"生成建議失敗: {e}")
            return {
                "action": "觀望",
                "position_size": "50%",
                "strategy": "等待明確方向",
                "risk_level": "中",
                "reason": "無法判斷，建議觀望"
            }

    def _get_regime_name(self, regime: MarketRegime) -> str:
        """取得市場狀態名稱"""
        names = {
            MarketRegime.BULL: "牛市 🐂",
            MarketRegime.BEAR: "熊市 🐻",
            MarketRegime.SIDEWAYS: "盤整 ↔️",
            MarketRegime.CRISIS: "危機 ⚠️"
        }
        return names.get(regime, "未知")

    def _get_indicator_summary(self, df: pd.DataFrame) -> Dict:
        """取得指標摘要"""
        try:
            latest = df.iloc[-1]
            
            # 轉換 numpy 類型為 Python 類型
            def to_python_type(value):
                if isinstance(value, (np.integer, np.int64, np.int32)):
                    return int(value)
                elif isinstance(value, (np.floating, np.float64, np.float32)):
                    return float(value)
                elif isinstance(value, np.ndarray):
                    return value.tolist()
                return value
            
            return {
                "close": to_python_type(latest["Close"]),
                "sma_short": to_python_type(latest.get("sma_short", 0)),
                "sma_long": to_python_type(latest.get("sma_long", 0)),
                "rsi": to_python_type(latest.get("rsi", 50)),
                "volatility": to_python_type(latest.get("volatility", 0)),
                "drawdown": to_python_type(latest.get("drawdown", 0)),
                "momentum_20": to_python_type(latest.get("momentum_20", 0)),
                "momentum_60": to_python_type(latest.get("momentum_60", 0))
            }
            
        except Exception as e:
            logger.error(f"取得指標摘要失敗: {e}")
            return {}

    def get_regime_history(self) -> List[Dict]:
        """取得市場狀態歷史"""
        return self.regime_history[-30:]  # 最近 30 筆


# 全局實例
_regime_detector = None


def get_market_regime_detector() -> MarketRegimeDetector:
    """取得 MarketRegimeDetector 單例"""
    global _regime_detector
    if _regime_detector is None:
        _regime_detector = MarketRegimeDetector()
    return _regime_detector
