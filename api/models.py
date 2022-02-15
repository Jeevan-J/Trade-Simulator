from sqlalchemy import Boolean, Column, DateTime, Integer, String, Float
from sqlalchemy.sql import func

from .database import Base

class Trades(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    trade_type = Column(String(10))
    trade_symbol = Column(String(15))
    quantity = Column(Float)
    leverage = Column(Integer)
    entry_price = Column(Float)
    stop_loss = Column(Float)
    target = Column(Float)
    leveraged_quantity = Column(Float)
    profit = Column(Float)
    profit_roe = Column(Float)
    loss = Column(Float)
    loss_roe = Column(Float)
    initial_margin = Column(Float)
    risk_reward_ratio = Column(Float)
    trade_status = Column(String(10))
    created_by = Column(String(50))
    created_at = Column(DateTime(timezone=True))
    closed_at = Column(DateTime(timezone=True), server_default=func.now())