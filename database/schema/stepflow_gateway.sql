-- StepFlow Gateway 数据库模式

-- API 规范模板表
CREATE TABLE IF NOT EXISTS api_spec_templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    spec_type TEXT NOT NULL,  -- openapi, asyncapi, graphql, etc.
    content TEXT NOT NULL,
    version TEXT,
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- API 文档表
CREATE TABLE IF NOT EXISTS api_documents (
    id TEXT PRIMARY KEY,
    template_id TEXT NOT NULL,
    name TEXT NOT NULL,
    spec_type TEXT NOT NULL,  -- openapi, asyncapi, graphql, etc.
    version TEXT,
    base_url TEXT,
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (template_id) REFERENCES api_spec_templates(id)
);

-- 端点表
CREATE TABLE IF NOT EXISTS api_endpoints (
    id TEXT PRIMARY KEY,
    api_document_id TEXT NOT NULL,
    endpoint_name TEXT NOT NULL,  -- path for OpenAPI, channel for AsyncAPI
    endpoint_type TEXT NOT NULL,  -- http, mqtt, kafka, websocket, etc.
    method TEXT,                  -- HTTP method for REST APIs
    operation_type TEXT,          -- get, post, publish, subscribe, etc.
    description TEXT,
    parameters TEXT,              -- JSON
    request_schema TEXT,          -- JSON
    response_schema TEXT,         -- JSON
    security TEXT,                -- JSON
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (api_document_id) REFERENCES api_documents(id)
);

-- 协议配置表
CREATE TABLE IF NOT EXISTS protocol_configs (
    id TEXT PRIMARY KEY,
    api_document_id TEXT NOT NULL,
    protocol_name TEXT NOT NULL,
    protocol_type TEXT NOT NULL,  -- http, mqtt, kafka, amqp, etc.
    config TEXT NOT NULL,         -- JSON
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (api_document_id) REFERENCES api_documents(id)
);

-- API 调用日志表
CREATE TABLE IF NOT EXISTS api_call_logs (
    id TEXT PRIMARY KEY,
    endpoint_id TEXT NOT NULL,
    operation_type TEXT NOT NULL,
    request_data TEXT,            -- JSON
    response_data TEXT,           -- JSON
    protocol_type TEXT NOT NULL,
    status TEXT NOT NULL,         -- success/error
    error_message TEXT,
    response_time_ms INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY (endpoint_id) REFERENCES api_endpoints(id)
);

-- 用户表
CREATE TABLE IF NOT EXISTS gateway_users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    permissions TEXT,             -- JSON
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 会话表
CREATE TABLE IF NOT EXISTS gateway_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    session_token TEXT UNIQUE NOT NULL,
    expires_at TEXT NOT NULL,
    client_info TEXT,             -- JSON
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES gateway_users(id)
);

-- API 认证配置表
CREATE TABLE IF NOT EXISTS api_auth_configs (
    id TEXT PRIMARY KEY,
    api_document_id TEXT NOT NULL,
    auth_type TEXT NOT NULL,      -- basic, bearer, api_key, oauth2
    auth_config TEXT NOT NULL,    -- JSON
    is_required INTEGER DEFAULT 1,
    is_global INTEGER DEFAULT 0,
    priority INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (api_document_id) REFERENCES api_documents(id)
);

-- 认证凭据表
CREATE TABLE IF NOT EXISTS auth_credentials (
    id TEXT PRIMARY KEY,
    auth_config_id TEXT NOT NULL,
    credential_type TEXT NOT NULL, -- username_password, token, api_key
    credential_data TEXT NOT NULL, -- JSON (encrypted)
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (auth_config_id) REFERENCES api_auth_configs(id)
);

-- 认证日志表
CREATE TABLE IF NOT EXISTS auth_logs (
    id TEXT PRIMARY KEY,
    auth_config_id TEXT NOT NULL,
    user_id TEXT,
    auth_type TEXT NOT NULL,
    auth_status TEXT NOT NULL,    -- success, failed
    auth_method TEXT NOT NULL,    -- static, dynamic, user_auth
    response_time_ms INTEGER,
    client_ip TEXT,
    error_message TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (auth_config_id) REFERENCES api_auth_configs(id),
    FOREIGN KEY (user_id) REFERENCES gateway_users(id)
);

