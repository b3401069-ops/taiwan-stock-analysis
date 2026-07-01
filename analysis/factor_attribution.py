"""
台灣股票分析工具 - 五因子歸因分析
Momentum/Reversal/Quality/Size/Liquidity 五因子歸因
參考 taiwan-quant-project 的 backtest/attribution.py
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from loguru import logger
import yfinance as yf
from sklearn.linear_model import LinearRegression

from data.data_fetcher import DataFetcher
from data.finmind_fetcher import get_finmind_fetcher


@dataclass
class FactorExposure:
    """因子暴露"""
    factor_name: str
    exposure: float  # 因子暴露（-1 到 1）
    contribution: float  # 因子貢獻（%）
    significance: float  # 顯著性（t-statistic）
    p_value: float  # p-value


@dataclass
class AttributionResult:
    """歸因分析結果"""
    portfolio_id: str
    period_start: str
    period_end: str
    total_return: float
    alpha: float  # 超額報酬
    factor_exposures: List[FactorExposure]
    r_squared: float  # R-squared
    residual_return: float  # 殘差報酬
    details: Dict


class FactorAttribution:
    """五因子歸因分析"""

    def __init__(self):
        """初始化五因子歸因分析"""
        self.data_fetcher = DataFetcher()
        self.finmind_fetcher = get_finmind_fetcher()
        
        # 因子定義
        self.factors = {
            "momentum": self._calculate_momentum_factor,
            "reversal": self._calculate_reversal_factor,
            "quality": self._calculate_quality_factor,
            "size": self._calculate_size_factor,
            "liquidity": self._calculate_liquidity_factor
        }

    def analyze(
        self,
        portfolio_returns: pd.Series,
        factor_returns: Dict[str, pd.Series],
        risk_free_rate: float = 0.02
    ) -> AttributionResult:
        """
        執行五因子歸因分析
        
        Args:
            portfolio_returns: 投資組合報酬率（時間序列）
            factor_returns: 因子報酬率（字典，key為因子名稱，value為報酬率時間序列）
            risk_free_rate: 無風險利率（年化）
            
        Returns:
            歸因分析結果
        """
        try:
            logger.info("開始五因子歸因分析...")
            
            # 對齊時間序列
            aligned_data = self._align_time_series(portfolio_returns, factor_returns)
            
            if aligned_data is None:
                raise ValueError("無法對齊時間序列")
            
            # 準備回歸資料
            X = aligned_data["factors"]  # 因子報酬率矩陣
            y = aligned_data["portfolio"]  # 投資組合報酬率
            
            # 執行回歸分析
            regression_result = self._run_regression(X, y, risk_free_rate)
            
            # 計算因子暴露和貢獻
            factor_exposures = self._calculate_factor_exposures(
                regression_result, factor_returns
            )
            
            # 計算 alpha
            alpha = regression_result["intercept"]
            
            # 計算殘差報酬
            residual_return = regression_result["residual"].mean() * 252  # 年化
            
            # 計算總報酬
            total_return = portfolio_returns.mean() * 252  # 年化
            
            result = AttributionResult(
                portfolio_id="portfolio",
                period_start=str(portfolio_returns.index[0]),
                period_end=str(portfolio_returns.index[-1]),
                total_return=float(total_return),
                alpha=float(alpha),
                factor_exposures=factor_exposures,
                r_squared=float(regression_result["r_squared"]),
                residual_return=float(residual_return),
                details={
                    "regression_coefficients": regression_result["coefficients"],
                    "regression_std_errors": regression_result["std_errors"],
                    "regression_t_stats": regression_result["t_stats"],
                    "regression_p_values": regression_result["p_values"],
                    "observations": len(y)
                }
            )
            
            logger.info(f"五因子歸因分析完成，R² = {regression_result['r_squared']:.3f}")
            
            return result
            
        except Exception as e:
            logger.error(f"五因子歸因分析失敗: {e}")
            raise

    def analyze_stock(
        self,
        stock_id: str,
        benchmark_id: str = "^TWII",  # 台灣加權指數
        period: str = "2y",
        risk_free_rate: float = 0.02
    ) -> AttributionResult:
        """
        分析單一股票的因子歸因
        
        Args:
            stock_id: 股票代碼
            benchmark_id: 基準指數代碼
            period: 分析期間
            risk_free_rate: 無風險利率
            
        Returns:
            歸因分析結果
        """
        try:
            logger.info(f"分析 {stock_id} 的因子歸因...")
            
            # 取得股票報酬率
            stock_returns = self._get_stock_returns(stock_id, period)
            
            # 計算因子報酬率
            factor_returns = self._calculate_factor_returns(stock_id, period)
            
            if stock_returns is None or not factor_returns:
                raise ValueError("無法取得股票或因子報酬率")
            
            # 執行歸因分析
            result = self.analyze(stock_returns, factor_returns, risk_free_rate)
            result.portfolio_id = stock_id
            
            return result
            
        except Exception as e:
            logger.error(f"分析 {stock_id} 因子歸因失敗: {e}")
            raise

    def analyze_portfolio(
        self,
        stock_ids: List[str],
        weights: List[float] = None,
        period: str = "2y",
        risk_free_rate: float = 0.02
    ) -> AttributionResult:
        """
        分析投資組合的因子歸因
        
        Args:
            stock_ids: 股票代碼列表
            weights: 權重列表
            period: 分析期間
            risk_free_rate: 無風險利率
            
        Returns:
            歸因分析結果
        """
        try:
            logger.info(f"分析投資組合的因子歸因: {stock_ids}")
            
            n = len(stock_ids)
            if weights is None:
                weights = [1.0 / n] * n
            elif len(weights) != n:
                raise ValueError("權重數量必須等於股票數量")
            
            # 正規化權重
            total_weight = sum(weights)
            weights = [w / total_weight for w in weights]
            
            # 取得所有股票報酬率
            all_returns = {}
            for stock_id in stock_ids:
                returns = self._get_stock_returns(stock_id, period)
                if returns is not None:
                    all_returns[stock_id] = returns
            
            if not all_returns:
                raise ValueError("無法取得任何股票報酬率")
            
            # 計算投資組合報酬率
            portfolio_returns = self._calculate_portfolio_returns(all_returns, weights)
            
            # 計算因子報酬率（使用第一檔股票作為代表）
            representative_stock = list(all_returns.keys())[0]
            factor_returns = self._calculate_factor_returns(representative_stock, period)
            
            # 執行歸因分析
            result = self.analyze(portfolio_returns, factor_returns, risk_free_rate)
            result.portfolio_id = f"Portfolio ({len(stock_ids)} stocks)"
            
            return result
            
        except Exception as e:
            logger.error(f"分析投資組合因子歸因失敗: {e}")
            raise

    def _align_time_series(
        self,
        portfolio_returns: pd.Series,
        factor_returns: Dict[str, pd.Series]
    ) -> Optional[Dict]:
        """對齊時間序列"""
        try:
            # 找出共同日期
            common_dates = portfolio_returns.index
            for factor_name, returns in factor_returns.items():
                common_dates = common_dates.intersection(returns.index)
            
            if len(common_dates) < 30:
                logger.warning("共同日期不足30天")
                return None
            
            # 對齊資料
            aligned_portfolio = portfolio_returns.loc[common_dates]
            aligned_factors = {}
            
            for factor_name, returns in factor_returns.items():
                aligned_factors[factor_name] = returns.loc[common_dates]
            
            # 建立因子矩陣
            factor_matrix = pd.DataFrame(aligned_factors)
            
            return {
                "portfolio": aligned_portfolio,
                "factors": factor_matrix,
                "dates": common_dates
            }
            
        except Exception as e:
            logger.error(f"對齊時間序列失敗: {e}")
            return None

    def _run_regression(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        risk_free_rate: float
    ) -> Dict:
        """執行回歸分析"""
        try:
            # 計算超額報酬（減去無風險利率）
            daily_risk_free = risk_free_rate / 252
            y_excess = y - daily_risk_free
            
            # 執行線性回歸
            model = LinearRegression()
            model.fit(X, y_excess)
            
            # 預測
            y_pred = model.predict(X)
            
            # 計算殘差
            residuals = y_excess - y_pred
            
            # 計算 R-squared
            ss_res = np.sum(residuals ** 2)
            ss_tot = np.sum((y_excess - np.mean(y_excess)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            
            # 計算標準誤差
            n = len(y)
            p = X.shape[1]
            
            if n > p + 1:
                mse = ss_res / (n - p - 1)
                var_coef = mse * np.linalg.inv(X.T @ X).diagonal()
                std_errors = np.sqrt(var_coef)
                
                # 計算 t-statistics 和 p-values
                t_stats = model.coef_ / std_errors
                from scipy import stats
                p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), df=n-p-1))
            else:
                std_errors = np.zeros(p)
                t_stats = np.zeros(p)
                p_values = np.ones(p)
            
            return {
                "coefficients": model.coef_.tolist(),
                "intercept": model.intercept_,
                "std_errors": std_errors.tolist(),
                "t_stats": t_stats.tolist(),
                "p_values": p_values.tolist(),
                "r_squared": float(r_squared),
                "residual": residuals,
                "predictions": y_pred
            }
            
        except Exception as e:
            logger.error(f"回歸分析失敗: {e}")
            raise

    def _calculate_factor_exposures(
        self,
        regression_result: Dict,
        factor_returns: Dict[str, pd.Series]
    ) -> List[FactorExposure]:
        """計算因子暴露和貢獻"""
        try:
            factor_names = list(factor_returns.keys())
            coefficients = regression_result["coefficients"]
            std_errors = regression_result["std_errors"]
            t_stats = regression_result["t_stats"]
            p_values = regression_result["p_values"]
            
            exposures = []
            
            for i, factor_name in enumerate(factor_names):
                if i < len(coefficients):
                    exposure = coefficients[i]
                    contribution = exposure * factor_returns[factor_name].mean() * 252  # 年化貢獻
                    significance = t_stats[i]
                    p_value = p_values[i]
                    
                    exposures.append(FactorExposure(
                        factor_name=factor_name,
                        exposure=float(exposure),
                        contribution=float(contribution),
                        significance=float(significance),
                        p_value=float(p_value)
                    ))
            
            return exposures
            
        except Exception as e:
            logger.error(f"計算因子暴露失敗: {e}")
            return []

    def _get_stock_returns(self, stock_id: str, period: str) -> Optional[pd.Series]:
        """取得股票報酬率"""
        try:
            ticker = yf.Ticker(stock_id)
            df = ticker.history(period=period)
            
            if df.empty:
                return None
            
            # 計算日報酬率
            returns = df["Close"].pct_change().dropna()
            returns.name = stock_id
            
            return returns
            
        except Exception as e:
            logger.error(f"取得 {stock_id} 報酬率失敗: {e}")
            return None

    def _calculate_portfolio_returns(
        self,
        all_returns: Dict[str, pd.Series],
        weights: List[float]
    ) -> pd.Series:
        """計算投資組合報酬率"""
        try:
            # 對齊時間序列
            common_dates = None
            for stock_id, returns in all_returns.items():
                if common_dates is None:
                    common_dates = set(returns.index)
                else:
                    common_dates = common_dates.intersection(set(returns.index))
            
            common_dates = sorted(common_dates)
            
            # 計算加權報酬率
            portfolio_returns = pd.Series(0.0, index=common_dates)
            
            for i, (stock_id, returns) in enumerate(all_returns.items()):
                aligned_returns = returns.loc[common_dates]
                portfolio_returns += aligned_returns * weights[i]
            
            return portfolio_returns
            
        except Exception as e:
            logger.error(f"計算投資組合報酬率失敗: {e}")
            return pd.Series()

    def _calculate_factor_returns(self, stock_id: str, period: str) -> Dict[str, pd.Series]:
        """計算因子報酬率"""
        try:
            # 取得股票資料
            ticker = yf.Ticker(stock_id)
            df = ticker.history(period=period)
            
            if df.empty:
                return {}
            
            # 計算技術指標
            df = self._add_technical_indicators(df)
            
            # 計算因子報酬率
            factor_returns = {}
            
            # 1. 動量因子（20日報酬率）
            momentum = df["Close"].pct_change(periods=20)
            factor_returns["momentum"] = momentum
            
            # 2. 反轉因子（5日報酬率的負值）
            reversal = -df["Close"].pct_change(periods=5)
            factor_returns["reversal"] = reversal
            
            # 3. 品質因子（ROE 的代理指標，使用報酬率波動率的負值）
            volatility = df["Close"].pct_change().rolling(window=20).std()
            quality = -volatility  # 低波動率 = 高品質
            factor_returns["quality"] = quality
            
            # 4. 規模因子（市值的代理指標，使用成交量）
            volume = df["Volume"]
            size = -volume / volume.rolling(window=20).mean()  # 低成交量 = 小型股
            factor_returns["size"] = size
            
            # 5. 流動性因子（成交量比率）
            volume_ratio = df["Volume"] / df["Volume"].rolling(window=20).mean()
            factor_returns["liquidity"] = volume_ratio
            
            # 清理資料
            for factor_name in factor_returns:
                factor_returns[factor_name] = factor_returns[factor_name].dropna()
            
            return factor_returns
            
        except Exception as e:
            logger.error(f"計算因子報酬率失敗: {e}")
            return {}

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

    def _calculate_momentum_factor(self, df: pd.DataFrame) -> pd.Series:
        """計算動量因子"""
        return df["Close"].pct_change(periods=20)

    def _calculate_reversal_factor(self, df: pd.DataFrame) -> pd.Series:
        """計算反轉因子"""
        return -df["Close"].pct_change(periods=5)

    def _calculate_quality_factor(self, df: pd.DataFrame) -> pd.Series:
        """計算品質因子"""
        volatility = df["Close"].pct_change().rolling(window=20).std()
        return -volatility

    def _calculate_size_factor(self, df: pd.DataFrame) -> pd.Series:
        """計算規模因子"""
        volume = df["Volume"]
        return -volume / volume.rolling(window=20).mean()

    def _calculate_liquidity_factor(self, df: pd.DataFrame) -> pd.Series:
        """計算流動性因子"""
        return df["Volume"] / df["Volume"].rolling(window=20).mean()

    def to_dict(self, result: AttributionResult) -> Dict:
        """將結果轉換為字典"""
        try:
            factor_exposures_dict = []
            for exposure in result.factor_exposures:
                factor_exposures_dict.append({
                    "factor_name": exposure.factor_name,
                    "exposure": f"{exposure.exposure:.3f}",
                    "contribution": f"{exposure.contribution:.3f}%",
                    "significance": f"{exposure.significance:.2f}",
                    "p_value": f"{exposure.p_value:.3f}",
                    "significant": exposure.p_value < 0.05
                })
            
            return {
                "portfolio_id": result.portfolio_id,
                "period": f"{result.period_start} ~ {result.period_end}",
                "total_return": f"{result.total_return:.2f}%",
                "alpha": f"{result.alpha:.3f}%",
                "r_squared": f"{result.r_squared:.3f}",
                "residual_return": f"{result.residual_return:.3f}%",
                "factor_exposures": factor_exposures_dict,
                "details": result.details
            }
            
        except Exception as e:
            logger.error(f"結果轉換失敗: {e}")
            return {}

    def get_factor_explanation(self) -> Dict:
        """取得因子解釋"""
        return {
            "momentum": {
                "name": "動量因子 (Momentum)",
                "description": "追蹤股票價格趨勢，動量強的股票傾向繼續上漲",
                "calculation": "20日報酬率",
                "interpretation": "正暴露表示追漲，負暴露表示追跌"
            },
            "reversal": {
                "name": "反轉因子 (Reversal)",
                "description": "短期反轉效應，近期下跌的股票傾向反彈",
                "calculation": "5日報酬率的負值",
                "interpretation": "正暴露表示買入近期下跌股票"
            },
            "quality": {
                "name": "品質因子 (Quality)",
                "description": "選擇財務健全的公司，品質股在熊市中表現較佳",
                "calculation": "報酬率波動率的負值",
                "interpretation": "正暴露表示偏好低波動股票"
            },
            "size": {
                "name": "規模因子 (Size)",
                "description": "小型股長期表現優於大型股，但波動較大",
                "calculation": "成交量的負值（代理指標）",
                "interpretation": "正暴露表示偏好小型股"
            },
            "liquidity": {
                "name": "流動性因子 (Liquidity)",
                "description": "流動性高的股票交易成本較低，價差較小",
                "calculation": "成交量比率",
                "interpretation": "正暴露表示偏好高流動性股票"
            }
        }


# 全局實例
_factor_attribution = None


def get_factor_attribution() -> FactorAttribution:
    """取得 FactorAttribution 單例"""
    global _factor_attribution
    if _factor_attribution is None:
        _factor_attribution = FactorAttribution()
    return _factor_attribution
