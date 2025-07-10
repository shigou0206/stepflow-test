#!/usr/bin/env python3
"""
AsyncAPI 插件测试脚本
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from stepflow_gateway.plugins.asyncapi import (
    AsyncAPISpecification,
    AsyncAPIParser,
    AsyncAPIExecutor,
    AsyncAPIProtocolAdapter
)
from stepflow_gateway.core.registry import ApiSpecRegistry
from stepflow_gateway.core.gateway import StepFlowGateway


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AsyncAPITestSuite:
    """AsyncAPI 测试套件"""
    
    def __init__(self):
        self.registry = ApiSpecRegistry()
        self.gateway = StepFlowGateway()
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """记录测试结果"""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {test_name}: {message}")
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
    
    def test_specification_creation(self):
        """测试规范创建"""
        try:
            # 创建基本规范
            spec = AsyncAPISpecification(
                spec_id="test-asyncapi-001",
                name="Test AsyncAPI",
                content={
                    "asyncapi": "2.6.0",
                    "info": {
                        "title": "Test API",
                        "version": "1.0.0"
                    },
                    "channels": {
                        "/test": {
                            "publish": {
                                "summary": "Test publish"
                            },
                            "subscribe": {
                                "summary": "Test subscribe"
                            }
                        }
                    }
                }
            )
            
            # 验证基本属性
            assert spec.spec_type == "asyncapi"
            assert spec.name == "Test AsyncAPI"
            assert spec.spec_id == "test-asyncapi-001"
            assert spec.version == "2.6.0"
            
            # 验证规范
            validation_result = spec.validate()
            assert validation_result, f"规范验证失败: {spec.content}"
            
            self.log_test("规范创建", True, "成功创建并验证 AsyncAPI 规范")
            return spec
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.log_test("规范创建", False, f"失败: {e}\n{error_details}")
            return None
    
    def test_parser_functionality(self):
        """测试解析器功能"""
        try:
            parser = AsyncAPIParser()
            
            # 测试解析能力检查
            valid_content = {
                "asyncapi": "2.6.0",
                "info": {"title": "Test"},
                "channels": {}
            }
            assert parser.can_parse(json.dumps(valid_content))
            
            # 测试无效内容
            invalid_content = {"openapi": "3.0.0"}
            assert not parser.can_parse(json.dumps(invalid_content))
            
            # 测试解析
            spec = parser.parse(json.dumps(valid_content), "test-parse-001", "Parsed API")
            assert spec is not None
            assert spec.name == "Parsed API"
            
            # 测试端点提取
            endpoints = parser.extract_endpoints(spec)
            assert isinstance(endpoints, list)
            
            self.log_test("解析器功能", True, "成功测试解析器各项功能")
            return parser, spec
            
        except Exception as e:
            self.log_test("解析器功能", False, f"失败: {e}")
            return None, None
    
    def test_executor_creation(self):
        """测试执行器创建"""
        try:
            spec = AsyncAPISpecification(
                name="Test Executor API",
                content={
                    "asyncapi": "2.6.0",
                    "info": {"title": "Test"},
                    "channels": {
                        "/test": {
                            "publish": {"summary": "Test"},
                            "subscribe": {"summary": "Test"}
                        }
                    }
                }
            )
            
            executor = AsyncAPIExecutor(spec)
            
            # 测试执行能力检查
            endpoint = {
                'type': 'async',
                'operation_type': 'publish',
                'protocol': 'websocket',
                'servers': [{'url': 'ws://localhost:8080'}]
            }
            
            assert executor.can_execute(endpoint)
            
            # 测试无效端点
            invalid_endpoint = {'type': 'sync'}
            assert not executor.can_execute(invalid_endpoint)
            
            self.log_test("执行器创建", True, "成功创建并测试执行器")
            return executor
            
        except Exception as e:
            self.log_test("执行器创建", False, f"失败: {e}")
            return None
    
    def test_protocol_adapter(self):
        """测试协议适配器"""
        try:
            adapter = AsyncAPIProtocolAdapter()
            
            # 测试协议支持
            assert adapter.protocol_name == "asyncapi"
            assert adapter.supports_protocol("websocket")
            assert adapter.supports_protocol("mqtt")
            assert adapter.supports_protocol("kafka")
            assert not adapter.supports_protocol("invalid")
            
            # 测试连接列表
            connections = adapter.get_connections()
            assert isinstance(connections, list)
            
            # 测试订阅列表
            subscriptions = adapter.get_subscriptions()
            assert isinstance(subscriptions, list)
            
            self.log_test("协议适配器", True, "成功测试协议适配器")
            return adapter
            
        except Exception as e:
            self.log_test("协议适配器", False, f"失败: {e}")
            return None
    
    def test_registry_integration(self):
        """测试注册表集成"""
        try:
            # 创建测试规范
            spec = AsyncAPISpecification(
                spec_id="registry-test-001",
                name="Registry Test API",
                content={
                    "asyncapi": "2.6.0",
                    "info": {"title": "Registry Test"},
                    "channels": {
                        "/events": {
                            "publish": {"summary": "Publish events"},
                            "subscribe": {"summary": "Subscribe events"}
                        }
                    }
                }
            )
            
            # 注册规范类
            self.registry.register_spec("asyncapi", AsyncAPISpecification)
            
            # 验证注册
            registered_spec_class = self.registry.get_spec("asyncapi")
            assert registered_spec_class is not None
            assert registered_spec_class == AsyncAPISpecification
            
            # 测试规范列表
            specs = self.registry.list_specs()
            assert len(specs) > 0
            assert "asyncapi" in specs
            
            self.log_test("注册表集成", True, "成功测试注册表集成")
            
        except Exception as e:
            self.log_test("注册表集成", False, f"失败: {e}")
    
    def test_gateway_integration(self):
        """测试网关集成"""
        try:
            # 注册 AsyncAPI 插件组件
            self.registry.register_parser("asyncapi", AsyncAPIParser)
            self.registry.register_executor("asyncapi", AsyncAPIExecutor)
            self.registry.register_protocol("asyncapi", AsyncAPIProtocolAdapter)
            
            # 测试插件注册
            parsers = self.registry.list_parsers()
            executors = self.registry.list_executors()
            protocols = self.registry.list_protocols()
            
            assert "asyncapi" in parsers
            assert "asyncapi" in executors
            assert "asyncapi" in protocols
            
            self.log_test("网关集成", True, "成功测试网关集成")
            
        except Exception as e:
            self.log_test("网关集成", False, f"失败: {e}")
    
    def test_async_operations(self):
        """测试异步操作"""
        async def run_async_tests():
            try:
                # 创建执行器
                spec = AsyncAPISpecification(
                    name="Async Test API",
                    content={
                        "asyncapi": "2.6.0",
                        "info": {"title": "Async Test"},
                        "channels": {
                            "/test": {
                                "publish": {"summary": "Test publish"},
                                "subscribe": {"summary": "Test subscribe"}
                            }
                        }
                    }
                )
                
                executor = AsyncAPIExecutor(spec)
                
                # 测试启动和停止
                await executor.start()
                assert executor.running == True
                
                await executor.stop()
                assert executor.running == False
                
                self.log_test("异步操作", True, "成功测试异步操作")
                
            except Exception as e:
                self.log_test("异步操作", False, f"失败: {e}")
        
        # 运行异步测试
        asyncio.run(run_async_tests())
    
    def test_message_handling(self):
        """测试消息处理"""
        try:
            spec = AsyncAPISpecification(
                name="Message Test API",
                content={
                    "asyncapi": "2.6.0",
                    "info": {"title": "Message Test"},
                    "channels": {
                        "/messages": {
                            "publish": {"summary": "Send message"},
                            "subscribe": {"summary": "Receive message"}
                        }
                    }
                }
            )
            
            executor = AsyncAPIExecutor(spec)
            
            # 测试消息处理器
            test_messages = []
            
            def message_handler(data):
                test_messages.append(data)
            
            executor.add_message_handler("/messages", message_handler)
            assert "/messages" in executor.message_handlers
            
            executor.remove_message_handler("/messages")
            assert "/messages" not in executor.message_handlers
            
            self.log_test("消息处理", True, "成功测试消息处理")
            
        except Exception as e:
            self.log_test("消息处理", False, f"失败: {e}")
    
    def test_protocol_handlers(self):
        """测试协议处理器"""
        try:
            adapter = AsyncAPIProtocolAdapter()
            
            # 测试 WebSocket 处理器
            ws_handler = adapter.protocol_handlers['websocket']
            assert ws_handler is not None
            
            # 测试 MQTT 处理器
            mqtt_handler = adapter.protocol_handlers['mqtt']
            assert mqtt_handler is not None
            
            # 测试 Kafka 处理器
            kafka_handler = adapter.protocol_handlers['kafka']
            assert kafka_handler is not None
            
            self.log_test("协议处理器", True, "成功测试协议处理器")
            
        except Exception as e:
            self.log_test("协议处理器", False, f"失败: {e}")
    
    def test_schema_validation(self):
        """测试模式验证"""
        try:
            parser = AsyncAPIParser()
            
            # 测试有效模式
            valid_schema = {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"}
                },
                "required": ["name"]
            }
            assert parser.validate_schema(valid_schema)
            
            # 测试无效模式
            invalid_schema = {"invalid": "schema"}
            assert not parser.validate_schema(invalid_schema)
            
            self.log_test("模式验证", True, "成功测试模式验证")
            
        except Exception as e:
            self.log_test("模式验证", False, f"失败: {e}")
    
    def test_reference_resolution(self):
        """测试引用解析"""
        try:
            spec = AsyncAPISpecification(
                name="Reference Test API",
                content={
                    "asyncapi": "2.6.0",
                    "info": {"title": "Reference Test"},
                    "channels": {},
                    "components": {
                        "messages": {
                            "TestMessage": {
                                "payload": {
                                    "type": "object",
                                    "properties": {
                                        "test": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            )
            
            # 测试引用解析
            ref = "#/components/messages/TestMessage"
            resolved = spec.resolve_reference(ref)
            assert resolved is not None
            assert "payload" in resolved
            
            self.log_test("引用解析", True, "成功测试引用解析")
            
        except Exception as e:
            self.log_test("引用解析", False, f"失败: {e}")
    
    def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始 AsyncAPI 插件测试")
        logger.info("=" * 60)
        
        # 运行测试
        self.test_specification_creation()
        self.test_parser_functionality()
        self.test_executor_creation()
        self.test_protocol_adapter()
        self.test_registry_integration()
        self.test_gateway_integration()
        self.test_async_operations()
        self.test_message_handling()
        self.test_protocol_handlers()
        self.test_schema_validation()
        self.test_reference_resolution()
        
        # 统计结果
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        logger.info("=" * 60)
        logger.info(f"📊 测试结果统计:")
        logger.info(f"   总测试数: {total_tests}")
        logger.info(f"   通过: {passed_tests}")
        logger.info(f"   失败: {failed_tests}")
        logger.info(f"   成功率: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            logger.info("\n❌ 失败的测试:")
            for result in self.test_results:
                if not result['success']:
                    logger.info(f"   - {result['test']}: {result['message']}")
        
        logger.info("\n🎉 AsyncAPI 插件测试完成!")
        
        return failed_tests == 0


def main():
    """主函数"""
    test_suite = AsyncAPITestSuite()
    success = test_suite.run_all_tests()
    
    if success:
        logger.info("✅ 所有测试通过!")
        return 0
    else:
        logger.error("❌ 部分测试失败!")
        return 1


if __name__ == "__main__":
    exit(main()) 