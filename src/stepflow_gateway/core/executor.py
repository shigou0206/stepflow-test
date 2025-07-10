"""
执行器基础类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseExecutor(ABC):
    """执行器基础类"""
    
    def __init__(self):
        pass
    
    @abstractmethod
    def execute(self, spec, operation: str, params: Dict[str, Any] = None, 
                data: Dict[str, Any] = None, headers: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行操作"""
        pass 