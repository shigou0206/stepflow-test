-- StepFlow Gateway SQLite 数据库初始化脚本
-- 创建完整的 SQLite 数据库结构

-- 启用外键约束
PRAGMA foreign_keys = ON;

-- 1. OpenAPI 模板表
CREATE TABLE openapi_templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    version TEXT NOT NULL,
    category TEXT,
    tags TEXT,
    template_content TEXT NOT NULL,
    content_type TEXT NOT NULL DEFAULT 'yaml',
    is_public INTEGER DEFAULT 0,
    created_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    status TEXT DEFAULT 'active'
);

-- 2. API 文档实例表
CREATE TABLE api_documents (
    id TEXT PRIMARY KEY,
    template_id TEXT,
    name TEXT NOT NULL,
    description TEXT,
    version TEXT NOT NULL,
    base_url TEXT NOT NULL,
    server_url TEXT,
    parsed_spec TEXT NOT NULL,
    original_content TEXT NOT NULL,
    content_type TEXT NOT NULL,
    auth_config TEXT,
    rate_limit_config TEXT,
    timeout_config TEXT,
    status TEXT DEFAULT 'active',
    health_status TEXT DEFAULT 'unknown',
    last_health_check TEXT,
    total_endpoints INTEGER DEFAULT 0,
    active_endpoints INTEGER DEFAULT 0,
    created_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (template_id) REFERENCES openapi_templates(id) ON DELETE SET NULL
);

-- 3. API 端点表
CREATE TABLE api_endpoints (
    id TEXT PRIMARY KEY,
    api_document_id TEXT NOT NULL,
    path TEXT NOT NULL,
    method TEXT NOT NULL CHECK (method IN ('GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS')),
    operation_id TEXT,
    summary TEXT,
    description TEXT,
    tags TEXT,
    parameters TEXT,
    request_body_schema TEXT,
    response_schemas TEXT,
    auth_required INTEGER DEFAULT 0,
    rate_limit_enabled INTEGER DEFAULT 0,
    timeout_ms INTEGER DEFAULT 30000,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'deprecated')),
    is_deprecated INTEGER DEFAULT 0,
    call_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    avg_response_time_ms INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (api_document_id) REFERENCES api_documents(id) ON DELETE CASCADE
);

-- 4. 资源引用表
CREATE TABLE resource_references (
    id TEXT PRIMARY KEY,
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    api_endpoint_id TEXT NOT NULL,
    reference_config TEXT,
    display_name TEXT,
    description TEXT,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'error')),
    last_used_at TEXT,
    usage_count INTEGER DEFAULT 0,
    created_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (api_endpoint_id) REFERENCES api_endpoints(id) ON DELETE CASCADE
);

-- 5. API 调用日志表
CREATE TABLE api_call_logs (
    id TEXT PRIMARY KEY,
    api_endpoint_id TEXT NOT NULL,
    resource_reference_id TEXT,
    request_method TEXT NOT NULL,
    request_url TEXT NOT NULL,
    request_headers TEXT,
    request_body TEXT,
    request_params TEXT,
    response_status_code INTEGER,
    response_headers TEXT,
    response_body TEXT,
    response_time_ms INTEGER,
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    error_message TEXT,
    error_type TEXT,
    client_ip TEXT,
    user_agent TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (api_endpoint_id) REFERENCES api_endpoints(id) ON DELETE CASCADE,
    FOREIGN KEY (resource_reference_id) REFERENCES resource_references(id) ON DELETE SET NULL
);

-- 6. API 健康检查表
CREATE TABLE api_health_checks (
    id TEXT PRIMARY KEY,
    api_document_id TEXT NOT NULL,
    check_type TEXT NOT NULL,
    status TEXT NOT NULL,
    response_time_ms INTEGER,
    error_message TEXT,
    details TEXT,
    checked_at TEXT NOT NULL,
    FOREIGN KEY (api_document_id) REFERENCES api_documents(id) ON DELETE CASCADE
);

-- 创建索引
-- OpenAPI 模板表索引
CREATE UNIQUE INDEX uk_template_name_version ON openapi_templates(name, version);
CREATE INDEX idx_template_category ON openapi_templates(category);
CREATE INDEX idx_template_status ON openapi_templates(status);
CREATE INDEX idx_template_created_at ON openapi_templates(created_at);

-- API 文档表索引
CREATE UNIQUE INDEX uk_api_name_version ON api_documents(name, version);
CREATE INDEX idx_api_template_id ON api_documents(template_id);
CREATE INDEX idx_api_status ON api_documents(status);
CREATE INDEX idx_api_health_status ON api_documents(health_status);
CREATE INDEX idx_api_created_at ON api_documents(created_at);

-- API 端点表索引
CREATE UNIQUE INDEX uk_endpoint_path_method ON api_endpoints(api_document_id, path, method);
CREATE INDEX idx_endpoint_api_document_id ON api_endpoints(api_document_id);
CREATE INDEX idx_endpoint_method ON api_endpoints(method);
CREATE INDEX idx_endpoint_status ON api_endpoints(status);
CREATE INDEX idx_endpoint_operation_id ON api_endpoints(operation_id);

