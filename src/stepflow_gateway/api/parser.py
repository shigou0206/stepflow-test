"""
OpenAPI $ref 解析器
处理 OpenAPI 文档中的 $ref 引用，展开为完整文档
"""

import json
import re
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
import yaml


class OpenApiRefResolver:
    """OpenAPI $ref 解析器"""
    
    def __init__(self):
        self.resolved_refs = {}  # 缓存已解析的引用
        self.external_docs = {}  # 外部文档缓存
        self.ref_stack = []  # 引用栈，用于检测循环引用
    
    def resolve_document(self, openapi_content: str) -> Dict[str, Any]:
        """解析 OpenAPI 文档，处理所有 $ref 引用"""
        try:
            # 重置状态
            self.resolved_refs = {}
            self.ref_stack = []
            
            # 解析文档
            if openapi_content.strip().startswith('{'):
                doc = json.loads(openapi_content)
            else:
                doc = yaml.safe_load(openapi_content)
            
            # 解析所有引用
            resolved_doc = self._resolve_refs(doc, doc)
            
            return resolved_doc
            
        except Exception as e:
            raise ValueError(f"Failed to resolve OpenAPI document: {e}")
    
    def _resolve_refs(self, obj: Any, root_doc: Dict[str, Any], path: str = "") -> Any:
        """递归解析对象中的所有 $ref 引用"""
        if isinstance(obj, dict):
            # 检查是否有 $ref
            if '$ref' in obj:
                return self._resolve_ref(obj['$ref'], root_doc, path)
            
            # 递归处理字典的所有值
            resolved = {}
            for key, value in obj.items():
                resolved[key] = self._resolve_refs(value, root_doc, f"{path}.{key}" if path else key)
            return resolved
            
        elif isinstance(obj, list):
            # 递归处理列表的所有元素
            return [self._resolve_refs(item, root_doc, f"{path}[{i}]") for i, item in enumerate(obj)]
        
        else:
            # 基本类型直接返回
            return obj
    
    def _resolve_ref(self, ref: str, root_doc: Dict[str, Any], current_path: str) -> Any:
        """解析单个 $ref 引用"""
        # 检查循环引用
        if ref in self.ref_stack:
            # 检测到循环引用，返回引用本身而不是解析
            return {'$ref': ref, '_circular': True}
        
        # 检查缓存
        if ref in self.resolved_refs:
            return self.resolved_refs[ref]
        
        # 添加到引用栈
        self.ref_stack.append(ref)
        
        try:
            # 解析引用路径
            if ref.startswith('#'):
                # 内部引用
                resolved = self._resolve_internal_ref(ref, root_doc)
            elif ref.startswith('http://') or ref.startswith('https://'):
                # 外部引用
                resolved = self._resolve_external_ref(ref)
            else:
                # 相对路径引用
                resolved = self._resolve_relative_ref(ref, root_doc, current_path)
            
            # 缓存结果
            self.resolved_refs[ref] = resolved
            return resolved
            
        finally:
            # 从引用栈中移除
            self.ref_stack.pop()
    
    def _resolve_internal_ref(self, ref: str, root_doc: Dict[str, Any]) -> Any:
        """解析内部引用 (#/path/to/component)"""
        try:
            # 移除开头的 #
            path = ref[1:]
            
            # 按 / 分割路径
            parts = path.split('/')
            
            # 从根文档开始导航
            current = root_doc
            for part in parts:
                if part:  # 跳过空字符串
                    current = current[part]
            
            # 递归解析引用的内容
            return self._resolve_refs(current, root_doc, path)
            
        except KeyError as e:
            raise ValueError(f"Invalid internal reference '{ref}': {e}")
    
    def _resolve_external_ref(self, ref: str) -> Any:
        """解析外部引用 (http://example.com/openapi.yaml#/components/schemas/User)"""
        try:
            # 解析 URL
            parsed_url = urlparse(ref)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
            fragment = parsed_url.fragment
            
            # 获取外部文档
            if base_url not in self.external_docs:
                import requests
                response = requests.get(base_url)
                response.raise_for_status()
                
                content = response.text
                if base_url.endswith('.json'):
                    external_doc = json.loads(content)
                else:
                    external_doc = yaml.safe_load(content)
                
                self.external_docs[base_url] = external_doc
            
            external_doc = self.external_docs[base_url]
            
            # 解析片段引用
            if fragment:
                return self._resolve_internal_ref(f"#{fragment}", external_doc)
            else:
                return external_doc
                
        except Exception as e:
            raise ValueError(f"Failed to resolve external reference '{ref}': {e}")
    
    def _resolve_relative_ref(self, ref: str, root_doc: Dict[str, Any], current_path: str) -> Any:
        """解析相对路径引用"""
        # 这里可以处理相对路径引用
        # 例如: ./schemas/User.yaml
        raise ValueError(f"Relative references not yet supported: {ref}")
    
    def extract_endpoints(self, resolved_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从解析后的文档中提取端点信息"""
        endpoints = []
        
        if 'paths' not in resolved_doc:
            return endpoints
        
        for path, path_item in resolved_doc['paths'].items():
            for method, operation in path_item.items():
                if method in ['get', 'post', 'put', 'delete', 'patch', 'head', 'options', 'trace']:
                    endpoint = {
                        'path': path,
                        'method': method.upper(),
                        'operation_id': operation.get('operationId', ''),
                        'summary': operation.get('summary', ''),
                        'description': operation.get('description', ''),
                        'tags': operation.get('tags', []),
                        'parameters': self._extract_parameters(operation.get('parameters', [])),
                        'request_body': self._extract_request_body(operation.get('requestBody')),
                        'responses': self._extract_responses(operation.get('responses', {}))
                    }
                    endpoints.append(endpoint)
        
        return endpoints
    
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
    
    def _extract_request_body(self, request_body: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """提取请求体信息"""
        if not request_body:
            return None
        
        return {
            'required': request_body.get('required', False),
            'description': request_body.get('description', ''),
            'content': request_body.get('content', {})
        }
    
    def _extract_responses(self, responses: Dict[str, Any]) -> Dict[str, Any]:
        """提取响应信息"""
        extracted = {}
        for status_code, response in responses.items():
            extracted[status_code] = {
                'description': response.get('description', ''),
                'content': response.get('content', {}),
                'headers': response.get('headers', {})
            }
        return extracted


# 使用示例
def resolve_openapi_document(openapi_content: str) -> Dict[str, Any]:
    """解析 OpenAPI 文档的便捷函数"""
    resolver = OpenApiRefResolver()
    return resolver.resolve_document(openapi_content)


def extract_endpoints_from_document(openapi_content: str) -> List[Dict[str, Any]]:
    """从 OpenAPI 文档中提取端点的便捷函数"""
    resolver = OpenApiRefResolver()
    resolved_doc = resolver.resolve_document(openapi_content)
    return resolver.extract_endpoints(resolved_doc) 