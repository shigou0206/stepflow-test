"""
Web 模型测试
"""

import pytest
from pydantic import ValidationError
from src.stepflow_gateway.web.models.user import (
    UserRegisterRequest, UserLoginRequest, UserResponse, LoginResponse
)
from src.stepflow_gateway.web.models.api import (
    OpenApiRegisterRequest, ApiCallRequest, ApiResponse
)
from src.stepflow_gateway.web.models.auth import (
    AuthConfigRequest, AuthConfigResponse
)
from src.stepflow_gateway.web.models.common import (
    SuccessResponse, ErrorResponse, PaginatedResponse
)


class TestUserModels:
    """用户模型测试"""
    
    def test_user_register_request_valid(self):
        """测试有效的用户注册请求"""
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "role": "user"
        }
        request = UserRegisterRequest(**data)
        assert request.username == "testuser"
        assert request.email == "test@example.com"
        assert request.password == "password123"
        assert request.role == "user"
    
    def test_user_register_request_invalid_email(self):
        """测试无效邮箱"""
        data = {
            "username": "testuser",
            "email": "invalid-email",
            "password": "password123"
        }
        with pytest.raises(ValidationError):
            UserRegisterRequest(**data)
    
    def test_user_login_request(self):
        """测试用户登录请求"""
        data = {
            "username": "testuser",
            "password": "password123"
        }
        request = UserLoginRequest(**data)
        assert request.username == "testuser"
        assert request.password == "password123"
    
    def test_user_response(self):
        """测试用户响应"""
        data = {
            "id": "user123",
            "username": "testuser",
            "email": "test@example.com",
            "role": "user",
            "is_active": True,
            "created_at": "2024-01-01T00:00:00Z"
        }
        response = UserResponse(**data)
        assert response.id == "user123"
        assert response.username == "testuser"
        assert response.is_active is True
    
    def test_login_response_success(self):
        """测试登录成功响应"""
        data = {
            "success": True,
            "user_id": "user123",
            "username": "testuser",
            "token": "jwt_token_here"
        }
        response = LoginResponse(**data)
        assert response.success is True
        assert response.user_id == "user123"
        assert response.token == "jwt_token_here"
    
    def test_login_response_error(self):
        """测试登录错误响应"""
        data = {
            "success": False,
            "error": "Invalid credentials"
        }
        response = LoginResponse(**data)
        assert response.success is False
        assert response.error == "Invalid credentials"


class TestApiModels:
    """API 模型测试"""
    
    def test_openapi_register_request(self):
        """测试 OpenAPI 注册请求"""
        data = {
            "name": "Petstore API",
            "openapi_content": '{"openapi": "3.0.0"}',
            "version": "1.0.0",
            "base_url": "https://petstore.swagger.io"
        }
        request = OpenApiRegisterRequest(**data)
        assert request.name == "Petstore API"
        assert request.openapi_content == '{"openapi": "3.0.0"}'
        assert request.version == "1.0.0"
        assert request.base_url == "https://petstore.swagger.io"
    
    def test_api_call_request(self):
        """测试 API 调用请求"""
        data = {
            "endpoint_id": "endpoint123",
            "request_data": {
                "params": {"id": 1},
                "headers": {"Content-Type": "application/json"}
            }
        }
        request = ApiCallRequest(**data)
        assert request.endpoint_id == "endpoint123"
        assert request.request_data["params"]["id"] == 1
    
    def test_api_response(self):
        """测试 API 响应"""
        data = {
            "id": "api123",
            "name": "Test API",
            "version": "1.0.0",
            "base_url": "https://api.example.com",
            "status": "active",
            "created_at": "2024-01-01T00:00:00Z"
        }
        response = ApiResponse(**data)
        assert response.id == "api123"
        assert response.name == "Test API"
        assert response.status == "active"


class TestAuthModels:
    """认证模型测试"""
    
    def test_auth_config_request(self):
        """测试认证配置请求"""
        data = {
            "api_document_id": "api123",
            "auth_type": "bearer",
            "auth_config": {
                "token": "your_token_here"
            },
            "is_required": True,
            "is_global": False,
            "priority": 1
        }
        request = AuthConfigRequest(**data)
        assert request.api_document_id == "api123"
        assert request.auth_type == "bearer"
        assert request.auth_config["token"] == "your_token_here"
        assert request.is_required is True
    
    def test_auth_config_response(self):
        """测试认证配置响应"""
        data = {
            "id": "config123",
            "api_document_id": "api123",
            "auth_type": "bearer",
            "auth_config": {"token": "your_token_here"},
            "auth_config_parsed": {"type": "bearer"},
            "is_required": True,
            "is_global": False,
            "priority": 1,
            "created_at": "2024-01-01T00:00:00Z"
        }
        response = AuthConfigResponse(**data)
        assert response.id == "config123"
        assert response.auth_type == "bearer"
        assert response.is_required is True


class TestCommonModels:
    """通用模型测试"""
    
    def test_success_response(self):
        """测试成功响应"""
        data = {
            "success": True,
            "message": "操作成功",
            "data": {"id": "123"}
        }
        response = SuccessResponse(**data)
        assert response.success is True
        assert response.message == "操作成功"
        assert response.data["id"] == "123"
    
    def test_error_response(self):
        """测试错误响应"""
        data = {
            "success": False,
            "error": "操作失败",
            "detail": "详细错误信息",
            "code": "ERROR_001"
        }
        response = ErrorResponse(**data)
        assert response.success is False
        assert response.error == "操作失败"
        assert response.detail == "详细错误信息"
        assert response.code == "ERROR_001"
    
    def test_paginated_response(self):
        """测试分页响应"""
        data = {
            "success": True,
            "data": [{"id": "1"}, {"id": "2"}],
            "total": 2,
            "page": 1,
            "size": 10,
            "has_next": False,
            "has_prev": False
        }
        response = PaginatedResponse(**data)
        assert response.success is True
        assert len(response.data) == 2
        assert response.total == 2
        assert response.has_next is False 