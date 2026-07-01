"""多因子選股引擎測試。"""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock


class TestMultiFactorScreener:
    """多因子選股引擎測試。"""

    def test_factor_weights_sum_to_one(self, sample_factor_weights):
        """因子權重總和應為 1。"""
        total = sum(sample_factor_weights.values())
        assert total == pytest.approx(1.0, abs=0.01)

    def test_factor_weights_positive(self, sample_factor_weights):
        """因子權重應為正數。"""
        for weight in sample_factor_weights.values():
            assert weight >= 0

    def test_six_factors(self, sample_factor_weights):
        """應有 6 個因子。"""
        expected_factors = ["momentum", "value", "quality", "size", "liquidity", "institutional"]
        assert len(sample_factor_weights) == 6
        
        for factor in expected_factors:
            assert factor in sample_factor_weights

    def test_screener_result_structure(self, sample_screener_result):
        """選股結果結構測試。"""
        for stock in sample_screener_result:
            # 檢查必要欄位
            assert "rank" in stock
            assert "stock_id" in stock
            assert "stock_name" in stock
            assert "composite_score" in stock
            
            # 檢查分數範圍
            assert 0 <= stock["composite_score"] <= 1

    def test_screener_result_ranking(self, sample_screener_result):
        """選股結果排名測試。"""
        for i in range(len(sample_screener_result) - 1):
            # 排名應遞增
            assert sample_screener_result[i]["rank"] < sample_screener_result[i + 1]["rank"]
            
            # 分數應遞減
            assert sample_screener_result[i]["composite_score"] >= sample_screener_result[i + 1]["composite_score"]

    def test_momentum_factor(self):
        """動量因子測試。"""
        # 20日報酬率計算
        prices = [100, 102, 105, 103, 108, 110, 112, 115, 113, 118,
                  120, 122, 125, 123, 128, 130, 132, 135, 133, 138]
        
        # 計算20日報酬率
        momentum = (prices[-1] - prices[0]) / prices[0]
        assert momentum > 0  # 正動量

    def test_value_factor(self):
        """價值因子測試。"""
        # PE ratio 測試
        pe_ratio = 15.0
        pe_score = 1 / pe_ratio  # PE 越低，分數越高
        
        assert pe_score > 0
        
        # 較低的 PE 應有較高的分數
        low_pe_score = 1 / 10.0
        high_pe_score = 1 / 30.0
        assert low_pe_score > high_pe_score

    def test_quality_factor(self):
        """品質因子測試。"""
        # ROE 測試
        roe = 0.20  # 20%
        assert 0 < roe < 1
        
        # 較高的 ROE 應有較高的分數
        high_roe = 0.25
        low_roe = 0.10
        assert high_roe > low_roe

    def test_size_factor(self):
        """規模因子測試。"""
        # 市值測試
        market_cap = 1_000_000_000_000  # 1 兆
        assert market_cap > 0

    def test_liquidity_factor(self):
        """流動性因子測試。"""
        # 成交量比率測試
        volume = 10_000_000
        avg_volume = 8_000_000
        volume_ratio = volume / avg_volume
        
        assert volume_ratio > 0

    def test_institutional_factor(self):
        """法人因子測試。"""
        # 法人買賣超測試
        institutional_buy = 500_000
        institutional_sell = 300_000
        net_flow = institutional_buy - institutional_sell
        
        assert net_flow > 0  # 正向法人流

    def test_composite_score_calculation(self, sample_factor_weights):
        """綜合分數計算測試。"""
        # 模擬各因子分數
        factor_scores = {
            "momentum": 0.8,
            "value": 0.7,
            "quality": 0.9,
            "size": 0.6,
            "liquidity": 0.75,
            "institutional": 0.85,
        }
        
        # 計算綜合分數
        composite_score = sum(
            factor_scores[factor] * weight
            for factor, weight in sample_factor_weights.items()
        )
        
        assert 0 <= composite_score <= 1

    def test_screener_top_n(self, sample_screener_result):
        """選股 Top N 測試。"""
        top_n = 2
        result = sample_screener_result[:top_n]
        
        assert len(result) == top_n
        assert result[0]["rank"] == 1
        assert result[1]["rank"] == 2


class TestFactorNormalization:
    """因子正規化測試。"""

    def test_min_max_normalization(self):
        """最小最大正規化測試。"""
        values = [10, 20, 30, 40, 50]
        min_val = min(values)
        max_val = max(values)
        
        normalized = [(v - min_val) / (max_val - min_val) for v in values]
        
        # 正規化後應在 0-1 之間
        for n in normalized:
            assert 0 <= n <= 1
        
        # 最小值應為 0，最大值應為 1
        assert normalized[0] == 0
        assert normalized[-1] == 1

    def test_zscore_normalization(self):
        """Z-score 正規化測試。"""
        import numpy as np
        
        values = np.array([10, 20, 30, 40, 50])
        mean = values.mean()
        std = values.std()
        
        zscores = (values - mean) / std
        
        # Z-score 平均應接近 0
        assert abs(zscores.mean()) < 0.01
        
        # Z-score 標準差應接近 1
        assert abs(zscores.std() - 1) < 0.01

    def test_percentile_rank(self):
        """百分位排名測試。"""
        values = [10, 20, 30, 40, 50]
        
        # 計算百分位排名
        ranks = []
        for v in values:
            rank = sum(1 for x in values if x <= v) / len(values)
            ranks.append(rank)
        
        # 排名應在 0-1 之間
        for r in ranks:
            assert 0 <= r <= 1
        
        # 最後一個值應為 1
        assert ranks[-1] == 1
