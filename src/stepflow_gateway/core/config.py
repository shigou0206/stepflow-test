"""
Gateway 配置管理模块
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class DatabaseConfig:
    """数据库配置"""
    path: str = "stepflow_gateway.db"
    timeout: int = 30
    check_same_thread: bool = False
    isolation_level: Optional[str] = None


@dataclass
class AuthConfig:
    """认证配置"""
    secret_key: str = "your-secret-key-change-in-production"
    token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    bcrypt_rounds: int = 12
    jwt_algorithm: str = "HS256"


@dataclass
class OAuth2Config:
    """OAuth2配置"""
    state_expire_minutes: int = 10
    pkce_enabled: bool = True
    default_scope: str = "read"
    callback_timeout: int = 30


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5


@dataclass
class GatewayConfig:
    """Gateway 主配置"""
    # 基础配置
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # 组件配置
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
    oauth2: OAuth2Config = field(default_factory=OAuth2Config)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    # 功能开关
    enable_cors: bool = True
    enable_rate_limit: bool = True
    enable_health_check: bool = True
    
    # 缓存配置
    cache_enabled: bool = True
    cache_ttl: int = 300  # 5分钟
    
    # 安全配置
    allowed_hosts: list = field(default_factory=lambda: ["*"])
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    
    @classmethod
    def from_file(cls, config_path: str) -> "GatewayConfig":
        """从配置文件加载配置"""
        config_file = Path(config_path)
        if not config_file.exists():
            return cls()
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        return cls.from_dict(config_data)
    
    @classmethod
    def from_dict(cls, config_data: Dict[str, Any]) -> "GatewayConfig":
        """从字典创建配置"""
        # 处理嵌套配置
        database_config = DatabaseConfig(**config_data.get('database', {}))
        auth_config = AuthConfig(**config_data.get('auth', {}))
        oauth2_config = OAuth2Config(**config_data.get('oauth2', {}))
        logging_config = LoggingConfig(**config_data.get('logging', {}))
        
        # 创建主配置
        return cls(
            host=config_data.get('host', '0.0.0.0'),
            port=config_data.get('port', 8000),
            debug=config_data.get('debug', False),
            database=database_config,
            auth=auth_config,
            oauth2=oauth2_config,
            logging=logging_config,
            enable_cors=config_data.get('enable_cors', True),
            enable_rate_limit=config_data.get('enable_rate_limit', True),
            enable_health_check=config_data.get('enable_health_check', True),
            cache_enabled=config_data.get('cache_enabled', True),
            cache_ttl=config_data.get('cache_ttl', 300),
            allowed_hosts=config_data.get('allowed_hosts', ["*"]),
            max_request_size=config_data.get('max_request_size', 10 * 1024 * 1024)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'host': self.host,
            'port': self.port,
            'debug': self.debug,
            'database': {
                'path': self.database.path,
                'timeout': self.database.timeout,
                'check_same_thread': self.database.check_same_thread,
                'isolation_level': self.database.isolation_level
            },
            'auth': {
                'secret_key': self.auth.secret_key,
                'token_expire_minutes': self.auth.token_expire_minutes,
                'refresh_token_expire_days': self.auth.refresh_token_expire_days,
                'bcrypt_rounds': self.auth.bcrypt_rounds,
                'jwt_algorithm': self.auth.jwt_algorithm
            },
            'oauth2': {
                'state_expire_minutes': self.oauth2.state_expire_minutes,
                'pkce_enabled': self.oauth2.pkce_enabled,
                'default_scope': self.oauth2.default_scope,
                'callback_timeout': self.oauth2.callback_timeout
            },
            'logging': {
                'level': self.logging.level,
                'format': self.logging.format,
                'file_path': self.logging.file_path,
                'max_bytes': self.logging.max_bytes,
                'backup_count': self.logging.backup_count
            },
            'enable_cors': self.enable_cors,
            'enable_rate_limit': self.enable_rate_limit,
            'enable_health_check': self.enable_health_check,
            'cache_enabled': self.cache_enabled,
            'cache_ttl': self.cache_ttl,
            'allowed_hosts': self.allowed_hosts,
            'max_request_size': self.max_request_size
        }
    
    def save_to_file(self, config_path: str):
        """保存配置到文件"""
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def from_env(cls) -> "GatewayConfig":
        """从环境变量加载配置"""
        config = cls()
        
        # 基础配置
        if os.getenv('GATEWAY_HOST'):
            config.host = os.getenv('GATEWAY_HOST')
        if os.getenv('GATEWAY_PORT'):
            config.port = int(os.getenv('GATEWAY_PORT'))
        if os.getenv('GATEWAY_DEBUG'):
            config.debug = os.getenv('GATEWAY_DEBUG').lower() == 'true'
        
        # 数据库配置
        if os.getenv('DATABASE_PATH'):
            config.database.path = os.getenv('DATABASE_PATH')
        
        # 认证配置
        if os.getenv('AUTH_SECRET_KEY'):
            config.auth.secret_key = os.getenv('AUTH_SECRET_KEY')
        if os.getenv('AUTH_TOKEN_EXPIRE_MINUTES'):
            config.auth.token_expire_minutes = int(os.getenv('AUTH_TOKEN_EXPIRE_MINUTES'))
        
        # OAuth2配置
        if os.getenv('OAUTH2_STATE_EXPIRE_MINUTES'):
            config.oauth2.state_expire_minutes = int(os.getenv('OAUTH2_STATE_EXPIRE_MINUTES'))
        if os.getenv('OAUTH2_PKCE_ENABLED'):
            config.oauth2.pkce_enabled = os.getenv('OAUTH2_PKCE_ENABLED').lower() == 'true'
        
        # 日志配置
        if os.getenv('LOG_LEVEL'):
            config.logging.level = os.getenv('LOG_LEVEL')
        if os.getenv('LOG_FILE_PATH'):
            config.logging.file_path = os.getenv('LOG_FILE_PATH')
        
        return config


def load_config(config_path: Optional[str] = None) -> GatewayConfig:
    """加载配置"""
    if config_path:
        return GatewayConfig.from_file(config_path)
    
    # 尝试从默认位置加载
    default_config_paths = [
        "config/gateway.json",
        "gateway.json",
        ".env"
    ]
    
    for path in default_config_paths:
        if Path(path).exists():
            if path.endswith('.env'):
                return GatewayConfig.from_env()
            else:
                return GatewayConfig.from_file(path)
    
    # 使用默认配置
    return GatewayConfig() 