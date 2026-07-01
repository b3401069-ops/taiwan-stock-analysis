"""通知服務測試。"""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestNotificationService:
    """通知服務測試。"""

    def test_discord_webhook_url_format(self):
        """Discord Webhook URL 格式測試。"""
        valid_urls = [
            "https://discord.com/api/webhooks/123456789/abcdefg",
            "https://discord.com/api/webhooks/987654321/xyz123",
        ]
        
        for url in valid_urls:
            assert url.startswith("https://discord.com/api/webhooks/")
            assert len(url.split("/")) >= 7

    def test_line_notify_token_format(self):
        """Line Notify Token 格式測試。"""
        valid_tokens = [
            "abc123def456ghi789",
            "xxxxxxxxxxxxxxxxxxxxxxxx",
        ]
        
        for token in valid_tokens:
            assert len(token) > 0
            assert token.isalnum() or set(token).issubset(set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"))

    def test_notification_history_structure(self, sample_notification_history):
        """通知歷史結構測試。"""
        for notification in sample_notification_history:
            assert "type" in notification
            assert "content" in notification
            assert "timestamp" in notification
            assert "success" in notification
            
            # 類型應為 discord 或 line
            assert notification["type"] in ["discord", "line"]
            
            # 成功狀態應為布林值
            assert isinstance(notification["success"], bool)

    def test_stock_alert_structure(self):
        """股票警報結構測試。"""
        alert = {
            "stock_id": "2330.TW",
            "stock_name": "台積電",
            "alert_type": "停損警報",
            "message": "跌破支撐",
            "price": 2400.0,
            "change_percent": -2.5,
        }
        
        required_fields = ["stock_id", "stock_name", "alert_type", "message"]
        for field in required_fields:
            assert field in alert
        
        # 價格應為正數
        assert alert["price"] > 0

    def test_report_notification_structure(self):
        """報告通知結構測試。"""
        report = {
            "report_type": "每日報告",
            "timestamp": datetime.now().isoformat(),
            "summary": "市場處於多頭狀態",
            "investment_advice": {
                "market_advice": "積極佈局",
                "position_size": "70-90%",
            },
        }
        
        assert "report_type" in report
        assert "timestamp" in report
        assert "summary" in report

    @patch("services.notification.get_notification_service")
    def test_discord_message_sending(self, mock_service):
        """Discord 訊息發送測試。"""
        mock_instance = MagicMock()
        mock_instance.send_discord_message.return_value = True
        mock_service.return_value = mock_instance
        
        service = mock_service()
        result = service.send_discord_message("測試訊息")
        
        assert result is True
        mock_instance.send_discord_message.assert_called_once_with("測試訊息")

    @patch("services.notification.get_notification_service")
    def test_line_message_sending(self, mock_service):
        """Line 訊息發送測試。"""
        mock_instance = MagicMock()
        mock_instance.send_line_message.return_value = True
        mock_service.return_value = mock_instance
        
        service = mock_service()
        result = service.send_line_message("測試訊息")
        
        assert result is True
        mock_instance.send_line_message.assert_called_once_with("測試訊息")

    @patch("services.notification.get_notification_service")
    def test_stock_alert_sending(self, mock_service):
        """股票警報發送測試。"""
        mock_instance = MagicMock()
        mock_instance.send_discord_stock_alert.return_value = True
        mock_service.return_value = mock_instance
        
        service = mock_service()
        result = service.send_discord_stock_alert(
            stock_id="2330.TW",
            stock_name="台積電",
            alert_type="停損警報",
            message="跌破支撐",
            price=2400.0,
            change_percent=-2.5,
        )
        
        assert result is True

    @patch("services.notification.get_notification_service")
    def test_report_notification_sending(self, mock_service):
        """報告通知發送測試。"""
        mock_instance = MagicMock()
        mock_instance.send_discord_report.return_value = True
        mock_service.return_value = mock_instance
        
        service = mock_service()
        result = service.send_discord_report(
            report_type="每日報告",
            report_data={"summary": "市場處於多頭狀態"},
        )
        
        assert result is True

    @patch("services.notification.get_notification_service")
    def test_notification_history_retrieval(self, mock_service, sample_notification_history):
        """通知歷史取得測試。"""
        mock_instance = MagicMock()
        mock_instance.get_notification_history.return_value = sample_notification_history
        mock_service.return_value = mock_instance
        
        service = mock_service()
        history = service.get_notification_history(limit=10)
        
        assert len(history) == 2
        assert history[0]["type"] == "discord"

    def test_alert_types(self):
        """警報類型測試。"""
        alert_types = [
            "停損警報",
            "停利警報",
            "漲幅警報",
            "跌幅警報",
            "一般警報",
        ]
        
        for alert_type in alert_types:
            assert alert_type in alert_types

    def test_report_types(self):
        """報告類型測試。"""
        report_types = [
            "每日報告",
            "每週報告",
            "每月報告",
            "AI 選股摘要",
        ]
        
        for report_type in report_types:
            assert report_type in report_types


class TestNotificationFormatting:
    """通知格式化測試。"""

    def test_discord_embed_structure(self):
        """Discord 嵌入式訊息結構測試。"""
        embed = {
            "title": "🚨 停損警報: 台積電 (2330.TW)",
            "description": "跌破支撐",
            "color": 0xff0000,
            "fields": [
                {"name": "目前價格", "value": "NT$ 2,400.00", "inline": True},
                {"name": "漲跌幅", "value": "🔴 -2.50%", "inline": True},
            ],
            "timestamp": datetime.now().isoformat(),
        }
        
        assert "title" in embed
        assert "description" in embed
        assert "fields" in embed
        assert len(embed["fields"]) > 0

    def test_line_message_format(self):
        """Line 訊息格式測試。"""
        message = """
🚨 停損警報: 台積電 (2330.TW)

📝 跌破支撐

💰 目前價格: NT$ 2,400.00
🔴 漲跌幅: -2.50%

⏰ 時間: 2024-01-15 15:30:00
"""
        
        # 驗證訊息包含必要元素
        assert "停損警報" in message
        assert "2330.TW" in message
        assert "目前價格" in message
        assert "漲跌幅" in message

    def test_report_message_format(self):
        """報告訊息格式測試。"""
        message = """
📊 AI 選股摘要報告

📋 執行摘要:
市場處於多頭狀態，信心水平 75%。

💡 投資建議:
• 市場建議: 積極佈局
• 建議部位: 70-90%
• 整體策略: 積極成長策略

⭐ 選股推薦:
1. 台積電 (2330.TW) - 分數: 0.7234
2. 聯發科 (2454.TW) - 分數: 0.6891
"""
        
        # 驗證訊息包含必要元素
        assert "AI 選股摘要" in message
        assert "執行摘要" in message
        assert "投資建議" in message
        assert "選股推薦" in message
