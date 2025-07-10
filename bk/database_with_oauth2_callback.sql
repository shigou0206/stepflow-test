-- StepFlow Gateway 完整数据库设计（包含 OAuth2 回调支持）
-- 支持 OpenAPI 模板管理、API 端点、HTTP 日志记录、完整的认证系统和 OAuth2 回调流程

-- 1. OpenAPI 模板表
CREATE TABLE openapi_templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    content TEXT NOT NULL,  -- OpenAPI 文档内容
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 2. API 文档表
CREATE TABLE api_documents (
    id TEXT PRIMARY KEY,
    template_id TEXT NOT NULL,
    name TEXT NOT NULL,
    version TEXT,
    base_url TEXT,
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (template_id) REFERENCES openapi_templates(id) ON DELETE CASCADE
);

-- 3. API 端点表
CREATE TABLE api_endpoints (
    id TEXT PRIMARY KEY,
    api_document_id TEXT NOT NULL,
    path TEXT NOT NULL,
    method TEXT NOT NULL,
    operation_id TEXT,
    summary TEXT,
    description TEXT,
    tags TEXT, -- JSON 格式
    status TEXT DEFAULT 'active',
    call_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    avg_response_time_ms INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (api_document_id) REFERENCES api_documents(id) ON DELETE CASCADE
);

-- 4. API 认证配置表
CREATE TABLE api_auth_configs (
    id TEXT PRIMARY KEY,
    api_document_id TEXT NOT NULL,
    auth_type TEXT NOT NULL, -- 'none', 'basic', 'bearer', 'api_key', 'oauth2', 'custom'
    auth_config TEXT NOT NULL, -- JSON 格式的认证配置
    is_required INTEGER DEFAULT 1, -- 是否必需认证
    is_global INTEGER DEFAULT 0, -- 是否全局配置
    priority INTEGER DEFAULT 0, -- 优先级
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (api_document_id) REFERENCES api_documents(id) ON DELETE CASCADE
);

-- 5. 认证凭据表
CREATE TABLE auth_credentials (
    id TEXT PRIMARY KEY,
    auth_config_id TEXT NOT NULL,
    credential_type TEXT NOT NULL, -- 'static', 'dynamic', 'template'
    credential_key TEXT NOT NULL, -- 凭据标识
    credential_value TEXT, -- 凭据值（加密存储）
    credential_template TEXT, -- 动态凭据模板
    is_encrypted INTEGER DEFAULT 1, -- 是否加密存储
    expires_at TEXT, -- 过期时间
    refresh_before_expiry INTEGER DEFAULT 3600, -- 过期前刷新时间（秒）
    last_refreshed_at TEXT, -- 最后刷新时间
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (auth_config_id) REFERENCES api_auth_configs(id) ON DELETE CASCADE
);

-- 6. 认证缓存表
CREATE TABLE auth_cache (
    id TEXT PRIMARY KEY,
    auth_config_id TEXT NOT NULL,
    cache_key TEXT NOT NULL, -- 缓存键
    cache_value TEXT NOT NULL, -- 缓存值（加密存储）
    cache_type TEXT NOT NULL, -- 'token', 'session', 'credential'
    expires_at TEXT NOT NULL, -- 缓存过期时间
    created_at TEXT NOT NULL,
    FOREIGN KEY (auth_config_id) REFERENCES api_auth_configs(id) ON DELETE CASCADE
);

-- 7. 认证日志表
CREATE TABLE auth_logs (
    id TEXT PRIMARY KEY,
    auth_config_id TEXT NOT NULL,
    request_id TEXT, -- 关联的请求ID
    auth_type TEXT NOT NULL, -- 认证类型
    auth_status TEXT NOT NULL, -- 'success', 'failed', 'expired', 'refreshed'
    auth_method TEXT NOT NULL, -- 'static', 'dynamic', 'cached'
    error_message TEXT, -- 错误信息
    response_time_ms INTEGER, -- 认证响应时间
    client_ip TEXT, -- 客户端IP
    user_agent TEXT, -- 用户代理
    created_at TEXT NOT NULL,
    FOREIGN KEY (auth_config_id) REFERENCES api_auth_configs(id) ON DELETE CASCADE
);

