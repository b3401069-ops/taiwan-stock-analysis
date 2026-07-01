"""
台灣股票分析工具 - 虛擬倉位系統
讓 AI 建議投資標的，建立虛擬倉位，進行投資回顧
"""
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from loguru import logger
from dataclasses import dataclass, asdict
import yfinance as yf


@dataclass
class Position:
    """持倉記錄"""
    stock_id: str
    stock_name: str
    entry_date: str
    entry_price: float
    shares: int
    entry_reason: str  # 進場原因
    ai_confidence: int  # AI 信心水平
    target_price: float  # 目標價
    stop_loss: float  # 停損價
    strategy: str  # 使用的策略


@dataclass
class TradeRecord:
    """交易記錄"""
    trade_id: str
    stock_id: str
    stock_name: str
    trade_type: str  # buy/sell
    date: str
    price: float
    shares: int
    amount: float
    reason: str
    profit_loss: Optional[float] = None
    profit_loss_pct: Optional[float] = None


@dataclass
class PortfolioSnapshot:
    """倉位快照"""
    date: str
    total_value: float
    total_cost: float
    total_profit_loss: float
    total_return_pct: float
    positions: List[Dict]
    cash: float


class VirtualPortfolio:
    """虛擬倉位管理系統"""

    def __init__(self, initial_capital: float = 1000000):
        """
        初始化虛擬倉位
        
        Args:
            initial_capital: 初始資金（預設 100 萬）
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[TradeRecord] = []
        self.snapshots: List[PortfolioSnapshot] = []
        self.created_at = datetime.now().isoformat()
        
        # 載入已存在的倉位（如果有）
        self._load_portfolio()

    def _load_portfolio(self):
        """載入倉位資料"""
        try:
            import os
            portfolio_file = "data/portfolio.json"
            if os.path.exists(portfolio_file):
                with open(portfolio_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.cash = data.get("cash", self.initial_capital)
                    self.positions = {
                        k: Position(**v) for k, v in data.get("positions", {}).items()
                    }
                    self.trade_history = [
                        TradeRecord(**t) for t in data.get("trade_history", [])
                    ]
                    logger.info(f"載入倉位: {len(self.positions)} 檔股票, 現金: {self.cash:,.0f}")
        except Exception as e:
            logger.warning(f"載入倉位失敗: {e}")

    def _save_portfolio(self):
        """儲存倉位資料"""
        try:
            import os
            os.makedirs("data", exist_ok=True)
            
            data = {
                "cash": self.cash,
                "positions": {k: asdict(v) for k, v in self.positions.items()},
                "trade_history": [asdict(t) for t in self.trade_history],
                "updated_at": datetime.now().isoformat()
            }
            
            with open("data/portfolio.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"儲存倉位失敗: {e}")

    def add_position(self, stock_id: str, stock_name: str, shares: int,
                     entry_price: float, entry_reason: str, ai_confidence: int,
                     target_price: float, stop_loss: float, strategy: str = "ai_suggestion") -> Dict:
        """
        新增持倉
        
        Args:
            stock_id: 股票代碼
            stock_name: 股票名稱
            shares: 股數
            entry_price: 進場價格
            entry_reason: 進場原因
            ai_confidence: AI 信心水平 (0-100)
            target_price: 目標價
            stop_loss: 停損價
            strategy: 使用的策略
            
        Returns:
            交易結果
        """
        try:
            # 計算總成本
            total_cost = entry_price * shares
            
            # 檢查資金是否足夠
            if total_cost > self.cash:
                return {
                    "success": False,
                    "error": f"資金不足。需要 {total_cost:,.0f}，目前現金 {self.cash:,.0f}"
                }
            
            # 建立持倉記錄
            position = Position(
                stock_id=stock_id,
                stock_name=stock_name,
                entry_date=datetime.now().strftime("%Y-%m-%d"),
                entry_price=entry_price,
                shares=shares,
                entry_reason=entry_reason,
                ai_confidence=ai_confidence,
                target_price=target_price,
                stop_loss=stop_loss,
                strategy=strategy
            )
            
            # 更新持倉
            if stock_id in self.positions:
                # 加碼：計算平均成本
                existing = self.positions[stock_id]
                total_shares = existing.shares + shares
                avg_price = (existing.entry_price * existing.shares + entry_price * shares) / total_shares
                
                position.shares = total_shares
                position.entry_price = avg_price
                position.entry_reason = f"{existing.entry_reason}; {entry_reason}"
            
            self.positions[stock_id] = position
            
            # 扣除現金
            self.cash -= total_cost
            
            # 記錄交易
            trade = TradeRecord(
                trade_id=f"T{len(self.trade_history)+1:04d}",
                stock_id=stock_id,
                stock_name=stock_name,
                trade_type="buy",
                date=datetime.now().strftime("%Y-%m-%d %H:%M"),
                price=entry_price,
                shares=shares,
                amount=total_cost,
                reason=entry_reason
            )
            self.trade_history.append(trade)
            
            # 儲存
            self._save_portfolio()
            
            logger.info(f"買入 {stock_name} ({stock_id}): {shares} 股 @ {entry_price}")
            
            return {
                "success": True,
                "message": f"成功買入 {stock_name} ({stock_id})",
                "data": {
                    "stock_id": stock_id,
                    "shares": shares,
                    "entry_price": entry_price,
                    "total_cost": total_cost,
                    "remaining_cash": self.cash,
                    "target_price": target_price,
                    "stop_loss": stop_loss
                }
            }
            
        except Exception as e:
            logger.error(f"新增持倉失敗: {e}")
            return {"success": False, "error": str(e)}

    def sell_position(self, stock_id: str, shares: int, sell_price: float,
                      reason: str = "手動賣出") -> Dict:
        """
        賣出持倉
        
        Args:
            stock_id: 股票代碼
            shares: 賣出股數
            sell_price: 賣出價格
            reason: 賣出原因
            
        Returns:
            交易結果
        """
        try:
            if stock_id not in self.positions:
                return {"success": False, "error": f"沒有持有 {stock_id}"}
            
            position = self.positions[stock_id]
            
            if shares > position.shares:
                return {"success": False, "error": f"持股不足。持有 {position.shares}，欲賣 {shares}"}
            
            # 計算損益
            entry_cost = position.entry_price * shares
            sell_amount = sell_price * shares
            profit_loss = sell_amount - entry_cost
            profit_loss_pct = (profit_loss / entry_cost) * 100
            
            # 更新持倉
            if shares == position.shares:
                # 全部賣出
                del self.positions[stock_id]
            else:
                # 部分賣出
                position.shares -= shares
            
            # 增加現金
            self.cash += sell_amount
            
            # 記錄交易
            trade = TradeRecord(
                trade_id=f"T{len(self.trade_history)+1:04d}",
                stock_id=stock_id,
                stock_name=position.stock_name,
                trade_type="sell",
                date=datetime.now().strftime("%Y-%m-%d %H:%M"),
                price=sell_price,
                shares=shares,
                amount=sell_amount,
                reason=reason,
                profit_loss=profit_loss,
                profit_loss_pct=profit_loss_pct
            )
            self.trade_history.append(trade)
            
            # 儲存
            self._save_portfolio()
            
            logger.info(f"賣出 {position.stock_name} ({stock_id}): {shares} 股 @ {sell_price}, 損益: {profit_loss:+,.0f}")
            
            return {
                "success": True,
                "message": f"成功賣出 {position.stock_name} ({stock_id})",
                "data": {
                    "stock_id": stock_id,
                    "shares": shares,
                    "sell_price": sell_price,
                    "sell_amount": sell_amount,
                    "profit_loss": profit_loss,
                    "profit_loss_pct": profit_loss_pct,
                    "remaining_cash": self.cash
                }
            }
            
        except Exception as e:
            logger.error(f"賣出持倉失敗: {e}")
            return {"success": False, "error": str(e)}

    def get_portfolio_summary(self) -> Dict:
        """取得倉位摘要"""
        try:
            # 取得即時價格
            total_value = self.cash
            positions_summary = []
            
            for stock_id, position in self.positions.items():
                try:
                    ticker = yf.Ticker(stock_id)
                    current_price = ticker.info.get("currentPrice", position.entry_price)
                except:
                    current_price = position.entry_price
                
                # 計算損益
                current_value = current_price * position.shares
                entry_cost = position.entry_price * position.shares
                profit_loss = current_value - entry_cost
                profit_loss_pct = (profit_loss / entry_cost) * 100 if entry_cost > 0 else 0
                
                total_value += current_value
                
                positions_summary.append({
                    "stock_id": stock_id,
                    "stock_name": position.stock_name,
                    "shares": position.shares,
                    "entry_price": position.entry_price,
                    "current_price": current_price,
                    "entry_date": position.entry_date,
                    "entry_reason": position.entry_reason,
                    "ai_confidence": position.ai_confidence,
                    "target_price": position.target_price,
                    "stop_loss": position.stop_loss,
                    "current_value": current_value,
                    "profit_loss": profit_loss,
                    "profit_loss_pct": profit_loss_pct,
                    "status": self._get_position_status(current_price, position)
                })
            
            # 計算總損益
            total_cost = sum(p.entry_price * p.shares for p in self.positions.values())
            total_profit_loss = total_value - self.initial_capital
            total_return_pct = (total_profit_loss / self.initial_capital) * 100
            
            # 排序：按損益排序
            positions_summary.sort(key=lambda x: x["profit_loss_pct"], reverse=True)
            
            return {
                "success": True,
                "data": {
                    "summary": {
                        "initial_capital": self.initial_capital,
                        "current_cash": self.cash,
                        "total_value": total_value,
                        "total_profit_loss": total_profit_loss,
                        "total_return_pct": total_return_pct,
                        "positions_count": len(self.positions),
                        "created_at": self.created_at
                    },
                    "positions": positions_summary,
                    "statistics": self._calculate_statistics()
                }
            }
            
        except Exception as e:
            logger.error(f"取得倉位摘要失敗: {e}")
            return {"success": False, "error": str(e)}

    def _get_position_status(self, current_price: float, position: Position) -> str:
        """取得持倉狀態"""
        if current_price >= position.target_price:
            return "達到目標"
        elif current_price <= position.stop_loss:
            return "觸及停損"
        elif current_price > position.entry_price:
            return "獲利中"
        else:
            return "虧損中"

    def _calculate_statistics(self) -> Dict:
        """計算交易統計"""
        if not self.trade_history:
            return {}
        
        sell_trades = [t for t in self.trade_history if t.trade_type == "sell"]
        
        if not sell_trades:
            return {
                "total_trades": len(self.trade_history),
                "win_rate": 0,
                "avg_profit": 0,
                "max_profit": 0,
                "max_loss": 0
            }
        
        profits = [t.profit_loss for t in sell_trades if t.profit_loss and t.profit_loss > 0]
        losses = [t.profit_loss for t in sell_trades if t.profit_loss and t.profit_loss < 0]
        
        win_rate = len(profits) / len(sell_trades) * 100 if sell_trades else 0
        
        return {
            "total_trades": len(self.trade_history),
            "sell_trades": len(sell_trades),
            "win_rate": win_rate,
            "total_profit": sum(profits),
            "total_loss": sum(losses),
            "net_profit": sum(t.profit_loss for t in sell_trades if t.profit_loss),
            "avg_profit": np.mean(profits) if profits else 0,
            "avg_loss": np.mean(losses) if losses else 0,
            "max_profit": max(profits) if profits else 0,
            "max_loss": min(losses) if losses else 0
        }

    def get_trade_history(self, limit: int = 50) -> Dict:
        """取得交易歷史"""
        trades = self.trade_history[-limit:]
        trades.reverse()  # 最新在前
        
        return {
            "success": True,
            "data": {
                "total_trades": len(self.trade_history),
                "trades": [asdict(t) for t in trades]
            }
        }

    def check_stop_loss_and_target(self) -> List[Dict]:
        """檢查停損和目標價"""
        alerts = []
        
        for stock_id, position in self.positions.items():
            try:
                ticker = yf.Ticker(stock_id)
                current_price = ticker.info.get("currentPrice", 0)
                
                if current_price <= position.stop_loss:
                    alerts.append({
                        "type": "stop_loss",
                        "stock_id": stock_id,
                        "stock_name": position.stock_name,
                        "current_price": current_price,
                        "stop_loss": position.stop_loss,
                        "message": f"⚠️ {position.stock_name} ({stock_id}) 觸及停損！目前 {current_price}，停損 {position.stop_loss}"
                    })
                
                elif current_price >= position.target_price:
                    alerts.append({
                        "type": "target_reached",
                        "stock_id": stock_id,
                        "stock_name": position.stock_name,
                        "current_price": current_price,
                        "target_price": position.target_price,
                        "message": f"🎯 {position.stock_name} ({stock_id}) 達到目標價！目前 {current_price}，目標 {position.target_price}"
                    })
                    
            except Exception as e:
                logger.warning(f"檢查 {stock_id} 失敗: {e}")
        
        return alerts

    def generate_investment_review(self) -> Dict:
        """生成投資回顧報告"""
        try:
            summary = self.get_portfolio_summary()
            
            if not summary.get("success"):
                return summary
            
            data = summary["data"]
            stats = data["statistics"]
            
            # 計算勝率
            win_rate = stats.get("win_rate", 0)
            
            # 找出最佳和最差持倉
            positions = data["positions"]
            best_position = max(positions, key=lambda x: x["profit_loss_pct"]) if positions else None
            worst_position = min(positions, key=lambda x: x["profit_loss_pct"]) if positions else None
            
            # 生成報告
            report = f"""📊 **虛擬倉位投資回顧報告**

