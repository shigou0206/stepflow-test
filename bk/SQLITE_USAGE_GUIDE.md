# StepFlow Gateway SQLite 数据库使用指南

## 概述

这个 SQLite 数据库设计为 StepFlow Gateway 提供了完整的 API 文档管理功能，支持：

1. **OpenAPI 模板存储** - 存储可重用的 API 模板
2. **API 文档实例** - 存储解析后的 API 文档
3. **API 端点管理** - 管理每个 API 的具体端点
4. **资源引用** - 支持工作流节点和调度任务引用
5. **调用日志** - 记录 API 调用历史和统计
6. **健康检查** - 监控 API 可用性

## 快速开始

### 1. 创建数据库

```bash
# 使用提供的初始化脚本
sqlite3 stepflow_gateway.db < database_init_sqlite.sql

# 或者使用 Python 脚本
python test_sqlite_database.py
```

### 2. 基本使用示例

```python
import sqlite3
import json
import uuid
from datetime import datetime

# 连接数据库
conn = sqlite3.connect('stepflow_gateway.db')
conn.row_factory = sqlite3.Row

# 插入 OpenAPI 模板
def insert_template(name, content):
    template_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO openapi_templates 
        (id, name, version, template_content, content_type, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (template_id, name, '1.0.0', content, 'yaml', now, now))
    
    conn.commit()
    return template_id

# 插入 API 文档实例
def insert_api_document(name, base_url, parsed_spec, template_id=None):
    doc_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO api_documents 
        (id, template_id, name, version, base_url, parsed_spec, original_content, 
         content_type, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (doc_id, template_id, name, '1.0.0', base_url, 
          json.dumps(parsed_spec), str(parsed_spec), 'yaml', now, now))
    
    conn.commit()
    return doc_id

# 插入 API 端点
def insert_endpoint(api_doc_id, path, method, operation_id, summary):
    endpoint_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO api_endpoints 
        (id, api_document_id, path, method, operation_id, summary, status, 
         created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (endpoint_id, api_doc_id, path, method, operation_id, summary, 
          'active', now, now))
    
    conn.commit()
    return endpoint_id
```

## 核心功能使用

### 1. 前端展示

```python
# 查询所有可用的 API 端点（用于前端展示）
def get_api_resources():
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            endpoint_id, path, method, operation_id, summary,
            api_name, api_version, base_url,
            call_count, success_count, error_count, reference_count
        FROM api_endpoint_resources
        WHERE endpoint_status = 'active' AND api_status = 'active'
        ORDER BY call_count DESC
    ''')
    
    return cursor.fetchall()

# 按标签过滤端点
def get_endpoints_by_tags(tags):
    cursor = conn.cursor()
    placeholders = ','.join(['?' for _ in tags])
    cursor.execute(f'''
        SELECT e.*, d.name as api_name, d.base_url
        FROM api_endpoints e
        JOIN api_documents d ON e.api_document_id = d.id
        WHERE e.status = 'active' 
        AND e.tags LIKE '%' || ? || '%'
    ''', tags)
    
    return cursor.fetchall()
```

### 2. HTTP 执行

```python
# 获取端点配置（用于 HTTP 执行）
def get_endpoint_config(endpoint_id):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            e.path, e.method, e.parameters, e.request_body_schema,
            d.base_url, d.auth_config, d.timeout_config
        FROM api_endpoints e
        JOIN api_documents d ON e.api_document_id = d.id
        WHERE e.id = ? AND e.status = 'active'
    ''', (endpoint_id,))
    
    return cursor.fetchone()

# 记录 API 调用日志
def log_api_call(endpoint_id, request_data, response_data, response_time):
    log_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO api_call_logs 
        (id, api_endpoint_id, request_method, request_url, request_headers,
         request_body, response_status_code, response_headers, response_body,
         response_time_ms, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        log_id, endpoint_id, request_data['method'], request_data['url'],
        json.dumps(request_data['headers']), request_data['body'],
        response_data['status_code'], json.dumps(response_data['headers']),
        response_data['body'], response_time, now
    ))
    
    conn.commit()
    return log_id
```

### 3. 工作流节点引用

