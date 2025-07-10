"""
StepFlow Gateway 集成测试
"""

import json
import tempfile
import os
import sys
import unittest
from pathlib import Path

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from stepflow_gateway import StepFlowGateway
from stepflow_gateway.core.config import GatewayConfig


class TestStepFlowGateway(unittest.TestCase):
    """StepFlow Gateway 集成测试"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时数据库
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        # 创建配置
        self.config = GatewayConfig()
        self.config.database.path = self.temp_db.name
        self.config.debug = True
        
        # 创建 Gateway 实例
        self.gateway = StepFlowGateway(self.config)
        
        # 初始化
        self.assertTrue(self.gateway.initialize())
    
    def tearDown(self):
        """测试后清理"""
        self.gateway.close()
        
        # 删除临时数据库
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_01_initialization(self):
        """测试初始化"""
        # 验证默认用户已创建
        admin_user = self.gateway.get_user(username='admin')
        self.assertIsNotNone(admin_user)
        self.assertEqual(admin_user['username'], 'admin')
        self.assertEqual(admin_user['role'], 'admin')
        
        api_user = self.gateway.get_user(username='api_user')
        self.assertIsNotNone(api_user)
        self.assertEqual(api_user['username'], 'api_user')
        self.assertEqual(api_user['role'], 'api_user')
    
    def test_02_api_registration(self):
        """测试 API 注册"""
        # 创建测试 OpenAPI 文档
        openapi_doc = {
            "openapi": "3.0.0",
            "info": {
                "title": "Test API",
                "version": "1.0.0"
            },
            "paths": {
                "/test": {
                    "get": {
                        "summary": "Test endpoint",
                        "operationId": "testGet"
                    },
                    "post": {
                        "summary": "Test POST",
                        "operationId": "testPost"
                    }
                }
            }
        }
        
        # 注册 API
        result = self.gateway.register_api(
            name="Test API",
            openapi_content=json.dumps(openapi_doc),
            version="1.0.0",
            base_url="https://api.test.com"
        )
        
        self.assertTrue(result['success'])
        self.assertIn('document_id', result)
        self.assertIn('endpoints', result)
        self.assertEqual(len(result['endpoints']), 2)
        
        # 验证 API 文档
        api_doc = self.gateway.get_api(result['document_id'])
        self.assertIsNotNone(api_doc)
        self.assertEqual(api_doc['name'], 'Test API')
        self.assertEqual(api_doc['version'], '1.0.0')
        self.assertEqual(api_doc['base_url'], 'https://api.test.com')
        
        # 验证端点
        endpoints = self.gateway.list_endpoints(result['document_id'])
        self.assertEqual(len(endpoints), 2)
        
        # 验证端点详情
        get_endpoint = next(ep for ep in endpoints if ep['method'] == 'GET')
        self.assertEqual(get_endpoint['path'], '/test')
        self.assertEqual(get_endpoint['summary'], 'Test endpoint')
        
        post_endpoint = next(ep for ep in endpoints if ep['method'] == 'POST')
        self.assertEqual(post_endpoint['path'], '/test')
        self.assertEqual(post_endpoint['summary'], 'Test POST')
    
    def test_03_authentication_config(self):
        """测试认证配置"""
        # 先注册一个 API
        openapi_doc = {
            "openapi": "3.0.0",
            "info": {"title": "Auth Test API", "version": "1.0.0"},
            "paths": {"/test": {"get": {"summary": "Test"}}}
        }
        
        result = self.gateway.register_api("Auth Test API", json.dumps(openapi_doc))
        api_document_id = result['document_id']
        
        # 添加 Basic 认证配置
        basic_config = {"username": "test", "password": "test123"}
        auth_id = self.gateway.add_auth_config(
            api_document_id, "basic", basic_config, is_required=True, priority=10
        )
        
        self.assertIsNotNone(auth_id)
        
        # 添加 API Key 认证配置
        api_key_config = {"key_name": "X-API-Key", "key_value": "test-key"}
        api_key_id = self.gateway.add_auth_config(
            api_document_id, "api_key", api_key_config, is_required=False, priority=5
        )
        
        self.assertIsNotNone(api_key_id)
        
        # 验证认证配置
        auth_configs = self.gateway.list_auth_configs(api_document_id)
        self.assertEqual(len(auth_configs), 2)
        
        # 验证配置详情
        basic_auth = next(cfg for cfg in auth_configs if cfg['auth_type'] == 'basic')
        self.assertEqual(basic_auth['is_required'], True)
        self.assertEqual(basic_auth['priority'], 10)
        self.assertEqual(basic_auth['auth_config']['username'], 'test')
        
        api_key_auth = next(cfg for cfg in auth_configs if cfg['auth_type'] == 'api_key')
        self.assertEqual(api_key_auth['is_required'], False)
        self.assertEqual(api_key_auth['priority'], 5)
        self.assertEqual(api_key_auth['auth_config']['key_name'], 'X-API-Key')
    
    def test_04_api_calling(self):
        """测试 API 调用"""
        # 注册 API
        openapi_doc = {
            "openapi": "3.0.0",
            "info": {"title": "Call Test API", "version": "1.0.0"},
            "paths": {
                "/data": {
                    "get": {"summary": "Get data"},
                    "post": {"summary": "Create data"}
                }
            }
        }
        
        result = self.gateway.register_api("Call Test API", json.dumps(openapi_doc))
        api_document_id = result['document_id']
        
        # 获取端点
        endpoints = self.gateway.list_endpoints(api_document_id)
        get_endpoint = next(ep for ep in endpoints if ep['method'] == 'GET')
        
        # 调用 GET API
        request_data = {
            'headers': {'Content-Type': 'application/json'},
            'params': {'limit': 10},
            'client_ip': '192.168.1.100'
        }
        
        result = self.gateway.call_api(get_endpoint['id'], request_data)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['status_code'], 200)
        self.assertIn('body', result)
        self.assertIn('headers', result)
        
        # 调用 POST API
        post_endpoint = next(ep for ep in endpoints if ep['method'] == 'POST')
        
        request_data = {
            'headers': {'Content-Type': 'application/json'},
            'body': {'name': 'test', 'value': 123},
            'client_ip': '192.168.1.100'
        }
        
        result = self.gateway.call_api(post_endpoint['id'], request_data)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['status_code'], 201)
        self.assertIn('body', result)
    
    def test_05_user_management(self):
        """测试用户管理"""
        # 创建用户
        user_id = self.gateway.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
            role="user"
        )
        
        self.assertIsNotNone(user_id)
        
        # 验证用户
        user = self.gateway.get_user(user_id=user_id)
        self.assertIsNotNone(user)
        self.assertEqual(user['username'], 'testuser')
        self.assertEqual(user['email'], 'test@example.com')
        self.assertEqual(user['role'], 'user')
        self.assertTrue(user['is_active'])
        
        # 用户认证
        auth_result = self.gateway.authenticate_user("testuser", "password123")
        self.assertTrue(auth_result['success'])
        self.assertIn('user', auth_result)
        self.assertIn('session_token', auth_result)
        
        # 验证会话
        session_result = self.gateway.validate_session(auth_result['session_token'])
        self.assertTrue(session_result['success'])
        self.assertEqual(session_result['user']['username'], 'testuser')
        
        # 列出用户
        users = self.gateway.list_users()
        self.assertGreaterEqual(len(users), 3)  # admin, api_user, testuser
        
        # 按角色过滤
        admin_users = self.gateway.list_users(role='admin')
        self.assertEqual(len(admin_users), 1)
        self.assertEqual(admin_users[0]['username'], 'admin')
    
    def test_06_statistics_and_monitoring(self):
        """测试统计和监控"""
        # 注册 API 并调用
        openapi_doc = {
            "openapi": "3.0.0",
            "info": {"title": "Stats API", "version": "1.0.0"},
            "paths": {"/stats": {"get": {"summary": "Get stats"}}}
        }
        
        result = self.gateway.register_api("Stats API", json.dumps(openapi_doc))
        api_document_id = result['document_id']
        endpoint_id = result['endpoints'][0]['id']
        
        # 调用 API 几次
        for i in range(3):
            request_data = {'headers': {}, 'client_ip': '192.168.1.100'}
            self.gateway.call_api(endpoint_id, request_data)
        
        # 检查统计信息
        stats = self.gateway.get_statistics()
        self.assertGreaterEqual(stats['templates'], 1)
        self.assertGreaterEqual(stats['api_documents'], 1)
        self.assertGreaterEqual(stats['endpoints'], 1)
        self.assertGreaterEqual(stats['api_calls'], 3)
        
        # 检查端点统计
        endpoint_stats = self.gateway.get_endpoint_statistics(endpoint_id)
        self.assertGreaterEqual(endpoint_stats.get('call_count', 0), 3)
        self.assertGreaterEqual(endpoint_stats.get('success_count', 0), 3)
        
        # 检查最近调用
        recent_calls = self.gateway.get_recent_calls(5)
        self.assertGreaterEqual(len(recent_calls), 3)
        
        # 健康检查
        health_result = self.gateway.check_health(api_document_id)
        self.assertEqual(health_result['status'], 'success')
        self.assertEqual(health_result['total_endpoints'], 1)
        self.assertEqual(health_result['active_endpoints'], 1)
    
    def test_07_resource_references(self):
        """测试资源引用"""
        # 注册 API
        openapi_doc = {
            "openapi": "3.0.0",
            "info": {"title": "Ref API", "version": "1.0.0"},
            "paths": {"/ref": {"get": {"summary": "Get ref"}}}
        }
        
        result = self.gateway.register_api("Ref API", json.dumps(openapi_doc))
        endpoint_id = result['endpoints'][0]['id']
        
        # 创建资源引用
        ref_id = self.gateway.create_resource_reference(
            resource_type="workflow_node",
            resource_id="node_001",
            api_endpoint_id=endpoint_id,
            display_name="测试节点",
            description="用于工作流的测试节点"
        )
        
        self.assertIsNotNone(ref_id)
        
        # 获取资源引用
        refs = self.gateway.get_resource_references("workflow_node")
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0]['resource_id'], 'node_001')
        self.assertEqual(refs[0]['display_name'], '测试节点')
        
        # 按资源 ID 过滤
        specific_refs = self.gateway.get_resource_references(resource_id='node_001')
        self.assertEqual(len(specific_refs), 1)
    
    def test_08_oauth2_support(self):
        """测试 OAuth2 支持"""
        # 注册 API
        openapi_doc = {
            "openapi": "3.0.0",
            "info": {"title": "OAuth2 API", "version": "1.0.0"},
            "paths": {"/oauth": {"get": {"summary": "OAuth test"}}}
        }
        
        result = self.gateway.register_api("OAuth2 API", json.dumps(openapi_doc))
        api_document_id = result['document_id']
        
        # 添加 OAuth2 认证配置
        oauth2_config = {
            "auth_url": "https://oauth.example.com/auth",
            "token_url": "https://oauth.example.com/token",
            "client_id": "test_client",
            "client_secret": "test_secret",
            "redirect_uri": "https://gateway.example.com/callback",
            "scope": "read write"
        }
        
        auth_id = self.gateway.add_auth_config(
            api_document_id, "oauth2", oauth2_config, is_required=True
        )
        
        # 创建 OAuth2 认证 URL
        user_id = self.gateway.get_user(username='admin')['id']
        auth_url_result = self.gateway.create_oauth2_auth_url(user_id, api_document_id)
        
        self.assertTrue(auth_url_result['success'])
        self.assertIn('auth_url', auth_url_result)
        self.assertIn('state_id', auth_url_result)
        self.assertIn('state', auth_url_result)
        
        # 模拟 OAuth2 回调
        callback_result = self.gateway.handle_oauth2_callback(
            auth_url_result['state_id'],
            'test_auth_code',
            auth_url_result['state']
        )
        
        self.assertTrue(callback_result['success'])
        self.assertIn('auth_id', callback_result)
        self.assertIn('user_auth', callback_result)
    
    def test_09_error_handling(self):
        """测试错误处理"""
        # 测试不存在的端点
        result = self.gateway.call_api("non-existent-id", {})
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        
        # 测试不存在的 API 文档
        api_doc = self.gateway.get_api("non-existent-id")
        self.assertIsNone(api_doc)
        
        # 测试不存在的用户
        user = self.gateway.get_user(username="non-existent")
        self.assertIsNone(user)
        
        # 测试无效的认证
        auth_result = self.gateway.authenticate_user("admin", "wrong-password")
        self.assertFalse(auth_result['success'])
        self.assertIn('error', auth_result)
    
    def test_10_configuration_management(self):
        """测试配置管理"""
        # 获取当前配置
        config = self.gateway.get_config()
        self.assertIsInstance(config, GatewayConfig)
        self.assertEqual(config.database.path, self.temp_db.name)
        
        # 更新配置
        new_config = GatewayConfig()
        new_config.database.path = self.temp_db.name
        new_config.debug = True
        new_config.logging.level = 'DEBUG'
        
        self.gateway.update_config(new_config)
        
        # 验证配置已更新
        updated_config = self.gateway.get_config()
        self.assertTrue(updated_config.debug)
        self.assertEqual(updated_config.logging.level, 'DEBUG')


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2) 