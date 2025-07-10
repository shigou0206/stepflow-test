-- StepFlow Gateway 简化版数据库设计
-- 只包含核心功能，便于快速上手和理解

-- 1. OpenAPI 模板表
CREATE TABLE openapi_templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    content TEXT NOT NULL,  -- OpenAPI 文档内容
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 2. API 端点表
CREATE TABLE api_endpoints (
    id TEXT PRIMARY KEY,
    template_id TEXT NOT NULL,
    path TEXT NOT NULL,
    method TEXT NOT NULL,
    base_url TEXT,
    operation_id TEXT,
    summary TEXT,
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (template_id) REFERENCES openapi_templates(id) ON DELETE CASCADE
);

-- 3. HTTP 请求日志表 (核心功能)
CREATE TABLE api_call_logs (
    id TEXT PRIMARY KEY,
    endpoint_id TEXT NOT NULL,
    request_method TEXT NOT NULL,
    request_url TEXT NOT NULL,
    request_headers TEXT,  -- JSON 格式
    request_body TEXT,
    response_status_code INTEGER,
    response_headers TEXT,  -- JSON 格式
    response_body TEXT,
    response_time_ms INTEGER,
    error_message TEXT,
    client_ip TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (endpoint_id) REFERENCES api_endpoints(id) ON DELETE CASCADE
);

-- 基本索引
CREATE INDEX idx_templates_status ON openapi_templates(status);
CREATE INDEX idx_endpoints_template ON api_endpoints(template_id);
CREATE INDEX idx_endpoints_method ON api_endpoints(method);
CREATE INDEX idx_logs_endpoint ON api_call_logs(endpoint_id);
CREATE INDEX idx_logs_status_code ON api_call_logs(response_status_code);
CREATE INDEX idx_logs_created_at ON api_call_logs(created_at);

-- 更新时间戳触发器
CREATE TRIGGER update_templates_updated_at 
    BEFORE UPDATE ON openapi_templates 
    FOR EACH ROW
BEGIN
    UPDATE openapi_templates SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER update_endpoints_updated_at 
    BEFORE UPDATE ON api_endpoints 
    FOR EACH ROW
BEGIN
    UPDATE api_endpoints SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- 插入示例数据
INSERT INTO openapi_templates (id, name, content, status, created_at, updated_at) VALUES
('template-1', 'Pet Store API', '{"openapi": "3.0.0", "info": {"title": "Pet Store API", "version": "1.0.0"}, "paths": {"/pets": {"get": {"summary": "List pets"}}}}', 'active', datetime('now'), datetime('now')),
('template-2', 'User Management API', '{"openapi": "3.0.0", "info": {"title": "User Management API", "version": "1.0.0"}, "paths": {"/users": {"get": {"summary": "List users"}}}}', 'active', datetime('now'), datetime('now'));

INSERT INTO api_endpoints (id, template_id, path, method, base_url, operation_id, summary, status, created_at, updated_at) VALUES
('endpoint-1', 'template-1', '/pets', 'GET', 'https://api.example.com', 'listPets', 'List all pets', 'active', datetime('now'), datetime('now')),
('endpoint-2', 'template-1', '/pets', 'POST', 'https://api.example.com', 'createPet', 'Create a new pet', 'active', datetime('now'), datetime('now')),
('endpoint-3', 'template-2', '/users', 'GET', 'https://api.example.com', 'listUsers', 'List all users', 'active', datetime('now'), datetime('now'));

-- 插入示例日志
INSERT INTO api_call_logs (id, endpoint_id, request_method, request_url, request_headers, request_body, response_status_code, response_headers, response_body, response_time_ms, client_ip, created_at) VALUES
('log-1', 'endpoint-1', 'GET', 'https://api.example.com/pets', '{"Content-Type": "application/json"}', '', 200, '{"Content-Type": "application/json"}', '{"pets": []}', 150, '192.168.1.100', datetime('now')),
('log-2', 'endpoint-2', 'POST', 'https://api.example.com/pets', '{"Content-Type": "application/json"}', '{"name": "Fluffy", "type": "cat"}', 201, '{"Content-Type": "application/json"}', '{"id": 1, "name": "Fluffy"}', 200, '192.168.1.100', datetime('now')),
('log-3', 'endpoint-1', 'GET', 'https://api.example.com/pets', '{"Content-Type": "application/json"}', '', 404, '{"Content-Type": "application/json"}', '{"error": "Not found"}', 50, '192.168.1.101', datetime('now'));

-- 创建简单视图
CREATE VIEW endpoint_summary AS
SELECT 
    e.id,
    e.path,
    e.method,
    e.summary,
    t.name as template_name,
    e.status,
    COUNT(l.id) as call_count,
    AVG(l.response_time_ms) as avg_response_time
FROM api_endpoints e
JOIN openapi_templates t ON e.template_id = t.id
LEFT JOIN api_call_logs l ON e.id = l.endpoint_id
GROUP BY e.id;

-- 显示创建结果
SELECT 'Database created successfully!' as message;
SELECT COUNT(*) as template_count FROM openapi_templates;
SELECT COUNT(*) as endpoint_count FROM api_endpoints;
SELECT COUNT(*) as log_count FROM api_call_logs; 