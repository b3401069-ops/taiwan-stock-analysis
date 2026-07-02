"""
台灣股票分析工具 - 工具函數
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from loguru import logger
import json
import re

# 允許的股票代碼字元：英數、點、減號，長度 1~15。
# 涵蓋台股（2330.TW / 6488.TWO）與國際代碼（AAPL、BRK-B 等），
# 同時擋掉路徑穿越、過長字串與其他異常/惡意輸入。
_STOCK_ID_PATTERN = re.compile(r"^[A-Za-z0-9.\-]{1,15}$")


def format_currency(amount: float, currency: str = "TWD") -> str:
    """格式化貨幣金額"""
    try:
        if currency == "TWD":
            return f"NT${amount:,.2f}"
        elif currency == "USD":
            return f"${amount:,.2f}"
        elif currency == "JPY":
            return f"¥{amount:,.0f}"
        elif currency == "KRW":
            return f"₩{amount:,.0f}"
        else:
            return f"{amount:,.2f} {currency}"
    except Exception as e:
        logger.error(f"格式化貨幣失敗: {e}")
        return str(amount)


def format_percentage(value: float, decimals: int = 2) -> str:
    """格式化百分比"""
    try:
        return f"{value:.{decimals}f}%"
    except Exception as e:
        logger.error(f"格式化百分比失敗: {e}")
        return str(value)


def format_number(value: float, decimals: int = 2) -> str:
    """格式化數字"""
    try:
        if abs(value) >= 1e9:
            return f"{value/1e9:.{decimals}f}B"
        elif abs(value) >= 1e6:
            return f"{value/1e6:.{decimals}f}M"
        elif abs(value) >= 1e3:
            return f"{value/1e3:.{decimals}f}K"
        else:
            return f"{value:.{decimals}f}"
    except Exception as e:
        logger.error(f"格式化數字失敗: {e}")
        return str(value)


def calculate_returns(prices: List[float]) -> List[float]:
    """計算收益率"""
    try:
        returns = []
        for i in range(1, len(prices)):
            if prices[i-1] != 0:
                returns.append((prices[i] - prices[i-1]) / prices[i-1])
            else:
                returns.append(0)
        return returns
    except Exception as e:
        logger.error(f"計算收益率失敗: {e}")
        return []


def calculate_volatility(returns: List[float], window: int = 20) -> float:
    """計算波動率"""
    try:
        if len(returns) < window:
            return 0
        
        # 計算滾動標準差
        volatility = pd.Series(returns).rolling(window=window).std().iloc[-1]
        
        # 年化波動率
        annualized_volatility = volatility * np.sqrt(252)
        
        return float(annualized_volatility)
    except Exception as e:
        logger.error(f"計算波動率失敗: {e}")
        return 0


def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.02) -> float:
    """計算夏普比率"""
    try:
        if not returns:
            return 0
        
        # 計算平均收益率
        mean_return = np.mean(returns) * 252  # 年化
        
        # 計算標準差
        std_return = np.std(returns) * np.sqrt(252)  # 年化
        
        # 計算夏普比率
        if std_return == 0:
            return 0
        
        sharpe_ratio = (mean_return - risk_free_rate) / std_return
        
        return float(sharpe_ratio)
    except Exception as e:
        logger.error(f"計算夏普比率失敗: {e}")
        return 0


def calculate_max_drawdown(prices: List[float]) -> Dict:
    """計算最大回撤"""
    try:
        if not prices:
            return {"max_drawdown": 0, "peak_index": 0, "trough_index": 0}
        
        # 計算累積最高點
        peak = prices[0]
        peak_index = 0
        max_drawdown = 0
        max_drawdown_peak_index = 0
        max_drawdown_trough_index = 0
        
        for i in range(1, len(prices)):
            if prices[i] > peak:
                peak = prices[i]
                peak_index = i
            
            drawdown = (peak - prices[i]) / peak
            
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                max_drawdown_peak_index = peak_index
                max_drawdown_trough_index = i
        
        return {
            "max_drawdown": float(max_drawdown),
            "peak_index": max_drawdown_peak_index,
            "trough_index": max_drawdown_trough_index
        }
    except Exception as e:
        logger.error(f"計算最大回撤失敗: {e}")
        return {"max_drawdown": 0, "peak_index": 0, "trough_index": 0}


def validate_stock_id(stock_id: str) -> bool:
    """驗證股票代碼格式（防止異常/惡意輸入，作為外部呼叫前的第一道防線）。"""
    try:
        if not stock_id or not isinstance(stock_id, str):
            return False
        return bool(_STOCK_ID_PATTERN.match(stock_id))
    except Exception as e:
        logger.error(f"驗證股票代碼失敗: {e}")
        return False


def parse_stock_info(stock_id: str) -> Dict:
    """解析股票代碼資訊"""
    try:
        if stock_id.endswith(".TW"):
            return {
                "code": stock_id.split(".")[0],
                "market": "TWSE",
                "country": "Taiwan",
                "currency": "TWD"
            }
        elif stock_id.endswith(".TWO"):
            return {
                "code": stock_id.split(".")[0],
                "market": "OTC",
                "country": "Taiwan",
                "currency": "TWD"
            }
        else:
            return {
                "code": stock_id,
                "market": "Unknown",
                "country": "Unknown",
                "currency": "Unknown"
            }
    except Exception as e:
        logger.error(f"解析股票代碼失敗: {e}")
        return {}


def safe_division(numerator: float, denominator: float, default: float = 0.0) -> float:
    """安全除法"""
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except Exception as e:
        logger.error(f"安全除法失敗: {e}")
        return default


def moving_average(data: List[float], window: int) -> List[float]:
    """計算移動平均線"""
    try:
        if len(data) < window:
            return []
        
        ma = []
        for i in range(window - 1, len(data)):
            avg = sum(data[i - window + 1:i + 1]) / window
            ma.append(avg)
        
        return ma
    except Exception as e:
        logger.error(f"計算移動平均線失敗: {e}")
        return []


def exponential_moving_average(data: List[float], span: int) -> List[float]:
    """計算指數移動平均線"""
    try:
        if not data:
            return []
        
        ema = [data[0]]
        multiplier = 2 / (span + 1)
        
        for i in range(1, len(data)):
            value = (data[i] - ema[-1]) * multiplier + ema[-1]
            ema.append(value)
        
        return ema
    except Exception as e:
        logger.error(f"計算指數移動平均線失敗: {e}")
        return []


def calculate_rsi(prices: List[float], period: int = 14) -> List[float]:
    """計算RSI指標"""
    try:
        if len(prices) < period + 1:
            return []
        
        # 計算價格變化
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        # 分離上漲和下跌
        gains = [max(0, delta) for delta in deltas]
        losses = [max(0, -delta) for delta in deltas]
        
        # 計算平均漲幅和跌幅
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        rsi_values = []
        
        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            rsi_values.append(rsi)
        
        return rsi_values
    except Exception as e:
        logger.error(f"計算RSI失敗: {e}")
        return []


def generate_mock_data(days: int = 30, base_price: float = 100.0, volatility: float = 0.02) -> Dict:
    """生成模擬數據"""
    try:
        dates = [datetime.now() - timedelta(days=days-i) for i in range(days)]
        prices = [base_price]
        
        for i in range(1, days):
            change = np.random.normal(0, volatility)
            new_price = prices[-1] * (1 + change)
            prices.append(new_price)
        
        volumes = [np.random.randint(1000000, 10000000) for _ in range(days)]
        
        return {
            "dates": [date.strftime("%Y-%m-%d") for date in dates],
            "prices": prices,
            "volumes": volumes,
            "high": [price * 1.02 for price in prices],
            "low": [price * 0.98 for price in prices],
            "open": [price * (1 + np.random.normal(0, 0.01)) for price in prices]
        }
    except Exception as e:
        logger.error(f"生成模擬數據失敗: {e}")
        return {}


def save_to_json(data: Any, filepath: str) -> bool:
    """儲存資料到JSON檔案"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"儲存JSON失敗: {e}")
        return False


def load_from_json(filepath: str) -> Any:
    """從JSON檔案載入資料"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"載入JSON失敗: {e}")
        return None


def timestamp_to_date(timestamp: float) -> str:
    """時間戳轉換為日期字串"""
    try:
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        logger.error(f"時間戳轉換失敗: {e}")
        return str(timestamp)


def date_to_timestamp(date_str: str) -> float:
    """日期字串轉換為時間戳"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").timestamp()
    except Exception as e:
        logger.error(f"日期字串轉換失敗: {e}")
        return 0