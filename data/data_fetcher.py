"""
台灣股票分析工具 - 資料取得模組
整合 Yahoo Finance + TWSE 官方 API + 資料庫快取
"""
import yfinance as yf
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from loguru import logger
import asyncio
import aiohttp
from config.config import get_settings


class DataFetcher:
    """資料取得類（整合 Yahoo Finance + TWSE + 資料庫）"""

    def __init__(self):
        self.settings = get_settings()
        self.cache = {}
        self.cache_ttl = self.settings.CACHE_TTL
        self._twse = None
        self._db = None

    @property
    def twse(self):
        """懶載入 TWSE Fetcher"""
        if self._twse is None:
            from data.twse_fetcher import get_twse_fetcher
            self._twse = get_twse_fetcher()
        return self._twse

    @property
    def db(self):
        """懶載入 DB Manager"""
        if self._db is None:
            from models.db_manager import get_db_manager
            self._db = get_db_manager()
        return self._db

    def _is_taiwan_stock(self, stock_id: str) -> bool:
        """判斷是否為台灣股票"""
        return stock_id.endswith(".TW") or stock_id.endswith(".TWO")
    
    async def get_stock_price(self, stock_id: str, period: str = "1y") -> Dict:
        """
        獲取股票價格歷史
        優先順序: 資料庫快取 → TWSE 官方 → Yahoo Finance
        """
        try:
            # 1. 先查資料庫快取
            try:
                days_map = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730, "5y": 1825}
                days = days_map.get(period, 365)
                start = date.today() - timedelta(days=days)
                db_df = self.db.get_price_df(stock_id, start_date=start)
                if not db_df.empty and len(db_df) > 20:
                    logger.info(f"從資料庫取得 {stock_id} {len(db_df)} 筆價格資料")
                    price_data = {
                        "stock_id": stock_id,
                        "period": period,
                        "data": [],
                        "summary": {
                            "start_date": str(db_df.index[0]),
                            "end_date": str(db_df.index[-1]),
                            "data_points": len(db_df),
                            "latest_price": float(db_df['close'].iloc[-1]),
                            "highest_price": float(db_df['high'].max()),
                            "lowest_price": float(db_df['low'].min()),
                            "average_price": float(db_df['close'].mean()),
                            "source": "database"
                        }
                    }
                    for dt, row in db_df.iterrows():
                        price_data["data"].append({
                            "date": str(dt),
                            "open": float(row['open']),
                            "high": float(row['high']),
                            "low": float(row['low']),
                            "close": float(row['close']),
                            "volume": int(row.get('volume', 0))
                        })
                    return price_data
            except Exception as e:
                logger.debug(f"資料庫查詢失敗: {e}")

            # 2. 嘗試 TWSE 官方資料（僅限台灣股票）
            if self._is_taiwan_stock(stock_id):
                try:
                    clean_id = stock_id.replace(".TW", "").replace(".TWO", "")
                    months = {"1mo": 1, "3mo": 3, "6mo": 6, "1y": 12, "2y": 24, "5y": 60}
                    n_months = months.get(period, 12)
                    twse_df = self.twse.get_stock_history(clean_id, n_months)
                    if not twse_df.empty:
                        logger.info(f"從 TWSE 取得 {stock_id} {len(twse_df)} 筆價格資料")
                        # 同步寫入資料庫
                        try:
                            self.db.upsert_stock(stock_id, stock_id.split(".")[0])
                            records = twse_df.to_dict("records")
                            self.db.bulk_insert_prices(stock_id, records)
                        except Exception as e:
                            logger.debug(f"寫入資料庫失敗: {e}")

                        price_data = {
                            "stock_id": stock_id,
                            "period": period,
                            "data": [],
                            "summary": {
                                "start_date": twse_df['date'].iloc[0],
                                "end_date": twse_df['date'].iloc[-1],
                                "data_points": len(twse_df),
                                "latest_price": float(twse_df['close'].iloc[-1]),
                                "highest_price": float(twse_df['high'].max()),
                                "lowest_price": float(twse_df['low'].min()),
                                "average_price": float(twse_df['close'].mean()),
                                "source": "twse"
                            }
                        }
                        for _, row in twse_df.iterrows():
                            price_data["data"].append({
                                "date": str(row['date']),
                                "open": float(row['open']),
                                "high": float(row['high']),
                                "low": float(row['low']),
                                "close": float(row['close']),
                                "volume": int(row.get('volume', 0))
                            })
                        return price_data
                except Exception as e:
                    logger.warning(f"TWSE 取得資料失敗: {e}，降級為 Yahoo Finance")

            # 3. 降級：使用 Yahoo Finance
            ticker = yf.Ticker(stock_id)
            history = ticker.history(period=period)

            if history.empty:
                raise ValueError(f"無法獲取股票 {stock_id} 的價格數據")

            # 同步寫入資料庫
            try:
                self.db.upsert_stock(stock_id, stock_id.split(".")[0])
                records = []
                for dt, row in history.iterrows():
                    records.append({
                        "date": dt.strftime("%Y-%m-%d"),
                        "open": float(row['Open']),
                        "high": float(row['High']),
                        "low": float(row['Low']),
                        "close": float(row['Close']),
                        "volume": int(row['Volume']),
                    })
                self.db.bulk_insert_prices(stock_id, records)
            except Exception as e:
                logger.debug(f"寫入資料庫失敗: {e}")

            price_data = {
                "stock_id": stock_id,
                "period": period,
                "data": [],
                "summary": {
                    "start_date": history.index[0].strftime("%Y-%m-%d"),
                    "end_date": history.index[-1].strftime("%Y-%m-%d"),
                    "data_points": len(history),
                    "latest_price": float(history['Close'].iloc[-1]),
                    "highest_price": float(history['High'].max()),
                    "lowest_price": float(history['Low'].min()),
                    "average_price": float(history['Close'].mean()),
                    "source": "yahoo_finance"
                }
            }

            for dt, row in history.iterrows():
                price_data["data"].append({
                    "date": dt.strftime("%Y-%m-%d"),
                    "open": float(row['Open']),
                    "high": float(row['High']),
                    "low": float(row['Low']),
                    "close": float(row['Close']),
                    "volume": int(row['Volume'])
                })

            return price_data

        except Exception as e:
            logger.error(f"獲取股票價格失敗: {e}")
            raise
    
    async def get_realtime_price(self, stock_id: str) -> Dict:
        """獲取即時股票價格"""
        try:
            # 使用Yahoo Finance獲取即時價格
            ticker = yf.Ticker(stock_id)
            
            # 獲取即時數據
            info = ticker.info
            
            if not info:
                raise ValueError(f"無法獲取股票 {stock_id} 的即時數據")
            
            # 構建即時數據
            realtime_data = {
                "stock_id": stock_id,
                "timestamp": datetime.now().isoformat(),
                "price": info.get("currentPrice", info.get("regularMarketPrice", 0)),
                "change": info.get("regularMarketChange", 0),
                "change_percent": info.get("regularMarketChangePercent", 0),
                "volume": info.get("regularMarketVolume", 0),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE", 0),
                "dividend_yield": info.get("dividendYield", 0),
                "52_week_high": info.get("fiftyTwoWeekHigh", 0),
                "52_week_low": info.get("fiftyTwoWeekLow", 0),
                "currency": info.get("currency", "TWD"),
                "exchange": info.get("exchange", "TWSE")
            }
            
            return realtime_data
            
        except Exception as e:
            logger.error(f"獲取即時股票價格失敗: {e}")
            raise
    
    async def get_stock_info(self, stock_id: str) -> Dict:
        """獲取股票基本資訊"""
        try:
            # 使用Yahoo Finance獲取股票資訊
            ticker = yf.Ticker(stock_id)
            info = ticker.info
            
            if not info:
                raise ValueError(f"無法獲取股票 {stock_id} 的基本資訊")
            
            # 構建股票資訊
            stock_info = {
                "stock_id": stock_id,
                "name": info.get("longName", info.get("shortName", "")),
                "market": info.get("market", ""),
                "industry": info.get("industry", ""),
                "sector": info.get("sector", ""),
                "description": info.get("longBusinessSummary", ""),
                "website": info.get("website", ""),
                "employees": info.get("fullTimeEmployees", 0),
                "country": info.get("country", ""),
                "city": info.get("city", ""),
                "currency": info.get("currency", "TWD"),
                "exchange": info.get("exchange", "TWSE")
            }
            
            return stock_info
            
        except Exception as e:
            logger.error(f"獲取股票基本資訊失敗: {e}")
            raise
    
    async def get_financial_data(self, stock_id: str) -> Dict:
        """獲取財務數據"""
        try:
            # 使用Yahoo Finance獲取財務數據
            ticker = yf.Ticker(stock_id)
            
            # 獲取財務報表
            financials = ticker.financials
            balance_sheet = ticker.balance_sheet
            cashflow = ticker.cashflow
            
            # 轉換為字典格式
            financial_data = {
                "stock_id": stock_id,
                "income_statement": {},
                "balance_sheet": {},
                "cash_flow": {},
                "ratios": {}
            }
            
            # 處理損益表
            if not financials.empty:
                for col in financials.columns:
                    year = col.strftime("%Y")
                    financial_data["income_statement"][year] = {}
                    for idx in financials.index:
                        value = financials.loc[idx, col]
                        if pd.notna(value):
                            financial_data["income_statement"][year][str(idx)] = float(value)
            
            # 處理資產負債表
            if not balance_sheet.empty:
                for col in balance_sheet.columns:
                    year = col.strftime("%Y")
                    financial_data["balance_sheet"][year] = {}
                    for idx in balance_sheet.index:
                        value = balance_sheet.loc[idx, col]
                        if pd.notna(value):
                            financial_data["balance_sheet"][year][str(idx)] = float(value)
            
            # 處理現金流量表
            if not cashflow.empty:
                for col in cashflow.columns:
                    year = col.strftime("%Y")
                    financial_data["cash_flow"][year] = {}
                    for idx in cashflow.index:
                        value = cashflow.loc[idx, col]
                        if pd.notna(value):
                            financial_data["cash_flow"][year][str(idx)] = float(value)
            
            return financial_data
            
        except Exception as e:
            logger.error(f"獲取財務數據失敗: {e}")
            raise
    
    async def get_market_indices(self, market: str = "taiwan") -> Dict:
        """獲取市場指數"""
        try:
            # 定義市場指數
            indices = {
                "taiwan": {
                    "TAIEX": "^TWII",  # 台灣加權指數
                    "OTC": "^OTC",     # 櫃買指數
                    "TECH": "^TWT01"   # 台灣科技指數
                },
                "japan": {
                    "NIKKEI": "^N225",  # 日經指數
                    "TOPIX": "^TOPX"    # 東證指數
                },
                "korea": {
                    "KOSPI": "^KS11",  # 韓國綜合指數
                    "KOSDAQ": "^KQ11"  # 韓國科斯達克指數
                },
                "usa": {
                    "SP500": "^GSPC",   # 標普500指數
                    "NASDAQ": "^IXIC",  # 納斯達克指數
                    "DOW": "^DJI"       # 道瓊斯指數
                }
            }
            
            if market not in indices:
                raise ValueError(f"不支持的市場: {market}")
            
            market_indices = {}
            for index_name, symbol in indices[market].items():
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    
                    market_indices[index_name] = {
                        "symbol": symbol,
                        "name": info.get("shortName", index_name),
                        "price": info.get("regularMarketPrice", 0),
                        "change": info.get("regularMarketChange", 0),
                        "change_percent": info.get("regularMarketChangePercent", 0),
                        "volume": info.get("regularMarketVolume", 0)
                    }
                except Exception as e:
                    logger.warning(f"獲取指數 {index_name} 失敗: {e}")
                    market_indices[index_name] = {
                        "symbol": symbol,
                        "name": index_name,
                        "error": str(e)
                    }
            
            return {
                "market": market,
                "timestamp": datetime.now().isoformat(),
                "indices": market_indices
            }
            
        except Exception as e:
            logger.error(f"獲取市場指數失敗: {e}")
            raise
    
    async def get_global_market_data(self) -> Dict:
        """獲取全球市場數據"""
        try:
            # 獲取各市場指數
            markets = ["taiwan", "japan", "korea", "usa"]
            global_data = {}
            
            for market in markets:
                try:
                    market_data = await self.get_market_indices(market)
                    global_data[market] = market_data
                except Exception as e:
                    logger.warning(f"獲取 {market} 市場數據失敗: {e}")
                    global_data[market] = {"error": str(e)}
            
            return {
                "timestamp": datetime.now().isoformat(),
                "markets": global_data
            }
            
        except Exception as e:
            logger.error(f"獲取全球市場數據失敗: {e}")
            raise
    
    async def get_stock_list(self, market: str = "taiwan") -> List[Dict]:
        """獲取股票列表"""
        try:
            if market == "taiwan":
                # 嘗試從 TWSE 取得即時列表
                try:
                    twse_list = self.twse.get_stock_list()
                    if not twse_list.empty:
                        result = []
                        for _, row in twse_list.iterrows():
                            result.append({
                                "id": f"{row['stock_id']}.TW",
                                "name": row['name'],
                                "industry": ""
                            })
                        return result
                except Exception as e:
                    logger.debug(f"TWSE 股票列表取得失敗: {e}")

                # 降級：返回常用股票
                return [
                    {"id": "2330.TW", "name": "台積電", "industry": "半導體"},
                    {"id": "2317.TW", "name": "鴻海", "industry": "電子零組件"},
                    {"id": "2454.TW", "name": "聯發科", "industry": "半導體"},
                    {"id": "2308.TW", "name": "台達電", "industry": "電子零組件"},
                    {"id": "2412.TW", "name": "中華電", "industry": "電信"},
                    {"id": "2881.TW", "name": "富邦金", "industry": "金融業"},
                    {"id": "2882.TW", "name": "國泰金", "industry": "金融業"},
                    {"id": "2884.TW", "name": "玉山金", "industry": "金融業"},
                    {"id": "2886.TW", "name": "兆豐金", "industry": "金融業"},
                    {"id": "2891.TW", "name": "中信金", "industry": "金融業"},
                ]
            else:
                return []

        except Exception as e:
            logger.error(f"獲取股票列表失敗: {e}")
            raise
    
    def clear_cache(self):
        """清除快取"""
        self.cache.clear()
        logger.info("快取已清除")