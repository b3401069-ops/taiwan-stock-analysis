"""
台灣股票分析工具 - 概念股輪動分析
追蹤熱門概念股輪動（CoWoS/散熱/低軌衛星/AI伺服器/車用電子）
參考 taiwan-quant-project 的 industry/concept_analyzer.py
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date, timedelta
from loguru import logger
import yfinance as yf
from dataclasses import dataclass
from enum import Enum

from data.data_fetcher import DataFetcher
from data.finmind_fetcher import get_finmind_fetcher


class ConceptTrend(Enum):
    """概念股趨勢"""
    HOT = "hot"             # 熱門
    RISING = "rising"       # 上升
    STABLE = "stable"       # 穩定
    DECLINING = "declining"  # 下降
    COLD = "cold"           # 冷門


@dataclass
class ConceptStock:
    """概念股"""
    concept_name: str
    stock_id: str
    stock_name: str
    correlation: float      # 與概念的相關性
    momentum_20d: float     # 20日動量
    momentum_60d: float     # 60日動量
    volume_ratio: float     # 成交量比率
    institutional_flow: float  # 法人流
    trend: ConceptTrend
    details: Dict


@dataclass
class ConceptGroup:
    """概念股群組"""
    concept_name: str
    description: str
    stocks: List[ConceptStock]
    avg_momentum_20d: float
    avg_momentum_60d: float
    avg_volume_ratio: float
    total_institutional_flow: float
    trend: ConceptTrend
    heat_score: float  # 0 到 1
    details: Dict


class ConceptRotationAnalyzer:
    """概念股輪動分析器"""

    def __init__(self):
        """初始化概念股輪動分析器"""
        self.data_fetcher = DataFetcher()
        self.finmind_fetcher = get_finmind_fetcher()
        
        # 概念股定義
        self.concepts = {
            "CoWoS 封裝": {
                "stocks": ["2330.TW", "3034.TW", "2379.TW", "6488.TW"],
                "keywords": ["CoWoS", "先進封裝", "AI 晶片"],
                "description": "台積電 CoWoS 先進封裝技術，用於 AI 晶片"
            },
            "散熱模組": {
                "stocks": ["3653.TW", "6666.TW", "2377.TW", "2345.TW"],
                "keywords": ["散熱", "液冷", "AI 伺服器"],
                "description": "AI 伺服器散熱解決方案"
            },
            "低軌衛星": {
                "stocks": ["3035.TW", "6666.TW", "2377.TW"],
                "keywords": ["衛星", "SpaceX", "Starlink"],
                "description": "低軌道衛星通訊產業鏈"
            },
            "AI 伺服器": {
                "stocks": ["2317.TW", "2382.TW", "4938.TW", "3231.TW"],
                "keywords": ["AI", "伺服器", "GPU", "NVIDIA"],
                "description": "AI 伺服器代工和相關零組件"
            },
            "車用電子": {
                "stocks": ["2345.TW", "2377.TW", "3653.TW", "2207.TW"],
                "keywords": ["電動車", "自駕", "車用晶片"],
                "description": "電動車和自駕車相關電子零組件"
            },
            "ABF 載板": {
                "stocks": ["3034.TW", "6488.TW", "2379.TW"],
                "keywords": ["ABF", "載板", "IC 載板"],
                "description": "ABF 載板產業，用於先進晶片封裝"
            },
            "矽智財": {
                "stocks": ["3661.TW", "8069.TW", "6488.TW"],
                "keywords": ["IP", "矽智財", "IC 設計"],
                "description": "IC 設計矽智財授權"
            },
            "被動元件": {
                "stocks": ["2327.TW", "6488.TW", "2379.TW"],
                "keywords": ["電容", "電阻", "被動元件"],
                "description": "電容、電阻等被動元件"
            }
        }

    def analyze_all_concepts(self, period: str = "6mo") -> List[ConceptGroup]:
        """
        分析所有概念股
        
        Args:
            period: 分析期間
            
        Returns:
            概念股群組列表
        """
        try:
            logger.info("開始分析所有概念股...")
            
            concept_groups = []
            
            for concept_name, concept_info in self.concepts.items():
                try:
                    group = self._analyze_concept_group(
                        concept_name, 
                        concept_info, 
                        period
                    )
                    if group:
                        concept_groups.append(group)
                except Exception as e:
                    logger.warning(f"分析概念 {concept_name} 失敗: {e}")
                    continue
            
            # 按熱度分數排序
            concept_groups.sort(key=lambda x: x.heat_score, reverse=True)
            
            logger.info(f"概念股分析完成，共 {len(concept_groups)} 個概念")
            
            return concept_groups
            
        except Exception as e:
            logger.error(f"分析所有概念股失敗: {e}")
            return []

    def find_hot_concepts(self, period: str = "6mo", min_heat: float = 0.5) -> List[ConceptGroup]:
        """
        尋找熱門概念股
        
        Args:
            period: 分析期間
            min_heat: 最低熱度分數
            
        Returns:
            熱門概念股列表
        """
        try:
            logger.info(f"尋找熱門概念股（最低熱度: {min_heat}）...")
            
            concept_groups = self.analyze_all_concepts(period)
            
            # 篩選熱門概念股
            hot_concepts = [g for g in concept_groups if g.heat_score >= min_heat]
            
            logger.info(f"找到 {len(hot_concepts)} 個熱門概念股")
            
            return hot_concepts
            
        except Exception as e:
            logger.error(f"尋找熱門概念股失敗: {e}")
            return []

    def _analyze_concept_group(
        self,
        concept_name: str,
        concept_info: Dict,
        period: str
    ) -> Optional[ConceptGroup]:
        """
        分析單一概念股群組
        
        Args:
            concept_name: 概念名稱
            concept_info: 概念資訊
            period: 分析期間
            
        Returns:
            概念股群組
        """
        try:
            stocks_info = concept_info.get("stocks", [])
            if not stocks_info:
                return None
            
            # 分析每檔股票
            concept_stocks = []
            for stock_id in stocks_info:
                try:
                    stock_analysis = self._analyze_concept_stock(
                        stock_id, concept_name, period
                    )
                    if stock_analysis:
                        concept_stocks.append(stock_analysis)
                except Exception as e:
                    logger.warning(f"分析概念股 {stock_id} 失敗: {e}")
                    continue
            
            if not concept_stocks:
                return None
            
            # 計算群組平均指標
            avg_momentum_20d = np.mean([s.momentum_20d for s in concept_stocks])
            avg_momentum_60d = np.mean([s.momentum_60d for s in concept_stocks])
            avg_volume_ratio = np.mean([s.volume_ratio for s in concept_stocks])
            total_institutional_flow = sum([s.institutional_flow for s in concept_stocks])
            
            # 計算熱度分數
            heat_score = self._calculate_heat_score(
                avg_momentum_20d, avg_momentum_60d, avg_volume_ratio, total_institutional_flow
            )
            
            # 判斷趨勢
            trend = self._determine_concept_trend(heat_score)
            
            return ConceptGroup(
                concept_name=concept_name,
                description=concept_info.get("description", ""),
                stocks=concept_stocks,
                avg_momentum_20d=float(avg_momentum_20d),
                avg_momentum_60d=float(avg_momentum_60d),
                avg_volume_ratio=float(avg_volume_ratio),
                total_institutional_flow=float(total_institutional_flow),
                trend=trend,
                heat_score=float(heat_score),
                details={
                    "keywords": concept_info.get("keywords", []),
                    "stock_count": len(concept_stocks)
                }
            )
            
        except Exception as e:
            logger.error(f"分析概念 {concept_name} 群組失敗: {e}")
            return None

    def _analyze_concept_stock(
        self,
        stock_id: str,
        concept_name: str,
        period: str
    ) -> Optional[ConceptStock]:
        """
        分析單一概念股
        
        Args:
            stock_id: 股票代碼
            concept_name: 概念名稱
            period: 分析期間
            
        Returns:
            概念股分析結果
        """
        try:
            # 取得股票資料
            ticker = yf.Ticker(stock_id)
            df = ticker.history(period=period)
            
            if df.empty:
                return None
            
            # 計算動量指標
            momentum_20d = df["Close"].pct_change(periods=20).iloc[-1] if len(df) >= 20 else 0
            momentum_60d = df["Close"].pct_change(periods=60).iloc[-1] if len(df) >= 60 else 0
            
            # 計算成交量比率
            volume_ma = df["Volume"].rolling(window=20).mean()
            volume_ratio = df["Volume"].iloc[-1] / volume_ma.iloc[-1] if volume_ma.iloc[-1] > 0 else 1.0
            
            # 計算相關性（簡化版本：使用動量作為相關性代理指標）
            correlation = self._calculate_correlation(stock_id, concept_name)
            
            # 取得法人流
            institutional_flow = self._get_institutional_flow(stock_id)
            
            # 判斷趨勢
            trend = self._determine_stock_trend(momentum_20d, momentum_60d, volume_ratio)
            
            # 取得股票名稱
            stock_name = self._get_stock_name(stock_id)
            
            return ConceptStock(
                concept_name=concept_name,
                stock_id=stock_id,
                stock_name=stock_name,
                correlation=float(correlation),
                momentum_20d=float(momentum_20d),
                momentum_60d=float(momentum_60d),
                volume_ratio=float(volume_ratio),
                institutional_flow=float(institutional_flow),
                trend=trend,
                details={
                    "current_price": float(df["Close"].iloc[-1]),
                    "volume": int(df["Volume"].iloc[-1])
                }
            )
            
        except Exception as e:
            logger.error(f"分析概念股 {stock_id} 失敗: {e}")
            return None

    def _calculate_correlation(self, stock_id: str, concept_name: str) -> float:
        """計算股票與概念的相關性（簡化版本）"""
        try:
            # 這裡可以根據關鍵字、新聞情緒等計算相關性
            # 簡化版本：返回固定值
            return 0.7
            
        except Exception as e:
            logger.error(f"計算相關性失敗: {e}")
            return 0.5

    def _get_institutional_flow(self, stock_id: str) -> float:
        """取得法人流"""
        try:
            clean_id = stock_id.replace(".TW", "").replace(".TWO", "")
            data = self.finmind_fetcher.get_institutional_investors(clean_id)
            
            if data.get("success") and not data["data"].empty:
                df = data["data"]
                
                # 計算最近5天的淨買賣超
                recent_data = df.tail(5)
                if "buy" in recent_data.columns and "sell" in recent_data.columns:
                    net_buy = recent_data["buy"].sum() - recent_data["sell"].sum()
                    return float(net_buy / 1e8)  # 轉換為億
            
            return 0.0
            
        except Exception as e:
            logger.error(f"取得法人流失敗: {e}")
            return 0.0

    def _calculate_heat_score(
        self,
        momentum_20d: float,
        momentum_60d: float,
        volume_ratio: float,
        institutional_flow: float
    ) -> float:
        """計算熱度分數"""
        try:
            # 標準化各指標
            # 動量指標：-10% 到 +10% 映射到 -1 到 1
            momentum_score = np.clip(momentum_20d * 10, -1, 1) * 0.4 + \
                           np.clip(momentum_60d * 5, -1, 1) * 0.2
            
            # 成交量比率：0.5 到 2.0 映射到 -1 到 1
            volume_score = np.clip((volume_ratio - 1) * 2, -1, 1) * 0.2
            
            # 法人流：-10億到 +10億映射到 -1 到 1
            institutional_score = np.clip(institutional_flow / 10, -1, 1) * 0.2
            
            # 綜合分數
            total_score = momentum_score + volume_score + institutional_score
            
            # 映射到 0-1 範圍
            heat_score = (total_score + 1) / 2
            
            return float(np.clip(heat_score, 0, 1))
            
        except Exception as e:
            logger.error(f"計算熱度分數失敗: {e}")
            return 0.5

    def _determine_concept_trend(self, heat_score: float) -> ConceptTrend:
        """判斷概念股趨勢"""
        try:
            if heat_score >= 0.8:
                return ConceptTrend.HOT
            elif heat_score >= 0.6:
                return ConceptTrend.RISING
            elif heat_score >= 0.4:
                return ConceptTrend.STABLE
            elif heat_score >= 0.2:
                return ConceptTrend.DECLINING
            else:
                return ConceptTrend.COLD
                
        except Exception as e:
            logger.error(f"判斷概念股趨勢失敗: {e}")
            return ConceptTrend.STABLE

    def _determine_stock_trend(
        self,
        momentum_20d: float,
        momentum_60d: float,
        volume_ratio: float
    ) -> ConceptTrend:
        """判斷單一股票趨勢"""
        try:
            # 計算綜合分數
            score = momentum_20d * 0.5 + momentum_60d * 0.3 + (volume_ratio - 1) * 0.2
            
            if score >= 0.1:
                return ConceptTrend.HOT
            elif score >= 0.05:
                return ConceptTrend.RISING
            elif score >= -0.05:
                return ConceptTrend.STABLE
            elif score >= -0.1:
                return ConceptTrend.DECLINING
            else:
                return ConceptTrend.COLD
                
        except Exception as e:
            logger.error(f"判斷股票趨勢失敗: {e}")
            return ConceptTrend.STABLE

    def _get_stock_name(self, stock_id: str) -> str:
        """取得股票名稱"""
        try:
            ticker = yf.Ticker(stock_id)
            info = ticker.info
            return info.get("longName", info.get("shortName", stock_id))
        except:
            return stock_id

    def get_concept_ranking(self, period: str = "6mo") -> List[Dict]:
        """取得概念股排名"""
        try:
            concepts = self.analyze_all_concepts(period)
            
            ranking = []
            for i, concept in enumerate(concepts):
                ranking.append({
                    "rank": i + 1,
                    "concept": concept.concept_name,
                    "description": concept.description,
                    "heat_score": round(concept.heat_score, 4),
                    "trend": concept.trend.value,
                    "avg_momentum_20d": f"{concept.avg_momentum_20d:.2%}",
                    "avg_momentum_60d": f"{concept.avg_momentum_60d:.2%}",
                    "avg_volume_ratio": round(concept.avg_volume_ratio, 2),
                    "total_institutional_flow": f"{concept.total_institutional_flow:.2f}億",
                    "stock_count": len(concept.stocks)
                })
            
            return ranking
            
        except Exception as e:
            logger.error(f"取得概念股排名失敗: {e}")
            return []

    def get_concept_analysis(self, period: str = "6mo") -> Dict:
        """取得概念股分析結果"""
        try:
            # 取得概念股排名
            ranking = self.get_concept_ranking(period)
            
            # 尋找熱門概念股
            hot_concepts = self.find_hot_concepts(period, min_heat=0.6)
            
            # 轉換熱門概念股為可序列化格式
            hot_concepts_data = []
            for concept in hot_concepts:
                stocks_data = []
                for stock in concept.stocks:
                    stocks_data.append({
                        "stock_id": stock.stock_id,
                        "stock_name": stock.stock_name,
                        "correlation": round(stock.correlation, 4),
                        "momentum_20d": f"{stock.momentum_20d:.2%}",
                        "trend": stock.trend.value
                    })
                
                hot_concepts_data.append({
                    "concept": concept.concept_name,
                    "description": concept.description,
                    "heat_score": round(concept.heat_score, 4),
                    "trend": concept.trend.value,
                    "stocks": stocks_data
                })
            
            return {
                "success": True,
                "data": {
                    "timestamp": datetime.now().isoformat(),
                    "concept_ranking": ranking,
                    "hot_concepts": hot_concepts_data,
                    "summary": {
                        "hottest_concept": ranking[0]["concept"] if ranking else "N/A",
                        "total_hot_concepts": len(hot_concepts_data),
                        "total_concepts": len(ranking)
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"取得概念股分析失敗: {e}")
            return {"success": False, "error": str(e)}

    def get_concept_explanation(self) -> Dict:
        """取得概念股輪動解釋"""
        return {
            "principle": "概念股輪動是指根據市場熱點和產業趨勢，在不同概念股之間進行資金配置的策略",
            "concepts": [
                {
                    "name": "CoWoS 封裝",
                    "description": "台積電 CoWoS 先進封裝技術，用於 AI 晶片",
                    "drivers": ["AI 需求成長", "先進封裝技術突破"]
                },
                {
                    "name": "散熱模組",
                    "description": "AI 伺服器散熱解決方案",
                    "drivers": ["AI 伺服器需求", "液冷技術發展"]
                },
                {
                    "name": "低軌衛星",
                    "description": "低軌道衛星通訊產業鏈",
                    "drivers": ["Starlink 發展", "衛星通訊需求"]
                },
                {
                    "name": "AI 伺服器",
                    "description": "AI 伺服器代工和相關零組件",
                    "drivers": ["AI 需求爆發", "NVIDIA GPU 供應"]
                },
                {
                    "name": "車用電子",
                    "description": "電動車和自駕車相關電子零組件",
                    "drivers": ["電動車普及", "自駕技術發展"]
                }
            ],
            "heat_levels": [
                {"level": "hot", "description": "熱門，市場關注度極高", "action": "積極佈局"},
                {"level": "rising", "description": "上升，市場關注度增加", "description": "適度佈局"},
                {"level": "stable", "description": "穩定，市場關注度平穩", "action": "持有觀察"},
                {"level": "declining", "description": "下降，市場關注度減少", "action": "減碼觀望"},
                {"level": "cold", "description": "冷門，市場關注度極低", "action": "避免佈局"}
            ],
            "usage_tips": [
                "關注產業新聞和政策動向",
                "注意概念股的估值泡沫",
                "控制單一概念股的曝險比例",
                "結合技術分析確認進出場時機",
                "定期檢視概念股的基本面變化"
            ]
        }


# 全局實例
_concept_rotation_analyzer = None


def get_concept_rotation_analyzer() -> ConceptRotationAnalyzer:
    """取得 ConceptRotationAnalyzer 單例"""
    global _concept_rotation_analyzer
    if _concept_rotation_analyzer is None:
        _concept_rotation_analyzer = ConceptRotationAnalyzer()
    return _concept_rotation_analyzer
