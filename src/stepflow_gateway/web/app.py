"""
StepFlow Gateway Web 应用
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import time
import logging

from .routes import (
    users_router, apis_router, endpoints_router, auth_router,
    calls_router, stats_router, resources_router, templates_router
)
from .dependencies import get_gateway, close_gateway

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("🚀 启动 StepFlow Gateway...")
    try:
        gateway = get_gateway()
        logger.info("✅ Gateway 初始化成功")
    except Exception as e:
        logger.error(f"❌ Gateway 初始化失败: {e}")
    
    yield
    
    # 关闭时清理
    logger.info("🛑 关闭 StepFlow Gateway...")
    close_gateway()
    logger.info("✅ Gateway 已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="StepFlow Gateway",
    description="API 网关服务 - 支持 OpenAPI 和 AsyncAPI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求处理时间中间件
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# 异常处理器
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证错误处理"""
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "请求参数验证失败",
            "detail": exc.errors()
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "code": str(exc.status_code)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "服务器内部错误",
            "detail": str(exc) if app.debug else "请联系管理员"
        }
    )


# 注册路由
app.include_router(users_router)
app.include_router(apis_router)
app.include_router(endpoints_router)
app.include_router(auth_router)
app.include_router(calls_router)
app.include_router(stats_router)
app.include_router(resources_router)
app.include_router(templates_router)


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "StepFlow Gateway API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


# 健康检查
@app.get("/health")
async def health_check(request: Request):
    """健康检查"""
    try:
        gateway = get_gateway()
        stats = gateway.get_statistics()
        return {"status": "healthy", "statistics": stats}
    except Exception as e:
        return JSONResponse(status_code=503, content={
            "status": "unhealthy",
            "error": str(e)
        })


# 版本信息
@app.get("/version")
async def get_version():
    """获取版本信息"""
    return {
        "name": "StepFlow Gateway",
        "version": "1.0.0",
        "description": "API 网关服务",
        "features": [
            "OpenAPI 3.0 支持",
            "AsyncAPI 支持",
            "动态 API 注册",
            "认证管理",
            "调用监控",
            "模板系统"
        ]
    } 