-- 8. Gateway 用户表
CREATE TABLE gateway_users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    password_hash TEXT NOT NULL, -- 加密的密码
    salt TEXT NOT NULL, -- 密码盐值
    role TEXT NOT NULL, -- 'admin', 'user', 'api_user'
    permissions TEXT, -- JSON 格式的权限配置
    is_active INTEGER DEFAULT 1,
    last_login_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 9. Gateway 会话表
CREATE TABLE gateway_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    session_token TEXT UNIQUE NOT NULL, -- 会话令牌
    refresh_token TEXT, -- 刷新令牌
    expires_at TEXT NOT NULL, -- 过期时间
    client_info TEXT, -- JSON 格式的客户端信息
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES gateway_users(id) ON DELETE CASCADE
);

-- 10. 资源引用表
CREATE TABLE resource_references (
    id TEXT PRIMARY KEY,
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    api_endpoint_id TEXT NOT NULL,
    reference_config TEXT, -- JSON 字符串
    display_name TEXT,
    description TEXT,
    status TEXT DEFAULT 'active',
    last_used_at TEXT,
    usage_count INTEGER DEFAULT 0,
    created_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (api_endpoint_id) REFERENCES api_endpoints(id) ON DELETE CASCADE
);

-- 11. API 调用日志表
CREATE TABLE api_call_logs (
    id TEXT PRIMARY KEY,
    api_endpoint_id TEXT NOT NULL,
    resource_reference_id TEXT,
    request_method TEXT NOT NULL,
    request_url TEXT NOT NULL,
    request_headers TEXT, -- JSON 字符串
    request_body TEXT,
    request_params TEXT, -- JSON 字符串
    response_status_code INTEGER,
    response_headers TEXT, -- JSON 字符串
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

-- 12. API 健康检查表
CREATE TABLE api_health_checks (
    id TEXT PRIMARY KEY,
    api_document_id TEXT NOT NULL,
    check_type TEXT NOT NULL,
    status TEXT NOT NULL,
    response_time_ms INTEGER,
    error_message TEXT,
    details TEXT, -- JSON 字符串
    checked_at TEXT NOT NULL,
    FOREIGN KEY (api_document_id) REFERENCES api_documents(id) ON DELETE CASCADE
);

-- ========== OAuth2 回调支持表 ==========

-- 13. OAuth2 授权状态表（管理授权流程状态）
CREATE TABLE oauth2_auth_states (
    id TEXT PRIMARY KEY,
    auth_config_id TEXT NOT NULL,
    user_id TEXT, -- 可为空，支持匿名授权
    state TEXT NOT NULL, -- 防CSRF的state参数
    code_verifier TEXT, -- PKCE支持（OAuth2.1）
    code_challenge TEXT, -- PKCE支持
    code_challenge_method TEXT, -- 'S256' 或 'plain'
    redirect_uri TEXT NOT NULL,
    scope TEXT,
    response_type TEXT DEFAULT 'code', -- 'code' 或 'token'
    client_id TEXT NOT NULL,
    expires_at TEXT NOT NULL, -- state过期时间
    created_at TEXT NOT NULL,
    FOREIGN KEY (auth_config_id) REFERENCES api_auth_configs(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES gateway_users(id) ON DELETE CASCADE
);

-- 14. 用户API授权表（管理用户对特定API的授权状态）
CREATE TABLE user_api_authorizations (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    api_document_id TEXT NOT NULL,
    auth_config_id TEXT NOT NULL,
    access_token TEXT, -- 加密存储
    refresh_token TEXT, -- 加密存储
    token_type TEXT DEFAULT 'Bearer',
    expires_at TEXT,
    scope TEXT,
    auth_id TEXT, -- 第三方返回的auth_id/user_id
    provider_user_id TEXT, -- 第三方用户ID
    provider_user_info TEXT, -- JSON格式的第三方用户信息
    is_active INTEGER DEFAULT 1,
    last_used_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES gateway_users(id) ON DELETE CASCADE,
    FOREIGN KEY (api_document_id) REFERENCES api_documents(id) ON DELETE CASCADE,
    FOREIGN KEY (auth_config_id) REFERENCES api_auth_configs(id) ON DELETE CASCADE
);

-- 15. OAuth2 回调日志表（详细记录回调过程）
CREATE TABLE oauth2_callback_logs (
    id TEXT PRIMARY KEY,
    auth_state_id TEXT NOT NULL,
    user_id TEXT,
    callback_code TEXT, -- 授权码
    callback_state TEXT, -- 回调中的state参数
    callback_error TEXT, -- 回调错误信息
    callback_error_description TEXT, -- 错误描述
    token_response TEXT, -- 完整的token响应（加密存储）
    auth_id TEXT, -- 第三方返回的auth_id
    provider_user_id TEXT, -- 第三方用户ID
    client_ip TEXT,
    user_agent TEXT,
    callback_status TEXT NOT NULL, -- 'success', 'failed', 'error'
    response_time_ms INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY (auth_state_id) REFERENCES oauth2_auth_states(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES gateway_users(id) ON DELETE CASCADE
);

-- ========== 创建索引 ==========

-- 原有表索引
CREATE INDEX idx_templates_status ON openapi_templates(status);
CREATE INDEX idx_documents_template ON api_documents(template_id);
CREATE INDEX idx_documents_status ON api_documents(status);
CREATE INDEX idx_endpoints_document ON api_endpoints(api_document_id);
CREATE INDEX idx_endpoints_method ON api_endpoints(method);
CREATE INDEX idx_endpoints_status ON api_endpoints(status);
CREATE INDEX idx_auth_api_document_id ON api_auth_configs(api_document_id);
CREATE INDEX idx_auth_type ON api_auth_configs(auth_type);
CREATE INDEX idx_auth_status ON api_auth_configs(status);
CREATE INDEX idx_cred_auth_config_id ON auth_credentials(auth_config_id);
CREATE INDEX idx_cred_type ON auth_credentials(credential_type);
CREATE INDEX idx_cred_expires_at ON auth_credentials(expires_at);
CREATE INDEX idx_cred_status ON auth_credentials(status);
CREATE INDEX idx_cache_auth_config_id ON auth_cache(auth_config_id);
CREATE INDEX idx_cache_key ON auth_cache(cache_key);
CREATE INDEX idx_cache_expires_at ON auth_cache(expires_at);
CREATE INDEX idx_auth_log_config_id ON auth_logs(auth_config_id);
CREATE INDEX idx_auth_log_status ON auth_logs(auth_status);
CREATE INDEX idx_auth_log_created_at ON auth_logs(created_at);
CREATE INDEX idx_user_username ON gateway_users(username);
CREATE INDEX idx_user_email ON gateway_users(email);
CREATE INDEX idx_user_role ON gateway_users(role);
CREATE INDEX idx_user_status ON gateway_users(is_active);
CREATE INDEX idx_session_user_id ON gateway_sessions(user_id);
CREATE INDEX idx_session_token ON gateway_sessions(session_token);
CREATE INDEX idx_session_expires_at ON gateway_sessions(expires_at);
CREATE INDEX idx_ref_resource_type_id ON resource_references(resource_type, resource_id);
CREATE INDEX idx_ref_api_endpoint_id ON resource_references(api_endpoint_id);
CREATE INDEX idx_ref_status ON resource_references(status);
CREATE INDEX idx_ref_last_used ON resource_references(last_used_at);
CREATE INDEX idx_log_api_endpoint_id ON api_call_logs(api_endpoint_id);
CREATE INDEX idx_log_resource_reference_id ON api_call_logs(resource_reference_id);
CREATE INDEX idx_log_status_code ON api_call_logs(response_status_code);
CREATE INDEX idx_log_created_at ON api_call_logs(created_at);
CREATE INDEX idx_log_error_type ON api_call_logs(error_type);
CREATE INDEX idx_health_api_document_id ON api_health_checks(api_document_id);
CREATE INDEX idx_health_status ON api_health_checks(status);
CREATE INDEX idx_health_checked_at ON api_health_checks(checked_at);

-- OAuth2 相关表索引
CREATE INDEX idx_oauth2_state_auth_config_id ON oauth2_auth_states(auth_config_id);
CREATE INDEX idx_oauth2_state_user_id ON oauth2_auth_states(user_id);
CREATE INDEX idx_oauth2_state_state ON oauth2_auth_states(state);
CREATE INDEX idx_oauth2_state_expires_at ON oauth2_auth_states(expires_at);
CREATE INDEX idx_oauth2_state_created_at ON oauth2_auth_states(created_at);

CREATE INDEX idx_user_auth_user_id ON user_api_authorizations(user_id);
CREATE INDEX idx_user_auth_api_document_id ON user_api_authorizations(api_document_id);
CREATE INDEX idx_user_auth_auth_config_id ON user_api_authorizations(auth_config_id);
CREATE INDEX idx_user_auth_auth_id ON user_api_authorizations(auth_id);
CREATE INDEX idx_user_auth_provider_user_id ON user_api_authorizations(provider_user_id);
CREATE INDEX idx_user_auth_expires_at ON user_api_authorizations(expires_at);
CREATE INDEX idx_user_auth_is_active ON user_api_authorizations(is_active);
CREATE INDEX idx_user_auth_last_used_at ON user_api_authorizations(last_used_at);

CREATE INDEX idx_callback_auth_state_id ON oauth2_callback_logs(auth_state_id);
CREATE INDEX idx_callback_user_id ON oauth2_callback_logs(user_id);
CREATE INDEX idx_callback_code ON oauth2_callback_logs(callback_code);
CREATE INDEX idx_callback_state ON oauth2_callback_logs(callback_state);
CREATE INDEX idx_callback_status ON oauth2_callback_logs(callback_status);
CREATE INDEX idx_callback_created_at ON oauth2_callback_logs(created_at);

-- ========== 创建视图 ==========

-- 原有视图
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

CREATE VIEW auth_statistics AS
SELECT 
    ac.auth_type,
    COUNT(al.id) as total_attempts,
    SUM(CASE WHEN al.auth_status = 'success' THEN 1 ELSE 0 END) as success_count,
    SUM(CASE WHEN al.auth_status = 'failed' THEN 1 ELSE 0 END) as failure_count,
    AVG(al.response_time_ms) as avg_response_time,
    MAX(al.created_at) as last_attempt
FROM api_auth_configs ac
LEFT JOIN auth_logs al ON ac.id = al.auth_config_id
GROUP BY ac.auth_type;

CREATE VIEW auth_failures AS
SELECT 
    al.auth_type,
    al.error_message,
    COUNT(*) as failure_count,
    MAX(al.created_at) as last_failure
FROM auth_logs al
WHERE al.auth_status = 'failed'
GROUP BY al.auth_type, al.error_message
ORDER BY failure_count DESC;

-- OAuth2 相关视图
CREATE VIEW oauth2_authorization_summary AS
SELECT 
    uaa.user_id,
    u.username,
    uaa.api_document_id,
    d.name as api_name,
    uaa.auth_config_id,
    ac.auth_type,
    uaa.auth_id,
    uaa.provider_user_id,
    uaa.scope,
    uaa.is_active,
    uaa.expires_at,
    uaa.last_used_at,
    uaa.created_at
FROM user_api_authorizations uaa
JOIN gateway_users u ON uaa.user_id = u.id
JOIN api_documents d ON uaa.api_document_id = d.id
JOIN api_auth_configs ac ON uaa.auth_config_id = ac.id
WHERE ac.auth_type = 'oauth2';

CREATE VIEW oauth2_callback_statistics AS
SELECT 
    ocl.callback_status,
    COUNT(*) as total_callbacks,
    AVG(ocl.response_time_ms) as avg_response_time,
    MAX(ocl.created_at) as last_callback
FROM oauth2_callback_logs ocl
GROUP BY ocl.callback_status;

CREATE VIEW oauth2_active_authorizations AS
SELECT 
    uaa.id,
    u.username,
    d.name as api_name,
    uaa.auth_id,
    uaa.provider_user_id,
    uaa.scope,
    uaa.expires_at,
    uaa.last_used_at
FROM user_api_authorizations uaa
JOIN gateway_users u ON uaa.user_id = u.id
JOIN api_documents d ON uaa.api_document_id = d.id
JOIN api_auth_configs ac ON uaa.auth_config_id = ac.id
WHERE ac.auth_type = 'oauth2' 
  AND uaa.is_active = 1 
  AND (uaa.expires_at IS NULL OR uaa.expires_at > datetime('now'));

-- ========== 创建触发器 ==========

-- 原有表触发器
CREATE TRIGGER update_templates_updated_at 
    BEFORE UPDATE ON openapi_templates 
    FOR EACH ROW
BEGIN
    UPDATE openapi_templates SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER update_documents_updated_at 
    BEFORE UPDATE ON api_documents 
    FOR EACH ROW
BEGIN
    UPDATE api_documents SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER update_endpoints_updated_at 
    BEFORE UPDATE ON api_endpoints 
    FOR EACH ROW
BEGIN
    UPDATE api_endpoints SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER update_auth_configs_updated_at 
    BEFORE UPDATE ON api_auth_configs 
    FOR EACH ROW
BEGIN
    UPDATE api_auth_configs SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER update_credentials_updated_at 
    BEFORE UPDATE ON auth_credentials 
    FOR EACH ROW
BEGIN
    UPDATE auth_credentials SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON gateway_users 
    FOR EACH ROW
BEGIN
    UPDATE gateway_users SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER update_refs_updated_at 
    BEFORE UPDATE ON resource_references 
    FOR EACH ROW
BEGIN
    UPDATE resource_references SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- OAuth2 相关表触发器
CREATE TRIGGER update_user_auth_updated_at 
    BEFORE UPDATE ON user_api_authorizations 
    FOR EACH ROW
BEGIN
    UPDATE user_api_authorizations SET updated_at = datetime('now') WHERE id = NEW.id;
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

-- OAuth2 授权使用统计触发器
CREATE TRIGGER update_user_auth_last_used_trigger 
    AFTER INSERT ON api_call_logs 
    FOR EACH ROW
BEGIN
    UPDATE user_api_authorizations 
    SET last_used_at = datetime('now')
    WHERE id = (
        SELECT uaa.id 
        FROM user_api_authorizations uaa
        JOIN api_endpoints e ON uaa.api_document_id = e.api_document_id
        WHERE e.id = NEW.api_endpoint_id 
          AND uaa.is_active = 1
        LIMIT 1
    );
END;

-- ========== 插入示例数据 ==========

-- 插入示例数据
INSERT INTO openapi_templates (id, name, content, status, created_at, updated_at) VALUES
('template-1', 'Pet Store API', '{"openapi": "3.0.0", "info": {"title": "Pet Store API", "version": "1.0.0"}, "paths": {"/pets": {"get": {"summary": "List pets"}}}}', 'active', datetime('now'), datetime('now')),
('template-2', 'User Management API', '{"openapi": "3.0.0", "info": {"title": "User Management API", "version": "1.0.0"}, "paths": {"/users": {"get": {"summary": "List users"}}}}', 'active', datetime('now'), datetime('now')),
('template-3', 'OAuth2 API', '{"openapi": "3.0.0", "info": {"title": "OAuth2 Protected API", "version": "1.0.0"}, "paths": {"/profile": {"get": {"summary": "Get user profile"}}}}', 'active', datetime('now'), datetime('now'));

INSERT INTO api_documents (id, template_id, name, version, base_url, status, created_at, updated_at) VALUES
('doc-1', 'template-1', 'Pet Store API v1', '1.0.0', 'https://api.example.com', 'active', datetime('now'), datetime('now')),
('doc-2', 'template-2', 'User Management API v1', '1.0.0', 'https://api.example.com', 'active', datetime('now'), datetime('now')),
('doc-3', 'template-3', 'OAuth2 Protected API v1', '1.0.0', 'https://api.example.com', 'active', datetime('now'), datetime('now'));

INSERT INTO api_endpoints (id, api_document_id, path, method, operation_id, summary, status, created_at, updated_at) VALUES
('endpoint-1', 'doc-1', '/pets', 'GET', 'listPets', 'List all pets', 'active', datetime('now'), datetime('now')),
('endpoint-2', 'doc-1', '/pets', 'POST', 'createPet', 'Create a new pet', 'active', datetime('now'), datetime('now')),
('endpoint-3', 'doc-2', '/users', 'GET', 'listUsers', 'List all users', 'active', datetime('now'), datetime('now')),
('endpoint-4', 'doc-3', '/profile', 'GET', 'getProfile', 'Get user profile', 'active', datetime('now'), datetime('now'));

-- 插入认证配置示例（包含 OAuth2）
INSERT INTO api_auth_configs (id, api_document_id, auth_type, auth_config, is_required, status, created_at, updated_at) VALUES
('auth-1', 'doc-1', 'bearer', '{"token": "encrypted_token_123", "prefix": "Bearer", "header_name": "Authorization"}', 1, 'active', datetime('now'), datetime('now')),
('auth-2', 'doc-2', 'api_key', '{"key_name": "X-API-Key", "key_value": "encrypted_api_key_456", "location": "header"}', 1, 'active', datetime('now'), datetime('now')),
('auth-3', 'doc-3', 'oauth2', '{"grant_type": "authorization_code", "client_id": "oauth2_client_789", "client_secret": "encrypted_client_secret", "auth_url": "https://oauth.example.com/authorize", "token_url": "https://oauth.example.com/token", "redirect_uri": "https://gateway.example.com/auth/callback", "scope": "read profile"}', 1, 'active', datetime('now'), datetime('now'));

-- 插入认证凭据示例
INSERT INTO auth_credentials (id, auth_config_id, credential_type, credential_key, credential_value, is_encrypted, status, created_at, updated_at) VALUES
('cred-1', 'auth-1', 'static', 'bearer_token', 'encrypted_bearer_token_value', 1, 'active', datetime('now'), datetime('now')),
('cred-2', 'auth-2', 'static', 'api_key', 'encrypted_api_key_value', 1, 'active', datetime('now'), datetime('now'));

-- 插入 Gateway 用户示例
INSERT INTO gateway_users (id, username, email, password_hash, salt, role, permissions, is_active, created_at, updated_at) VALUES
('user-1', 'admin', 'admin@example.com', 'hashed_password_123', 'salt_123', 'admin', '{"all": true}', 1, datetime('now'), datetime('now')),
('user-2', 'api_user', 'api@example.com', 'hashed_password_456', 'salt_456', 'api_user', '{"api_access": true}', 1, datetime('now'), datetime('now')),
('user-3', 'oauth_user', 'oauth@example.com', 'hashed_password_789', 'salt_789', 'user', '{"oauth_access": true}', 1, datetime('now'), datetime('now'));

-- 插入示例日志
INSERT INTO api_call_logs (id, api_endpoint_id, request_method, request_url, request_headers, response_status_code, response_headers, response_body, response_time_ms, client_ip, created_at) VALUES
('log-1', 'endpoint-1', 'GET', 'https://api.example.com/pets', '{"Content-Type": "application/json", "Authorization": "Bearer token123"}', 200, '{"Content-Type": "application/json"}', '{"pets": []}', 150, '192.168.1.100', datetime('now')),
('log-2', 'endpoint-2', 'POST', 'https://api.example.com/pets', '{"Content-Type": "application/json", "Authorization": "Bearer token123"}', 201, '{"Content-Type": "application/json"}', '{"id": 1, "name": "Fluffy"}', 200, '192.168.1.100', datetime('now')),
('log-3', 'endpoint-3', 'GET', 'https://api.example.com/users', '{"Content-Type": "application/json", "X-API-Key": "key456"}', 200, '{"Content-Type": "application/json"}', '{"users": []}', 120, '192.168.1.101', datetime('now'));

-- 插入认证日志示例
INSERT INTO auth_logs (id, auth_config_id, auth_type, auth_status, auth_method, response_time_ms, client_ip, created_at) VALUES
('auth-log-1', 'auth-1', 'bearer', 'success', 'static', 50, '192.168.1.100', datetime('now')),
('auth-log-2', 'auth-2', 'api_key', 'success', 'static', 30, '192.168.1.101', datetime('now'));

-- 插入 OAuth2 示例数据
INSERT INTO oauth2_auth_states (id, auth_config_id, user_id, state, code_verifier, code_challenge, code_challenge_method, redirect_uri, scope, client_id, expires_at, created_at) VALUES
('state-1', 'auth-3', 'user-3', 'random_state_123', 'code_verifier_456', 'code_challenge_789', 'S256', 'https://gateway.example.com/auth/callback', 'read profile', 'oauth2_client_789', datetime('now', '+10 minutes'), datetime('now'));

INSERT INTO user_api_authorizations (id, user_id, api_document_id, auth_config_id, access_token, refresh_token, token_type, expires_at, scope, auth_id, provider_user_id, is_active, created_at, updated_at) VALUES
('auth-session-1', 'user-3', 'doc-3', 'auth-3', 'encrypted_access_token_123', 'encrypted_refresh_token_456', 'Bearer', datetime('now', '+1 hour'), 'read profile', 'oauth_user_789', 'provider_user_123', 1, datetime('now'), datetime('now'));

INSERT INTO oauth2_callback_logs (id, auth_state_id, user_id, callback_code, callback_state, token_response, auth_id, provider_user_id, client_ip, callback_status, response_time_ms, created_at) VALUES
('callback-1', 'state-1', 'user-3', 'auth_code_123', 'random_state_123', 'encrypted_token_response', 'oauth_user_789', 'provider_user_123', '192.168.1.102', 'success', 250, datetime('now'));

-- 显示创建结果
SELECT 'Database with OAuth2 callback support created successfully!' as message;
SELECT COUNT(*) as template_count FROM openapi_templates;
SELECT COUNT(*) as document_count FROM api_documents;
SELECT COUNT(*) as endpoint_count FROM api_endpoints;
SELECT COUNT(*) as auth_config_count FROM api_auth_configs;
SELECT COUNT(*) as credential_count FROM auth_credentials;
SELECT COUNT(*) as user_count FROM gateway_users;
SELECT COUNT(*) as log_count FROM api_call_logs;
SELECT COUNT(*) as auth_log_count FROM auth_logs;
SELECT COUNT(*) as oauth2_state_count FROM oauth2_auth_states;
SELECT COUNT(*) as user_auth_count FROM user_api_authorizations;
SELECT COUNT(*) as callback_log_count FROM oauth2_callback_logs; 