-- 资源引用表索引
CREATE INDEX idx_ref_resource_type_id ON resource_references(resource_type, resource_id);
CREATE INDEX idx_ref_api_endpoint_id ON resource_references(api_endpoint_id);
CREATE INDEX idx_ref_status ON resource_references(status);
CREATE INDEX idx_ref_last_used ON resource_references(last_used_at);

-- API 调用日志表索引
CREATE INDEX idx_log_api_endpoint_id ON api_call_logs(api_endpoint_id);
CREATE INDEX idx_log_resource_reference_id ON api_call_logs(resource_reference_id);
CREATE INDEX idx_log_status_code ON api_call_logs(response_status_code);
CREATE INDEX idx_log_created_at ON api_call_logs(created_at);
CREATE INDEX idx_log_error_type ON api_call_logs(error_type);

-- API 健康检查表索引
CREATE INDEX idx_health_api_document_id ON api_health_checks(api_document_id);
CREATE INDEX idx_health_status ON api_health_checks(status);
CREATE INDEX idx_health_checked_at ON api_health_checks(checked_at);

-- 复合索引
CREATE INDEX idx_endpoints_doc_method_status ON api_endpoints(api_document_id, method, status);
CREATE INDEX idx_refs_type_status_endpoint ON resource_references(resource_type, status, api_endpoint_id);
CREATE INDEX idx_logs_endpoint_time ON api_call_logs(api_endpoint_id, created_at DESC);

-- 创建视图
-- API 端点资源视图
CREATE VIEW api_endpoint_resources AS
SELECT 
    e.id as endpoint_id,
    e.path,
    e.method,
    e.operation_id,
    e.summary,
    e.description,
    e.tags,
    d.id as api_document_id,
    d.name as api_name,
    d.version as api_version,
    d.base_url,
    e.status as endpoint_status,
    d.status as api_status,
    e.call_count,
    e.success_count,
    e.error_count,
    e.avg_response_time_ms,
    COUNT(r.id) as reference_count
FROM api_endpoints e
JOIN api_documents d ON e.api_document_id = d.id
LEFT JOIN resource_references r ON e.id = r.api_endpoint_id AND r.status = 'active'
GROUP BY e.id, d.id;

-- 资源引用统计视图
CREATE VIEW resource_reference_stats AS
SELECT 
    r.resource_type,
    r.resource_id,
    COUNT(r.id) as total_references,
    SUM(CASE WHEN r.status = 'active' THEN 1 ELSE 0 END) as active_references,
    SUM(CASE WHEN r.status = 'error' THEN 1 ELSE 0 END) as error_references,
    SUM(r.usage_count) as total_usage,
    MAX(r.last_used_at) as last_used
FROM resource_references r
GROUP BY r.resource_type, r.resource_id;

-- 创建触发器
-- 更新时间戳触发器
CREATE TRIGGER update_openapi_templates_updated_at 
    BEFORE UPDATE ON openapi_templates 
    FOR EACH ROW
BEGIN
    UPDATE openapi_templates SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER update_api_documents_updated_at 
    BEFORE UPDATE ON api_documents 
    FOR EACH ROW
BEGIN
    UPDATE api_documents SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER update_api_endpoints_updated_at 
    BEFORE UPDATE ON api_endpoints 
    FOR EACH ROW
BEGIN
    UPDATE api_endpoints SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER update_resource_references_updated_at 
    BEFORE UPDATE ON resource_references 
    FOR EACH ROW
BEGIN
    UPDATE resource_references SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- 统计更新触发器
CREATE TRIGGER update_endpoint_stats_trigger 
    AFTER INSERT ON api_call_logs 
    FOR EACH ROW
BEGIN
    UPDATE api_endpoints 
    SET 
        call_count = call_count + 1,
        success_count = CASE WHEN NEW.response_status_code BETWEEN 200 AND 299 
                             THEN success_count + 1 ELSE success_count END,
        error_count = CASE WHEN NEW.response_status_code >= 400 
                           THEN error_count + 1 ELSE error_count END,
        avg_response_time_ms = CASE 
            WHEN avg_response_time_ms IS NULL THEN NEW.response_time_ms
            ELSE (avg_response_time_ms + NEW.response_time_ms) / 2
        END
    WHERE id = NEW.api_endpoint_id;
END;

-- 端点计数更新触发器
CREATE TRIGGER update_document_endpoint_count_insert 
    AFTER INSERT ON api_endpoints 
    FOR EACH ROW
BEGIN
    UPDATE api_documents 
    SET 
        total_endpoints = total_endpoints + 1,
        active_endpoints = active_endpoints + CASE WHEN NEW.status = 'active' THEN 1 ELSE 0 END
    WHERE id = NEW.api_document_id;
