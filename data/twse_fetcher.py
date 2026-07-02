"""
台灣股票分析工具 - TWSE 官方資料取得模組
從證交所 Open API 取得免費公開資料
"""

import json
import time
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from loguru import logger


class TWSEFetcher:
    """TWSE 官方資料取得類"""

    BASE_URL = "https://openapi.twse.com.tw/v1"
    TPEX_URL = "https://www.tpex.org.tw/openapi/v1"

    # 請求間隔限制（秒），避免被封鎖
    REQUEST_INTERVAL = 0.5

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
            }
        )
        self._last_request_time = 0

    def _throttle(self):
        """限流：確保請求間隔"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.REQUEST_INTERVAL:
            time.sleep(self.REQUEST_INTERVAL - elapsed)
        self._last_request_time = time.time()

    def _get_json(self, url: str, params: Optional[Dict] = None) -> Any:
        """發送 GET 請求並返回 JSON"""
        self._throttle()
        try:
            resp = self.session.get(url, params=params, timeout=15)
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "")
            if "json" not in content_type:
                logger.warning(f"TWSE API 回傳非 JSON 格式（可能休市）: {url}")
                return []
            return resp.json()
        except requests.RequestException as e:
            logger.error(f"TWSE API 請求失敗: {url} - {e}")
            raise

    # ──────────────────────────────────────────────
    #  每日收盤行情（上市）
    # ──────────────────────────────────────────────
    def get_daily_closing(self) -> pd.DataFrame:
        """
        取得上市股票每日收盤行情
        欄位: Code, Name, Open, High, Low, Close, Change, TradeVolume, TradeValue, ...
        """
        url = f"{self.BASE_URL}/exchangeReport/STOCK_DAY_ALL"
        data = self._get_json(url)

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        # 轉換欄位類型
        numeric_cols = [
            "OpeningPrice",
            "HighestPrice",
            "LowestPrice",
            "ClosingPrice",
            "Change",
            "TradeVolume",
            "TradeValue",
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].str.replace(",", ""), errors="coerce")

        df.rename(
            columns={
                "Code": "stock_id",
                "Name": "name",
                "OpeningPrice": "open",
                "HighestPrice": "high",
                "LowestPrice": "low",
                "ClosingPrice": "close",
                "Change": "change",
                "TradeVolume": "volume",
                "TradeValue": "trade_value",
                "Transaction": "transactions",
            },
            inplace=True,
        )

        df["date"] = datetime.now().strftime("%Y-%m-%d")
        return df

    # ──────────────────────────────────────────────
    #  三大法人買賣超日報
    # ──────────────────────────────────────────────
    def get_institutional_investors(self) -> pd.DataFrame:
        """
        取得三大法人個股買賣超明細
        包含: 外資、投信、自營商
        """
        url = f"{self.BASE_URL}/fund/T86"
        data = self._get_json(url)

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        df.rename(
            columns={
                "Code": "stock_id",
                "Name": "name",
                "Foreign_Investor_buy": "foreign_buy",
                "Foreign_Investor_sell": "foreign_sell",
                "Foreign_Investor_net": "foreign_net",
                "Investment_Trust_buy": "trust_buy",
                "Investment_Trust_sell": "trust_sell",
                "Investment_Trust_net": "trust_net",
                "Dealer_self_buy": "dealer_buy",
                "Dealer_self_sell": "dealer_sell",
                "Dealer_self_net": "dealer_net",
                "Total_net": "total_net",
            },
            inplace=True,
            errors="ignore",
        )

        # 轉換數值欄位
        for col in df.columns:
            if col not in ("stock_id", "name"):
                df[col] = pd.to_numeric(df[col].str.replace(",", ""), errors="coerce")

        df["date"] = datetime.now().strftime("%Y-%m-%d")
        return df

    # ──────────────────────────────────────────────
    #  融資融券統計
    # ──────────────────────────────────────────────
    def get_margin_trading(self) -> pd.DataFrame:
        """
        取得融資融券統計
        """
        url = f"{self.BASE_URL}/marginTrading/TFMSA"
        data = self._get_json(url)

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        df.rename(
            columns={
                "Code": "stock_id",
                "Name": "name",
                "MarginPurchaseBuy": "margin_buy",
                "MarginPurchaseSell": "margin_sell",
                "MarginPurchaseCashRepayment": "margin_repay",
                "MarginPurchaseLimit": "margin_limit",
                "MarginPurchaseOutstanding": "margin_balance",
                "MarginPurchaseTodayBalance": "margin_today_balance",
                "ShortSaleBuy": "short_buy",
                "ShortSaleSell": "short_sell",
                "ShortSaleCashRepayment": "short_repay",
                "ShortSaleLimit": "short_limit",
                "ShortSaleOutstanding": "short_balance",
                "ShortSaleTodayBalance": "short_today_balance",
            },
            inplace=True,
            errors="ignore",
        )

        for col in df.columns:
            if col not in ("stock_id", "name", "date"):
                df[col] = pd.to_numeric(df[col].str.replace(",", ""), errors="coerce")

        df["date"] = datetime.now().strftime("%Y-%m-%d")
        return df

    # ──────────────────────────────────────────────
    #  個股日成交資訊（歷史 K 棒）
    # ──────────────────────────────────────────────
    def get_stock_daily_history(
        self, stock_id: str, year: int, month: int
    ) -> pd.DataFrame:
        """
        取得個股指定月份的日成交資訊
        URL: https://www.twse.com.tw/exchangeReport/STOCK_DAY
        回傳: 日期, 成交股數, 成交金額, 開盤價, 最高價, 最低價, 收盤價, 漲跌價差, 成交筆數
        """
        date_str = f"{year}{month:02d}01"
        url = "https://www.twse.com.tw/exchangeReport/STOCK_DAY"
        params = {
            "response": "json",
            "date": date_str,
            "stockNo": stock_id,
        }

        self._throttle()
        try:
            resp = self.session.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error(f"取得個股歷史資料失敗: {stock_id} {year}/{month} - {e}")
            return pd.DataFrame()

        if not data.get("data"):
            return pd.DataFrame()

        rows = []
        for row in data["data"]:
            # 格式: [日期, 成交股數, 成交金額, 開盤價, 最高價, 最低價, 收盤價, 漲跌價差, 成交筆數]
            try:
                # 日期格式: 112/06/01 (民國年)
                parts = row[0].split("/")
                ad_year = int(parts[0]) + 1911
                date_str = f"{ad_year}-{parts[1]}-{parts[2]}"

                rows.append(
                    {
                        "date": date_str,
                        "volume": int(row[1].replace(",", "")),
                        "trade_value": int(row[2].replace(",", "")),
                        "open": float(row[3].replace(",", "")),
                        "high": float(row[4].replace(",", "")),
                        "low": float(row[5].replace(",", "")),
                        "close": float(row[6].replace(",", "")),
                        "change": row[7].strip(),
                        "transactions": int(row[8].replace(",", "")),
                    }
                )
            except (ValueError, IndexError) as e:
                logger.warning(f"解析資料列失敗: {row} - {e}")
                continue

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        df["stock_id"] = stock_id
        return df

    def get_stock_history(self, stock_id: str, months: int = 12) -> pd.DataFrame:
        """
        取得個股最近 N 個月的歷史日成交資訊
        """
        today = date.today()
        all_dfs = []

        for i in range(months):
            d = today - timedelta(days=30 * i)
            df = self.get_stock_daily_history(stock_id, d.year, d.month)
            if not df.empty:
                all_dfs.append(df)

        if not all_dfs:
            return pd.DataFrame()

        result = pd.concat(all_dfs, ignore_index=True)
        result.sort_values("date", inplace=True)
        result.drop_duplicates(subset=["date"], keep="last", inplace=True)
        result.reset_index(drop=True, inplace=True)
        return result

    # ──────────────────────────────────────────────
    #  上市股票列表
    # ──────────────────────────────────────────────
    def get_stock_list(self) -> pd.DataFrame:
        """
        取得上市股票列表（從每日收盤行情提取）
        """
        df = self.get_daily_closing()
        if df.empty:
            return pd.DataFrame()

        return df[["stock_id", "name"]].copy()

    # ──────────────────────────────────────────────
    #  輔助方法
    # ──────────────────────────────────────────────
    def get_stock_info(self, stock_id: str) -> Optional[Dict]:
        """取得單一股票基本資訊"""
        df = self.get_daily_closing()
        if df.empty:
            return None

        row = df[df["stock_id"] == stock_id]
        if row.empty:
            return None

        return row.iloc[0].to_dict()


# 全域實例
_twse_fetcher: Optional[TWSEFetcher] = None


def get_twse_fetcher() -> TWSEFetcher:
    """取得 TWSEFetcher 全域實例"""
    global _twse_fetcher
    if _twse_fetcher is None:
        _twse_fetcher = TWSEFetcher()
    return _twse_fetcher
