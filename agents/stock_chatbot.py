"""
台灣股票分析工具 - AI 股票聊天分析師
可以問答的 AI 分析師，用自然語言回答股票問題
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Optional

from loguru import logger

from analysis.industry_comparison import get_industry_comparison
from analysis.stock_analyst import get_stock_analyst
from analysis.valuation_metrics import get_valuation_metrics
from data.dividend_fetcher import get_dividend_fetcher
from data.twse_fetcher import get_twse_fetcher


class StockChatbot:
    """AI 股票聊天分析師"""

    def __init__(self):
        self.analyst = get_stock_analyst()
        self.valuation = get_valuation_metrics()
        self.industry = get_industry_comparison()
        self.dividend = get_dividend_fetcher()
        self.twse = get_twse_fetcher()

        # 對話歷史
        self.conversation_history = []

    async def chat(self, user_message: str) -> Dict:
        """
        與 AI 分析師對話

        Args:
            user_message: 用戶訊息

        Returns:
            AI 回應（JSON 格式）
        """
        try:
            # 記錄用戶訊息
            self.conversation_history.append(
                {
                    "role": "user",
                    "content": user_message,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # 分析用戶意圖
            intent = self._detect_intent(user_message)

            # 根據意圖生成回應
            response = await self._generate_response(user_message, intent)

            # 記錄 AI 回應
            self.conversation_history.append(
                {
                    "role": "assistant",
                    "content": response["message"],
                    "timestamp": datetime.now().isoformat(),
                }
            )

            return {
                "success": True,
                "data": {
                    "message": response["message"],
                    "intent": intent,
                    "data": response.get("data", {}),
                    "suggestions": response.get("suggestions", []),
                },
            }

        except Exception as e:
            logger.error(f"聊天失敗: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": {"message": "抱歉，我遇到了一些問題，請稍後再試。"},
            }

    def _detect_intent(self, message: str) -> str:
        """檢測用戶意圖"""
        message = message.lower().strip()

        # 股票代碼模式
        stock_pattern = r"(\d{4,6})\.?(tw|two)?"

        # 問候語
        if any(word in message for word in ["你好", "嗨", "hi", "hello", "哈囉"]):
            return "greeting"

        # 分析相關
        elif any(word in message for word in ["分析", "評估", "看法", "怎麼看"]):
            return "analysis"

        # 建議相關
        elif any(
            word in message for word in ["建議", "買", "賣", "持有", "進場", "出場"]
        ):
            return "recommendation"

        # 價格相關
        elif any(word in message for word in ["價格", "股價", "多少錢", "報價"]):
            return "price"

        # 估值相關
        elif any(
            word in message
            for word in ["估值", "pe", "pb", "本益比", "淨值比", "便宜", "貴"]
        ):
            return "valuation"

        # 產業相關
        elif any(word in message for word in ["產業", "同業", "比較", "排名"]):
            return "industry"

        # 股利相關
        elif any(word in message for word in ["股利", "配息", "殖利率", "填息"]):
            return "dividend"

        # 趨勢相關
        elif any(word in message for word in ["趨勢", "走勢", "方向", "漲", "跌"]):
            return "trend"

        # 風險相關
        elif any(word in message for word in ["風險", "危險", "停損", "停利"]):
            return "risk"

        # 預測相關
        elif any(word in message for word in ["預測", "未來", "明天", "下週"]):
            return "prediction"

        # 幫助
        elif any(word in message for word in ["幫助", "help", "功能", "可以做什麼"]):
            return "help"

        # 包含股票代碼
        elif re.search(stock_pattern, message):
            return "stock_query"

        # 預設
        else:
            return "general"

    async def _generate_response(self, message: str, intent: str) -> Dict:
        """生成回應"""

        # 提取股票代碼
        stock_id = self._extract_stock_id(message)

        if intent == "greeting":
            return self._greeting_response()

        elif intent == "help":
            return self._help_response()

        elif intent == "analysis":
            if stock_id:
                return await self._analysis_response(stock_id)
            else:
                return self._ask_stock_id_response("分析")

        elif intent == "recommendation":
            if stock_id:
                return await self._recommendation_response(stock_id)
            else:
                return self._ask_stock_id_response("建議")

        elif intent == "price":
            if stock_id:
                return await self._price_response(stock_id)
            else:
                return self._ask_stock_id_response("價格")

        elif intent == "valuation":
            if stock_id:
                return await self._valuation_response(stock_id)
            else:
                return self._ask_stock_id_response("估值")

        elif intent == "industry":
            if stock_id:
                return await self._industry_response(stock_id)
            else:
                return self._ask_stock_id_response("產業比較")

        elif intent == "dividend":
            if stock_id:
                return await self._dividend_response(stock_id)
            else:
                return self._ask_stock_id_response("股利")

        elif intent == "trend":
            if stock_id:
                return await self._trend_response(stock_id)
            else:
                return self._ask_stock_id_response("趨勢")

        elif intent == "risk":
            if stock_id:
                return await self._risk_response(stock_id)
            else:
                return self._ask_stock_id_response("風險")

        elif intent == "prediction":
            if stock_id:
                return await self._prediction_response(stock_id)
            else:
                return self._ask_stock_id_response("預測")

        elif intent == "stock_query":
            return await self._general_stock_response(stock_id)

        else:
            return self._general_response()

    def _extract_stock_id(self, message: str) -> Optional[str]:
        """從訊息中提取股票代碼"""
        # 匹配 4-6 位數字，可能帶 .TW 或 .TWO
        pattern = r"(\d{4,6})\.?(tw|two)?"
        match = re.search(pattern, message.lower())

        if match:
            stock_num = match.group(1)
            suffix = match.group(2)

            if suffix:
                return f"{stock_num}.{suffix.upper()}"
            else:
                # 預設加 .TW
                return f"{stock_num}.TW"

        return None

    def _greeting_response(self) -> Dict:
        """問候回應"""
        return {
            "message": "你好！👋 我是 AI 股票分析師，可以幫你分析台灣股票。\n\n"
            "你可以問我：\n"
            "• 「分析台積電」- 綜合分析\n"
            "• 「2330 的建議」- 投資建議\n"
            "• 「台積電估值」- 估值分析\n"
            "• 「2330 股利」- 股利資訊\n"
            "• 「幫助」- 查看所有功能",
            "suggestions": ["分析 2330", "幫助", "2330 建議"],
        }

    def _help_response(self) -> Dict:
        """幫助回應"""
        return {
            "message": "📚 **AI 股票分析師功能**\n\n"
            "**分析功能：**\n"
            "• 「分析 {股票代碼}」- 完整綜合分析\n"
            "• 「{股票代碼} 建議」- 投資建議\n"
            "• 「{股票代碼} 趨勢」- 趨勢分析\n"
            "• 「{股票代碼} 預測」- ML 預測\n\n"
            "**數據查詢：**\n"
            "• 「{股票代碼} 股價」- 即時報價\n"
            "• 「{股票代碼} 估值」- PE、PB 等估值指標\n"
            "• 「{股票代碼} 產業」- 產業比較\n"
            "• 「{股票代碼} 股利」- 股利和填息率\n"
            "• 「{股票代碼} 風險」- 風險評估\n\n"
            "**範例：**\n"
            "• 「分析 2330」\n"
            "• 「台積電估值」\n"
            "• 「2317 股利」\n"
            "• 「聯發科建議」",
            "suggestions": ["分析 2330", "2317 估值", "聯發科建議"],
        }

    async def _analysis_response(self, stock_id: str) -> Dict:
        """綜合分析回應"""
        try:
            result = await self.analyst.analyze(stock_id, include_ml=True)

            if not result.get("success"):
                return {"message": f"無法分析 {stock_id}，請確認股票代碼是否正確。"}

            data = result.get("data", {})
            price_info = data.get("price_info", {})
            trend = data.get("trend_analysis", {})
            ml = data.get("ml_prediction", {})
            rec = data.get("recommendation", {})
            risk = data.get("risk_assessment", {})

            # 格式化回應
            message = f"📊 **{stock_id} 綜合分析報告**\n\n"

            # 價格資訊
            current_price = price_info.get("current_price", "N/A")
            change = price_info.get("change", 0)
            change_pct = price_info.get("change_percent", 0)
            change_emoji = "📈" if change >= 0 else "📉"
            message += f"**目前股價：** {current_price} 元 {change_emoji} {change:+.1f} ({change_pct:+.2f}%)\n\n"

            # 趨勢分析
            message += "**趨勢分析：**\n"
            short_trend = trend.get("short_term", "neutral")
            medium_trend = trend.get("medium_term", "neutral")
            long_trend = trend.get("long_term", "neutral")
            trend_score = trend.get("score", 0)

            message += f"• 短期：{self._trend_emoji(short_trend)} {self._trend_text(short_trend)}\n"
            message += f"• 中期：{self._trend_emoji(medium_trend)} {self._trend_text(medium_trend)}\n"
            message += f"• 長期：{self._trend_emoji(long_trend)} {self._trend_text(long_trend)}\n"
            message += f"• 趨勢評分：{trend_score}/100\n\n"

            # ML 預測
            if ml:
                message += "**ML 預測：**\n"
                message += f"• 預測趨勢：{self._trend_emoji(ml.get('trend', 'neutral'))} {self._trend_text(ml.get('trend', 'neutral'))}\n"
                message += f"• 預期報酬：{ml.get('expected_return', 0)*100:+.1f}%\n"
                message += f"• 預測模型：{ml.get('model', 'N/A')}\n\n"

            # 投資建議
            action = rec.get("action", "hold")
            action_emoji = {"buy": "🟢", "sell": "🔴", "hold": "🟡"}.get(action, "⚪")
            action_text = {"buy": "買入", "sell": "賣出", "hold": "持有"}.get(
                action, "觀望"
            )

            message += "**💡 投資建議：**\n"
            message += f"• 建議動作：{action_emoji} **{action_text}**\n"
            message += f"• 目標價：{rec.get('target_price', 'N/A')} 元\n"
            message += f"• 停損價：{rec.get('stop_loss', 'N/A')} 元\n"
            message += f"• 信心水平：{rec.get('confidence', 0)}%\n\n"

            # 風險評估
            risk_level = risk.get("level", "medium")
            risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(
                risk_level, "⚪"
            )

            message += "**⚠️ 風險評估：**\n"
            message += f"• 風險等級：{risk_emoji} {risk_level.upper()}\n"
            message += f"• 風險評分：{risk.get('score', 0)}/100\n"

            suggestions = [f"{stock_id} 估值", f"{stock_id} 產業", f"{stock_id} 股利"]

            return {"message": message, "data": data, "suggestions": suggestions}

        except Exception as e:
            logger.error(f"分析回應失敗: {e}")
            return {"message": f"分析 {stock_id} 時發生錯誤：{str(e)}"}

    async def _recommendation_response(self, stock_id: str) -> Dict:
        """投資建議回應"""
        try:
            result = await self.analyst.analyze(stock_id, include_ml=True)

            if not result.get("success"):
                return {"message": f"無法取得 {stock_id} 的建議。"}

            rec = result.get("data", {}).get("recommendation", {})
            risk = result.get("data", {}).get("risk_assessment", {})

            action = rec.get("action", "hold")
            action_emoji = {"buy": "🟢", "sell": "🔴", "hold": "🟡"}.get(action, "⚪")
            action_text = {"buy": "買入", "sell": "賣出", "hold": "持有"}.get(
                action, "觀望"
            )

            message = f"💡 **{stock_id} 投資建議**\n\n"
            message += f"**建議動作：** {action_emoji} **{action_text}**\n\n"
            message += f"**詳細建議：**\n"
            message += f"• 目標價：{rec.get('target_price', 'N/A')} 元\n"
            message += f"• 停損價：{rec.get('stop_loss', 'N/A')} 元\n"
            message += f"• 建議比例：{rec.get('position_size', 'N/A')}\n"
            message += f"• 持有期限：{rec.get('holding_period', 'N/A')}\n"
            message += f"• 信心水平：{rec.get('confidence', 0)}%\n\n"

            message += "**⚠️ 風險提醒：**\n"
            for factor in risk.get("factors", []):
                message += f"• {factor}\n"

            return {"message": message, "data": rec}

        except Exception as e:
            return {"message": f"取得建議時發生錯誤：{str(e)}"}

    async def _price_response(self, stock_id: str) -> Dict:
        """價格回應"""
        try:
            # 從 TWSE 取得即時報價
            quote = self.twse.get_stock_quote(stock_id)

            if not quote:
                return {"message": f"無法取得 {stock_id} 的即時報價。"}

            message = f"📊 **{stock_id} 即時報價**\n\n"
            message += f"**股票名稱：** {quote.get('name', stock_id)}\n"
            message += f"**目前價格：** {quote.get('price', 'N/A')} 元\n"
            message += f"**漲跌：** {quote.get('change', 0):+.1f} ({quote.get('change_percent', 0):+.2f}%)\n\n"
            message += f"**今日資訊：**\n"
            message += f"• 開盤：{quote.get('open', 'N/A')} 元\n"
            message += f"• 最高：{quote.get('high', 'N/A')} 元\n"
            message += f"• 最低：{quote.get('low', 'N/A')} 元\n"
            message += f"• 成交量：{quote.get('volume', 'N/A')} 張\n"

            return {"message": message, "data": quote}

        except Exception as e:
            return {"message": f"取得價格時發生錯誤：{str(e)}"}

    async def _valuation_response(self, stock_id: str) -> Dict:
        """估值回應"""
        try:
            result = self.valuation.get_valuation(stock_id)

            if not result.get("success"):
                return {"message": f"無法取得 {stock_id} 的估值資料。"}

            data = result.get("data", {})
            pe = data.get("pe_ratio", {})
            pb = data.get("pb_ratio", {})
            div = data.get("dividend_yield", {})
            rating = data.get("valuation_rating", {})

            message = f"📈 **{stock_id} 估值分析**\n\n"

            # 估值評級
            rating_label = rating.get("label", "未知")
            rating_emoji = {"低估": "🟢", "合理": "🟡", "中性": "⚪", "高估": "🔴"}.get(
                rating_label, "⚪"
            )

            message += f"**估值評級：** {rating_emoji} **{rating_label}**\n\n"

            message += "**主要指標：**\n"
            message += f"• 本益比 (PE)：{pe.get('trailing_pe', 'N/A')}\n"
            message += f"• 股價淨值比 (PB)：{pb.get('pb_ratio', 'N/A')}\n"
            message += f"• 股利殖利率：{div.get('dividend_yield', 'N/A')}%\n"
            message += (
                f"• EV/EBITDA：{data.get('ev_ebitda', {}).get('ev_ebitda', 'N/A')}\n"
            )
            message += f"• PEG：{data.get('peg_ratio', {}).get('peg_ratio', 'N/A')}\n\n"

            message += "**評估因素：**\n"
            for factor in rating.get("factors", []):
                message += f"• {factor}\n"

            return {"message": message, "data": data}

        except Exception as e:
            return {"message": f"取得估值時發生錯誤：{str(e)}"}

    async def _industry_response(self, stock_id: str) -> Dict:
        """產業比較回應"""
        try:
            result = self.industry.get_industry_analysis(stock_id)

            if not result.get("success"):
                return {"message": f"無法取得 {stock_id} 的產業比較資料。"}

            data = result.get("data", {})
            industry = data.get("industry", "未知")
            rankings = data.get("rankings", {})
            analysis = data.get("analysis", {})

            message = f"🏭 **{stock_id} 產業比較分析**\n\n"
            message += f"**所屬產業：** {industry}\n\n"

            message += "**產業排名：**\n"
            for metric, info in rankings.items():
                rank = info.get("rank", 0)
                total = info.get("total", 0)
                metric_name = {
                    "pe_ratio": "本益比",
                    "pb_ratio": "股價淨值比",
                    "dividend_yield": "股利殖利率",
                    "roe": "ROE",
                    "profit_margin": "淨利率",
                    "revenue_growth": "營收成長",
                }.get(metric, metric)

                rank_emoji = (
                    "🥇"
                    if rank == 1
                    else "🥈" if rank == 2 else "🥉" if rank == 3 else "📊"
                )
                message += f"• {metric_name}：{rank_emoji} 第 {rank}/{total} 名\n"

            message += f"\n**分析結論：**\n{analysis.get('summary', 'N/A')}\n\n"

            if analysis.get("strengths"):
                message += "**優勢：**\n"
                for s in analysis["strengths"]:
                    message += f"✅ {s}\n"

            if analysis.get("weaknesses"):
                message += "**劣勢：**\n"
                for w in analysis["weaknesses"]:
                    message += f"⚠️ {w}\n"

            return {"message": message, "data": data}

        except Exception as e:
            return {"message": f"取得產業比較時發生錯誤：{str(e)}"}

    async def _dividend_response(self, stock_id: str) -> Dict:
        """股利回應"""
        try:
            clean_id = stock_id.replace(".TW", "").replace(".TWO", "")
            result = self.dividend.get_dividend_data(clean_id)

            if not result.get("success"):
                return {"message": f"無法取得 {stock_id} 的股利資料。"}

            data = result.get("data", {})
            stats = data.get("statistics", {})
            fill = data.get("fill_analysis", {})

            message = f"💰 **{stock_id} 股利分析**\n\n"

            message += "**股利統計：**\n"
            message += f"• 平均現金股利：{stats.get('avg_cash_dividend', 'N/A')} 元\n"
            message += f"• 最高現金股利：{stats.get('max_cash_dividend', 'N/A')} 元\n"
            message += f"• 連續發放年數：{stats.get('consecutive_years', 'N/A')} 年\n"
            message += f"• 股利穩定性：{self._stability_text(stats.get('dividend_stability', 'unknown'))}\n"
            message += f"• 股利趨勢：{self._trend_text(stats.get('dividend_trend', 'unknown'))}\n\n"

            if fill:
                fill_rate = fill.get("fill_rate", 0)
                fill_rating = fill.get("fill_rating", "unknown")

                message += "**填息分析：**\n"
                message += f"• 填息率：{fill_rate}%\n"
                message += f"• 平均填息天數：{fill.get('avg_fill_days', 'N/A')} 天\n"
                message += f"• 填息評級：{self._fill_rating_text(fill_rating)}\n"

            return {"message": message, "data": data}

        except Exception as e:
            return {"message": f"取得股利時發生錯誤：{str(e)}"}

    async def _trend_response(self, stock_id: str) -> Dict:
        """趨勢回應"""
        try:
            result = await self.analyst.analyze(stock_id, include_ml=False)

            if not result.get("success"):
                return {"message": f"無法取得 {stock_id} 的趨勢資料。"}

            trend = result.get("data", {}).get("trend_analysis", {})

            message = f"📈 **{stock_id} 趨勢分析**\n\n"

            short = trend.get("short_term", "neutral")
            medium = trend.get("medium_term", "neutral")
            long = trend.get("long_term", "neutral")
            score = trend.get("score", 0)

            message += "**趨勢方向：**\n"
            message += (
                f"• 短期（5天）：{self._trend_emoji(short)} {self._trend_text(short)}\n"
            )
            message += f"• 中期（20天）：{self._trend_emoji(medium)} {self._trend_text(medium)}\n"
            message += f"• 長期（60天）：{self._trend_emoji(long)} {self._trend_text(long)}\n\n"

            message += f"**趨勢評分：** {score}/100\n\n"

            # 趨勢解讀
            if score >= 70:
                message += "**解讀：** 多頭排列，趨勢明確向上 🚀\n"
            elif score >= 50:
                message += "**解讀：** 中性偏多，可觀察後進場\n"
            elif score >= 30:
                message += "**解讀：** 中性偏空，建議觀望\n"
            else:
                message += "**解讀：** 空頭排列，建議避開 ⚠️\n"

            return {"message": message, "data": trend}

        except Exception as e:
            return {"message": f"取得趨勢時發生錯誤：{str(e)}"}

    async def _risk_response(self, stock_id: str) -> Dict:
        """風險回應"""
        try:
            result = await self.analyst.analyze(stock_id, include_ml=False)

            if not result.get("success"):
                return {"message": f"無法取得 {stock_id} 的風險資料。"}

            risk = result.get("data", {}).get("risk_assessment", {})

            level = risk.get("level", "medium")
            level_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(level, "⚪")

            message = f"⚠️ **{stock_id} 風險評估**\n\n"
            message += f"**風險等級：** {level_emoji} **{level.upper()}**\n"
            message += f"**風險評分：** {risk.get('score', 0)}/100\n\n"

            message += "**風險因素：**\n"
            for factor in risk.get("factors", []):
                message += f"• {factor}\n"

            message += "\n**風險管理建議：**\n"
            if level == "high":
                message += "• 建議減持或避開\n"
                message += "• 若持有，設定嚴格停損\n"
                message += "• 分散投資降低風險\n"
            elif level == "medium":
                message += "• 控制部位大小\n"
                message += "• 設定停損保護\n"
                message += "• 持續關注市場動態\n"
            else:
                message += "• 風險較低，可適度配置\n"
                message += "• 仍需設定停損\n"

            return {"message": message, "data": risk}

        except Exception as e:
            return {"message": f"取得風險時發生錯誤：{str(e)}"}

    async def _prediction_response(self, stock_id: str) -> Dict:
        """預測回應"""
        try:
            result = await self.analyst.analyze(stock_id, include_ml=True)

            if not result.get("success"):
                return {"message": f"無法取得 {stock_id} 的預測資料。"}

            ml = result.get("data", {}).get("ml_prediction", {})

            if not ml:
                return {"message": f"無法生成 {stock_id} 的預測，可能資料不足。"}

            trend = ml.get("trend", "neutral")
            expected_return = ml.get("expected_return", 0)
            model = ml.get("model", "N/A")
            confidence = ml.get("confidence", 0)

            message = f"🔮 **{stock_id} ML 預測**\n\n"
            message += (
                f"**預測趨勢：** {self._trend_emoji(trend)} {self._trend_text(trend)}\n"
            )
            message += f"**預期報酬：** {expected_return*100:+.1f}%\n"
            message += f"**預測模型：** {model}\n"
            message += f"**信心水平：** {confidence}%\n\n"

            message += "**各模型預測：**\n"
            for pred in ml.get("predictions", []):
                model_name = pred.get("model", "N/A")
                pred_trend = pred.get("trend", "neutral")
                message += f"• {model_name}：{self._trend_emoji(pred_trend)} {self._trend_text(pred_trend)}\n"

            message += "\n**⚠️ 注意事項：**\n"
            message += "• ML 預測僅供參考，非投資建議\n"
            message += "• 市場變化難以完全預測\n"
            message += "• 請結合其他分析做判斷\n"

            return {"message": message, "data": ml}

        except Exception as e:
            return {"message": f"取得預測時發生錯誤：{str(e)}"}

    async def _general_stock_response(self, stock_id: str) -> Dict:
        """一般股票查詢回應"""
        return {
            "message": f"你想了解 {stock_id} 的什麼資訊？\n\n"
            "你可以問我：\n"
            f"• 「分析 {stock_id}」- 綜合分析\n"
            f"• 「{stock_id} 建議」- 投資建議\n"
            f"• 「{stock_id} 估值」- 估值分析\n"
            f"• 「{stock_id} 股利」- 股利資訊",
            "suggestions": [f"分析 {stock_id}", f"{stock_id} 建議", f"{stock_id} 估值"],
        }

    def _general_response(self) -> Dict:
        """一般回應"""
        return {
            "message": "我不太理解你的問題。😅\n\n"
            "你可以試試：\n"
            "• 輸入股票代碼（如 2330）\n"
            "• 說「分析台積電」\n"
            "• 說「幫助」查看所有功能",
            "suggestions": ["幫助", "分析 2330", "2317 建議"],
        }

    def _ask_stock_id_response(self, action: str) -> Dict:
        """要求輸入股票代碼"""
        return {
            "message": f"請提供股票代碼，我才能幫你{action}。\n\n"
            f"例如：「{action} 2330」或「{action} 台積電」",
            "suggestions": [f"{action} 2330", f"{action} 2317", f"{action} 2454"],
        }

    def _trend_emoji(self, trend: str) -> str:
        """趨勢表情符號"""
        return {
            "up": "📈",
            "down": "📉",
            "neutral": "➡️",
            "bullish": "🚀",
            "bearish": "🐻",
        }.get(trend, "➡️")

    def _trend_text(self, trend: str) -> str:
        """趨勢文字"""
        return {
            "up": "上漲",
            "down": "下跌",
            "neutral": "盤整",
            "bullish": "多頭",
            "bearish": "空頭",
            "increasing": "上升",
            "decreasing": "下降",
            "stable": "穩定",
        }.get(trend, "未知")

    def _stability_text(self, stability: str) -> str:
        """穩定性文字"""
        return {
            "very_stable": "非常穩定 ⭐⭐⭐",
            "stable": "穩定 ⭐⭐",
            "moderate": "中等 ⭐",
            "volatile": "波動",
            "unknown": "未知",
        }.get(stability, "未知")

    def _fill_rating_text(self, rating: str) -> str:
        """填息評級文字"""
        return {
            "excellent": "優秀 ⭐⭐⭐",
            "good": "良好 ⭐⭐",
            "average": "普通 ⭐",
            "poor": "較差",
            "unknown": "未知",
        }.get(rating, "未知")

    def get_conversation_history(self) -> List[Dict]:
        """取得對話歷史"""
        return self.conversation_history

    def clear_history(self):
        """清除對話歷史"""
        self.conversation_history = []


# 全局實例
_chatbot = None


def get_stock_chatbot() -> StockChatbot:
    """取得 StockChatbot 單例"""
    global _chatbot
    if _chatbot is None:
        _chatbot = StockChatbot()
    return _chatbot
