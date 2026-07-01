"""
台灣股票分析工具 - 多因子選股引擎
動量/價值/品質/規模/流動性/法人 6 因子篩選
參考 taiwan-quant-project 的 screener/engine.py
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date, timedelta
from loguru import logger
from dataclasses import dataclass
from enum import Enum
import yfinance as yf

from data.data_fetcher import DataFetcher
from data.finmind_fetcher import get_finmind_fetcher
from analysis.valuation_metrics import ValuationMetrics


class FactorType(Enum):
    """因子類型"""
    MOMENTUM = "momentum"       # 動量因子
    VALUE = "value"             # 價值因子
    QUALITY = "quality"         # 品質因子
    SIZE = "size"               # 規模因子
    LIQUIDITY = "liquidity"     # 流動性因子
    INSTITUTIONAL = "institutional"  # 法人因子


@dataclass
class FactorScore:
    """因子分數"""
    factor_type: FactorType
    score: float  # -1 到 1
    weight: float  # 權重
    details: Dict  # 詳細資訊


@dataclass
class StockScore:
    """股票綜合分數"""
    stock_id: str
    stock_name: str
    composite_score: float  # 綜合分數
    factor_scores: List[FactorScore]
    rank: int
    details: Dict


class MultiFactorScreener:
    """多因子選股引擎"""

    def __init__(self):
        """初始化多因子選股引擎"""
        self.data_fetcher = DataFetcher()
        self.valuation_metrics = ValuationMetrics()
        self.finmind_fetcher = get_finmind_fetcher()
        
        # 因子權重（可調整）
        self.factor_weights = {
            FactorType.MOMENTUM: 0.20,
            FactorType.VALUE: 0.25,
            FactorType.QUALITY: 0.25,
            FactorType.SIZE: 0.10,
            FactorType.LIQUIDITY: 0.10,
            FactorType.INSTITUTIONAL: 0.10
        }
        
        # 預設股票池（可擴展）
        self.default_universe = [
            "2330.TW",  # 台積電
            "2317.TW",  # 鴻海
            "2454.TW",  # 聯發科
            "2308.TW",  # 台達電
            "2412.TW",  # 中華電
            "2881.TW",  # 富邦金
            "2882.TW",  # 國泰金
            "2886.TW",  # 兆豐金
            "2884.TW",  # 玉山金
            "2885.TW",  # 元大金
            "2303.TW",  # 聯電
            "2395.TW",  # 研華
            "2379.TW",  # 瑞昱
            "2356.TW",  # 英業達
            "2382.TW",  # 廣達
        ]

    def screen(self, universe: List[str] = None, top_n: int = 10) -> List[StockScore]:
        """
        多因子選股篩選
        
        Args:
            universe: 股票池（預設使用 default_universe）
            top_n: 返回前 N 名
            
        Returns:
            排序後的股票分數列表
        """
        try:
            logger.info("開始多因子選股篩選...")
            
            # 使用預設股票池或指定股票池
            if universe is None:
                universe = self.default_universe
            
            # 計算每檔股票的因子分數
            stock_scores = []
            for stock_id in universe:
                try:
                    score = self._calculate_stock_score(stock_id)
                    if score is not None:
                        stock_scores.append(score)
                except Exception as e:
                    logger.warning(f"計算 {stock_id} 因子分數失敗: {e}")
                    continue
            
            # 按綜合分數排序
            stock_scores.sort(key=lambda x: x.composite_score, reverse=True)
            
            # 設定排名
            for i, score in enumerate(stock_scores):
                score.rank = i + 1
            
            # 返回前 N 名
            result = stock_scores[:top_n]
            
            logger.info(f"多因子選股完成，共 {len(result)} 檔股票")
            return result
            
        except Exception as e:
            logger.error(f"多因子選股失敗: {e}")
            return []

    def _calculate_stock_score(self, stock_id: str) -> Optional[StockScore]:
        """
        計算單一股票的綜合分數
        
        Args:
            stock_id: 股票代碼
            
        Returns:
            股票綜合分數
        """
        try:
            # 取得股票資料
            stock_data = self._get_stock_data(stock_id)
            if stock_data is None:
                return None
            
            # 計算各因子分數
            factor_scores = []
            
            # 1. 動量因子
            momentum_score = self._calculate_momentum_factor(stock_data)
            factor_scores.append(momentum_score)
            
            # 2. 價值因子
            value_score = self._calculate_value_factor(stock_id, stock_data)
            factor_scores.append(value_score)
            
            # 3. 品質因子
            quality_score = self._calculate_quality_factor(stock_id, stock_data)
            factor_scores.append(quality_score)
            
            # 4. 規模因子
            size_score = self._calculate_size_factor(stock_id, stock_data)
            factor_scores.append(size_score)
            
            # 5. 流動性因子
            liquidity_score = self._calculate_liquidity_factor(stock_data)
            factor_scores.append(liquidity_score)
            
            # 6. 法人因子
            institutional_score = self._calculate_institutional_factor(stock_id, stock_data)
            factor_scores.append(institutional_score)
            
            # 計算綜合分數
            composite_score = self._calculate_composite_score(factor_scores)
            
            # 取得股票名稱
            stock_name = self._get_stock_name(stock_id)
            
            return StockScore(
                stock_id=stock_id,
                stock_name=stock_name,
                composite_score=composite_score,
                factor_scores=factor_scores,
                rank=0,  # 稍後設定
                details={
                    "current_price": stock_data.get("current_price", 0),
                    "market_cap": stock_data.get("market_cap", 0),
                    "pe_ratio": stock_data.get("pe_ratio", 0),
                    "pb_ratio": stock_data.get("pb_ratio", 0)
                }
            )
            
        except Exception as e:
            logger.error(f"計算 {stock_id} 綜合分數失敗: {e}")
            return None

    def _get_stock_data(self, stock_id: str) -> Optional[Dict]:
        """取得股票資料"""
        try:
            # 取得 Yahoo Finance 資料
            ticker = yf.Ticker(stock_id)
            info = ticker.info
            history = ticker.history(period="6mo")
            
            if not info or history.empty:
                return None
            
            # 計算技術指標
            history = self._add_technical_indicators(history)
            
            # 取得估值指標
            valuation = self.valuation_metrics.get_valuation(stock_id)
            valuation_data = valuation.get("data", {}) if valuation.get("success") else {}
            
            return {
                "stock_id": stock_id,
                "info": info,
                "history": history,
                "current_price": info.get("currentPrice", info.get("regularMarketPrice", 0)),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": valuation_data.get("pe_ratio", 0),
                "pb_ratio": valuation_data.get("pb_ratio", 0),
                "dividend_yield": valuation_data.get("dividend_yield", 0),
                "revenue_growth": info.get("revenueGrowth", 0),
                "profit_margins": info.get("profitMargins", 0),
                "roe": info.get("returnOnEquity", 0),
                "volume": history["volume"].iloc[-1] if not history.empty else 0,
                "avg_volume": history["volume"].mean() if not history.empty else 0
            }
            
        except Exception as e:
            logger.error(f"取得 {stock_id} 資料失敗: {e}")
            return None

    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """計算技術指標"""
        try:
            # 移動平均
            df["sma_20"] = df["Close"].rolling(window=20).mean()
            df["sma_60"] = df["Close"].rolling(window=60).mean()
            
            # RSI
            delta = df["Close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df["rsi"] = 100 - (100 / (1 + rs))
            
            # 動量指標
            df["momentum_20"] = df["Close"].pct_change(periods=20)
            df["momentum_60"] = df["Close"].pct_change(periods=60)
            
            # 波動率
            df["volatility"] = df["Close"].pct_change().rolling(window=20).std()
            
            # 成交量比率
            df["volume_ma"] = df["Volume"].rolling(window=20).mean()
            df["volume_ratio"] = df["Volume"] / df["volume_ma"]
            
            return df
            
        except Exception as e:
            logger.error(f"計算技術指標失敗: {e}")
            return df

    def _calculate_momentum_factor(self, stock_data: Dict) -> FactorScore:
        """計算動量因子分數"""
        try:
            history = stock_data.get("history", pd.DataFrame())
            if history.empty:
                return FactorScore(
                    factor_type=FactorType.MOMENTUM,
                    score=0.0,
                    weight=self.factor_weights[FactorType.MOMENTUM],
                    details={"error": "無歷史資料"}
                )
            
            # 計算動量分數
            momentum_20 = history["momentum_20"].iloc[-1] if "momentum_20" in history.columns else 0
            momentum_60 = history["momentum_60"].iloc[-1] if "momentum_60" in history.columns else 0
            
            # 標準化分數 (-1 到 1)
            # 20日動量：-10% 到 +10% 映射到 -1 到 1
            score_20 = np.clip(momentum_20 * 10, -1, 1)
            
            # 60日動量：-20% 到 +20% 映射到 -1 到 1
            score_60 = np.clip(momentum_60 * 5, -1, 1)
            
            # 加權平均
            score = 0.6 * score_20 + 0.4 * score_60
            
            return FactorScore(
                factor_type=FactorType.MOMENTUM,
                score=float(score),
                weight=self.factor_weights[FactorType.MOMENTUM],
                details={
                    "momentum_20": float(momentum_20),
                    "momentum_60": float(momentum_60),
                    "score_20": float(score_20),
                    "score_60": float(score_60)
                }
            )
            
        except Exception as e:
            logger.error(f"計算動量因子失敗: {e}")
            return FactorScore(
                factor_type=FactorType.MOMENTUM,
                score=0.0,
                weight=self.factor_weights[FactorType.MOMENTUM],
                details={"error": str(e)}
            )

    def _calculate_value_factor(self, stock_id: str, stock_data: Dict) -> FactorScore:
        """計算價值因子分數"""
        try:
            pe_ratio = stock_data.get("pe_ratio", 0)
            pb_ratio = stock_data.get("pb_ratio", 0)
            dividend_yield = stock_data.get("dividend_yield", 0)
            
            # PE 分數：PE 越低越好
            # PE < 10: 1分, PE 10-20: 0分, PE > 20: -1分
            if pe_ratio and pe_ratio > 0:
                if pe_ratio < 10:
                    pe_score = 1.0
                elif pe_ratio < 15:
                    pe_score = 0.5
                elif pe_ratio < 20:
                    pe_score = 0.0
                elif pe_ratio < 30:
                    pe_score = -0.5
                else:
                    pe_score = -1.0
            else:
                pe_score = 0.0
            
            # PB 分數：PB 越低越好
            # PB < 1: 1分, PB 1-2: 0分, PB > 2: -1分
            if pb_ratio and pb_ratio > 0:
                if pb_ratio < 1:
                    pb_score = 1.0
                elif pb_ratio < 1.5:
                    pb_score = 0.5
                elif pb_ratio < 2:
                    pb_score = 0.0
                elif pb_ratio < 3:
                    pb_score = -0.5
                else:
                    pb_score = -1.0
            else:
                pb_score = 0.0
            
            # 股利殖利率分數：殖利率越高越好
            # > 5%: 1分, 3-5%: 0.5分, 1-3%: 0分, < 1%: -0.5分
            if dividend_yield and dividend_yield > 0:
                if dividend_yield > 5:
                    dy_score = 1.0
                elif dividend_yield > 3:
                    dy_score = 0.5
                elif dividend_yield > 1:
                    dy_score = 0.0
                else:
                    dy_score = -0.5
            else:
                dy_score = -0.5
            
            # 加權平均
            score = 0.4 * pe_score + 0.3 * pb_score + 0.3 * dy_score
            
            return FactorScore(
                factor_type=FactorType.VALUE,
                score=float(score),
                weight=self.factor_weights[FactorType.VALUE],
                details={
                    "pe_ratio": float(pe_ratio),
                    "pb_ratio": float(pb_ratio),
                    "dividend_yield": float(dividend_yield),
                    "pe_score": float(pe_score),
                    "pb_score": float(pb_score),
                    "dy_score": float(dy_score)
                }
            )
            
        except Exception as e:
            logger.error(f"計算價值因子失敗: {e}")
            return FactorScore(
                factor_type=FactorType.VALUE,
                score=0.0,
                weight=self.factor_weights[FactorType.VALUE],
                details={"error": str(e)}
            )

    def _calculate_quality_factor(self, stock_id: str, stock_data: Dict) -> FactorScore:
        """計算品質因子分數"""
        try:
            roe = stock_data.get("roe", 0)
            profit_margins = stock_data.get("profit_margins", 0)
            revenue_growth = stock_data.get("revenue_growth", 0)
            
            # ROE 分數：ROE 越高越好
            # > 20%: 1分, 15-20%: 0.5分, 10-15%: 0分, < 10%: -0.5分
            if roe and roe > 0:
                if roe > 20:
                    roe_score = 1.0
                elif roe > 15:
                    roe_score = 0.5
                elif roe > 10:
                    roe_score = 0.0
                else:
                    roe_score = -0.5
            else:
                roe_score = -0.5
            
            # 毛利率分數：毛利率越高越好
            # > 30%: 1分, 20-30%: 0.5分, 10-20%: 0分, < 10%: -0.5分
            if profit_margins and profit_margins > 0:
                if profit_margins > 30:
                    margin_score = 1.0
                elif profit_margins > 20:
                    margin_score = 0.5
                elif profit_margins > 10:
                    margin_score = 0.0
                else:
                    margin_score = -0.5
            else:
                margin_score = -0.5
            
            # 營收成長分數：營收成長越高越好
            # > 20%: 1分, 10-20%: 0.5分, 0-10%: 0分, < 0%: -1分
            if revenue_growth and revenue_growth > 0:
                if revenue_growth > 20:
                    growth_score = 1.0
                elif revenue_growth > 10:
                    growth_score = 0.5
                elif revenue_growth > 0:
                    growth_score = 0.0
                else:
                    growth_score = -1.0
            else:
                growth_score = -0.5
            
            # 加權平均
            score = 0.4 * roe_score + 0.3 * margin_score + 0.3 * growth_score
            
            return FactorScore(
                factor_type=FactorType.QUALITY,
                score=float(score),
                weight=self.factor_weights[FactorType.QUALITY],
                details={
                    "roe": float(roe),
                    "profit_margins": float(profit_margins),
                    "revenue_growth": float(revenue_growth),
                    "roe_score": float(roe_score),
                    "margin_score": float(margin_score),
                    "growth_score": float(growth_score)
                }
            )
            
        except Exception as e:
            logger.error(f"計算品質因子失敗: {e}")
            return FactorScore(
                factor_type=FactorType.QUALITY,
                score=0.0,
                weight=self.factor_weights[FactorType.QUALITY],
                details={"error": str(e)}
            )

    def _calculate_size_factor(self, stock_id: str, stock_data: Dict) -> FactorScore:
        """計算規模因子分數"""
        try:
            market_cap = stock_data.get("market_cap", 0)
            
            # 市值分數：市值越小越好（小型股效應）
            # < 100億: 1分, 100-500億: 0.5分, 500-1000億: 0分, > 1000億: -0.5分
            if market_cap and market_cap > 0:
                market_cap_billion = market_cap / 1e8  # 轉換為億
                
                if market_cap_billion < 100:
                    score = 1.0
                elif market_cap_billion < 500:
                    score = 0.5
                elif market_cap_billion < 1000:
                    score = 0.0
                else:
                    score = -0.5
            else:
                score = 0.0
            
            return FactorScore(
                factor_type=FactorType.SIZE,
                score=float(score),
                weight=self.factor_weights[FactorType.SIZE],
                details={
                    "market_cap": float(market_cap),
                    "market_cap_billion": float(market_cap / 1e8) if market_cap else 0
                }
            )
            
        except Exception as e:
            logger.error(f"計算規模因子失敗: {e}")
            return FactorScore(
                factor_type=FactorType.SIZE,
                score=0.0,
                weight=self.factor_weights[FactorType.SIZE],
                details={"error": str(e)}
            )

    def _calculate_liquidity_factor(self, stock_data: Dict) -> FactorScore:
        """計算流動性因子分數"""
        try:
            history = stock_data.get("history", pd.DataFrame())
            if history.empty:
                return FactorScore(
                    factor_type=FactorType.LIQUIDITY,
                    score=0.0,
                    weight=self.factor_weights[FactorType.LIQUIDITY],
                    details={"error": "無歷史資料"}
                )
            
            # 計算成交量比率
            volume_ratio = history["volume_ratio"].iloc[-1] if "volume_ratio" in history.columns else 1.0
            
            # 成交量比率分數：成交量比率越高越好
            # > 2: 1分, 1.5-2: 0.5分, 1-1.5: 0分, < 1: -0.5分
            if volume_ratio and volume_ratio > 0:
                if volume_ratio > 2:
                    score = 1.0
                elif volume_ratio > 1.5:
                    score = 0.5
                elif volume_ratio > 1:
                    score = 0.0
                else:
                    score = -0.5
            else:
                score = -0.5
            
            return FactorScore(
                factor_type=FactorType.LIQUIDITY,
                score=float(score),
                weight=self.factor_weights[FactorType.LIQUIDITY],
                details={
                    "volume_ratio": float(volume_ratio)
                }
            )
            
        except Exception as e:
            logger.error(f"計算流動性因子失敗: {e}")
            return FactorScore(
                factor_type=FactorType.LIQUIDITY,
                score=0.0,
                weight=self.factor_weights[FactorType.LIQUIDITY],
                details={"error": str(e)}
            )

    def _calculate_institutional_factor(self, stock_id: str, stock_data: Dict) -> FactorScore:
        """計算法人因子分數"""
        try:
            # 嘗試從 FinMind 取得三大法人資料
            clean_id = stock_id.replace(".TW", "").replace(".TWO", "")
            
            try:
                institutional_data = self.finmind_fetcher.get_institutional_investors(clean_id)
                if institutional_data.get("success") and not institutional_data["data"].empty:
                    df = institutional_data["data"]
                    
                    # 計算最近 5 天的法人買賣超
                    recent_data = df.tail(5)
                    
                    # 計算總買賣超金額
                    total_buy = 0
                    total_sell = 0
                    
                    for _, row in recent_data.iterrows():
                        if "buy" in row and "sell" in row:
                            total_buy += row["buy"]
                            total_sell += row["sell"]
                    
                    net_buy = total_buy - total_buy
                    
                    # 淨買超分數
                    if net_buy > 0:
                        score = min(net_buy / 1e8, 1.0)  # 淨買超金額（億）
                    else:
                        score = max(net_buy / 1e8, -1.0)
                    
                    return FactorScore(
                        factor_type=FactorType.INSTITUTIONAL,
                        score=float(score),
                        weight=self.factor_weights[FactorType.INSTITUTIONAL],
                        details={
                            "total_buy": float(total_buy),
                            "total_sell": float(total_sell),
                            "net_buy": float(net_buy)
                        }
                    )
                    
            except Exception as e:
                logger.debug(f"FinMind 法人資料取得失敗: {e}")
            
            # 如果無法取得法人資料，返回中性分數
            return FactorScore(
                factor_type=FactorType.INSTITUTIONAL,
                score=0.0,
                weight=self.factor_weights[FactorType.INSTITUTIONAL],
                details={"error": "無法取得法人資料"}
            )
            
        except Exception as e:
            logger.error(f"計算法人因子失敗: {e}")
            return FactorScore(
                factor_type=FactorType.INSTITUTIONAL,
                score=0.0,
                weight=self.factor_weights[FactorType.INSTITUTIONAL],
                details={"error": str(e)}
            )

    def _calculate_composite_score(self, factor_scores: List[FactorScore]) -> float:
        """計算綜合分數"""
        try:
            total_score = 0.0
            total_weight = 0.0
            
            for factor_score in factor_scores:
                total_score += factor_score.score * factor_score.weight
                total_weight += factor_score.weight
            
            if total_weight > 0:
                return total_score / total_weight
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"計算綜合分數失敗: {e}")
            return 0.0

    def _get_stock_name(self, stock_id: str) -> str:
        """取得股票名稱"""
        try:
            # 從 Yahoo Finance 取得股票名稱
            ticker = yf.Ticker(stock_id)
            info = ticker.info
            return info.get("longName", info.get("shortName", stock_id))
        except:
            return stock_id

    def get_factor_explanation(self) -> Dict:
        """取得因子解釋"""
        return {
            "momentum": {
                "name": "動量因子",
                "description": "追蹤股票價格趨勢，動量強的股票傾向繼續上漲",
                "metrics": ["20日報酬率", "60日報酬率"],
                "weight": self.factor_weights[FactorType.MOMENTUM]
            },
            "value": {
                "name": "價值因子",
                "description": "尋找被低估的股票，價值股長期表現優於成長股",
                "metrics": ["PE ratio", "PB ratio", "股利殖利率"],
                "weight": self.factor_weights[FactorType.VALUE]
            },
            "quality": {
                "name": "品質因子",
                "description": "選擇財務健全的公司，品質股在熊市中表現較佳",
                "metrics": ["ROE", "毛利率", "營收成長率"],
                "weight": self.factor_weights[FactorType.QUALITY]
            },
            "size": {
                "name": "規模因子",
                "description": "小型股長期表現優於大型股，但波動較大",
                "metrics": ["市值"],
                "weight": self.factor_weights[FactorType.SIZE]
            },
            "liquidity": {
                "name": "流動性因子",
                "description": "流動性高的股票交易成本較低，價差較小",
                "metrics": ["成交量比率"],
                "weight": self.factor_weights[FactorType.LIQUIDITY]
            },
            "institutional": {
                "name": "法人因子",
                "description": "法人買賣超反映機構投資人的看法",
                "metrics": ["三大法人買賣超"],
                "weight": self.factor_weights[FactorType.INSTITUTIONAL]
            }
        }

    def update_weights(self, new_weights: Dict[FactorType, float]):
        """更新因子權重"""
        try:
            # 驗證權重
            total_weight = sum(new_weights.values())
            if abs(total_weight - 1.0) > 0.01:
                logger.warning(f"因子權重總和為 {total_weight}，將自動正規化")
                for factor_type in new_weights:
                    new_weights[factor_type] /= total_weight
            
            self.factor_weights.update(new_weights)
            logger.info(f"因子權重更新: {self.factor_weights}")
            
        except Exception as e:
            logger.error(f"更新因子權重失敗: {e}")


# 全局實例
_multi_factor_screener = None


def get_multi_factor_screener() -> MultiFactorScreener:
    """取得 MultiFactorScreener 單例"""
    global _multi_factor_screener
    if _multi_factor_screener is None:
        _multi_factor_screener = MultiFactorScreener()
    return _multi_factor_screener