-- OAuth2 授权状态表
CREATE TABLE IF NOT EXISTS oauth2_auth_states (
    id TEXT PRIMARY KEY,
    auth_config_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    api_document_id TEXT NOT NULL,
    state TEXT NOT NULL,
    code_verifier TEXT NOT NULL,
    code_challenge TEXT NOT NULL,
    code_challenge_method TEXT DEFAULT 'S256',
    redirect_uri TEXT NOT NULL,
    scope TEXT,
    response_type TEXT DEFAULT 'code',
    client_id TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (auth_config_id) REFERENCES api_auth_configs(id),
    FOREIGN KEY (user_id) REFERENCES gateway_users(id),
    FOREIGN KEY (api_document_id) REFERENCES api_documents(id)
);

-- 用户 API 授权表
CREATE TABLE IF NOT EXISTS user_api_authorizations (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    api_document_id TEXT NOT NULL,
    auth_config_id TEXT NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_type TEXT DEFAULT 'Bearer',
    expires_at TEXT NOT NULL,
    scope TEXT,
    auth_id TEXT,
    provider_user_id TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES gateway_users(id),
    FOREIGN KEY (api_document_id) REFERENCES api_documents(id),
    FOREIGN KEY (auth_config_id) REFERENCES api_auth_configs(id)
);

-- OAuth2 回调日志表
CREATE TABLE IF NOT EXISTS oauth2_callback_logs (
    id TEXT PRIMARY KEY,
    auth_state_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    callback_code TEXT NOT NULL,
    callback_state TEXT NOT NULL,
    token_response TEXT NOT NULL, -- JSON
    auth_id TEXT,
    provider_user_id TEXT,
    client_ip TEXT,
    callback_status TEXT NOT NULL, -- success, failed
    response_time_ms INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY (auth_state_id) REFERENCES oauth2_auth_states(id),
    FOREIGN KEY (user_id) REFERENCES gateway_users(id)
);

-- 资源引用表
CREATE TABLE IF NOT EXISTS resource_references (
    id TEXT PRIMARY KEY,
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    api_endpoint_id TEXT NOT NULL,
    display_name TEXT,
    description TEXT,
    reference_config TEXT,        -- JSON
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (api_endpoint_id) REFERENCES api_endpoints(id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_api_documents_status ON api_documents(status);
CREATE INDEX IF NOT EXISTS idx_api_endpoints_document_id ON api_endpoints(api_document_id);
CREATE INDEX IF NOT EXISTS idx_api_call_logs_endpoint_id ON api_call_logs(endpoint_id);
CREATE INDEX IF NOT EXISTS idx_api_call_logs_created_at ON api_call_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_gateway_users_username ON gateway_users(username);
CREATE INDEX IF NOT EXISTS idx_gateway_users_email ON gateway_users(email);
CREATE INDEX IF NOT EXISTS idx_gateway_sessions_token ON gateway_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_gateway_sessions_user_id ON gateway_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_api_auth_configs_document_id ON api_auth_configs(api_document_id);
CREATE INDEX IF NOT EXISTS idx_auth_logs_config_id ON auth_logs(auth_config_id);
CREATE INDEX IF NOT EXISTS idx_auth_logs_created_at ON auth_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_oauth2_auth_states_state ON oauth2_auth_states(state);
CREATE INDEX IF NOT EXISTS idx_oauth2_auth_states_user_id ON oauth2_auth_states(user_id);
CREATE INDEX IF NOT EXISTS idx_user_api_authorizations_user_id ON user_api_authorizations(user_id);
CREATE INDEX IF NOT EXISTS idx_user_api_authorizations_document_id ON user_api_authorizations(api_document_id);
CREATE INDEX IF NOT EXISTS idx_resource_references_type_id ON resource_references(resource_type, resource_id); 