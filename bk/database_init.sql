-- StepFlow Gateway 数据库初始化脚本
-- 创建完整的数据库结构

-- 启用必要的扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 1. OpenAPI 模板表
CREATE TABLE openapi_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    version VARCHAR(50) NOT NULL,
    category VARCHAR(100),
    tags TEXT[],
    template_content TEXT NOT NULL,
    content_type VARCHAR(20) NOT NULL DEFAULT 'yaml',
    is_public BOOLEAN DEFAULT false,
    created_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active'
);

-- 2. API 文档实例表
CREATE TABLE api_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID REFERENCES openapi_templates(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    version VARCHAR(50) NOT NULL,
    base_url VARCHAR(500) NOT NULL,
    server_url VARCHAR(500),
    parsed_spec JSONB NOT NULL,
    original_content TEXT NOT NULL,
    content_type VARCHAR(20) NOT NULL,
    auth_config JSONB,
    rate_limit_config JSONB,
    timeout_config JSONB,
    status VARCHAR(20) DEFAULT 'active',
    health_status VARCHAR(20) DEFAULT 'unknown',
    last_health_check TIMESTAMP WITH TIME ZONE,
    total_endpoints INTEGER DEFAULT 0,
    active_endpoints INTEGER DEFAULT 0,
    created_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. API 端点表
CREATE TABLE api_endpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_document_id UUID NOT NULL REFERENCES api_documents(id) ON DELETE CASCADE,
    path VARCHAR(500) NOT NULL,
    method VARCHAR(10) NOT NULL,
    operation_id VARCHAR(255),
    summary TEXT,
    description TEXT,
    tags TEXT[],
    parameters JSONB,
    request_body_schema JSONB,
    response_schemas JSONB,
    auth_required BOOLEAN DEFAULT false,
    rate_limit_enabled BOOLEAN DEFAULT false,
    timeout_ms INTEGER DEFAULT 30000,
    status VARCHAR(20) DEFAULT 'active',
    is_deprecated BOOLEAN DEFAULT false,
    call_count BIGINT DEFAULT 0,
    success_count BIGINT DEFAULT 0,
    error_count BIGINT DEFAULT 0,
    avg_response_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. 资源引用表
CREATE TABLE resource_references (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID NOT NULL,
    api_endpoint_id UUID NOT NULL REFERENCES api_endpoints(id) ON DELETE CASCADE,
    reference_config JSONB,
    display_name VARCHAR(255),
    description TEXT,
    status VARCHAR(20) DEFAULT 'active',
    last_used_at TIMESTAMP WITH TIME ZONE,
    usage_count INTEGER DEFAULT 0,
    created_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. API 调用日志表
CREATE TABLE api_call_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_endpoint_id UUID NOT NULL REFERENCES api_endpoints(id) ON DELETE CASCADE,
    resource_reference_id UUID REFERENCES resource_references(id) ON DELETE SET NULL,
    request_method VARCHAR(10) NOT NULL,
    request_url TEXT NOT NULL,
    request_headers JSONB,
    request_body TEXT,
    request_params JSONB,
    response_status_code INTEGER,
    response_headers JSONB,
    response_body TEXT,
    response_time_ms INTEGER,
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    error_message TEXT,
    error_type VARCHAR(50),
    client_ip INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. API 健康检查表
CREATE TABLE api_health_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_document_id UUID NOT NULL REFERENCES api_documents(id) ON DELETE CASCADE,
    check_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    response_time_ms INTEGER,
    error_message TEXT,
    details JSONB,
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
-- OpenAPI 模板表索引
CREATE UNIQUE INDEX uk_template_name_version ON openapi_templates(name, version);
CREATE INDEX idx_template_category ON openapi_templates(category);
CREATE INDEX idx_template_tags ON openapi_templates USING GIN(tags);
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
CREATE INDEX idx_endpoint_tags ON api_endpoints USING GIN(tags);
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
    COUNT(CASE WHEN r.status = 'active' THEN 1 END) as active_references,
    COUNT(CASE WHEN r.status = 'error' THEN 1 END) as error_references,
    SUM(r.usage_count) as total_usage,
    MAX(r.last_used_at) as last_used
FROM resource_references r
GROUP BY r.resource_type, r.resource_id;

-- 创建约束
-- 检查约束
ALTER TABLE api_endpoints 
ADD CONSTRAINT chk_method 
CHECK (method IN ('GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'));

ALTER TABLE api_documents 
ADD CONSTRAINT chk_doc_status 
CHECK (status IN ('active', 'inactive', 'error'));

ALTER TABLE api_endpoints 
ADD CONSTRAINT chk_endpoint_status 
CHECK (status IN ('active', 'inactive', 'deprecated'));

ALTER TABLE resource_references 
ADD CONSTRAINT chk_ref_status 
CHECK (status IN ('active', 'inactive', 'error'));

-- 创建触发器函数
-- 更新时间戳触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 统计更新触发器函数
CREATE OR REPLACE FUNCTION update_endpoint_stats()
RETURNS TRIGGER AS $$
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
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 端点计数更新触发器函数
CREATE OR REPLACE FUNCTION update_document_endpoint_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE api_documents 
        SET 
            total_endpoints = total_endpoints + 1,
            active_endpoints = active_endpoints + CASE WHEN NEW.status = 'active' THEN 1 ELSE 0 END
        WHERE id = NEW.api_document_id;
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        -- 如果状态发生变化
        IF OLD.status != NEW.status THEN
            UPDATE api_documents 
            SET 
                active_endpoints = active_endpoints + 
                    CASE WHEN NEW.status = 'active' THEN 1 ELSE 0 END -
                    CASE WHEN OLD.status = 'active' THEN 1 ELSE 0 END
            WHERE id = NEW.api_document_id;
        END IF;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE api_documents 
        SET 
            total_endpoints = total_endpoints - 1,
            active_endpoints = active_endpoints - CASE WHEN OLD.status = 'active' THEN 1 ELSE 0 END
        WHERE id = OLD.api_document_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ language 'plpgsql';

-- 创建触发器
-- 更新时间戳触发器
CREATE TRIGGER update_openapi_templates_updated_at 
    BEFORE UPDATE ON openapi_templates 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_api_documents_updated_at 
    BEFORE UPDATE ON api_documents 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_api_endpoints_updated_at 
    BEFORE UPDATE ON api_endpoints 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_resource_references_updated_at 
    BEFORE UPDATE ON resource_references 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 统计更新触发器
CREATE TRIGGER update_endpoint_stats_trigger 
    AFTER INSERT ON api_call_logs 
    FOR EACH ROW EXECUTE FUNCTION update_endpoint_stats();

-- 端点计数更新触发器
CREATE TRIGGER update_document_endpoint_count_trigger 
    AFTER INSERT OR UPDATE OR DELETE ON api_endpoints 
    FOR EACH ROW EXECUTE FUNCTION update_document_endpoint_count();

-- 插入示例数据
-- 插入示例 OpenAPI 模板
INSERT INTO openapi_templates (name, description, version, category, tags, template_content, content_type, is_public) VALUES
(
    'PetStore API',
    'Swagger PetStore API 示例',
    '1.0.0',
    '示例',
    ARRAY['petstore', 'demo', 'swagger'],
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
    true
);

-- 插入示例 API 文档实例
INSERT INTO api_documents (name, description, version, base_url, parsed_spec, original_content, content_type) VALUES
(
    'PetStore Demo',
    'PetStore API 演示实例',
    '1.0.0',
    'https://petstore.swagger.io/v1',
    '{"openapi":"3.0.0","info":{"title":"Swagger Petstore","version":"1.0.0"},"paths":{}}'::jsonb,
    'openapi: 3.0.0
info:
  title: Swagger Petstore
  version: 1.0.0
paths:
  /pets:
    get:
      summary: List all pets
      operationId: listPets',
    'yaml'
);

-- 获取刚插入的 API 文档 ID
DO $$
DECLARE
    doc_id UUID;
BEGIN
    SELECT id INTO doc_id FROM api_documents WHERE name = 'PetStore Demo' LIMIT 1;
    
    -- 插入示例端点
    INSERT INTO api_endpoints (api_document_id, path, method, operation_id, summary, description, tags, status) VALUES
    (doc_id, '/pets', 'GET', 'listPets', 'List all pets', '获取所有宠物列表', ARRAY['pets', 'list'], 'active'),
    (doc_id, '/pets', 'POST', 'createPets', 'Create a pet', '创建新宠物', ARRAY['pets', 'create'], 'active'),
    (doc_id, '/pets/{petId}', 'GET', 'showPetById', 'Info for a specific pet', '获取特定宠物信息', ARRAY['pets', 'detail'], 'active');
END $$;

-- 创建注释
COMMENT ON TABLE openapi_templates IS 'OpenAPI 文档模板表';
COMMENT ON TABLE api_documents IS 'API 文档实例表';
COMMENT ON TABLE api_endpoints IS 'API 端点表';
COMMENT ON TABLE resource_references IS '资源引用表';
COMMENT ON TABLE api_call_logs IS 'API 调用日志表';
COMMENT ON TABLE api_health_checks IS 'API 健康检查表';

COMMENT ON VIEW api_endpoint_resources IS 'API 端点资源视图，用于前端展示';
COMMENT ON VIEW resource_reference_stats IS '资源引用统计视图';

-- 显示创建结果
SELECT 'Database initialization completed successfully!' as status; 