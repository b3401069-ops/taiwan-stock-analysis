"""
台灣股票分析工具 - AI 選股摘要
使用 Claude API 生成選股報告
參考 taiwan-quant-project 的 report/ai_report.py
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from loguru import logger
import json

from data.data_fetcher import DataFetcher
from analysis.multi_factor_screener import get_multi_factor_screener
from analysis.industry_rotation import get_industry_rotation_analyzer
from analysis.concept_rotation import get_concept_rotation_analyzer
from analysis.market_regime import get_market_regime_detector


class AIStockSummary:
    """AI 選股摘要生成器"""

    def __init__(self):
        """初始化 AI 選股摘要生成器"""
        self.data_fetcher = DataFetcher()
        self.multi_factor_screener = get_multi_factor_screener()
        self.industry_rotation = get_industry_rotation_analyzer()
        self.concept_rotation = get_concept_rotation_analyzer()
        self.market_regime = get_market_regime_detector()
        
        # AI 模型設定（可擴展為 Claude API）
        self.ai_model = "local_analysis"  # 本地分析，無需外部 API

    def generate_summary(
        self,
        universe: List[str] = None,
        top_n: int = 10,
        include_analysis: bool = True
    ) -> Dict:
        """
        生成 AI 選股摘要
        
        Args:
            universe: 股票池（預設使用預設股票池）
            top_n: 返回前 N 名
            include_analysis: 是否包含詳細分析
            
        Returns:
            AI 選股摘要
        """
        try:
            logger.info("開始生成 AI 選股摘要...")
            
            # 1. 多因子選股篩選
            screener_results = self.multi_factor_screener.screen(universe, top_n)
            
            # 2. 市場狀態分析
            market_analysis = self._analyze_market_regime()
            
            # 3. 產業輪動分析
            industry_analysis = self._analyze_industry_rotation()
            
            # 4. 概念股輪動分析
            concept_analysis = self._analyze_concept_rotation()
            
            # 5. 生成投資建議
            investment_advice = self._generate_investment_advice(
                screener_results, market_analysis, industry_analysis, concept_analysis
            )
            
            # 6. 風險提示
            risk_warnings = self._generate_risk_warnings(
                market_analysis, screener_results
            )
            
            # 7. 生成摘要報告
            summary_report = self._generate_report(
                screener_results, market_analysis, industry_analysis,
                concept_analysis, investment_advice, risk_warnings, include_analysis
            )
            
            logger.info("AI 選股摘要生成完成")
            
            return {
                "success": True,
                "data": summary_report
            }
            
        except Exception as e:
            logger.error(f"生成 AI 選股摘要失敗: {e}")
            return {"success": False, "error": str(e)}

    def _analyze_market_regime(self) -> Dict:
        """分析市場狀態"""
        try:
            result = self.market_regime.detect_regime("^TWII")
            if result.get("success"):
                return result["data"]
            else:
                return {
                    "regime": "unknown",
                    "regime_name": "未知",
                    "confidence": 0,
                    "suggestion": {
                        "action": "觀望",
                        "reason": "無法判斷市場狀態"
                    }
                }
        except Exception as e:
            logger.error(f"分析市場狀態失敗: {e}")
            return {
                "regime": "unknown",
                "regime_name": "未知",
                "confidence": 0,
                "suggestion": {
                    "action": "觀望",
                    "reason": "分析失敗"
                }
            }

    def _analyze_industry_rotation(self) -> Dict:
        """分析產業輪動"""
        try:
            result = self.industry_rotation.get_rotation_analysis("6mo")
            if result.get("success"):
                return result["data"]
            else:
                return {
                    "industry_ranking": [],
                    "rotation_opportunities": [],
                    "summary": {
                        "strongest_industry": "N/A",
                        "weakest_industry": "N/A",
                        "total_opportunities": 0
                    }
                }
        except Exception as e:
            logger.error(f"分析產業輪動失敗: {e}")
            return {
                "industry_ranking": [],
                "rotation_opportunities": [],
                "summary": {
                    "strongest_industry": "N/A",
                    "weakest_industry": "N/A",
                    "total_opportunities": 0
                }
            }

    def _analyze_concept_rotation(self) -> Dict:
        """分析概念股輪動"""
        try:
            result = self.concept_rotation.get_concept_analysis("6mo")
            if result.get("success"):
                return result["data"]
            else:
                return {
                    "concept_ranking": [],
                    "hot_concepts": [],
                    "summary": {
                        "hottest_concept": "N/A",
                        "total_hot_concepts": 0,
                        "total_concepts": 0
                    }
                }
        except Exception as e:
            logger.error(f"分析概念股輪動失敗: {e}")
            return {
                "concept_ranking": [],
                "hot_concepts": [],
                "summary": {
                    "hottest_concept": "N/A",
                    "total_hot_concepts": 0,
                    "total_concepts": 0
                }
            }

    def _generate_investment_advice(
        self,
        screener_results: List,
        market_analysis: Dict,
        industry_analysis: Dict,
        concept_analysis: Dict
    ) -> Dict:
        """生成投資建議"""
        try:
            # 市場狀態建議
            market_regime = market_analysis.get("regime", "unknown")
            market_suggestion = market_analysis.get("suggestion", {})
            
            # 產業建議
            strongest_industry = industry_analysis.get("summary", {}).get("strongest_industry", "N/A")
            weakest_industry = industry_analysis.get("summary", {}).get("weakest_industry", "N/A")
            
            # 概念股建議
            hottest_concept = concept_analysis.get("summary", {}).get("hottest_concept", "N/A")
            
            # 根據市場狀態調整建議
            if market_regime == "bull":
                market_advice = "市場處於多頭格局，可積極佈局"
                position_size = "70-90%"
            elif market_regime == "bear":
                market_advice = "市場處於空頭格局，應降低曝險"
                position_size = "20-40%"
            elif market_regime == "crisis":
                market_advice = "市場出現危機訊號，應優先保護資金"
                position_size = "0-20%"
            else:
                market_advice = "市場盤整，適合區間操作"
                position_size = "40-60%"
            
            # 選股建議
            stock_recommendations = []
            for i, stock in enumerate(screener_results[:5]):  # 前5名
                stock_recommendations.append({
                    "rank": i + 1,
                    "stock_id": stock.stock_id,
                    "stock_name": stock.stock_name,
                    "composite_score": round(stock.composite_score, 4),
                    "reason": f"綜合分數 {stock.composite_score:.4f}，排名第 {i + 1}"
                })
            
            # 產業配置建議
            industry_allocation = {
                "strongest": strongest_industry,
                "weakest": weakest_industry,
                "allocation": {
                    strongest_industry: 0.6,
                    weakest_industry: 0.4
                }
            }
            
            # 概念股建議
            concept_advice = f"目前最熱門的概念是 {hottest_concept}"
            
            return {
                "market_advice": market_advice,
                "position_size": position_size,
                "stock_recommendations": stock_recommendations,
                "industry_allocation": industry_allocation,
                "concept_advice": concept_advice,
                "overall_strategy": self._determine_overall_strategy(market_regime)
            }
            
        except Exception as e:
            logger.error(f"生成投資建議失敗: {e}")
            return {
                "market_advice": "無法生成建議",
                "position_size": "50%",
                "stock_recommendations": [],
                "industry_allocation": {},
                "concept_advice": "無法生成建議",
                "overall_strategy": "觀望"
            }

    def _determine_overall_strategy(self, market_regime: str) -> str:
        """決定整體策略"""
        try:
            if market_regime == "bull":
                return "積極成長策略"
            elif market_regime == "bear":
                return "防禦價值策略"
            elif market_regime == "crisis":
                return "現金為王策略"
            else:
                return "均衡配置策略"
        except Exception as e:
            logger.error(f"決定整體策略失敗: {e}")
            return "均衡配置策略"

    def _generate_risk_warnings(
        self,
        market_analysis: Dict,
        screener_results: List
    ) -> List[str]:
        """生成風險提示"""
        try:
            warnings = []
            
            # 市場風險提示
            market_regime = market_analysis.get("regime", "unknown")
            if market_regime == "crisis":
                warnings.append("⚠️ 市場處於危機狀態，請謹慎投資")
            elif market_regime == "bear":
                warnings.append("⚠️ 市場處於空頭格局，請控制曝險")
            
            # 集中度風險提示
            if len(screener_results) > 0:
                top_stock = screener_results[0]
                if top_stock.composite_score > 0.8:
                    warnings.append(f"⚠️ {top_stock.stock_name} 分數過高，可能有過熱風險")
            
            # 通用風險提示
            warnings.append("📊 所有分析僅供參考，不構成投資建議")
            warnings.append("💰 投資有風險，請謹慎評估")
            warnings.append("📈 建議定期檢視投資組合")
            
            return warnings
            
        except Exception as e:
            logger.error(f"生成風險提示失敗: {e}")
            return ["⚠️ 無法生成風險提示"]

    def _generate_report(
        self,
        screener_results: List,
        market_analysis: Dict,
        industry_analysis: Dict,
        concept_analysis: Dict,
        investment_advice: Dict,
        risk_warnings: List[str],
        include_analysis: bool
    ) -> Dict:
        """生成摘要報告"""
        try:
            # 基本資訊
            report = {
                "timestamp": datetime.now().isoformat(),
                "report_type": "AI 選股摘要",
                "version": "1.0"
            }
            
            # 市場狀態摘要
            report["market_summary"] = {
                "regime": market_analysis.get("regime", "unknown"),
                "regime_name": market_analysis.get("regime_name", "未知"),
                "confidence": market_analysis.get("confidence", 0),
                "suggestion": market_analysis.get("suggestion", {})
            }
            
            # 選股結果摘要
            stock_summary = []
            for stock in screener_results:
                stock_summary.append({
                    "rank": stock.rank,
                    "stock_id": stock.stock_id,
                    "stock_name": stock.stock_name,
                    "composite_score": round(stock.composite_score, 4),
                    "current_price": stock.details.get("current_price", 0),
                    "pe_ratio": stock.details.get("pe_ratio", 0),
                    "pb_ratio": stock.details.get("pb_ratio", 0)
                })
            
            report["stock_summary"] = stock_summary
            
            # 投資建議
            report["investment_advice"] = investment_advice
            
            # 風險提示
            report["risk_warnings"] = risk_warnings
            
            # 詳細分析（可選）
            if include_analysis:
                report["detailed_analysis"] = {
                    "market_analysis": market_analysis,
                    "industry_analysis": industry_analysis,
                    "concept_analysis": concept_analysis,
                    "screener_details": [
                        {
                            "stock_id": stock.stock_id,
                            "stock_name": stock.stock_name,
                            "factor_scores": [
                                {
                                    "factor_type": fs.factor_type.value,
                                    "score": round(fs.score, 4),
                                    "weight": round(fs.weight, 4),
                                    "details": fs.details
                                }
                                for fs in stock.factor_scores
                            ]
                        }
                        for stock in screener_results
                    ]
                }
            
            # 生成執行摘要
            report["executive_summary"] = self._generate_executive_summary(
                market_analysis, screener_results, investment_advice
            )
            
            return report
            
        except Exception as e:
            logger.error(f"生成報告失敗: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }

    def _generate_executive_summary(
        self,
        market_analysis: Dict,
        screener_results: List,
        investment_advice: Dict
    ) -> str:
        """生成執行摘要"""
        try:
            # 市場狀態
            market_regime = market_analysis.get("regime_name", "未知")
            market_confidence = market_analysis.get("confidence", 0)
            
            # 選股結果
            stock_count = len(screener_results)
            top_stock = screener_results[0] if screener_results else None
            
            # 投資建議
            market_advice = investment_advice.get("market_advice", "無法生成建議")
            position_size = investment_advice.get("position_size", "50%")
            overall_strategy = investment_advice.get("overall_strategy", "均衡配置策略")
            
            # 生成摘要文字
            summary = f"""
