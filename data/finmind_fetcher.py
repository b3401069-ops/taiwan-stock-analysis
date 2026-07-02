"""
台灣股票分析工具 - FinMind API 資料抓取
整合 FinMind 作為額外資料來源
"""

import time
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from loguru import logger


class FinMindFetcher:
    """FinMind API 資料抓取器"""

    def __init__(self, api_token: str = ""):
        """
        初始化 FinMind 抓取器

        Args:
            api_token: FinMind API Token（免費申請）
        """
        self.api_url = "https://api.finmindtrade.com/api/v4/data"
        self.api_token = api_token
        self.session = requests.Session()

        # 設定 headers
        self.session.headers.update({"Content-Type": "application/json"})

    def _make_request(
        self,
        dataset: str,
        data_id: str,
        start_date: str = "",
        end_date: str = "",
        extra_params: Dict = None,
    ) -> Dict:
        """
        發送 API 請求

        Args:
            dataset: 資料集名稱
            data_id: 股票代碼
            start_date: 開始日期
            end_date: 結束日期
            extra_params: 額外參數

        Returns:
            API 回應
        """
        try:
            params = {
                "dataset": dataset,
                "data_id": data_id,
            }

            if start_date:
                params["start_date"] = start_date
            if end_date:
                params["end_date"] = end_date

            if extra_params:
                params.update(extra_params)

            # 加入 API Token
            if self.api_token:
                params["token"] = self.api_token

            response = self.session.get(self.api_url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            if data.get("status") == 200:
                return {"success": True, "data": data.get("data", [])}
            else:
                return {"success": False, "error": data.get("msg", "Unknown error")}

        except requests.exceptions.RequestException as e:
            logger.error(f"FinMind API 請求失敗: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"FinMind 資料處理失敗: {e}")
            return {"success": False, "error": str(e)}

    def get_stock_price(
        self, stock_id: str, start_date: str = "", end_date: str = ""
    ) -> Dict:
        """
        取得股票日K線資料

        Args:
            stock_id: 股票代碼
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)

        Returns:
            日K線資料
        """
        # 預設最近 1 年
        if not start_date:
            start_date = (date.today() - timedelta(days=365)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = date.today().strftime("%Y-%m-%d")

        result = self._make_request("TaiwanStockPrice", stock_id, start_date, end_date)

        if result.get("success"):
            df = pd.DataFrame(result["data"])
            if not df.empty:
                # 轉換欄位名稱
                df = df.rename(
                    columns={
                        "Trading_Volume": "volume",
                        "close": "Close",
                        "max": "High",
                        "min": "Low",
                        "open": "Open",
                        "spread": "Spread",
                    }
                )

                # 轉換日期格式
                df["date"] = pd.to_datetime(df["date"])
                df = df.sort_values("date")

                return {"success": True, "data": df}

        return result

    def get_institutional_investors(
        self, stock_id: str, start_date: str = "", end_date: str = ""
    ) -> Dict:
        """
        取得三大法人買賣超資料

        Args:
            stock_id: 股票代碼
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            三大法人資料
        """
        if not start_date:
            start_date = (date.today() - timedelta(days=90)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = date.today().strftime("%Y-%m-%d")

        result = self._make_request(
            "TaiwanStockInstitutionalInvestorsBuySell", stock_id, start_date, end_date
        )

        if result.get("success"):
            df = pd.DataFrame(result["data"])
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"])
                return {"success": True, "data": df}

        return result

    def get_margin_trading(
        self, stock_id: str, start_date: str = "", end_date: str = ""
    ) -> Dict:
        """
        取得融資融券資料

        Args:
            stock_id: 股票代碼
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            融資融券資料
        """
        if not start_date:
            start_date = (date.today() - timedelta(days=90)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = date.today().strftime("%Y-%m-%d")

        result = self._make_request(
            "TaiwanStockMarginPurchaseShortSale", stock_id, start_date, end_date
        )

        if result.get("success"):
            df = pd.DataFrame(result["data"])
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"])
                return {"success": True, "data": df}

        return result

    def get_monthly_revenue(
        self, stock_id: str, start_date: str = "", end_date: str = ""
    ) -> Dict:
        """
        取得月營收資料

        Args:
            stock_id: 股票代碼
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            月營收資料
        """
        if not start_date:
            start_date = (date.today() - timedelta(days=365 * 2)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = date.today().strftime("%Y-%m-%d")

        result = self._make_request(
            "TaiwanStockMonthRevenue", stock_id, start_date, end_date
        )

        if result.get("success"):
            df = pd.DataFrame(result["data"])
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"])
                return {"success": True, "data": df}

        return result

    def get_dividend(
        self, stock_id: str, start_date: str = "", end_date: str = ""
    ) -> Dict:
        """
        取得股利資料

        Args:
            stock_id: 股票代碼
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            股利資料
        """
        if not start_date:
            start_date = (date.today() - timedelta(days=365 * 5)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = date.today().strftime("%Y-%m-%d")

        result = self._make_request(
            "TaiwanStockDividend", stock_id, start_date, end_date
        )

        if result.get("success"):
            df = pd.DataFrame(result["data"])
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"])
                return {"success": True, "data": df}

        return result

    def get_financial_statements(
        self, stock_id: str, start_date: str = "", end_date: str = ""
    ) -> Dict:
        """
        取得財務報表

        Args:
            stock_id: 股票代碼
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            財務報表資料
        """
        if not start_date:
            start_date = (date.today() - timedelta(days=365 * 3)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = date.today().strftime("%Y-%m-%d")

        result = self._make_request(
            "FinancialStatements", stock_id, start_date, end_date
        )

        if result.get("success"):
            df = pd.DataFrame(result["data"])
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"])
                return {"success": True, "data": df}

        return result

    def get_balance_sheet(
        self, stock_id: str, start_date: str = "", end_date: str = ""
    ) -> Dict:
        """
        取得資產負債表

        Args:
            stock_id: 股票代碼
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            資產負債表資料
        """
        if not start_date:
            start_date = (date.today() - timedelta(days=365 * 3)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = date.today().strftime("%Y-%m-%d")

        result = self._make_request(
            "TaiwanStockBalanceSheet", stock_id, start_date, end_date
        )

        if result.get("success"):
            df = pd.DataFrame(result["data"])
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"])
                return {"success": True, "data": df}

        return result

    def get_cash_flows(
        self, stock_id: str, start_date: str = "", end_date: str = ""
    ) -> Dict:
        """
        取得現金流量表

        Args:
            stock_id: 股票代碼
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            現金流量表資料
        """
        if not start_date:
            start_date = (date.today() - timedelta(days=365 * 3)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = date.today().strftime("%Y-%m-%d")

        result = self._make_request(
            "TaiwanStockCashFlowsStatement", stock_id, start_date, end_date
        )

        if result.get("success"):
            df = pd.DataFrame(result["data"])
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"])
                return {"success": True, "data": df}

        return result

    def get_taiex(self, start_date: str = "", end_date: str = "") -> Dict:
        """
        取得加權指數資料

        Args:
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            加權指數資料
        """
        if not start_date:
            start_date = (date.today() - timedelta(days=365 * 2)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = date.today().strftime("%Y-%m-%d")

        result = self._make_request("TAIEX", "", start_date, end_date)

        if result.get("success"):
            df = pd.DataFrame(result["data"])
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"])
                return {"success": True, "data": df}

        return result

    def get_all_data(
        self, stock_id: str, start_date: str = "", end_date: str = ""
    ) -> Dict:
        """
        取得所有資料（一次性）

        Args:
            stock_id: 股票代碼
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            所有資料
        """
        logger.info(f"從 FinMind 取得 {stock_id} 所有資料...")

        results = {}

        # 取得各種資料
        results["price"] = self.get_stock_price(stock_id, start_date, end_date)
        results["institutional"] = self.get_institutional_investors(
            stock_id, start_date, end_date
        )
        results["margin"] = self.get_margin_trading(stock_id, start_date, end_date)
        results["revenue"] = self.get_monthly_revenue(stock_id, start_date, end_date)
        results["dividend"] = self.get_dividend(stock_id, start_date, end_date)
        results["financial"] = self.get_financial_statements(
            stock_id, start_date, end_date
        )
        results["balance_sheet"] = self.get_balance_sheet(
            stock_id, start_date, end_date
        )
        results["cash_flows"] = self.get_cash_flows(stock_id, start_date, end_date)

        # 統計成功/失敗
        success_count = sum(1 for r in results.values() if r.get("success"))
        total_count = len(results)

        logger.info(f"FinMind 資料取得完成: {success_count}/{total_count} 成功")

        return {
            "success": True,
            "data": results,
            "summary": {
                "stock_id": stock_id,
                "success_count": success_count,
                "total_count": total_count,
            },
        }


# 全局實例
_finmind_fetcher = None


def get_finmind_fetcher(api_token: str = "") -> FinMindFetcher:
    """取得 FinMindFetcher 單例"""
    global _finmind_fetcher
    if _finmind_fetcher is None:
        _finmind_fetcher = FinMindFetcher(api_token)
    return _finmind_fetcher
