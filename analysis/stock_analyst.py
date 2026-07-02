"""
台灣股票分析工具 - 本地 AI 分析引擎
整合技術分析、基本面分析、ML 預測，生成綜合分析報告
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from loguru import logger

from analysis.fundamental_analysis import FundamentalAnalysis
from analysis.ml_prediction import MLPrediction
from analysis.technical_analysis import TechnicalAnalysis
from data.data_fetcher import DataFetcher
from data.stock_data import StockData


class StockAnalyst:
    """本地 AI 股票分析引擎"""

    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.stock_data = StockData()
        self.technical = TechnicalAnalysis()
        self.ml = MLPrediction()
        self.fundamental = FundamentalAnalysis()

    async def analyze(
        self, stock_id: str, include_ml: bool = True, prediction_days: int = 5
    ) -> Dict:
        """
        綜合分析股票

        Args:
            stock_id: 股票代碼 (e.g., "2330.TW")
            include_ml: 是否包含 ML 預測
            prediction_days: 預測天數

        Returns:
            綜合分析報告
        """
        try:
            logger.info(f"開始分析 {stock_id}...")
            start_time = datetime.now()

            # 並行取得資料
            price_data = await self.data_fetcher.get_stock_price(stock_id, period="1y")
            realtime = await self.data_fetcher.get_realtime_price(stock_id)

            # 轉換為 DataFrame
            df = pd.DataFrame(price_data["data"])
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)
            df = df.sort_index()

            # 執行技術分析
            tech_result = await self.technical.analyze(stock_id)

            # 執行 ML 預測
            ml_result = {}
            if include_ml:
                try:
                    ml_result = await self.ml.predict(
                        stock_id, model="ensemble", days=prediction_days
                    )
                except Exception as e:
                    logger.warning(f"ML 預測失敗: {e}")

            # 生成 AI 分析報告
            analysis_report = self._generate_analysis_report(
                stock_id=stock_id,
                price_data=price_data,
                realtime=realtime,
                tech_result=tech_result,
                ml_result=ml_result,
                df=df,
            )

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"{stock_id} 分析完成，耗時 {elapsed:.1f} 秒")

            return analysis_report

        except Exception as e:
            logger.error(f"分析 {stock_id} 失敗: {e}")
            raise

    def _generate_analysis_report(
        self,
        stock_id: str,
        price_data: Dict,
        realtime: Dict,
        tech_result: Dict,
        ml_result: Dict,
        df: pd.DataFrame,
    ) -> Dict:
        """生成綜合分析報告"""

        # 基本資訊
        latest_price = realtime.get("price", 0)
        change = realtime.get("change", 0)
        change_pct = realtime.get("change_percent", 0)

        # 技術指標摘要
        tech_summary = tech_result.get("summary", {})
        tech_indicators = tech_result.get("indicators", {})

        # ML 預測摘要
        ml_summary = ml_result.get("summary", {}) if ml_result else {}
        ml_predictions = ml_result.get("predictions", {}) if ml_result else {}

        # 趨勢判斷
        trend_analysis = self._analyze_trend(df, tech_indicators)

        # 生成投資建議
        recommendation = self._generate_recommendation(
            latest_price=latest_price,
            trend_analysis=trend_analysis,
            tech_summary=tech_summary,
            ml_summary=ml_summary,
            tech_indicators=tech_indicators,
        )

        # 生成風險評估
        risk_assessment = self._assess_risk(df, tech_indicators)

        # 生成操作建議
        action_plan = self._generate_action_plan(
            recommendation=recommendation,
            trend_analysis=trend_analysis,
            risk_assessment=risk_assessment,
            latest_price=latest_price,
            tech_indicators=tech_indicators,
        )

        return {
            "stock_id": stock_id,
            "timestamp": datetime.now().isoformat(),
            "price_info": {
                "current": latest_price,
                "change": change,
                "change_percent": change_pct,
                "high_52w": price_data.get("summary", {}).get("highest_price", 0),
                "low_52w": price_data.get("summary", {}).get("lowest_price", 0),
                "avg_volume": df["volume"].tail(20).mean() if not df.empty else 0,
            },
            "trend_analysis": trend_analysis,
            "technical_summary": tech_summary,
            "ml_prediction": {
                "model": ml_predictions.get("ensemble", {}).get("model", "N/A"),
                "trend": ml_predictions.get("ensemble", {}).get("trend", "N/A"),
                "expected_return": ml_predictions.get("ensemble", {}).get(
                    "expected_return", 0
                ),
                "predictions": ml_predictions.get("ensemble", {}).get(
                    "predictions", []
                )[:5],
                "model_agreement": ml_predictions.get("ensemble", {}).get(
                    "model_agreement", 0
                ),
            },
            "recommendation": recommendation,
            "risk_assessment": risk_assessment,
            "action_plan": action_plan,
            "analysis_summary": self._generate_text_summary(
                stock_id, latest_price, trend_analysis, recommendation, risk_assessment
            ),
        }

    def _analyze_trend(self, df: pd.DataFrame, tech_indicators: Dict) -> Dict:
        """分析價格趨勢"""
        try:
            if df.empty:
                return {
                    "short_term": "neutral",
                    "medium_term": "neutral",
                    "long_term": "neutral",
                    "strength": 0,
                }

            close = df["close"]

            # 短期趨勢（5日）
            ma5 = close.rolling(5).mean()
            short_trend = "up" if close.iloc[-1] > ma5.iloc[-1] else "down"

            # 中期趨勢（20日）
            ma20 = close.rolling(20).mean()
            medium_trend = "up" if close.iloc[-1] > ma20.iloc[-1] else "down"

            # 長期趨勢（60日）
            ma60 = close.rolling(60).mean()
            long_trend = (
                "up"
                if close.iloc[-1] > ma60.iloc[-1]
                else "down" if len(close) >= 60 else "neutral"
            )

            # 趨勢強度（用最近20日報酬率的標準差）
            returns = close.pct_change().tail(20)
            volatility = returns.std()

            # 動量（最近5日報酬率）
            momentum = (
                (close.iloc[-1] / close.iloc[-6] - 1) * 100 if len(close) >= 6 else 0
            )

            # 趨勢評分（-100 到 100）
            score = 0
            if short_trend == "up":
                score += 20
            else:
                score -= 20
            if medium_trend == "up":
                score += 30
            else:
                score -= 30
            if long_trend == "up":
                score += 50
            else:
                score -= 50

            # 調整動量
            score += min(max(momentum * 2, -20), 20)

            return {
                "short_term": short_trend,
                "medium_term": medium_trend,
                "long_term": long_trend,
                "momentum_5d": round(momentum, 2),
                "volatility": round(volatility * 100, 2),
                "score": round(score, 1),
                "ma5": round(float(ma5.iloc[-1]), 2) if not ma5.empty else 0,
                "ma20": round(float(ma20.iloc[-1]), 2) if not ma20.empty else 0,
                "ma60": round(float(ma60.iloc[-1]), 2) if len(close) >= 60 else 0,
            }
        except Exception as e:
            logger.error(f"趨勢分析失敗: {e}")
            return {
                "short_term": "neutral",
                "medium_term": "neutral",
                "long_term": "neutral",
                "score": 0,
            }

    def _generate_recommendation(
        self,
        latest_price: float,
        trend_analysis: Dict,
        tech_summary: Dict,
        ml_summary: Dict,
        tech_indicators: Dict,
    ) -> Dict:
        """生成投資建議"""
        try:
            score = 0
            reasons = []

            # 趨勢評分
            trend_score = trend_analysis.get("score", 0)
            score += trend_score * 0.3

            if trend_score > 50:
                reasons.append("多頭趨勢明確")
            elif trend_score < -50:
                reasons.append("空頭趨勢明顯")

            # 技術指標評分
            rsi = tech_indicators.get("rsi", {})
            if rsi:
                rsi_value = rsi.get("value", 50)
                if rsi_value < 30:
                    score += 15
                    reasons.append(f"RSI={rsi_value:.0f} 超賣")
                elif rsi_value > 70:
                    score -= 15
                    reasons.append(f"RSI={rsi_value:.0f} 超買")

            macd = tech_indicators.get("macd", {})
            if macd:
                macd_signal = macd.get("signal", "")
                if macd_signal == "bullish":
                    score += 10
                    reasons.append("MACD 看多")
                elif macd_signal == "bearish":
                    score -= 10
                    reasons.append("MACD 看空")

            bollinger = tech_indicators.get("bollinger", {})
            if bollinger:
                position = bollinger.get("position", "")
                if position == "below_lower":
                    score += 10
                    reasons.append("價格低於布林下軌")
                elif position == "above_upper":
                    score -= 10
                    reasons.append("價格高於布林上軌")

            # ML 預測評分
            ml_trend = ml_summary.get("trend", "")
            ml_expected_return = ml_summary.get("expected_return", 0)

            if ml_trend == "up":
                score += 15
                reasons.append(f"ML預測上漲 {ml_expected_return:.1%}")
            elif ml_trend == "down":
                score -= 15
                reasons.append(f"ML預測下跌 {ml_expected_return:.1%}")

            # 生成建議
            if score >= 40:
                action = "buy"
                confidence = min(90, 60 + score * 0.3)
                risk_level = "中"
            elif score >= 10:
                action = "buy_light"
                confidence = min(80, 50 + score * 0.3)
                risk_level = "中低"
            elif score <= -40:
                action = "sell"
                confidence = min(90, 60 + abs(score) * 0.3)
                risk_level = "高"
            elif score <= -10:
                action = "sell_light"
                confidence = min(80, 50 + abs(score) * 0.3)
                risk_level = "中高"
            else:
                action = "hold"
                confidence = 50
                risk_level = "中"

            return {
                "action": action,
                "score": round(score, 1),
                "confidence": round(confidence, 1),
                "risk_level": risk_level,
                "reasons": reasons,
                "target_price": self._calculate_target_price(
                    latest_price, trend_analysis, ml_summary
                ),
                "stop_loss": round(latest_price * 0.95, 2),
            }
        except Exception as e:
            logger.error(f"生成建議失敗: {e}")
            return {
                "action": "hold",
                "score": 0,
                "confidence": 50,
                "risk_level": "中",
                "reasons": [],
            }

    def _calculate_target_price(self, current: float, trend: Dict, ml: Dict) -> float:
        """計算目標價"""
        try:
            # 使用 ML 預測
            ml_expected = ml.get("expected_return", 0)
            if ml_expected != 0:
                target = current * (1 + ml_expected)
                return round(target, 2)

            # 使用趨勢分析
            trend_score = trend.get("score", 0)
            if trend_score > 50:
                return round(current * 1.1, 2)
            elif trend_score < -50:
                return round(current * 0.9, 2)
            else:
                return round(current * 1.03, 2)
        except Exception:
            return round(current * 1.05, 2)

    def _assess_risk(self, df: pd.DataFrame, tech_indicators: Dict) -> Dict:
        """評估風險"""
        try:
            if df.empty:
                return {"level": "medium", "score": 50, "factors": []}

            factors = []
            risk_score = 0

            # 波動率風險
            returns = df["close"].pct_change().tail(20)
            volatility = returns.std() * np.sqrt(252) * 100  # 年化波動率
            if volatility > 40:
                risk_score += 30
                factors.append(f"波動率高 ({volatility:.1f}%)")
            elif volatility > 25:
                risk_score += 15
                factors.append(f"波動率中等 ({volatility:.1f}%)")
            else:
                factors.append(f"波動率低 ({volatility:.1f}%)")

            # ATR 風險
            atr = tech_indicators.get("atr", {})
            if atr:
                atr_value = atr.get("value", 0)
                atr_pct = (
                    (atr_value / df["close"].iloc[-1]) * 100
                    if df["close"].iloc[-1] > 0
                    else 0
                )
                if atr_pct > 3:
                    risk_score += 20
                    factors.append(f"ATR 偏高 ({atr_pct:.1f}%)")

            # RSI 極端值風險
            rsi = tech_indicators.get("rsi", {})
            if rsi:
                rsi_value = rsi.get("value", 50)
                if rsi_value > 80 or rsi_value < 20:
                    risk_score += 15
                    factors.append(f"RSI 極端 ({rsi_value:.0f})")

            # 趨勢反轉風險
            trend_score = tech_indicators.get("trend", {}).get("score", 0)
            if abs(trend_score) > 60:
                risk_score += 10
                factors.append("趨勢可能反轉")

            # 風險等級
            if risk_score >= 60:
                level = "high"
            elif risk_score >= 30:
                level = "medium"
            else:
                level = "low"

            return {
                "level": level,
                "score": round(risk_score, 1),
                "factors": factors,
                "volatility_annual": round(volatility, 1),
            }
        except Exception as e:
            logger.error(f"風險評估失敗: {e}")
            return {"level": "medium", "score": 50, "factors": []}

    def _generate_action_plan(
        self,
        recommendation: Dict,
        trend_analysis: Dict,
        risk_assessment: Dict,
        latest_price: float,
        tech_indicators: Dict,
    ) -> Dict:
        """生成操作計劃"""
        try:
            action = recommendation.get("action", "hold")
            target = recommendation.get("target_price", latest_price * 1.05)
            stop_loss = recommendation.get("stop_loss", latest_price * 0.95)
            risk_level = risk_assessment.get("level", "medium")

            # 倉位建議
            if risk_level == "high":
                position_pct = 20
            elif risk_level == "medium":
                position_pct = 40
            else:
                position_pct = 60

            # 具體操作
            if action in ["buy", "buy_light"]:
                plan = {
                    "action": "買入",
                    "entry_price": latest_price,
                    "target_price": target,
                    "stop_loss": stop_loss,
                    "position_size": f"{position_pct}%",
                    "steps": [
                        f"1. 在 {latest_price:.2f} 附近分批買入",
                        f"2. 設定停損點 {stop_loss:.2f}",
                        f"3. 目標價 {target:.2f}",
                        "4. 定期檢視技術指標",
                    ],
                }
            elif action in ["sell", "sell_light"]:
                plan = {
                    "action": "賣出",
                    "entry_price": latest_price,
                    "target_price": target,
                    "stop_loss": stop_loss,
                    "position_size": f"{position_pct}%",
                    "steps": [
                        f"1. 在 {latest_price:.2f} 附近分批賣出",
                        f"2. 若反彈至 {latest_price * 1.02:.2f} 考慮加碼賣出",
                        "3. 觀望後再決定是否回補",
                    ],
                }
            else:
                plan = {
                    "action": "持有觀望",
                    "entry_price": latest_price,
                    "target_price": target,
                    "stop_loss": stop_loss,
                    "position_size": f"{position_pct}%",
                    "steps": [
                        "1. 維持現有部位",
                        "2. 設定提醒價格",
                        "3. 等待明確訊號再行動",
                    ],
                }

            return plan
        except Exception as e:
            logger.error(f"生成操作計劃失敗: {e}")
            return {"action": "持有觀望", "steps": []}

    def _generate_text_summary(
        self,
        stock_id: str,
        latest_price: float,
        trend_analysis: Dict,
        recommendation: Dict,
        risk_assessment: Dict,
    ) -> str:
        """生成文字摘要"""
        try:
            trend = trend_analysis.get("short_term", "neutral")
            trend_desc = (
                "上漲" if trend == "up" else "下跌" if trend == "down" else "盤整"
            )

            action = recommendation.get("action", "hold")
            action_desc = {
                "buy": "建議買入",
                "buy_light": "建議輕倉買入",
                "sell": "建議賣出",
                "sell_light": "建議輕倉賣出",
                "hold": "建議持有觀望",
            }.get(action, "建議觀望")

            risk = risk_assessment.get("level", "medium")
            risk_desc = {"high": "高風險", "medium": "中等風險", "low": "低風險"}.get(
                risk, "中等風險"
            )

            summary = f"""
【{stock_id} 綜合分析報告】

📊 現價: {latest_price:.2f}
📈 趨勢: {trend_analysis.get('medium_term', 'neutral')} (中期), {trend} (短期)
🎯 建議: {action_desc}
⚠️ 風險: {risk_desc}
📈 目標價: {recommendation.get('target_price', 0):.2f}
📉 停損價: {recommendation.get('stop_loss', 0):.2f}

主要理由:
"""
            for reason in recommendation.get("reasons", []):
                summary += f"• {reason}\n"

            if risk_assessment.get("factors"):
                summary += "\n風險因素:\n"
                for factor in risk_assessment["factors"]:
                    summary += f"• {factor}\n"

            return summary.strip()
        except Exception as e:
            logger.error(f"生成文字摘要失敗: {e}")
            return f"{stock_id} 分析報告生成失敗"


# 全局實例
_analyst = None


def get_stock_analyst() -> StockAnalyst:
    """取得 StockAnalyst 單例"""
    global _analyst
    if _analyst is None:
        _analyst = StockAnalyst()
    return _analyst
