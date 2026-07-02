"""
台灣股票分析工具 - 除權息資料抓取模組
從 TWSE 取得完整除權息資料，計算填息率
資料來源：TWSE OpenAPI（免費）
"""
import requests
import pandas as pd
import numpy as np
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from loguru import logger


class DividendFetcher:
    """除權息資料抓取類"""

    # TWSE API
    TWSE_BASE = "https://openapi.twse.com.tw/v1"
    TWSE_DIVIDEND_URL = f"{TWSE_BASE}/exchangeReport/TWT49U"
    TWSE_EXRIGHT_URL = f"{TWSE_BASE}/exchangeReport/TWT53U"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        self._last_request_time = 0
        self.REQUEST_INTERVAL = 0.5

    def _throttle(self):
        """請求節流"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.REQUEST_INTERVAL:
            time.sleep(self.REQUEST_INTERVAL - elapsed)
        self._last_request_time = time.time()

    def get_dividend_data(self, stock_id: str, years: int = 5) -> Dict:
        """
        取得除權息資料

        Args:
            stock_id: 股票代碼 (e.g., "2330")
            years: 取得幾年資料

        Returns:
            除權息資料（JSON 格式）
        """
        try:
            logger.info(f"取得 {stock_id} 除權息資料...")

            # 取得除權息預報
            dividend_schedule = self._get_dividend_schedule(stock_id)

            # 取得歷史除權息
            historical_dividend = self._get_historical_dividend(stock_id, years)

            # 計算填息率
            fill_rate = self._calculate_fill_rate(stock_id, historical_dividend)

            result = {
                "success": True,
                "data": {
                    "stock_id": stock_id,
                    "timestamp": datetime.now().isoformat(),

                    # 除權息預報
                    "upcoming": dividend_schedule,

                    # 歷史除權息
                    "history": historical_dividend,

                    # 填息分析
                    "fill_analysis": fill_rate,

                    # 統計資料
                    "statistics": self._calculate_statistics(historical_dividend)
                }
            }

            return result

        except Exception as e:
            logger.error(f"取得除權息資料失敗: {e}")
            return {"success": False, "error": str(e)}

    def _get_dividend_schedule(self, stock_id: str) -> List[Dict]:
        """取得除權息預報"""
        try:
            self._throttle()

            # TWSE 除權息預報 API
            response = self.session.get(self.TWSE_DIVIDEND_URL, timeout=15)

            if response.status_code != 200:
                logger.warning(f"TWSE 除權息預報請求失敗: {response.status_code}")
                return self._get_mock_schedule(stock_id)

            try:
                data = response.json()
                if not data:
                    return self._get_mock_schedule(stock_id)

                # 篩選目標股票
                target_data = []
                for item in data:
                    code = item.get("SecuritiesCompanyCode", "")
                    if code == stock_id:
                        target_data.append({
                            "stock_id": code,
                            "name": item.get("CompanyName", ""),
                            "ex_dividend_date": item.get("ExDividendDate", ""),
                            "ex_right_date": item.get("ExRightsDate", ""),
                            "cash_dividend": float(item.get("CashDividend", 0)),
                            "stock_dividend": float(item.get("StockDividend", 0)),
                            "announcement_date": item.get("AnnouncementDate", ""),
                            "record_date": item.get("RecordDate", ""),
                            "payment_date": item.get("PaymentDate", "")
                        })

                return target_data

            except json.JSONDecodeError:
                logger.warning("TWSE 除權息預報回傳非 JSON")
                return self._get_mock_schedule(stock_id)

        except Exception as e:
            logger.error(f"取得除權息預報失敗: {e}")
            return self._get_mock_schedule(stock_id)

    def _get_historical_dividend(self, stock_id: str, years: int) -> List[Dict]:
        """取得歷史除權息資料"""
        try:
            self._throttle()

            # TWSE 除權息歷史 API
            response = self.session.get(self.TWSE_EXRIGHT_URL, timeout=15)

            if response.status_code != 200:
                logger.warning(f"TWSE 除權息歷史請求失敗: {response.status_code}")
                return self._get_mock_history(stock_id, years)

            try:
                data = response.json()
                if not data:
                    return self._get_mock_history(stock_id, years)

                # 篩選目標股票
                target_data = []
                cutoff_year = datetime.now().year - years

                for item in data:
                    code = item.get("SecuritiesCompanyCode", "")
                    if code == stock_id:
                        ex_date = item.get("ExDate", "")
                        if ex_date:
                            try:
                                year = int(ex_date.split("/")[0]) + 1911  # 民國轉西元
                                if year >= cutoff_year:
                                    target_data.append({
                                        "stock_id": code,
                                        "ex_date": ex_date,
                                        "year": year,
                                        "cash_dividend": float(item.get("CashDividend", 0)),
                                        "stock_dividend": float(item.get("StockDividend", 0)),
                                        "total_dividend": float(item.get("TotalDividend", 0)),
                                        "reference_price": float(item.get("ReferencePrice", 0))
                                    })
                            except (ValueError, IndexError):
                                continue

                # 按年份排序
                target_data.sort(key=lambda x: x.get("year", 0), reverse=True)
                return target_data

            except json.JSONDecodeError:
                return self._get_mock_history(stock_id, years)

        except Exception as e:
            logger.error(f"取得歷史除權息失敗: {e}")
            return self._get_mock_history(stock_id, years)

    def _calculate_fill_rate(self, stock_id: str, historical_dividend: List[Dict]) -> Dict:
        """計算填息率"""
        try:
            import yfinance as yf

            if not historical_dividend:
                return {"error": "無歷史資料"}

            fill_results = []
            total_fill_days = 0
            filled_count = 0

            for div in historical_dividend[:5]:  # 最近 5 次
                ex_date_str = div.get("ex_date", "")
                cash_div = div.get("cash_dividend", 0)
                ref_price = div.get("reference_price", 0)

                if not ex_date_str or cash_div <= 0:
                    continue

                # 轉換日期
                try:
                    parts = ex_date_str.split("/")
                    ex_date = date(int(parts[0]) + 1911, int(parts[1]), int(parts[2]))
                except (ValueError, IndexError):
                    continue

                # 取得除息前後的價格
                try:
                    ticker = yf.Ticker(stock_id)
                    start = ex_date - timedelta(days=30)
                    end = ex_date + timedelta(days=90)
                    history = ticker.history(start=start, end=end)

                    if history.empty:
                        continue

                    # 除息前收盤價
                    pre_ex = history[history.index.date < ex_date]
                    if pre_ex.empty:
                        continue
                    pre_price = pre_ex.iloc[-1]["Close"]

                    # 除息後價格
                    post_ex = history[history.index.date >= ex_date]
                    if post_ex.empty:
                        continue

                    # 計算填息
                    target_price = pre_price - cash_div
                    filled = False
                    fill_days = None

                    for i, (idx, row) in enumerate(post_ex.iterrows()):
                        if row["Close"] >= target_price:
                            filled = True
                            fill_days = i + 1
                            break

                    fill_results.append({
                        "ex_date": ex_date_str,
                        "cash_dividend": cash_div,
                        "pre_ex_price": round(pre_price, 2),
                        "target_price": round(target_price, 2),
                        "filled": filled,
                        "fill_days": fill_days,
                        "fill_status": "已填息" if filled else "未填息"
                    })

                    if filled:
                        filled_count += 1
                        total_fill_days += fill_days

                except Exception as e:
                    logger.warning(f"計算填息率失敗: {e}")
                    continue

            # 統計
            total = len(fill_results)
            fill_rate = (filled_count / total * 100) if total > 0 else 0
            avg_fill_days = (total_fill_days / filled_count) if filled_count > 0 else None

            return {
                "fill_results": fill_results,
                "total_dividends": total,
                "filled_count": filled_count,
                "fill_rate": round(fill_rate, 1),
                "avg_fill_days": avg_fill_days,
                "fill_rating": self._get_fill_rating(fill_rate, avg_fill_days)
            }

        except Exception as e:
            logger.error(f"計算填息率失敗: {e}")
            return {"error": str(e)}

    def _get_fill_rating(self, fill_rate: float, avg_fill_days: Optional[float]) -> str:
        """填息評級"""
        if fill_rate >= 80 and avg_fill_days and avg_fill_days <= 30:
            return "excellent"  # 優秀
        elif fill_rate >= 60:
            return "good"  # 良好
        elif fill_rate >= 40:
            return "average"  # 普通
        else:
            return "poor"  # 較差

    def _calculate_statistics(self, historical_dividend: List[Dict]) -> Dict:
        """計算統計資料"""
        if not historical_dividend:
            return {}

        cash_dividends = [d.get("cash_dividend", 0) for d in historical_dividend if d.get("cash_dividend", 0) > 0]

        if not cash_dividends:
            return {}

        return {
            "years_count": len(historical_dividend),
            "avg_cash_dividend": round(np.mean(cash_dividends), 2),
            "max_cash_dividend": round(max(cash_dividends), 2),
            "min_cash_dividend": round(min(cash_dividends), 2),
            "dividend_stability": self._calculate_stability(cash_dividends),
            "consecutive_years": self._count_consecutive_years(historical_dividend),
            "dividend_trend": self._calculate_trend(cash_dividends)
        }

    def _calculate_stability(self, dividends: List[float]) -> str:
        """計算股利穩定性"""
        if len(dividends) < 2:
            return "unknown"

        cv = np.std(dividends) / np.mean(dividends)  # 變異係數

        if cv < 0.2:
            return "very_stable"  # 非常穩定
        elif cv < 0.4:
            return "stable"  # 穩定
        elif cv < 0.6:
            return "moderate"  # 中等
        else:
            return "volatile"  # 波動

    def _count_consecutive_years(self, historical_dividend: List[Dict]) -> int:
        """計算連續發放年數"""
        if not historical_dividend:
            return 0

        # 按年份排序
        sorted_div = sorted(historical_dividend, key=lambda x: x.get("year", 0), reverse=True)

        consecutive = 0
        current_year = datetime.now().year

        for div in sorted_div:
            year = div.get("year", 0)
            cash = div.get("cash_dividend", 0)

            if year == current_year and cash > 0:
                consecutive += 1
                current_year -= 1
            elif year < current_year:
                break

        return consecutive

    def _calculate_trend(self, dividends: List[float]) -> str:
        """計算股利趨勢"""
        if len(dividends) < 2:
            return "unknown"

        # 簡單線性回歸
        x = np.arange(len(dividends))
        slope = np.polyfit(x, dividends, 1)[0]

        if slope > 0.5:
            return "increasing"  # 上升
        elif slope < -0.5:
            return "decreasing"  # 下降
        else:
            return "stable"  # 穩定

    def _get_mock_schedule(self, stock_id: str) -> List[Dict]:
        """模擬除權息預報"""
        return [{
            "stock_id": stock_id,
            "name": "模擬資料",
            "ex_dividend_date": "2024/06/15",
            "cash_dividend": 0,
            "stock_dividend": 0,
            "source": "mock"
        }]

    def _get_mock_history(self, stock_id: str, years: int) -> List[Dict]:
        """模擬歷史除權息"""
        return [{
            "stock_id": stock_id,
            "ex_date": f"{datetime.now().year - 1}/06/15",
            "year": datetime.now().year - 1,
            "cash_dividend": 0,
            "stock_dividend": 0,
            "source": "mock"
        }]


# 全局實例
_dividend_fetcher = None


def get_dividend_fetcher() -> DividendFetcher:
    """取得 DividendFetcher 單例"""
    global _dividend_fetcher
    if _dividend_fetcher is None:
        _dividend_fetcher = DividendFetcher()
    return _dividend_fetcher