END;

CREATE TRIGGER update_document_endpoint_count_update 
    AFTER UPDATE ON api_endpoints 
    FOR EACH ROW
BEGIN
    UPDATE api_documents 
    SET 
        active_endpoints = active_endpoints + 
            CASE WHEN NEW.status = 'active' THEN 1 ELSE 0 END -
            CASE WHEN OLD.status = 'active' THEN 1 ELSE 0 END
    WHERE id = NEW.api_document_id;
END;

CREATE TRIGGER update_document_endpoint_count_delete 
    AFTER DELETE ON api_endpoints 
    FOR EACH ROW
BEGIN
    UPDATE api_documents 
    SET 
        total_endpoints = total_endpoints - 1,
        active_endpoints = active_endpoints - CASE WHEN OLD.status = 'active' THEN 1 ELSE 0 END
    WHERE id = OLD.api_document_id;
END;

-- 插入示例数据
-- 插入示例 OpenAPI 模板
INSERT INTO openapi_templates (id, name, description, version, category, tags, template_content, content_type, is_public, created_at, updated_at) VALUES
(
    '550e8400-e29b-41d4-a716-446655440001',
    'PetStore API',
    'Swagger PetStore API 示例',
    '1.0.0',
    '示例',
    '["petstore", "demo", "swagger"]',
    'openapi: 3.0.0
info:
  title: Swagger Petstore
  version: 1.0.0
  description: A sample API that uses a petstore as an example
servers:
  - url: https://petstore.swagger.io/v1
paths:
  /pets:
    get:
      summary: List all pets
      operationId: listPets
      tags:
        - pets
      parameters:
        - name: limit
          in: query
          description: How many items to return at one time
          required: false
          schema:
            type: integer
            format: int32
      responses:
        "200":
          description: A paged array of pets
          headers:
            x-next:
              description: A link to the next page of responses
              schema:
                type: string
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Pets"
        default:
          description: unexpected error
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
    post:
      summary: Create a pet
      operationId: createPets
      tags:
        - pets
      responses:
        "201":
          description: Null response
        default:
          description: unexpected error
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
  /pets/{petId}:
    get:
      summary: Info for a specific pet
      operationId: showPetById
      tags:
        - pets
      parameters:
        - name: petId
          in: path
          required: true
          description: The id of the pet to retrieve
          schema:
            type: string
      responses:
        "200":
          description: Expected response to a valid request
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Pet"
        default:
          description: unexpected error
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
components:
  schemas:
    Pet:
      type: object
      required:
        - id
        - name
      properties:
        id:
          type: integer
          format: int64
        name:
          type: string
        tag:
          type: string
    Pets:
      type: array
      items:
        $ref: "#/components/schemas/Pet"
    Error:
      type: object
      required:
        - code
        - message
      properties:
        code:
          type: integer
          format: int32
        message:
          type: string',
    'yaml',
    1,
    datetime('now'),
    datetime('now')
);

-- 插入示例 API 文档实例
INSERT INTO api_documents (id, name, description, version, base_url, parsed_spec, original_content, content_type, created_at, updated_at) VALUES
(
    '550e8400-e29b-41d4-a716-446655440002',
    'PetStore Demo',
    'PetStore API 演示实例',
    '1.0.0',
    'https://petstore.swagger.io/v1',
    '{"openapi":"3.0.0","info":{"title":"Swagger Petstore","version":"1.0.0"},"paths":{}}',
    'openapi: 3.0.0
info:
  title: Swagger Petstore
  version: 1.0.0
paths:
  /pets:
    get:
      summary: List all pets
      operationId: listPets',
    'yaml',
    datetime('now'),
    datetime('now')
);

-- 插入示例端点
INSERT INTO api_endpoints (id, api_document_id, path, method, operation_id, summary, description, tags, status, created_at, updated_at) VALUES
(
    '550e8400-e29b-41d4-a716-446655440003',
    '550e8400-e29b-41d4-a716-446655440002',
    '/pets',
    'GET',
    'listPets',
    'List all pets',
    '获取所有宠物列表',
    '["pets", "list"]',
    'active',
    datetime('now'),
    datetime('now')
),
(
    '550e8400-e29b-41d4-a716-446655440004',
    '550e8400-e29b-41d4-a716-446655440002',
    '/pets',
    'POST',
    'createPets',
    'Create a pet',
    '创建新宠物',
    '["pets", "create"]',
    'active',
    datetime('now'),
    datetime('now')
),
(
    '550e8400-e29b-41d4-a716-446655440005',
    '550e8400-e29b-41d4-a716-446655440002',
    '/pets/{petId}',
    'GET',
    'showPetById',
    'Info for a specific pet',
    '获取特定宠物信息',
    '["pets", "detail"]',
    'active',
    datetime('now'),
    datetime('now')
);

-- 显示创建结果
SELECT 'SQLite database initialization completed successfully!' as status; 