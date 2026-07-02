"""
台灣股票分析工具 - 資料庫管理器
提供 CRUD 操作和資料同步功能
"""

import os
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from models.database import (
    Base,
    IndicatorCache,
    InstitutionalInvestor,
    MarginTrading,
    PredictionCache,
    Price,
    Stock,
)


class DBManager:
    """資料庫管理器"""

    def __init__(self, db_url: Optional[str] = None):
        if db_url is None:
            # 預設使用 SQLite
            db_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "data", "stock_analysis.db"
            )
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            db_url = f"sqlite:///{db_path}"

        self.engine = create_engine(db_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def init_db(self):
        """初始化資料庫（建表）"""
        Base.metadata.create_all(self.engine)
        logger.info("資料庫表已建立")

    def get_session(self) -> Session:
        """取得資料庫 session"""
        return self.SessionLocal()

    # ──────────────────────────────────────────────
    #  Stock CRUD
    # ──────────────────────────────────────────────
    def upsert_stock(
        self, stock_id: str, name: str, market: str = "taiwan", industry: str = ""
    ) -> Stock:
        """新增或更新股票"""
        with self.get_session() as session:
            stock = session.query(Stock).filter_by(stock_id=stock_id).first()
            if stock:
                stock.name = name
                stock.market = market
                stock.industry = industry
            else:
                stock = Stock(
                    stock_id=stock_id, name=name, market=market, industry=industry
                )
                session.add(stock)
            session.commit()
            session.refresh(stock)
            return stock

    def get_stock(self, stock_id: str) -> Optional[Stock]:
        """取得單一股票"""
        with self.get_session() as session:
            return session.query(Stock).filter_by(stock_id=stock_id).first()

    def get_stocks(self, market: Optional[str] = None) -> List[Stock]:
        """取得股票列表"""
        with self.get_session() as session:
            query = session.query(Stock)
            if market:
                query = query.filter_by(market=market)
            return query.all()

    # ──────────────────────────────────────────────
    #  Price CRUD
    # ──────────────────────────────────────────────
    def upsert_price(
        self,
        stock_id: str,
        trade_date: date,
        open_p: float,
        high: float,
        low: float,
        close: float,
        volume: int,
        trade_value: float = 0,
        transactions: int = 0,
        change: float = 0,
    ) -> Price:
        """新增或更新價格"""
        with self.get_session() as session:
            price = (
                session.query(Price)
                .filter_by(stock_id=stock_id, date=trade_date)
                .first()
            )
            if price:
                price.open = open_p
                price.high = high
                price.low = low
                price.close = close
                price.volume = volume
                price.trade_value = trade_value
                price.transactions = transactions
                price.change = change
            else:
                price = Price(
                    stock_id=stock_id,
                    date=trade_date,
                    open=open_p,
                    high=high,
                    low=low,
                    close=close,
                    volume=volume,
                    trade_value=trade_value,
                    transactions=transactions,
                    change=change,
                )
                session.add(price)
            session.commit()
            session.refresh(price)
            return price

    def get_prices(
        self,
        stock_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Price]:
        """取得價格歷史"""
        with self.get_session() as session:
            query = session.query(Price).filter_by(stock_id=stock_id)
            if start_date:
                query = query.filter(Price.date >= start_date)
            if end_date:
                query = query.filter(Price.date <= end_date)
            return query.order_by(Price.date).all()

    def get_price_df(
        self,
        stock_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ):
        """取得價格歷史，回傳 DataFrame"""
        import pandas as pd

        prices = self.get_prices(stock_id, start_date, end_date)
        if not prices:
            return pd.DataFrame()
        rows = []
        for p in prices:
            rows.append(
                {
                    "date": p.date,
                    "open": p.open,
                    "high": p.high,
                    "low": p.low,
                    "close": p.close,
                    "volume": p.volume,
                    "trade_value": p.trade_value,
                    "change": p.change,
                }
            )
        df = pd.DataFrame(rows)
        df.set_index("date", inplace=True)
        return df

    def bulk_insert_prices(self, stock_id: str, records: List[Dict]) -> int:
        """批量插入價格資料"""
        count = 0
        with self.get_session() as session:
            for rec in records:
                trade_date = rec.get("date")
                if isinstance(trade_date, str):
                    trade_date = datetime.strptime(trade_date, "%Y-%m-%d").date()

                exists = (
                    session.query(Price)
                    .filter_by(stock_id=stock_id, date=trade_date)
                    .first()
                )

                if not exists:
                    price = Price(
                        stock_id=stock_id,
                        date=trade_date,
                        open=rec.get("open"),
                        high=rec.get("high"),
                        low=rec.get("low"),
                        close=rec.get("close"),
                        volume=rec.get("volume", 0),
                        trade_value=rec.get("trade_value", 0),
                        transactions=rec.get("transactions", 0),
                    )
                    session.add(price)
                    count += 1
            session.commit()
        return count

    # ──────────────────────────────────────────────
    #  Institutional Investor CRUD
    # ──────────────────────────────────────────────
    def upsert_institutional(
        self, stock_id: str, trade_date: date, data: Dict
    ) -> InstitutionalInvestor:
        """新增或更新三大法人資料"""
        with self.get_session() as session:
            record = (
                session.query(InstitutionalInvestor)
                .filter_by(stock_id=stock_id, date=trade_date)
                .first()
            )

            if record:
                for k, v in data.items():
                    if hasattr(record, k):
                        setattr(record, k, v)
            else:
                record = InstitutionalInvestor(
                    stock_id=stock_id, date=trade_date, **data
                )
                session.add(record)

            session.commit()
            session.refresh(record)
            return record

    def get_institutional(
        self, stock_id: str, days: int = 30
    ) -> List[InstitutionalInvestor]:
        """取得三大法人歷史資料"""
        with self.get_session() as session:
            start = date.today() - timedelta(days=days)
            return (
                session.query(InstitutionalInvestor)
                .filter(
                    InstitutionalInvestor.stock_id == stock_id,
                    InstitutionalInvestor.date >= start,
                )
                .order_by(InstitutionalInvestor.date)
                .all()
            )

    # ──────────────────────────────────────────────
    #  Margin Trading CRUD
    # ──────────────────────────────────────────────
    def upsert_margin(
        self, stock_id: str, trade_date: date, data: Dict
    ) -> MarginTrading:
        """新增或更新融資融券資料"""
        with self.get_session() as session:
            record = (
                session.query(MarginTrading)
                .filter_by(stock_id=stock_id, date=trade_date)
                .first()
            )

            if record:
                for k, v in data.items():
                    if hasattr(record, k):
                        setattr(record, k, v)
            else:
                record = MarginTrading(stock_id=stock_id, date=trade_date, **data)
                session.add(record)

            session.commit()
            session.refresh(record)
            return record

    def get_margin(self, stock_id: str, days: int = 30) -> List[MarginTrading]:
        """取得融資融券歷史資料"""
        with self.get_session() as session:
            start = date.today() - timedelta(days=days)
            return (
                session.query(MarginTrading)
                .filter(MarginTrading.stock_id == stock_id, MarginTrading.date >= start)
                .order_by(MarginTrading.date)
                .all()
            )

    # ──────────────────────────────────────────────
    #  Cache 操作
    # ──────────────────────────────────────────────
    def get_cached_prediction(
        self, stock_id: str, model: str, target_date: date
    ) -> Optional[PredictionCache]:
        """取得快取的預測結果"""
        with self.get_session() as session:
            return (
                session.query(PredictionCache)
                .filter_by(stock_id=stock_id, model=model, predict_date=target_date)
                .first()
            )

    def save_prediction(
        self,
        stock_id: str,
        model: str,
        target_date: date,
        predicted_price: float,
        lower: float,
        upper: float,
    ) -> PredictionCache:
        """儲存預測結果"""
        with self.get_session() as session:
            record = PredictionCache(
                stock_id=stock_id,
                model=model,
                predict_date=target_date,
                predicted_price=predicted_price,
                confidence_lower=lower,
                confidence_upper=upper,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record

    # ──────────────────────────────────────────────
    #  資料同步
    # ──────────────────────────────────────────────
    def sync_stock_prices(self, stock_id: str, months: int = 12) -> int:
        """從 TWSE 同步股票價格資料到資料庫"""
        from data.twse_fetcher import get_twse_fetcher

        twse = get_twse_fetcher()
        logger.info(f"正在同步 {stock_id} 最近 {months} 個月的價格資料...")

        # 去掉 .TW / .TWO 後綴
        clean_id = stock_id.replace(".TW", "").replace(".TWO", "")
        df = twse.get_stock_history(clean_id, months)
        if df.empty:
            logger.warning(f"無法取得 {stock_id} 的歷史資料")
            return 0

        records = df.to_dict("records")
        count = self.bulk_insert_prices(stock_id, records)
        logger.info(f"已同步 {stock_id} 筆價格資料: {count} 筆新增")
        return count


# 全域實例
_db_manager: Optional[DBManager] = None


def get_db_manager() -> DBManager:
    """取得 DBManager 全域實例"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DBManager()
        _db_manager.init_db()
    return _db_manager
