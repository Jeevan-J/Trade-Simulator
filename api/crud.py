from sqlalchemy.orm import Session

from . import models, schemas

def get_trade(db: Session, trade_id: int):
    return db.query(models.Trades).filter(models.Trades.id == trade_id).first()

def get_trades(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Trades).offset(skip).limit(limit).all()

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