**報告日期：** {datetime.now().strftime("%Y-%m-%d %H:%M")}

---

**💰 資金概況**
• 初始資金：{self.initial_capital:,.0f} 元
• 目前總值：{data['summary']['total_value']:,.0f} 元
• 總損益：{data['summary']['total_profit_loss']:+,.0f} 元 ({data['summary']['total_return_pct']:+.2f}%)
• 持倉數量：{data['summary']['positions_count']} 檔

---

**📈 交易統計**
• 總交易次數：{stats.get('total_trades', 0)}
• 勝率：{win_rate:.1f}%
• 總獲利：{stats.get('total_profit', 0):+,.0f} 元
• 總虧損：{stats.get('total_loss', 0):+,.0f} 元
• 平均獲利：{stats.get('avg_profit', 0):+,.0f} 元
• 平均虧損：{stats.get('avg_loss', 0):+,.0f} 元

---

**🏆 持倉表現**
"""
            
            for pos in positions:
                emoji = "🟢" if pos["profit_loss_pct"] >= 0 else "🔴"
                status = pos["status"]
                report += f"""
• {emoji} **{pos['stock_name']}** ({pos['stock_id']})
  - 進場價：{pos['entry_price']:.1f} → 目前：{pos['current_price']:.1f}
  - 損益：{pos['profit_loss']:+,.0f} 元 ({pos['profit_loss_pct']:+.2f}%)
  - 狀態：{status}
  - 進場原因：{pos['entry_reason'][:50]}...
