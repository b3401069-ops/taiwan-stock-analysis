"""
台灣股票分析工具 - 回測系統 (Backtesting)
驗證交易策略的歷史表現
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, date
from dataclasses import dataclass, field
from loguru import logger

from data.data_fetcher import DataFetcher
from data.stock_data import StockData


@dataclass
class Trade:
    """交易記錄"""
    date: str
    action: str          # "buy" or "sell"
    price: float
    shares: int
    value: float
    commission: float
    reason: str = ""


@dataclass
class BacktestResult:
    """回測結果"""
    strategy_name: str
    stock_id: str
    start_date: str
    end_date: str
    initial_capital: float
    final_capital: float
    total_return: float          # 總報酬率 (%)
    annual_return: float         # 年化報酬率 (%)
    max_drawdown: float          # 最大回撤 (%)
    max_drawdown_period: str     # 最大回撤期間
    win_rate: float              # 勝率 (%)
    total_trades: int            # 總交易次數
    winning_trades: int          # 獲利交易次數
    losing_trades: int           # 虧損交易次數
    avg_win: float               # 平均獲利 (%)
    avg_loss: float              # 平均虧損 (%)
    profit_factor: float         # 獲利因子
    sharpe_ratio: float          # 夏普比率
    sortino_ratio: float         # 索提諾比率
    calmar_ratio: float          # 卡瑪比率
    trades: List[Trade]          # 交易記錄
    equity_curve: pd.Series      # 資產曲線
    benchmark_return: float      # 基準報酬率 (買入持有)
    alpha: float                 # 超額報酬

    def to_dict(self) -> Dict:
        """轉換為字典（方便 JSON 序列化）"""
        return {
            "strategy_name": self.strategy_name,
            "stock_id": self.stock_id,
            "period": f"{self.start_date} ~ {self.end_date}",
            "initial_capital": self.initial_capital,
            "final_capital": round(self.final_capital, 2),
            "total_return": f"{self.total_return:.2f}%",
            "annual_return": f"{self.annual_return:.2f}%",
            "max_drawdown": f"{self.max_drawdown:.2f}%",
            "max_drawdown_period": self.max_drawdown_period,
            "win_rate": f"{self.win_rate:.1f}%",
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "avg_win": f"{self.avg_win:.2f}%",
            "avg_loss": f"{self.avg_loss:.2f}%",
            "profit_factor": round(self.profit_factor, 2),
            "sharpe_ratio": round(self.sharpe_ratio, 2),
            "sortino_ratio": round(self.sortino_ratio, 2),
            "calmar_ratio": round(self.calmar_ratio, 2),
            "benchmark_return": f"{self.benchmark_return:.2f}%",
            "alpha": f"{self.alpha:.2f}%",
            "trades": [
                {
                    "date": t.date,
                    "action": t.action,
                    "price": round(t.price, 2),
                    "shares": t.shares,
                    "value": round(t.value, 2),
                    "reason": t.reason
                }
                for t in self.trades[-20:]  # 只返回最後 20 筆
            ]
        }


class BacktestEngine:
    """回測引擎"""

    def __init__(self, commission_rate: float = 0.001425, tax_rate: float = 0.003):
        """
        Args:
            commission_rate: 手續費率 (台灣預設 0.1425%)
            tax_rate: 證交稅 (賣出時 0.3%)
        """
        self.commission_rate = commission_rate
        self.tax_rate = tax_rate
        self.stock_data = StockData()

    def run(
        self,
        stock_id: str,
        strategy: Callable,
        start_date: str = None,
        end_date: str = None,
        initial_capital: float = 1000000,
        period: str = "2y"
    ) -> BacktestResult:
        """
        執行回測

        Args:
            stock_id: 股票代碼
            strategy: 策略函數，接收 DataFrame，返回 "buy"/"sell"/"hold"
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            initial_capital: 初始資金
            period: 資料期間

        Returns:
            BacktestResult
        """
        import yfinance as yf

        logger.info(f"開始回測 {stock_id}...")

        # 取得歷史資料
        ticker = yf.Ticker(stock_id)
        df = ticker.history(period=period)

        if df.empty:
            raise ValueError(f"無法取得 {stock_id} 的歷史資料")

        # 準備資料
        df.columns = [c.lower() for c in df.columns]
        df.index.name = "date"

        # 計算技術指標
        df = self._add_indicators(df)

        # 篩選日期範圍
        if start_date:
            df = df[df.index >= start_date]
        if end_date:
            df = df[df.index <= end_date]

        if len(df) < 20:
            raise ValueError("資料不足，無法回測")

        # 執行策略
        capital = initial_capital
        position = 0           # 持有股數
        shares = 0
        trades = []
        equity_curve = []
        buy_price = 0
        in_position = False

        for i in range(60, len(df)):  # 從第 60 天開始（需要足夠指標計算）
            current_row = df.iloc[i]
            current_price = current_row["close"]
            current_date = str(df.index[i].date())

            # 準備策略輸入（使用完整 DataFrame 到當前點）
            # 策略會用 iloc[-1] 取最新值
            current_df = df.iloc[:i+1]

            # 呼叫策略
            signal = strategy(current_df)

            # 執行交易
            if signal == "buy" and not in_position:
                # 買入：用全部資金（支援零股）
                max_shares = int(capital / (current_price * (1 + self.commission_rate)))
                if max_shares > 0:
                    shares = max_shares
                    cost = shares * current_price
                    commission = cost * self.commission_rate
                    total_cost = cost + commission

                    if total_cost <= capital:
                        capital -= total_cost
                        position = shares
                        buy_price = current_price
                        in_position = True

                        trades.append(Trade(
                            date=current_date,
                            action="buy",
                            price=current_price,
                            shares=shares,
                            value=cost,
                            commission=commission,
                            reason=f"RSI={current_df['rsi'].iloc[-1]:.1f}"
                        ))

            elif signal == "sell" and in_position:
                # 賣出：賣掉全部
                revenue = position * current_price
                commission = revenue * self.commission_rate
                tax = revenue * self.tax_rate
                net_revenue = revenue - commission - tax

                capital += net_revenue

                profit_pct = (current_price - buy_price) / buy_price * 100

                trades.append(Trade(
                    date=current_date,
                    action="sell",
                    price=current_price,
                    shares=position,
                    value=revenue,
                    commission=commission + tax,
                    reason=f"RSI={current_df['rsi'].iloc[-1]:.1f}, 獲利={profit_pct:.1f}%"
                ))

                position = 0
                shares = 0
                buy_price = 0
                in_position = False

            # 記錄資產價值
            total_equity = capital + (position * current_price)
            equity_curve.append({
                "date": current_date,
                "equity": total_equity,
                "capital": capital,
                "position_value": position * current_price
            })

        # 計算績效指標
        equity_series = pd.Series(
            [e["equity"] for e in equity_curve],
            index=[e["date"] for e in equity_curve]
        )

        final_capital = equity_series.iloc[-1] if not equity_series.empty else initial_capital

        # 計算各項指標
        total_return = (final_capital - initial_capital) / initial_capital * 100
        days = len(equity_series)
        annual_return = ((final_capital / initial_capital) ** (252 / days) - 1) * 100 if days > 0 else 0

        # 最大回撤
        peak = equity_series.expanding().max()
        drawdown = (equity_series - peak) / peak * 100
        max_drawdown = drawdown.min()

        # 勝率
        winning_trades = 0
        losing_trades = 0
        total_wins = 0
        total_losses = 0

        for i in range(0, len(trades) - 1, 2):
            if i + 1 < len(trades):
                buy_trade = trades[i]
                sell_trade = trades[i + 1]
                profit = (sell_trade.price - buy_trade.price) / buy_trade.price * 100

                if profit > 0:
                    winning_trades += 1
                    total_wins += profit
                else:
                    losing_trades += 1
                    total_losses += abs(profit)

        total_trade_pairs = winning_trades + losing_trades
        win_rate = (winning_trades / total_trade_pairs * 100) if total_trade_pairs > 0 else 0
        avg_win = (total_wins / winning_trades) if winning_trades > 0 else 0
        avg_loss = (total_losses / losing_trades) if losing_trades > 0 else 0
        profit_factor = (total_wins / total_losses) if total_losses > 0 else float("inf")

        # 夏普比率
        returns = equity_series.pct_change().dropna()
        if len(returns) > 0 and returns.std() > 0:
            sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252)
        else:
            sharpe_ratio = 0

        # 索提諾比率（只考慮下行風險）
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0 and downside_returns.std() > 0:
            sortino_ratio = (returns.mean() / downside_returns.std()) * np.sqrt(252)
        else:
            sortino_ratio = 0

        # 卡瑪比率
        calmar_ratio = (annual_return / abs(max_drawdown)) if max_drawdown != 0 else 0

        # 基準報酬率（買入持有）
        benchmark_return = (df["close"].iloc[-1] / df["close"].iloc[0] - 1) * 100

        # Alpha
        alpha = total_return - benchmark_return

        result = BacktestResult(
            strategy_name=strategy.__name__ if hasattr(strategy, "__name__") else "custom",
            stock_id=stock_id,
            start_date=str(df.index[20].date()),
            end_date=str(df.index[-1].date()),
            initial_capital=initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            annual_return=annual_return,
            max_drawdown=max_drawdown,
            max_drawdown_period="",
            win_rate=win_rate,
            total_trades=len(trades),
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            trades=trades,
            equity_curve=equity_series,
            benchmark_return=benchmark_return,
            alpha=alpha
        )

        logger.info(f"回測完成: 總報酬 {total_return:.2f}%, 最大回撤 {max_drawdown:.2f}%")

        return result

    def _add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """計算技術指標"""
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


# ──────────────────────────────────────────────
#  內建策略
# ──────────────────────────────────────────────

def strategy_rsi_oversold(df: pd.DataFrame) -> str:
    """
    RSI 超賣策略
    - RSI < 30 買入
    - RSI > 70 賣出
    """
    rsi = df["rsi"].iloc[-1]
    if rsi < 30:
        return "buy"
    elif rsi > 70:
        return "sell"
    return "hold"


def strategy_macd_crossover(df: pd.DataFrame) -> str:
    """
    MACD 黃金交叉策略
    - MACD 線上穿訊號線買入
    - MACD 線下穿訊號線賣出
    """
    if len(df) < 2:
        return "hold"

    macd = df["macd"].iloc[-1]
    signal = df["macd_signal"].iloc[-1]
    macd_prev = df["macd"].iloc[-2]
    signal_prev = df["macd_signal"].iloc[-2]

    # 黃金交叉
    if macd > signal and macd_prev <= signal_prev:
        return "buy"
    # 死亡交叉
    elif macd < signal and macd_prev >= signal_prev:
        return "sell"

    return "hold"


def strategy_ma_crossover(df: pd.DataFrame) -> str:
    """
    均線交叉策略
    - 5日均線上穿20日均線買入
    - 5日均線下穿20日均線賣出
    """
    if len(df) < 2:
        return "hold"

    ma5 = df["ma5"].iloc[-1]
    ma20 = df["ma20"].iloc[-1]
    ma5_prev = df["ma5"].iloc[-2]
    ma20_prev = df["ma20"].iloc[-2]

    # 黃金交叉
    if ma5 > ma20 and ma5_prev <= ma20_prev:
        return "buy"
    # 死亡交叉
    elif ma5 < ma20 and ma5_prev >= ma20_prev:
        return "sell"

    return "hold"


def strategy_bollinger_bounce(df: pd.DataFrame) -> str:
    """
    布林通道反彈策略
    - 價格觸及下軌買入
    - 價格觸及上軌賣出
    """
    close = df["close"].iloc[-1]
    upper = df["bb_upper"].iloc[-1]
    lower = df["bb_lower"].iloc[-1]

    if close <= lower:
        return "buy"
    elif close >= upper:
        return "sell"

    return "hold"


def strategy_combined(df: pd.DataFrame) -> str:
    """
    綜合策略（多指標確認）
    - RSI 超賣 + MACD 黃金交叉 → 買入
    - RSI 超買 + MACD 死亡交叉 → 賣出
    """
    rsi = df["rsi"].iloc[-1]

    if len(df) < 2:
        return "hold"

    macd = df["macd"].iloc[-1]
    signal = df["macd_signal"].iloc[-1]
    macd_prev = df["macd"].iloc[-2]
    signal_prev = df["macd_signal"].iloc[-2]

    # 買入條件：RSI 超賣 + MACD 黃金交叉
    if rsi < 35 and macd > signal and macd_prev <= signal_prev:
        return "buy"

    # 賣出條件：RSI 超買 + MACD 死亡交叉
    if rsi > 65 and macd < signal and macd_prev >= signal_prev:
        return "sell"

    return "hold"


# 全局實例
_backtest_engine = None


def get_backtest_engine() -> BacktestEngine:
    """取得 BacktestEngine 單例"""
    global _backtest_engine
    if _backtest_engine is None:
        _backtest_engine = BacktestEngine()
    return _backtest_engine


# 策略字典
STRATEGIES = {
    "rsi_oversold": strategy_rsi_oversold,
    "macd_crossover": strategy_macd_crossover,
    "ma_crossover": strategy_ma_crossover,
    "bollinger_bounce": strategy_bollinger_bounce,
    "combined": strategy_combined
}
