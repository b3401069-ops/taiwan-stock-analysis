"""
台灣股票分析工具 - 進階回測系統
包含：組合回測、參數優化、停損停利、跨市場測試
"""

from datetime import datetime
from itertools import product
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yfinance as yf
from loguru import logger

from analysis.backtest import STRATEGIES, BacktestEngine, BacktestResult, Trade


class AdvancedBacktestEngine(BacktestEngine):
    """進階回測引擎"""

    # ──────────────────────────────────────────────
    #  1. 組合策略回測
    # ──────────────────────────────────────────────

    def run_portfolio(
        self,
        stock_ids: List[str],
        strategy: Callable,
        weights: List[float] = None,
        period: str = "2y",
        initial_capital: float = 1000000,
        rebalance_days: int = 20,
    ) -> Dict:
        """
        組合策略回測

        Args:
            stock_ids: 股票代碼列表
            strategy: 策略函數
            weights: 權重列表（預設平均分配）
            period: 回測期間
            initial_capital: 初始資金
            rebalance_days: 再平衡天數

        Returns:
            組合回測結果
        """
        n = len(stock_ids)
        if weights is None:
            weights = [1.0 / n] * n
        elif len(weights) != n:
            raise ValueError("權重數量必須等於股票數量")

        # 正規化權重
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]

        logger.info(f"開始組合回測: {stock_ids}, 權重: {weights}")

        # 下載所有股票資料
        all_data = {}
        for stock_id in stock_ids:
            try:
                ticker = yf.Ticker(stock_id)
                df = ticker.history(period=period)
                if not df.empty:
                    df.columns = [c.lower() for c in df.columns]
                    df = self._add_indicators(df)
                    all_data[stock_id] = df
            except Exception as e:
                logger.warning(f"下載 {stock_id} 失敗: {e}")

        if not all_data:
            raise ValueError("無法下載任何股票資料")

        # 找出共同日期
        common_dates = None
        for stock_id, df in all_data.items():
            if common_dates is None:
                common_dates = set(df.index)
            else:
                common_dates = common_dates.intersection(set(df.index))

        common_dates = sorted(common_dates)

        if len(common_dates) < 60:
            raise ValueError("共同交易日不足")

        # 初始化
        capital = initial_capital
        positions = {sid: 0 for sid in all_data.keys()}  # 每檔股票的持股數
        buy_prices = {sid: 0 for sid in all_data.keys()}
        trades = []
        equity_curve = []
        last_rebalance = 0

        # 模擬交易
        for i in range(60, len(common_dates)):
            current_date = common_dates[i]
            total_equity = capital

            # 計算每檔股票的信號和資產價值
            signals = {}
            for stock_id, df in all_data.items():
                if current_date in df.index:
                    idx = df.index.get_loc(current_date)
                    current_df = df.iloc[: idx + 1]
                    signal = strategy(current_df)
                    signals[stock_id] = signal

                    current_price = df.loc[current_date, "close"]
                    total_equity += positions[stock_id] * current_price

            # 記錄資產曲線
            equity_curve.append(
                {
                    "date": str(current_date.date()),
                    "equity": total_equity,
                    "capital": capital,
                }
            )

            # 再平衡或策略信號交易
            days_since_rebalance = i - last_rebalance

            if days_since_rebalance >= rebalance_days:
                # 再平衡：按權重重新分配
                last_rebalance = i
                logger.debug(f"再平衡: {current_date.date()}")

                # 賣出所有持股
                for stock_id in all_data.keys():
                    if positions[stock_id] > 0:
                        df = all_data[stock_id]
                        if current_date in df.index:
                            price = df.loc[current_date, "close"]
                            revenue = positions[stock_id] * price
                            commission = revenue * self.commission_rate
                            tax = revenue * self.tax_rate
                            capital += revenue - commission - tax

                            trades.append(
                                Trade(
                                    date=str(current_date.date()),
                                    action="sell",
                                    price=price,
                                    shares=positions[stock_id],
                                    value=revenue,
                                    commission=commission + tax,
                                    reason="再平衡",
                                )
                            )
                            positions[stock_id] = 0

                # 按權重買入
                for stock_id, weight in zip(all_data.keys(), weights):
                    df = all_data[stock_id]
                    if current_date in df.index:
                        price = df.loc[current_date, "close"]
                        target_value = total_equity * weight
                        shares = int(target_value / price)

                        if shares > 0:
                            cost = shares * price
                            commission = cost * self.commission_rate
                            if cost + commission <= capital:
                                capital -= cost + commission
                                positions[stock_id] = shares
                                buy_prices[stock_id] = price

                                trades.append(
                                    Trade(
                                        date=str(current_date.date()),
                                        action="buy",
                                        price=price,
                                        shares=shares,
                                        value=cost,
                                        commission=commission,
                                        reason=f"權重={weight:.1%}",
                                    )
                                )

        # 計算績效
        equity_series = pd.Series(
            [e["equity"] for e in equity_curve], index=[e["date"] for e in equity_curve]
        )

        final_capital = (
            equity_series.iloc[-1] if not equity_series.empty else initial_capital
        )
        total_return = (final_capital - initial_capital) / initial_capital * 100

        # 計算基準（等權重買入持有）
        benchmark_returns = []
        for stock_id, df in all_data.items():
            if len(df) >= 2:
                ret = (df["close"].iloc[-1] / df["close"].iloc[0] - 1) * 100
                benchmark_returns.append(ret)
        benchmark_return = np.mean(benchmark_returns) if benchmark_returns else 0

        return {
            "strategy": (
                strategy.__name__ if hasattr(strategy, "__name__") else "custom"
            ),
            "stocks": stock_ids,
            "weights": {sid: f"{w:.1%}" for sid, w in zip(stock_ids, weights)},
            "period": f"{common_dates[60].date()} ~ {common_dates[-1].date()}",
            "initial_capital": initial_capital,
            "final_capital": round(final_capital, 2),
            "total_return": f"{total_return:.2f}%",
            "benchmark_return": f"{benchmark_return:.2f}%",
            "alpha": f"{total_return - benchmark_return:.2f}%",
            "total_trades": len(trades),
            "rebalance_count": len(trades) // (2 * len(stock_ids)),
            "equity_curve": equity_curve[-30:],  # 最後 30 天
        }

    # ──────────────────────────────────────────────
    #  2. 參數優化
    # ──────────────────────────────────────────────

    def optimize_parameter(
        self,
        stock_id: str,
        strategy_name: str,
        param_name: str,
        param_values: List[Any],
        period: str = "2y",
        initial_capital: float = 1000000,
    ) -> List[Dict]:
        """
        參數優化：測試不同參數值的表現

        Args:
            stock_id: 股票代碼
            strategy_name: 策略名稱
            param_name: 參數名稱
            param_values: 參數值列表
            period: 回測期間
            initial_capital: 初始資金

        Returns:
            各參數的回測結果
        """
        logger.info(f"參數優化: {strategy_name}, {param_name} = {param_values}")

        results = []
        for value in param_values:
            try:
                # 建立帶參數的策略
                strategy = self._create_strategy_with_param(
                    strategy_name, param_name, value
                )

                result = self.run(
                    stock_id=stock_id,
                    strategy=strategy,
                    initial_capital=initial_capital,
                    period=period,
                )

                results.append(
                    {
                        "parameter": param_name,
                        "value": value,
                        "total_return": result.total_return,
                        "max_drawdown": result.max_drawdown,
                        "win_rate": result.win_rate,
                        "sharpe_ratio": result.sharpe_ratio,
                        "total_trades": result.total_trades,
                    }
                )
            except Exception as e:
                results.append(
                    {"parameter": param_name, "value": value, "error": str(e)}
                )

        # 按報酬率排序
        results.sort(key=lambda x: x.get("total_return", 0), reverse=True)
        return results

    def _create_strategy_with_param(
        self, strategy_name: str, param_name: str, value: Any
    ) -> Callable:
        """建立帶參數的策略函數"""

        if strategy_name == "rsi_oversold" and param_name == "rsi_buy_threshold":

            def strategy(df):
                rsi = df["rsi"].iloc[-1]
                if rsi < value:
                    return "buy"
                elif rsi > 70:
                    return "sell"
                return "hold"

            strategy.__name__ = f"rsi_buy_{value}"
            return strategy

        elif strategy_name == "rsi_oversold" and param_name == "rsi_sell_threshold":

            def strategy(df):
                rsi = df["rsi"].iloc[-1]
                if rsi < 30:
                    return "buy"
                elif rsi > value:
                    return "sell"
                return "hold"

            strategy.__name__ = f"rsi_sell_{value}"
            return strategy

        elif strategy_name == "ma_crossover" and param_name == "fast_period":

            def strategy(df):
                if len(df) < 2:
                    return "hold"
                fast_ma = df["close"].rolling(value).mean()
                slow_ma = df["ma20"]
                if (
                    fast_ma.iloc[-1] > slow_ma.iloc[-1]
                    and fast_ma.iloc[-2] <= slow_ma.iloc[-2]
                ):
                    return "buy"
                elif (
                    fast_ma.iloc[-1] < slow_ma.iloc[-1]
                    and fast_ma.iloc[-2] >= slow_ma.iloc[-2]
                ):
                    return "sell"
                return "hold"

            strategy.__name__ = f"ma_cross_{value}_20"
            return strategy

        elif strategy_name == "bollinger_bounce" and param_name == "bb_std":

            def strategy(df):
                close = df["close"].iloc[-1]
                middle = df["bb_middle"].iloc[-1]
                std = df["close"].rolling(20).std().iloc[-1]
                upper = middle + value * std
                lower = middle - value * std
                if close <= lower:
                    return "buy"
                elif close >= upper:
                    return "sell"
                return "hold"

            strategy.__name__ = f"bb_{value}std"
            return strategy

        else:
            raise ValueError(f"未知的策略/參數組合: {strategy_name}/{param_name}")

    # ──────────────────────────────────────────────
    #  3. 停損停利策略
    # ──────────────────────────────────────────────

    def run_with_stop_loss(
        self,
        stock_id: str,
        strategy: Callable,
        stop_loss_pct: float = -5.0,
        take_profit_pct: float = 15.0,
        trailing_stop: bool = False,
        period: str = "2y",
        initial_capital: float = 1000000,
    ) -> BacktestResult:
        """
        帶停損停利的回測

        Args:
            stock_id: 股票代碼
            strategy: 原始策略
            stop_loss_pct: 停損百分比 (負數，如 -5 表示跌 5% 停損)
            take_profit_pct: 停利百分比 (正數，如 15 表示漲 15% 停利)
            trailing_stop: 是否使用移動停損
            period: 回測期間
            initial_capital: 初始資金

        Returns:
            BacktestResult
        """
        import yfinance as yf

        logger.info(
            f"停損停利回測: stop_loss={stop_loss_pct}%, take_profit={take_profit_pct}%"
        )

        # 取得歷史資料
        ticker = yf.Ticker(stock_id)
        df = ticker.history(period=period)

        if df.empty:
            raise ValueError(f"無法取得 {stock_id} 的歷史資料")

        df.columns = [c.lower() for c in df.columns]
        df = self._add_indicators(df)

        if len(df) < 60:
            raise ValueError("資料不足")

        # 模擬交易
        capital = initial_capital
        position = 0
        in_position = False
        buy_price = 0
        highest_since_buy = 0  # 買入後的最高價（用於移動停損）
        trades = []
        equity_curve = []

        for i in range(60, len(df)):
            current_row = df.iloc[i]
            current_price = current_row["close"]
            current_date = str(df.index[i].date())
            current_df = df.iloc[: i + 1]

            # 更新最高價
            if in_position:
                highest_since_buy = max(highest_since_buy, current_price)

            # 檢查停損停利
            should_stop = False
            stop_reason = ""

            if in_position:
                profit_pct = (current_price - buy_price) / buy_price * 100

                # 停損檢查
                if profit_pct <= stop_loss_pct:
                    should_stop = True
                    stop_reason = f"停損 ({profit_pct:.1f}%)"

                # 停利檢查
                elif profit_pct >= take_profit_pct:
                    should_stop = True
                    stop_reason = f"停利 ({profit_pct:.1f}%)"

                # 移動停損
                elif trailing_stop:
                    drawdown_from_high = (
                        (current_price - highest_since_buy) / highest_since_buy * 100
                    )
                    if drawdown_from_high <= stop_loss_pct and profit_pct > 0:
                        should_stop = True
                        stop_reason = f"移動停損 (從高點跌 {drawdown_from_high:.1f}%)"

            # 執行交易
            if should_stop and in_position:
                # 停損/停利賣出
                revenue = position * current_price
                commission = revenue * self.commission_rate
                tax = revenue * self.tax_rate
                net_revenue = revenue - commission - tax
                capital += net_revenue

                trades.append(
                    Trade(
                        date=current_date,
                        action="sell",
                        price=current_price,
                        shares=position,
                        value=revenue,
                        commission=commission + tax,
                        reason=stop_reason,
                    )
                )

                position = 0
                in_position = False
                buy_price = 0
                highest_since_buy = 0

            else:
                # 正常策略信號
                signal = strategy(current_df)

                if signal == "buy" and not in_position:
                    max_shares = int(
                        capital / (current_price * (1 + self.commission_rate))
                    )
                    if max_shares > 0:
                        shares = max_shares
                        cost = shares * current_price
                        commission = cost * self.commission_rate
                        if cost + commission <= capital:
                            capital -= cost + commission
                            position = shares
                            buy_price = current_price
                            in_position = True
                            highest_since_buy = current_price

                            trades.append(
                                Trade(
                                    date=current_date,
                                    action="buy",
                                    price=current_price,
                                    shares=shares,
                                    value=cost,
                                    commission=commission,
                                    reason=signal,
                                )
                            )

                elif signal == "sell" and in_position:
                    revenue = position * current_price
                    commission = revenue * self.commission_rate
                    tax = revenue * self.tax_rate
                    net_revenue = revenue - commission - tax
                    capital += net_revenue

                    trades.append(
                        Trade(
                            date=current_date,
                            action="sell",
                            price=current_price,
                            shares=position,
                            value=revenue,
                            commission=commission + tax,
                            reason=f"策略賣出 (獲利={(current_price-buy_price)/buy_price*100:.1f}%)",
                        )
                    )

                    position = 0
                    in_position = False
                    buy_price = 0
                    highest_since_buy = 0

            # 記錄資產
            total_equity = capital + (position * current_price)
            equity_curve.append({"date": current_date, "equity": total_equity})

        # 計算績效
        equity_series = pd.Series(
            [e["equity"] for e in equity_curve], index=[e["date"] for e in equity_curve]
        )

        final_capital = (
            equity_series.iloc[-1] if not equity_series.empty else initial_capital
        )
        total_return = (final_capital - initial_capital) / initial_capital * 100
        days = len(equity_series)
        annual_return = (
            ((final_capital / initial_capital) ** (252 / days) - 1) * 100
            if days > 0
            else 0
        )

        # 最大回撤
        peak = equity_series.expanding().max()
        drawdown = (equity_series - peak) / peak * 100
        max_drawdown = drawdown.min()

        # 勝率
        winning = sum(1 for t in trades if t.action == "sell" and t.price > buy_price)
        total_sells = sum(1 for t in trades if t.action == "sell")
        win_rate = (winning / total_sells * 100) if total_sells > 0 else 0

        # 基準
        benchmark_return = (df["close"].iloc[-1] / df["close"].iloc[0] - 1) * 100

        return BacktestResult(
            strategy_name=f"{strategy.__name__}_SL{stop_loss_pct}_TP{take_profit_pct}",
            stock_id=stock_id,
            start_date=str(df.index[60].date()),
            end_date=str(df.index[-1].date()),
            initial_capital=initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            annual_return=annual_return,
            max_drawdown=max_drawdown,
            max_drawdown_period="",
            win_rate=win_rate,
            total_trades=len(trades),
            winning_trades=winning,
            losing_trades=total_sells - winning,
            avg_win=0,
            avg_loss=0,
            profit_factor=0,
            sharpe_ratio=0,
            sortino_ratio=0,
            calmar_ratio=0,
            trades=trades,
            equity_curve=equity_series,
            benchmark_return=benchmark_return,
            alpha=total_return - benchmark_return,
        )

    # ──────────────────────────────────────────────
    #  4. 跨市場回測
    # ──────────────────────────────────────────────

    def run_cross_market(
        self,
        stock_ids: List[str],
        strategy: Callable,
        period: str = "2y",
        initial_capital: float = 1000000,
    ) -> List[Dict]:
        """
        跨市場回測：測試策略在不同股票的表現

        Args:
            stock_ids: 股票代碼列表
            strategy: 策略函數
            period: 回測期間
            initial_capital: 初始資金

        Returns:
            各股票的回測結果
        """
        logger.info(f"跨市場回測: {stock_ids}")

        results = []
        for stock_id in stock_ids:
            try:
                result = self.run(
                    stock_id=stock_id,
                    strategy=strategy,
                    initial_capital=initial_capital,
                    period=period,
                )

                results.append(
                    {
                        "stock_id": stock_id,
                        "total_return": result.total_return,
                        "annual_return": result.annual_return,
                        "max_drawdown": result.max_drawdown,
                        "win_rate": result.win_rate,
                        "total_trades": result.total_trades,
                        "sharpe_ratio": result.sharpe_ratio,
                        "benchmark_return": result.benchmark_return,
                        "alpha": result.alpha,
                    }
                )
            except Exception as e:
                results.append({"stock_id": stock_id, "error": str(e)})

        # 按報酬率排序
        results.sort(key=lambda x: x.get("total_return", 0), reverse=True)
        return results


# 全局實例
_advanced_engine = None


def get_advanced_backtest_engine() -> AdvancedBacktestEngine:
    """取得 AdvancedBacktestEngine 單例"""
    global _advanced_engine
    if _advanced_engine is None:
        _advanced_engine = AdvancedBacktestEngine()
    return _advanced_engine
