"""
台灣股票分析工具 - 通知服務
支援 Discord/Line 通知
參考 taiwan-quant-project 的 notification/line_notify.py
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from loguru import logger


class NotificationService:
    """通知服務"""

    def __init__(self):
        """初始化通知服務"""
        # Discord 設定
        self.discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "")

        # Line 設定
        self.line_notify_token = os.getenv("LINE_NOTIFY_TOKEN", "")

        # 通知歷史
        self.notification_history = []

    def send_discord_message(
        self,
        content: str,
        embeds: List[Dict] = None,
        username: str = "台灣股票分析工具",
        avatar_url: str = None,
    ) -> bool:
        """
        發送 Discord 訊息

        Args:
            content: 訊息內容
            embeds: 嵌入式訊息
            username: 使用者名稱
            avatar_url: 頭像 URL

        Returns:
            是否成功
        """
        try:
            if not self.discord_webhook_url:
                logger.warning("Discord webhook URL 未設定")
                return False

            # 準備資料
            data = {
                "content": content,
                "username": username,
                "allowed_mentions": {"parse": []},  # 避免意外 ping
            }

            if embeds:
                data["embeds"] = embeds

            if avatar_url:
                data["avatar_url"] = avatar_url

            # 發送請求
            response = requests.post(self.discord_webhook_url, json=data, timeout=10)

            if response.status_code == 204:
                logger.info(f"Discord 訊息發送成功")

                # 記錄歷史
                self.notification_history.append(
                    {
                        "type": "discord",
                        "content": (
                            content[:100] + "..." if len(content) > 100 else content
                        ),
                        "timestamp": datetime.now().isoformat(),
                        "success": True,
                    }
                )

                return True
            else:
                logger.error(f"Discord 訊息發送失敗: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Discord 訊息發送失敗: {e}")
            return False

    def send_discord_stock_alert(
        self,
        stock_id: str,
        stock_name: str,
        alert_type: str,
        message: str,
        price: float = None,
        change_percent: float = None,
    ) -> bool:
        """
        發送 Discord 股票警報

        Args:
            stock_id: 股票代碼
            stock_name: 股票名稱
            alert_type: 警報類型
            message: 訊息內容
            price: 目前價格
            change_percent: 漲跌幅

        Returns:
            是否成功
        """
        try:
            # 建立嵌入式訊息
            embed = {
                "title": f"🚨 {alert_type}: {stock_name} ({stock_id})",
                "description": message,
                "color": (
                    0xFF0000
                    if "賣出" in alert_type or "下跌" in alert_type
                    else 0x00FF00
                ),
                "fields": [],
                "timestamp": datetime.now().isoformat(),
            }

            if price:
                embed["fields"].append(
                    {"name": "目前價格", "value": f"NT$ {price:.2f}", "inline": True}
                )

            if change_percent:
                color = "🟢" if change_percent >= 0 else "🔴"
                embed["fields"].append(
                    {
                        "name": "漲跌幅",
                        "value": f"{color} {change_percent:+.2f}%",
                        "inline": True,
                    }
                )

            embed["fields"].append(
                {
                    "name": "時間",
                    "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "inline": False,
                }
            )

            return self.send_discord_message(content="", embeds=[embed])

        except Exception as e:
            logger.error(f"Discord 股票警報發送失敗: {e}")
            return False

    def send_discord_report(self, report_type: str, report_data: Dict) -> bool:
        """
        發送 Discord 報告

        Args:
            report_type: 報告類型
            report_data: 報告資料

        Returns:
            是否成功
        """
        try:
            # 建立嵌入式訊息
            embed = {
                "title": f"📊 {report_type}",
                "description": report_data.get("summary", ""),
                "color": 0x667EEA,
                "fields": [],
                "timestamp": datetime.now().isoformat(),
            }

            # 添加投資建議
            advice = report_data.get("investment_advice", {})
            if advice:
                embed["fields"].append(
                    {
                        "name": "市場建議",
                        "value": advice.get("market_advice", "N/A"),
                        "inline": False,
                    }
                )

                embed["fields"].append(
                    {
                        "name": "建議部位",
                        "value": advice.get("position_size", "N/A"),
                        "inline": True,
                    }
                )

                embed["fields"].append(
                    {
                        "name": "整體策略",
                        "value": advice.get("overall_strategy", "N/A"),
                        "inline": True,
                    }
                )

            # 添加選股推薦
            recommendations = advice.get("stock_recommendations", [])
            if recommendations:
                stock_list = "\n".join(
                    [
                        f"{i+1}. {rec['stock_name']} ({rec['stock_id']}) - 分數: {rec['composite_score']:.2f}"
                        for i, rec in enumerate(recommendations[:5])
                    ]
                )

                embed["fields"].append(
                    {"name": "⭐ 選股推薦", "value": stock_list, "inline": False}
                )

            # 添加風險提示
            warnings = report_data.get("risk_warnings", [])
            if warnings:
                warning_text = "\n".join(warnings[:3])
                embed["fields"].append(
                    {"name": "⚠️ 風險提示", "value": warning_text, "inline": False}
                )

            return self.send_discord_message(content="", embeds=[embed])

        except Exception as e:
            logger.error(f"Discord 報告發送失敗: {e}")
            return False

    def send_line_message(self, message: str) -> bool:
        """
        發送 Line 訊息

        Args:
            message: 訊息內容

        Returns:
            是否成功
        """
        try:
            if not self.line_notify_token:
                logger.warning("Line Notify token 未設定")
                return False

            # Line Notify API
            url = "https://notify-api.line.me/api/notify"

            headers = {
                "Authorization": f"Bearer {self.line_notify_token}",
                "Content-Type": "application/x-www-form-urlencoded",
            }

            data = {"message": message}

            response = requests.post(url, headers=headers, data=data, timeout=10)

            if response.status_code == 200:
                logger.info(f"Line 訊息發送成功")

                # 記錄歷史
                self.notification_history.append(
                    {
                        "type": "line",
                        "content": (
                            message[:100] + "..." if len(message) > 100 else message
                        ),
                        "timestamp": datetime.now().isoformat(),
                        "success": True,
                    }
                )

                return True
            else:
                logger.error(f"Line 訊息發送失敗: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Line 訊息發送失敗: {e}")
            return False

    def send_line_stock_alert(
        self,
        stock_id: str,
        stock_name: str,
        alert_type: str,
        message: str,
        price: float = None,
        change_percent: float = None,
    ) -> bool:
        """
        發送 Line 股票警報

        Args:
            stock_id: 股票代碼
            stock_name: 股票名稱
            alert_type: 警報類型
            message: 訊息內容
            price: 目前價格
            change_percent: 漲跌幅

        Returns:
            是否成功
        """
        try:
            # 建立訊息
            lines = [
                f"🚨 {alert_type}: {stock_name} ({stock_id})",
                f"",
                f"📝 {message}",
            ]

            if price:
                lines.append(f"💰 目前價格: NT$ {price:.2f}")

            if change_percent:
                color = "🟢" if change_percent >= 0 else "🔴"
                lines.append(f"{color} 漲跌幅: {change_percent:+.2f}%")

            lines.append(f"")
            lines.append(f"⏰ 時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            message = "\n".join(lines)

            return self.send_line_message(message)

        except Exception as e:
            logger.error(f"Line 股票警報發送失敗: {e}")
            return False

    def send_line_report(self, report_type: str, report_data: Dict) -> bool:
        """
        發送 Line 報告

        Args:
            report_type: 報告類型
            report_data: 報告資料

        Returns:
            是否成功
        """
        try:
            # 建立訊息
            lines = [
                f"📊 {report_type}",
                f"",
                f"📋 執行摘要:",
                report_data.get("summary", ""),
                f"",
            ]

            # 添加投資建議
            advice = report_data.get("investment_advice", {})
            if advice:
                lines.append(f"💡 投資建議:")
                lines.append(f"  • 市場建議: {advice.get('market_advice', 'N/A')}")
                lines.append(f"  • 建議部位: {advice.get('position_size', 'N/A')}")
                lines.append(f"  • 整體策略: {advice.get('overall_strategy', 'N/A')}")
                lines.append(f"")

            # 添加選股推薦
            recommendations = advice.get("stock_recommendations", [])
            if recommendations:
                lines.append(f"⭐ 選股推薦:")
                for i, rec in enumerate(recommendations[:5]):
                    lines.append(
                        f"  {i+1}. {rec['stock_name']} ({rec['stock_id']}) - 分數: {rec['composite_score']:.2f}"
                    )
                lines.append(f"")

            # 添加風險提示
            warnings = report_data.get("risk_warnings", [])
            if warnings:
                lines.append(f"⚠️ 風險提示:")
                for warning in warnings[:3]:
                    lines.append(f"  • {warning}")

            message = "\n".join(lines)

            return self.send_line_message(message)

        except Exception as e:
            logger.error(f"Line 報告發送失敗: {e}")
            return False

    def get_notification_history(self, limit: int = 50) -> List[Dict]:
        """取得通知歷史"""
        return self.notification_history[-limit:]

    def clear_notification_history(self):
        """清除通知歷史"""
        self.notification_history = []


# 全局實例
_notification_service = None


def get_notification_service() -> NotificationService:
    """取得 NotificationService 單例"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
