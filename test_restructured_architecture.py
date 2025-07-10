#!/usr/bin/env python3
"""
测试重构后的 StepFlow Gateway 架构
"""

import asyncio
import json
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from stepflow_gateway.core.registry import ApiSpecRegistry
from stepflow_gateway.core.base.api_spec import ApiSpecification
from stepflow_gateway.core.base.parser import BaseParser
from stepflow_gateway.core.base.executor import BaseExecutor
from stepflow_gateway.core.base.protocol import BaseProtocolAdapter


def test_registry():
    """测试注册器功能"""
    print("🧪 测试 API 规范注册器...")
    
    registry = ApiSpecRegistry()
    
    # 测试注册功能
    print("  📝 测试注册功能...")
    
    # 模拟注册一个规范
    class TestSpec(ApiSpecification):
        @property
        def spec_type(self) -> str:
            return "test"
        
        @property
        def version(self) -> str:
            return "1.0.0"
        
        def validate(self, content: str) -> bool:
            return True
        
        def parse(self, content: str) -> dict:
            return {"test": "data"}
        
        def extract_endpoints(self, parsed_content: dict) -> list:
            return [{"name": "/test", "type": "http"}]
    
    class TestParser(BaseParser):
        def parse(self, content: str) -> dict:
            return {"parsed": "data"}
        
        def validate(self, content: str) -> bool:
            return True
    
    class TestExecutor(BaseExecutor):
        async def execute(self, endpoint_id: str, request_data: dict) -> dict:
            return {"success": True, "result": "test"}
        
        def get_supported_protocols(self) -> list:
            return ["http"]
    
    class TestProtocol(BaseProtocolAdapter):
        @property
        def protocol_name(self):
            return "test"
        async def connect(self, config: dict = None):
            self._connected = True
        
        async def execute(self, operation: str, data: dict) -> dict:
            return {"success": True}
        
        async def disconnect(self):
            self._connected = False
    
    # 注册组件
    registry.register_spec("test", TestSpec)
    registry.register_parser("test", TestParser)
    registry.register_executor("test", TestExecutor)
    registry.register_protocol("test_protocol", TestProtocol)
    
    # 验证注册
    assert registry.get_spec("test") == TestSpec
    assert registry.get_parser("test") == TestParser
    assert registry.get_executor("test") == TestExecutor
    assert registry.get_protocol("test_protocol") == TestProtocol
    
    print("  ✅ 注册功能测试通过")
    
    # 测试创建实例
    print("  🔧 测试实例创建...")
    
    spec = registry.create_spec("test")
    parser = registry.create_parser("test")
    executor = registry.create_executor("test")
    protocol = registry.create_protocol("test_protocol", {})
    
    assert spec is not None
    assert parser is not None
    assert executor is not None
    assert protocol is not None
    
    print("  ✅ 实例创建测试通过")
    
    # 测试列表功能
    print("  📋 测试列表功能...")
    
    specs = registry.list_specs()
    parsers = registry.list_parsers()
    executors = registry.list_executors()
    protocols = registry.list_protocols()
    
    assert "test" in specs
    assert "test" in parsers
    assert "test" in executors
    assert "test_protocol" in protocols
    
    print("  ✅ 列表功能测试通过")
    
    # 测试信息获取
    print("  ℹ️  测试信息获取...")
    
    spec_info = registry.get_spec_info("test")
    protocol_info = registry.get_protocol_info("test_protocol")
    
    assert spec_info["spec_type"] == "test"
    assert protocol_info["protocol_name"] == "test_protocol"
    
    print("  ✅ 信息获取测试通过")
    
    # 测试注册器摘要
    print("  📊 测试注册器摘要...")
    
    summary = registry.get_registry_summary()
    
    assert summary["specifications"]["count"] == 1
    assert summary["parsers"]["count"] == 1
    assert summary["executors"]["count"] == 1
    assert summary["protocols"]["count"] == 1
    
    print("  ✅ 注册器摘要测试通过")
    
    print("✅ 注册器测试完成\n")


def test_base_classes():
    """测试基础抽象类"""
    print("🧪 测试基础抽象类...")
    
    # 测试 ApiSpecification
    print("  📋 测试 ApiSpecification...")
    
    class TestSpec(ApiSpecification):
        @property
        def spec_type(self) -> str:
            return "test"
        
        @property
        def version(self) -> str:
            return "1.0.0"
        
        def validate(self, content: str) -> bool:
            return True
        
        def parse(self, content: str) -> dict:
            return {"test": "data"}
        
        def extract_endpoints(self, parsed_content: dict) -> list:
            return [{"name": "/test", "type": "http"}]
    
    spec = TestSpec()
    
    assert spec.spec_type == "test"
    assert spec.version == "1.0.0"
    assert spec.validate("test")
    assert spec.parse("test") == {"test": "data"}
    assert len(spec.extract_endpoints({})) == 1
    
    print("  ✅ ApiSpecification 测试通过")
    
    # 测试 BaseParser
    print("  🔍 测试 BaseParser...")
    
    class TestParser(BaseParser):
        def parse(self, content: str) -> dict:
            return {"parsed": "data"}
        
        def validate(self, content: str) -> bool:
            return True
    
    parser = TestParser()
    
    assert parser.parse("test") == {"parsed": "data"}
    assert parser.validate("test")
    
    # 测试内容解析
    json_content = '{"test": "data"}'
    yaml_content = 'test: data'
    
    parsed_json = parser.parse_content(json_content)
    parsed_yaml = parser.parse_content(yaml_content)
    
    assert parsed_json == {"test": "data"}
    assert parsed_yaml == {"test": "data"}
    
    print("  ✅ BaseParser 测试通过")
    
    # 测试 BaseExecutor
    print("  ⚡ 测试 BaseExecutor...")
    
    class TestExecutor(BaseExecutor):
        async def execute(self, endpoint_id: str, request_data: dict) -> dict:
            return {"success": True, "result": "test"}
        
        def get_supported_protocols(self) -> list:
            return ["http"]
    
    executor = TestExecutor()
    
    assert executor.get_supported_protocols() == ["http"]
    
    print("  ✅ BaseExecutor 测试通过")
    
    # 测试 BaseProtocolAdapter
    print("  🔌 测试 BaseProtocolAdapter...")
    
    class TestProtocol(BaseProtocolAdapter):
        @property
        def protocol_name(self):
            return "test"
        async def connect(self, config: dict = None):
            self._connected = True
        
        async def execute(self, operation: str, data: dict) -> dict:
            return {"success": True}
        
        async def disconnect(self):
            self._connected = False
    
    protocol = TestProtocol({})
    
    assert protocol.protocol_name == "test"
    assert not protocol.is_connected
    
    print("  ✅ BaseProtocolAdapter 测试通过")
    
    print("✅ 基础抽象类测试完成\n")


