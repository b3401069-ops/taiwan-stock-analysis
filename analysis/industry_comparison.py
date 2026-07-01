"""
台灣股票分析工具 - 產業比較分析模組
建立產業分類，比較同業估值和財務指標
資料來源：Yahoo Finance（免費）
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed


# ──────────────────────────────────────────────
#  台灣主要產業分類
# ──────────────────────────────────────────────

TAIWAN_INDUSTRIES = {
    "半導體": {
        "stocks": ["2330.TW", "2379.TW", "3034.TW", "2454.TW", "2303.TW", "3711.TW", "2327.TW", "6488.TW"],
        "description": "IC 設計、晶圓代工、封測、設備"
    },
    "電子代工": {
        "stocks": ["2317.TW", "2382.TW", "4938.TW", "3231.TW", "2356.TW"],
        "description": "電腦、手機、伺服器代工"
    },
    "金融": {
        "stocks": ["2881.TW", "2882.TW", "2884.TW", "2891.TW", "2886.TW", "2880.TW", "2892.TW"],
        "description": "銀行、壽險、證券"
    },
    "電信": {
        "stocks": ["2412.TW", "3045.TW", "4904.TW"],
        "description": "電信服務"
    },
    "傳產": {
        "stocks": ["1301.TW", "1303.TW", "1326.TW", "2002.TW", "1101.TW", "2912.TW"],
        "description": "塑化、鋼鐵、水泥、食品"
    },
    "生技": {
        "stocks": ["4142.TW", "6547.TW", "3164.TW", "6535.TW", "4157.TW"],
        "description": "製藥、醫療器材、新藥開發"
    },
    "電動車": {
        "stocks": ["2345.TW", "2377.TW", "3653.TW", "6666.TW", "2207.TW"],
        "description": "電動車相關、充電樁、電池"
    },
    "AI 概念": {
        "stocks": ["2330.TW", "2379.TW", "3034.TW", "2454.TW", "3661.TW", "8069.TW"],
        "description": "AI 晶片、伺服器、散熱"
    }
}


class IndustryComparison:
    """產業比較分析類"""

    def __init__(self):
        self.cache = {}
        self.cache_timeout = 3600  # 快取 1 小時

    def get_industry_analysis(self, stock_id: str) -> Dict:
        """
        取得股票的產業分析

        Args:
            stock_id: 股票代碼

        Returns:
            產業比較分析結果
        """
        try:
            # 找出所屬產業
            industry = self._find_industry(stock_id)
            if not industry:
                return {
                    "success": False,
                    "error": f"找不到 {stock_id} 的產業分類"
                }

            # 取得同業數據
            peers_data = self._get_peers_data(industry["stocks"])

            # 計算產業平均
            industry_avg = self._calculate_industry_average(peers_data)

            # 取得目標股票數據
            target_data = peers_data.get(stock_id, {})

            # 計算排名
            rankings = self._calculate_rankings(stock_id, peers_data)

            result = {
                "success": True,
                "data": {
                    "stock_id": stock_id,
                    "industry": industry["name"],
                    "industry_description": industry["description"],
                    "timestamp": datetime.now().isoformat(),

                    # 目標股票
                    "target_stock": target_data,

                    # 產業平均
                    "industry_average": industry_avg,

                    # 排名
                    "rankings": rankings,

                    # 同業比較
                    "peers_comparison": self._format_peers_comparison(stock_id, peers_data, industry_avg),

                    # 分析結論
                    "analysis": self._generate_analysis(stock_id, target_data, industry_avg, rankings)
                }
            }

            return result

        except Exception as e:
            logger.error(f"產業分析失敗: {e}")
            return {"success": False, "error": str(e)}

    def get_all_industries(self) -> Dict:
        """取得所有產業列表"""
        industries = []
        for name, info in TAIWAN_INDUSTRIES.items():
            industries.append({
                "name": name,
                "description": info["description"],
                "stock_count": len(info["stocks"]),
                "stocks": info["stocks"]
            })

        return {"success": True, "data": industries}

    def get_industry_stocks(self, industry_name: str) -> Dict:
        """取得產業內所有股票"""
        if industry_name not in TAIWAN_INDUSTRIES:
            return {"success": False, "error": f"找不到產業: {industry_name}"}

        industry = TAIWAN_INDUSTRIES[industry_name]
        return {
            "success": True,
            "data": {
                "industry": industry_name,
                "stocks": industry["stocks"],
                "description": industry["description"]
            }
        }

    def _find_industry(self, stock_id: str) -> Optional[Dict]:
        """找出股票所屬產業"""
        for name, info in TAIWAN_INDUSTRIES.items():
            if stock_id in info["stocks"]:
                return {"name": name, **info}
        return None

    def _get_peers_data(self, stock_ids: List[str]) -> Dict:
        """取得同業數據（並行處理）"""
        peers_data = {}

        def fetch_stock_data(stock_id):
            try:
                ticker = yf.Ticker(stock_id)
                info = ticker.info

                if not info:
                    return stock_id, None

                data = {
                    "stock_id": stock_id,
                    "name": info.get("shortName", stock_id),
                    "price": info.get("currentPrice", info.get("regularMarketPrice", 0)),
                    "market_cap": info.get("marketCap", 0),
                    "pe_ratio": info.get("trailingPE", 0),
                    "pb_ratio": info.get("priceToBook", 0),
                    "dividend_yield": info.get("dividendYield", 0),
                    "ps_ratio": info.get("priceToSalesTrailing12Months", 0),
                    "ev_ebitda": info.get("enterpriseToEbitda", 0),
                    "profit_margin": info.get("profitMargins", 0),
                    "roe": info.get("returnOnEquity", 0),
                    "revenue_growth": info.get("revenueGrowth", 0),
                    "earnings_growth": info.get("earningsGrowth", 0)
                }

                return stock_id, data
            except Exception as e:
                logger.warning(f"取得 {stock_id} 數據失敗: {e}")
                return stock_id, None

        # 並行取得數據
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(fetch_stock_data, sid) for sid in stock_ids]
            for future in as_completed(futures):
                stock_id, data = future.result()
                if data:
                    peers_data[stock_id] = data

        return peers_data

    def _calculate_industry_average(self, peers_data: Dict) -> Dict:
        """計算產業平均"""
        if not peers_data:
            return {}

        metrics = ["pe_ratio", "pb_ratio", "dividend_yield", "ps_ratio", "ev_ebitda",
                    "profit_margin", "roe", "revenue_growth", "earnings_growth"]

        averages = {}
        for metric in metrics:
            values = [d.get(metric, 0) for d in peers_data.values() if d.get(metric, 0)]
            if values:
                averages[metric] = round(np.mean(values), 2)
            else:
                averages[metric] = None

        return averages

    def _calculate_rankings(self, stock_id: str, peers_data: Dict) -> Dict:
        """計算排名"""
        if stock_id not in peers_data:
            return {}

        rankings = {}
        metrics_to_rank = {
            "pe_ratio": "ascending",  # PE 越低越好
            "pb_ratio": "ascending",  # PB 越低越好
            "dividend_yield": "descending",  # 股利越高越好
            "roe": "descending",  # ROE 越高越好
            "profit_margin": "descending",  # 淨利率越高越好
            "revenue_growth": "descending"  # 營收成長越高越好
        }

        for metric, order in metrics_to_rank.items():
            values = []
            for sid, data in peers_data.items():
                val = data.get(metric, 0)
                if val:
                    values.append((sid, val))

            if not values:
                continue

            # 排序
            if order == "ascending":
                values.sort(key=lambda x: x[1])
            else:
                values.sort(key=lambda x: x[1], reverse=True)

            # 找排名
            for rank, (sid, val) in enumerate(values, 1):
                if sid == stock_id:
                    rankings[metric] = {
                        "rank": rank,
                        "total": len(values),
                        "value": round(val, 2),
                        "percentile": round((1 - (rank - 1) / len(values)) * 100, 1)
                    }
                    break

        return rankings

    def _format_peers_comparison(self, stock_id: str, peers_data: Dict, industry_avg: Dict) -> List[Dict]:
        """格式化同業比較"""
        comparison = []

        for sid, data in peers_data.items():
            is_target = (sid == stock_id)
            comparison.append({
                "stock_id": sid,
                "name": data.get("name", sid),
                "is_target": is_target,
                "price": data.get("price", 0),
                "market_cap": data.get("market_cap", 0),
                "pe_ratio": data.get("pe_ratio", 0),
                "pb_ratio": data.get("pb_ratio", 0),
                "dividend_yield": data.get("dividend_yield", 0),
                "roe": data.get("roe", 0),
                "profit_margin": data.get("profit_margin", 0),
                "pe_vs_industry": self._compare_to_avg(data.get("pe_ratio", 0), industry_avg.get("pe_ratio")),
                "pb_vs_industry": self._compare_to_avg(data.get("pb_ratio", 0), industry_avg.get("pb_ratio"))
            })

        # 排序：目標股票優先
        comparison.sort(key=lambda x: (not x["is_target"], x["stock_id"]))
        return comparison

    def _compare_to_avg(self, value: float, avg: float) -> Optional[str]:
        """比較與平均的差異"""
        if not value or not avg or avg == 0:
            return None

        diff = (value - avg) / avg * 100
        if diff > 20:
            return f"+{diff:.1f}% (高於平均)"
        elif diff < -20:
            return f"{diff:.1f}% (低於平均)"
        else:
            return f"{diff:.1f}% (接近平均)"

    def _generate_analysis(self, stock_id: str, target_data: Dict, industry_avg: Dict, rankings: Dict) -> Dict:
        """生成分析結論"""
        if not target_data or not industry_avg:
            return {"summary": "數據不足，無法分析"}

        strengths = []
        weaknesses = []
        opportunities = []
        threats = []

        # PE 分析
        pe = target_data.get("pe_ratio", 0)
        avg_pe = industry_avg.get("pe_ratio", 0)
        if pe and avg_pe:
            if pe < avg_pe * 0.8:
                strengths.append("本益比低於產業平均，可能被低估")
            elif pe > avg_pe * 1.2:
                weaknesses.append("本益比高於產業平均，可能被高估")

        # ROE 分析
        roe = target_data.get("roe", 0)
        avg_roe = industry_avg.get("roe", 0)
        if roe and avg_roe:
            if roe > avg_roe * 1.2:
                strengths.append("ROE 高於產業平均，獲利能力強")
            elif roe < avg_roe * 0.8:
                weaknesses.append("ROE 低於產業平均，獲利能力待改善")

        # 股利分析
        div_yield = target_data.get("dividend_yield", 0)
        avg_div = industry_avg.get("dividend_yield", 0)
        if div_yield and avg_div:
            if div_yield > avg_div * 1.2:
                strengths.append("股利殖利率高於產業平均")
            elif div_yield < avg_div * 0.5:
                opportunities.append("股利政策可能調整")

        # 成長分析
        growth = target_data.get("revenue_growth", 0)
        avg_growth = industry_avg.get("revenue_growth", 0)
        if growth and avg_growth:
            if growth > avg_growth:
                opportunities.append("營收成長優於同業")
            else:
                threats.append("營收成長落後同業")

        # 總結
        pe_rank = rankings.get("pe_ratio", {}).get("rank", 0)
        total = rankings.get("pe_ratio", {}).get("total", 0)

        summary = f"{stock_id} 在產業中"
        if pe_rank:
            if pe_rank <= total * 0.3:
                summary += "估值排名前段，相對便宜"
            elif pe_rank >= total * 0.7:
                summary += "估值排名後段，相對昂貴"
            else:
                summary += "估值處於中間水平"

        return {
            "summary": summary,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "opportunities": opportunities,
            "threats": threats,
            "overall_rating": self._calculate_overall_rating(strengths, weaknesses, opportunities, threats)
        }

    def _calculate_overall_rating(self, strengths, weaknesses, opportunities, threats) -> str:
        """計算總體評級"""
        score = len(strengths) - len(weaknesses) + len(opportunities) - len(threats)

        if score >= 3:
            return "excellent"
        elif score >= 1:
            return "good"
        elif score >= -1:
            return "neutral"
        else:
            return "cautious"


# 全局實例
_industry = None


def get_industry_comparison() -> IndustryComparison:
    """取得 IndustryComparison 單例"""
    global _industry
    if _industry is None:
        _industry = IndustryComparison()
    return _industry
