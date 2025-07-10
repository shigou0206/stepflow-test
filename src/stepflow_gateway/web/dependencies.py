"""
Web 依赖注入模块
"""

from typing import Generator
from stepflow_gateway.core.gateway import StepFlowGateway

# 全局 Gateway 实例
_gateway: StepFlowGateway = None

def get_gateway() -> StepFlowGateway:
    """获取 Gateway 实例"""
    global _gateway
    if _gateway is None:
        _gateway = StepFlowGateway()
        try:
            _gateway.initialize()
        except Exception as e:
            print(f"⚠️ Gateway 初始化失败: {e}")
    return _gateway

def set_gateway(gateway: StepFlowGateway):
    """设置 Gateway 实例（主要用于测试）"""
    global _gateway
    _gateway = gateway

def close_gateway():
    """关闭 Gateway 实例"""
    global _gateway
    if _gateway:
        _gateway.close()
        _gateway = None 