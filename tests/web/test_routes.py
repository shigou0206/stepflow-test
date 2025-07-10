"""
Web 路由测试
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from src.stepflow_gateway.web.app import app
from stepflow_gateway.core.gateway import StepFlowGateway

client = TestClient(app)


class TestRootEndpoints:
    """根端点测试"""
    
    def test_root(self):
        """测试根路径"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "StepFlow Gateway API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
    
    def test_health_check(self):
        """测试健康检查"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.get_statistics.return_value = {"total_apis": 5, "total_calls": 100}
            mock_gateway.get_recent_calls.return_value = [{"id": "call1", "status": "success"}]
            mock_gateway.get_error_logs.return_value = [{"id": "error1", "message": "test error"}]
            mock_gateway.list_apis.return_value = [{"id": "api1", "name": "Test API"}]
            mock_get_gateway.return_value = mock_gateway
            
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "statistics" in data


class TestUserRoutes:
    """用户路由测试"""
    
    def test_register_user_success(self):
        """测试用户注册成功"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.create_user.return_value = "user123"
            mock_get_gateway.return_value = mock_gateway
            
            response = client.post("/users/register", json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123"
            })
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "用户注册成功"
            assert data["data"]["user_id"] == "user123"
    
    def test_register_user_exception(self):
        """测试用户注册异常"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.create_user.side_effect = Exception("Registration failed")
            mock_get_gateway.return_value = mock_gateway
            
            response = client.post("/users/register", json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123"
            })
            assert response.status_code == 400
            data = response.json()
            assert "Registration failed" in data["detail"]
    
    def test_login_user_success(self):
        """测试用户登录成功"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.login_user.return_value = "user123"
            mock_get_gateway.return_value = mock_gateway
            
            response = client.post("/users/login", json={
                "username": "testuser",
                "password": "password123"
            })
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "登录成功"
            assert data["data"]["user_id"] == "user123"
    
    def test_login_user_failure(self):
        """测试用户登录失败"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.login_user.side_effect = Exception("Invalid password")
            mock_get_gateway.return_value = mock_gateway
            
            response = client.post("/users/login", json={
                "username": "testuser",
                "password": "wrongpassword"
            })
            assert response.status_code == 400
            data = response.json()
            assert "Invalid password" in data["detail"]
    
    def test_get_users_success(self):
        """测试获取用户列表成功"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.database_manager.list_users.return_value = [
                {"id": "user1", "username": "user1", "email": "user1@example.com"},
                {"id": "user2", "username": "user2", "email": "user2@example.com"}
            ]
            mock_get_gateway.return_value = mock_gateway
            
            response = client.get("/users")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["username"] == "user1"
    
    def test_get_user_success(self):
        """测试获取用户详情成功"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.get_user.return_value = {
                "id": "user123",
                "username": "testuser",
                "email": "test@example.com"
            }
            mock_get_gateway.return_value = mock_gateway
            
            response = client.get("/users/user123")
            assert response.status_code == 200
            data = response.json()
            assert data["username"] == "testuser"
    
    def test_get_user_not_found(self):
        """测试获取用户详情失败"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.get_user.return_value = None
            mock_get_gateway.return_value = mock_gateway
            
            response = client.get("/users/nonexistent")
            assert response.status_code == 404
            data = response.json()
            assert "用户不存在" in data["detail"]


