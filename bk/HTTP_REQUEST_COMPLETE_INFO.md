# StepFlow Gateway 完整 HTTP 请求信息总结

## 概述

StepFlow Gateway 的 `api_call_logs` 表记录了每个 HTTP 请求的**完整信息**，包括请求和响应的所有细节。这为调试、监控、审计和性能分析提供了全面的数据支持。

## 完整的 HTTP 请求信息包含内容

### 1. 基础标识信息
- **日志ID**: 唯一标识每条日志记录
- **API端点ID**: 关联的API端点标识
- **资源引用ID**: 关联的工作流或调度任务标识
- **创建时间**: 请求发生的时间戳

### 2. 请求信息 (Request Information)

#### HTTP 方法
- **字段**: `request_method`
- **内容**: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
- **用途**: 确定请求的操作类型

#### 完整 URL
- **字段**: `request_url`
- **内容**: 完整的请求URL，包括协议、域名、路径、查询参数
- **示例**: `https://api.example.com/v1/users?limit=10&page=1`

#### 请求头 (Headers)
- **字段**: `request_headers` (JSON格式)
- **包含内容**:
  - `Content-Type`: 内容类型
  - `Authorization`: 认证信息 (Bearer token, API key等)
  - `User-Agent`: 客户端标识
  - `Accept`: 接受的响应类型
  - `X-Request-ID`: 请求追踪ID
  - `X-Forwarded-For`: 客户端IP
  - 其他自定义头部

#### 请求体 (Body)
- **字段**: `request_body`
- **内容**: 完整的请求体数据
- **格式**: JSON, XML, 表单数据, 二进制数据等
- **用途**: 记录POST/PUT/PATCH请求的完整数据

#### 请求参数 (Parameters)
- **字段**: `request_params` (JSON格式)
- **包含内容**:
  - **查询参数**: URL中的?参数
  - **路径参数**: URL路径中的变量
  - **表单参数**: 表单提交的数据

### 3. 响应信息 (Response Information)

#### HTTP 状态码
- **字段**: `response_status_code`
- **内容**: 200, 201, 400, 401, 404, 500等
- **用途**: 判断请求是否成功

#### 响应头 (Headers)
- **字段**: `response_headers` (JSON格式)
- **包含内容**:
  - `Content-Type`: 响应内容类型
  - `Content-Length`: 响应体大小
  - `Cache-Control`: 缓存控制
  - `X-Rate-Limit-Remaining`: 限流信息
  - `X-Request-ID`: 请求追踪ID
  - 其他服务器返回的头部

#### 响应体 (Body)
- **字段**: `response_body`
- **内容**: 完整的响应数据
- **格式**: JSON, XML, HTML, 二进制数据等
- **用途**: 记录服务器返回的完整数据

### 4. 性能信息 (Performance Information)

#### 响应时间
- **字段**: `response_time_ms`
- **内容**: 请求从发送到接收响应的总时间（毫秒）
- **用途**: 性能监控和优化

#### 数据大小
- **字段**: `request_size_bytes`, `response_size_bytes`
- **内容**: 请求和响应的数据大小（字节）
- **用途**: 网络流量监控

### 5. 错误信息 (Error Information)

#### 错误消息
- **字段**: `error_message`
- **内容**: 详细的错误描述
- **示例**:
  - "Connection timeout after 30 seconds"
  - "Invalid JSON format in request body"
  - "Authentication failed: Invalid token"

#### 错误类型
- **字段**: `error_type`
- **分类**:
  - `timeout`: 超时错误
  - `validation`: 验证错误
  - `authentication`: 认证错误
  - `authorization`: 授权错误
  - `network`: 网络错误
  - `server_error`: 服务器错误

### 6. 客户端信息 (Client Information)

#### 客户端IP
- **字段**: `client_ip`
- **内容**: 发起请求的客户端IP地址
- **用途**: 访问追踪和安全审计

#### 用户代理
- **字段**: `user_agent`
- **内容**: 客户端软件标识
- **用途**: 客户端识别和统计

## 实际数据示例

### 成功的 GET 请求记录