async def test_async_components():
    """测试异步组件"""
    print("🧪 测试异步组件...")
    
    # 测试协议适配器
    print("  🔌 测试协议适配器...")
    
    class TestProtocol(BaseProtocolAdapter):
        async def connect(self, config: dict = None):
            self._connected = True
            self._connection_info = {"status": "connected"}
        
        async def execute(self, operation: str, data: dict) -> dict:
            return {"success": True, "operation": operation, "data": data}
        
        async def disconnect(self):
            self._connected = False
    
    protocol = TestProtocol({"test": "config"})
    
    # 测试连接
    await protocol.connect()
    assert protocol.is_connected
    
    # 测试执行
    result = await protocol.execute("test", {"key": "value"})
    assert result["success"]
    assert result["operation"] == "test"
    
    # 测试断开连接
    await protocol.disconnect()
    assert not protocol.is_connected
    
    print("  ✅ 协议适配器测试通过")
    
    # 测试执行器
    print("  ⚡ 测试执行器...")
    
    class TestExecutor(BaseExecutor):
        async def execute(self, endpoint_id: str, request_data: dict) -> dict:
            return {"success": True, "endpoint_id": endpoint_id, "data": request_data}
        
        def get_supported_protocols(self) -> list:
            return ["http", "https"]
    
    executor = TestExecutor()
    
    result = await executor.execute("test-endpoint", {"test": "data"})
    assert result["success"]
    assert result["endpoint_id"] == "test-endpoint"
    
    print("  ✅ 执行器测试通过")
    
    print("✅ 异步组件测试完成\n")


def test_plugin_architecture():
    """测试插件架构"""
    print("🧪 测试插件架构...")
    
    # 测试插件注册
    print("  📝 测试插件注册...")
    
    registry = ApiSpecRegistry()
    
    # 模拟插件注册
    def register_test_plugin(reg):
        class TestSpec(ApiSpecification):
            @property
            def spec_type(self) -> str:
                return "test_plugin"
            
            @property
            def version(self) -> str:
                return "1.0.0"
            
            def validate(self, content: str) -> bool:
                return True
            
            def parse(self, content: str) -> dict:
                return {"plugin": "data"}
            
            def extract_endpoints(self, parsed_content: dict) -> list:
                return [{"name": "/plugin", "type": "http"}]
        
        class TestParser(BaseParser):
            def parse(self, content: str) -> dict:
                return {"parsed": "plugin"}
            
            def validate(self, content: str) -> bool:
                return True
        
        class TestExecutor(BaseExecutor):
            async def execute(self, endpoint_id: str, request_data: dict) -> dict:
                return {"success": True, "plugin": "executed"}
            
            def get_supported_protocols(self) -> list:
                return ["http"]
        
        reg.register_spec("test_plugin", TestSpec)
        reg.register_parser("test_plugin", TestParser)
        reg.register_executor("test_plugin", TestExecutor)
    
    # 注册插件
    register_test_plugin(registry)
    
    # 验证插件注册
    assert "test_plugin" in registry.list_specs()
    assert "test_plugin" in registry.list_parsers()
    assert "test_plugin" in registry.list_executors()
    
    print("  ✅ 插件注册测试通过")
    
    # 测试插件功能
    print("  🔧 测试插件功能...")
    
    spec = registry.create_spec("test_plugin")
    parser = registry.create_parser("test_plugin")
    executor = registry.create_executor("test_plugin")
    
    assert spec.spec_type == "test_plugin"
    assert parser.parse("test") == {"parsed": "plugin"}
    
    print("  ✅ 插件功能测试通过")
    
    print("✅ 插件架构测试完成\n")


def main():
    """主测试函数"""
    print("🚀 开始测试重构后的 StepFlow Gateway 架构\n")
    
    try:
        # 测试注册器
        test_registry()
        
        # 测试基础抽象类
        test_base_classes()
        
        # 测试异步组件
        asyncio.run(test_async_components())
        
        # 测试插件架构
        test_plugin_architecture()
        
        print("🎉 所有测试通过！重构后的架构工作正常。")
        print("\n📋 测试总结:")
        print("  ✅ API 规范注册器")
        print("  ✅ 基础抽象类")
        print("  ✅ 异步组件")
        print("  ✅ 插件架构")
        print("\n🚀 架构重构成功！现在可以支持多种 API 规范。")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 