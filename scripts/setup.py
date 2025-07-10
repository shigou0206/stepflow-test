#!/usr/bin/env python3
"""
StepFlow Gateway 项目设置脚本
用于初始化数据库、环境配置等
"""

import os
import sys
import sqlite3
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / 'src'))

def init_database(db_path: str = "stepflow_gateway.db"):
    """初始化数据库"""
    print(f"🔧 初始化数据库: {db_path}")
    
    # 检查数据库文件是否存在
    if os.path.exists(db_path):
        print(f"⚠️  数据库文件 {db_path} 已存在")
        response = input("是否要重新创建？(y/N): ")
        if response.lower() != 'y':
            print("❌ 取消数据库初始化")
            return
    
    # 读取数据库模式文件
    schema_file = project_root / "database" / "schema" / "stepflow_gateway.sql"
    if not schema_file.exists():
        print(f"❌ 数据库模式文件不存在: {schema_file}")
        return
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 读取并执行SQL
        with open(schema_file, 'r') as f:
            sql_content = f.read()
        
        cursor.executescript(sql_content)
        conn.commit()
        conn.close()
        
        print("✅ 数据库初始化成功！")
        print(f"📁 数据库文件: {db_path}")
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")

def init_test_database():
    """初始化测试数据库"""
    print("🧪 初始化测试数据库...")
    
    test_db_path = "test_stepflow_gateway.db"
    init_database(test_db_path)
    
    print("✅ 测试数据库初始化完成！")

def run_tests():
    """运行测试"""
    print("🧪 运行测试...")
    
    # 运行集成测试
    test_files = [
        "tests/integration/test_auth_integration.py",
        "tests/integration/test_oauth2_callback.py"
    ]
    
    for test_file in test_files:
        test_path = project_root / test_file
        if test_path.exists():
            print(f"运行测试: {test_file}")
            os.system(f"python {test_path}")
        else:
            print(f"⚠️  测试文件不存在: {test_file}")

def create_directories():
    """创建必要的目录"""
    print("📁 创建项目目录...")
    
    directories = [
        "logs",
        "data",
        "config",
        "temp"
    ]
    
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(exist_ok=True)
        print(f"   创建目录: {directory}")

def check_dependencies():
    """检查依赖"""
    print("📦 检查依赖...")
    
    required_packages = [
        'sqlite3',
        'json',
        'uuid',
        'datetime',
        'typing'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"   ❌ {package}")
    
    if missing_packages:
        print(f"\n⚠️  缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
    else:
        print("\n✅ 所有依赖包已安装")

def show_project_info():
    """显示项目信息"""
    print("📋 StepFlow Gateway 项目信息")
    print("=" * 50)
    print(f"项目根目录: {project_root}")
    print(f"Python版本: {sys.version}")
    print(f"当前工作目录: {os.getcwd()}")
    
    # 检查关键文件
    key_files = [
        "database/schema/stepflow_gateway.sql",
        "tests/integration/test_auth_integration.py",
        "tests/integration/test_oauth2_callback.py",
        "README.md"
    ]
    
    print("\n📁 关键文件检查:")
    for file_path in key_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="StepFlow Gateway 项目设置脚本")
    parser.add_argument("command", choices=[
        "init-db", "init-test-db", "run-tests", "create-dirs", 
        "check-deps", "info", "all"
    ], help="要执行的命令")
    parser.add_argument("--db-path", default="stepflow_gateway.db", 
                       help="数据库文件路径")
    
    args = parser.parse_args()
    
    print("🚀 StepFlow Gateway 项目设置")
    print("=" * 50)
    
    if args.command == "init-db":
        init_database(args.db_path)
    elif args.command == "init-test-db":
        init_test_database()
    elif args.command == "run-tests":
        run_tests()
    elif args.command == "create-dirs":
        create_directories()
    elif args.command == "check-deps":
        check_dependencies()
    elif args.command == "info":
        show_project_info()
    elif args.command == "all":
        print("🔄 执行完整设置流程...")
        create_directories()
        check_dependencies()
        init_database(args.db_path)
        init_test_database()
        run_tests()
        show_project_info()
    
    print("\n🎉 设置完成！")

if __name__ == "__main__":
    main() 