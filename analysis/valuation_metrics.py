"""
台灣股票分析工具 - 估值指標計算模組
自動計算 PE、PB、股利殖利率等估值指標
資料來源：Yahoo Finance（免費）
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from loguru import logger
import yfinance as yf


def convert_numpy_types(obj):
    """轉換 numpy 類型為 Python 原生類型"""
    if isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(v) for v in obj]
    return obj


class ValuationMetrics:
    """估值指標計算類"""

    def __init__(self):
        self.cache = {}  # 簡單快取

    def get_valuation(self, stock_id: str) -> Dict:
        """
        取得完整估值指標

        Args:
            stock_id: 股票代碼 (e.g., "2330.TW")

        Returns:
            完整估值數據（JSON 格式）
        """
        try:
            logger.info(f"取得 {stock_id} 估值指標...")

            # 取得 Yahoo Finance 數據
            ticker = yf.Ticker(stock_id)
            info = ticker.info
            history = ticker.history(period="1y")

            if not info:
                return {"success": False, "error": "無法取得股票資訊"}

            # 取得財務數據
            financials = ticker.financials
            balance_sheet = ticker.balance_sheet

            # 計算估值指標
            valuation = {
                "stock_id": stock_id,
                "timestamp": datetime.now().isoformat(),
                "current_price": info.get("currentPrice", info.get("regularMarketPrice", 0)),

                # 基本估值
                "pe_ratio": self._calculate_pe(info, financials),
                "pb_ratio": self._calculate_pb(info, balance_sheet),
                "dividend_yield": self._calculate_dividend_yield(info),
                "ps_ratio": self._calculate_ps(info),

                # 進階估值
                "ev_ebitda": self._calculate_ev_ebitda(info),
                "peg_ratio": self._calculate_peg(info),
                "free_cash_flow_yield": self._calculate_fcf_yield(info),

                # 歷史估值
                "historical_pe": self._get_historical_pe(stock_id, history, financials),
                "valuation_range": self._calculate_valuation_range(stock_id),

                # 股利資訊
                "dividend_info": self._get_dividend_info(ticker, info),

                # 估值評級
                "valuation_rating": None  # 稍後計算
            }

            # 計算估值評級
            valuation["valuation_rating"] = self._calculate_rating(valuation)

            # 轉換 numpy 類型
            valuation = convert_numpy_types(valuation)

            return {"success": True, "data": valuation}

        except Exception as e:
            logger.error(f"取得估值指標失敗: {e}")
            return {"success": False, "error": str(e)}

    def _calculate_pe(self, info: Dict, financials: pd.DataFrame) -> Dict:
        """計算本益比 (PE Ratio)"""
        try:
            # 目前 PE
            trailing_pe = info.get("trailingPE", 0)
            forward_pe = info.get("forwardPE", 0)

            # 計算歷史平均 PE
            historical_pe = []
            if financials is not None and not financials.empty:
                # 取得過去幾年的 EPS
                for col in financials.columns[:4]:  # 最近 4 季
                    if "Net Income" in financials.index:
                        net_income = financials.loc["Net Income", col]
                        shares = info.get("sharesOutstanding", 1)
                        if shares > 0 and net_income > 0:
                            eps = net_income / shares
                            price = info.get("currentPrice", 0)
                            if eps > 0:
                                historical_pe.append(price / eps)

            avg_pe = np.mean(historical_pe) if historical_pe else trailing_pe

            return {
                "trailing_pe": round(trailing_pe, 2) if trailing_pe else None,
                "forward_pe": round(forward_pe, 2) if forward_pe else None,
                "historical_avg_pe": round(avg_pe, 2) if avg_pe else None,
                "pe_percentile": self._calculate_percentile(trailing_pe, historical_pe),
                "is_undervalued": trailing_pe < avg_pe * 0.8 if trailing_pe and avg_pe else None
            }
        except Exception as e:
            logger.warning(f"計算 PE 失敗: {e}")
            return {"trailing_pe": None, "forward_pe": None}

    def _calculate_pb(self, info: Dict, balance_sheet: pd.DataFrame) -> Dict:
        """計算股價淨值比 (PB Ratio)"""
        try:
            pb_ratio = info.get("priceToBook", 0)
            book_value = info.get("bookValue", 0)

            # 計算歷史 PB
            historical_pb = []
            if balance_sheet is not None and not balance_sheet.empty:
                if "Stockholders Equity" in balance_sheet.index:
                    for col in balance_sheet.columns[:4]:
                        equity = balance_sheet.loc["Stockholders Equity", col]
                        shares = info.get("sharesOutstanding", 1)
                        if shares > 0 and equity > 0:
                            bvps = equity / shares
                            price = info.get("currentPrice", 0)
                            if bvps > 0:
                                historical_pb.append(price / bvps)

            avg_pb = np.mean(historical_pb) if historical_pb else pb_ratio

            return {
                "pb_ratio": round(pb_ratio, 2) if pb_ratio else None,
                "book_value_per_share": round(book_value, 2) if book_value else None,
                "historical_avg_pb": round(avg_pb, 2) if avg_pb else None,
                "pb_percentile": self._calculate_percentile(pb_ratio, historical_pb),
                "is_undervalued": pb_ratio < avg_pb * 0.8 if pb_ratio and avg_pb else None
            }
        except Exception as e:
            logger.warning(f"計算 PB 失敗: {e}")
            return {"pb_ratio": None, "book_value_per_share": None}

    def _calculate_dividend_yield(self, info: Dict) -> Dict:
        """計算股利殖利率"""
        try:
            dividend_yield = info.get("dividendYield", 0)
            dividend_rate = info.get("dividendRate", 0)
            payout_ratio = info.get("payoutRatio", 0)

            return {
                "dividend_yield": round(dividend_yield * 100, 2) if dividend_yield else None,
                "dividend_rate": round(dividend_rate, 2) if dividend_rate else None,
                "payout_ratio": round(payout_ratio * 100, 2) if payout_ratio else None,
                "is_high_yield": dividend_yield > 0.05 if dividend_yield else None  # > 5%
            }
        except Exception as e:
            logger.warning(f"計算股利殖利率失敗: {e}")
            return {"dividend_yield": None}

    def _calculate_ps(self, info: Dict) -> Dict:
        """計算股價營收比 (PS Ratio)"""
        try:
            ps_ratio = info.get("priceToSalesTrailing12Months", 0)
            return {
                "ps_ratio": round(ps_ratio, 2) if ps_ratio else None
            }
        except Exception:
            return {"ps_ratio": None}

    def _calculate_ev_ebitda(self, info: Dict) -> Dict:
        """計算企業價值倍數 (EV/EBITDA)"""
        try:
            ev_ebitda = info.get("enterpriseToEbitda", 0)
            ev_revenue = info.get("enterpriseToRevenue", 0)

            return {
                "ev_ebitda": round(ev_ebitda, 2) if ev_ebitda else None,
                "ev_revenue": round(ev_revenue, 2) if ev_revenue else None
            }
        except Exception:
            return {"ev_ebitda": None}

    def _calculate_peg(self, info: Dict) -> Dict:
        """計算本益成長比 (PEG Ratio)"""
        try:
            peg_ratio = info.get("pegRatio", 0)
            earnings_growth = info.get("earningsGrowth", 0)

            return {
                "peg_ratio": round(peg_ratio, 2) if peg_ratio else None,
                "earnings_growth": round(earnings_growth * 100, 2) if earnings_growth else None,
                "is_undervalued": peg_ratio < 1 if peg_ratio else None
            }
        except Exception:
            return {"peg_ratio": None}

    def _calculate_fcf_yield(self, info: Dict) -> Dict:
        """計算自由現金流收益率"""
        try:
            fcf = info.get("freeCashflow", 0)
            market_cap = info.get("marketCap", 0)
            price = info.get("currentPrice", 0)
            shares = info.get("sharesOutstanding", 1)

            if market_cap > 0 and fcf > 0:
                fcf_yield = fcf / market_cap
                fcf_per_share = fcf / shares if shares > 0 else 0

                return {
                    "fcf_yield": round(fcf_yield * 100, 2),
                    "fcf_per_share": round(fcf_per_share, 2),
                    "is_high_yield": fcf_yield > 0.05  # > 5%
                }
            return {"fcf_yield": None}
        except Exception:
            return {"fcf_yield": None}

    def _get_historical_pe(self, stock_id: str, history: pd.DataFrame, financials: pd.DataFrame) -> List[Dict]:
        """取得歷史 PE 趨勢"""
        try:
            if history.empty or financials.empty:
                return []

            historical_pe = []
            # 簡化：用過去一年的季度數據
            for i in range(min(4, len(financials.columns))):
                quarter = financials.columns[i]
                if "Net Income" in financials.index:
                    net_income = financials.loc["Net Income", quarter]
                    shares = 100000000  # 假設 1 億股

                    if net_income > 0:
                        eps = net_income / shares
                        # 找該季度附近的價格
                        quarter_date = quarter
                        nearby_prices = history[
                            (history.index >= quarter_date - timedelta(days=30)) &
                            (history.index <= quarter_date + timedelta(days=30))
                        ]

                        if not nearby_prices.empty:
                            avg_price = nearby_prices["Close"].mean()
                            pe = avg_price / eps

                            historical_pe.append({
                                "date": str(quarter.date()) if hasattr(quarter, 'date') else str(quarter),
                                "pe": round(pe, 2),
                                "eps": round(eps, 2)
                            })

            return historical_pe

        except Exception as e:
            logger.warning(f"取得歷史 PE 失敗: {e}")
            return []

    def _calculate_valuation_range(self, stock_id: str) -> Dict:
        """計算估值範圍"""
        try:
            ticker = yf.Ticker(stock_id)
            info = ticker.info

            # 取得 52 週高低
            high_52w = info.get("fiftyTwoWeekHigh", 0)
            low_52w = info.get("fiftyTwoWeekLow", 0)
            current = info.get("currentPrice", 0)

            if high_52w > 0 and low_52w > 0 and current > 0:
                # 計算在 52 週範圍的位置
                position = (current - low_52w) / (high_52w - low_52w)

                return {
                    "high_52w": round(high_52w, 2),
                    "low_52w": round(low_52w, 2),
                    "current": round(current, 2),
                    "position_percent": round(position * 100, 1),
                    "near_high": position > 0.8,
                    "near_low": position < 0.2
                }
            return {}
        except Exception:
            return {}

    def _get_dividend_info(self, ticker: yf.Ticker, info: Dict) -> Dict:
        """取得股利資訊"""
        try:
            dividends = ticker.dividends

            dividend_info = {
                "current_yield": info.get("dividendYield", 0),
                "annual_dividend": info.get("dividendRate", 0),
                "payout_ratio": info.get("payoutRatio", 0),
                "ex_dividend_date": str(info.get("exDividendDate", "")),
                "dividend_history": []
            }

            # 取得過去 5 年股利歷史
            if not dividends.empty:
                yearly_dividends = dividends.resample('Y').sum()
                for date, amount in yearly_dividends.items():
                    dividend_info["dividend_history"].append({
                        "year": date.year,
                        "amount": round(float(amount), 2)
                    })

                # 計算平均股利
                if len(yearly_dividends) > 0:
                    dividend_info["avg_annual_dividend"] = round(float(yearly_dividends.mean()), 2)
                    dividend_info["dividend_growth"] = self._calculate_dividend_growth(yearly_dividends)

            return dividend_info

        except Exception as e:
            logger.warning(f"取得股利資訊失敗: {e}")
            return {}

    def _calculate_dividend_growth(self, yearly_dividends: pd.Series) -> float:
        """計算股利成長率"""
        try:
            if len(yearly_dividends) < 2:
                return 0

            # 計算年化成長率
            first = float(yearly_dividends.iloc[0])
            last = float(yearly_dividends.iloc[-1])
            years = len(yearly_dividends) - 1

            if first > 0 and years > 0:
                growth = ((last / first) ** (1 / years) - 1) * 100
                return round(growth, 2)
            return 0
        except Exception:
            return 0

    def _calculate_percentile(self, current: float, historical: List[float]) -> float:
        """計算目前值在歷史數據中的百分位"""
        try:
            if not historical or not current:
                return None

            historical = [x for x in historical if x > 0]
            if not historical:
                return None

            count_below = sum(1 for x in historical if x < current)
            percentile = (count_below / len(historical)) * 100
            return round(percentile, 1)
        except Exception:
            return None

    def _calculate_rating(self, valuation: Dict) -> Dict:
        """計算估值評級"""
        try:
            score = 0
            factors = []

            # PE 評分
            pe = valuation.get("pe_ratio", {}).get("trailing_pe")
            if pe:
                if pe < 15:
                    score += 2
                    factors.append("PE 偏低（便宜）")
                elif pe > 30:
                    score -= 2
                    factors.append("PE 偏高（昂貴）")
                else:
                    factors.append("PE 適中")

            # PB 評分
            pb = valuation.get("pb_ratio", {}).get("pb_ratio")
            if pb:
                if pb < 1.5:
                    score += 2
                    factors.append("PB 偏低（便宜）")
                elif pb > 5:
                    score -= 2
                    factors.append("PB 偏高（昂貴）")

            # 股利殖利率評分
            div_yield = valuation.get("dividend_yield", {}).get("dividend_yield")
            if div_yield:
                if div_yield > 5:
                    score += 2
                    factors.append("高股利殖利率")
                elif div_yield > 3:
                    score += 1
                    factors.append("中等股利殖利率")

            # PEG 評分
            peg = valuation.get("peg_ratio", {}).get("peg_ratio")
            if peg:
                if peg < 1:
                    score += 2
                    factors.append("PEG < 1（成長股便宜）")
                elif peg > 2:
                    score -= 1
                    factors.append("PEG > 2（成長股昂貴）")

            # 總評
            if score >= 4:
                rating = "undervalued"
                label = "低估"
            elif score >= 2:
                rating = "fair_value"
                label = "合理"
            elif score >= 0:
                rating = "neutral"
                label = "中性"
            else:
                rating = "overvalued"
                label = "高估"

            return {
                "rating": rating,
                "label": label,
                "score": score,
                "factors": factors
            }

        except Exception as e:
            logger.warning(f"計算估值評級失敗: {e}")
            return {"rating": "unknown", "label": "未知"}


# 全局實例
_valuation = None


def get_valuation_metrics() -> ValuationMetrics:
    """取得 ValuationMetrics 單例"""
    global _valuation
    if _valuation is None:
        _valuation = ValuationMetrics()
    return _valuation
