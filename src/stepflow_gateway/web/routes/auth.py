"""
认证配置路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from ..models.auth import (
    AuthConfigRequest, AuthConfigResponse, SessionRequest,
    SessionResponse, SessionValidateRequest
)
from ..models.common import SuccessResponse, ErrorResponse
from ..dependencies import get_gateway
from stepflow_gateway.core.gateway import StepFlowGateway

router = APIRouter(prefix="/auth", tags=["认证配置"])


@router.post("/configs", response_model=SuccessResponse)
async def create_auth_config(
    request: AuthConfigRequest,
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """创建认证配置"""
    try:
        auth_config_id = gateway.add_auth_config(
            api_document_id=request.api_document_id,
            auth_type=request.auth_type,
            auth_config=request.auth_config,
            is_required=request.is_required,
            is_global=request.is_global,
            priority=request.priority
        )
        return SuccessResponse(
            message="认证配置创建成功",
            data={"config_id": auth_config_id}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/configs", response_model=List[AuthConfigResponse])
async def get_auth_configs(
    gateway: StepFlowGateway = Depends(get_gateway),
    api_document_id: Optional[str] = Query(None),
    auth_type: Optional[str] = Query(None)
):
    """获取认证配置列表"""
    try:
        configs = gateway.list_auth_configs(
            api_document_id=api_document_id,
            auth_type=auth_type
        )
        return [
            AuthConfigResponse(
                id=config["id"],
                api_document_id=config["api_document_id"],
                auth_type=config["auth_type"],
                auth_config=config["auth_config"],
                auth_config_parsed=config.get("auth_config_parsed"),
                is_required=config["is_required"],
                is_global=config["is_global"],
                priority=config["priority"],
                created_at=config["created_at"],
                updated_at=config.get("updated_at")
            )
            for config in configs
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/configs/{config_id}", response_model=AuthConfigResponse)
async def get_auth_config(
    config_id: str,
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """获取认证配置详情"""
    try:
        config = gateway.get_auth_config(config_id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="认证配置不存在"
            )
        return AuthConfigResponse(**config)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/configs/{config_id}", response_model=SuccessResponse)
async def update_auth_config(
    config_id: str,
    request: AuthConfigRequest,
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """更新认证配置"""
    try:
        success = gateway.update_auth_config(
            auth_config_id=config_id,
            auth_type=request.auth_type,
            auth_config=request.auth_config,
            is_required=request.is_required,
            is_global=request.is_global,
            priority=request.priority
        )
        if success:
            return SuccessResponse(message="认证配置更新成功")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="认证配置更新失败"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/configs/{config_id}", response_model=SuccessResponse)
async def delete_auth_config(
    config_id: str,
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """删除认证配置"""
    try:
        success = gateway.delete_auth_config(config_id)
        if success:
            return SuccessResponse(message="认证配置删除成功")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="认证配置删除失败"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: SessionRequest,
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """创建会话"""
    try:
        session_token = gateway.create_session(
            user_id=request.user_id,
            client_info=request.client_info
        )
        return SessionResponse(
            success=True,
            session_token=session_token
        )
    except Exception as e:
        return SessionResponse(
            success=False,
            error=str(e)
        )


@router.post("/sessions/validate", response_model=dict)
async def validate_session(
    request: SessionValidateRequest,
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """验证会话"""
    try:
        session_info = gateway.validate_session(
            session_token=request.session_token
        )
        return session_info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.delete("/sessions/{session_token}", response_model=SuccessResponse)
async def delete_session(
    session_token: str,
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """删除会话"""
    try:
        success = gateway.invalidate_session(session_token)
        if success:
            return SuccessResponse(message="会话删除成功")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="会话删除失败"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) 