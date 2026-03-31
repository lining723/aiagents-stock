from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class EntryRange(BaseModel):
    min: float = Field(..., description="进场区间最小值")
    max: float = Field(..., description="进场区间最大值")


class MonitoredStockCreate(BaseModel):
    symbol: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    rating: str = Field(default="持有", description="投资评级：买入/持有/卖出")
    entry_range: EntryRange = Field(..., description="进场区间")
    take_profit: float = Field(..., description="止盈位")
    stop_loss: float = Field(..., description="止损位")
    check_interval: int = Field(default=30, description="检查间隔（分钟）", ge=1, le=1440)
    notification_enabled: bool = Field(default=True, description="是否启用通知")
    trading_hours_only: bool = Field(default=True, description="是否仅交易时段监控")
    quant_enabled: bool = Field(default=False, description="是否启用量化交易")
    quant_config: Optional[Dict[str, Any]] = Field(default=None, description="量化配置")


class MonitoredStockUpdate(BaseModel):
    rating: Optional[str] = Field(None, description="投资评级：买入/持有/卖出")
    entry_range: Optional[EntryRange] = Field(None, description="进场区间")
    take_profit: Optional[float] = Field(None, description="止盈位")
    stop_loss: Optional[float] = Field(None, description="止损位")
    check_interval: Optional[int] = Field(None, description="检查间隔（分钟）", ge=1, le=1440)
    notification_enabled: Optional[bool] = Field(None, description="是否启用通知")
    trading_hours_only: Optional[bool] = Field(None, description="是否仅交易时段监控")
    quant_enabled: Optional[bool] = Field(None, description="是否启用量化交易")
    quant_config: Optional[Dict[str, Any]] = Field(None, description="量化配置")


class MonitoredStockInfo(BaseModel):
    id: str = Field(..., description="ID")
    symbol: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    rating: str = Field(..., description="投资评级")
    entry_range: Dict[str, Any] = Field(..., description="进场区间")
    take_profit: Optional[float] = Field(None, description="止盈位")
    stop_loss: Optional[float] = Field(None, description="止损位")
    current_price: Optional[float] = Field(None, description="当前价格")
    last_checked: Optional[str] = Field(None, description="最后检查时间")
    check_interval: int = Field(..., description="检查间隔（分钟）")
    notification_enabled: bool = Field(..., description="是否启用通知")
    trading_hours_only: bool = Field(..., description="是否仅交易时段监控")
    quant_enabled: bool = Field(..., description="是否启用量化交易")
    quant_config: Optional[Dict[str, Any]] = Field(None, description="量化配置")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")


class MonitoredStockListResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    stocks: List[MonitoredStockInfo] = Field(default_factory=list, description="监测股票列表")
    total: int = Field(default=0, description="总数")


class MonitoredStockResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    stock: Optional[MonitoredStockInfo] = Field(None, description="监测股票信息")


class NotificationInfo(BaseModel):
    id: str = Field(..., description="通知ID")
    stock_id: str = Field(..., description="股票ID")
    symbol: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    type: str = Field(..., description="通知类型：entry/take_profit/stop_loss")
    message: str = Field(..., description="通知消息")
    triggered_at: str = Field(..., description="触发时间")
    sent: bool = Field(..., description="是否已发送")


class NotificationListResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    notifications: List[NotificationInfo] = Field(default_factory=list, description="通知列表")
    total: int = Field(default=0, description="总数")


class MonitorConfig(BaseModel):
    monitor_enabled: bool = Field(default=False, description="监控服务是否启用")
    check_interval: int = Field(default=300, description="全局检查间隔（秒）")
    auto_notification: bool = Field(default=True, description="是否自动发送通知")


class MonitorConfigResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    config: MonitorConfig = Field(..., description="监控配置")
