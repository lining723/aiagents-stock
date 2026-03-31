from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date


class LonghubangAnalysisRequest(BaseModel):
    analysis_mode: str = Field(default="指定日期", description="分析模式：指定日期 或 最近N天")
    date: Optional[str] = Field(None, description="指定日期，格式 YYYY-MM-DD")
    days: int = Field(default=1, description="最近天数，analysis_mode为最近N天时使用", ge=1, le=10)


class LonghubangReportInfo(BaseModel):
    report_id: str = Field(..., description="报告ID")
    date: str = Field(..., description="分析日期")
    created_at: datetime = Field(..., description="创建时间")
    stock_count: int = Field(default=0, description="股票数量")
    youzi_count: int = Field(default=0, description="游资数量")


class LonghubangReportDetail(BaseModel):
    report_id: str = Field(..., description="报告ID")
    date: str = Field(..., description="分析日期")
    created_at: datetime = Field(..., description="创建时间")
    data_info: Dict[str, Any] = Field(default_factory=dict, description="数据信息")
    agents_analysis: Dict[str, Any] = Field(default_factory=dict, description="分析师分析")
    final_report: Dict[str, Any] = Field(default_factory=dict, description="最终报告")
    recommended_stocks: List[Dict[str, Any]] = Field(default_factory=list, description="推荐股票")


class LonghubangAnalysisResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    report_id: Optional[str] = Field(None, description="报告ID")
    data_info: Optional[Dict[str, Any]] = Field(None, description="数据信息")
    agents_analysis: Optional[Dict[str, Any]] = Field(None, description="分析师分析")
    final_report: Optional[Dict[str, Any]] = Field(None, description="最终报告")
    recommended_stocks: Optional[List[Dict[str, Any]]] = Field(None, description="推荐股票")


class LonghubangReportListResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    reports: List[LonghubangReportInfo] = Field(default_factory=list, description="报告列表")
    total: int = Field(default=0, description="总数")
