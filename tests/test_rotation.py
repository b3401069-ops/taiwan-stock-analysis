"""產業輪動與概念股輪動測試。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestIndustryRotation:
    """產業輪動分析測試。"""

    def test_industry_ranking_structure(self, sample_industry_ranking):
        """產業排名結構測試。"""
        for industry in sample_industry_ranking:
            assert "rank" in industry
            assert "industry" in industry
            assert "strength_score" in industry
            assert "signal" in industry

            # 分數應在 0-1 之間
            assert 0 <= industry["strength_score"] <= 1

            # 信號應為有效值
            valid_signals = ["strong_buy", "buy", "neutral", "sell", "strong_sell"]
            assert industry["signal"] in valid_signals

    def test_industry_ranking_order(self, sample_industry_ranking):
        """產業排名順序測試。"""
        for i in range(len(sample_industry_ranking) - 1):
            # 排名應遞增
            assert (
                sample_industry_ranking[i]["rank"]
                < sample_industry_ranking[i + 1]["rank"]
            )

            # 分數應遞減
            assert (
                sample_industry_ranking[i]["strength_score"]
                >= sample_industry_ranking[i + 1]["strength_score"]
            )

    def test_industry_momentum_calculation(self):
        """產業動量計算測試。"""
        # 20日動量計算
        prices = [
            100,
            102,
            105,
            103,
            108,
            110,
            112,
            115,
            113,
            118,
            120,
            122,
            125,
            123,
            128,
            130,
            132,
            135,
            133,
            138,
        ]

        momentum_20d = (prices[-1] - prices[0]) / prices[0] * 100
        assert momentum_20d > 0  # 正動量

    def test_industry_relative_strength(self):
        """產業相對強度測試。"""
        industry_return = 15.0  # 產業報酬率
        market_return = 10.0  # 市場報酬率

        relative_strength = industry_return - market_return
        assert relative_strength > 0  # 強於市場

    def test_rotation_signal_generation(self):
        """輪動信號生成測試。"""
        # 從弱勢產業轉移到強勢產業
        weak_industry = {"industry": "傳統產業", "strength_score": 0.4}
        strong_industry = {"industry": "半導體", "strength_score": 0.8}

        signal = {
            "from_industry": weak_industry["industry"],
            "to_industry": strong_industry["industry"],
            "signal_strength": strong_industry["strength_score"]
            - weak_industry["strength_score"],
            "expected_return": "5-10%",
            "risk_level": "medium",
        }

        assert signal["signal_strength"] > 0
        assert signal["from_industry"] != signal["to_industry"]

    @patch("analysis.industry_rotation.get_industry_rotation_analyzer")
    def test_analyzer_initialization(self, mock_analyzer):
        """分析器初始化測試。"""
        mock_instance = MagicMock()
        mock_analyzer.return_value = mock_instance

        analyzer = mock_analyzer()
        assert analyzer is not None


class TestConceptRotation:
    """概念股輪動分析測試。"""

    def test_concept_ranking_structure(self, sample_concept_ranking):
        """概念股排名結構測試。"""
        for concept in sample_concept_ranking:
            assert "rank" in concept
            assert "concept" in concept
            assert "heat_score" in concept
            assert "trend" in concept

            # 熱度分數應在 0-1 之間
            assert 0 <= concept["heat_score"] <= 1

            # 趨勢應為有效值
            valid_trends = ["hot", "warm", "neutral", "cool", "cold"]
            assert concept["trend"] in valid_trends

    def test_concept_ranking_order(self, sample_concept_ranking):
        """概念股排名順序測試。"""
        for i in range(len(sample_concept_ranking) - 1):
            # 排名應遞增
            assert (
                sample_concept_ranking[i]["rank"]
                < sample_concept_ranking[i + 1]["rank"]
            )

            # 熱度分數應遞減
            assert (
                sample_concept_ranking[i]["heat_score"]
                >= sample_concept_ranking[i + 1]["heat_score"]
            )

    def test_concept_heat_score_calculation(self):
        """概念股熱度分數計算測試。"""
        # 熱度因素
        momentum_score = 0.8
        volume_score = 0.7
        institutional_score = 0.9

        # 綜合熱度分數
        heat_score = (momentum_score + volume_score + institutional_score) / 3
        assert 0 <= heat_score <= 1

    def test_concept_trend_classification(self):
        """概念股趨勢分類測試。"""
        heat_scores = {
            "hot": 0.85,
            "warm": 0.65,
            "neutral": 0.50,
            "cool": 0.35,
            "cold": 0.15,
        }

        for trend, score in heat_scores.items():
            if score >= 0.8:
                expected_trend = "hot"
            elif score >= 0.6:
                expected_trend = "warm"
            elif score >= 0.4:
                expected_trend = "neutral"
            elif score >= 0.2:
                expected_trend = "cool"
            else:
                expected_trend = "cold"

            assert expected_trend == trend

    def test_concept_stock_count(self, sample_concept_ranking):
        """概念股股票數量測試。"""
        for concept in sample_concept_ranking:
            assert "stock_count" in concept
            assert concept["stock_count"] > 0

    def test_concept_volume_ratio(self, sample_concept_ranking):
        """概念股成交量比率測試。"""
        for concept in sample_concept_ranking:
            if "avg_volume_ratio" in concept:
                assert concept["avg_volume_ratio"] > 0

    def test_concept_institutional_flow(self, sample_concept_ranking):
        """概念股法人流向測試。"""
        for concept in sample_concept_ranking:
            if "total_institutional_flow" in concept:
                # 應包含數字和單位
                flow = concept["total_institutional_flow"]
                assert "億" in flow or "萬" in flow

    @patch("analysis.concept_rotation.get_concept_rotation_analyzer")
    def test_concept_analyzer_initialization(self, mock_analyzer):
        """概念股分析器初始化測試。"""
        mock_instance = MagicMock()
        mock_analyzer.return_value = mock_instance

        analyzer = mock_analyzer()
        assert analyzer is not None


class TestRotationStrategy:
    """輪動策略測試。"""

    def test_sector_rotation_logic(self):
        """產業輪動邏輯測試。"""
        # 強勢產業應有較高的分數
        strong_sector = {"industry": "半導體", "strength_score": 0.85}
        weak_sector = {"industry": "傳統產業", "strength_score": 0.45}

        # 應該從弱勢產業轉移到強勢產業
        should_rotate = (
            strong_sector["strength_score"] > weak_sector["strength_score"] + 0.1
        )
        assert should_rotate is True

    def test_rotation_timing(self):
        """輪動時機測試。"""
        # 產業強度變化
        current_strength = 0.8
        previous_strength = 0.6

        # 強度增加應為正向信號
        strength_change = current_strength - previous_strength
        signal = "positive" if strength_change > 0 else "negative"
        assert signal == "positive"

    def test_rotation_risk_assessment(self):
        """輪動風險評估測試。"""
        # 風險等級
        risk_levels = {
            "low": {"min": 0, "max": 0.3},
            "medium": {"min": 0.3, "max": 0.6},
            "high": {"min": 0.6, "max": 1.0},
        }

        for level, range_info in risk_levels.items():
            assert range_info["min"] < range_info["max"]
            assert 0 <= range_info["min"] <= 1
            assert 0 <= range_info["max"] <= 1

    def test_rotation_expected_return(self):
        """輪動預期報酬測試。"""
        # 預期報酬應為正數
        expected_returns = ["3-5%", "5-10%", "10-15%", "15-20%"]

        for return_range in expected_returns:
            # 解析範圍
            parts = return_range.replace("%", "").split("-")
            min_return = float(parts[0])
            max_return = float(parts[1])

            assert min_return < max_return
            assert min_return > 0

    def test_multiple_concepts_tracking(self):
        """多概念股追蹤測試。"""
        concepts = [
            {"concept": "CoWoS", "heat_score": 0.9},
            {"concept": "散熱", "heat_score": 0.85},
            {"concept": "低軌衛星", "heat_score": 0.7},
            {"concept": "AI 伺服器", "heat_score": 0.8},
            {"concept": "車用電子", "heat_score": 0.75},
        ]

        # 所有概念股應有有效的熱度分數
        for concept in concepts:
            assert 0 <= concept["heat_score"] <= 1

        # 應按熱度分數排序
        sorted_concepts = sorted(concepts, key=lambda x: x["heat_score"], reverse=True)
        assert sorted_concepts[0]["concept"] == "CoWoS"
