# StepFlow Gateway 数据库设计学习指南

## 🎯 学习目标
帮助您逐步理解 StepFlow Gateway 的数据库设计，从简单到复杂，循序渐进。

## 📚 学习路径

### 第一阶段：核心概念理解 (1-2天)

#### 1. 基本需求理解
- **问题**: 为什么需要这个数据库？
- **答案**: 存储 OpenAPI 模板、解析后的 API 文档、端点信息，支持动态 API 调用和资源引用

#### 2. 核心表结构 (重点关注)
```
openapi_templates     ← 存储 OpenAPI 文档模板
api_documents        ← 存储解析后的 API 文档
api_endpoints        ← 存储具体的 API 端点
api_call_logs        ← 存储 HTTP 请求日志
```

### 第二阶段：详细表结构 (2-3天)

#### 1. 模板管理表
```sql
-- 最简单的表：存储 OpenAPI 模板
CREATE TABLE openapi_templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    content TEXT NOT NULL,  -- OpenAPI 文档内容
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

#### 2. API 文档表
```sql
-- 存储解析后的 API 文档
CREATE TABLE api_documents (
    id TEXT PRIMARY KEY,
    template_id TEXT NOT NULL,
    name TEXT NOT NULL,
    version TEXT,
    base_url TEXT,
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

#### 3. API 端点表
```sql
-- 存储具体的 API 端点信息
CREATE TABLE api_endpoints (
    id TEXT PRIMARY KEY,
    api_document_id TEXT NOT NULL,
    path TEXT NOT NULL,
    method TEXT NOT NULL,
    operation_id TEXT,
    summary TEXT,
    description TEXT,
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

#### 4. 请求日志表
```sql
-- 存储 HTTP 请求日志
CREATE TABLE api_call_logs (
    id TEXT PRIMARY KEY,
    api_endpoint_id TEXT NOT NULL,
    request_method TEXT NOT NULL,
    request_url TEXT NOT NULL,
    response_status_code INTEGER,
    response_time_ms INTEGER,
    created_at TEXT NOT NULL
);
```

### 第三阶段：高级功能 (3-5天)

#### 1. 资源引用表
- **用途**: 记录哪些工作流/任务使用了哪些 API
- **关系**: 多对多关系，支持资源追踪

#### 2. 健康检查表
- **用途**: 监控 API 端点的可用性
- **功能**: 定期检查 API 状态

#### 3. 视图和索引
- **视图**: 简化复杂查询
- **索引**: 提高查询性能

## 🗂️ 简化版本 (快速上手)

如果您想先实现基本功能，可以使用这个简化版本：

```sql
-- 简化版数据库设计
CREATE TABLE openapi_templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE api_endpoints (
    id TEXT PRIMARY KEY,
    template_id TEXT NOT NULL,
    path TEXT NOT NULL,
    method TEXT NOT NULL,
    base_url TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE api_call_logs (
    id TEXT PRIMARY KEY,
    endpoint_id TEXT NOT NULL,
    request_method TEXT NOT NULL,
    request_url TEXT NOT NULL,
    response_status_code INTEGER,
    response_time_ms INTEGER,
    created_at TEXT NOT NULL
);
```

## 📖 学习建议

### 1. 按优先级学习
1. **高优先级**: `api_call_logs` (HTTP 请求日志)
2. **中优先级**: `openapi_templates`, `api_documents`, `api_endpoints`
3. **低优先级**: `resource_references`, `api_health_checks`

### 2. 实践步骤
1. 先运行简化版本
2. 理解基本功能后，逐步添加高级功能
3. 根据实际需求调整表结构

### 3. 重点关注
- **HTTP 请求日志**: 这是最核心的功能
- **API 端点管理**: 支持动态 API 调用
- **模板存储**: 支持 OpenAPI 文档管理

## 🔧 快速测试

使用这个简单的测试脚本快速验证基本功能：

```python
import sqlite3

# 创建简化版数据库
conn = sqlite3.connect('simple_gateway.db')
cursor = conn.cursor()

# 创建表
cursor.execute('''
CREATE TABLE IF NOT EXISTS openapi_templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS api_call_logs (
    id TEXT PRIMARY KEY,
    endpoint_id TEXT NOT NULL,
    request_method TEXT NOT NULL,
    request_url TEXT NOT NULL,
    response_status_code INTEGER,
    response_time_ms INTEGER,
    created_at TEXT NOT NULL
)
''')

# 插入测试数据
cursor.execute('''
INSERT INTO openapi_templates (id, name, content, created_at)
VALUES (?, ?, ?, ?)
''', ('template-1', 'Pet Store API', '{"openapi": "3.0.0", ...}', '2024-01-01'))

cursor.execute('''
INSERT INTO api_call_logs (id, endpoint_id, request_method, request_url, 
                          response_status_code, response_time_ms, created_at)
VALUES (?, ?, ?, ?, ?, ?, ?)
''', ('log-1', 'endpoint-1', 'GET', 'https://api.example.com/pets', 200, 150, '2024-01-01'))

conn.commit()
conn.close()
```

## 📋 学习检查清单

### 基础理解 ✅
- [ ] 理解为什么需要这个数据库
- [ ] 理解核心表的作用
- [ ] 能够创建基本的表结构

### 中级理解 ✅
- [ ] 理解表之间的关系
- [ ] 能够编写基本查询
- [ ] 理解索引的作用

### 高级理解 ✅
- [ ] 理解视图的作用
- [ ] 理解触发器的用途
- [ ] 能够优化查询性能

## 🆘 遇到问题？

### 常见问题
1. **表太多记不住**: 先记住核心的 4 个表
2. **字段太多**: 先理解主要字段，其他字段可以后续学习
3. **关系复杂**: 画图理解表之间的关系

### 学习资源
- 查看 `test_sqlite_database.py` 了解基本用法
- 查看 `SQLITE_USAGE_GUIDE.md` 了解详细用法
- 查看 `HTTP_REQUEST_COMPLETE_INFO.md` 了解日志记录

## 🎉 学习目标

完成学习后，您应该能够：
1. 理解数据库的整体架构
2. 根据需求选择合适的表
3. 编写基本的查询语句
4. 进行简单的数据库操作

记住：**循序渐进，先实现基本功能，再逐步完善！** 