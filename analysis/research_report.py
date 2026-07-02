"""
台灣股票分析工具 - 股票研究報告系統
每週自動產生持股研究報告
"""

import json
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import yfinance as yf
from loguru import logger

from analysis.industry_comparison import get_industry_comparison
from analysis.stock_analyst import get_stock_analyst
from analysis.valuation_metrics import get_valuation_metrics
from analysis.virtual_portfolio import get_virtual_portfolio
from data.twse_fetcher import get_twse_fetcher


class ResearchReportGenerator:
    """股票研究報告生成器"""

    def __init__(self):
        self.analyst = get_stock_analyst()
        self.valuation = get_valuation_metrics()
        self.industry = get_industry_comparison()
        self.portfolio = get_virtual_portfolio()
        self.twse = get_twse_fetcher()

    def generate_portfolio_report(self, report_type: str = "weekly") -> Dict:
        """
        產生持股研究報告

        Args:
            report_type: 報告類型 (daily/weekly/monthly)

        Returns:
            研究報告（JSON 格式）
        """
        try:
            # 取得持倉資料
            portfolio_data = self.portfolio.get_portfolio_summary()

            if not portfolio_data.get("success"):
                return {"success": False, "error": "無法取得持倉資料"}

            positions = portfolio_data["data"]["positions"]

            if not positions:
                return {
                    "success": True,
                    "data": {
                        "report_type": report_type,
                        "message": "目前沒有持股，無法產生報告",
                        "generated_at": datetime.now().isoformat(),
                    },
                }

            # 產生每檔股票的分析
            stock_reports = []
            for position in positions:
                stock_report = self._analyze_stock_for_report(position)
                stock_reports.append(stock_report)

            # 產生整體報告
            report = self._compile_report(
                stock_reports, portfolio_data["data"], report_type
            )

            return {"success": True, "data": report}

        except Exception as e:
            logger.error(f"產生研究報告失敗: {e}")
            return {"success": False, "error": str(e)}

    def generate_single_stock_report(self, stock_id: str) -> Dict:
        """
        產生單一股票研究報告

        Args:
            stock_id: 股票代碼

        Returns:
            研究報告（JSON 格式）
        """
        try:
            # 取得分析資料
            analysis = self.analyst.analyze(stock_id, include_ml=True)

            if not analysis.get("success"):
                return {"success": False, "error": f"無法分析 {stock_id}"}

            data = analysis["data"]

            # 取得估值資料
            valuation = self.valuation.get_valuation(stock_id)

            # 取得產業比較
            industry = self.industry.get_industry_analysis(stock_id)

            # 組合報告
            report = {
                "stock_id": stock_id,
                "stock_name": data.get("stock_name", stock_id),
                "report_type": "single_stock",
                "generated_at": datetime.now().isoformat(),
                # 價格資訊
                "price_info": data.get("price_info", {}),
                # 趨勢分析
                "trend_analysis": data.get("trend_analysis", {}),
                # ML 預測
                "ml_prediction": data.get("ml_prediction", {}),
                # 投資建議
                "recommendation": data.get("recommendation", {}),
                # 風險評估
                "risk_assessment": data.get("risk_assessment", {}),
                # 估值指標
                "valuation": (
                    valuation.get("data", {}) if valuation.get("success") else {}
                ),
                # 產業比較
                "industry": industry.get("data", {}) if industry.get("success") else {},
                # 綜合報告文字
                "summary": data.get("analysis_summary", ""),
            }

            return {"success": True, "data": report}

        except Exception as e:
            logger.error(f"產生單一股票報告失敗: {e}")
            return {"success": False, "error": str(e)}

    def _analyze_stock_for_report(self, position: Dict) -> Dict:
        """分析單一持股"""
        try:
            stock_id = position["stock_id"]
            stock_name = position["stock_name"]

            logger.info(f"分析 {stock_name} ({stock_id})...")

            # 取得即時價格
            try:
                ticker = yf.Ticker(stock_id)
                current_price = ticker.info.get(
                    "currentPrice", position["current_price"]
                )
            except:
                current_price = position["current_price"]

            # 計算持倉損益
            entry_price = position["entry_price"]
            shares = position["shares"]
            profit_loss = (current_price - entry_price) * shares
            profit_loss_pct = (profit_loss / (entry_price * shares)) * 100

            # 取得技術分析
            try:
                analysis = self.analyst.analyze(stock_id, include_ml=False)
                trend = analysis.get("data", {}).get("trend_analysis", {})
                risk = analysis.get("data", {}).get("risk_assessment", {})
            except:
                trend = {}
                risk = {}

            # 取得估值
            try:
                valuation = self.valuation.get_valuation(stock_id)
                valuation_data = valuation.get("data", {})
            except:
                valuation_data = {}

            # 計算距離目標價和停損
            target_price = position.get("target_price", 0)
            stop_loss = position.get("stop_loss", 0)

            distance_to_target = (
                ((target_price - current_price) / current_price * 100)
                if target_price > 0
                else 0
            )
            distance_to_stop = (
                ((stop_loss - current_price) / current_price * 100)
                if stop_loss > 0
                else 0
            )

            # 生成建議
            suggestion = self._generate_suggestion(
                current_price,
                entry_price,
                target_price,
                stop_loss,
                trend,
                risk,
                valuation_data,
                profit_loss_pct,
            )

            return {
                "stock_id": stock_id,
                "stock_name": stock_name,
                "entry_date": position["entry_date"],
                "entry_price": entry_price,
                "current_price": current_price,
                "shares": shares,
                "profit_loss": profit_loss,
                "profit_loss_pct": profit_loss_pct,
                "target_price": target_price,
                "stop_loss": stop_loss,
                "distance_to_target": distance_to_target,
                "distance_to_stop": distance_to_stop,
                "trend": trend,
                "risk": risk,
                "valuation": valuation_data,
                "suggestion": suggestion,
                "entry_reason": position.get("entry_reason", ""),
            }

        except Exception as e:
            logger.error(f"分析持股失敗: {e}")
            return {
                "stock_id": position.get("stock_id"),
                "stock_name": position.get("stock_name"),
                "error": str(e),
            }

    def _generate_suggestion(
        self,
        current_price,
        entry_price,
        target_price,
        stop_loss,
        trend,
        risk,
        valuation,
        profit_loss_pct,
    ) -> Dict:
        """生成建議"""
        try:
            # 趨勢評分
            trend_score = trend.get("score", 50)

            # 風險等級
            risk_level = risk.get("level", "medium")

            # 估值評級
            valuation_rating = valuation.get("valuation_rating", {}).get(
                "label", "中性"
            )

            # 綜合判斷
            if profit_loss_pct > 20 and trend_score < 50:
                action = "consider_sell"
                reason = "獲利豐厚且趨勢轉弱，考慮獲利了結"
                confidence = 70

            elif profit_loss_pct < -10 and risk_level == "high":
                action = "stop_loss"
                reason = "虧損擴大且風險升高，建議停損"
                confidence = 80

            elif current_price <= stop_loss:
                action = "stop_loss"
                reason = "已觸及停損價，建議執行停損"
                confidence = 90

            elif current_price >= target_price:
                action = "take_profit"
                reason = "已達目標價，考慮獲利了結"
                confidence = 85

            elif trend_score >= 70 and valuation_rating in ["低估", "合理"]:
                action = "hold_or_add"
                reason = "趨勢向上且估值合理，可考慮加碼"
                confidence = 65

            elif trend_score <= 30 and risk_level == "high":
                action = "reduce"
                reason = "趨勢轉弱且風險升高，考慮減碼"
                confidence = 70

            else:
                action = "hold"
                reason = "目前狀況穩定，繼續持有觀察"
                confidence = 60

            return {
                "action": action,
                "reason": reason,
                "confidence": confidence,
                "trend_score": trend_score,
                "risk_level": risk_level,
                "valuation_rating": valuation_rating,
            }

        except Exception as e:
            logger.error(f"生成建議失敗: {e}")
            return {"action": "hold", "reason": "無法判斷，建議觀望", "confidence": 50}

    def _compile_report(
        self, stock_reports: List[Dict], portfolio_data: Dict, report_type: str
    ) -> Dict:
        """組合完整報告"""
        try:
            # 統計數據
            total_positions = len(stock_reports)
            profitable_positions = len(
                [r for r in stock_reports if r.get("profit_loss", 0) > 0]
            )
            losing_positions = total_positions - profitable_positions

            total_profit_loss = sum(r.get("profit_loss", 0) for r in stock_reports)
            avg_return = (
                np.mean([r.get("profit_loss_pct", 0) for r in stock_reports])
                if stock_reports
                else 0
            )

            # 找出最佳和最差
            best_stock = (
                max(stock_reports, key=lambda x: x.get("profit_loss_pct", 0))
                if stock_reports
                else None
            )
            worst_stock = (
                min(stock_reports, key=lambda x: x.get("profit_loss_pct", 0))
                if stock_reports
                else None
            )

            # 生成文字報告
            report_text = self._generate_report_text(
                stock_reports,
                portfolio_data,
                report_type,
                total_positions,
                profitable_positions,
                losing_positions,
                total_profit_loss,
                avg_return,
                best_stock,
                worst_stock,
            )

            # 報告日期
            today = datetime.now()
            if report_type == "weekly":
                period = f"{(today - timedelta(days=7)).strftime('%Y/%m/%d')} - {today.strftime('%Y/%m/%d')}"
            elif report_type == "monthly":
                period = f"{today.strftime('%Y年%m月')}"
            else:
                period = today.strftime("%Y/%m/%d")

            return {
                "report_type": report_type,
                "report_period": period,
                "generated_at": today.isoformat(),
                # 摘要
                "summary": {
                    "total_positions": total_positions,
                    "profitable_positions": profitable_positions,
                    "losing_positions": losing_positions,
                    "total_profit_loss": total_profit_loss,
                    "average_return": avg_return,
                    "best_stock": (
                        {
                            "stock_id": best_stock["stock_id"],
                            "stock_name": best_stock["stock_name"],
                            "return_pct": best_stock["profit_loss_pct"],
                        }
                        if best_stock
                        else None
                    ),
                    "worst_stock": (
                        {
                            "stock_id": worst_stock["stock_id"],
                            "stock_name": worst_stock["stock_name"],
                            "return_pct": worst_stock["profit_loss_pct"],
                        }
                        if worst_stock
                        else None
                    ),
                },
                # 個股報告
                "stock_reports": stock_reports,
                # 整體建議
                "overall_suggestion": self._generate_overall_suggestion(stock_reports),
                # 文字報告
                "report_text": report_text,
            }

        except Exception as e:
            logger.error(f"組合報告失敗: {e}")
            return {"error": str(e)}

    def _generate_report_text(
        self,
        stock_reports,
        portfolio_data,
        report_type,
        total_positions,
        profitable_positions,
        losing_positions,
        total_profit_loss,
        avg_return,
        best_stock,
        worst_stock,
    ) -> str:
        """生成文字報告"""
        try:
            today = datetime.now()

            if report_type == "weekly":
                title = f"📊 每週持股研究報告"
                period = f"報告期間：{(today - timedelta(days=7)).strftime('%Y/%m/%d')} - {today.strftime('%Y/%m/%d')}"
            elif report_type == "monthly":
                title = f"📊 每月持股研究報告"
                period = f"報告期間：{today.strftime('%Y年%m月')}"
            else:
                title = f"📊 每日持股研究報告"
                period = f"報告日期：{today.strftime('%Y/%m/%d')}"

            report = f"""
{title}
{period}
報告生成時間：{today.strftime('%Y-%m-%d %H:%M')}

═══════════════════════════════════════════════════════════════

📋 **持倉摘要**

• 持股數量：{total_positions} 檔
• 獲利持股：{profitable_positions} 檔
• 虧損持股：{losing_positions} 檔
• 持倉總損益：{total_profit_loss:+,.0f} 元
• 平均報酬率：{avg_return:+.2f}%

"""

            # 最佳和最差持股
            if best_stock:
                report += f"🏆 **最佳持股**：{best_stock['stock_name']} ({best_stock['stock_id']}) - 報酬 {best_stock['profit_loss_pct']:+.2f}%\n"
            if worst_stock and worst_stock.get("profit_loss_pct", 0) < 0:
                report += f"⚠️ **最差持股**：{worst_stock['stock_name']} ({worst_stock['stock_id']}) - 報酬 {worst_stock['profit_loss_pct']:+.2f}%\n"

            report += (
                "\n═══════════════════════════════════════════════════════════════\n\n"
            )

            # 個股分析
            report += "📈 **個股分析**\n\n"

            for i, stock in enumerate(stock_reports, 1):
                if "error" in stock:
                    report += f"{i}. {stock.get('stock_name', 'N/A')} - 分析失敗: {stock['error']}\n\n"
                    continue

                # 狀態表情
                if stock["profit_loss_pct"] >= 10:
                    status_emoji = "🟢"
                elif stock["profit_loss_pct"] >= 0:
                    status_emoji = "🟡"
                else:
                    status_emoji = "🔴"

                report += f"{status_emoji} **{i}. {stock['stock_name']}** ({stock['stock_id']})\n\n"

                # 價格資訊
                report += f"   **價格資訊**\n"
                report += f"   • 進場價：{stock['entry_price']:.1f} 元 ({stock['entry_date']})\n"
                report += f"   • 目前價：{stock['current_price']:.1f} 元\n"
                report += f"   • 持股數：{stock['shares']} 股\n"
                report += f"   • 損益：{stock['profit_loss']:+,.0f} 元 ({stock['profit_loss_pct']:+.2f}%)\n\n"

                # 目標價和停損
                report += f"   **目標與停損**\n"
                report += f"   • 目標價：{stock['target_price']:.1f} 元 (距離 {stock['distance_to_target']:+.1f}%)\n"
                report += f"   • 停損價：{stock['stop_loss']:.1f} 元 (距離 {stock['distance_to_stop']:+.1f}%)\n\n"

                # 趨勢分析
                trend = stock.get("trend", {})
                if trend:
                    report += f"   **趨勢分析**\n"
                    report += f"   • 短期：{self._trend_text(trend.get('short_term', 'neutral'))}\n"
                    report += f"   • 中期：{self._trend_text(trend.get('medium_term', 'neutral'))}\n"
                    report += f"   • 長期：{self._trend_text(trend.get('long_term', 'neutral'))}\n"
                    report += f"   • 趨勢評分：{trend.get('score', 0)}/100\n\n"

                # 建議
                suggestion = stock.get("suggestion", {})
                if suggestion:
                    action_text = {
                        "hold": "繼續持有",
                        "hold_or_add": "持有/加碼",
                        "reduce": "考慮減碼",
                        "stop_loss": "執行停損",
                        "take_profit": "獲利了結",
                        "consider_sell": "考慮賣出",
                    }.get(suggestion.get("action", "hold"), "持有觀察")

                    report += f"   **💡 本週建議**\n"
                    report += f"   • 建議動作：**{action_text}**\n"
                    report += f"   • 建議原因：{suggestion.get('reason', 'N/A')}\n"
                    report += f"   • 信心水平：{suggestion.get('confidence', 0)}%\n"

                report += "\n───────────────────────────────────────────────────────────────\n\n"

            # 整體建議
            report += "📝 **整體建議**\n\n"
            overall = self._generate_overall_suggestion(stock_reports)
            report += f"{overall}\n\n"

            # 風險警示
            report += "⚠️ **風險警示**\n\n"
            report += "• 所有分析僅供參考，不構成投資建議\n"
            report += "• 投資有風險，請謹慎評估\n"
            report += "• 建議定期檢視投資組合\n"
            report += "• 遇到重大市場變化時，請重新評估\n"

            return report

        except Exception as e:
            logger.error(f"生成文字報告失敗: {e}")
            return f"報告生成失敗: {str(e)}"

    def _generate_overall_suggestion(self, stock_reports: List[Dict]) -> str:
        """生成整體建議"""
        try:
            if not stock_reports:
                return "目前沒有持股。"

            # 統計建議
            suggestions = {}
            for stock in stock_reports:
                action = stock.get("suggestion", {}).get("action", "hold")
                suggestions[action] = suggestions.get(action, 0) + 1

            # 生成建議
            advice = []

            # 停損警示
            stop_loss_count = suggestions.get("stop_loss", 0)
            if stop_loss_count > 0:
                advice.append(f"🔴 **{stop_loss_count} 檔股票觸及停損**，建議優先處理")

            # 獲利了結
            take_profit_count = suggestions.get("take_profit", 0) + suggestions.get(
                "consider_sell", 0
            )
            if take_profit_count > 0:
                advice.append(
                    f"🟢 **{take_profit_count} 檔股票達到目標**，可考慮獲利了結"
                )

            # 加碼機會
            add_count = suggestions.get("hold_or_add", 0)
            if add_count > 0:
                advice.append(f"📈 **{add_count} 檔股票趨勢良好**，可考慮加碼")

            # 減碼警示
            reduce_count = suggestions.get("reduce", 0)
            if reduce_count > 0:
                advice.append(f"⚠️ **{reduce_count} 檔股票趨勢轉弱**，考慮減碼")

            # 繼續持有
            hold_count = suggestions.get("hold", 0)
            if hold_count > 0:
                advice.append(f"✅ **{hold_count} 檔股票狀況穩定**，繼續持有觀察")

            if not advice:
                advice.append("目前持股狀況穩定，繼續觀察")

            return "\n".join(advice)

        except Exception as e:
            logger.error(f"生成整體建議失敗: {e}")
            return "無法生成整體建議"

    def _trend_text(self, trend: str) -> str:
        """趨勢文字"""
        return {
            "up": "上漲 📈",
            "down": "下跌 📉",
            "neutral": "盤整 ➡️",
            "bullish": "多頭 🚀",
            "bearish": "空頭 🐻",
        }.get(trend, "未知")

    def schedule_weekly_report(self) -> Dict:
        """排程每週報告"""
        try:
            # 產生報告
            report = self.generate_portfolio_report("weekly")

            if report.get("success"):
                # 儲存報告
                self._save_report(report["data"], "weekly")

                return {
                    "success": True,
                    "message": "每週報告已產生",
                    "data": report["data"],
                }
            else:
                return report

        except Exception as e:
            logger.error(f"排程每週報告失敗: {e}")
            return {"success": False, "error": str(e)}

    def _save_report(self, report: Dict, report_type: str):
        """儲存報告"""
        try:
            import os

            os.makedirs("reports", exist_ok=True)

            today = datetime.now().strftime("%Y%m%d")
            filename = f"reports/{report_type}_report_{today}.json"

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            logger.info(f"報告已儲存: {filename}")

        except Exception as e:
            logger.error(f"儲存報告失敗: {e}")

    def get_report_history(self, limit: int = 10) -> Dict:
        """取得報告歷史"""
        try:
            import os

            reports_dir = "reports"

            if not os.path.exists(reports_dir):
                return {"success": True, "data": []}

            # 取得所有報告檔案
            files = []
            for f in os.listdir(reports_dir):
                if f.endswith(".json"):
                    filepath = os.path.join(reports_dir, f)
                    files.append(
                        {
                            "filename": f,
                            "path": filepath,
                            "modified": datetime.fromtimestamp(
                                os.path.getmtime(filepath)
                            ).isoformat(),
                        }
                    )

            # 排序（最新在前）
            files.sort(key=lambda x: x["modified"], reverse=True)
            files = files[:limit]

            return {"success": True, "data": files}

        except Exception as e:
            logger.error(f"取得報告歷史失敗: {e}")
            return {"success": False, "error": str(e)}


# 全局實例
_report_generator = None


def get_research_report_generator() -> ResearchReportGenerator:
    """取得 ResearchReportGenerator 單例"""
    global _report_generator
    if _report_generator is None:
        _report_generator = ResearchReportGenerator()
    return _report_generator