class TestApiRoutes:
    """API 路由测试"""
    
    def test_register_api_success(self):
        """测试 API 注册成功"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.register_api.return_value = "api123"
            mock_get_gateway.return_value = mock_gateway
            
            response = client.post("/apis/register", json={
                "name": "Test API",
                "openapi_content": "openapi: 3.0.0\ninfo:\n  title: Test API"
            })
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "API 注册成功"
            assert data["data"]["api_id"] == "api123"
    
    def test_register_api_exception(self):
        """测试 API 注册异常"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.register_api.side_effect = Exception("Registration failed")
            mock_get_gateway.return_value = mock_gateway
            
            response = client.post("/apis/register", json={
                "name": "Test API",
                "openapi_content": "invalid content"
            })
            assert response.status_code == 400
            data = response.json()
            assert "Registration failed" in data["detail"]
    
    def test_get_apis(self):
        """测试获取 API 列表"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.list_apis.return_value = [
                {"id": "api1", "name": "API 1", "version": "1.0.0"},
                {"id": "api2", "name": "API 2", "version": "2.0.0"}
            ]
            mock_get_gateway.return_value = mock_gateway
            
            response = client.get("/apis")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["name"] == "API 1"
    
    def test_get_api_success(self):
        """测试获取 API 详情成功"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.get_api.return_value = {
                "id": "api123",
                "name": "Test API",
                "version": "1.0.0"
            }
            mock_get_gateway.return_value = mock_gateway
            
            response = client.get("/apis/api123")
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Test API"
    
    def test_get_api_not_found(self):
        """测试获取 API 详情失败"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.get_api.return_value = None
            mock_get_gateway.return_value = mock_gateway
            
            response = client.get("/apis/nonexistent")
            assert response.status_code == 404
            data = response.json()
            assert "API 不存在" in data["detail"]
    
    def test_update_api_success(self):
        """测试更新 API 成功"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.update_api.return_value = True
            mock_get_gateway.return_value = mock_gateway
            
            response = client.put("/apis/api123", json={
                "name": "Updated API",
                "openapi_content": "openapi: 3.0.0\ninfo:\n  title: Updated API"
            })
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "API 更新成功"
    
    def test_delete_api_success(self):
        """测试删除 API 成功"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.delete_api.return_value = True
            mock_get_gateway.return_value = mock_gateway
            
            response = client.delete("/apis/api123")
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "API 删除成功"


class TestCallRoutes:
    """调用路由测试"""
    
    def test_execute_api_call_success(self):
        """测试 API 调用成功"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.call_api.return_value = {"result": "success"}
            mock_get_gateway.return_value = mock_gateway
            
            response = client.post("/calls/execute", json={
                "endpoint_id": "endpoint123",
                "request_data": {"param1": "value1"}
            })
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "API 调用成功"
            assert data["data"]["result"] == "success"
    
    def test_execute_api_call_exception(self):
        """测试 API 调用异常"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.call_api.side_effect = Exception("Call failed")
            mock_get_gateway.return_value = mock_gateway
            
            response = client.post("/calls/execute", json={
                "endpoint_id": "endpoint123",
                "request_data": {"param1": "value1"}
            })
            assert response.status_code == 400
            data = response.json()
            assert "Call failed" in data["detail"]
    
    def test_get_call_history(self):
        """测试获取调用历史"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.get_recent_calls.return_value = [
                {"id": "call1", "endpoint_id": "endpoint1", "status": "success"},
                {"id": "call2", "endpoint_id": "endpoint2", "status": "error"}
            ]
            mock_get_gateway.return_value = mock_gateway
            
            response = client.get("/calls/history")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["id"] == "call1"
    
    def test_get_call_detail_success(self):
        """测试获取调用详情成功"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.get_recent_calls.return_value = [
                {"id": "call123", "endpoint_id": "endpoint1", "status": "success"}
            ]
            mock_get_gateway.return_value = mock_gateway
            
            response = client.get("/calls/history/call123")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "call123"
    
    def test_get_call_detail_not_found(self):
        """测试获取调用详情失败"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.get_recent_calls.return_value = []
            mock_get_gateway.return_value = mock_gateway
            
            response = client.get("/calls/history/nonexistent")
            assert response.status_code == 404
            data = response.json()
            assert "调用记录不存在" in data["detail"]


