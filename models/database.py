"""
台灣股票分析工具 - 資料庫模型定義
使用 SQLAlchemy ORM，開發環境用 SQLite，生產環境可切換 PostgreSQL
"""
from datetime import datetime, date
from typing import Optional
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Date, DateTime,
    ForeignKey, UniqueConstraint, Index, Text, Boolean
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from loguru import logger
import os

Base = declarative_base()


# ──────────────────────────────────────────────
#  股票基本資料
# ──────────────────────────────────────────────
class Stock(Base):
    """股票基本資訊"""
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(50), nullable=False)
    market = Column(String(20), default="taiwan")  # taiwan, tpe
    industry = Column(String(50))
    listed_date = Column(String(10))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 關聯
    prices = relationship("Price", back_populates="stock", cascade="all, delete-orphan")
    institutional_records = relationship("InstitutionalInvestor", back_populates="stock", cascade="all, delete-orphan")
    margin_records = relationship("MarginTrading", back_populates="stock", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Stock {self.stock_id} {self.name}>"


# ──────────────────────────────────────────────
#  每日價格資料
# ──────────────────────────────────────────────
class Price(Base):
    """每日收盤價格"""
    __tablename__ = "prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(String(20), ForeignKey("stocks.stock_id"), nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    change = Column(Float)
    volume = Column(Integer)
    trade_value = Column(Float)
    transactions = Column(Integer)

    # 關聯
    stock = relationship("Stock", back_populates="prices")

    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uix_stock_date"),
        Index("ix_prices_stock_date", "stock_id", "date"),
    )

    def __repr__(self):
        return f"<Price {self.stock_id} {self.date} close={self.close}>"


# ──────────────────────────────────────────────
#  三大法人買賣超
# ──────────────────────────────────────────────
class InstitutionalInvestor(Base):
    """三大法人買賣超日報"""
    __tablename__ = "institutional_investors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(String(20), ForeignKey("stocks.stock_id"), nullable=False)
    date = Column(Date, nullable=False)

    # 外資
    foreign_buy = Column(Integer)
    foreign_sell = Column(Integer)
    foreign_net = Column(Integer)

    # 投信
    trust_buy = Column(Integer)
    trust_sell = Column(Integer)
    trust_net = Column(Integer)

    # 自營商
    dealer_buy = Column(Integer)
    dealer_sell = Column(Integer)
    dealer_net = Column(Integer)

    # 合計
    total_net = Column(Integer)

    # 關聯
    stock = relationship("Stock", back_populates="institutional_records")

    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uix_inst_stock_date"),
        Index("ix_inst_stock_date", "stock_id", "date"),
    )


# ──────────────────────────────────────────────
#  融資融券
# ──────────────────────────────────────────────
class MarginTrading(Base):
    """融資融券統計"""
    __tablename__ = "margin_trading"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(String(20), ForeignKey("stocks.stock_id"), nullable=False)
    date = Column(Date, nullable=False)

    # 融資
    margin_buy = Column(Integer)
    margin_sell = Column(Integer)
    margin_repay = Column(Integer)
    margin_limit = Column(Integer)
    margin_balance = Column(Integer)
    margin_today_balance = Column(Integer)

    # 融券
    short_buy = Column(Integer)
    short_sell = Column(Integer)
    short_repay = Column(Integer)
    short_limit = Column(Integer)
    short_balance = Column(Integer)
    short_today_balance = Column(Integer)

    # 關聯
    stock = relationship("Stock", back_populates="margin_records")

    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uix_margin_stock_date"),
    )


# ──────────────────────────────────────────────
#  技術指標快取
# ──────────────────────────────────────────────
class IndicatorCache(Base):
    """技術指標計算結果快取"""
    __tablename__ = "indicator_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(String(20), nullable=False)
    indicator = Column(String(50), nullable=False)  # sma_20, rsi_14, macd, ...
    date = Column(Date, nullable=False)
    value = Column(Float)
    params = Column(Text)  # JSON 格式的參數

    __table_args__ = (
        UniqueConstraint("stock_id", "indicator", "date", name="uix_indicator"),
        Index("ix_indicator_stock", "stock_id", "indicator"),
    )


# ──────────────────────────────────────────────
#  ML 預測結果快取
# ──────────────────────────────────────────────
class PredictionCache(Base):
    """ML 預測結果快取"""
    __tablename__ = "prediction_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(String(20), nullable=False)
    model = Column(String(50), nullable=False)  # arima, xgboost, ensemble, ...
    predict_date = Column(Date, nullable=False)  # 預測目標日期
    predicted_price = Column(Float)
    confidence_lower = Column(Float)
    confidence_upper = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("stock_id", "model", "predict_date", name="uix_prediction"),
        Index("ix_prediction_stock_model", "stock_id", "model"),
    )