```python
# 创建工作流节点引用
def create_workflow_reference(workflow_node_id, endpoint_id, config):
    ref_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO resource_references 
        (id, resource_type, resource_id, api_endpoint_id, reference_config,
         display_name, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        ref_id, 'workflow_node', workflow_node_id, endpoint_id,
        json.dumps(config), config.get('display_name', 'API Call'),
        'active', now, now
    ))
    
    conn.commit()
    return ref_id

# 获取工作流节点的 API 引用
def get_workflow_references(workflow_id):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT r.*, e.path, e.method, e.operation_id, e.summary,
               d.name as api_name, d.base_url
        FROM resource_references r
        JOIN api_endpoints e ON r.api_endpoint_id = e.id
        JOIN api_documents d ON e.api_document_id = d.id
        WHERE r.resource_type = 'workflow_node' 
        AND r.resource_id = ? AND r.status = 'active'
    ''', (workflow_id,))
    
    return cursor.fetchall()
```

### 4. 调度任务引用

```python
# 创建调度任务引用
def create_scheduled_task_reference(task_id, endpoint_id, schedule_config):
    ref_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO resource_references 
        (id, resource_type, resource_id, api_endpoint_id, reference_config,
         display_name, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        ref_id, 'scheduled_task', task_id, endpoint_id,
        json.dumps(schedule_config), schedule_config.get('name', 'Scheduled API Call'),
        'active', now, now
    ))
    
    conn.commit()
    return ref_id

# 获取调度任务的 API 引用
def get_scheduled_task_references(task_id):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT r.*, e.path, e.method, e.operation_id, e.summary,
               d.name as api_name, d.base_url
        FROM resource_references r
        JOIN api_endpoints e ON r.api_endpoint_id = e.id
        JOIN api_documents d ON e.api_document_id = d.id
        WHERE r.resource_type = 'scheduled_task' 
        AND r.resource_id = ? AND r.status = 'active'
    ''', (task_id,))
    
    return cursor.fetchall()
```

## 监控和统计

### 1. API 健康检查

```python
# 记录健康检查结果
def record_health_check(api_doc_id, check_type, status, response_time=None, error_msg=None):
    check_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO api_health_checks 
        (id, api_document_id, check_type, status, response_time_ms, 
         error_message, checked_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (check_id, api_doc_id, check_type, status, response_time, error_msg, now))
    
    # 更新 API 文档的健康状态
    cursor.execute('''
        UPDATE api_documents 
        SET health_status = ?, last_health_check = ?
        WHERE id = ?
    ''', (status, now, api_doc_id))
    
    conn.commit()
    return check_id

# 获取 API 健康状态
def get_api_health_status(api_doc_id):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT health_status, last_health_check,
               (SELECT COUNT(*) FROM api_health_checks 
                WHERE api_document_id = ? AND status = 'success' 
                AND checked_at > datetime('now', '-1 hour')) as recent_success,
               (SELECT COUNT(*) FROM api_health_checks 
                WHERE api_document_id = ? AND status = 'failed' 
                AND checked_at > datetime('now', '-1 hour')) as recent_failures
        FROM api_documents 
        WHERE id = ?
    ''', (api_doc_id, api_doc_id, api_doc_id))
    
    return cursor.fetchone()
```

### 2. 性能统计

```python
# 获取端点性能统计
def get_endpoint_stats(endpoint_id, days=30):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            COUNT(*) as total_calls,
            SUM(CASE WHEN response_status_code BETWEEN 200 AND 299 THEN 1 ELSE 0 END) as success_calls,
            SUM(CASE WHEN response_status_code >= 400 THEN 1 ELSE 0 END) as error_calls,
            AVG(response_time_ms) as avg_response_time,
            MAX(response_time_ms) as max_response_time,
            MIN(response_time_ms) as min_response_time
        FROM api_call_logs 
        WHERE api_endpoint_id = ? 
        AND created_at > datetime('now', '-{} days')
    '''.format(days), (endpoint_id,))
    
    return cursor.fetchone()

# 获取 API 文档统计
def get_api_document_stats(api_doc_id):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            d.name, d.version, d.total_endpoints, d.active_endpoints,
            SUM(e.call_count) as total_calls,
            SUM(e.success_count) as total_success,
            SUM(e.error_count) as total_errors,
            AVG(e.avg_response_time_ms) as avg_response_time
        FROM api_documents d
        LEFT JOIN api_endpoints e ON d.id = e.api_document_id
        WHERE d.id = ?
        GROUP BY d.id
    ''', (api_doc_id,))
    
    return cursor.fetchone()
```

