"""
StepFlow Gateway 命令行接口
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

from .core.gateway import StepFlowGateway
from .core.config import GatewayConfig


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='StepFlow Gateway CLI')
    parser.add_argument('--config', '-c', help='配置文件路径')
    parser.add_argument('--database', '-d', help='数据库路径')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 初始化命令
    init_parser = subparsers.add_parser('init', help='初始化 Gateway')
    init_parser.add_argument('--force', action='store_true', help='强制重新初始化')
    
    # 注册 API 命令
    register_parser = subparsers.add_parser('register', help='注册 OpenAPI 文档')
    register_parser.add_argument('name', help='API 名称')
    register_parser.add_argument('file', help='OpenAPI 文档文件路径')
    register_parser.add_argument('--version', help='API 版本')
    register_parser.add_argument('--base-url', help='基础 URL')
    
    # 列出 API 命令
    list_parser = subparsers.add_parser('list', help='列出 API')
    list_parser.add_argument('--status', default='active', help='状态过滤')
    
    # 调用 API 命令
    call_parser = subparsers.add_parser('call', help='调用 API')
    call_parser.add_argument('endpoint_id', help='端点 ID')
    call_parser.add_argument('--method', default='GET', help='HTTP 方法')
    call_parser.add_argument('--headers', help='请求头 (JSON)')
    call_parser.add_argument('--body', help='请求体 (JSON)')
    call_parser.add_argument('--params', help='查询参数 (JSON)')
    
    # 认证配置命令
    auth_parser = subparsers.add_parser('auth', help='管理认证配置')
    auth_subparsers = auth_parser.add_subparsers(dest='auth_command', help='认证子命令')
    
    add_auth_parser = auth_subparsers.add_parser('add', help='添加认证配置')
    add_auth_parser.add_argument('api_document_id', help='API 文档 ID')
    add_auth_parser.add_argument('auth_type', help='认证类型')
    add_auth_parser.add_argument('config_file', help='认证配置文件路径')
    
    list_auth_parser = auth_subparsers.add_parser('list', help='列出认证配置')
    list_auth_parser.add_argument('--api-document-id', help='API 文档 ID')
    list_auth_parser.add_argument('--auth-type', help='认证类型')
    
    # 用户管理命令
    user_parser = subparsers.add_parser('user', help='用户管理')
    user_subparsers = user_parser.add_subparsers(dest='user_command', help='用户子命令')
    
    create_user_parser = user_subparsers.add_parser('create', help='创建用户')
    create_user_parser.add_argument('username', help='用户名')
    create_user_parser.add_argument('email', help='邮箱')
    create_user_parser.add_argument('password', help='密码')
    create_user_parser.add_argument('--role', default='user', help='角色')
    
    list_users_parser = user_subparsers.add_parser('list', help='列出用户')
    list_users_parser.add_argument('--role', help='角色过滤')
    
    # 统计命令
    stats_parser = subparsers.add_parser('stats', help='查看统计信息')
    stats_parser.add_argument('--endpoint-id', help='端点 ID')
    stats_parser.add_argument('--recent', type=int, help='最近调用数量')
    stats_parser.add_argument('--errors', type=int, help='错误日志数量')
    
    # 健康检查命令
    health_parser = subparsers.add_parser('health', help='健康检查')
    health_parser.add_argument('api_document_id', help='API 文档 ID')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 加载配置
    config = load_config(args)
    
    # 创建 Gateway 实例
    with StepFlowGateway(config) as gateway:
        if args.command == 'init':
            handle_init(gateway, args)
        elif args.command == 'register':
            handle_register(gateway, args)
        elif args.command == 'list':
            handle_list(gateway, args)
        elif args.command == 'call':
            handle_call(gateway, args)
        elif args.command == 'auth':
            handle_auth(gateway, args)
        elif args.command == 'user':
            handle_user(gateway, args)
        elif args.command == 'stats':
            handle_stats(gateway, args)
        elif args.command == 'health':
            handle_health(gateway, args)


def load_config(args) -> GatewayConfig:
    """加载配置"""
    config = GatewayConfig()
    
    if args.config:
        config = GatewayConfig.from_file(args.config)
    
    if args.database:
        config.database.path = args.database
    
    if args.debug:
        config.debug = True
        config.logging.level = 'DEBUG'
    
    return config


def handle_init(gateway: StepFlowGateway, args):
    """处理初始化命令"""
    print("正在初始化 StepFlow Gateway...")
    
    if gateway.initialize():
        print("✅ Gateway 初始化成功")
        print("默认用户:")
        print("  - 管理员: admin/admin123")
        print("  - API用户: api_user/api123")
    else:
        print("❌ Gateway 初始化失败")
        sys.exit(1)


def handle_register(gateway: StepFlowGateway, args):
    """处理注册命令"""
    print(f"正在注册 API: {args.name}")
    
    # 读取 OpenAPI 文档
    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        sys.exit(1)
    
    # 注册 API
    result = gateway.register_api(args.name, content, args.version, args.base_url)
    
    if result['success']:
        print("✅ API 注册成功")
        print(f"  文档 ID: {result['document_id']}")
        print(f"  端点数量: {len(result['endpoints'])}")
        
        for endpoint in result['endpoints']:
            print(f"    - {endpoint['method']} {endpoint['path']}")
    else:
        print(f"❌ API 注册失败: {result['error']}")
        sys.exit(1)


def handle_list(gateway: StepFlowGateway, args):
    """处理列出命令"""
    apis = gateway.list_apis(args.status)
    
    if not apis:
        print("没有找到 API")
        return
    
    print(f"找到 {len(apis)} 个 API:")
    for api in apis:
        print(f"  - {api['name']} (ID: {api['id']})")
        print(f"    版本: {api.get('version', 'N/A')}")
        print(f"    基础URL: {api.get('base_url', 'N/A')}")
        print(f"    状态: {api['status']}")
        print()


def handle_call(gateway: StepFlowGateway, args):
    """处理调用命令"""
    print(f"正在调用端点: {args.endpoint_id}")
    
    # 构建请求数据
    request_data = {
        'method': args.method,
        'headers': {},
        'body': None,
        'params': {}
    }
    
    if args.headers:
        try:
            request_data['headers'] = json.loads(args.headers)
        except json.JSONDecodeError:
            print("❌ 请求头格式错误")
            sys.exit(1)
    
    if args.body:
        try:
            request_data['body'] = json.loads(args.body)
        except json.JSONDecodeError:
            print("❌ 请求体格式错误")
            sys.exit(1)
    
    if args.params:
        try:
            request_data['params'] = json.loads(args.params)
        except json.JSONDecodeError:
            print("❌ 查询参数格式错误")
            sys.exit(1)
    
    # 调用 API
    result = gateway.call_api(args.endpoint_id, request_data)
    
    if result['success']:
        print("✅ API 调用成功")
        print(f"状态码: {result.get('status_code', 'N/A')}")
        print("响应头:")
        for key, value in result.get('headers', {}).items():
            print(f"  {key}: {value}")
        print("响应体:")
        print(json.dumps(result.get('body', {}), indent=2, ensure_ascii=False))
    else:
        print(f"❌ API 调用失败: {result['error']}")
        sys.exit(1)


def handle_auth(gateway: StepFlowGateway, args):
    """处理认证命令"""
    if args.auth_command == 'add':
        print(f"正在添加认证配置: {args.auth_type}")
        
        # 读取认证配置
        try:
            with open(args.config_file, 'r', encoding='utf-8') as f:
                auth_config = json.load(f)
        except Exception as e:
            print(f"❌ 读取认证配置文件失败: {e}")
            sys.exit(1)
        
        # 添加认证配置
        auth_config_id = gateway.add_auth_config(
            args.api_document_id, args.auth_type, auth_config
        )
        
        print(f"✅ 认证配置添加成功 (ID: {auth_config_id})")
        
    elif args.auth_command == 'list':
        auth_configs = gateway.list_auth_configs(args.api_document_id, args.auth_type)
        
        if not auth_configs:
            print("没有找到认证配置")
            return
        
        print(f"找到 {len(auth_configs)} 个认证配置:")
        for config in auth_configs:
            print(f"  - {config['auth_type']} (ID: {config['id']})")
            print(f"    优先级: {config['priority']}")
            print(f"    必需: {config['is_required']}")
            print(f"    全局: {config['is_global']}")
            print()


def handle_user(gateway: StepFlowGateway, args):
    """处理用户命令"""
    if args.user_command == 'create':
        print(f"正在创建用户: {args.username}")
        
        try:
            user_id = gateway.create_user(
                args.username, args.email, args.password, args.role
            )
            print(f"✅ 用户创建成功 (ID: {user_id})")
        except Exception as e:
            print(f"❌ 用户创建失败: {e}")
            sys.exit(1)
        
    elif args.user_command == 'list':
        users = gateway.list_users(args.role)
        
        if not users:
            print("没有找到用户")
            return
        
        print(f"找到 {len(users)} 个用户:")
        for user in users:
            print(f"  - {user['username']} (ID: {user['id']})")
            print(f"    邮箱: {user['email']}")
            print(f"    角色: {user['role']}")
            print(f"    状态: {'活跃' if user['is_active'] else '禁用'}")
            print()


def handle_stats(gateway: StepFlowGateway, args):
    """处理统计命令"""
    if args.endpoint_id:
        stats = gateway.get_endpoint_statistics(args.endpoint_id)
        print(f"端点统计 (ID: {args.endpoint_id}):")
        print(f"  调用次数: {stats.get('call_count', 0)}")
        print(f"  成功次数: {stats.get('success_count', 0)}")
        print(f"  错误次数: {stats.get('error_count', 0)}")
        print(f"  平均响应时间: {stats.get('avg_response_time_ms', 0)}ms")
        
    elif args.recent:
        calls = gateway.get_recent_calls(args.recent)
        print(f"最近 {len(calls)} 次调用:")
        for call in calls:
            print(f"  - {call['request_method']} {call['path']}")
            print(f"    状态码: {call['response_status_code']}")
            print(f"    响应时间: {call['response_time_ms']}ms")
            print(f"    时间: {call['created_at']}")
            print()
        
    elif args.errors:
        errors = gateway.get_error_logs(args.errors)
        print(f"最近 {len(errors)} 个错误:")
        for error in errors:
            print(f"  - {error['request_method']} {error['path']}")
            print(f"    状态码: {error['response_status_code']}")
            print(f"    错误信息: {error.get('error_message', 'N/A')}")
            print(f"    时间: {error['created_at']}")
            print()
        
    else:
        stats = gateway.get_statistics()
        print("系统统计:")
        print(f"  模板数量: {stats['templates']}")
        print(f"  API文档数量: {stats['api_documents']}")
        print(f"  端点数量: {stats['endpoints']}")
        print(f"  用户数量: {stats['users']}")
        print(f"  认证配置数量: {stats['auth_configs']}")
        print(f"  API调用总数: {stats['api_calls']}")


def handle_health(gateway: StepFlowGateway, args):
    """处理健康检查命令"""
    print(f"正在检查 API 健康状态: {args.api_document_id}")
    
    result = gateway.check_health(args.api_document_id)
    
    if result['status'] == 'success':
        print("✅ API 健康状态良好")
    elif result['status'] == 'warning':
        print("⚠️  API 健康状态警告")
    else:
        print("❌ API 健康状态异常")
    
    print(f"  API名称: {result.get('api_name', 'N/A')}")
    print(f"  总端点数: {result.get('total_endpoints', 0)}")
    print(f"  活跃端点数: {result.get('active_endpoints', 0)}")
    print(f"  检查时间: {result.get('check_time', 'N/A')}")


if __name__ == '__main__':
    main() 