"""
通用响应模型
"""

from pydantic import BaseModel
from typing import Optional, Any, Dict, List


class SuccessResponse(BaseModel):
    """成功响应模型"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = False
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


class PaginatedResponse(BaseModel):
    """分页响应模型"""
    success: bool = True
    data: List[Any]
    total: int
    page: int
    size: int
    has_next: bool
    has_prev: bool 