class TestAuthRoutes:
    """认证路由测试"""
    
    def test_create_auth_config_success(self):
        """测试创建认证配置成功"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.add_auth_config.return_value = "config123"
            mock_get_gateway.return_value = mock_gateway
            
            response = client.post("/auth/configs", json={
                "api_document_id": "api123",
                "auth_type": "bearer",
                "auth_config": {"token": "your_token"}
            })
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "认证配置创建成功"
            assert data["data"]["config_id"] == "config123"
    
    def test_create_auth_config_exception(self):
        """测试创建认证配置异常"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.add_auth_config.side_effect = Exception("Config creation failed")
            mock_get_gateway.return_value = mock_gateway
            
            response = client.post("/auth/configs", json={
                "api_document_id": "api123",
                "auth_type": "bearer",
                "auth_config": {"token": "your_token"}
            })
            assert response.status_code == 400
            data = response.json()
            assert "Config creation failed" in data["detail"]
    
    def test_get_auth_configs(self):
        """测试获取认证配置列表"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.list_auth_configs.return_value = [
                {"id": "config1", "auth_type": "bearer", "api_document_id": "api1"},
                {"id": "config2", "auth_type": "api_key", "api_document_id": "api2"}
            ]
            mock_get_gateway.return_value = mock_gateway
            
            response = client.get("/auth/configs")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["auth_type"] == "bearer"
    
    def test_get_auth_config_success(self):
        """测试获取认证配置详情成功"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.get_auth_config.return_value = {
                "id": "config123",
                "auth_type": "bearer",
                "api_document_id": "api123"
            }
            mock_get_gateway.return_value = mock_gateway
            
            response = client.get("/auth/configs/config123")
            assert response.status_code == 200
            data = response.json()
            assert data["auth_type"] == "bearer"
    
    def test_get_auth_config_not_found(self):
        """测试获取认证配置详情失败"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.get_auth_config.return_value = None
            mock_get_gateway.return_value = mock_gateway
            
            response = client.get("/auth/configs/nonexistent")
            assert response.status_code == 404
            data = response.json()
            assert "认证配置不存在" in data["detail"]
    
    def test_create_session_success(self):
        """测试创建会话成功"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.create_session.return_value = "session_token_123"
            mock_get_gateway.return_value = mock_gateway
            
            response = client.post("/auth/sessions", json={
                "user_id": "user123",
                "client_info": {"ip": "127.0.0.1"}
            })
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["session_token"] == "session_token_123"
    
    def test_validate_session_success(self):
        """测试验证会话成功"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.validate_session.return_value = {
                "valid": True,
                "user_id": "user123",
                "expires_at": "2025-12-31T23:59:59"
            }
            mock_get_gateway.return_value = mock_gateway
            
            response = client.post("/auth/sessions/validate", json={
                "session_token": "valid_token"
            })
            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True
            assert data["user_id"] == "user123"


class TestEndpointRoutes:
    """端点路由测试"""
    
    def test_get_endpoints_success(self):
        """测试获取端点列表成功"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.list_endpoints.return_value = [
                {"id": "endpoint1", "path": "/api/v1/users", "method": "GET"},
                {"id": "endpoint2", "path": "/api/v1/users", "method": "POST"}
            ]
            mock_get_gateway.return_value = mock_gateway
            
            response = client.get("/endpoints")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["path"] == "/api/v1/users"
    
    def test_get_endpoint_success(self):
        """测试获取端点详情成功"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.get_endpoint.return_value = {
                "id": "endpoint123",
                "path": "/api/v1/users",
                "method": "GET"
            }
            mock_get_gateway.return_value = mock_gateway
            
            response = client.get("/endpoints/endpoint123")
            assert response.status_code == 200
            data = response.json()
            assert data["path"] == "/api/v1/users"
    
    def test_get_endpoint_not_found(self):
        """测试获取端点详情失败"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.get_endpoint.return_value = None
            mock_get_gateway.return_value = mock_gateway
            
            response = client.get("/endpoints/nonexistent")
            assert response.status_code == 404
            data = response.json()
            assert "端点不存在" in data["detail"]
    
    def test_test_endpoint_success(self):
        """测试端点测试成功"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.get_endpoint.return_value = {
                "id": "endpoint123",
                "path": "/api/v1/users",
                "method": "GET"
            }
            mock_get_gateway.return_value = mock_gateway
            
            response = client.get("/endpoints/endpoint123/test")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["endpoint_id"] == "endpoint123"


class TestStatsRoutes:
    """统计路由测试"""
    
    def test_get_overview_stats(self):
        """测试获取概览统计"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.get_statistics.return_value = {"total_apis": 5, "total_calls": 100}
            mock_gateway.get_recent_calls.return_value = [{"id": "call1", "status": "success"}]
            mock_gateway.get_error_logs.return_value = [{"id": "error1", "message": "test error"}]
            mock_gateway.list_apis.return_value = [{"id": "api1", "name": "Test API"}]
            mock_get_gateway.return_value = mock_gateway
            
            response = client.get("/stats/overview")
            assert response.status_code == 200
            data = response.json()
            assert data["total_apis"] == 5
            assert data["total_calls"] == 1
    
    def test_get_api_stats(self):
        """测试获取 API 统计"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.get_api.return_value = {"id": "api123", "name": "Test API"}
            mock_gateway.list_endpoints.return_value = [{"id": "endpoint1"}]
            mock_gateway.get_recent_calls.return_value = [{"api_id": "api123", "status": "success"}]
            mock_get_gateway.return_value = mock_gateway
            
            response = client.get("/stats/api/api123")
            assert response.status_code == 200
            data = response.json()
            assert data["api_id"] == "api123"
            assert data["api_name"] == "Test API"
    
    def test_get_endpoint_stats(self):
        """测试获取端点统计"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.get_endpoint.return_value = {
                "id": "endpoint123",
                "path": "/api/v1/users",
                "method": "GET"
            }
            mock_gateway.get_endpoint_statistics.return_value = {"call_count": 10}
            mock_get_gateway.return_value = mock_gateway
            
            response = client.get("/stats/endpoint/endpoint123")
            assert response.status_code == 200
            data = response.json()
            assert data["endpoint_id"] == "endpoint123"
            assert data["endpoint_path"] == "/api/v1/users"


class TestErrorHandling:
    """错误处理测试"""
    
    def test_http_exception(self):
        """测试 HTTP 异常处理"""
        with patch('src.stepflow_gateway.web.app.get_gateway') as mock_get_gateway:
            mock_gateway = Mock()
            mock_gateway.get_statistics.side_effect = Exception("Database error")
            mock_get_gateway.return_value = mock_gateway
            
            response = client.get("/stats/overview")
            assert response.status_code == 500
            data = response.json()
            assert "Database error" in data["detail"] 