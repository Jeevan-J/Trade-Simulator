from typing import List

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from binance import Client
from dotenv import load_dotenv
import os, uuid
from fastapi_utils.tasks import repeat_every

from . import crud, models, schemas
from .database import SessionLocal, engine

load_dotenv()

bapi_key = os.getenv("BINANCE_API_KEY","")
bapi_secret = os.getenv("BINANCE_API_SECRET","")

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

bclient = Client(bapi_key, bapi_secret)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

ACTIVE_TRADES = dict({})

@app.post("/trades/", response_model=schemas.TradeCreate)
async def create_trade(trade: schemas.TradeCreate):
    global ACTIVE_TRADES
    ACTIVE_TRADES[str(uuid.uuid4())]=trade
    return trade

@app.get("/active_trades", response_model=List[schemas.TradeCreate])
async def get_active_trades():
    # global ACTIVE_TRADES
    active_trades = json.loads(open("data/active_trades.json","r").read())
    return list(active_trades.values())

@app.get("/closed_trades", response_model=List[schemas.Trade])
async def get_closed_trades(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_trades(db, skip=skip, limit=limit)

@app.on_event("startup")
@repeat_every(seconds=5)
async def check_trades() -> None:
    global bclient, ACTIVE_TRADES
    db = get_db()
    try:
        for active_trade_id in list(ACTIVE_TRADES.keys()):
            active_trade = ACTIVE_TRADES[active_trade_id]
            res = bclient.get_symbol_ticker(symbol=active_trade.trade_symbol)
            print(active_trade.trade_status,"::",active_trade.entry_price, "::", float(res['price']))
            if active_trade.trade_status == "Waiting":
                if (active_trade.trade_type == "Long") and (active_trade.entry_price < float(res['price'])):
                    ACTIVE_TRADES[active_trade_id].trade_status = "Opened"
                    print("Opened a trade")
                elif (active_trade.trade_type == "Short") and (active_trade.entry_price > float(res['price'])):
                    ACTIVE_TRADES[active_trade_id].trade_status = "Opened"
                    print("Opened a trade")
                pass
            elif active_trade.trade_status == "Opened":
                trade_completed = False
                if (active_trade.trade_type == "Long"):
                    if (active_trade.target < float(res['price'])):
                        ACTIVE_TRADES[active_trade_id].trade_status = "Success"
                        trade_completed = True
                    elif (active_trade.stop_loss > float(res['price'])):
                        ACTIVE_TRADES[active_trade_id].trade_status = "Failed"
                        trade_completed = True
                elif (active_trade.trade_type == "Short"):
                    if (active_trade.target > float(res['price'])):
                        ACTIVE_TRADES[active_trade_id].trade_status = "Success"
                        trade_completed = True
                    elif (active_trade.stop_loss < float(res['price'])):
                        ACTIVE_TRADES[active_trade_id].trade_status = "Failed"
                        trade_completed = True
                if trade_completed:
                    print("Closed a trade")
                    ACTIVE_TRADES.pop(active_trade_id)
                    crud.create_trade(db, active_trade)
                pass
    except Exception as e:
        print(str(e))