"""
            
            if best_position:
                report += f"""
---

**🌟 最佳持倉**
• {best_position['stock_name']} ({best_position['stock_id']})
• 報酬率：{best_position['profit_loss_pct']:+.2f}%
"""
            
            if worst_position and worst_position["profit_loss_pct"] < 0:
                report += f"""
**⚠️ 最差持倉**
• {worst_position['stock_name']} ({worst_position['stock_id']})
• 報酬率：{worst_position['profit_loss_pct']:+.2f}%
"""
            
            report += """
---

**💡 投資建議**
"""
            
            if win_rate >= 60:
                report += "• 勝率超過 60%，表現優秀！\n"
            elif win_rate >= 40:
                report += "• 勝率中等，可考慮優化進場時機\n"
            else:
                report += "• 勝率偏低，建議檢討投資策略\n"
            
            if data['summary']['total_return_pct'] > 0:
                report += "• 整體獲利，繼續保持！\n"
            else:
                report += "• 目前虧損，建議檢討停損機制\n"
            
            return {
                "success": True,
                "data": {
                    "report": report,
                    "summary": data["summary"],
                    "statistics": stats,
                    "positions": positions
                }
            }
            
        except Exception as e:
            logger.error(f"生成投資回顧失敗: {e}")
            return {"success": False, "error": str(e)}

    def reset_portfolio(self) -> Dict:
        """重置倉位"""
        try:
            self.cash = self.initial_capital
            self.positions = {}
            self.trade_history = []
            self._save_portfolio()
            
            return {
                "success": True,
                "message": f"倉位已重置，初始資金 {self.initial_capital:,.0f} 元"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# 全局實例
_portfolio = None


def get_virtual_portfolio(initial_capital: float = 1000000) -> VirtualPortfolio:
    """取得 VirtualPortfolio 單例"""
    global _portfolio
    if _portfolio is None:
        _portfolio = VirtualPortfolio(initial_capital)
    return _portfolio