📊 AI 選股摘要報告

【市場狀態】
目前市場處於 {market_regime} 狀態，信心水平 {market_confidence}%。
{market_advice}

【選股結果】
共篩選出 {stock_count} 檔股票，推薦首選為 {top_stock.stock_name if top_stock else 'N/A'}。

【投資建議】
建議採用 {overall_strategy}，建議部位大小為 {position_size}。

【風險提示】
投資有風險，請謹慎評估，建議定期檢視投資組合。
"""
            
            return summary.strip()
            
        except Exception as e:
            logger.error(f"生成執行摘要失敗: {e}")
            return "無法生成執行摘要"

    def get_ai_analysis_explanation(self) -> Dict:
        """取得 AI 分析解釋"""
        return {
            "methodology": "結合多因子選股、市場狀態偵測、產業輪動、概念股輪動進行綜合分析",
            "data_sources": [
                "Yahoo Finance 歷史資料",
                "FinMind 三大法人資料",
                "技術指標計算",
                "估值指標分析"
            ],
            "analysis_steps": [
                "1. 多因子選股篩選",
                "2. 市場狀態偵測",
                "3. 產業輪動分析",
                "4. 概念股輪動分析",
                "5. 投資建議生成",
                "6. 風險提示生成"
            ],
            "factors_used": [
                "動量因子",
                "價值因子",
                "品質因子",
                "規模因子",
                "流動性因子",
                "法人因子"
            ],
            "limitations": [
                "歷史表現不代表未來",
                "無法預測黑天鵝事件",
                "模型可能存在偏差",
                "需要定期重新校準"
            ],
            "usage_tips": [
                "結合其他分析方法使用",
                "定期檢視模型表現",
                "根據市場變化調整參數",
                "控制單一股票曝險比例"
            ]
        }


# 全局實例
_ai_stock_summary = None


def get_ai_stock_summary() -> AIStockSummary:
    """取得 AIStockSummary 單例"""
    global _ai_stock_summary
    if _ai_stock_summary is None:
        _ai_stock_summary = AIStockSummary()
    return _ai_stock_summary
