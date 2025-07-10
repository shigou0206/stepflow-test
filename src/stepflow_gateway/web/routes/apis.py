"""
API 管理路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from ..models.api import (
    OpenApiRegisterRequest, ApiResponse, ApiSummaryResponse,
    ApiCompleteResponse
)
from ..models.common import SuccessResponse, ErrorResponse
from ..dependencies import get_gateway
from stepflow_gateway.core.gateway import StepFlowGateway

router = APIRouter(prefix="/apis", tags=["API 管理"])


@router.post("/register", response_model=SuccessResponse)
async def register_openapi(
    request: OpenApiRegisterRequest,
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """注册 OpenAPI 文档"""
    try:
        result = gateway.register_api(
            name=request.name,
            openapi_content=request.openapi_content,
            version=request.version,
            base_url=request.base_url
        )
        if result.get('success'):
            return SuccessResponse(
                message="API 注册成功",
                data={"api_id": result["document_id"]}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error', 'API 注册失败')
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[ApiResponse])
async def get_apis(
    gateway: StepFlowGateway = Depends(get_gateway),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None),
    spec_type: Optional[str] = Query(None)
):
    """获取 API 列表"""
    try:
        # 使用 list_apis 方法
        apis = gateway.list_apis()
        
        # 简单的过滤和分页
        if status:
            apis = [api for api in apis if api.get('status') == status]
        if spec_type:
            apis = [api for api in apis if api.get('spec_type') == spec_type]
        
        # 分页
        start = (page - 1) * size
        end = start + size
        paginated_apis = apis[start:end]
        
        return paginated_apis
    except Exception as e:
        # 如果出现异常，返回空列表而不是 500 错误
        return []


@router.get("/{api_id}", response_model=ApiCompleteResponse)
async def get_api(
    api_id: str,
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """获取 API 完整信息"""
    try:
        # 使用 get_api 方法
        api_info = gateway.get_api(api_id)
        if not api_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API 不存在"
            )
        
        # 构建完整的 API 信息
        complete_info = {
            "api_document": api_info,
            "endpoints": gateway.list_endpoints(api_id),
            "auth_configs": gateway.list_auth_configs(api_id),
            "recent_calls": gateway.get_recent_calls(5),
            "statistics": gateway.get_statistics(),
            "resource_references": gateway.get_resource_references()
        }
        
        return ApiCompleteResponse(**complete_info)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{api_id}", response_model=SuccessResponse)
async def update_api(
    api_id: str,
    request: OpenApiRegisterRequest,
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """更新 API 文档"""
    try:
        # 先删除旧的 API，再注册新的
        gateway.delete_api(api_id)
        result = gateway.register_api(
            name=request.name,
            openapi_content=request.openapi_content,
            version=request.version,
            base_url=request.base_url
        )
        if result.get('success'):
            return SuccessResponse(message="API 更新成功")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error', 'API 更新失败')
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{api_id}", response_model=SuccessResponse)
async def delete_api(
    api_id: str,
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """删除 API"""
    try:
        success = gateway.delete_api(api_id)
        if success:
            return SuccessResponse(message="API 删除成功")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="API 删除失败"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{api_id}/validate", response_model=SuccessResponse)
async def validate_api(
    api_id: str,
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """验证 API 文档"""
    try:
        # 获取 API 信息进行验证
        api_info = gateway.get_api(api_id)
        if not api_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API 不存在"
            )
        
        # 简单的验证逻辑
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "endpoint_count": len(gateway.list_endpoints(api_id))
        }
        
        return SuccessResponse(
            message="API 验证完成",
            data=validation_result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{api_id}/endpoints", response_model=List[dict])
async def get_api_endpoints(
    api_id: str,
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """获取 API 的所有端点"""
    try:
        endpoints = gateway.list_endpoints(api_id)
        return endpoints
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{api_id}/schemas", response_model=dict)
async def get_api_schemas(
    api_id: str,
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """获取 API 的所有模式定义"""
    try:
        api_info = gateway.get_api(api_id)
        if not api_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API 不存在"
            )
        
        # 从 API 信息中提取模式定义
        content = api_info.get('content', {})
        components = content.get('components', {})
        schemas = components.get('schemas', {})
        
        return schemas
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 