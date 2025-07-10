"""
解析器抽象基类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import json
import yaml


class BaseParser(ABC):
    """解析器抽象基类"""
    
    def __init__(self):
        self.resolved_refs = {}  # 缓存已解析的引用
        self.ref_stack = []  # 引用栈，用于检测循环引用
    
    @abstractmethod
    def parse(self, content: str) -> Dict[str, Any]:
        """解析内容"""
        pass
    
    @abstractmethod
    def validate(self, content: str) -> bool:
        """验证内容"""
        pass
    
    def parse_content(self, content: str) -> Dict[str, Any]:
        """解析内容（JSON 或 YAML）"""
        try:
            if content.strip().startswith('{'):
                return json.loads(content)
            else:
                return yaml.safe_load(content)
        except Exception as e:
            raise ValueError(f"Failed to parse content: {e}")
    
    def resolve_refs(self, obj: Any, root_doc: Dict[str, Any], path: str = "") -> Any:
        """递归解析对象中的所有 $ref 引用"""
        if isinstance(obj, dict):
            # 检查是否有 $ref
            if '$ref' in obj:
                return self.resolve_ref(obj['$ref'], root_doc, path)
            
            # 递归处理字典的所有值
            resolved = {}
            for key, value in obj.items():
                resolved[key] = self.resolve_refs(value, root_doc, f"{path}.{key}" if path else key)
            return resolved
            
        elif isinstance(obj, list):
            # 递归处理列表的所有元素
            return [self.resolve_refs(item, root_doc, f"{path}[{i}]") for i, item in enumerate(obj)]
        
        else:
            # 基本类型直接返回
            return obj
    
    def resolve_ref(self, ref: str, root_doc: Dict[str, Any], current_path: str) -> Any:
        """解析单个 $ref 引用"""
        # 检查循环引用
        if ref in self.ref_stack:
            return {'$ref': ref, '_circular': True}
        
        # 检查缓存
        if ref in self.resolved_refs:
            return self.resolved_refs[ref]
        
        # 添加到引用栈
        self.ref_stack.append(ref)
        
        try:
            # 解析引用
            resolved = self._resolve_ref_impl(ref, root_doc, current_path)
            
            # 缓存结果
            self.resolved_refs[ref] = resolved
            return resolved
            
        finally:
            # 从引用栈中移除
            self.ref_stack.pop()
    
    def _resolve_ref_impl(self, ref: str, root_doc: Dict[str, Any], current_path: str) -> Any:
        """实现具体的引用解析逻辑"""
        if ref.startswith('#'):
            return self._resolve_internal_ref(ref, root_doc)
        elif ref.startswith('http://') or ref.startswith('https://'):
            return self._resolve_external_ref(ref)
        else:
            return self._resolve_relative_ref(ref, root_doc, current_path)
    
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
            return self.resolve_refs(current, root_doc, path)
            
        except KeyError as e:
            raise ValueError(f"Invalid internal reference '{ref}': {e}")
    
    def _resolve_external_ref(self, ref: str) -> Any:
        """解析外部引用 (http://example.com/openapi.yaml#/components/schemas/User)"""
        # 这里可以实现外部引用解析
        # 暂时抛出异常，后续可以实现
        raise ValueError(f"External references not yet supported: {ref}")
    
    def _resolve_relative_ref(self, ref: str, root_doc: Dict[str, Any], current_path: str) -> Any:
        """解析相对路径引用"""
        # 这里可以实现相对路径引用解析
        # 暂时抛出异常，后续可以实现
        raise ValueError(f"Relative references not yet supported: {ref}")
    
    def extract_parameters(self, parameters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
    
    def extract_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """提取模式信息"""
        if not schema:
            return {}
        
        return {
            'type': schema.get('type', ''),
            'format': schema.get('format', ''),
            'description': schema.get('description', ''),
            'properties': schema.get('properties', {}),
            'required': schema.get('required', []),
            'items': schema.get('items', {}),
            'enum': schema.get('enum', []),
            'default': schema.get('default'),
            'example': schema.get('example')
        } 