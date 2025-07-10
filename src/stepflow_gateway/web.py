from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uvicorn
import json

from .core.config import GatewayConfig
from .core.gateway import StepFlowGateway

# 初始化 FastAPI 应用
app = FastAPI(title="StepFlow Gateway API", version="1.0.0")

# 允许所有 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化 Gateway 实例（全局单例）
gateway = StepFlowGateway()

# 启动时初始化数据库
try:
    gateway.initialize()
    print("✅ StepFlow Gateway 初始化成功")
except Exception as e:
    print(f"❌ StepFlow Gateway 初始化失败: {e}")
    # 继续运行，但某些功能可能不可用

# Pydantic 请求模型
class UserRegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    role: Optional[str] = "user"
    permissions: Optional[Dict[str, Any]] = None

class UserLoginRequest(BaseModel):
    username: str
    password: str

class ApiCallRequest(BaseModel):
    endpoint_id: str
    request_data: Dict[str, Any]

class OpenApiRegisterRequest(BaseModel):
    name: str
    openapi_content: str
    version: Optional[str] = None
    base_url: Optional[str] = None

class AuthConfigRequest(BaseModel):
    api_document_id: str
    auth_type: str  # basic, bearer, api_key, oauth2
    auth_config: Dict[str, Any]
    is_required: bool = True
    is_global: bool = False
    priority: int = 0

# 基础健康检查
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "StepFlow Gateway"}

# 用户管理
@app.post("/register")
def register_user(req: UserRegisterRequest):
    try:
        user_id = gateway.create_user(
            username=req.username,
            email=req.email,
            password=req.password,
            role=req.role,
            permissions=req.permissions
        )
        return {"success": True, "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/login")
def login_user(req: UserLoginRequest):
    result = gateway.authenticate_user(req.username, req.password)
    if not result.get("success"):
        raise HTTPException(status_code=401, detail=result.get("error", "Login failed"))
    return result

