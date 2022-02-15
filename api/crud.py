from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from . import models, schemas

def get_trade(db: Session, trade_id: int):
    return db.query(models.Trades).filter(models.Trades.id == trade_id).first()

def get_trades(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Trades).offset(skip).limit(limit).all()
    
def get_active_trades(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Trades).filter(or_(models.Trades.trade_status == "Waiting",models.Trades.trade_status == "Opened")).offset(skip).limit(limit).all()

def create_trade(db: Session, trade: schemas.TradeCreate):
    db_trade = models.Trades(
        trade_type=trade.trade_type,
        trade_symbol=trade.trade_symbol,
        quantity=trade.quantity,
        leverage=trade.leverage,
        entry_price=trade.entry_price,
        stop_loss=trade.stop_loss,
        target=trade.target,
        leveraged_quantity=trade.leveraged_quantity,
        profit=trade.profit,
        profit_roe=trade.profit_roe,
        loss=trade.loss,
        loss_roe=trade.loss_roe,
        initial_margin=trade.initial_margin,
        risk_reward_ratio=trade.risk_reward_ratio,
        trade_status=trade.trade_status,
        created_by=trade.created_by,
        created_at=trade.created_at,
    )
    db.add(db_trade)
    db.commit()
    db.refresh(db_trade)
    return db_trade

def update_trade(db: Session, db_trade: models.Trades): #trade_id: int, updates: dict):
    # db_trade = db.query(models.Trades).filter(models.Trades.id == trade_id).first()
    # for trade_key, trade_value in updates.items():
    #     setattr(db_trade, trade_key, trade_value)
    db.add(db_trade)
    db.commit()
    db.refresh(db_trade)
    return db_trade
