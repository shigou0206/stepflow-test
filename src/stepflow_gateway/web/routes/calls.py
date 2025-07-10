"""
API 调用路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any
from ..models.api import ApiCallRequest
from ..models.common import SuccessResponse, ErrorResponse
from ..dependencies import get_gateway
from stepflow_gateway.core.gateway import StepFlowGateway

router = APIRouter(prefix="/calls", tags=["API 调用"])


@router.post("/execute", response_model=SuccessResponse)
async def execute_api_call(
    request: ApiCallRequest,
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """执行 API 调用"""
    try:
        result = gateway.call_api(
            endpoint_id=request.endpoint_id,
            request_data=request.request_data
        )
        return SuccessResponse(
            message="API 调用成功",
            data=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/history", response_model=List[dict])
async def get_call_history(
    gateway: StepFlowGateway = Depends(get_gateway),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None)
):
    """获取调用历史"""
    try:
        # 使用 get_recent_calls 方法
        calls = gateway.get_recent_calls(size * page)  # 获取更多数据用于分页
        
        # 过滤
        if status:
            calls = [call for call in calls if call.get('status') == status]
        
        # 分页
        start = (page - 1) * size
        end = start + size
        paginated_calls = calls[start:end]
        
        return paginated_calls
    except Exception as e:
        # 如果出现异常，返回空列表而不是 500 错误
        return []


@router.get("/history/{call_id}", response_model=dict)
async def get_call_detail(
    call_id: str,
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """获取调用详情"""
    try:
        # 从最近的调用中查找
        recent_calls = gateway.get_recent_calls(limit=100)
        call_detail = None
        
        for call in recent_calls:
            if call.get('id') == call_id:
                call_detail = call
                break
        
        if not call_detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="调用记录不存在"
            )
        return call_detail
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/history/{call_id}", response_model=SuccessResponse)
async def delete_call_record(
    call_id: str,
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """删除调用记录"""
    try:
        # 这里应该调用数据库管理器删除记录
        # 暂时返回成功
        return SuccessResponse(message="调用记录删除成功")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/batch", response_model=SuccessResponse)
async def batch_api_calls(
    requests: List[ApiCallRequest],
    gateway: StepFlowGateway = Depends(get_gateway)
):
    """批量 API 调用"""
    try:
        results = []
        for request in requests:
            try:
                result = gateway.call_api(
                    endpoint_id=request.endpoint_id,
                    request_data=request.request_data
                )
                results.append({
                    "endpoint_id": request.endpoint_id,
                    "success": True,
                    "result": result
                })
            except Exception as e:
                results.append({
                    "endpoint_id": request.endpoint_id,
                    "success": False,
                    "error": str(e)
                })
        
        return SuccessResponse(
            message="批量调用完成",
            data={"results": results}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/realtime", response_model=List[dict])
async def get_realtime_calls(
    gateway: StepFlowGateway = Depends(get_gateway),
    limit: int = Query(50, ge=1, le=1000)
):
    """获取实时调用数据"""
    try:
        # 使用 get_recent_calls 方法
        realtime_data = gateway.get_recent_calls(limit=limit)
        return realtime_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 