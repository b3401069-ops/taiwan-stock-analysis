"""
台灣股票分析工具 - Walk-Forward 驗證引擎
滾動窗口訓練/測試，避免過擬合
參考 taiwan-quant-project 的 backtest/walk_forward.py
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yfinance as yf
from loguru import logger

from analysis.backtest import STRATEGIES, BacktestEngine, BacktestResult


@dataclass
class WalkForwardResult:
    """Walk-Forward 驗證結果"""

    strategy_name: str
    stock_id: str
    total_periods: int
    avg_return: float
    avg_max_drawdown: float
    avg_win_rate: float
    avg_sharpe_ratio: float
    return_std: float
    max_drawdown_std: float
    win_rate_std: float
    sharpe_std: float
    period_results: List[Dict]
    overall_metrics: Dict


class WalkForwardValidator:
    """Walk-Forward 驗證器"""

    def __init__(self, commission_rate: float = 0.001425, tax_rate: float = 0.003):
        """
        初始化 Walk-Forward 驗證器

        Args:
            commission_rate: 手續費率
            tax_rate: 證交稅
        """
        self.commission_rate = commission_rate
        self.tax_rate = tax_rate
        self.backtest_engine = BacktestEngine(commission_rate, tax_rate)

    def validate(
        self,
        stock_id: str,
        strategy: Callable,
        train_window: int = 252,  # 訓練窗口（交易日，約1年）
        test_window: int = 63,  # 測試窗口（交易日，約1季）
        step_size: int = 21,  # 步進大小（交易日，約1月）
        total_years: int = 5,  # 總回測年數
        initial_capital: float = 1000000,
    ) -> WalkForwardResult:
        """
        執行 Walk-Forward 驗證

        Args:
            stock_id: 股票代碼
            strategy: 策略函數
            train_window: 訓練窗口大小（交易日）
            test_window: 測試窗口大小（交易日）
            step_size: 步進大小（交易日）
            total_years: 總回測年數
            initial_capital: 初始資金

        Returns:
            Walk-Forward 驗證結果
        """
        try:
            logger.info(
                f"開始 Walk-Forward 驗證: {stock_id}, 策略: {strategy.__name__}"
            )

            # 取得歷史資料
            ticker = yf.Ticker(stock_id)
            df = ticker.history(period=f"{total_years}y")

            if df.empty:
                raise ValueError(f"無法取得 {stock_id} 的歷史資料")

            # 準備資料
            df.columns = [c.lower() for c in df.columns]
            df.index.name = "date"

            # 計算技術指標
            df = self._add_indicators(df)

            # 初始化結果列表
            period_results = []

            # 滾動窗口驗證
            start_idx = train_window
            end_idx = len(df) - test_window

            period_count = 0

            while start_idx < end_idx:
                try:
                    # 定義訓練和測試期間
                    train_start = start_idx - train_window
                    train_end = start_idx
                    test_start = start_idx
                    test_end = min(start_idx + test_window, len(df))

                    # 提取訓練和測試資料
                    train_data = df.iloc[train_start:train_end].copy()
                    test_data = df.iloc[test_start:test_end].copy()

                    if (
                        len(train_data) < train_window * 0.8
                        or len(test_data) < test_window * 0.5
                    ):
                        start_idx += step_size
                        continue

                    # 在訓練期間優化策略參數（簡化版本）
                    optimized_params = self._optimize_strategy_params(
                        train_data, strategy
                    )

                    # 在測試期間執行策略
                    test_result = self._run_test_period(
                        test_data, strategy, optimized_params, initial_capital
                    )

                    if test_result is not None:
                        period_results.append(test_result)
                        period_count += 1

                    # 步進
                    start_idx += step_size

                except Exception as e:
                    logger.warning(f"Walk-Forward 期間 {period_count} 失敗: {e}")
                    start_idx += step_size
                    continue

            if not period_results:
                raise ValueError("Walk-Forward 驗證無有效結果")

            # 計算整體指標
            overall_metrics = self._calculate_overall_metrics(period_results)

            # 計算平均指標
            avg_return = np.mean([r["total_return"] for r in period_results])
            avg_max_drawdown = np.mean([r["max_drawdown"] for r in period_results])
            avg_win_rate = np.mean([r["win_rate"] for r in period_results])
            avg_sharpe = np.mean([r["sharpe_ratio"] for r in period_results])

            # 計算標準差
            return_std = np.std([r["total_return"] for r in period_results])
            max_drawdown_std = np.std([r["max_drawdown"] for r in period_results])
            win_rate_std = np.std([r["win_rate"] for r in period_results])
            sharpe_std = np.std([r["sharpe_ratio"] for r in period_results])

            result = WalkForwardResult(
                strategy_name=strategy.__name__,
                stock_id=stock_id,
                total_periods=period_count,
                avg_return=float(avg_return),
                avg_max_drawdown=float(avg_max_drawdown),
                avg_win_rate=float(avg_win_rate),
                avg_sharpe_ratio=float(avg_sharpe),
                return_std=float(return_std),
                max_drawdown_std=float(max_drawdown_std),
                win_rate_std=float(win_rate_std),
                sharpe_std=float(sharpe_std),
                period_results=period_results,
                overall_metrics=overall_metrics,
            )

            logger.info(
                f"Walk-Forward 驗證完成: {period_count} 個期間，平均報酬率 {avg_return:.2f}%"
            )

            return result

        except Exception as e:
            logger.error(f"Walk-Forward 驗證失敗: {e}")
            raise

    def _add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """計算技術指標"""
        try:
            # 移動平均
            df["ma5"] = df["close"].rolling(5).mean()
            df["ma10"] = df["close"].rolling(10).mean()
            df["ma20"] = df["close"].rolling(20).mean()
            df["ma60"] = df["close"].rolling(60).mean()

            # RSI
            delta = df["close"].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            df["rsi"] = 100 - (100 / (1 + gain / loss))

            # MACD
            ema12 = df["close"].ewm(span=12).mean()
            ema26 = df["close"].ewm(span=26).mean()
            df["macd"] = ema12 - ema26
            df["macd_signal"] = df["macd"].ewm(span=9).mean()
            df["macd_histogram"] = df["macd"] - df["macd_signal"]

            # 布林通道
            df["bb_middle"] = df["close"].rolling(20).mean()
            bb_std = df["close"].rolling(20).std()
            df["bb_upper"] = df["bb_middle"] + 2 * bb_std
            df["bb_lower"] = df["bb_middle"] - 2 * bb_std

            # 成交量指標
            df["volume_ma"] = df["volume"].rolling(20).mean()
            df["volume_ratio"] = df["volume"] / df["volume_ma"]

            return df

        except Exception as e:
            logger.error(f"計算技術指標失敗: {e}")
            return df

    def _optimize_strategy_params(
        self, train_data: pd.DataFrame, strategy: Callable
    ) -> Dict:
        """
        在訓練期間優化策略參數（簡化版本）

        Args:
            train_data: 訓練資料
            strategy: 策略函數

        Returns:
            優化後的參數
        """
        try:
            # 簡化版本：返回預設參數
            # 實際應用中可以進行網格搜索或貝葉斯優化
            return {
                "rsi_oversold": 30,
                "rsi_overbought": 70,
                "macd_threshold": 0,
                "bb_std": 2,
            }

        except Exception as e:
            logger.warning(f"策略參數優化失敗: {e}")
            return {}

    def _run_test_period(
        self,
        test_data: pd.DataFrame,
        strategy: Callable,
        params: Dict,
        initial_capital: float,
    ) -> Optional[Dict]:
        """
        在測試期間執行策略

        Args:
            test_data: 測試資料
            strategy: 策略函數
            params: 策略參數
            initial_capital: 初始資金

        Returns:
            測試結果
        """
        try:
            # 模擬交易
            capital = initial_capital
            shares = 0
            trades = []
            equity_curve = []

            for i in range(20, len(test_data)):
                current_date = test_data.index[i]
                current_price = test_data["close"].iloc[i]

                # 取得策略信號
                signal_data = test_data.iloc[: i + 1]
                signal = strategy(signal_data)

                # 執行交易
                if signal == "buy" and shares == 0:
                    # 買入
                    shares = int(capital * 0.9 / current_price / 1000) * 1000
                    if shares > 0:
                        commission = shares * current_price * self.commission_rate
                        capital -= shares * current_price + commission
                        trades.append(
                            {
                                "date": str(current_date.date()),
                                "action": "buy",
                                "price": current_price,
                                "shares": shares,
                            }
                        )

                elif signal == "sell" and shares > 0:
                    # 賣出
                    commission = shares * current_price * self.commission_rate
                    tax = shares * current_price * self.tax_rate
                    capital += shares * current_price - commission - tax

                    trades.append(
                        {
                            "date": str(current_date.date()),
                            "action": "sell",
                            "price": current_price,
                            "shares": shares,
                        }
                    )
                    shares = 0

                # 記錄資產曲線
                total_equity = capital + shares * current_price
                equity_curve.append(total_equity)

            if not equity_curve:
                return None

            # 計算績效指標
            final_equity = equity_curve[-1]
            total_return = (final_equity - initial_capital) / initial_capital * 100

            # 計算最大回撤
            equity_series = pd.Series(equity_curve)
            rolling_max = equity_series.expanding().max()
            drawdowns = (equity_series - rolling_max) / rolling_max * 100
            max_drawdown = drawdowns.min()

            # 計算勝率
            if trades:
                buy_prices = [t["price"] for t in trades if t["action"] == "buy"]
                sell_prices = [t["price"] for t in trades if t["action"] == "sell"]

                if buy_prices and sell_prices:
                    win_trades = sum(
                        1
                        for i in range(min(len(buy_prices), len(sell_prices)))
                        if sell_prices[i] > buy_prices[i]
                    )
                    win_rate = win_trades / min(len(buy_prices), len(sell_prices)) * 100
                else:
                    win_rate = 0
            else:
                win_rate = 0

            # 計算夏普比率（簡化）
            if len(equity_curve) > 1:
                returns = pd.Series(equity_curve).pct_change().dropna()
                if len(returns) > 0 and returns.std() > 0:
                    sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252)
                else:
                    sharpe_ratio = 0
            else:
                sharpe_ratio = 0

            return {
                "start_date": str(test_data.index[20].date()),
                "end_date": str(test_data.index[-1].date()),
                "initial_capital": initial_capital,
                "final_capital": float(final_equity),
                "total_return": float(total_return),
                "max_drawdown": float(max_drawdown),
                "win_rate": float(win_rate),
                "sharpe_ratio": float(sharpe_ratio),
                "total_trades": len(trades),
                "trades": trades,
            }

        except Exception as e:
            logger.error(f"測試期間執行失敗: {e}")
            return None

    def _calculate_overall_metrics(self, period_results: List[Dict]) -> Dict:
        """計算整體指標"""
        try:
            returns = [r["total_return"] for r in period_results]
            drawdowns = [r["max_drawdown"] for r in period_results]
            win_rates = [r["win_rate"] for r in period_results]
            sharpes = [r["sharpe_ratio"] for r in period_results]

            # 計算複合報酬率
            compound_return = 1.0
            for r in returns:
                compound_return *= 1 + r / 100
            compound_return = (compound_return - 1) * 100

            # 計算報酬率穩定性
            return_stability = (
                np.std(returns) / np.mean(returns) if np.mean(returns) != 0 else 0
            )

            # 計算風險調整後報酬
            risk_adjusted_return = (
                np.mean(returns) / np.std(returns) if np.std(returns) != 0 else 0
            )

            return {
                "compound_return": float(compound_return),
                "return_stability": float(return_stability),
                "risk_adjusted_return": float(risk_adjusted_return),
                "positive_periods": sum(1 for r in returns if r > 0),
                "negative_periods": sum(1 for r in returns if r < 0),
                "best_period_return": float(max(returns)),
                "worst_period_return": float(min(returns)),
                "avg_drawdown": float(np.mean(drawdowns)),
                "max_drawdown": float(min(drawdowns)),
                "avg_win_rate": float(np.mean(win_rates)),
                "avg_sharpe": float(np.mean(sharpes)),
            }

        except Exception as e:
            logger.error(f"計算整體指標失敗: {e}")
            return {}

    def to_dict(self, result: WalkForwardResult) -> Dict:
        """將結果轉換為字典"""
        try:
            return {
                "strategy_name": result.strategy_name,
                "stock_id": result.stock_id,
                "total_periods": result.total_periods,
                "avg_return": f"{result.avg_return:.2f}%",
                "avg_max_drawdown": f"{result.avg_max_drawdown:.2f}%",
                "avg_win_rate": f"{result.avg_win_rate:.1f}%",
                "avg_sharpe_ratio": f"{result.avg_sharpe_ratio:.2f}",
                "return_std": f"{result.return_std:.2f}%",
                "max_drawdown_std": f"{result.max_drawdown_std:.2f}%",
                "win_rate_std": f"{result.win_rate_std:.2f}%",
                "sharpe_std": f"{result.sharpe_std:.2f}",
                "overall_metrics": result.overall_metrics,
                "period_results": result.period_results[-5:],  # 只返回最後5個期間
            }

        except Exception as e:
            logger.error(f"結果轉換失敗: {e}")
            return {}


# 全局實例
_walk_forward_validator = None


def get_walk_forward_validator() -> WalkForwardValidator:
    """取得 WalkForwardValidator 單例"""
    global _walk_forward_validator
    if _walk_forward_validator is None:
        _walk_forward_validator = WalkForwardValidator()
    return _walk_forward_validator
