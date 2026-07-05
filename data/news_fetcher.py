"""
台灣股票分析工具 - 財經新聞抓取
資料來源（全部免費）：
- FinMind TaiwanStockNews：個股新聞（依股票代碼查詢）
- 鉅亨網 cnyes API：台股市場即時新聞
- TWSE OpenAPI 重大訊息（t187ap04_L）：上市公司重大訊息公告
"""

import time
from datetime import date, timedelta
from typing import Dict, List, Optional

import requests
from loguru import logger

from data.finmind_fetcher import get_finmind_fetcher


class NewsFetcher:
    """財經新聞抓取器"""

    CNYES_API = "https://api.cnyes.com/media/api/v1/newslist/category/tw_stock"
    CNYES_ARTICLE_URL = "https://news.cnyes.com/news/id/{news_id}"
    TWSE_ANNOUNCEMENTS = "https://openapi.twse.com.tw/v1/opendata/t187ap04_L"

    def __init__(self):
        self.session = requests.Session()
        # 部分來源會擋無 UA 的請求
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
                ),
                "Accept": "application/json",
            }
        )

    # ──────────────────────────────────────────────
    #  個股新聞（FinMind）
    # ──────────────────────────────────────────────

    def get_stock_news(self, stock_id: str, days: int = 7, limit: int = 20) -> Dict:
        """
        取得個股相關新聞（FinMind TaiwanStockNews）

        Args:
            stock_id: 股票代碼（如 "2330"，自動去除 .TW 後綴）
            days: 回溯天數
            limit: 最多回傳幾則

        Returns:
            {"success": bool, "stock_id": str, "count": int, "news": [...]}
        """
        clean_id = stock_id.replace(".TWO", "").replace(".TW", "").strip()
        start_date = (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")

        fetcher = get_finmind_fetcher()
        result = fetcher._make_request(
            "TaiwanStockNews", clean_id, start_date=start_date
        )

        if not result.get("success"):
            return {
                "success": False,
                "stock_id": clean_id,
                "error": result.get("error", "FinMind 查詢失敗"),
            }

        news = []
        # 新的排前面
        for item in reversed(result.get("data", [])):
            news.append(
                {
                    "date": item.get("date", ""),
                    "title": item.get("title", ""),
                    "source": item.get("source", "FinMind"),
                    "url": item.get("link", ""),
                }
            )
            if len(news) >= limit:
                break

        return {
            "success": True,
            "stock_id": clean_id,
            "count": len(news),
            "news": news,
        }

    # ──────────────────────────────────────────────
    #  市場新聞（鉅亨網）
    # ──────────────────────────────────────────────

    def get_market_news(self, limit: int = 20) -> Dict:
        """
        取得台股市場最新新聞（鉅亨網 tw_stock 分類）

        Returns:
            {"success": bool, "count": int, "news": [...]}
        """
        try:
            response = self.session.get(
                self.CNYES_API,
                params={"page": 1, "limit": min(limit, 30)},
                timeout=15,
            )
            response.raise_for_status()
            payload = response.json()

            items = (payload.get("items") or {}).get("data") or []
            news = []
            for item in items[:limit]:
                publish_ts = item.get("publishAt")
                published = (
                    time.strftime("%Y-%m-%d %H:%M", time.localtime(publish_ts))
                    if publish_ts
                    else ""
                )
                news_id = item.get("newsId", "")
                news.append(
                    {
                        "date": published,
                        "title": item.get("title", ""),
                        "summary": item.get("summary", ""),
                        "source": "鉅亨網",
                        "url": (
                            self.CNYES_ARTICLE_URL.format(news_id=news_id)
                            if news_id
                            else ""
                        ),
                    }
                )

            return {"success": True, "count": len(news), "news": news}

        except Exception as e:
            logger.error(f"鉅亨網新聞抓取失敗: {e}")
            return {"success": False, "error": str(e)}

    # ──────────────────────────────────────────────
    #  重大訊息公告（TWSE）
    # ──────────────────────────────────────────────

    def get_material_announcements(
        self, stock_id: Optional[str] = None, limit: int = 50
    ) -> Dict:
        """
        取得上市公司重大訊息公告（TWSE OpenAPI，每日更新）

        Args:
            stock_id: 指定股票代碼則只回傳該公司的公告；None 則回傳全部
            limit: 最多回傳幾則

        Returns:
            {"success": bool, "count": int, "announcements": [...]}
        """
        try:
            response = self.session.get(self.TWSE_ANNOUNCEMENTS, timeout=15)
            response.raise_for_status()
            rows = response.json()

            clean_id = None
            if stock_id:
                clean_id = stock_id.replace(".TWO", "").replace(".TW", "").strip()

            announcements = []
            for row in rows:
                # TWSE 開放資料欄位名偶有前後空白，統一 strip 後比對
                fields = {str(k).strip(): v for k, v in row.items()}
                company_id = str(fields.get("公司代號", "")).strip()

                if clean_id and company_id != clean_id:
                    continue

                announcements.append(
                    {
                        "stock_id": company_id,
                        "company": fields.get("公司名稱", ""),
                        "date": fields.get("發言日期", ""),
                        "time": fields.get("發言時間", ""),
                        "subject": fields.get("主旨", ""),
                        "source": "TWSE 重大訊息",
                    }
                )
                if len(announcements) >= limit:
                    break

            return {
                "success": True,
                "count": len(announcements),
                "announcements": announcements,
            }

        except Exception as e:
            logger.error(f"TWSE 重大訊息抓取失敗: {e}")
            return {"success": False, "error": str(e)}

    # ──────────────────────────────────────────────
    #  投資組合新聞摘要（給 AI 產生投資建議用）
    # ──────────────────────────────────────────────

    def get_portfolio_news_digest(
        self, stock_ids: List[str], days: int = 7, per_stock_limit: int = 5
    ) -> Dict:
        """
        一次取得多檔持股的新聞 + 重大訊息 + 市場新聞，
        供 AI Agent 產生投資建議時作為消息面輸入。

        Args:
            stock_ids: 股票代碼清單
            days: 個股新聞回溯天數
            per_stock_limit: 每檔股票最多幾則新聞
        """
        digest: Dict = {
            "generated_at": date.today().isoformat(),
            "market_news": self.get_market_news(limit=10),
            "stocks": {},
        }

        announcements = self.get_material_announcements(limit=200)

        for stock_id in stock_ids:
            clean_id = stock_id.replace(".TWO", "").replace(".TW", "").strip()
            stock_news = self.get_stock_news(
                clean_id, days=days, limit=per_stock_limit
            )

            stock_announcements = []
            if announcements.get("success"):
                stock_announcements = [
                    a
                    for a in announcements["announcements"]
                    if a["stock_id"] == clean_id
                ]

            digest["stocks"][clean_id] = {
                "news": stock_news.get("news", []),
                "announcements": stock_announcements,
            }
            # FinMind 免費額度有請求頻率限制，稍作間隔
            time.sleep(0.5)

        return {"success": True, "data": digest}


# 全局實例
_news_fetcher = None


def get_news_fetcher() -> NewsFetcher:
    """取得 NewsFetcher 單例"""
    global _news_fetcher
    if _news_fetcher is None:
        _news_fetcher = NewsFetcher()
    return _news_fetcher
