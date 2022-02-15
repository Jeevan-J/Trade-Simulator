from typing import List, Optional, Literal, Dict
from datetime import datetime
from pydantic import BaseModel, root_validator

class TradeBase(BaseModel):
    """
    Mandatory Input Fields
    """
    trade_type: Literal['Long','Short']
    trade_symbol: str = "BTCUSDT"
    quantity: float
    leverage: int
    entry_price: float
    stop_loss: float
    target: float
    created_by: str

    """
    Calculated Fields
    """
    leveraged_quantity: Optional[float]
    profit: Optional[float]
    profit_roe: Optional[float]
    loss: Optional[float]
    loss_roe: Optional[float]
    initial_margin: Optional[float]
    risk_reward_ratio: Optional[float]
    created_at: Optional[datetime]
    trade_status: Optional[Literal['Waiting','Opened','Success','Failed']]

    @root_validator
    def compute_values(cls, values) -> Dict:
        values["leveraged_quantity"] = values.get('quantity') * values.get('leverage')
        values["profit"] = abs((values.get('target')-values.get('entry_price'))*(values.get('leveraged_quantity')/values.get('entry_price')))
        values["loss"] = -1*abs((values.get('stop_loss')-values.get('entry_price'))*(values.get('leveraged_quantity')/values.get('entry_price')))
        values["initial_margin"] = (1/values.get('leverage'))*values.get('leveraged_quantity')
        values["profit_roe"] = values["profit"] / values["initial_margin"]
        values["loss_roe"] = values["loss"] / values["initial_margin"]
        values["risk_reward_ratio"] = abs(values["profit"]/values["loss"])
        if (values.get("created_at") == None) or (values.get("created_at") == ""):
            values["created_at"] = datetime.now()
        if (values.get("trade_status") == None) or (values.get("trade_status") == ""):
            values["trade_status"] = "Waiting"
        return values
        
class TradeCreate(TradeBase):
    pass

class Trade(TradeBase):
    id: int

    class Config:
        orm_mode = True