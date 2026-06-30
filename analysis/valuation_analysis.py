"""
台灣股票分析工具 - 估值分析模組
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from loguru import logger

# 導入數據處理模組
from data.data_fetcher import DataFetcher
from config.config import VALUATION_MODELS_CONFIG


class ValuationAnalysis:
    """估值分析類"""
    
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.config = VALUATION_MODELS_CONFIG
    
    async def analyze(self, stock_id: str, models: Optional[List[str]] = None) -> Dict:
        """執行估值分析"""
        try:
            # 獲取股票基本資訊
            stock_info = await self.data_fetcher.get_stock_info(stock_id)
            
            # 獲取財務數據
            financial_data = await self.data_fetcher.get_financial_data(stock_id)
            
            # 獲取即時價格數據
            realtime_data = await self.data_fetcher.get_realtime_price(stock_id)
            
            # 默認分析所有估值模型
            if models is None:
                models = ["pe", "pb", "dividend_yield", "ev_ebitda", "fcf_yield"]
            
            analysis_result = {
                "stock_id": stock_id,
                "timestamp": pd.Timestamp.now().isoformat(),
                "company_info": stock_info,
                "current_price": realtime_data.get("price", 0),
                "valuation_models": {},
                "composite_valuation": {},
                "summary": {}
            }
            
            # 計算各個估值模型
            for model in models:
                if model == "pe":
                    analysis_result["valuation_models"]["pe"] = self._calculate_pe_valuation(financial_data, realtime_data)
                elif model == "pb":
                    analysis_result["valuation_models"]["pb"] = self._calculate_pb_valuation(financial_data, realtime_data)
                elif model == "dividend_yield":
                    analysis_result["valuation_models"]["dividend_yield"] = self._calculate_dividend_yield_valuation(financial_data, realtime_data)
                elif model == "ev_ebitda":
                    analysis_result["valuation_models"]["ev_ebitda"] = self._calculate_ev_ebitda_valuation(financial_data, realtime_data)
                elif model == "fcf_yield":
                    analysis_result["valuation_models"]["fcf_yield"] = self._calculate_fcf_yield_valuation(financial_data, realtime_data)
            
            # 計算綜合估值
            analysis_result["composite_valuation"] = self._calculate_composite_valuation(analysis_result["valuation_models"])
            
            # 生成分析摘要
            analysis_result["summary"] = self._generate_summary(analysis_result)
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"估值分析失敗: {e}")
            raise
    
    def _calculate_pe_valuation(self, financial_data: Dict, realtime_data: Dict) -> Dict:
        """計算本益比估值"""
        try:
            pe_ratio = realtime_data.get("pe_ratio", 0)
            
            # 獲取歷史本益比數據（這裡需要從資料庫獲取，暫時使用假設值）
            historical_pe = {
                "average": 15,
                "min": 10,
                "max": 25,
                "current": pe_ratio
            }
            
            # 計算估值
            valuation = "fair"
            if pe_ratio > 0:
                if pe_ratio < historical_pe["average"] * 0.8:
                    valuation = "undervalued"
                elif pe_ratio > historical_pe["average"] * 1.2:
                    valuation = "overvalued"
                else:
                    valuation = "fair"
            
            # 計算目標價格
            target_price = 0
            if pe_ratio > 0 and realtime_data.get("price", 0) > 0:
                # 使用歷史平均本益比計算目標價格
                historical_avg_pe = historical_pe["average"]
                current_price = realtime_data.get("price", 0)
                
                # 假設EPS不變
                eps = current_price / pe_ratio
                target_price = eps * historical_avg_pe
            
            return {
                "current_pe": pe_ratio,
                "historical_pe": historical_pe,
                "valuation": valuation,
                "target_price": target_price,
                "weight": self.config["pe_ratio"]["weight"],
                "description": self.config["pe_ratio"]["description"]
            }
            
        except Exception as e:
            logger.error(f"計算本益比估值失敗: {e}")
            raise
    
    def _calculate_pb_valuation(self, financial_data: Dict, realtime_data: Dict) -> Dict:
        """計算股價淨值比估值"""
        try:
            pb_ratio = 0
            
            # 計算PB比率
            if financial_data.get("balance_sheet"):
                latest_year = max(financial_data["balance_sheet"].keys())
                balance_data = financial_data["balance_sheet"][latest_year]
                
                if "Stockholders Equity" in balance_data and balance_data["Stockholders Equity"] != 0:
                    # 假設股數為1億股
                    shares_outstanding = 100000000
                    book_value_per_share = balance_data["Stockholders Equity"] / shares_outstanding
                    
                    if book_value_per_share > 0:
                        current_price = realtime_data.get("price", 0)
                        pb_ratio = current_price / book_value_per_share
            
            # 獲取歷史PB數據（這裡需要從資料庫獲取，暫時使用假設值）
            historical_pb = {
                "average": 1.5,
                "min": 0.8,
                "max": 2.5,
                "current": pb_ratio
            }
            
            # 計算估值
            valuation = "fair"
            if pb_ratio > 0:
                if pb_ratio < historical_pb["average"] * 0.8:
                    valuation = "undervalued"
                elif pb_ratio > historical_pb["average"] * 1.2:
                    valuation = "overvalued"
                else:
                    valuation = "fair"
            
            # 計算目標價格
            target_price = 0
            if pb_ratio > 0 and realtime_data.get("price", 0) > 0:
                # 使用歷史平均PB計算目標價格
                historical_avg_pb = historical_pb["average"]
                current_price = realtime_data.get("price", 0)
                
                # 假設淨資產不變
                book_value_per_share = current_price / pb_ratio
                target_price = book_value_per_share * historical_avg_pb
            
            return {
                "current_pb": pb_ratio,
                "historical_pb": historical_pb,
                "valuation": valuation,
                "target_price": target_price,
                "weight": self.config["pb_ratio"]["weight"],
                "description": self.config["pb_ratio"]["description"]
            }
            
        except Exception as e:
            logger.error(f"計算股價淨值比估值失敗: {e}")
            raise
    
    def _calculate_dividend_yield_valuation(self, financial_data: Dict, realtime_data: Dict) -> Dict:
        """計算股利殖利率估值"""
        try:
            dividend_yield = realtime_data.get("dividend_yield", 0)
            
            # 獲取歷史股利殖利率數據（這裡需要從資料庫獲取，暫時使用假設值）
            historical_yield = {
                "average": 0.04,
                "min": 0.02,
                "max": 0.06,
                "current": dividend_yield
            }
            
            # 計算估值
            valuation = "fair"
            if dividend_yield > 0:
                if dividend_yield > historical_yield["average"] * 1.2:
                    valuation = "undervalued"  # 高殖利率可能表示股價被低估
                elif dividend_yield < historical_yield["average"] * 0.8:
                    valuation = "overvalued"  # 低殖利率可能表示股價被高估
                else:
                    valuation = "fair"
            
            # 計算目標價格
            target_price = 0
            if dividend_yield > 0 and realtime_data.get("price", 0) > 0:
                # 使用歷史平均殖利率計算目標價格
                historical_avg_yield = historical_yield["average"]
                current_price = realtime_data.get("price", 0)
                
                # 假設股利不變
                dividend_per_share = current_price * dividend_yield
                target_price = dividend_per_share / historical_avg_yield
            
            return {
                "current_yield": dividend_yield,
                "historical_yield": historical_yield,
                "valuation": valuation,
                "target_price": target_price,
                "weight": self.config["dividend_yield"]["weight"],
                "description": self.config["dividend_yield"]["description"]
            }
            
        except Exception as e:
            logger.error(f"計算股利殖利率估值失敗: {e}")
            raise
    
    def _calculate_ev_ebitda_valuation(self, financial_data: Dict, realtime_data: Dict) -> Dict:
        """計算企業價值/EBITDA估值"""
        try:
            ev_ebitda = 0
            
            # 這裡需要企業價值和EBITDA數據
            # 暫時返回示例數據
            
            # 獲取歷史EV/EBITDA數據（這裡需要從資料庫獲取，暫時使用假設值）
            historical_ev_ebitda = {
                "average": 10,
                "min": 6,
                "max": 15,
                "current": ev_ebitda
            }
            
            # 計算估值
            valuation = "fair"
            if ev_ebitda > 0:
                if ev_ebitda < historical_ev_ebitda["average"] * 0.8:
                    valuation = "undervalued"
                elif ev_ebitda > historical_ev_ebitda["average"] * 1.2:
                    valuation = "overvalued"
                else:
                    valuation = "fair"
            
            return {
                "current_ev_ebitda": ev_ebitda,
                "historical_ev_ebitda": historical_ev_ebitda,
                "valuation": valuation,
                "target_price": 0,  # 需要更多數據計算
                "weight": self.config["ev_ebitda"]["weight"],
                "description": self.config["ev_ebitda"]["description"]
            }
            
        except Exception as e:
            logger.error(f"計算EV/EBITDA估值失敗: {e}")
            raise
    
    def _calculate_fcf_yield_valuation(self, financial_data: Dict, realtime_data: Dict) -> Dict:
        """計算自由現金流收益率估值"""
        try:
            fcf_yield = 0
            
            # 計算自由現金流收益率
            if financial_data.get("cash_flow"):
                latest_year = max(financial_data["cash_flow"].keys())
                cashflow_data = financial_data["cash_flow"][latest_year]
                
                if "Free Cash Flow" in cashflow_data:
                    # 假設股數為1億股
                    shares_outstanding = 100000000
                    fcf_per_share = cashflow_data["Free Cash Flow"] / shares_outstanding
                    
                    current_price = realtime_data.get("price", 0)
                    if current_price > 0:
                        fcf_yield = fcf_per_share / current_price
            
            # 獲取歷史FCF收益率數據（這裡需要從資料庫獲取，暫時使用假設值）
            historical_fcf_yield = {
                "average": 0.05,
                "min": 0.02,
                "max": 0.08,
                "current": fcf_yield
            }
            
            # 計算估值
            valuation = "fair"
            if fcf_yield > 0:
                if fcf_yield > historical_fcf_yield["average"] * 1.2:
                    valuation = "undervalued"  # 高FCF收益率可能表示股價被低估
                elif fcf_yield < historical_fcf_yield["average"] * 0.8:
                    valuation = "overvalued"  # 低FCF收益率可能表示股價被高估
                else:
                    valuation = "fair"
            
            # 計算目標價格
            target_price = 0
            if fcf_yield > 0 and realtime_data.get("price", 0) > 0:
                # 使用歷史平均FCF收益率計算目標價格
                historical_avg_yield = historical_fcf_yield["average"]
                current_price = realtime_data.get("price", 0)
                
                # 假設FCF不變
                fcf_per_share = current_price * fcf_yield
                target_price = fcf_per_share / historical_avg_yield
            
            return {
                "current_fcf_yield": fcf_yield,
                "historical_fcf_yield": historical_fcf_yield,
                "valuation": valuation,
                "target_price": target_price,
                "weight": self.config["free_cash_flow_yield"]["weight"],
                "description": self.config["free_cash_flow_yield"]["description"]
            }
            
        except Exception as e:
            logger.error(f"計算自由現金流收益率估值失敗: {e}")
            raise
    
    def _calculate_composite_valuation(self, valuation_models: Dict) -> Dict:
        """計算綜合估值"""
        try:
            composite = {
                "weighted_score": 0,
                "valuation": "fair",
                "target_price": 0,
                "confidence": 0.5
            }
            
            weighted_score = 0
            total_weight = 0
            target_prices = []
            
            # 計算加權分數
            for model_name, model_data in valuation_models.items():
                weight = model_data.get("weight", 0)
                valuation = model_data.get("valuation", "fair")
                
                # 將估值轉換為分數
                score = 0
                if valuation == "undervalued":
                    score = 1
                elif valuation == "fair":
                    score = 0
                elif valuation == "overvalued":
                    score = -1
                
                weighted_score += score * weight
                total_weight += weight
                
                # 收集目標價格
                target_price = model_data.get("target_price", 0)
                if target_price > 0:
                    target_prices.append(target_price)
            
            # 計算加權分數
            if total_weight > 0:
                composite["weighted_score"] = weighted_score / total_weight
            
            # 判斷綜合估值
            if composite["weighted_score"] > 0.2:
                composite["valuation"] = "undervalued"
                composite["confidence"] = min(0.9, 0.5 + composite["weighted_score"])
            elif composite["weighted_score"] < -0.2:
                composite["valuation"] = "overvalued"
                composite["confidence"] = min(0.9, 0.5 - composite["weighted_score"])
            else:
                composite["valuation"] = "fair"
                composite["confidence"] = 0.5
            
            # 計算目標價格（使用中位數）
            if target_prices:
                composite["target_price"] = np.median(target_prices)
            
            return composite
            
        except Exception as e:
            logger.error(f"計算綜合估值失敗: {e}")
            raise
    
    def _generate_summary(self, analysis_result: Dict) -> Dict:
        """生成分析摘要"""
        try:
            summary = {
                "overall_valuation": "fair",
                "undervalued_models": [],
                "overvalued_models": [],
                "fair_valued_models": [],
                "recommendation": "hold",
                "upside_potential": 0
            }
            
            # 分析各個模型的估值
            for model_name, model_data in analysis_result["valuation_models"].items():
                valuation = model_data.get("valuation", "fair")
                
                if valuation == "undervalued":
                    summary["undervalued_models"].append(model_name)
                elif valuation == "overvalued":
                    summary["overvalued_models"].append(model_name)
                else:
                    summary["fair_valued_models"].append(model_name)
            
            # 生成總體估值
            composite = analysis_result.get("composite_valuation", {})
            summary["overall_valuation"] = composite.get("valuation", "fair")
            
            # 生成建議
            if summary["overall_valuation"] == "undervalued":
                summary["recommendation"] = "buy"
            elif summary["overall_valuation"] == "overvalued":
                summary["recommendation"] = "sell"
            else:
                summary["recommendation"] = "hold"
            
            # 計算上漲潛力
            current_price = analysis_result.get("current_price", 0)
            target_price = composite.get("target_price", 0)
            
            if current_price > 0 and target_price > 0:
                summary["upside_potential"] = (target_price - current_price) / current_price
            
            return summary
            
        except Exception as e:
            logger.error(f"生成分析摘要失敗: {e}")
            raise