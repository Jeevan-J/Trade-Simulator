from typing import List

from fastapi import Depends, FastAPI, HTTPException, Request
from sqlalchemy.orm import Session
from binance import Client
from dotenv import load_dotenv
import os, uuid, time
from fastapi_utils.tasks import repeat_every
import logging
from sse_starlette.sse import EventSourceResponse
from sh import tail

from . import crud, models, schemas
from .database import SessionLocal, engine

load_dotenv()

bapi_key = os.getenv("BINANCE_API_KEY","")
bapi_secret = os.getenv("BINANCE_API_SECRET","")

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

bclient = Client(bapi_key, bapi_secret)

# setup loggers
logging.config.fileConfig('api/logging.conf', defaults={'logfilename': 'data/trades.log'}, disable_existing_loggers=False)
# get root logger
logger = logging.getLogger("tradeSimulator")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/trades/", response_model=schemas.Trade)
async def create_trade(trade: schemas.TradeCreate, db: Session = Depends(get_db)):
    trade = crud.create_trade(db, trade)
    return trade

@app.get("/active_trades", response_model=List[schemas.Trade])
async def get_active_trades(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    active_trades = crud.get_active_trades(db, skip=skip, limit=limit)
    return active_trades

@app.get("/closed_trades", response_model=List[schemas.Trade])
async def get_closed_trades(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    trades = crud.get_trades(db, skip=skip, limit=limit)
    return trades

async def logGenerator(request):
    LOGFILE = "data/trades.log"
    for line in tail("-f", LOGFILE, _iter=True):
        if await request.is_disconnected():
            print("client disconnected!!!")
            break
        yield line
        time.sleep(0.5)

# @app.get("/logstream")
# async def logstream(request: Request):
#     event_generator = logGenerator(request)
#     return EventSourceResponse(event_generator)

@app.on_event("startup")
@repeat_every(seconds=5)
async def check_trades() -> None:
    global bclient
    db = SessionLocal()
    try:
        ACTIVE_TRADES = crud.get_active_trades(db)
        for active_trade in ACTIVE_TRADES:
            res = bclient.get_symbol_ticker(symbol=active_trade.trade_symbol)
            trade_updated = False
            if active_trade.trade_status == "Waiting":
                if (active_trade.trade_type == "Long") and (active_trade.entry_price < float(res['price'])):
                    active_trade.trade_status = "Opened"
                    trade_updated = True
                    logger.info(str(active_trade.id)+" :: Opened a trade")
                elif (active_trade.trade_type == "Short") and (active_trade.entry_price > float(res['price'])):
                    active_trade.trade_status = "Opened"
                    trade_updated = True
                    logger.info(str(active_trade.id)+" :: Opened a trade")
                pass
            if active_trade.trade_status == "Opened":
                if (active_trade.trade_type == "Long"):
                    if (active_trade.target < float(res['price'])):
                        active_trade.trade_status = "Success"
                        logger.info(str(active_trade.id)+" :: Closed a trade")
                        trade_updated = True
                    elif (active_trade.stop_loss > float(res['price'])):
                        active_trade.trade_status = "Failed"
                        logger.info(str(active_trade.id)+" :: Closed a trade")
                        trade_updated = True
                elif (active_trade.trade_type == "Short"):
                    if (active_trade.target > float(res['price'])):
                        active_trade.trade_status = "Success"
                        logger.info(str(active_trade.id)+" :: Closed a trade")
                        trade_updated = True
                    elif (active_trade.stop_loss < float(res['price'])):
                        active_trade.trade_status = "Failed"
                        logger.info(str(active_trade.id)+" :: Closed a trade")
                        trade_updated = True
            if trade_updated:
                crud.update_trade(db, active_trade)
            pass
    except Exception as e:
        print(str(e))
        logger.error(str(e))
    db.close()