## 数据维护

### 1. 数据清理

```python
# 清理旧的调用日志
def cleanup_old_logs(days=30):
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM api_call_logs 
        WHERE created_at < datetime('now', '-{} days')
    '''.format(days))
    
    deleted_count = cursor.rowcount
    conn.commit()
    return deleted_count

# 清理过期的健康检查记录
def cleanup_old_health_checks(days=7):
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM api_health_checks 
        WHERE checked_at < datetime('now', '-{} days')
    '''.format(days))
    
    deleted_count = cursor.rowcount
    conn.commit()
    return deleted_count
```

### 2. 数据备份

```python
import shutil
from datetime import datetime

# 备份数据库
def backup_database(backup_dir='backups'):
    import os
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{backup_dir}/stepflow_gateway_{timestamp}.db"
    
    shutil.copy2('stepflow_gateway.db', backup_path)
    return backup_path

# 恢复数据库
def restore_database(backup_path):
    shutil.copy2(backup_path, 'stepflow_gateway.db')
    return True
```

## 最佳实践

### 1. 连接管理

```python
import contextlib

@contextlib.contextmanager
def get_db_connection():
    """数据库连接上下文管理器"""
    conn = sqlite3.connect('stepflow_gateway.db')
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# 使用示例
def example_usage():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM api_endpoints LIMIT 5')
        return cursor.fetchall()
```

### 2. 事务管理

```python
def batch_insert_endpoints(api_doc_id, endpoints):
    """批量插入端点（使用事务）"""
    with get_db_connection() as conn:
        try:
            cursor = conn.cursor()
            for endpoint in endpoints:
                cursor.execute('''
                    INSERT INTO api_endpoints 
                    (id, api_document_id, path, method, operation_id, summary, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(uuid.uuid4()), api_doc_id, endpoint['path'], endpoint['method'],
                    endpoint['operation_id'], endpoint['summary'], 'active',
                    datetime.now().isoformat(), datetime.now().isoformat()
                ))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
```

### 3. 错误处理

```python
def safe_query(query, params=None):
    """安全的查询函数"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"数据库查询错误: {e}")
        return []
    except Exception as e:
        print(f"未知错误: {e}")
        return []
```

## 性能优化

### 1. 索引使用

数据库已经创建了必要的索引，但可以根据查询模式添加更多：

```sql
-- 如果经常按时间范围查询日志
CREATE INDEX idx_logs_time_range ON api_call_logs(created_at, api_endpoint_id);

-- 如果经常按状态和类型查询引用
CREATE INDEX idx_refs_type_status ON resource_references(resource_type, status);
```

### 2. 查询优化

```python
# 使用 LIMIT 限制结果集大小
def get_recent_logs(limit=100):
    cursor.execute('''
        SELECT * FROM api_call_logs 
        ORDER BY created_at DESC 
        LIMIT ?
    ''', (limit,))

# 使用分页查询
def get_logs_paginated(page=1, page_size=50):
    offset = (page - 1) * page_size
    cursor.execute('''
        SELECT * FROM api_call_logs 
        ORDER BY created_at DESC 
        LIMIT ? OFFSET ?
    ''', (page_size, offset))
```

## 故障排除

### 1. 常见问题

**问题**: 外键约束错误
```sql
-- 检查外键约束是否启用
PRAGMA foreign_keys;

-- 启用外键约束
PRAGMA foreign_keys = ON;
```

**问题**: 数据库锁定
```python
# 设置超时时间
conn = sqlite3.connect('stepflow_gateway.db', timeout=30.0)
```

**问题**: 内存不足
```sql
-- 清理数据库
VACUUM;

-- 分析表统计信息
ANALYZE;
```

### 2. 调试查询

```python
# 启用查询计划
def explain_query(query, params=None):
    cursor.execute(f"EXPLAIN QUERY PLAN {query}", params or ())
    return cursor.fetchall()

# 检查表结构
def show_table_info(table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return cursor.fetchall()
```

---

这个 SQLite 数据库设计为 StepFlow Gateway 提供了完整的数据管理功能，支持从模板存储到实际执行的完整流程。 