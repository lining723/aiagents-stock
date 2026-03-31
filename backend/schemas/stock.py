from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ValueStockRequest(BaseModel):
    pe_max: float = Field(default=20.0, description="最大市盈率")
    pb_max: float = Field(default=1.5, description="最大市净率")
    top_n: int = Field(default=10, description="返回前N只股票", ge=5, le=50)


class MainForceStockRequest(BaseModel):
    days_ago: int = Field(default=1, description="距今多少天", ge=1, le=30)
    min_market_cap: float = Field(default=50.0, description="最小市值（亿）", ge=1.0)
    max_market_cap: float = Field(default=500.0, description="最大市值（亿）", ge=1.0)
    max_range_change: float = Field(default=20.0, description="最大涨跌幅限制（%）", ge=1.0)
    top_n: int = Field(default=20, description="返回前N只股票", ge=5, le=100)


class StockInfo(BaseModel):
    symbol: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    pe_ratio: Optional[float] = Field(None, description="市盈率")
    pb_ratio: Optional[float] = Field(None, description="市净率")
    dividend_rate: Optional[float] = Field(None, description="股息率")
    debt_ratio: Optional[float] = Field(None, description="资产负债率")
    market_cap: Optional[float] = Field(None, description="市值")
    industry: Optional[str] = Field(None, description="所属行业")
    range_change: Optional[float] = Field(None, description="区间涨跌幅")
    main_fund_inflow: Optional[float] = Field(None, description="主力资金净流入")


class StockListResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    count: int = Field(default=0, description="股票数量")
    stocks: List[StockInfo] = Field(default_factory=list, description="股票列表")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
