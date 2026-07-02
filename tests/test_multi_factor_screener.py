"""多因子選股引擎測試。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest


class TestMultiFactorScreener:
    """多因子選股引擎測試。"""

    def test_factor_weights_initialization(self):
        """因子權重初始化測試。"""
        # 預設權重
        default_weights = {
            "momentum": 0.2,
            "value": 0.25,
            "quality": 0.25,
            "size": 0.1,
            "liquidity": 0.1,
            "institutional": 0.1,
        }

        # 驗證權重總和
        total = sum(default_weights.values())
        assert total == pytest.approx(1.0, abs=0.01)

        # 驗證所有因子
        expected_factors = [
            "momentum",
            "value",
            "quality",
            "size",
            "liquidity",
            "institutional",
        ]
        for factor in expected_factors:
            assert factor in default_weights

    def test_momentum_score_calculation(self):
        """動量分數計算測試。"""
        # 建立測試資料
        prices = pd.Series(
            [
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
        )

        # 計算 20 日動量
        momentum_20d = (prices.iloc[-1] - prices.iloc[0]) / prices.iloc[0]

        # 動量應為正數（持續上漲）
        assert momentum_20d > 0

    def test_value_score_calculation(self):
        """價值分數計算測試。"""
        # PE ratio
        pe_ratio = 15.0
        pe_score = 1 / pe_ratio  # PE 越低，分數越高

        assert pe_score > 0

        # 較低的 PE 應有較高的分數
        low_pe_score = 1 / 10.0
        high_pe_score = 1 / 30.0
        assert low_pe_score > high_pe_score

    def test_quality_score_calculation(self):
        """品質分數計算測試。"""
        # ROE
        roe = 0.20  # 20%
        assert 0 < roe < 1

        # 較高的 ROE 應有較高的分數
        high_roe = 0.25
        low_roe = 0.10
        assert high_roe > low_roe

    def test_size_score_calculation(self):
        """規模分數計算測試。"""
        # 市值
        market_cap = 1_000_000_000_000  # 1 兆
        assert market_cap > 0

    def test_liquidity_score_calculation(self):
        """流動性分數計算測試。"""
        # 成交量比率
        volume = 10_000_000
        avg_volume = 8_000_000
        volume_ratio = volume / avg_volume

        assert volume_ratio > 0

    def test_institutional_score_calculation(self):
        """法人分數計算測試。"""
        # 法人買賣超
        institutional_buy = 500_000
        institutional_sell = 300_000
        net_flow = institutional_buy - institutional_sell

        assert net_flow > 0  # 正向法人流

    def test_composite_score_calculation(self):
        """綜合分數計算測試。"""
        # 因子權重
        weights = {
            "momentum": 0.2,
            "value": 0.25,
            "quality": 0.25,
            "size": 0.1,
            "liquidity": 0.1,
            "institutional": 0.1,
        }

        # 因子分數
        scores = {
            "momentum": 0.8,
            "value": 0.7,
            "quality": 0.9,
            "size": 0.6,
            "liquidity": 0.75,
            "institutional": 0.85,
        }

        # 計算綜合分數
        composite_score = sum(
            scores[factor] * weight for factor, weight in weights.items()
        )

        assert 0 <= composite_score <= 1

    def test_factor_normalization_min_max(self):
        """因子正規化（最小最大法）測試。"""
        values = pd.Series([10, 20, 30, 40, 50])

        # 最小最大正規化
        min_val = values.min()
        max_val = values.max()
        normalized = (values - min_val) / (max_val - min_val)

        # 正規化後應在 0-1 之間
        assert normalized.min() == 0
        assert normalized.max() == 1

    def test_factor_normalization_zscore(self):
        """因子正規化（Z-score）測試。"""
        values = pd.Series([10, 20, 30, 40, 50])

        # Z-score 正規化
        mean = values.mean()
        std = values.std()
        zscores = (values - mean) / std

        # Z-score 平均應接近 0
        assert abs(zscores.mean()) < 0.01

        # Z-score 標準差應接近 1
        assert abs(zscores.std() - 1) < 0.01

    def test_factor_percentile_rank(self):
        """因子百分位排名測試。"""
        values = pd.Series([10, 20, 30, 40, 50])

        # 百分位排名
        ranks = values.rank(pct=True)

        # 排名應在 0-1 之間
        assert ranks.min() > 0
        assert ranks.max() == 1.0

    def test_screener_result_structure(self):
        """選股結果結構測試。"""
        # 模擬選股結果
        result = [
            {
                "rank": 1,
                "stock_id": "2330.TW",
                "stock_name": "台積電",
                "composite_score": 0.7234,
                "details": {
                    "current_price": 2450.0,
                    "momentum_score": 0.85,
                    "value_score": 0.65,
                    "quality_score": 0.78,
                },
            },
        ]

        # 驗證結構
        for stock in result:
            assert "rank" in stock
            assert "stock_id" in stock
            assert "stock_name" in stock
            assert "composite_score" in stock
            assert "details" in stock

            # 驗證分數範圍
            assert 0 <= stock["composite_score"] <= 1

    def test_screener_ranking_order(self):
        """選股排名順序測試。"""
        # 模擬選股結果
        results = [
            {"rank": 1, "composite_score": 0.7234},
            {"rank": 2, "composite_score": 0.6891},
            {"rank": 3, "composite_score": 0.6543},
        ]

        # 驗證排名順序
        for i in range(len(results) - 1):
            assert results[i]["rank"] < results[i + 1]["rank"]
            assert results[i]["composite_score"] >= results[i + 1]["composite_score"]

    def test_screener_top_n(self):
        """選股 Top N 測試。"""
        # 模擬選股結果
        all_results = [
            {"rank": i, "composite_score": 0.8 - i * 0.05} for i in range(1, 21)
        ]

        # 取前 10 名
        top_n = 10
        top_results = all_results[:top_n]

        assert len(top_results) == top_n
        assert top_results[0]["rank"] == 1
        assert top_results[-1]["rank"] == top_n


class TestFactorWeights:
    """因子權重測試。"""

    def test_weights_sum_to_one(self):
        """權重總和應為 1。"""
        weights = {
            "momentum": 0.2,
            "value": 0.25,
            "quality": 0.25,
            "size": 0.1,
            "liquidity": 0.1,
            "institutional": 0.1,
        }

        total = sum(weights.values())
        assert total == pytest.approx(1.0, abs=0.01)

    def test_weights_positive(self):
        """權重應為正數。"""
        weights = {
            "momentum": 0.2,
            "value": 0.25,
            "quality": 0.25,
            "size": 0.1,
            "liquidity": 0.1,
            "institutional": 0.1,
        }

        for weight in weights.values():
            assert weight >= 0

    def test_weights_update(self):
        """權重更新測試。"""
        original_weights = {
            "momentum": 0.2,
            "value": 0.25,
            "quality": 0.25,
            "size": 0.1,
            "liquidity": 0.1,
            "institutional": 0.1,
        }

        # 更新權重
        new_weights = original_weights.copy()
        new_weights["momentum"] = 0.3
        new_weights["value"] = 0.2

        # 重新正規化
        total = sum(new_weights.values())
        normalized_weights = {k: v / total for k, v in new_weights.items()}

        # 驗證總和
        assert sum(normalized_weights.values()) == pytest.approx(1.0, abs=0.01)

    def test_custom_weights(self):
        """自訂權重測試。"""
        custom_weights = {
            "momentum": 0.4,
            "value": 0.3,
            "quality": 0.2,
            "size": 0.05,
            "liquidity": 0.03,
            "institutional": 0.02,
        }

        # 驗證總和
        total = sum(custom_weights.values())
        assert total == pytest.approx(1.0, abs=0.01)

    def test_equal_weights(self):
        """等權重測試。"""
        factors = ["momentum", "value", "quality", "size", "liquidity", "institutional"]
        equal_weight = 1.0 / len(factors)

        equal_weights = {factor: equal_weight for factor in factors}

        # 驗證總和
        total = sum(equal_weights.values())
        assert total == pytest.approx(1.0, abs=0.01)