@app.get("/users/{user_id}")
def get_user(user_id: str):
    user = gateway.get_user(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/users")
def list_users(role: Optional[str] = None, is_active: bool = True):
    users = gateway.list_users(role=role, is_active=is_active)
    return {"users": users}

# OpenAPI 文档管理
@app.post("/apis/register")
def register_api(req: OpenApiRegisterRequest):
    try:
        result = gateway.register_api(
            name=req.name,
            openapi_content=req.openapi_content,
            version=req.version,
            base_url=req.base_url
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/apis")
def list_apis(status: str = 'active'):
    apis = gateway.list_apis(status=status)
    return {"apis": apis}

@app.get("/apis/{api_id}")
def get_api(api_id: str):
    api = gateway.get_api(api_id)
    if not api:
        raise HTTPException(status_code=404, detail="API not found")
    return api

@app.delete("/apis/{api_id}")
def delete_api(api_id: str):
    success = gateway.delete_api(api_id)
    if not success:
        raise HTTPException(status_code=404, detail="API not found")
    return {"success": True}

# 端点管理
@app.get("/endpoints")
def list_endpoints_detailed(api_document_id: str = None):
    """返回详细端点信息，含参数、响应、tags、operationId、security"""
    endpoints = gateway.list_endpoints(api_document_id=api_document_id)
    # 详细结构补充
    api = None
    if api_document_id:
        api = gateway.get_api(api_document_id)
        openapi_content = api.get("openapi_content") or api.get("content")
        if openapi_content:
            try:
                openapi_doc = json.loads(openapi_content)
            except Exception:
                openapi_doc = None
        else:
            openapi_doc = None
    else:
        openapi_doc = None
    detailed = []
    for ep in endpoints:
        detail = dict(ep)
        # 尝试补充参数、响应、tags、operationId、security
        if openapi_doc:
            path_item = openapi_doc.get("paths", {}).get(ep["path"], {})
            method_item = path_item.get(ep["method"].lower(), {})
            detail["parameters"] = method_item.get("parameters", [])
            detail["requestBody"] = method_item.get("requestBody")
            detail["responses"] = method_item.get("responses")
            detail["tags"] = method_item.get("tags", [])
            detail["operationId"] = method_item.get("operationId")
            detail["security"] = method_item.get("security")
        detailed.append(detail)
    return {"success": True, "endpoints": detailed}

@app.get("/endpoints/search")
def search_endpoints(q: str, api_document_id: Optional[str] = None):
    """搜索端点，支持按路径、方法、摘要、描述搜索"""
    try:
        endpoints = gateway.list_endpoints(api_document_id=api_document_id)
        if not q:
            return {"success": True, "endpoints": endpoints}
        
        # 简单搜索实现
        q_lower = q.lower()
        filtered = []
        for ep in endpoints:
            if (q_lower in ep.get("path", "").lower() or
                q_lower in ep.get("method", "").lower() or
                q_lower in ep.get("summary", "").lower() or
                q_lower in ep.get("description", "").lower()):
                filtered.append(ep)
        
        return {"success": True, "endpoints": filtered, "query": q}
    except Exception as e:
        return {"success": True, "endpoints": [], "query": q, "error": str(e)}

@app.get("/endpoints/{endpoint_id}")
def get_endpoint(endpoint_id: str):
    endpoint = gateway.get_endpoint(endpoint_id)
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    return endpoint

# 认证配置管理
@app.post("/auth/configs")
def add_auth_config(req: AuthConfigRequest):
    try:
        auth_config_id = gateway.add_auth_config(
            api_document_id=req.api_document_id,
            auth_type=req.auth_type,
            auth_config=req.auth_config,
            is_required=req.is_required,
            is_global=req.is_global,
            priority=req.priority
        )
        return {"success": True, "auth_config_id": auth_config_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/auth/configs")
def list_auth_configs_detailed(api_document_id: Optional[str] = None, auth_type: Optional[str] = None):
    """返回详细认证配置信息，便于前端渲染认证选择器"""
    configs = gateway.list_auth_configs(api_document_id=api_document_id, auth_type=auth_type)
    detailed_configs = []
    for config in configs:
        detail = dict(config)
        # 解析认证配置JSON
        try:
            auth_config = json.loads(config.get("auth_config", "{}"))
            detail["auth_config_parsed"] = auth_config
        except Exception:
            detail["auth_config_parsed"] = {}
        detailed_configs.append(detail)
    return {"success": True, "auth_configs": detailed_configs}

@app.get("/auth/configs/{auth_config_id}")
def get_auth_config_detailed(auth_config_id: str):
    """获取单个认证配置详情"""
    config = gateway.get_auth_config(auth_config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Auth config not found")
    # 解析认证配置JSON
    try:
        auth_config = json.loads(config.get("auth_config", "{}"))
        config["auth_config_parsed"] = auth_config
    except Exception:
        config["auth_config_parsed"] = {}
    return {"success": True, "auth_config": config}

@app.put("/auth/configs/{auth_config_id}")
def update_auth_config(auth_config_id: str, req: AuthConfigRequest):
    """更新认证配置"""
    try:
        success = gateway.update_auth_config(
            auth_config_id=auth_config_id,
            auth_config=req.auth_config,
            is_required=req.is_required,
            is_global=req.is_global,
            priority=req.priority
        )
        if success:
            return {"success": True}
        else:
            raise HTTPException(status_code=404, detail="Auth config not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/auth/configs/{auth_config_id}")
def delete_auth_config(auth_config_id: str):
    """删除认证配置"""
    success = gateway.delete_auth_config(auth_config_id)
    if not success:
        raise HTTPException(status_code=404, detail="Auth config not found")
    return {"success": True}

# API 调用
@app.post("/api/call")
def call_api(req: ApiCallRequest):
    result = gateway.call_api(req.endpoint_id, req.request_data)
    return result

@app.post("/api/call/path")
async def call_api_by_path(request: Request):
    """通过路径调用 API"""
    try:
        # 从查询参数获取路径信息
        path = request.query_params.get("path")
        method = request.query_params.get("method")
        api_document_id = request.query_params.get("api_document_id")
        
        if not path or not method:
            raise HTTPException(status_code=400, detail="path and method are required")
        
        # 从请求体获取请求数据
        request_data = await request.json()
        
        result = gateway.call_api_by_path(path, method, request_data, api_document_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 监控和统计
@app.get("/statistics")
def get_statistics():
    stats = gateway.get_statistics()
    return {"success": True, **stats}

@app.get("/statistics/endpoints/{endpoint_id}")
def get_endpoint_statistics(endpoint_id: str):
    stats = gateway.get_endpoint_statistics(endpoint_id)
    return {"success": True, **stats}

@app.get("/logs/recent")
def get_recent_calls(limit: int = 10, api_document_id: Optional[str] = None):
    """获取最近的调用日志，支持按API文档过滤"""
    calls = gateway.get_recent_calls(limit)
    if api_document_id:
        # 过滤指定API文档的调用
        filtered_calls = []
        for call in calls:
            endpoint = gateway.get_endpoint(call.get("api_endpoint_id"))
            if endpoint and endpoint.get("api_document_id") == api_document_id:
                filtered_calls.append(call)
        calls = filtered_calls
    return {"success": True, "recent_calls": calls}

@app.get("/logs/errors")
def get_error_logs(limit: int = 10):
    return gateway.get_error_logs(limit)

@app.get("/health/apis/{api_document_id}")
def check_api_health(api_document_id: str):
    return gateway.check_health(api_document_id)

# 会话管理
@app.post("/sessions")
def create_session(user_id: str, client_info: Optional[Dict[str, Any]] = None):
    session_token = gateway.create_session(user_id, client_info)
    return {"success": True, "session_token": session_token}

@app.post("/sessions/validate")
async def validate_session(request: Request):
    """验证会话令牌"""
    try:
        data = await request.json()
        session_token = data.get("session_token")
        if not session_token:
            raise HTTPException(status_code=400, detail="session_token is required")
        
        result = gateway.validate_session(session_token)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/sessions")
def invalidate_session(session_token: str):
    success = gateway.invalidate_session(session_token)
    return {"success": success}

# OAuth2 支持
@app.post("/oauth2/auth-url")
def create_oauth2_auth_url(user_id: str, api_document_id: str):
    result = gateway.create_oauth2_auth_url(user_id, api_document_id)
    return result

@app.post("/oauth2/callback")
def handle_oauth2_callback(auth_state_id: str, callback_code: str, callback_state: str):
    result = gateway.handle_oauth2_callback(auth_state_id, callback_code, callback_state)
    return result

# 资源引用
@app.post("/resources/references")
def create_resource_reference(
    resource_type: str,
    resource_id: str,
    api_endpoint_id: str,
    display_name: Optional[str] = None,
    description: Optional[str] = None,
    reference_config: Optional[Dict[str, Any]] = None
):
    ref_id = gateway.create_resource_reference(
        resource_type, resource_id, api_endpoint_id, display_name, description, reference_config
    )
    return {"success": True, "reference_id": ref_id}

@app.get("/resources/references")
def get_resource_references(resource_type: Optional[str] = None, resource_id: Optional[str] = None):
    refs = gateway.get_resource_references(resource_type, resource_id)
    return {"success": True, "resource_references": refs}

# 前端渲染专用接口
@app.get("/apis/{api_id}/openapi")
def get_openapi_doc(api_id: str):
    """返回注册时的 OpenAPI 原文档（JSON）"""
    api = gateway.get_api(api_id)
    if not api:
        raise HTTPException(status_code=404, detail="API not found")
    # openapi_content 可能在 api_spec_templates 或 api_documents
    # 先查 api_documents，再查 api_spec_templates
    openapi_content = api.get("openapi_content") or api.get("content")
    if not openapi_content:
        # 兼容老数据结构
        from ..database.manager import DatabaseManager
        db = gateway.db_manager
        with db.get_cursor() as cursor:
            cursor.execute("SELECT content FROM api_spec_templates WHERE id = ?", (api.get("template_id"),))
            row = cursor.fetchone()
            if row:
                openapi_content = row[0]
    if not openapi_content:
        raise HTTPException(status_code=404, detail="OpenAPI content not found")
    try:
        return {"success": True, "openapi": json.loads(openapi_content)}
    except Exception:
        return {"success": True, "openapi": openapi_content}

@app.get("/apis/{api_id}/tags")
def get_api_tags(api_id: str):
    """获取API文档的所有tags，用于前端分组展示"""
    try:
        api = gateway.get_api(api_id)
        if not api:
            raise HTTPException(status_code=404, detail="API not found")
        
        openapi_content = api.get("openapi_content") or api.get("content")
        if not openapi_content:
            db = gateway.db_manager
            with db.get_cursor() as cursor:
                cursor.execute("SELECT content FROM api_spec_templates WHERE id = ?", (api.get("template_id"),))
                row = cursor.fetchone()
                if row:
                    openapi_content = row[0]
        
        if openapi_content:
            openapi_doc = json.loads(openapi_content)
            tags = openapi_doc.get("tags", [])
            return {"success": True, "tags": tags}
        else:
            return {"success": True, "tags": []}
    except Exception as e:
        return {"success": True, "tags": []}

@app.get("/apis/{api_id}/summary")
def get_api_summary(api_id: str):
    """获取API文档摘要信息，用于前端列表展示"""
    api = gateway.get_api(api_id)
    if not api:
        raise HTTPException(status_code=404, detail="API not found")
    
    # 获取端点统计
    endpoints = gateway.list_endpoints(api_document_id=api_id)
    endpoint_count = len(endpoints)
    
    # 获取认证配置统计
    auth_configs = gateway.list_auth_configs(api_document_id=api_id)
    auth_count = len(auth_configs)
    
    # 获取最近调用统计
    recent_calls = gateway.get_recent_calls(limit=100)
    api_calls = [call for call in recent_calls if call.get("api_document_id") == api_id]
    call_count = len(api_calls)
    
    summary = {
        "id": api_id,
        "name": api.get("name"),
        "version": api.get("version"),
        "base_url": api.get("base_url"),
        "status": api.get("status"),
        "created_at": api.get("created_at"),
        "endpoint_count": endpoint_count,
        "auth_config_count": auth_count,
        "recent_call_count": call_count
    }
    
    return {"success": True, "summary": summary}

@app.get("/templates")
def list_templates():
    """列出所有 OpenAPI 模板（template），用于前端展示"""
    with gateway.db_manager.get_cursor() as cursor:
        cursor.execute("SELECT id, name, content, status, created_at, updated_at FROM api_spec_templates ORDER BY created_at DESC")
        templates = [dict(row) for row in cursor.fetchall()]
    return {"success": True, "templates": templates}

@app.get("/apis/{api_id}/complete")
def get_api_complete_info(api_id: str):
    """获取 API 文档的完整信息，包括模板、端点、认证配置、统计等"""
    try:
        # 获取 API 文档基本信息
        api = gateway.get_api(api_id)
        if not api:
            raise HTTPException(status_code=404, detail="API not found")
        
        # 获取模板信息
        template_info = None
        if api.get("template_id"):
            with gateway.db_manager.get_cursor() as cursor:
                cursor.execute("SELECT id, name, content, status, created_at, updated_at FROM api_spec_templates WHERE id = ?", (api["template_id"],))
                row = cursor.fetchone()
                if row:
                    template_info = dict(row)
        
        # 获取端点信息
        endpoints = gateway.list_endpoints(api_document_id=api_id)
        
        # 获取认证配置
        auth_configs = gateway.list_auth_configs(api_document_id=api_id)
        
        # 获取最近调用日志
        recent_calls = gateway.get_recent_calls(limit=10)
        api_calls = [call for call in recent_calls if call.get("api_document_id") == api_id]
        
        # 获取统计信息
        stats = gateway.get_statistics()
        
        # 获取资源引用
        resource_refs = gateway.get_resource_references()
        api_refs = [ref for ref in resource_refs if ref.get("api_endpoint_id") in [ep.get("id") for ep in endpoints]]
        
        # 构建完整信息
        complete_info = {
            "api_document": api,
            "template": template_info,
            "endpoints": endpoints,
            "auth_configs": auth_configs,
            "recent_calls": api_calls,
            "statistics": {
                "total_endpoints": len(endpoints),
                "total_auth_configs": len(auth_configs),
                "total_calls": len(api_calls),
                "resource_references": len(api_refs)
            },
            "resource_references": api_refs
        }
        
        return {"success": True, "complete_info": complete_info}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取API完整信息失败: {str(e)}")

@app.get("/templates/{template_id}/complete")
def get_template_complete_info(template_id: str):
    """通过模板 ID 获取该模板关联的所有 API 文档完整信息"""
    try:
        # 获取模板信息
        with gateway.db_manager.get_cursor() as cursor:
            cursor.execute("SELECT id, name, content, status, created_at, updated_at FROM api_spec_templates WHERE id = ?", (template_id,))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Template not found")
            template_info = dict(row)
        
        # 获取该模板关联的所有 API 文档
        with gateway.db_manager.get_cursor() as cursor:
            cursor.execute("SELECT id, name, version, base_url, status, created_at, updated_at FROM api_documents WHERE template_id = ?", (template_id,))
            api_documents = [dict(row) for row in cursor.fetchall()]
        
        # 获取每个 API 文档的详细信息
        complete_apis = []
        for api_doc in api_documents:
            api_id = api_doc["id"]
            
            # 获取端点信息
            endpoints = gateway.list_endpoints(api_document_id=api_id)
            
            # 获取认证配置
            auth_configs = gateway.list_auth_configs(api_document_id=api_id)
            
            # 获取最近调用日志
            recent_calls = gateway.get_recent_calls(limit=5)
            api_calls = [call for call in recent_calls if call.get("api_document_id") == api_id]
            
            # 构建单个 API 的完整信息
            api_complete = {
                "api_document": api_doc,
                "endpoints": endpoints,
                "auth_configs": auth_configs,
                "recent_calls": api_calls,
                "statistics": {
                    "total_endpoints": len(endpoints),
                    "total_auth_configs": len(auth_configs),
                    "total_calls": len(api_calls)
                }
            }
            complete_apis.append(api_complete)
        
        # 构建模板完整信息
        complete_info = {
            "template": template_info,
            "api_documents": complete_apis,
            "statistics": {
                "total_api_documents": len(api_documents),
                "total_endpoints": sum(len(api["endpoints"]) for api in complete_apis),
                "total_auth_configs": sum(len(api["auth_configs"]) for api in complete_apis)
            }
        }
        
        return {"success": True, "complete_info": complete_info}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模板完整信息失败: {str(e)}")

@app.on_event("shutdown")
def shutdown_event():
    gateway.close()

if __name__ == "__main__":
    uvicorn.run("stepflow_gateway.web:app", host="0.0.0.0", port=8000, reload=True) 