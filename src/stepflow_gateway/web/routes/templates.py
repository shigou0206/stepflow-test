"""
模板管理路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from ..models.common import SuccessResponse
from ..dependencies import get_gateway
from stepflow_gateway.core.gateway import StepFlowGateway

router = APIRouter(prefix="/templates", tags=["模板管理"])


class TemplateRequest(BaseModel):
    """模板请求"""
    name: str
    description: Optional[str] = None
    template_data: Dict[str, Any]
    template_type: str = "api_call"


@router.post("/", response_model=SuccessResponse)
async def create_template(
    request: TemplateRequest,
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """创建模板"""
    try:
        result = gateway.create_template(
            name=request.name,
            description=request.description,
            template_data=request.template_data,
            template_type=request.template_type
        )
        return SuccessResponse(
            message="模板创建成功",
            data={"template_id": result["template_id"]}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[dict])
async def get_templates(
    gateway: StepFlowGateway = Depends(get_gateway),
    template_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100)
):
    """获取模板列表"""
    try:
        filters = {}
        if template_type:
            filters["template_type"] = template_type
            
        templates = gateway.get_templates(
            filters=filters,
            page=page,
            size=size
        )
        return templates
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{template_id}", response_model=dict)
async def get_template(
    template_id: str,
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """获取模板详情"""
    try:
        template = gateway.get_template(template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模板不存在"
            )
        return template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{template_id}", response_model=SuccessResponse)
async def update_template(
    template_id: str,
    request: TemplateRequest,
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """更新模板"""
    try:
        gateway.update_template(
            template_id=template_id,
            name=request.name,
            description=request.description,
            template_data=request.template_data,
            template_type=request.template_type
        )
        return SuccessResponse(message="模板更新成功")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{template_id}", response_model=SuccessResponse)
async def delete_template(
    template_id: str,
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """删除模板"""
    try:
        gateway.delete_template(template_id)
        return SuccessResponse(message="模板删除成功")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{template_id}/execute", response_model=SuccessResponse)
async def execute_template(
    template_id: str,
    parameters: Dict[str, Any],
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """执行模板"""
    try:
        result = gateway.execute_template(template_id, parameters)
        return SuccessResponse(
            message="模板执行成功",
            data=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) 