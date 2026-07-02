"""
台灣股票分析工具 - 產業輪動分析
追蹤產業強度變化、識別輪動機會
參考 taiwan-quant-project 的 industry/analyzer.py
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yfinance as yf
from loguru import logger

from data.data_fetcher import DataFetcher
from data.finmind_fetcher import get_finmind_fetcher


class RotationSignal(Enum):
    """輪動信號"""

    STRONG_BUY = "strong_buy"  # 強力買入
    BUY = "buy"  # 買入
    HOLD = "hold"  # 持有
    SELL = "sell"  # 賣出
    STRONG_SELL = "strong_sell"  # 強力賣出


@dataclass
class IndustryStrength:
    """產業強度"""

    industry_name: str
    strength_score: float  # -1 到 1
    momentum_20d: float  # 20日動量
    momentum_60d: float  # 60日動量
    relative_strength: float  # 相對強度
    turnover_rate: float  # 周轉率
    institutional_flow: float  # 法人流
    signal: RotationSignal
    details: Dict


@dataclass
class RotationOpportunity:
    """輪動機會"""

    from_industry: str
    to_industry: str
    signal_strength: float  # 0 到 1
    expected_return: float  # 預期報酬率
    risk_level: str  # 低/中/高
    reason: str
    suggested_allocation: Dict[str, float]


class IndustryRotationAnalyzer:
    """產業輪動分析器"""

    def __init__(self):
        """初始化產業輪動分析器"""
        self.data_fetcher = DataFetcher()
        self.finmind_fetcher = get_finmind_fetcher()

        # 台灣主要產業定義
        self.industries = {
            "半導體": {
                "stocks": ["2330.TW", "2379.TW", "3034.TW", "2454.TW", "2303.TW"],
                "weight": 0.35,  # 在加權指數中的權重
                "description": "IC 設計、晶圓代工、封測、設備",
            },
            "電子代工": {
                "stocks": ["2317.TW", "2382.TW", "4938.TW", "3231.TW"],
                "weight": 0.15,
                "description": "電腦、手機、伺服器代工",
            },
            "金融": {
                "stocks": ["2881.TW", "2882.TW", "2884.TW", "2891.TW", "2886.TW"],
                "weight": 0.12,
                "description": "銀行、壽險、證券",
            },
            "電信": {
                "stocks": ["2412.TW", "3045.TW", "4904.TW"],
                "weight": 0.05,
                "description": "電信服務",
            },
            "傳產": {
                "stocks": ["1301.TW", "1303.TW", "1326.TW", "2002.TW", "1101.TW"],
                "weight": 0.15,
                "description": "塑化、鋼鐵、水泥、食品",
            },
            "生技": {
                "stocks": ["4142.TW", "6547.TW", "3164.TW", "6535.TW"],
                "weight": 0.05,
                "description": "製藥、醫療器材、新藥開發",
            },
            "電動車": {
                "stocks": ["2345.TW", "2377.TW", "3653.TW", "6666.TW"],
                "weight": 0.05,
                "description": "電動車相關、充電樁、電池",
            },
            "AI 概念": {
                "stocks": ["2330.TW", "2379.TW", "3034.TW", "2454.TW", "3661.TW"],
                "weight": 0.08,
                "description": "AI 晶片、伺服器、散熱",
            },
        }

    def analyze_all_industries(self, period: str = "6mo") -> List[IndustryStrength]:
        """
        分析所有產業的強度

        Args:
            period: 分析期間

        Returns:
            產業強度列表
        """
        try:
            logger.info("開始分析所有產業強度...")

            industry_strengths = []

            for industry_name, industry_info in self.industries.items():
                try:
                    strength = self._analyze_industry_strength(
                        industry_name, industry_info, period
                    )
                    if strength:
                        industry_strengths.append(strength)
                except Exception as e:
                    logger.warning(f"分析產業 {industry_name} 失敗: {e}")
                    continue

            # 按強度分數排序
            industry_strengths.sort(key=lambda x: x.strength_score, reverse=True)

            logger.info(f"產業強度分析完成，共 {len(industry_strengths)} 個產業")

            return industry_strengths

        except Exception as e:
            logger.error(f"分析所有產業強度失敗: {e}")
            return []

    def find_rotation_opportunities(
        self, period: str = "6mo"
    ) -> List[RotationOpportunity]:
        """
        尋找輪動機會

        Args:
            period: 分析期間

        Returns:
            輪動機會列表
        """
        try:
            logger.info("開始尋找輪動機會...")

            # 取得所有產業強度
            industry_strengths = self.analyze_all_industries(period)

            if len(industry_strengths) < 2:
                return []

            # 找出最強和最弱的產業
            strongest = industry_strengths[0]
            weakest = industry_strengths[-1]

            opportunities = []

            # 檢查是否需要輪動
            if strongest.strength_score > 0.3 and weakest.strength_score < -0.3:
                # 強勢產業和弱勢產業差距足夠大
                opportunity = RotationOpportunity(
                    from_industry=weakest.industry_name,
                    to_industry=strongest.industry_name,
                    signal_strength=min(
                        abs(strongest.strength_score - weakest.strength_score), 1.0
                    ),
                    expected_return=(strongest.strength_score - weakest.strength_score)
                    * 10,  # 簡化預期報酬
                    risk_level="中",
                    reason=f"{strongest.industry_name} 強度 {strongest.strength_score:.2f}，{weakest.industry_name} 強度 {weakest.strength_score:.2f}",
                    suggested_allocation={
                        strongest.industry_name: 0.7,
                        weakest.industry_name: 0.3,
                    },
                )
                opportunities.append(opportunity)

            # 尋找其他輪動機會
            for i in range(len(industry_strengths) - 1):
                current = industry_strengths[i]
                next_industry = industry_strengths[i + 1]

                # 如果兩個產業強度差距足夠大
                if current.strength_score - next_industry.strength_score > 0.4:
                    opportunity = RotationOpportunity(
                        from_industry=next_industry.industry_name,
                        to_industry=current.industry_name,
                        signal_strength=min(
                            current.strength_score - next_industry.strength_score, 1.0
                        ),
                        expected_return=(
                            current.strength_score - next_industry.strength_score
                        )
                        * 8,
                        risk_level="低",
                        reason=f"{current.industry_name} 相對 {next_industry.industry_name} 強度差距 {current.strength_score - next_industry.strength_score:.2f}",
                        suggested_allocation={
                            current.industry_name: 0.6,
                            next_industry.industry_name: 0.4,
                        },
                    )
                    opportunities.append(opportunity)

            logger.info(f"找到 {len(opportunities)} 個輪動機會")

            return opportunities

        except Exception as e:
            logger.error(f"尋找輪動機會失敗: {e}")
            return []

    def _analyze_industry_strength(
        self, industry_name: str, industry_info: Dict, period: str
    ) -> Optional[IndustryStrength]:
        """
        分析單一產業的強度

        Args:
            industry_name: 產業名稱
            industry_info: 產業資訊
            period: 分析期間

        Returns:
            產業強度
        """
        try:
            stocks = industry_info.get("stocks", [])
            if not stocks:
                return None

            # 計算產業指數報酬率
            industry_returns = self._calculate_industry_returns(stocks, period)

            if industry_returns is None or industry_returns.empty:
                return None

            # 計算動量指標
            momentum_20d = (
                industry_returns.pct_change(periods=20).iloc[-1]
                if len(industry_returns) >= 20
                else 0
            )
            momentum_60d = (
                industry_returns.pct_change(periods=60).iloc[-1]
                if len(industry_returns) >= 60
                else 0
            )

            # 計算相對強度（與加權指數比較）
            relative_strength = self._calculate_relative_strength(
                industry_returns, period
            )

            # 計算周轉率（簡化版本）
            turnover_rate = self._calculate_turnover_rate(stocks, period)

            # 計算法人流（簡化版本）
            institutional_flow = self._calculate_institutional_flow(stocks)

            # 計算綜合強度分數
            strength_score = self._calculate_strength_score(
                momentum_20d,
                momentum_60d,
                relative_strength,
                turnover_rate,
                institutional_flow,
            )

            # 判斷信號
            signal = self._determine_signal(strength_score)

            return IndustryStrength(
                industry_name=industry_name,
                strength_score=float(strength_score),
                momentum_20d=float(momentum_20d),
                momentum_60d=float(momentum_60d),
                relative_strength=float(relative_strength),
                turnover_rate=float(turnover_rate),
                institutional_flow=float(institutional_flow),
                signal=signal,
                details={
                    "stocks": stocks,
                    "weight": industry_info.get("weight", 0),
                    "description": industry_info.get("description", ""),
                },
            )

        except Exception as e:
            logger.error(f"分析產業 {industry_name} 強度失敗: {e}")
            return None

    def _calculate_industry_returns(
        self, stocks: List[str], period: str
    ) -> Optional[pd.Series]:
        """計算產業指數報酬率"""
        try:
            # 取得所有股票的報酬率
            all_returns = []

            for stock_id in stocks:
                try:
                    ticker = yf.Ticker(stock_id)
                    df = ticker.history(period=period)

                    if not df.empty:
                        returns = df["Close"].pct_change()
                        returns.name = stock_id
                        all_returns.append(returns)
                except Exception as e:
                    logger.warning(f"取得 {stock_id} 報酬率失敗: {e}")
                    continue

            if not all_returns:
                return None

            # 對齊時間序列
            returns_df = pd.concat(all_returns, axis=1)
            returns_df = returns_df.dropna()

            if returns_df.empty:
                return None

            # 計算產業平均報酬率（等權重）
            industry_returns = returns_df.mean(axis=1)

            # 計算累積報酬率
            cumulative_returns = (1 + industry_returns).cumprod()

            return cumulative_returns

        except Exception as e:
            logger.error(f"計算產業報酬率失敗: {e}")
            return None

    def _calculate_relative_strength(
        self, industry_returns: pd.Series, period: str
    ) -> float:
        """計算相對強度（與加權指數比較）"""
        try:
            # 取得加權指數報酬率
            taiex_ticker = yf.Ticker("^TWII")
            taiex_df = taiex_ticker.history(period=period)

            if taiex_df.empty:
                return 0.0

            taiex_returns = taiex_df["Close"].pct_change()
            taiex_cumulative = (1 + taiex_returns).cumprod()

            # 對齊時間
            common_dates = industry_returns.index.intersection(taiex_cumulative.index)

            if len(common_dates) < 20:
                return 0.0

            industry_aligned = industry_returns.loc[common_dates]
            taiex_aligned = taiex_cumulative.loc[common_dates]

            # 計算相對強度
            relative_strength = (
                industry_aligned.iloc[-1] / taiex_aligned.iloc[-1] - 1
            ) * 100

            return float(relative_strength)

        except Exception as e:
            logger.error(f"計算相對強度失敗: {e}")
            return 0.0

    def _calculate_turnover_rate(self, stocks: List[str], period: str) -> float:
        """計算周轉率（簡化版本）"""
        try:
            turnover_rates = []

            for stock_id in stocks[:3]:  # 只取前3檔股票
                try:
                    ticker = yf.Ticker(stock_id)
                    df = ticker.history(period=period)

                    if not df.empty and "Volume" in df.columns:
                        # 簡化計算：成交量 / 平均成交量
                        avg_volume = df["Volume"].mean()
                        recent_volume = df["Volume"].iloc[-5:].mean()

                        if avg_volume > 0:
                            turnover = recent_volume / avg_volume
                            turnover_rates.append(turnover)
                except Exception as e:
                    continue

            if turnover_rates:
                return float(np.mean(turnover_rates))
            else:
                return 1.0

        except Exception as e:
            logger.error(f"計算周轉率失敗: {e}")
            return 1.0

    def _calculate_institutional_flow(self, stocks: List[str]) -> float:
        """計算法人流（簡化版本）"""
        try:
            # 嘗試從 FinMind 取得法人資料
            institutional_flows = []

            for stock_id in stocks[:2]:  # 只取前2檔股票
                try:
                    clean_id = stock_id.replace(".TW", "").replace(".TWO", "")
                    data = self.finmind_fetcher.get_institutional_investors(clean_id)

                    if data.get("success") and not data["data"].empty:
                        df = data["data"]

                        # 計算最近5天的淨買賣超
                        recent_data = df.tail(5)
                        if (
                            "buy" in recent_data.columns
                            and "sell" in recent_data.columns
                        ):
                            net_buy = (
                                recent_data["buy"].sum() - recent_data["sell"].sum()
                            )
                            institutional_flows.append(net_buy)
                except Exception as e:
                    continue

            if institutional_flows:
                # 正值表示法人淨買超
                return float(np.mean(institutional_flows) / 1e8)  # 轉換為億
            else:
                return 0.0

        except Exception as e:
            logger.error(f"計算法人流失敗: {e}")
            return 0.0

    def _calculate_strength_score(
        self,
        momentum_20d: float,
        momentum_60d: float,
        relative_strength: float,
        turnover_rate: float,
        institutional_flow: float,
    ) -> float:
        """計算綜合強度分數"""
        try:
            # 標準化各指標
            # 動量指標：-10% 到 +10% 映射到 -1 到 1
            momentum_score = (
                np.clip(momentum_20d * 10, -1, 1) * 0.4
                + np.clip(momentum_60d * 5, -1, 1) * 0.2
            )

            # 相對強度：-20% 到 +20% 映射到 -1 到 1
            rs_score = np.clip(relative_strength / 20, -1, 1) * 0.2

            # 周轉率：0.5 到 2.0 映射到 -1 到 1
            turnover_score = np.clip((turnover_rate - 1) * 2, -1, 1) * 0.1

            # 法人流：-10億到 +10億映射到 -1 到 1
            institutional_score = np.clip(institutional_flow / 10, -1, 1) * 0.1

            # 綜合分數
            total_score = (
                momentum_score + rs_score + turnover_score + institutional_score
            )

            return float(np.clip(total_score, -1, 1))

        except Exception as e:
            logger.error(f"計算強度分數失敗: {e}")
            return 0.0

    def _determine_signal(self, strength_score: float) -> RotationSignal:
        """判斷輪動信號"""
        try:
            if strength_score >= 0.6:
                return RotationSignal.STRONG_BUY
            elif strength_score >= 0.3:
                return RotationSignal.BUY
            elif strength_score >= -0.3:
                return RotationSignal.HOLD
            elif strength_score >= -0.6:
                return RotationSignal.SELL
            else:
                return RotationSignal.STRONG_SELL

        except Exception as e:
            logger.error(f"判斷信號失敗: {e}")
            return RotationSignal.HOLD

    def get_industry_ranking(self, period: str = "6mo") -> List[Dict]:
        """取得產業排名"""
        try:
            strengths = self.analyze_all_industries(period)

            ranking = []
            for i, strength in enumerate(strengths):
                ranking.append(
                    {
                        "rank": i + 1,
                        "industry": strength.industry_name,
                        "strength_score": round(strength.strength_score, 4),
                        "signal": strength.signal.value,
                        "momentum_20d": f"{strength.momentum_20d:.2%}",
                        "momentum_60d": f"{strength.momentum_60d:.2%}",
                        "relative_strength": f"{strength.relative_strength:.2f}%",
                        "description": strength.details.get("description", ""),
                    }
                )

            return ranking

        except Exception as e:
            logger.error(f"取得產業排名失敗: {e}")
            return []

    def get_rotation_analysis(self, period: str = "6mo") -> Dict:
        """取得輪動分析結果"""
        try:
            # 取得產業排名
            ranking = self.get_industry_ranking(period)

            # 尋找輪動機會
            opportunities = self.find_rotation_opportunities(period)

            # 轉換輪動機會為可序列化格式
            opportunities_data = []
            for opp in opportunities:
                opportunities_data.append(
                    {
                        "from_industry": opp.from_industry,
                        "to_industry": opp.to_industry,
                        "signal_strength": round(opp.signal_strength, 4),
                        "expected_return": f"{opp.expected_return:.2f}%",
                        "risk_level": opp.risk_level,
                        "reason": opp.reason,
                        "suggested_allocation": opp.suggested_allocation,
                    }
                )

            return {
                "success": True,
                "data": {
                    "timestamp": datetime.now().isoformat(),
                    "industry_ranking": ranking,
                    "rotation_opportunities": opportunities_data,
                    "summary": {
                        "strongest_industry": (
                            ranking[0]["industry"] if ranking else "N/A"
                        ),
                        "weakest_industry": (
                            ranking[-1]["industry"] if ranking else "N/A"
                        ),
                        "total_opportunities": len(opportunities_data),
                    },
                },
            }

        except Exception as e:
            logger.error(f"取得輪動分析失敗: {e}")
            return {"success": False, "error": str(e)}

    def get_industry_explanation(self) -> Dict:
        """取得產業輪動解釋"""
        return {
            "principle": "產業輪動是指根據經濟週期和市場趨勢，在不同產業之間進行資金配置的策略",
            "factors": [
                {
                    "name": "動量因子",
                    "description": "追蹤產業近期表現，動量強的產業傾向繼續表現良好",
                },
                {
                    "name": "相對強度",
                    "description": "比較產業與大盤的表現，相對強度高的產業具有超額報酬",
                },
                {
                    "name": "周轉率",
                    "description": "高周轉率表示市場關注度高，可能有輪動機會",
                },
                {"name": "法人流", "description": "法人買賣超反映機構投資人的看法"},
            ],
            "signals": [
                {"signal": "strong_buy", "description": "強力買入，產業強度極高"},
                {"signal": "buy", "description": "買入，產業強度高"},
                {"signal": "hold", "description": "持有，產業強度中性"},
                {"signal": "sell", "description": "賣出，產業強度弱"},
                {"signal": "strong_sell", "description": "強力賣出，產業強度極弱"},
            ],
            "usage_tips": [
                "建議定期檢視產業輪動機會",
                "可結合市場狀態（牛市/熊市）調整策略",
                "注意產業之間的相關性",
                "控制單一產業的曝險比例",
            ],
        }


# 全局實例
_industry_rotation_analyzer = None


def get_industry_rotation_analyzer() -> IndustryRotationAnalyzer:
    """取得 IndustryRotationAnalyzer 單例"""
    global _industry_rotation_analyzer
    if _industry_rotation_analyzer is None:
        _industry_rotation_analyzer = IndustryRotationAnalyzer()
    return _industry_rotation_analyzer
