"""
台灣股票分析工具 - 基本面分析模組
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from loguru import logger

# 導入數據處理模組
from data.data_fetcher import DataFetcher


class FundamentalAnalysis:
    """基本面分析類"""
    
    def __init__(self):
        self.data_fetcher = DataFetcher()
    
    async def analyze(self, stock_id: str) -> Dict:
        """執行基本面分析"""
        try:
            # 獲取股票基本資訊
            stock_info = await self.data_fetcher.get_stock_info(stock_id)
            
            # 獲取財務數據
            financial_data = await self.data_fetcher.get_financial_data(stock_id)
            
            # 獲取即時價格數據
            realtime_data = await self.data_fetcher.get_realtime_price(stock_id)
            
            analysis_result = {
                "stock_id": stock_id,
                "timestamp": pd.Timestamp.now().isoformat(),
                "company_info": stock_info,
                "financial_analysis": {},
                "profitability": {},
                "growth": {},
                "stability": {},
                "valuation_metrics": {},
                "summary": {}
            }
            
            # 計算財務比率
            analysis_result["financial_analysis"] = self._calculate_financial_ratios(financial_data, realtime_data)
            
            # 分析獲利能力
            analysis_result["profitability"] = self._analyze_profitability(financial_data)
            
            # 分析成長性
            analysis_result["growth"] = self._analyze_growth(financial_data)
            
            # 分析穩定性
            analysis_result["stability"] = self._analyze_stability(financial_data)
            
            # 計算估值指標
            analysis_result["valuation_metrics"] = self._calculate_valuation_metrics(financial_data, realtime_data)
            
            # 生成分析摘要
            analysis_result["summary"] = self._generate_summary(analysis_result)
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"基本面分析失敗: {e}")
            raise
    
    def _calculate_financial_ratios(self, financial_data: Dict, realtime_data: Dict) -> Dict:
        """計算財務比率"""
        try:
            ratios = {}
            
            # 獲取最新的財務數據
            if financial_data.get("income_statement"):
                latest_year = max(financial_data["income_statement"].keys())
                income_data = financial_data["income_statement"][latest_year]
                
                # 計算毛利率
                if "Gross Profit" in income_data and "Total Revenue" in income_data:
                    ratios["gross_margin"] = income_data["Gross Profit"] / income_data["Total Revenue"]
                
                # 計算營業利益率
                if "Operating Income" in income_data and "Total Revenue" in income_data:
                    ratios["operating_margin"] = income_data["Operating Income"] / income_data["Total Revenue"]
                
                # 計算淨利率
                if "Net Income" in income_data and "Total Revenue" in income_data:
                    ratios["net_margin"] = income_data["Net Income"] / income_data["Total Revenue"]
            
            # 獲取資產負債表數據
            if financial_data.get("balance_sheet"):
                latest_year = max(financial_data["balance_sheet"].keys())
                balance_data = financial_data["balance_sheet"][latest_year]
                
                # 計算負債比率
                if "Total Debt" in balance_data and "Total Assets" in balance_data:
                    ratios["debt_ratio"] = balance_data["Total Debt"] / balance_data["Total Assets"]
                
                # 計算流動比率
                if "Current Assets" in balance_data and "Current Liabilities" in balance_data:
                    ratios["current_ratio"] = balance_data["Current Assets"] / balance_data["Current Liabilities"]
                
                # 計算速動比率
                if "Current Assets" in balance_data and "Inventory" in balance_data and "Current Liabilities" in balance_data:
                    ratios["quick_ratio"] = (balance_data["Current Assets"] - balance_data["Inventory"]) / balance_data["Current Liabilities"]
            
            # 獲取現金流量表數據
            if financial_data.get("cash_flow"):
                latest_year = max(financial_data["cash_flow"].keys())
                cashflow_data = financial_data["cash_flow"][latest_year]
                
                # 計算營業現金流對淨利比率
                if "Operating Cash Flow" in cashflow_data and "Net Income" in cashflow_data:
                    ratios["ocf_to_net_income"] = cashflow_data["Operating Cash Flow"] / cashflow_data["Net Income"]
            
            # 計算估值比率
            ratios["pe_ratio"] = realtime_data.get("pe_ratio", 0)
            ratios["dividend_yield"] = realtime_data.get("dividend_yield", 0)
            
            return ratios
            
        except Exception as e:
            logger.error(f"計算財務比率失敗: {e}")
            raise
    
    def _analyze_profitability(self, financial_data: Dict) -> Dict:
        """分析獲利能力"""
        try:
            profitability = {
                "metrics": {},
                "trend": "stable",
                "rating": "average"
            }
            
            # 獲取多年財務數據
            if financial_data.get("income_statement"):
                years = sorted(financial_data["income_statement"].keys())
                
                gross_margins = []
                operating_margins = []
                net_margins = []
                
                for year in years:
                    income_data = financial_data["income_statement"][year]
                    
                    # 計算毛利率
                    if "Gross Profit" in income_data and "Total Revenue" in income_data:
                        gross_margins.append(income_data["Gross Profit"] / income_data["Total Revenue"])
                    
                    # 計算營業利益率
                    if "Operating Income" in income_data and "Total Revenue" in income_data:
                        operating_margins.append(income_data["Operating Income"] / income_data["Total Revenue"])
                    
                    # 計算淨利率
                    if "Net Income" in income_data and "Total Revenue" in income_data:
                        net_margins.append(income_data["Net Income"] / income_data["Total Revenue"])
                
                # 計算平均值和趨勢
                if gross_margins:
                    profitability["metrics"]["gross_margin"] = {
                        "values": gross_margins,
                        "average": np.mean(gross_margins),
                        "trend": "up" if len(gross_margins) > 1 and gross_margins[-1] > gross_margins[-2] else "down"
                    }
                
                if operating_margins:
                    profitability["metrics"]["operating_margin"] = {
                        "values": operating_margins,
                        "average": np.mean(operating_margins),
                        "trend": "up" if len(operating_margins) > 1 and operating_margins[-1] > operating_margins[-2] else "down"
                    }
                
                if net_margins:
                    profitability["metrics"]["net_margin"] = {
                        "values": net_margins,
                        "average": np.mean(net_margins),
                        "trend": "up" if len(net_margins) > 1 and net_margins[-1] > net_margins[-2] else "down"
                    }
                
                # 評估獲利能力
                if net_margins:
                    avg_net_margin = np.mean(net_margins)
                    if avg_net_margin > 0.15:
                        profitability["rating"] = "excellent"
                    elif avg_net_margin > 0.10:
                        profitability["rating"] = "good"
                    elif avg_net_margin > 0.05:
                        profitability["rating"] = "average"
                    else:
                        profitability["rating"] = "poor"
            
            return profitability
            
        except Exception as e:
            logger.error(f"分析獲利能力失敗: {e}")
            raise
    
    def _analyze_growth(self, financial_data: Dict) -> Dict:
        """分析成長性"""
        try:
            growth = {
                "metrics": {},
                "trend": "stable",
                "rating": "average"
            }
            
            # 獲取多年財務數據
            if financial_data.get("income_statement"):
                years = sorted(financial_data["income_statement"].keys())
                
                revenue_growth = []
                net_income_growth = []
                
                for i in range(1, len(years)):
                    current_year = years[i]
                    previous_year = years[i-1]
                    
                    current_data = financial_data["income_statement"][current_year]
                    previous_data = financial_data["income_statement"][previous_year]
                    
                    # 計算營收成長率
                    if "Total Revenue" in current_data and "Total Revenue" in previous_data:
                        if previous_data["Total Revenue"] != 0:
                            growth_rate = (current_data["Total Revenue"] - previous_data["Total Revenue"]) / previous_data["Total Revenue"]
                            revenue_growth.append(growth_rate)
                    
                    # 計算淨利成長率
                    if "Net Income" in current_data and "Net Income" in previous_data:
                        if previous_data["Net Income"] != 0:
                            growth_rate = (current_data["Net Income"] - previous_data["Net Income"]) / previous_data["Net Income"]
                            net_income_growth.append(growth_rate)
                
                # 計算平均成長率和趨勢
                if revenue_growth:
                    growth["metrics"]["revenue_growth"] = {
                        "values": revenue_growth,
                        "average": np.mean(revenue_growth),
                        "trend": "up" if len(revenue_growth) > 1 and revenue_growth[-1] > revenue_growth[-2] else "down"
                    }
                
                if net_income_growth:
                    growth["metrics"]["net_income_growth"] = {
                        "values": net_income_growth,
                        "average": np.mean(net_income_growth),
                        "trend": "up" if len(net_income_growth) > 1 and net_income_growth[-1] > net_income_growth[-2] else "down"
                    }
                
                # 評估成長性
                if revenue_growth:
                    avg_growth = np.mean(revenue_growth)
                    if avg_growth > 0.20:
                        growth["rating"] = "excellent"
                    elif avg_growth > 0.10:
                        growth["rating"] = "good"
                    elif avg_growth > 0.05:
                        growth["rating"] = "average"
                    else:
                        growth["rating"] = "poor"
            
            return growth
            
        except Exception as e:
            logger.error(f"分析成長性失敗: {e}")
            raise
    
    def _analyze_stability(self, financial_data: Dict) -> Dict:
        """分析穩定性"""
        try:
            stability = {
                "metrics": {},
                "trend": "stable",
                "rating": "average"
            }
            
            # 獲取多年財務數據
            if financial_data.get("income_statement"):
                years = sorted(financial_data["income_statement"].keys())
                
                revenue_volatility = []
                net_income_volatility = []
                
                for i in range(1, len(years)):
                    current_year = years[i]
                    previous_year = years[i-1]
                    
                    current_data = financial_data["income_statement"][current_year]
                    previous_data = financial_data["income_statement"][previous_year]
                    
                    # 計算營收波動性
                    if "Total Revenue" in current_data and "Total Revenue" in previous_data:
                        if previous_data["Total Revenue"] != 0:
                            volatility = abs((current_data["Total Revenue"] - previous_data["Total Revenue"]) / previous_data["Total Revenue"])
                            revenue_volatility.append(volatility)
                    
                    # 計算淨利波動性
                    if "Net Income" in current_data and "Net Income" in previous_data:
                        if previous_data["Net Income"] != 0:
                            volatility = abs((current_data["Net Income"] - previous_data["Net Income"]) / previous_data["Net Income"])
                            net_income_volatility.append(volatility)
                
                # 計算平均波動性
                if revenue_volatility:
                    stability["metrics"]["revenue_volatility"] = {
                        "values": revenue_volatility,
                        "average": np.mean(revenue_volatility),
                        "trend": "up" if len(revenue_volatility) > 1 and revenue_volatility[-1] > revenue_volatility[-2] else "down"
                    }
                
                if net_income_volatility:
                    stability["metrics"]["net_income_volatility"] = {
                        "values": net_income_volatility,
                        "average": np.mean(net_income_volatility),
                        "trend": "up" if len(net_income_volatility) > 1 and net_income_volatility[-1] > net_income_volatility[-2] else "down"
                    }
                
                # 評估穩定性
                if revenue_volatility:
                    avg_volatility = np.mean(revenue_volatility)
                    if avg_volatility < 0.10:
                        stability["rating"] = "excellent"
                    elif avg_volatility < 0.20:
                        stability["rating"] = "good"
                    elif avg_volatility < 0.30:
                        stability["rating"] = "average"
                    else:
                        stability["rating"] = "poor"
            
            return stability
            
        except Exception as e:
            logger.error(f"分析穩定性失敗: {e}")
            raise
    
    def _calculate_valuation_metrics(self, financial_data: Dict, realtime_data: Dict) -> Dict:
        """計算估值指標"""
        try:
            valuation = {
                "pe_ratio": realtime_data.get("pe_ratio", 0),
                "pb_ratio": 0,
                "dividend_yield": realtime_data.get("dividend_yield", 0),
                "ev_ebitda": 0,
                "free_cash_flow_yield": 0,
                "peg_ratio": 0
            }
            
            # 計算PB比率（需要淨資產數據）
            if financial_data.get("balance_sheet"):
                latest_year = max(financial_data["balance_sheet"].keys())
                balance_data = financial_data["balance_sheet"][latest_year]
                
                if "Stockholders Equity" in balance_data and balance_data["Stockholders Equity"] != 0:
                    # 假設股數為1億股（實際應該從資料獲取）
                    shares_outstanding = 100000000
                    book_value_per_share = balance_data["Stockholders Equity"] / shares_outstanding
                    
                    if book_value_per_share > 0:
                        current_price = realtime_data.get("price", 0)
                        valuation["pb_ratio"] = current_price / book_value_per_share
            
            # 計算EV/EBITDA（需要更多數據）
            # 這裡需要企業價值和EBITDA數據，暫時跳過
            
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
                        valuation["free_cash_flow_yield"] = fcf_per_share / current_price
            
            # 計算PEG比率
            if valuation["pe_ratio"] > 0:
                # 這裡需要成長率數據，暫時使用假設值
                assumed_growth_rate = 0.10  # 10%
                valuation["peg_ratio"] = valuation["pe_ratio"] / (assumed_growth_rate * 100)
            
            return valuation
            
        except Exception as e:
            logger.error(f"計算估值指標失敗: {e}")
            raise
    
    def _generate_summary(self, analysis_result: Dict) -> Dict:
        """生成分析摘要"""
        try:
            summary = {
                "overall_rating": "neutral",
                "strengths": [],
                "weaknesses": [],
                "recommendation": "hold"
            }
            
            strengths = []
            weaknesses = []
            
            # 分析獲利能力
            profitability = analysis_result.get("profitability", {})
            if profitability.get("rating") == "excellent":
                strengths.append("獲利能力優秀")
            elif profitability.get("rating") == "poor":
                weaknesses.append("獲利能力較弱")
            
            # 分析成長性
            growth = analysis_result.get("growth", {})
            if growth.get("rating") == "excellent":
                strengths.append("成長性優秀")
            elif growth.get("rating") == "poor":
                weaknesses.append("成長性較弱")
            
            # 分析穩定性
            stability = analysis_result.get("stability", {})
            if stability.get("rating") == "excellent":
                strengths.append("財務穩定性高")
            elif stability.get("rating") == "poor":
                weaknesses.append("財務穩定性較低")
            
            # 分析估值
            valuation = analysis_result.get("valuation_metrics", {})
            pe_ratio = valuation.get("pe_ratio", 0)
            dividend_yield = valuation.get("dividend_yield", 0)
            
            if pe_ratio > 0 and pe_ratio < 15:
                strengths.append("本益比偏低，估值合理")
            elif pe_ratio > 30:
                weaknesses.append("本益比偏高，估值較高")
            
            if dividend_yield > 0.05:
                strengths.append("股利殖利率高")
            
            summary["strengths"] = strengths
            summary["weaknesses"] = weaknesses
            
            # 生成總體評級
            if len(strengths) > len(weaknesses):
                summary["overall_rating"] = "positive"
                summary["recommendation"] = "buy"
            elif len(weaknesses) > len(strengths):
                summary["overall_rating"] = "negative"
                summary["recommendation"] = "sell"
            else:
                summary["overall_rating"] = "neutral"
                summary["recommendation"] = "hold"
            
            return summary
            
        except Exception as e:
            logger.error(f"生成分析摘要失敗: {e}")
            raise