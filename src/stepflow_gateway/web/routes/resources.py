"""
资源管理路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from ..models.common import SuccessResponse
from ..dependencies import get_gateway
from stepflow_gateway.core.gateway import StepFlowGateway

router = APIRouter(prefix="/resources", tags=["资源管理"])


@router.get("/", response_model=List[dict])
async def get_resources(
    gateway: StepFlowGateway = Depends(get_gateway),
    api_id: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100)
):
    """获取资源列表"""
    try:
        filters = {}
        if api_id:
            filters["api_id"] = api_id
        if resource_type:
            filters["resource_type"] = resource_type
            
        resources = gateway.get_resources(
            filters=filters,
            page=page,
            size=size
        )
        return resources
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{resource_id}", response_model=dict)
async def get_resource(
    resource_id: str,
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """获取资源详情"""
    try:
        resource = gateway.get_resource(resource_id)
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="资源不存在"
            )
        return resource
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{resource_id}/references", response_model=List[dict])
async def get_resource_references(
    resource_id: str,
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """获取资源引用"""
    try:
        references = gateway.get_resource_references(resource_id)
        return references
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/schemas", response_model=List[dict])
async def get_schemas(
    gateway: StepFlowGateway = Depends(get_gateway),
    api_id: Optional[str] = Query(None)
):
    """获取模式定义"""
    try:
        schemas = gateway.get_schemas(api_id=api_id)
        return schemas
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/schemas/{schema_name}", response_model=dict)
async def get_schema(
    schema_name: str,
    gateway: StepFlowGateway = Depends(get_gateway),
    api_id: Optional[str] = Query(None)
):
    """获取指定模式定义"""
    try:
        schema = gateway.get_schema(schema_name, api_id=api_id)
        if not schema:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模式定义不存在"
            )
        return schema
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 