# StepFlow Gateway

一个动态 API 网关，支持 OpenAPI 文档注册、认证管理、API 调用和监控。

## 🚀 快速开始

### 1. 启动服务

```bash
# 安装依赖
poetry install

# 启动 FastAPI 服务
poetry run uvicorn src.stepflow_gateway.web:app --reload --host 0.0.0.0 --port 8000
```

### 2. 访问 API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 3. 基本使用流程

```python
import requests
import json

base_url = "http://localhost:8000"

# 1. 注册用户
response = requests.post(f"{base_url}/register", json={
    "username": "testuser",
    "email": "test@example.com", 
    "password": "password123"
})

# 2. 用户登录
response = requests.post(f"{base_url}/login", json={
    "username": "testuser",
    "password": "password123"
})

# 3. 注册 OpenAPI 文档
openapi_content = {
    "openapi": "3.0.0",
    "info": {"title": "My API", "version": "1.0.0"},
    "paths": {
        "/users": {
            "get": {"summary": "Get users"}
        }
    }
}

response = requests.post(f"{base_url}/apis/register", json={
    "name": "My API",
    "openapi_content": json.dumps(openapi_content),
    "version": "1.0.0",
    "base_url": "https://api.example.com"
})

# 4. 调用 API
response = requests.post(f"{base_url}/api/call", json={
    "endpoint_id": "endpoint-id-from-step-3",
    "request_data": {
        "method": "GET",
        "url": "https://api.example.com/users",
        "headers": {"Content-Type": "application/json"}
    }
})
```

## 📋 主要功能

### 🔐 认证管理
- **Basic Auth**: 用户名密码认证
- **Bearer Token**: JWT 令牌认证  
- **API Key**: API 密钥认证
- **OAuth2**: OAuth2 授权码流程

### 📄 OpenAPI 支持
- 动态注册 OpenAPI 3.0 文档
- 自动解析端点和参数
- 支持多种认证方式配置

### 📊 监控和日志
- API 调用统计
- 响应时间监控
- 错误日志记录
- 健康检查

### 👥 用户管理
- 用户注册和登录
- 角色权限管理
- 会话管理

## 🛠️ API 接口

### 用户管理
- `POST /register` - 注册用户
- `POST /login` - 用户登录
- `GET /users/{user_id}` - 获取用户信息

### OpenAPI 管理
- `POST /apis/register` - 注册 OpenAPI 文档
- `GET /apis` - 列出所有 API
- `GET /endpoints` - 列出端点

### API 调用
- `POST /api/call` - 通过端点 ID 调用 API
- `POST /api/call/path` - 通过路径调用 API

### 认证配置
- `POST /auth/configs` - 添加认证配置
- `GET /auth/configs` - 列出认证配置

### 监控统计
- `GET /statistics` - 获取统计信息
- `GET /logs/recent` - 获取最近调用日志
- `GET /health` - 健康检查

## 📁 项目结构

```
stepflow-test/
├── src/stepflow_gateway/
│   ├── core/           # 核心配置和网关
│   ├── database/       # 数据库管理
│   ├── auth/          # 认证管理
│   ├── api/           # API 管理
│   └── web.py         # FastAPI 服务
├── database/          # 数据库模式
├── examples/          # 使用示例
├── tests/            # 测试用例
└── docs/             # 文档
```

## 🔧 配置

### 数据库配置
默认使用 SQLite，可通过环境变量配置：

```bash
export DATABASE_PATH=/path/to/database.db
```

### 认证配置
```python
from stepflow_gateway.core.config import GatewayConfig

config = GatewayConfig()
config.auth.token_expire_minutes = 60
config.oauth2.state_expire_minutes = 10
```

## 🧪 运行测试

```bash
# 运行所有测试
poetry run pytest

# 运行集成测试
poetry run pytest tests/test_gateway_integration.py -v
```

## 📖 完整示例

查看 `examples/complete_usage_example.py` 了解完整的使用流程。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## �� 许可证

MIT License 