```json
{
  "id": "54c8fd8f-c56e-4ee1-90f9-22b41cfd7ee4",
  "api_endpoint_id": "endpoint-12345",
  "request_method": "GET",
  "request_url": "https://api.example.com/v1/users?limit=10&page=1",
  "request_headers": {
    "Content-Type": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "User-Agent": "StepFlow-Gateway/1.0.0",
    "Accept": "application/json",
    "X-Request-ID": "req-12345-67890"
  },
  "request_body": "",
  "request_params": {
    "query": {"limit": "10", "page": "1"},
    "path": {}
  },
  "response_status_code": 200,
  "response_headers": {
    "Content-Type": "application/json; charset=utf-8",
    "Content-Length": "1024",
    "Cache-Control": "no-cache",
    "X-Rate-Limit-Remaining": "999",
    "X-Request-ID": "req-12345-67890"
  },
  "response_body": {
    "success": true,
    "data": [
      {"id": "1", "name": "John Doe", "email": "john@example.com"},
      {"id": "2", "name": "Jane Smith", "email": "jane@example.com"}
    ],
    "meta": {"total": 2, "page": 1, "limit": 10}
  },
  "response_time_ms": 150,
  "request_size_bytes": 0,
  "response_size_bytes": 446,
  "client_ip": "192.168.1.100",
  "user_agent": "StepFlow-Gateway/1.0.0",
  "created_at": "2025-07-06T08:56:50.598565"
}
```

### 失败的 POST 请求记录

```json
{
  "id": "fb03c7ed-a0c3-43fc-ab2f-c89d7b1cb377",
  "api_endpoint_id": "endpoint-12345",
  "request_method": "POST",
  "request_url": "https://api.example.com/v1/users",
  "request_headers": {
    "Content-Type": "application/json",
    "Authorization": "Bearer invalid-token",
    "User-Agent": "StepFlow-Gateway/1.0.0"
  },
  "request_body": {
    "name": "Test User",
    "email": "test@example.com",
    "password": "secret123"
  },
  "request_params": {
    "query": {},
    "path": {}
  },
  "response_status_code": 401,
  "response_headers": {
    "Content-Type": "application/json",
    "WWW-Authenticate": "Bearer"
  },
  "response_body": {
    "error": "Unauthorized",
    "message": "Invalid or expired token"
  },
  "response_time_ms": 0,
  "request_size_bytes": 112,
  "response_size_bytes": 89,
  "error_message": "Authentication failed: Invalid token",
  "error_type": "authentication",
  "client_ip": "192.168.1.100",
  "user_agent": "StepFlow-Gateway/1.0.0",
  "created_at": "2025-07-06T08:56:50.600002"
}
```

## 信息完整性保证

### 1. 请求完整性
- ✅ HTTP 方法
- ✅ 完整 URL
- ✅ 所有请求头
- ✅ 请求体内容
- ✅ 查询参数和路径参数
- ✅ 客户端信息

### 2. 响应完整性
- ✅ HTTP 状态码
- ✅ 所有响应头
- ✅ 响应体内容
- ✅ 错误信息（如果有）

### 3. 性能完整性
- ✅ 响应时间
- ✅ 请求大小
- ✅ 响应大小

### 4. 追踪完整性
- ✅ 唯一日志ID
- ✅ 时间戳
- ✅ 关联的API端点
- ✅ 关联的资源引用

## 应用场景

### 1. 调试和故障排除
- 查看完整的请求和响应数据
- 分析错误原因
- 追踪请求流程

### 2. 性能监控
- 监控响应时间
- 识别慢请求
- 分析网络流量

### 3. 安全审计
- 记录所有API调用
- 追踪客户端访问
- 监控异常行为

### 4. 业务分析
- 统计API使用情况
- 分析用户行为
- 优化API设计

### 5. 合规性
- 满足审计要求
- 数据保留策略
- 隐私保护

## 数据安全和隐私

### 敏感信息处理
- 自动脱敏认证信息
- 可配置的敏感字段过滤
- 数据加密存储

### 数据保留
- 可配置的保留期限
- 自动清理过期数据
- 数据归档策略

---

**总结**: StepFlow Gateway 的 HTTP 请求日志记录包含了**完整的 HTTP 请求信息**，从请求的每个细节到响应的完整数据，为系统监控、调试、安全和分析提供了全面的数据支持。 