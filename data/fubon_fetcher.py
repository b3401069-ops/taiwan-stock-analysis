"""
台灣股票分析工具 - 富邦證券 SDK 整合模組
需要在另一台電腦上安裝 fubon_sdk 套件
回傳格式：JSON
"""
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from loguru import logger

try:
    from fubon_sdk.sdk import FubonSDK
    from fubon_sdk.constant import TimeInForce, OrderType, PriceType, MarketType
    FUBON_AVAILABLE = True
except ImportError:
    FUBON_AVAILABLE = False
    logger.warning("fubon_sdk 未安裝，富邦功能將無法使用")


class FubonFetcher:
    """富邦證券 SDK 整合類"""

    def __init__(self, api_key: str = None, api_secret: str = None, account: str = None):
        """
        初始化富邦 SDK

        Args:
            api_key: API Key
            api_secret: API Secret
            account: 帳號
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.account = account
        self.sdk = None
        self.connected = False

        if FUBON_AVAILABLE:
            self._connect()
        else:
            logger.warning("富邦 SDK 未安裝，請先安裝: pip install fubon-sdk")

    def _connect(self):
        """連接富邦 API"""
        try:
            self.sdk = FubonSDK()
            self.sdk.login(self.api_key, self.api_secret, self.account)
            self.connected = True
            logger.info("富邦 SDK 連接成功")
        except Exception as e:
            logger.error(f"富邦 SDK 連接失敗: {e}")
            self.connected = False

    def is_connected(self) -> bool:
        """檢查連接狀態"""
        return self.connected and FUBON_AVAILABLE

    # ──────────────────────────────────────────────
    #  即時報價
    # ──────────────────────────────────────────────

    def get_realtime_quote(self, stock_id: str) -> Dict:
        """
        取得即時報價

        Args:
            stock_id: 股票代碼 (e.g., "2330")

        Returns:
            JSON 格式的即時報價
        """
        if not self.is_connected():
            return self._mock_realtime_quote(stock_id)

        try:
            # 調用富邦 SDK 取得即時報價
            quote = self.sdk.get_quote(stock_id)

            result = {
                "stock_id": stock_id,
                "timestamp": datetime.now().isoformat(),
                "price_info": {
                    "current": quote.get("price", 0),
                    "open": quote.get("open", 0),
                    "high": quote.get("high", 0),
                    "low": quote.get("low", 0),
                    "close": quote.get("close", 0),
                    "previous_close": quote.get("previous_close", 0),
                    "change": quote.get("change", 0),
                    "change_percent": quote.get("change_percent", 0)
                },
                "volume_info": {
                    "volume": quote.get("volume", 0),
                    "amount": quote.get("amount", 0),
                    "avg_price": quote.get("avg_price", 0)
                },
                "orderbook": {
                    "bid": [
                        {"price": quote.get(f"bid_price_{i}", 0), "volume": quote.get(f"bid_volume_{i}", 0)}
                        for i in range(1, 6)
                    ],
                    "ask": [
                        {"price": quote.get(f"ask_price_{i}", 0), "volume": quote.get(f"ask_volume_{i}", 0)}
                        for i in range(1, 6)
                    ]
                },
                "source": "fubon_realtime"
            }

            return {"success": True, "data": result}

        except Exception as e:
            logger.error(f"富邦即時報價失敗: {e}")
            return {"success": False, "error": str(e), "data": self._mock_realtime_quote(stock_id)["data"]}

    # ──────────────────────────────────────────────
    #  歷史資料
    # ──────────────────────────────────────────────

    def get_historical_data(
        self,
        stock_id: str,
        start_date: str = None,
        end_date: str = None,
        interval: str = "1d"
    ) -> Dict:
        """
        取得歷史資料

        Args:
            stock_id: 股票代碼
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            interval: 資料間隔 (1m, 5m, 15m, 30m, 1h, 1d)

        Returns:
            JSON 格式的歷史資料
        """
        if not self.is_connected():
            return self._mock_historical_data(stock_id)

        try:
            # 預設日期
            if end_date is None:
                end_date = datetime.now().strftime("%Y-%m-%d")
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

            # 調用富邦 SDK
            bars = self.sdk.get_bars(stock_id, start_date, end_date, interval)

            data = []
            for bar in bars:
                data.append({
                    "date": bar.get("date", ""),
                    "open": bar.get("open", 0),
                    "high": bar.get("high", 0),
                    "low": bar.get("low", 0),
                    "close": bar.get("close", 0),
                    "volume": bar.get("volume", 0)
                })

            result = {
                "stock_id": stock_id,
                "start_date": start_date,
                "end_date": end_date,
                "interval": interval,
                "count": len(data),
                "data": data,
                "source": "fubon_historical"
            }

            return {"success": True, "data": result}

        except Exception as e:
            logger.error(f"富邦歷史資料失敗: {e}")
            return {"success": False, "error": str(e), "data": self._mock_historical_data(stock_id)["data"]}

    # ──────────────────────────────────────────────
    #  財報數據
    # ──────────────────────────────────────────────

    def get_financial_report(self, stock_id: str, report_type: str = "income") -> Dict:
        """
        取得財報數據

        Args:
            stock_id: 股票代碼
            report_type: 報表類型 (income, balance, cashflow, ratios)

        Returns:
            JSON 格式的財報數據
        """
        if not self.is_connected():
            return self._mock_financial_report(stock_id, report_type)

        try:
            # 調用富邦 SDK
            if report_type == "income":
                report = self.sdk.get_income_statement(stock_id)
            elif report_type == "balance":
                report = self.sdk.get_balance_sheet(stock_id)
            elif report_type == "cashflow":
                report = self.sdk.get_cash_flow(stock_id)
            elif report_type == "ratios":
                report = self.sdk.get_financial_ratios(stock_id)
            else:
                raise ValueError(f"未知的報表類型: {report_type}")

            result = {
                "stock_id": stock_id,
                "report_type": report_type,
                "period": report.get("period", ""),
                "data": report.get("data", {}),
                "source": "fubon_financial"
            }

            return {"success": True, "data": result}

        except Exception as e:
            logger.error(f"富邦財報失敗: {e}")
            return {"success": False, "error": str(e)}

    # ──────────────────────────────────────────────
    #  籌碼面數據
    # ──────────────────────────────────────────────

    def get_institutional_data(self, stock_id: str) -> Dict:
        """
        取得三大法人買賣超

        Returns:
            JSON 格式的法人資料
        """
        if not self.is_connected():
            return self._mock_institutional_data(stock_id)

        try:
            data = self.sdk.get_institutional(stock_id)

            result = {
                "stock_id": stock_id,
                "date": data.get("date", ""),
                "foreign_buy": data.get("foreign_buy", 0),
                "foreign_sell": data.get("foreign_sell", 0),
                "foreign_net": data.get("foreign_net", 0),
                "trust_buy": data.get("trust_buy", 0),
                "trust_sell": data.get("trust_sell", 0),
                "trust_net": data.get("trust_net", 0),
                "dealer_buy": data.get("dealer_buy", 0),
                "dealer_sell": data.get("dealer_sell", 0),
                "dealer_net": data.get("dealer_net", 0),
                "source": "fubon_institutional"
            }

            return {"success": True, "data": result}

        except Exception as e:
            logger.error(f"富邦法人資料失敗: {e}")
            return {"success": False, "error": str(e)}

    def get_margin_trading(self, stock_id: str) -> Dict:
        """
        取得融資融券資料

        Returns:
            JSON 格式的融資融券資料
        """
        if not self.is_connected():
            return self._mock_margin_data(stock_id)

        try:
            data = self.sdk.get_margin(stock_id)

            result = {
                "stock_id": stock_id,
                "date": data.get("date", ""),
                "margin_buy": data.get("margin_buy", 0),
                "margin_sell": data.get("margin_sell", 0),
                "margin_balance": data.get("margin_balance", 0),
                "short_buy": data.get("short_buy", 0),
                "short_sell": data.get("short_sell", 0),
                "short_balance": data.get("short_balance", 0),
                "source": "fubon_margin"
            }

            return {"success": True, "data": result}

        except Exception as e:
            logger.error(f"富邦融資融券失敗: {e}")
            return {"success": False, "error": str(e)}

    # ──────────────────────────────────────────────
    #  綜合分析（整合所有資料）
    # ──────────────────────────────────────────────

    def get_comprehensive_data(self, stock_id: str) -> Dict:
        """
        取得綜合資料（即時報價 + 歷史 + 財報 + 籌碼）

        Returns:
            JSON 格式的綜合資料
        """
        result = {
            "stock_id": stock_id,
            "timestamp": datetime.now().isoformat(),
            "realtime": {},
            "historical": {},
            "financial": {},
            "institutional": {},
            "margin": {}
        }

        # 並行取得所有資料
        result["realtime"] = self.get_realtime_quote(stock_id)
        result["historical"] = self.get_historical_data(stock_id, interval="1d")
        result["financial"] = self.get_financial_report(stock_id, "ratios")
        result["institutional"] = self.get_institutional_data(stock_id)
        result["margin"] = self.get_margin_trading(stock_id)

        return {"success": True, "data": result}

    # ──────────────────────────────────────────────
    #  Mock 資料（SDK 未連接時使用）
    # ──────────────────────────────────────────────

    def _mock_realtime_quote(self, stock_id: str) -> Dict:
        """模擬即時報價"""
        return {
            "success": True,
            "data": {
                "stock_id": stock_id,
                "timestamp": datetime.now().isoformat(),
                "price_info": {
                    "current": 1000.0,
                    "open": 995.0,
                    "high": 1010.0,
                    "low": 990.0,
                    "close": 1000.0,
                    "previous_close": 998.0,
                    "change": 2.0,
                    "change_percent": 0.2
                },
                "volume_info": {
                    "volume": 50000000,
                    "amount": 50000000000,
                    "avg_price": 1000.0
                },
                "orderbook": {
                    "bid": [{"price": 999, "volume": 1000}, {"price": 998, "volume": 2000}],
                    "ask": [{"price": 1001, "volume": 1500}, {"price": 1002, "volume": 2500}]
                },
                "source": "mock"
            }
        }

    def _mock_historical_data(self, stock_id: str) -> Dict:
        """模擬歷史資料"""
        return {
            "success": True,
            "data": {
                "stock_id": stock_id,
                "count": 0,
                "data": [],
                "source": "mock"
            }
        }

    def _mock_financial_report(self, stock_id: str, report_type: str) -> Dict:
        """模擬財報"""
        return {
            "success": True,
            "data": {
                "stock_id": stock_id,
                "report_type": report_type,
                "data": {},
                "source": "mock"
            }
        }

    def _mock_institutional_data(self, stock_id: str) -> Dict:
        """模擬法人資料"""
        return {
            "success": True,
            "data": {
                "stock_id": stock_id,
                "foreign_net": 0,
                "trust_net": 0,
                "dealer_net": 0,
                "source": "mock"
            }
        }

    def _mock_margin_data(self, stock_id: str) -> Dict:
        """模擬融資融券"""
        return {
            "success": True,
            "data": {
                "stock_id": stock_id,
                "margin_balance": 0,
                "short_balance": 0,
                "source": "mock"
            }
        }


# 全局實例
_fubon_fetcher = None


def get_fubon_fetcher(api_key: str = None, api_secret: str = None, account: str = None) -> FubonFetcher:
    """取得 FubonFetcher 單例"""
    global _fubon_fetcher
    if _fubon_fetcher is None:
        _fubon_fetcher = FubonFetcher(api_key, api_secret, account)
    return _fubon_fetcher
