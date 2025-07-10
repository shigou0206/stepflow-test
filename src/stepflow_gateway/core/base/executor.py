"""
执行器抽象基类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging
import time
from datetime import datetime


class BaseExecutor(ABC):
    """执行器抽象基类"""
    
    def __init__(self, db_manager=None, auth_manager=None):
        self.db_manager = db_manager
        self.auth_manager = auth_manager
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def execute(self, endpoint_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行 API 调用"""
        pass
    
    @abstractmethod
    def get_supported_protocols(self) -> List[str]:
        """获取支持的协议"""
        pass
    
    def get_endpoint(self, endpoint_id: str) -> Optional[Dict[str, Any]]:
        """获取端点信息"""
        if not self.db_manager:
            return None
        
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute('''
                    SELECT * FROM api_endpoints WHERE id = ?
                ''', (endpoint_id,))
                
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            self.logger.error(f"Failed to get endpoint {endpoint_id}: {e}")
            return None
    
    def get_api_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """获取 API 文档信息"""
        if not self.db_manager:
            return None
        
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute('''
                    SELECT * FROM api_documents WHERE id = ?
                ''', (document_id,))
                
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            self.logger.error(f"Failed to get API document {document_id}: {e}")
            return None
    
    def log_api_call(self, endpoint_id: str, request_data: Dict[str, Any], 
                    response_data: Dict[str, Any], response_time_ms: int):
        """记录 API 调用日志"""
        if not self.db_manager:
            return
        
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute('''
                    INSERT INTO api_call_logs 
                    (id, endpoint_id, operation_type, request_data, response_data, 
                     protocol_type, status, error_message, response_time_ms, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    self._generate_id(),
                    endpoint_id,
                    request_data.get('operation_type', 'unknown'),
                    self._serialize_data(request_data),
                    self._serialize_data(response_data),
                    request_data.get('protocol_type', 'unknown'),
                    'success' if response_data.get('success', False) else 'error',
                    response_data.get('error', ''),
                    response_time_ms,
                    datetime.now().isoformat()
                ))
        except Exception as e:
            self.logger.error(f"Failed to log API call: {e}")
    
    def handle_authentication(self, endpoint_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理认证"""
        if not self.auth_manager:
            return {'success': True, 'auth_headers': {}}
        
        try:
            endpoint = self.get_endpoint(endpoint_id)
            if not endpoint:
                return {'success': False, 'error': 'Endpoint not found'}
            
            document_id = endpoint.get('api_document_id')
            if not document_id:
                return {'success': False, 'error': 'API document not found'}
            
            return self.auth_manager.handle_api_authentication(document_id, request_data)
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def validate_request_data(self, endpoint: Dict[str, Any], request_data: Dict[str, Any]) -> bool:
        """验证请求数据"""
        # 这里可以实现请求数据验证逻辑
        # 暂时返回 True，后续可以实现具体的验证
        return True
    
    def build_request(self, endpoint: Dict[str, Any], request_data: Dict[str, Any]) -> Dict[str, Any]:
        """构建请求"""
        # 这里可以实现请求构建逻辑
        # 子类可以重写此方法
        return {
            'endpoint': endpoint,
            'request_data': request_data,
            'timestamp': datetime.now().isoformat()
        }
    
    def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """处理响应"""
        # 这里可以实现响应处理逻辑
        # 子类可以重写此方法
        return response
    
    def _generate_id(self) -> str:
        """生成唯一 ID"""
        import uuid
        return str(uuid.uuid4())
    
    def _serialize_data(self, data: Dict[str, Any]) -> str:
        """序列化数据为 JSON 字符串"""
        import json
        try:
            return json.dumps(data, ensure_ascii=False)
        except Exception:
            return str(data)
    
    def _deserialize_data(self, data_str: str) -> Dict[str, Any]:
        """反序列化 JSON 字符串为数据"""
        import json
        try:
            return json.loads(data_str)
        except Exception:
            return {}
    
    def get_protocol_adapter(self, protocol_type: str):
        """获取协议适配器"""
        # 这里可以实现协议适配器获取逻辑
        # 子类可以重写此方法
        return None
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取执行器指标"""
        return {
            'executor_type': self.__class__.__name__,
            'supported_protocols': self.get_supported_protocols(),
            'timestamp': datetime.now().isoformat()
        } 