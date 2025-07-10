"""
解析器基础类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BaseParser(ABC):
    """解析器基础类"""
    
    def __init__(self):
        pass
    
    @abstractmethod
    def parse(self, content: Dict[str, Any], spec_id: str = None, name: str = None):
        """解析内容"""
        pass
    
    @abstractmethod
    def parse_endpoints(self, spec) -> List[Dict[str, Any]]:
        """解析端点信息"""
        pass 