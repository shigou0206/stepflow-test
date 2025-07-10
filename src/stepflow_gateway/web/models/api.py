"""
API 相关模型
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class OpenApiRegisterRequest(BaseModel):
    """OpenAPI 注册请求"""
    name: str
    openapi_content: str
    version: Optional[str] = None
    base_url: Optional[str] = None


class AsyncApiRegisterRequest(BaseModel):
    """AsyncAPI 注册请求"""
    name: str
    asyncapi_content: str
    version: Optional[str] = None
    base_url: Optional[str] = None


class ApiRegisterRequest(BaseModel):
    """通用 API 注册请求"""
    name: str
    content: str
    spec_type: str  # "openapi" 或 "asyncapi"
    version: Optional[str] = None
    base_url: Optional[str] = None


class ApiCallRequest(BaseModel):
    """API 调用请求"""
    endpoint_id: str
    request_data: Dict[str, Any]


class ApiResponse(BaseModel):
    """API 响应"""
    id: str
    name: str
    version: Optional[str] = None
    base_url: Optional[str] = None
    status: str
    created_at: str
    updated_at: Optional[str] = None


class EndpointResponse(BaseModel):
    """端点响应"""
    id: str
    path: str
    method: str
    summary: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[List[Dict[str, Any]]] = None
    request_body: Optional[Dict[str, Any]] = None
    responses: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    operation_id: Optional[str] = None
    security: Optional[List[Dict[str, Any]]] = None


class ApiSummaryResponse(BaseModel):
    """API 摘要响应"""
    id: str
    name: str
    version: Optional[str] = None
    base_url: Optional[str] = None
    status: str
    created_at: str
    endpoint_count: int
    auth_config_count: int
    recent_call_count: int


class ApiCompleteResponse(BaseModel):
    """API 完整信息响应"""
    api_document: Dict[str, Any]
    template: Optional[Dict[str, Any]] = None
    endpoints: List[Dict[str, Any]]
    auth_configs: List[Dict[str, Any]]
    recent_calls: List[Dict[str, Any]]
    statistics: Dict[str, Any]
    resource_references: List[Dict[str, Any]] 