#!/usr/bin/env python3
"""
OAuth2 回调流程集成测试
演示用户首次访问 API 时跳转认证页并回调的完整流程
"""

import sqlite3
import json
import time
import uuid
import secrets
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class OAuth2CallbackTest:
    """OAuth2 回调流程测试"""
    
    def __init__(self, db_path: str = "gateway_with_oauth2.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
    
    def setup_database(self):
        """设置数据库"""
        print("🔧 设置包含 OAuth2 回调支持的数据库...")
        with open('database_with_oauth2_callback.sql', 'r') as f:
            sql_content = f.read()
        try:
            self.cursor.executescript(sql_content)
            self.conn.commit()
            print("✅ 数据库设置完成！")
        except Exception as e:
            print(f"❌ 数据库初始化失败: {e}")
    
    def test_oauth2_authorization_flow(self):
        """测试 OAuth2 授权码流程"""
        print("\n🔄 测试 OAuth2 授权码流程...")
        
        # 1. 用户首次访问需要 OAuth2 认证的 API
        user_id = "user-3"  # 从示例数据中获取
        api_document_id = "doc-3"  # OAuth2 保护的 API
        
        print(f"   用户 {user_id} 首次访问 API {api_document_id}")
        
        # 2. 检查用户是否已有授权
        has_authorization = self.check_user_authorization(user_id, api_document_id)
        
        if not has_authorization:
            print("   ❌ 用户未授权，需要跳转到认证页")
            
            # 3. 创建 OAuth2 授权状态
            auth_state = self.create_oauth2_auth_state(user_id, api_document_id)
            print(f"   创建授权状态: {auth_state['id']}")
            
            # 4. 生成认证跳转 URL
            auth_url = self.generate_auth_url(auth_state)
            print(f"   认证跳转 URL: {auth_url}")
            
            # 5. 模拟用户授权（在实际场景中，用户会在浏览器中完成）
            print("   🔐 模拟用户在认证页授权...")
            
            # 6. 处理 OAuth2 回调
            callback_result = self.handle_oauth2_callback(auth_state['id'])
            
            if callback_result['success']:
                print("   ✅ OAuth2 回调处理成功")
                print(f"   获取到 access_token: {callback_result['access_token'][:20]}...")
                print(f"   用户 auth_id: {callback_result['auth_id']}")
                
                # 7. 保存用户授权信息
                auth_session = self.save_user_authorization(user_id, api_document_id, callback_result)
                print(f"   保存授权会话: {auth_session['id']}")
                
                # 8. 现在可以调用 API 了
                api_response = self.call_protected_api(user_id, api_document_id)
                print(f"   API 调用成功: {api_response['status_code']}")
            else:
                print(f"   ❌ OAuth2 回调失败: {callback_result['error']}")
        else:
            print("   ✅ 用户已有授权，直接调用 API")
            api_response = self.call_protected_api(user_id, api_document_id)
            print(f"   API 调用成功: {api_response['status_code']}")
    
    def check_user_authorization(self, user_id: str, api_document_id: str) -> bool:
        """检查用户是否已有授权"""
        self.cursor.execute('''
            SELECT id FROM user_api_authorizations 
            WHERE user_id = ? AND api_document_id = ? AND is_active = 1
            AND (expires_at IS NULL OR expires_at > datetime('now'))
        ''', (user_id, api_document_id))
        
        return self.cursor.fetchone() is not None
    
    def create_oauth2_auth_state(self, user_id: str, api_document_id: str) -> dict:
        """创建 OAuth2 授权状态"""
        # 获取 OAuth2 认证配置
        self.cursor.execute('''
            SELECT id, auth_config FROM api_auth_configs 
            WHERE api_document_id = ? AND auth_type = 'oauth2' AND status = 'active'
        ''', (api_document_id,))
        
        auth_config_row = self.cursor.fetchone()
        if not auth_config_row:
            raise Exception("未找到 OAuth2 认证配置")
        
        auth_config = json.loads(auth_config_row['auth_config'])
        
        # 生成 PKCE 参数
        code_verifier = secrets.token_urlsafe(32)
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode().rstrip('=')
        
        # 生成 state 参数
        state = secrets.token_urlsafe(16)
        
        # 创建授权状态记录
        state_id = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(minutes=10)
        
        self.cursor.execute('''
            INSERT INTO oauth2_auth_states 
            (id, auth_config_id, user_id, state, code_verifier, code_challenge, 
             code_challenge_method, redirect_uri, scope, client_id, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            state_id,
            auth_config_row['id'],
            user_id,
            state,
            code_verifier,
            code_challenge,
            'S256',
            auth_config['redirect_uri'],
            auth_config['scope'],
            auth_config['client_id'],
            expires_at.isoformat(),
            datetime.now().isoformat()
        ))
        
        self.conn.commit()
        
        return {
            'id': state_id,
            'state': state,
            'code_verifier': code_verifier,
            'code_challenge': code_challenge,
            'auth_config': auth_config
        }
    
    def generate_auth_url(self, auth_state: dict) -> str:
        """生成认证跳转 URL"""
        auth_config = auth_state['auth_config']
        
        params = {
            'response_type': 'code',
            'client_id': auth_config['client_id'],
            'redirect_uri': auth_config['redirect_uri'],
            'scope': auth_config['scope'],
            'state': auth_state['state'],
            'code_challenge': auth_state['code_challenge'],
            'code_challenge_method': 'S256'
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{auth_config['auth_url']}?{query_string}"
    
    def handle_oauth2_callback(self, auth_state_id: str) -> dict:
        """处理 OAuth2 回调"""
        # 获取授权状态
        self.cursor.execute('''
            SELECT * FROM oauth2_auth_states WHERE id = ?
        ''', (auth_state_id,))
        
        auth_state = self.cursor.fetchone()
        if not auth_state:
            return {'success': False, 'error': '授权状态不存在'}
        
        # 模拟 OAuth2 提供商返回授权码
        auth_code = f"auth_code_{secrets.token_hex(8)}"
        
        # 模拟用授权码换取 token
        token_response = self.exchange_code_for_token(auth_code, auth_state['code_verifier'])
        
        if token_response['success']:
            # 记录回调日志
            self.log_oauth2_callback(auth_state_id, auth_state['user_id'], 
                                   auth_code, auth_state['state'], token_response)
            
            return {
                'success': True,
                'access_token': token_response['access_token'],
                'refresh_token': token_response['refresh_token'],
                'auth_id': token_response['auth_id'],
                'provider_user_id': token_response['provider_user_id']
            }
        else:
            return {'success': False, 'error': token_response['error']}
    
    def exchange_code_for_token(self, auth_code: str, code_verifier: str) -> dict:
        """模拟用授权码换取 token"""
        # 模拟网络请求延迟
        time.sleep(0.1)
        
        # 模拟 OAuth2 提供商验证并返回 token
        return {
            'success': True,
            'access_token': f"access_token_{secrets.token_hex(16)}",
            'refresh_token': f"refresh_token_{secrets.token_hex(16)}",
            'token_type': 'Bearer',
            'expires_in': 3600,
            'scope': 'read profile',
            'auth_id': f"auth_user_{secrets.token_hex(8)}",
            'provider_user_id': f"provider_user_{secrets.token_hex(8)}"
        }
    
    def log_oauth2_callback(self, auth_state_id: str, user_id: str, 
                          callback_code: str, callback_state: str, token_response: dict):
        """记录 OAuth2 回调日志"""
        log_id = str(uuid.uuid4())
        
        self.cursor.execute('''
            INSERT INTO oauth2_callback_logs 
            (id, auth_state_id, user_id, callback_code, callback_state, 
             token_response, auth_id, provider_user_id, client_ip, 
             callback_status, response_time_ms, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            log_id,
            auth_state_id,
            user_id,
            callback_code,
            callback_state,
            json.dumps(token_response),  # 加密存储
            token_response['auth_id'],
            token_response['provider_user_id'],
            '192.168.1.102',
            'success',
            250,
            datetime.now().isoformat()
        ))
        
        self.conn.commit()
    
    def save_user_authorization(self, user_id: str, api_document_id: str, 
                              callback_result: dict) -> dict:
        """保存用户授权信息"""
        # 获取认证配置
        self.cursor.execute('''
            SELECT id FROM api_auth_configs 
            WHERE api_document_id = ? AND auth_type = 'oauth2' AND status = 'active'
        ''', (api_document_id,))
        
        auth_config_id = self.cursor.fetchone()['id']
        
        # 计算过期时间
        expires_at = datetime.now() + timedelta(hours=1)
        
        # 创建授权会话
        session_id = str(uuid.uuid4())
        
        self.cursor.execute('''
            INSERT INTO user_api_authorizations 
            (id, user_id, api_document_id, auth_config_id, access_token, 
             refresh_token, token_type, expires_at, scope, auth_id, 
             provider_user_id, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id,
            user_id,
            api_document_id,
            auth_config_id,
            callback_result['access_token'],  # 加密存储
            callback_result['refresh_token'],  # 加密存储
            'Bearer',
            expires_at.isoformat(),
            'read profile',
            callback_result['auth_id'],
            callback_result['provider_user_id'],
            1,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        self.conn.commit()
        
        return {
            'id': session_id,
            'auth_id': callback_result['auth_id'],
            'expires_at': expires_at.isoformat()
        }
    
    def call_protected_api(self, user_id: str, api_document_id: str) -> dict:
        """调用受保护的 API"""
        # 获取用户授权信息
        self.cursor.execute('''
            SELECT access_token, auth_id FROM user_api_authorizations 
            WHERE user_id = ? AND api_document_id = ? AND is_active = 1
        ''', (user_id, api_document_id))
        
        auth_info = self.cursor.fetchone()
        if not auth_info:
            return {'status_code': 401, 'error': '未授权'}
        
        # 模拟 API 调用
        time.sleep(0.05)
        
        response = {
            'status_code': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': {
                'user_id': auth_info['auth_id'],
                'profile': {
                    'name': 'John Doe',
                    'email': 'john@example.com',
                    'avatar': 'https://example.com/avatar.jpg'
                }
            }
        }
        
        # 记录 API 调用日志
        self.log_api_call(api_document_id, response)
        
        return response
    
    def log_api_call(self, api_document_id: str, response: dict):
        """记录 API 调用日志"""
        # 获取端点信息
        self.cursor.execute('''
            SELECT id FROM api_endpoints 
            WHERE api_document_id = ? LIMIT 1
        ''', (api_document_id,))
        
        endpoint = self.cursor.fetchone()
        if endpoint:
            log_id = str(uuid.uuid4())
            
            self.cursor.execute('''
                INSERT INTO api_call_logs 
                (id, api_endpoint_id, request_method, request_url, 
                 request_headers, response_status_code, response_headers, 
                 response_body, response_time_ms, client_ip, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                log_id,
                endpoint['id'],
                'GET',
                'https://api.example.com/profile',
                json.dumps({'Authorization': 'Bearer access_token_xxx'}),
                response['status_code'],
                json.dumps(response['headers']),
                json.dumps(response['body']),
                50,
                '192.168.1.102',
                datetime.now().isoformat()
            ))
            
            self.conn.commit()
    
    def test_multiple_users_oauth2_flow(self):
        """测试多个用户的 OAuth2 流程"""
        print("\n👥 测试多个用户的 OAuth2 流程...")
        
        # 创建新用户
        new_user_id = str(uuid.uuid4())
        self.cursor.execute('''
            INSERT INTO gateway_users (id, username, email, password_hash, salt, role, permissions, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            new_user_id,
            'new_oauth_user',
            'new_oauth@example.com',
            'hashed_password_new',
            'salt_new',
            'user',
            '{"oauth_access": true}',
            1,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        # 测试新用户的 OAuth2 流程
        print(f"   新用户 {new_user_id} 开始 OAuth2 授权流程...")
        
        # 检查授权状态
        has_auth = self.check_user_authorization(new_user_id, "doc-3")
        print(f"   用户授权状态: {'已授权' if has_auth else '未授权'}")
        
        if not has_auth:
            # 创建授权状态
            auth_state = self.create_oauth2_auth_state(new_user_id, "doc-3")
            print(f"   创建授权状态: {auth_state['id']}")
            
            # 处理回调
            callback_result = self.handle_oauth2_callback(auth_state['id'])
            if callback_result['success']:
                # 保存授权
                auth_session = self.save_user_authorization(new_user_id, "doc-3", callback_result)
                print(f"   保存授权会话: {auth_session['id']}")
                
                # 调用 API
                api_response = self.call_protected_api(new_user_id, "doc-3")
                print(f"   API 调用结果: {api_response['status_code']}")
        
        self.conn.commit()
    
    def show_oauth2_statistics(self):
        """显示 OAuth2 统计信息"""
        print("\n📊 OAuth2 统计信息:")
        
        # 1. 授权状态统计
        self.cursor.execute('SELECT COUNT(*) as count FROM oauth2_auth_states')
        state_count = self.cursor.fetchone()['count']
        
        # 2. 用户授权统计
        self.cursor.execute('SELECT COUNT(*) as count FROM user_api_authorizations')
        auth_count = self.cursor.fetchone()['count']
        
        # 3. 回调日志统计
        self.cursor.execute('SELECT COUNT(*) as count FROM oauth2_callback_logs')
        callback_count = self.cursor.fetchone()['count']
        
        # 4. 活跃授权统计
        self.cursor.execute('''
            SELECT COUNT(*) as count FROM user_api_authorizations 
            WHERE is_active = 1 AND (expires_at IS NULL OR expires_at > datetime('now'))
        ''')
        active_auth_count = self.cursor.fetchone()['count']
        
        print(f"   OAuth2 授权状态数量: {state_count}")
        print(f"   用户授权数量: {auth_count}")
        print(f"   回调日志数量: {callback_count}")
        print(f"   活跃授权数量: {active_auth_count}")
        
        # 5. 回调状态统计
        self.cursor.execute('''
            SELECT callback_status, COUNT(*) as count
            FROM oauth2_callback_logs
            GROUP BY callback_status
        ''')
        callback_stats = self.cursor.fetchall()
        print(f"\n   回调状态统计:")
        for stat in callback_stats:
            print(f"     {stat['callback_status']}: {stat['count']}")
        
        # 6. 用户授权详情
        self.cursor.execute('''
            SELECT u.username, d.name as api_name, uaa.auth_id, uaa.provider_user_id, uaa.expires_at
            FROM user_api_authorizations uaa
            JOIN gateway_users u ON uaa.user_id = u.id
            JOIN api_documents d ON uaa.api_document_id = d.id
            WHERE uaa.is_active = 1
            ORDER BY uaa.created_at DESC
        ''')
        auth_details = self.cursor.fetchall()
        print(f"\n   用户授权详情:")
        for detail in auth_details:
            print(f"     {detail['username']} -> {detail['api_name']} (auth_id: {detail['auth_id']})")
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()

def main():
    """主函数"""
    print("🚀 StepFlow Gateway OAuth2 回调流程集成测试")
    print("=" * 70)
    
    try:
        # 创建测试实例
        test = OAuth2CallbackTest()
        
        # 设置数据库
        test.setup_database()
        
        # 测试 OAuth2 授权码流程
        test.test_oauth2_authorization_flow()
        
        # 测试多个用户的 OAuth2 流程
        test.test_multiple_users_oauth2_flow()
        
        # 显示统计信息
        test.show_oauth2_statistics()
        
        # 关闭连接
        test.close()
        
        print("\n🎉 OAuth2 回调流程测试完成！")
        print("📁 数据库文件: gateway_with_oauth2.db")
        print("💡 可以使用 SQLite 工具查看数据:")
        print("   sqlite3 gateway_with_oauth2.db")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")

if __name__ == "__main__":
    main() 