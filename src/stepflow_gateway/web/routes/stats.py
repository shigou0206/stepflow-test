"""
统计信息路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from ..models.common import SuccessResponse
from ..dependencies import get_gateway
from stepflow_gateway.core.gateway import StepFlowGateway

router = APIRouter(prefix="/stats", tags=["统计信息"])


@router.get("/overview", response_model=dict)
async def get_overview_stats(
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """获取概览统计"""
    try:
        # 使用现有的统计方法
        stats = gateway.get_statistics()
        recent_calls = gateway.get_recent_calls(10)
        error_logs = gateway.get_error_logs(10)
        
        overview = {
            "total_apis": len(gateway.list_apis()),
            "total_calls": len(recent_calls),
            "error_count": len(error_logs),
            "recent_calls": recent_calls,
            "error_logs": error_logs
        }
        return overview
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/api/{api_id}", response_model=dict)
async def get_api_stats(
    api_id: str,
    gateway: StepFlowGateway = Depends(get_gateway),
    period: Optional[str] = Query("7d", description="统计周期: 1d, 7d, 30d, 90d")
):
    """获取 API 统计"""
    try:
        # 获取 API 信息
        api_info = gateway.get_api(api_id)
        if not api_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API 不存在"
            )
        
        # 获取端点统计
        endpoints = gateway.list_endpoints(api_id)
        recent_calls = gateway.get_recent_calls(50)
        
        # 过滤该 API 的调用
        api_calls = [call for call in recent_calls if call.get('api_id') == api_id]
        
        stats = {
            "api_id": api_id,
            "api_name": api_info.get('name'),
            "endpoint_count": len(endpoints),
            "call_count": len(api_calls),
            "error_count": len([call for call in api_calls if call.get('status') == 'error']),
            "period": period
        }
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/endpoint/{endpoint_id}", response_model=dict)
async def get_endpoint_stats(
    endpoint_id: str,
    gateway: StepFlowGateway = Depends(get_gateway),
    period: Optional[str] = Query("7d", description="统计周期: 1d, 7d, 30d, 90d")
):
    """获取端点统计"""
    try:
        # 获取端点信息
        endpoint = gateway.get_endpoint(endpoint_id)
        if not endpoint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="端点不存在"
            )
        
        # 获取端点统计
        endpoint_stats = gateway.get_endpoint_statistics(endpoint_id)
        
        stats = {
            "endpoint_id": endpoint_id,
            "endpoint_path": endpoint.get('path'),
            "endpoint_method": endpoint.get('method'),
            "statistics": endpoint_stats,
            "period": period
        }
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/user/{user_id}", response_model=dict)
async def get_user_stats(
    user_id: str,
    gateway: StepFlowGateway = Depends(get_gateway),
    period: Optional[str] = Query("7d", description="统计周期: 1d, 7d, 30d, 90d")
):
    """获取用户统计"""
    try:
        # 获取用户信息
        user = gateway.get_user(user_id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 简单的用户统计
        stats = {
            "user_id": user_id,
            "username": user.get('username'),
            "role": user.get('role'),
            "is_active": user.get('is_active'),
            "created_at": user.get('created_at'),
            "period": period
        }
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/performance", response_model=dict)
async def get_performance_stats(
    gateway: StepFlowGateway = Depends(get_gateway),
    period: Optional[str] = Query("1h", description="统计周期: 1h, 6h, 24h")
):
    """获取性能统计"""
    try:
        # 使用现有的统计方法
        stats = gateway.get_statistics()
        recent_calls = gateway.get_recent_calls(100)
        
        # 简单的性能统计
        performance = {
            "total_calls": len(recent_calls),
            "success_rate": len([call for call in recent_calls if call.get('status') == 'success']) / len(recent_calls) if recent_calls else 0,
            "period": period,
            "statistics": stats
        }
        return performance
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/errors", response_model=dict)
async def get_error_stats(
    gateway: StepFlowGateway = Depends(get_gateway),
    period: Optional[str] = Query("24h", description="统计周期: 1h, 6h, 24h, 7d")
):
    """获取错误统计"""
    try:
        # 使用现有的错误日志方法
        error_logs = gateway.get_error_logs(50)
        
        error_stats = {
            "total_errors": len(error_logs),
            "error_logs": error_logs,
            "period": period
        }
        return error_stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 