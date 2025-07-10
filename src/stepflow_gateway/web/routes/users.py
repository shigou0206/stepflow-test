"""
用户管理路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from ..models.user import (
    UserRegisterRequest, UserLoginRequest, UserResponse, 
    UserUpdateRequest, LoginResponse
)
from ..models.common import SuccessResponse, ErrorResponse
from ..dependencies import get_gateway
from stepflow_gateway.core.gateway import StepFlowGateway

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.post("/register", response_model=SuccessResponse)
async def register_user(
    request: UserRegisterRequest,
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """注册新用户"""
    try:
        # 使用 gateway 的 create_user 方法
        user_id = gateway.create_user(
            username=request.username,
            email=request.email,
            password=request.password,
            role=request.role,
            permissions=request.permissions
        )
        return SuccessResponse(
            message="用户注册成功",
            data={"user_id": user_id}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=LoginResponse)
async def login_user(
    request: UserLoginRequest,
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """用户登录"""
    try:
        # 使用 gateway 的 authenticate_user 方法
        result = gateway.authenticate_user(
            username=request.username,
            password=request.password
        )
        if result.get("success"):
            return LoginResponse(
                success=True,
                user_id=result["user"]["id"],
                username=result["user"]["username"],
                token=result["session_token"]
            )
        else:
            return LoginResponse(
                success=False,
                error=result.get("error", "登录失败")
            )
    except Exception as e:
        return LoginResponse(
            success=False,
            error=str(e)
        )


@router.get("/", response_model=List[UserResponse])
async def get_users(
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """获取所有用户"""
    try:
        # 使用 gateway 的 list_users 方法
        users = gateway.list_users()
        return [
            UserResponse(
                id=user["id"],
                username=user["username"],
                email=user["email"],
                role=user["role"],
                is_active=user["is_active"],
                created_at=user["created_at"],
                permissions=user.get("permissions")
            )
            for user in users
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """获取指定用户"""
    try:
        # 使用 gateway 的 get_user 方法
        user = gateway.get_user(user_id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        return UserResponse(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            role=user["role"],
            is_active=user["is_active"],
            created_at=user["created_at"],
            permissions=user.get("permissions")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{user_id}", response_model=SuccessResponse)
async def update_user(
    user_id: str,
    request: UserUpdateRequest,
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """更新用户信息"""
    try:
        update_data = {}
        if request.email is not None:
            update_data["email"] = request.email
        if request.role is not None:
            update_data["role"] = request.role
        if request.permissions is not None:
            update_data["permissions"] = request.permissions
        if request.is_active is not None:
            update_data["is_active"] = request.is_active
            
        # 使用 database_manager 的 update_user 方法
        gateway.db_manager.update_user(user_id, update_data)
        return SuccessResponse(message="用户更新成功")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{user_id}", response_model=SuccessResponse)
async def delete_user(
    user_id: str,
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """删除用户"""
    try:
        # 使用 database_manager 的 delete_user 方法
        gateway.db_manager.delete_user(user_id)
        return SuccessResponse(message="用户删除成功")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) 