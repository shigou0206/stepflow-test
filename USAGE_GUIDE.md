# StepFlow Gateway 使用指南

## 🎯 如何使用 StepFlow Gateway 注册和调用 OpenAPI 规范的接口

### 1. 启动服务

```bash
# 启动 FastAPI 服务
poetry run uvicorn src.stepflow_gateway.web:app --reload --host 0.0.0.0 --port 8000
```

### 2. 注册你的 OpenAPI 文档

假设你有一个 OpenAPI 规范的接口文档，比如：

```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "我的 API",
    "version": "1.0.0",
    "description": "我的业务 API"
  },
  "servers": [
    {
      "url": "https://api.mycompany.com/v1",
      "description": "生产环境"
    }
  ],
  "paths": {
    "/users": {
      "get": {
        "summary": "获取用户列表",
        "operationId": "getUsers",
        "responses": {
          "200": {
            "description": "成功",
            "content": {
              "application/json": {
                "schema": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "id": {"type": "integer"},
                      "name": {"type": "string"},
                      "email": {"type": "string"}
                    }
                  }
                }
              }
            }
          }
        }
      },
      "post": {
        "summary": "创建用户",
        "operationId": "createUser",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "name": {"type": "string"},
                  "email": {"type": "string"}
                }
              }
            }
          }
        },
        "responses": {
          "201": {
            "description": "用户创建成功"
          }
        }
      }
    },
    "/users/{userId}": {
      "get": {
        "summary": "获取单个用户",
        "operationId": "getUser",
        "parameters": [
          {
            "name": "userId",
            "in": "path",
            "required": true,
            "schema": {"type": "integer"}
          }
        ],
        "responses": {
          "200": {
            "description": "成功"
          }
        }
      }
    }
  }
}
```

#### 注册 API 文档

```python
import requests
import json

base_url = "http://localhost:8000"

# 注册 OpenAPI 文档
response = requests.post(f"{base_url}/apis/register", json={
    "name": "我的业务 API",
    "openapi_content": json.dumps(your_openapi_document),  # 你的 OpenAPI 文档
    "version": "1.0.0",
    "base_url": "https://api.mycompany.com/v1"
})

result = response.json()
print(f"注册结果: {result}")

# 获取 document_id 和 endpoints
document_id = result["document_id"]
endpoints = result["endpoints"]
```

### 3. 配置认证（如果需要）

如果你的 API 需要认证，可以配置认证方式：

```python
# 配置 API Key 认证
auth_response = requests.post(f"{base_url}/auth/configs", json={
    "api_document_id": document_id,
    "auth_type": "api_key",
    "auth_config": {
        "key_name": "X-API-Key",
        "key_value": "your-api-key-here"
    },
    "is_required": True
})

# 配置 Bearer Token 认证
auth_response = requests.post(f"{base_url}/auth/configs", json={
    "api_document_id": document_id,
    "auth_type": "bearer",
    "auth_config": {
        "token": "your-bearer-token-here"
    },
    "is_required": True
})
```

### 4. 调用你的 API

#### 方式一：通过端点 ID 调用

```python
# 获取端点列表
endpoints_response = requests.get(f"{base_url}/endpoints", params={
    "api_document_id": document_id
})
endpoints_list = endpoints_response.json()["endpoints"]

# 调用获取用户列表的 API
get_users_endpoint = next(e for e in endpoints_list if e["path"] == "/users" and e["method"] == "GET")

api_call_response = requests.post(f"{base_url}/api/call", json={
    "endpoint_id": get_users_endpoint["id"],
    "request_data": {
        "method": "GET",
        "url": "https://api.mycompany.com/v1/users",
        "headers": {
            "Content-Type": "application/json",
            "X-API-Key": "your-api-key-here"  # 如果配置了认证
        },
        "params": {},
        "body": None
    }
})

result = api_call_response.json()
print(f"API 调用结果: {result}")
```

#### 方式二：通过路径调用

