"""
台灣股票分析工具 - 財報數據抓取模組
資料來源：公開資訊觀測站 (MOPS) + TWSE
"""
import requests
import pandas as pd
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from loguru import logger
import time


class FinancialFetcher:
    """財報數據抓取類"""

    # 公開資訊觀測站 API
    MOPS_BASE = "https://mops.twse.com.tw/mops/web/"
    TWSE_BASE = "https://openapi.twse.com.tw/v1"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        self._last_request_time = 0
        self.REQUEST_INTERVAL = 1.0  # MOPS 比較嚴格，間隔要長一點

    def _throttle(self):
        """請求節流"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.REQUEST_INTERVAL:
            time.sleep(self.REQUEST_INTERVAL - elapsed)
        self._last_request_time = time.time()

    # ──────────────────────────────────────────────
    #  公開資訊觀測站 (MOPS) - 財務報表
    # ──────────────────────────────────────────────

    def get_income_statement(self, stock_id: str, year: int = None, quarter: int = None) -> Dict:
        """
        取得損益表 (Income Statement)

        Args:
            stock_id: 股票代碼 (e.g., "2330")
            year: 年度 (民國年，e.g., 112 = 2023)
            quarter: 季度 (1-4)

        Returns:
            損益表資料
        """
        try:
            if year is None:
                year = datetime.now().year - 1911  # 轉換為民國年
            if quarter is None:
                quarter = (datetime.now().month - 1) // 3 + 1

            self._throttle()

            # MOPS API 請求
            url = f"{self.MOPS_BASE}ajax_t164sb04"
            data = {
                "encodeURIComponent": "1",
                "step": "1",
                "firstin": "1",
                "off": "1",
                "co_id": stock_id,
                "year": str(year),
                "season": f"0{quarter}"
            }

            resp = self.session.post(url, data=data, timeout=15)

            if resp.status_code != 200:
                logger.warning(f"MOPS 損益表請求失敗: {resp.status_code}")
                return self._get_mock_income_statement(stock_id)

            # 解析 HTML 表格
            try:
                tables = pd.read_html(resp.text)
                if not tables:
                    return self._get_mock_income_statement(stock_id)

                # 取得損益表
                df = tables[0]

                # 整理資料
                result = {
                    "stock_id": stock_id,
                    "year": year + 1911,  # 轉換為西元年
                    "quarter": quarter,
                    "items": {}
                }

                for _, row in df.iterrows():
                    if len(row) >= 2:
                        item_name = str(row.iloc[0]).strip()
                        item_value = row.iloc[1]

                        # 轉換數值
                        if isinstance(item_value, str):
                            item_value = item_value.replace(",", "").replace("--", "0")
                            try:
                                item_value = float(item_value)
                            except ValueError:
                                continue

                        result["items"][item_name] = item_value

                return result

            except Exception as e:
                logger.warning(f"解析 MOPS 損益表失敗: {e}")
                return self._get_mock_income_statement(stock_id)

        except Exception as e:
            logger.error(f"取得損益表失敗: {e}")
            return self._get_mock_income_statement(stock_id)

    def get_balance_sheet(self, stock_id: str, year: int = None, quarter: int = None) -> Dict:
        """
        取得資產負債表 (Balance Sheet)

        Args:
            stock_id: 股票代碼
            year: 年度 (民國年)
            quarter: 季度

        Returns:
            資產負債表資料
        """
        try:
            if year is None:
                year = datetime.now().year - 1911
            if quarter is None:
                quarter = (datetime.now().month - 1) // 3 + 1

            self._throttle()

            url = f"{self.MOPS_BASE}ajax_t164sb03"
            data = {
                "encodeURIComponent": "1",
                "step": "1",
                "firstin": "1",
                "off": "1",
                "co_id": stock_id,
                "year": str(year),
                "season": f"0{quarter}"
            }

            resp = self.session.post(url, data=data, timeout=15)

            if resp.status_code != 200:
                return self._get_mock_balance_sheet(stock_id)

            try:
                tables = pd.read_html(resp.text)
                if not tables:
                    return self._get_mock_balance_sheet(stock_id)

                df = tables[0]

                result = {
                    "stock_id": stock_id,
                    "year": year + 1911,
                    "quarter": quarter,
                    "items": {}
                }

                for _, row in df.iterrows():
                    if len(row) >= 2:
                        item_name = str(row.iloc[0]).strip()
                        item_value = row.iloc[1]

                        if isinstance(item_value, str):
                            item_value = item_value.replace(",", "").replace("--", "0")
                            try:
                                item_value = float(item_value)
                            except ValueError:
                                continue

                        result["items"][item_name] = item_value

                return result

            except Exception as e:
                logger.warning(f"解析資產負債表失敗: {e}")
                return self._get_mock_balance_sheet(stock_id)

        except Exception as e:
            logger.error(f"取得資產負債表失敗: {e}")
            return self._get_mock_balance_sheet(stock_id)

    def get_cash_flow(self, stock_id: str, year: int = None, quarter: int = None) -> Dict:
        """
        取得現金流量表 (Cash Flow Statement)

        Args:
            stock_id: 股票代碼
            year: 年度 (民國年)
            quarter: 季度

        Returns:
            現金流量表資料
        """
        try:
            if year is None:
                year = datetime.now().year - 1911
            if quarter is None:
                quarter = (datetime.now().month - 1) // 3 + 1

            self._throttle()

            url = f"{self.MOPS_BASE}ajax_t164sb05"
            data = {
                "encodeURIComponent": "1",
                "step": "1",
                "firstin": "1",
                "off": "1",
                "co_id": stock_id,
                "year": str(year),
                "season": f"0{quarter}"
            }

            resp = self.session.post(url, data=data, timeout=15)

            if resp.status_code != 200:
                return self._get_mock_cash_flow(stock_id)

            try:
                tables = pd.read_html(resp.text)
                if not tables:
                    return self._get_mock_cash_flow(stock_id)

                df = tables[0]

                result = {
                    "stock_id": stock_id,
                    "year": year + 1911,
                    "quarter": quarter,
                    "items": {}
                }

                for _, row in df.iterrows():
                    if len(row) >= 2:
                        item_name = str(row.iloc[0]).strip()
                        item_value = row.iloc[1]

                        if isinstance(item_value, str):
                            item_value = item_value.replace(",", "").replace("--", "0")
                            try:
                                item_value = float(item_value)
                            except ValueError:
                                continue

                        result["items"][item_name] = item_value

                return result

            except Exception as e:
                logger.warning(f"解析現金流量表失敗: {e}")
                return self._get_mock_cash_flow(stock_id)

        except Exception as e:
            logger.error(f"取得現金流量表失敗: {e}")
            return self._get_mock_cash_flow(stock_id)

    # ──────────────────────────────────────────────
    #  TWSE - 基本財務指標
    # ──────────────────────────────────────────────

    def get_financial_ratios(self, stock_id: str) -> Dict:
        """
        取得財務比率指標
        結合 MOPS 財報計算
        """
        try:
            # 取得最近一季財報
            income = self.get_income_statement(stock_id)
            balance = self.get_balance_sheet(stock_id)
            cash_flow = self.get_cash_flow(stock_id)

            items_income = income.get("items", {})
            items_balance = balance.get("items", {})
            items_cash = cash_flow.get("items", {})

            ratios = {}

            # ── 獲利能力 ──
            revenue = items_income.get("營業收入", 0)
            gross_profit = items_income.get("營業毛利", 0)
            operating_income = items_income.get("營業利益", 0)
            net_income = items_income.get("本期淨利", 0)

            if revenue > 0:
                ratios["gross_margin"] = round(gross_profit / revenue * 100, 2)  # 毛利率
                ratios["operating_margin"] = round(operating_income / revenue * 100, 2)  # 營益率
                ratios["net_margin"] = round(net_income / revenue * 100, 2)  # 淨利率

            # ── 財務結構 ──
            total_assets = items_balance.get("資產總計", 0)
            total_liabilities = items_balance.get("負債總計", 0)
            equity = items_balance.get("權益總計", 0)

            if total_assets > 0:
                ratios["debt_ratio"] = round(total_liabilities / total_assets * 100, 2)  # 負債比率
                ratios["equity_ratio"] = round(equity / total_assets * 100, 2)  # 權益比率

            # ── 流動性 ──
            current_assets = items_balance.get("流動資產", 0)
            current_liabilities = items_balance.get("流動負債", 0)

            if current_liabilities > 0:
                ratios["current_ratio"] = round(current_assets / current_liabilities * 100, 2)  # 流動比率

            # ── 現金流 ──
            operating_cash_flow = items_cash.get("營業活動之淨現金流入（流出）", 0)
            if net_income > 0:
                ratios["ocf_to_net_income"] = round(operating_cash_flow / net_income * 100, 2)  # 營業現金流對淨利比

            # ── 每股數據 ──
            # 假設股數（實際應該從資料取得）
            shares = 100000000  # 1 億股
            if shares > 0:
                ratios["eps"] = round(net_income / shares, 2)  # 每股盈餘
                if equity > 0:
                    ratios["bvps"] = round(equity / shares, 2)  # 每股淨值

            return {
                "stock_id": stock_id,
                "period": f"{income.get('year', '')}Q{income.get('quarter', '')}",
                "ratios": ratios,
                "income_summary": {
                    "revenue": revenue,
                    "gross_profit": gross_profit,
                    "operating_income": operating_income,
                    "net_income": net_income
                },
                "balance_summary": {
                    "total_assets": total_assets,
                    "total_liabilities": total_liabilities,
                    "equity": equity,
                    "current_assets": current_assets,
                    "current_liabilities": current_liabilities
                }
            }

        except Exception as e:
            logger.error(f"取得財務比率失敗: {e}")
            return {"stock_id": stock_id, "ratios": {}, "error": str(e)}

    def get_multi_quarter_data(self, stock_id: str, quarters: int = 4) -> List[Dict]:
        """
        取得多季財報資料（用於趨勢分析）

        Args:
            stock_id: 股票代碼
            quarters: 要取得幾季

        Returns:
            多季財報資料列表
        """
        results = []
        current_year = datetime.now().year - 1911
        current_quarter = (datetime.now().month - 1) // 3 + 1

        for i in range(quarters):
            q = current_quarter - i
            y = current_year

            while q <= 0:
                q += 4
                y -= 1

            if y < 100:  # 不要太舊的資料
                break

            logger.info(f"取得 {stock_id} {y+1911}Q{q} 財報...")
            data = self.get_financial_ratios(stock_id)

            if data.get("ratios"):
                data["year"] = y + 1911
                data["quarter"] = q
                results.append(data)

            time.sleep(1)  # 避免請求太快

        return results

    # ──────────────────────────────────────────────
    #  Mock 資料（API 失敗時使用）
    # ──────────────────────────────────────────────

    def _get_mock_income_statement(self, stock_id: str) -> Dict:
        """模擬損益表（API 失敗時使用）"""
        logger.info(f"使用模擬損益表資料: {stock_id}")
        return {
            "stock_id": stock_id,
            "year": 2023,
            "quarter": 4,
            "items": {
                "營業收入": 0,
                "營業成本": 0,
                "營業毛利": 0,
                "營業費用": 0,
                "營業利益": 0,
                "業外收入": 0,
                "稅前淨利": 0,
                "所得稅": 0,
                "本期淨利": 0
            },
            "source": "mock"
        }

    def _get_mock_balance_sheet(self, stock_id: str) -> Dict:
        """模擬資產負債表"""
        return {
            "stock_id": stock_id,
            "year": 2023,
            "quarter": 4,
            "items": {
                "流動資產": 0,
                "非流動資產": 0,
                "資產總計": 0,
                "流動負債": 0,
                "非流動負債": 0,
                "負債總計": 0,
                "權益總計": 0
            },
            "source": "mock"
        }

    def _get_mock_cash_flow(self, stock_id: str) -> Dict:
        """模擬現金流量表"""
        return {
            "stock_id": stock_id,
            "year": 2023,
            "quarter": 4,
            "items": {
                "營業活動之淨現金流入（流出）": 0,
                "投資活動之淨現金流入（流出）": 0,
                "籌資活動之淨現金流入（流出）": 0,
                "本期現金及約當現金淨增（減）": 0
            },
            "source": "mock"
        }


# 全局實例
_financial_fetcher = None


def get_financial_fetcher() -> FinancialFetcher:
    """取得 FinancialFetcher 單例"""
    global _financial_fetcher
    if _financial_fetcher is None:
        _financial_fetcher = FinancialFetcher()
    return _financial_fetcher
