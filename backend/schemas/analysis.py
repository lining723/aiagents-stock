from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class TechnicalAnalysisRequest(BaseModel):
    symbol: str = Field(..., description="股票代码")
    days_ago: int = Field(default=60, description="分析天数", ge=30, le=365)


class FundamentalAnalysisRequest(BaseModel):
    symbol: str = Field(..., description="股票代码")


class ComprehensiveAnalysisRequest(BaseModel):
    symbol: str = Field(..., description="股票代码")
    days_ago: int = Field(default=60, description="分析天数", ge=30, le=365)


class TechnicalIndicator(BaseModel):
    name: str = Field(..., description="指标名称")
    value: Optional[float] = Field(None, description="当前值")
    signal: Optional[str] = Field(None, description="信号: buy/sell/hold")
    description: Optional[str] = Field(None, description="说明")


class KlineData(BaseModel):
    date: str = Field(..., description="日期")
    open: float = Field(..., description="开盘价")
    close: float = Field(..., description="收盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    volume: float = Field(..., description="成交量")
    ma5: Optional[float] = Field(None, description="MA5")
    ma10: Optional[float] = Field(None, description="MA10")
    ma20: Optional[float] = Field(None, description="MA20")


class TechnicalAnalysisResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    symbol: str = Field(..., description="股票代码")
    name: Optional[str] = Field(None, description="股票名称")
    current_price: Optional[float] = Field(None, description="当前价格")
    change_percent: Optional[float] = Field(None, description="涨跌幅")
    indicators: List[TechnicalIndicator] = Field(default_factory=list, description="技术指标列表")
    kline_data: Optional[List[KlineData]] = Field(None, description="K线数据")
    summary: Optional[str] = Field(None, description="技术分析总结")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class FundamentalMetric(BaseModel):
    name: str = Field(..., description="指标名称")
    value: Optional[float] = Field(None, description="数值")
    unit: Optional[str] = Field(None, description="单位")
    rank: Optional[str] = Field(None, description="评级: excellent/good/average/poor")
    description: Optional[str] = Field(None, description="说明")


class FundamentalAnalysisResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    symbol: str = Field(..., description="股票代码")
    name: Optional[str] = Field(None, description="股票名称")
    industry: Optional[str] = Field(None, description="所属行业")
    market_cap: Optional[float] = Field(None, description="市值")
    pe_ratio: Optional[float] = Field(None, description="市盈率")
    pb_ratio: Optional[float] = Field(None, description="市净率")
    roe: Optional[float] = Field(None, description="净资产收益率")
    debt_ratio: Optional[float] = Field(None, description="资产负债率")
    dividend_rate: Optional[float] = Field(None, description="股息率")
    metrics: List[FundamentalMetric] = Field(default_factory=list, description="基本面指标列表")
    summary: Optional[str] = Field(None, description="基本面分析总结")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class AnalysisScore(BaseModel):
    category: str = Field(..., description="评分类别")
    score: float = Field(..., description="得分 0-100")
    weight: float = Field(default=1.0, description="权重")


class ComprehensiveAnalysisResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    symbol: str = Field(..., description="股票代码")
    name: Optional[str] = Field(None, description="股票名称")
    overall_score: float = Field(..., description="综合得分 0-100")
    overall_rating: str = Field(..., description="综合评级: 强烈推荐/推荐/持有/观望/回避")
    scores: List[AnalysisScore] = Field(default_factory=list, description="各维度评分")
    technical_analysis: Optional[TechnicalAnalysisResponse] = Field(None, description="技术分析")
    fundamental_analysis: Optional[FundamentalAnalysisResponse] = Field(None, description="基本面分析")
    risks: List[str] = Field(default_factory=list, description="风险提示")
    opportunities: List[str] = Field(default_factory=list, description="投资机会")
    recommendations: List[str] = Field(default_factory=list, description="操作建议")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class AIAnalysisRequest(BaseModel):
    symbol: str = Field(..., description="股票代码")
    days_ago: int = Field(default=60, description="分析天数", ge=30, le=365)


class AIAnalysisResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    symbol: str = Field(..., description="股票代码")
    name: Optional[str] = Field(None, description="股票名称")
    ai_report: str = Field(..., description="AI生成的分析报告")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class BatchAIAnalysisRequest(BaseModel):
    symbols: List[str] = Field(..., description="股票代码列表")
    days_ago: int = Field(default=60, description="分析天数", ge=30, le=365)


class BatchAIAnalysisResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    total: int = Field(..., description="总请求数")
    success_count: int = Field(..., description="成功数")
    failed_count: int = Field(..., description="失败数")
    results: List[AIAnalysisResponse] = Field(default_factory=list, description="成功的分析结果")
    failed_symbols: List[str] = Field(default_factory=list, description="失败的股票代码")


class AnalysisHistoryItem(BaseModel):
    id: str = Field(..., description="记录ID")
    symbol: str = Field(..., description="股票代码")
    name: Optional[str] = Field(None, description="股票名称")
    created_at: str = Field(..., description="创建时间")
    ai_report: Optional[str] = Field(None, description="AI分析报告详情(仅在获取详情时返回)")


class AnalysisHistoryListResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    total: int = Field(..., description="总数")
    items: List[AnalysisHistoryItem] = Field(default_factory=list, description="历史记录列表")


class AnalysisHistoryDetailResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    data: Optional[AnalysisHistoryItem] = Field(None, description="记录详情")
