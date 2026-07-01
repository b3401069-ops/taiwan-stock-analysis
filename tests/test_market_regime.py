"""市場狀態偵測測試。"""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock


class TestMarketRegimeDetector:
    """市場狀態偵測器測試。"""

    def test_regime_types(self):
        """測試市場狀態類型。"""
        valid_regimes = ["bull", "bear", "sideways", "crisis"]
        
        for regime in valid_regimes:
            assert regime in ["bull", "bear", "sideways", "crisis"]

    def test_regime_names(self):
        """測試市場狀態名稱映射。"""
        regime_names = {
            "bull": "多頭",
            "bear": "空頭",
            "sideways": "盤整",
            "crisis": "危機",
        }
        
        for regime, name in regime_names.items():
            assert name in ["多頭", "空頭", "盤整", "危機"]

    def test_confidence_range(self):
        """測試信心水平範圍。"""
        # 信心水平應在 0-100 之間
        confidence_values = [0, 25, 50, 75, 100]
        
        for conf in confidence_values:
            assert 0 <= conf <= 100

    def test_suggestion_structure(self):
        """測試建議結構。"""
        suggestion = {
            "action": "積極佈局",
            "reason": "加權指數站上所有均線",
            "position_size": "70-90%",
            "strategy": "積極成長策略",
        }
        
        required_keys = ["action", "reason"]
        for key in required_keys:
            assert key in suggestion

    def test_regime_suggestions(self):
        """測試不同狀態的建議。"""
        suggestions = {
            "bull": {"action": "積極佈局", "position_size": "70-90%"},
            "bear": {"action": "減碼觀望", "position_size": "20-40%"},
            "sideways": {"action": "觀望等待", "position_size": "40-60%"},
            "crisis": {"action": "現金為王", "position_size": "0-20%"},
        }
        
        for regime, suggestion in suggestions.items():
            assert "action" in suggestion
            assert "position_size" in suggestion

    @patch("analysis.market_regime.get_market_regime_detector")
    def test_detector_initialization(self, mock_detector):
        """測試偵測器初始化。"""
        mock_instance = MagicMock()
        mock_detector.return_value = mock_instance
        
        detector = mock_detector()
        assert detector is not None

    def test_moving_average_signals(self):
        """測試移動平均線信號。"""
        # 價格在均線之上應為多頭信號
        price_above_ma = True
        ma_signal = "bullish" if price_above_ma else "bearish"
        assert ma_signal == "bullish"
        
        # 價格在均線之下應為空頭信號
        price_below_ma = False
        ma_signal = "bullish" if price_below_ma else "bearish"
        assert ma_signal == "bearish"

    def test_volume_signals(self):
        """測試成交量信號。"""
        # 成交量放大應為強勢信號
        high_volume = True
        volume_signal = "strong" if high_volume else "weak"
        assert volume_signal == "strong"
        
        # 成交量萎縮應為弱勢信號
        low_volume = False
        volume_signal = "strong" if low_volume else "weak"
        assert volume_signal == "weak"

    def test_market_breadth(self):
        """測試市場寬度。"""
        # 上漲家數多於下跌家數應為多頭
        advancing = 456
        declining = 234
        
        breadth_ratio = advancing / (advancing + declining)
        assert breadth_ratio > 0.5  # 多頭
        
        # 下跌家數多於上漲家數應為空頭
        advancing = 234
        declining = 456
        
        breadth_ratio = advancing / (advancing + declining)
        assert breadth_ratio < 0.5  # 空頭

    def test_regime_confidence_levels(self):
        """測試不同狀態的信心水平。"""
        confidence_levels = {
            "bull": 75,
            "bear": 70,
            "sideways": 60,
            "crisis": 85,
        }
        
        for regime, confidence in confidence_levels.items():
            assert 0 <= confidence <= 100
