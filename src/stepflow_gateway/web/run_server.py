"""
StepFlow Gateway 服务器启动脚本
"""

import uvicorn
import argparse
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def main():
    parser = argparse.ArgumentParser(description="StepFlow Gateway 服务器")
    parser.add_argument("--host", default="0.0.0.0", help="服务器主机地址")
    parser.add_argument("--port", type=int, default=8000, help="服务器端口")
    parser.add_argument("--reload", action="store_true", help="开发模式自动重载")
    parser.add_argument("--workers", type=int, default=1, help="工作进程数")
    parser.add_argument("--log-level", default="info", 
                       choices=["debug", "info", "warning", "error"],
                       help="日志级别")
    
    args = parser.parse_args()
    
    print("🚀 启动 StepFlow Gateway 服务器...")
    print(f"📍 地址: http://{args.host}:{args.port}")
    print(f"📚 API 文档: http://{args.host}:{args.port}/docs")
    print(f"🔄 重载模式: {'开启' if args.reload else '关闭'}")
    print(f"👥 工作进程: {args.workers}")
    print(f"📝 日志级别: {args.log_level}")
    print()
    
    try:
        uvicorn.run(
            "src.stepflow_gateway.web.app:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            workers=args.workers,
            log_level=args.log_level,
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 