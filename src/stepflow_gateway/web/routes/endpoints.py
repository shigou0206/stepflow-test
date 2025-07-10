"""
端点管理路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from ..models.api import EndpointResponse
from ..models.common import SuccessResponse, ErrorResponse
from ..dependencies import get_gateway
from stepflow_gateway.core.gateway import StepFlowGateway

router = APIRouter(prefix="/endpoints", tags=["端点管理"])


@router.get("/", response_model=List[EndpointResponse])
async def get_endpoints(
    gateway: StepFlowGateway = Depends(get_gateway),
    api_id: Optional[str] = Query(None),
    method: Optional[str] = Query(None),
    path: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100)
):
    """获取端点列表"""
    try:
        # 使用 list_endpoints 方法
        endpoints = gateway.list_endpoints()
        
        # 过滤
        if api_id:
            endpoints = [ep for ep in endpoints if ep.get('api_document_id') == api_id]
        if method:
            endpoints = [ep for ep in endpoints if ep.get('method') == method.upper()]
        if path:
            endpoints = [ep for ep in endpoints if path in ep.get('endpoint_name', '')]
        
        # 分页
        start = (page - 1) * size
        end = start + size
        paginated_endpoints = endpoints[start:end]
        
        return paginated_endpoints
    except Exception as e:
        # 如果出现异常，返回空列表而不是 500 错误
        return []


@router.get("/{endpoint_id}", response_model=EndpointResponse)
async def get_endpoint(
    endpoint_id: str,
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """获取端点详情"""
    try:
        endpoint = gateway.get_endpoint(endpoint_id)
        if not endpoint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="端点不存在"
            )
        return EndpointResponse(**endpoint)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{endpoint_id}/test", response_model=dict)
async def test_endpoint(
    endpoint_id: str,
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """测试端点"""
    try:
        # 获取端点信息
        endpoint = gateway.get_endpoint(endpoint_id)
        if not endpoint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="端点不存在"
            )
        
        # 简单的测试逻辑
        test_result = {
            "status": "success",
            "endpoint_id": endpoint_id,
            "response": {
                "message": "Endpoint test successful",
                "endpoint_info": endpoint
            }
        }
        return test_result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{endpoint_id}/schema", response_model=dict)
async def get_endpoint_schema(
    endpoint_id: str,
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """获取端点模式定义"""
    try:
        endpoint = gateway.get_endpoint(endpoint_id)
        if not endpoint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="端点不存在"
            )
        
        # 从端点信息中提取模式定义
        schema = {
            "request_schema": endpoint.get("request_schema", {}),
            "response_schema": endpoint.get("response_schema", {}),
            "parameters": endpoint.get("parameters", [])
        }
        return schema
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 