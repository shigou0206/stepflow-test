"""
OpenAPI 规范实现
"""

from typing import Dict, Any, List, Optional
from ...core.base.api_spec import ApiSpecification


class OpenApiSpecification(ApiSpecification):
    """OpenAPI 规范实现"""
    
    @property
    def spec_type(self) -> str:
        return "openapi"
    
    @property
    def version(self) -> str:
        return "3.0.0"
    
    def validate(self, content: str) -> bool:
        """验证 OpenAPI 规范内容"""
        try:
            import json
            doc = json.loads(content)
            
            # 基本验证
            if 'openapi' not in doc:
                return False
            
            if 'info' not in doc:
                return False
            
            if 'paths' not in doc:
                return False
            
            # 验证版本
            openapi_version = doc['openapi']
            if not openapi_version.startswith('3.'):
                return False
            
            return True
            
        except Exception:
            return False
    
    def parse(self, content: str) -> Dict[str, Any]:
        """解析 OpenAPI 规范内容"""
        import json
        return json.loads(content)
    
    def extract_endpoints(self, parsed_content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取 OpenAPI 端点信息"""
        endpoints = []
        
        if 'paths' not in parsed_content:
            return endpoints
        
        for path, path_item in parsed_content['paths'].items():
            for method, operation in path_item.items():
                if method in ['get', 'post', 'put', 'delete', 'patch', 'head', 'options', 'trace']:
                    endpoint = self._extract_endpoint(path, method, operation, parsed_content)
                    endpoints.append(endpoint)
        
        return endpoints
    
    def _extract_endpoint(self, path: str, method: str, operation: Dict[str, Any], 
                         doc: Dict[str, Any]) -> Dict[str, Any]:
        """提取单个端点信息"""
        # 提取参数
        parameters = self._extract_parameters(operation.get('parameters', []))
        
        # 提取请求体
        request_schema = self._extract_request_body(operation.get('requestBody'))
        
        # 提取响应
        response_schema = self._extract_responses(operation.get('responses', {}))
        
        # 提取安全要求
        security = operation.get('security', [])
        
        endpoint = {
            'name': path,
            'type': 'http',
            'method': method.upper(),
            'operation_type': method.lower(),
            'description': operation.get('description', ''),
            'summary': operation.get('summary', ''),
            'operation_id': operation.get('operationId', ''),
            'parameters': parameters,
            'request_schema': request_schema,
            'response_schema': response_schema,
            'security': security,
            'tags': operation.get('tags', []),
            'bindings': {}
        }
        
        return self.normalize_endpoint(endpoint)
    
    def _extract_parameters(self, parameters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """提取参数信息"""
        extracted = []
        for param in parameters:
            extracted_param = {
                'name': param.get('name', ''),
                'in': param.get('in', ''),
                'required': param.get('required', False),
                'description': param.get('description', ''),
                'schema': param.get('schema', {})
            }
            extracted.append(extracted_param)
        return extracted
    
    def _extract_request_body(self, request_body: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """提取请求体信息"""
        if not request_body:
            return {}
        
        content = request_body.get('content', {})
        schemas = {}
        
        for content_type, content_info in content.items():
            schemas[content_type] = {
                'schema': content_info.get('schema', {}),
                'example': content_info.get('example'),
                'examples': content_info.get('examples', {})
            }
        
        return {
            'required': request_body.get('required', False),
            'description': request_body.get('description', ''),
            'content': schemas
        }
    
    def _extract_responses(self, responses: Dict[str, Any]) -> Dict[str, Any]:
        """提取响应信息"""
        extracted = {}
        for status_code, response in responses.items():
            content = response.get('content', {})
            schemas = {}
            
            for content_type, content_info in content.items():
                schemas[content_type] = {
                    'schema': content_info.get('schema', {}),
                    'example': content_info.get('example'),
                    'examples': content_info.get('examples', {})
                }
            
            extracted[status_code] = {
                'description': response.get('description', ''),
                'content': schemas,
                'headers': response.get('headers', {})
            }
        
        return extracted
    
    def get_path_parameters(self, path: str) -> List[str]:
        """获取路径参数"""
        import re
        pattern = r'\{([^}]+)\}'
        return re.findall(pattern, path)
    
    def validate_path_parameters(self, path: str, parameters: List[Dict[str, Any]]) -> bool:
        """验证路径参数"""
        path_params = self.get_path_parameters(path)
        param_names = [p['name'] for p in parameters if p.get('in') == 'path']
        
        return set(path_params) == set(param_names) 