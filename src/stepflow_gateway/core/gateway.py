"""
StepFlow Gateway 主类
"""

import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

from .config import GatewayConfig, load_config
from .registry import ApiSpecRegistry
from ..database.manager import DatabaseManager
from ..auth.manager import AuthManager
from ..api.manager import ApiManager
from ..plugins import register_plugins


class StepFlowGateway:
    """StepFlow Gateway 主类"""
    
    def __init__(self, config: Optional[GatewayConfig] = None):
        self.config = config or load_config()
        self.logger = self._setup_logging()
        
        # 初始化插件注册器
        self.registry = ApiSpecRegistry()
        
        # 注册插件
        register_plugins(self.registry)
        
        # 初始化组件
        self.db_manager = DatabaseManager(self.config.database)
        self.auth_manager = AuthManager(self.db_manager, self.config.auth, self.config.oauth2)
        self.api_manager = ApiManager(self.db_manager, self.auth_manager)
        
        self.logger.info("StepFlow Gateway 初始化完成")
    
    def _setup_logging(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger('stepflow_gateway')
        logger.setLevel(getattr(logging, self.config.logging.level))
        
        # 创建格式化器
        formatter = logging.Formatter(self.config.logging.format)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 文件处理器（如果配置了）
        if self.config.logging.file_path:
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                self.config.logging.file_path,
                maxBytes=self.config.logging.max_bytes,
                backupCount=self.config.logging.backup_count
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def initialize(self):
        """初始化 Gateway"""
        try:
            self.logger.info("开始初始化 StepFlow Gateway...")
            
            # 初始化数据库
            self.db_manager.initialize()
            self.logger.info("数据库初始化完成")
            
            # 创建默认用户（如果不存在）
            self._create_default_users()
            
            self.logger.info("StepFlow Gateway 初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"Gateway 初始化失败: {e}")
            return False
    
    def _create_default_users(self):
        """创建默认用户"""
        try:
            # 检查是否已有管理员用户
            admin_user = self.db_manager.get_user(username='admin')
            if not admin_user:
                # 创建管理员用户
                password_hash, salt = self.auth_manager.hash_password('admin123')
                self.db_manager.create_user(
                    username='admin',
                    email='admin@stepflow.local',
                    password_hash=password_hash,
                    role='admin',
                    permissions={'all': True}
                )
                self.logger.info("创建默认管理员用户: admin/admin123")
            
            # 检查是否已有API用户
            api_user = self.db_manager.get_user(username='api_user')
            if not api_user:
                # 创建API用户
                password_hash, salt = self.auth_manager.hash_password('api123')
                self.db_manager.create_user(
                    username='api_user',
                    email='api@stepflow.local',
                    password_hash=password_hash,
                    role='api_user',
                    permissions={'api_access': True}
                )
                self.logger.info("创建默认API用户: api_user/api123")
                
        except Exception as e:
            self.logger.warning(f"创建默认用户失败: {e}")
    
    # API 文档管理
    def register_api(self, name: str, content: str, spec_type: str = "openapi", version: str = None, 
                    base_url: str = None) -> Dict[str, Any]:
        """注册 API"""
        try:
            # 检查是否支持该规范类型
            if spec_type not in self.registry.list_specs():
                return {
                    'success': False,
                    'error': f"不支持的规范类型: {spec_type}"
                }
            
            # 根据规范类型选择不同的处理方式
            if spec_type == "openapi":
                result = self.api_manager.register_api(name, content, version, base_url)
            elif spec_type == "asyncapi":
                result = self._register_asyncapi(name, content, version, base_url)
            else:
                return {
                    'success': False,
                    'error': f"不支持的规范类型: {spec_type}"
                }
            
            if result['success']:
                self.logger.info(f"API注册成功: {name} (ID: {result['document_id']})")
            else:
                self.logger.error(f"API注册失败: {result['error']}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"API注册异常: {e}")
            return {'success': False, 'error': str(e)}
    
    def _register_asyncapi(self, name: str, content: str, version: str = None, 
                          base_url: str = None) -> Dict[str, Any]:
        """注册 AsyncAPI 文档"""
        try:
            # 获取 AsyncAPI 解析器
            parser_class = self.registry.get_parser("asyncapi")
            if not parser_class:
                return {
                    'success': False,
                    'error': "AsyncAPI 解析器未注册"
                }
            
            # 解析 AsyncAPI 文档
            parser = parser_class()
            spec = parser.parse(content, name=name)
            
            # 验证规范
            if not spec.validate():
                return {
                    'success': False,
                    'error': "AsyncAPI 规范验证失败"
                }
            
            # 保存到数据库
            template_id = self._save_asyncapi_template(name, content)
            document_id = self._save_asyncapi_document(template_id, name, version, base_url, spec)
            endpoints = self._extract_and_save_asyncapi_endpoints(spec, document_id)
            
            return {
                'success': True,
                'template_id': template_id,
                'document_id': document_id,
                'endpoints': endpoints
            }
            
        except Exception as e:
            self.logger.error(f"AsyncAPI 注册失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _save_asyncapi_template(self, name: str, content: str) -> str:
        """保存 AsyncAPI 模板"""
        return self.db_manager.create_api_spec_template(
            name=name,
            content=content,
            spec_type="asyncapi"
        )
    
    def _save_asyncapi_document(self, template_id: str, name: str, version: str, 
                               base_url: str, spec) -> str:
        """保存 AsyncAPI 文档"""
        return self.db_manager.create_api_document(
            template_id=template_id,
            name=name,
            version=version or spec.version,
            base_url=base_url,
            spec_type="asyncapi",
            status="active"
        )
    
    def _extract_and_save_asyncapi_endpoints(self, spec, document_id: str) -> List[Dict[str, Any]]:
        """提取并保存 AsyncAPI 端点"""
        endpoints = spec.extract_endpoints(spec.content)
        saved_endpoints = []
        
        for endpoint in endpoints:
            endpoint_id = self.db_manager.create_api_endpoint(
                api_document_id=document_id,
                path=endpoint.get('channel_name', ''),
                method=endpoint.get('method', ''),
                summary=endpoint.get('description', ''),
                description=endpoint.get('description', ''),
                parameters=endpoint.get('parameters', []),
                request_body=endpoint.get('request_schema', {}),
                responses=endpoint.get('response_schema', {}),
                tags=endpoint.get('tags', []),
                operation_id=endpoint.get('operation_id', ''),
                security=endpoint.get('security', []),
                spec_type="asyncapi",
                operation_type=endpoint.get('operation_type', ''),
                protocol=endpoint.get('protocol', ''),
                channel_name=endpoint.get('channel_name', '')
            )
            saved_endpoints.append({
                'id': endpoint_id,
                'path': endpoint.get('channel_name', ''),
                'method': endpoint.get('method', ''),
                'description': endpoint.get('description', '')
            })
        
        return saved_endpoints
    
    def get_api(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """获取 API 信息"""
        return self.api_manager.get_api(doc_id)
    
    def list_apis(self, status: str = 'active') -> List[Dict[str, Any]]:
        """列出所有 API"""
        return self.api_manager.list_apis(status)
    
    def delete_api(self, doc_id: str) -> bool:
        """删除 API"""
        success = self.api_manager.delete_api(doc_id)
        if success:
            self.logger.info(f"API删除成功: {doc_id}")
        else:
            self.logger.warning(f"API删除失败: {doc_id}")
        return success
    
    # API 端点管理
    def get_endpoint(self, endpoint_id: str) -> Optional[Dict[str, Any]]:
        """获取端点信息"""
        return self.api_manager.get_endpoint(endpoint_id)
    
    def list_endpoints(self, api_document_id: str = None) -> List[Dict[str, Any]]:
        """列出端点"""
        return self.api_manager.list_endpoints(api_document_id)
    
    def find_endpoint(self, path: str, method: str, api_document_id: str = None) -> Optional[Dict[str, Any]]:
        """查找端点"""
        # 通过列出端点并匹配来查找
        endpoints = self.api_manager.list_endpoints(api_document_id)
        for endpoint in endpoints:
            if endpoint['path'] == path and endpoint['method'] == method:
                return endpoint
        return None
    
    # API 调用
    def call_api(self, endpoint_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """调用 API"""
        try:
            start_time = time.time()
            
            # 调用 API
            result = self.api_manager.call_api(endpoint_id, request_data)
            
            # 记录调用时间
            call_time = time.time() - start_time
            self.logger.info(f"API调用完成: {endpoint_id}, 耗时: {call_time:.3f}s")
            
            return result
            
        except Exception as e:
            self.logger.error(f"API调用异常: {e}")
            return {'success': False, 'error': str(e)}
    
    def call_api_by_path(self, path: str, method: str, request_data: Dict[str, Any], 
                        api_document_id: str = None) -> Dict[str, Any]:
        """通过路径调用 API"""
        try:
            # 直接使用 ApiManager 的 call_api_by_path 方法
            return self.api_manager.call_api_by_path(path, method, request_data, api_document_id)
            
        except Exception as e:
            self.logger.error(f"通过路径调用API异常: {e}")
            return {'success': False, 'error': str(e)}
    
    # 认证管理
    def add_auth_config(self, api_document_id: str, auth_type: str, auth_config: Dict[str, Any],
                       is_required: bool = True, is_global: bool = False, priority: int = 0) -> str:
        """添加认证配置"""
        auth_config_id = self.api_manager.add_auth_config(
            api_document_id, auth_type, auth_config, is_required, is_global, priority
        )
        self.logger.info(f"添加认证配置: {auth_type} -> {api_document_id}")
        return auth_config_id
    
    def get_auth_config(self, auth_config_id: str) -> Optional[Dict[str, Any]]:
        """获取认证配置"""
        return self.api_manager.get_auth_config(auth_config_id)
    
    def list_auth_configs(self, api_document_id: str = None, auth_type: str = None) -> List[Dict[str, Any]]:
        """列出认证配置"""
        return self.api_manager.list_auth_configs(api_document_id, auth_type)
    
    def update_auth_config(self, auth_config_id: str, **kwargs) -> bool:
        """更新认证配置"""
        success = self.api_manager.update_auth_config(auth_config_id, **kwargs)
        if success:
            self.logger.info(f"更新认证配置: {auth_config_id}")
        return success
    
    def delete_auth_config(self, auth_config_id: str) -> bool:
        """删除认证配置"""
        success = self.api_manager.delete_auth_config(auth_config_id)
        if success:
            self.logger.info(f"删除认证配置: {auth_config_id}")
        return success
    
    # 用户管理
    def create_user(self, username: str, email: str, password: str, 
                   role: str = 'user', permissions: Dict[str, Any] = None) -> str:
        """创建用户"""
        try:
            password_hash, salt = self.auth_manager.hash_password(password)
            user_id = self.db_manager.create_user(
                username, email, password_hash, role, permissions, salt=salt
            )
            self.logger.info(f"创建用户: {username}")
            return user_id
            
        except Exception as e:
            self.logger.error(f"创建用户失败: {e}")
            raise
    
    def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """用户认证"""
        return self.auth_manager.authenticate_basic(username, password)
    
    def get_user(self, user_id: str = None, username: str = None, email: str = None) -> Optional[Dict[str, Any]]:
        """获取用户"""
        return self.db_manager.get_user(user_id, username, email)
    
    def list_users(self, role: str = None, is_active: bool = True) -> List[Dict[str, Any]]:
        """列出用户"""
        return self.db_manager.list_users(role, is_active)
    
    # OAuth2 支持
    def create_oauth2_auth_url(self, user_id: str, api_document_id: str) -> Dict[str, Any]:
        """创建 OAuth2 认证 URL"""
        try:
            # 获取 OAuth2 认证配置
            auth_configs = self.api_manager.list_auth_configs(api_document_id, 'oauth2')
            if not auth_configs:
                return {'success': False, 'error': 'No OAuth2 configuration found'}
            
            auth_config = auth_configs[0]  # 使用第一个 OAuth2 配置
            
            # 创建授权状态
            auth_state = self.auth_manager.create_oauth2_auth_state(user_id, api_document_id, auth_config)
            
            # 生成认证 URL
            config = auth_config['auth_config']
            params = {
                'response_type': 'code',
                'client_id': config['client_id'],
                'redirect_uri': config['redirect_uri'],
                'scope': config.get('scope', 'read'),
                'state': auth_state['state'],
                'code_challenge': auth_state['code_challenge'],
                'code_challenge_method': 'S256'
            }
            
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            auth_url = f"{config['auth_url']}?{query_string}"
            
            return {
                'success': True,
                'auth_url': auth_url,
                'state_id': auth_state['id'],
                'state': auth_state['state']
            }
            
        except Exception as e:
            self.logger.error(f"创建OAuth2认证URL失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def handle_oauth2_callback(self, auth_state_id: str, callback_code: str, callback_state: str) -> Dict[str, Any]:
        """处理 OAuth2 回调"""
        return self.auth_manager.handle_oauth2_callback(auth_state_id, callback_code, callback_state)
    
    # 资源引用管理
    def create_resource_reference(self, resource_type: str, resource_id: str, 
                                api_endpoint_id: str, display_name: str = None,
                                description: str = None, reference_config: Dict[str, Any] = None) -> str:
        """创建资源引用"""
        ref_id = self.api_manager.create_resource_reference(
            resource_type, resource_id, api_endpoint_id, display_name, description, reference_config
        )
        self.logger.info(f"创建资源引用: {resource_type}:{resource_id}")
        return ref_id
    
    def get_resource_references(self, resource_type: str = None, resource_id: str = None) -> List[Dict[str, Any]]:
        """获取资源引用"""
        return self.api_manager.get_resource_references(resource_type, resource_id)
    
    # 监控和统计
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.api_manager.get_api_statistics()
    
    def get_endpoint_statistics(self, endpoint_id: str) -> Dict[str, Any]:
        """获取端点统计"""
        return self.api_manager.get_endpoint_statistics(endpoint_id)
    
    def get_recent_calls(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的调用"""
        return self.api_manager.get_recent_api_calls(limit)
    
    def get_error_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取错误日志"""
        return self.api_manager.get_error_logs(limit)
    
    def check_health(self, api_document_id: str) -> Dict[str, Any]:
        """健康检查"""
        return self.api_manager.check_api_health(api_document_id)
    
    # 会话管理
    def create_session(self, user_id: str, client_info: Dict[str, Any] = None) -> str:
        """创建会话"""
        return self.auth_manager.create_session(user_id, client_info)
    
    def validate_session(self, session_token: str) -> Dict[str, Any]:
        """验证会话"""
        return self.auth_manager.authenticate_bearer(session_token)
    
    def invalidate_session(self, session_token: str) -> bool:
        """使会话失效"""
        return self.auth_manager.invalidate_session(session_token)
    
    # 工具方法
    def get_config(self) -> GatewayConfig:
        """获取配置"""
        return self.config
    
    def update_config(self, new_config: GatewayConfig):
        """更新配置"""
        self.config = new_config
        self.logger.info("配置已更新")
    
    def close(self):
        """关闭 Gateway"""
        try:
            self.db_manager.close()
            self.logger.info("StepFlow Gateway 已关闭")
        except Exception as e:
            self.logger.error(f"关闭Gateway时出错: {e}")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close() 