```python
# 直接通过路径调用
path_call_response = requests.post(f"{base_url}/api/call/path", params={
    "path": "/users",
    "method": "GET",
    "api_document_id": document_id
}, json={
    "method": "GET",
    "url": "https://api.mycompany.com/v1/users",
    "headers": {
        "Content-Type": "application/json"
    },
    "params": {},
    "body": None
})

result = path_call_response.json()
print(f"路径调用结果: {result}")
```

### 5. 创建用户（可选）

如果你需要用户管理功能：

```python
# 注册用户
register_response = requests.post(f"{base_url}/register", json={
    "username": "myuser",
    "email": "user@mycompany.com",
    "password": "password123",
    "role": "user"
})

# 用户登录
login_response = requests.post(f"{base_url}/login", json={
    "username": "myuser",
    "password": "password123"
})

login_result = login_response.json()
session_token = login_result["session_token"]
```

### 6. 监控和统计

```python
# 获取统计信息
stats_response = requests.get(f"{base_url}/statistics")
stats = stats_response.json()
print(f"统计信息: {stats}")

# 获取最近的调用日志
logs_response = requests.get(f"{base_url}/logs/recent", params={"limit": 10})
logs = logs_response.json()
print(f"最近调用: {logs}")
```

## 🔧 实际使用示例

### 示例 1：调用 GitHub API

```python
# GitHub API 的 OpenAPI 文档（简化版）
github_openapi = {
    "openapi": "3.0.0",
    "info": {"title": "GitHub API", "version": "1.0.0"},
    "servers": [{"url": "https://api.github.com"}],
    "paths": {
        "/user": {
            "get": {
                "summary": "获取当前用户信息",
                "responses": {"200": {"description": "成功"}}
            }
        }
    }
}

# 注册 GitHub API
response = requests.post(f"{base_url}/apis/register", json={
    "name": "GitHub API",
    "openapi_content": json.dumps(github_openapi),
    "version": "1.0.0",
    "base_url": "https://api.github.com"
})

# 调用 GitHub API
api_call_response = requests.post(f"{base_url}/api/call", json={
    "endpoint_id": "endpoint-id-from-registration",
    "request_data": {
        "method": "GET",
        "url": "https://api.github.com/user",
        "headers": {
            "Authorization": "Bearer your-github-token",
            "Accept": "application/vnd.github.v3+json"
        }
    }
})
```

### 示例 2：调用天气 API

```python
# 天气 API 的 OpenAPI 文档
weather_openapi = {
    "openapi": "3.0.0",
    "info": {"title": "Weather API", "version": "1.0.0"},
    "servers": [{"url": "https://api.weatherapi.com/v1"}],
    "paths": {
        "/current.json": {
            "get": {
                "summary": "获取当前天气",
                "parameters": [
                    {
                        "name": "q",
                        "in": "query",
                        "required": true,
                        "schema": {"type": "string"}
                    }
                ],
                "responses": {"200": {"description": "成功"}}
            }
        }
    }
}

# 注册天气 API
response = requests.post(f"{base_url}/apis/register", json={
    "name": "Weather API",
    "openapi_content": json.dumps(weather_openapi),
    "version": "1.0.0",
    "base_url": "https://api.weatherapi.com/v1"
})

# 调用天气 API
api_call_response = requests.post(f"{base_url}/api/call", json={
    "endpoint_id": "endpoint-id-from-registration",
    "request_data": {
        "method": "GET",
        "url": "https://api.weatherapi.com/v1/current.json",
        "headers": {"Content-Type": "application/json"},
        "params": {"q": "Beijing", "key": "your-api-key"}
    }
})
```

## 📊 查看 API 文档

访问 http://localhost:8000/docs 查看完整的 Swagger 文档，可以：

- 查看所有可用的 API 接口
- 直接在浏览器中测试 API
- 查看请求和响应的格式
- 下载 OpenAPI 规范

## 🎯 总结

使用 StepFlow Gateway 的步骤：

1. **启动服务** - 运行 FastAPI 服务
2. **注册 OpenAPI 文档** - 上传你的 API 规范
3. **配置认证** - 设置认证方式（如需要）
4. **调用 API** - 通过网关调用你的 API
5. **监控使用** - 查看调用统计和日志

这样你就可以通过 StepFlow Gateway 统一管理和调用你的所有 API 了！ 