"""
台灣股票分析工具 - 建議引擎模組
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from loguru import logger

# 導入分析模組
from analysis.technical_analysis import TechnicalAnalysis
from analysis.fundamental_analysis import FundamentalAnalysis
from analysis.valuation_analysis import ValuationAnalysis
from analysis.ml_prediction import MLPrediction


class RecommendationEngine:
    """建議引擎類"""
    
    def __init__(self):
        self.technical_analysis = TechnicalAnalysis()
        self.fundamental_analysis = FundamentalAnalysis()
        self.valuation_analysis = ValuationAnalysis()
        self.ml_prediction = MLPrediction()
    
    async def get_recommendation(self, stock_id: str) -> Dict:
        """獲取買賣建議"""
        try:
            # 執行各種分析
            technical_result = await self.technical_analysis.analyze(stock_id)
            fundamental_result = await self.fundamental_analysis.analyze(stock_id)
            valuation_result = await self.valuation_analysis.analyze(stock_id)
            prediction_result = await self.ml_prediction.predict(stock_id, "ensemble", 30)
            
            # 生成建議
            recommendation = {
                "stock_id": stock_id,
                "timestamp": pd.Timestamp.now().isoformat(),
                "technical_analysis": technical_result,
                "fundamental_analysis": fundamental_result,
                "valuation_analysis": valuation_result,
                "ml_prediction": prediction_result,
                "overall_recommendation": {},
                "risk_assessment": {},
                "action_plan": {}
            }
            
            # 生成總體建議
            recommendation["overall_recommendation"] = self._generate_overall_recommendation(
                technical_result, fundamental_result, valuation_result, prediction_result
            )
            
            # 評估風險
            recommendation["risk_assessment"] = self._assess_risk(
                technical_result, fundamental_result, valuation_result, prediction_result
            )
            
            # 生成行動計劃
            recommendation["action_plan"] = self._generate_action_plan(
                recommendation["overall_recommendation"],
                recommendation["risk_assessment"]
            )
            
            return recommendation
            
        except Exception as e:
            logger.error(f"獲取買賣建議失敗: {e}")
            raise
    
    def _generate_overall_recommendation(self, technical: Dict, fundamental: Dict, valuation: Dict, prediction: Dict) -> Dict:
        """生成總體建議"""
        try:
            # 計算各個分析的分數
            scores = {
                "technical": self._calculate_technical_score(technical),
                "fundamental": self._calculate_fundamental_score(fundamental),
                "valuation": self._calculate_valuation_score(valuation),
                "prediction": self._calculate_prediction_score(prediction)
            }
            
            # 計算加權總分（技術分析30%，基本面30%，估值25%，預測15%）
            weights = {
                "technical": 0.30,
                "fundamental": 0.30,
                "valuation": 0.25,
                "prediction": 0.15
            }
            
            weighted_score = 0
            for category, score in scores.items():
                weighted_score += score * weights[category]
            
            # 生成建議
            recommendation = "hold"
            confidence = "medium"
            
            if weighted_score > 0.6:
                recommendation = "buy"
                confidence = "high"
            elif weighted_score > 0.3:
                recommendation = "buy"
                confidence = "medium"
            elif weighted_score < -0.6:
                recommendation = "sell"
                confidence = "high"
            elif weighted_score < -0.3:
                recommendation = "sell"
                confidence = "medium"
            else:
                recommendation = "hold"
                confidence = "medium"
            
            return {
                "recommendation": recommendation,
                "confidence": confidence,
                "weighted_score": weighted_score,
                "component_scores": scores,
                "weights": weights,
                "reasoning": self._generate_reasoning(scores, recommendation)
            }
            
        except Exception as e:
            logger.error(f"生成總體建議失敗: {e}")
            raise
    
    def _calculate_technical_score(self, technical: Dict) -> float:
        """計算技術分析分數"""
        try:
            score = 0
            
            # 分析信號
            signals = technical.get("signals", {})
            overall_signal = signals.get("overall_signal", "neutral")
            confidence = signals.get("confidence", 0.5)
            
            if overall_signal == "buy":
                score = confidence
            elif overall_signal == "sell":
                score = -confidence
            else:
                score = 0
            
            # 分析摘要
            summary = technical.get("summary", {})
            trend = summary.get("trend", "neutral")
            
            if trend == "bullish":
                score += 0.2
            elif trend == "bearish":
                score -= 0.2
            
            return max(-1, min(1, score))  # 限制在-1到1之間
            
        except Exception as e:
            logger.error(f"計算技術分析分數失敗: {e}")
            return 0
    
    def _calculate_fundamental_score(self, fundamental: Dict) -> float:
        """計算基本面分析分數"""
        try:
            score = 0
            
            # 分析獲利能力
            profitability = fundamental.get("profitability", {})
            if profitability.get("rating") == "excellent":
                score += 0.3
            elif profitability.get("rating") == "good":
                score += 0.15
            elif profitability.get("rating") == "poor":
                score -= 0.3
            
            # 分析成長性
            growth = fundamental.get("growth", {})
            if growth.get("rating") == "excellent":
                score += 0.3
            elif growth.get("rating") == "good":
                score += 0.15
            elif growth.get("rating") == "poor":
                score -= 0.3
            
            # 分析穩定性
            stability = fundamental.get("stability", {})
            if stability.get("rating") == "excellent":
                score += 0.2
            elif stability.get("rating") == "good":
                score += 0.1
            elif stability.get("rating") == "poor":
                score -= 0.2
            
            return max(-1, min(1, score))  # 限制在-1到1之間
            
        except Exception as e:
            logger.error(f"計算基本面分析分數失敗: {e}")
            return 0
    
    def _calculate_valuation_score(self, valuation: Dict) -> float:
        """計算估值分析分數"""
        try:
            score = 0
            
            # 分析綜合估值
            composite = valuation.get("composite_valuation", {})
            weighted_score = composite.get("weighted_score", 0)
            
            # 轉換為-1到1的分數
            score = weighted_score
            
            return max(-1, min(1, score))  # 限制在-1到1之間
            
        except Exception as e:
            logger.error(f"計算估值分析分數失敗: {e}")
            return 0
    
    def _calculate_prediction_score(self, prediction: Dict) -> float:
        """計算預測分析分數"""
        try:
            score = 0
            
            # 分析預測結果
            summary = prediction.get("summary", {})
            expected_return = summary.get("expected_return", 0)
            trend = summary.get("trend", "neutral")
            
            # 根據預期收益率計算分數
            if expected_return > 0.1:
                score = 0.8
            elif expected_return > 0.05:
                score = 0.5
            elif expected_return > 0:
                score = 0.2
            elif expected_return > -0.05:
                score = -0.2
            elif expected_return > -0.1:
                score = -0.5
            else:
                score = -0.8
            
            # 根據趨勢調整
            if trend == "up":
                score += 0.2
            elif trend == "down":
                score -= 0.2
            
            return max(-1, min(1, score))  # 限制在-1到1之間
            
        except Exception as e:
            logger.error(f"計算預測分析分數失敗: {e}")
            return 0
    
    def _assess_risk(self, technical: Dict, fundamental: Dict, valuation: Dict, prediction: Dict) -> Dict:
        """評估風險"""
        try:
            risk_factors = []
            risk_score = 0
            
            # 技術分析風險
            technical_summary = technical.get("summary", {})
            if technical_summary.get("risk_level") == "high":
                risk_factors.append("技術面風險高")
                risk_score += 0.3
            
            # 基本面風險
            fundamental_summary = fundamental.get("summary", {})
            if "weaknesses" in fundamental_summary:
                for weakness in fundamental_summary["weaknesses"]:
                    if "獲利" in weakness or "成長" in weakness:
                        risk_factors.append(f"基本面風險：{weakness}")
                        risk_score += 0.2
            
            # 估值風險
            valuation_summary = valuation.get("summary", {})
            if valuation_summary.get("overall_valuation") == "overvalued":
                risk_factors.append("估值偏高")
                risk_score += 0.3
            
            # 預測風險
            prediction_summary = prediction.get("summary", {})
            if prediction_summary.get("volatility") == "high":
                risk_factors.append("波動性高")
                risk_score += 0.2
            
            # 計算總體風險等級
            risk_level = "low"
            if risk_score > 0.6:
                risk_level = "high"
            elif risk_score > 0.3:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            return {
                "risk_score": risk_score,
                "risk_level": risk_level,
                "risk_factors": risk_factors,
                "risk_mitigation": self._generate_risk_mitigation(risk_factors)
            }
            
        except Exception as e:
            logger.error(f"評估風險失敗: {e}")
            raise
    
    def _generate_risk_mitigation(self, risk_factors: List[str]) -> List[str]:
        """生成風險緩解策略"""
        try:
            mitigation = []
            
            for risk in risk_factors:
                if "技術面" in risk:
                    mitigation.append("設定停損點，控制單筆損失")
                elif "基本面" in risk:
                    mitigation.append("分散投資，降低單一個股風險")
                elif "估值" in risk:
                    mitigation.append("等待估值回落再進場")
                elif "波動性" in risk:
                    mitigation.append("降低投資部位，分批進場")
            
            return mitigation
            
        except Exception as e:
            logger.error(f"生成風險緩解策略失敗: {e}")
            return []
    
    def _generate_action_plan(self, recommendation: Dict, risk_assessment: Dict) -> Dict:
        """生成行動計劃"""
        try:
            action_plan = {
                "immediate_action": "none",
                "entry_strategy": {},
                "exit_strategy": {},
                "position_sizing": {},
                "timeline": {}
            }
            
            rec = recommendation.get("recommendation", "hold")
            confidence = recommendation.get("confidence", "medium")
            risk_level = risk_assessment.get("risk_level", "medium")
            
            # 根據建議生成行動
            if rec == "buy":
                action_plan["immediate_action"] = "consider_buy"
                
                # 進場策略
                if confidence == "high":
                    action_plan["entry_strategy"] = {
                        "strategy": "aggressive",
                        "entry_price": "current_price",
                        "position_size": "full_position"
                    }
                else:
                    action_plan["entry_strategy"] = {
                        "strategy": "conservative",
                        "entry_price": "wait_for_dip",
                        "position_size": "half_position"
                    }
                
                # 出場策略
                action_plan["exit_strategy"] = {
                    "take_profit": "10-15%",
                    "stop_loss": "5-8%",
                    "trailing_stop": "5%"
                }
                
            elif rec == "sell":
                action_plan["immediate_action"] = "consider_sell"
                
                # 出場策略
                action_plan["exit_strategy"] = {
                    "strategy": "immediate",
                    "reason": "sell_signal"
                }
                
            else:
                action_plan["immediate_action"] = "hold"
                action_plan["entry_strategy"] = {"strategy": "none"}
                action_plan["exit_strategy"] = {"strategy": "none"}
            
            # 根據風險調整部位大小
            if risk_level == "high":
                action_plan["position_sizing"] = {
                    "max_position": "25%",
                    "suggested_position": "10-15%"
                }
            elif risk_level == "medium":
                action_plan["position_sizing"] = {
                    "max_position": "50%",
                    "suggested_position": "25-30%"
                }
            else:
                action_plan["position_sizing"] = {
                    "max_position": "100%",
                    "suggested_position": "50-75%"
                }
            
            # 時間規劃
            action_plan["timeline"] = {
                "short_term": "1-3個月",
                "medium_term": "3-6個月",
                "long_term": "6-12個月"
            }
            
            return action_plan
            
        except Exception as e:
            logger.error(f"生成行動計劃失敗: {e}")
            raise
    
    def _generate_reasoning(self, scores: Dict, recommendation: str) -> List[str]:
        """生成建議理由"""
        try:
            reasoning = []
            
            # 技術分析理由
            if scores["technical"] > 0.3:
                reasoning.append("技術面顯示買入信號")
            elif scores["technical"] < -0.3:
                reasoning.append("技術面顯示賣出信號")
            
            # 基本面理由
            if scores["fundamental"] > 0.3:
                reasoning.append("基本面表現良好")
            elif scores["fundamental"] < -0.3:
                reasoning.append("基本面表現較弱")
            
            # 估值理由
            if scores["valuation"] > 0.3:
                reasoning.append("估值偏低，具有投資價值")
            elif scores["valuation"] < -0.3:
                reasoning.append("估值偏高，投資風險較大")
            
            # 預測理由
            if scores["prediction"] > 0.3:
                reasoning.append("機器學習預測上漲機率高")
            elif scores["prediction"] < -0.3:
                reasoning.append("機器學習預測下跌機率高")
            
            return reasoning
            
        except Exception as e:
            logger.error(f"生成建議理由失敗: {e}")
            return []