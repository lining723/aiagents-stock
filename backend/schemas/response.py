from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Optional, Any, List

T = TypeVar('T')


class ResponseBase(BaseModel):
    code: int = Field(..., description="响应状态码，200表示成功")
    message: str = Field(..., description="响应消息")


class SuccessResponse(ResponseBase, Generic[T]):
    data: Optional[T] = Field(None, description="响应数据")
    
    @classmethod
    def success(cls, data: T = None, message: str = "操作成功") -> "SuccessResponse[T]":
        return cls(code=200, message=message, data=data)


class ErrorResponse(ResponseBase):
    errors: Optional[List[Any]] = Field(None, description="错误详情列表")
    
    @classmethod
    def error(cls, code: int = 400, message: str = "操作失败", errors: Optional[List[Any]] = None) -> "ErrorResponse":
        return cls(code=code, message=message, errors=errors)


class HealthCheckResponse(BaseModel):
    status: str
    service: str
    version: str
