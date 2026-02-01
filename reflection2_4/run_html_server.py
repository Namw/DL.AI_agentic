#!/usr/bin/env python3
"""
print_html HTTP 服务器启动脚本
通过 Web 界面展示 print_html 函数的结果，无需 Jupyter/IPython 环境
"""
import sys
import argparse
from utils.html_server import start_server, start_server_in_background
import threading
import time


def main():
    parser = argparse.ArgumentParser(
        description='启动 print_html HTTP 服务器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                    # 使用默认端口 8080
  %(prog)s -p 8888            # 使用端口 8888
  %(prog)s -p 8080 -b         # 在后台启动服务器
  %(prog)s --host 0.0.0.0     # 允许外部访问
  %(prog)s --help             # 显示帮助信息
        """
    )
    
    parser.add_argument(
        '-p', '--port',
        type=int,
        default=8080,
        help='服务器端口 (默认: 8080)'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default='localhost',
        help='服务器主机地址 (默认: localhost)'
    )
    
    parser.add_argument(
        '-b', '--background',
        action='store_true',
        help='在后台启动服务器'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='显示详细信息'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("print_html HTTP 服务器")
    print("=" * 60)
    print(f"主机: {args.host}")
    print(f"端口: {args.port}")
    print(f"后台模式: {'是' if args.background else '否'}")
    print("-" * 60)
    
    if args.background:
        print("正在后台启动服务器...")
        server_thread = start_server_in_background(args.port, args.host)
        
        print(f"服务器已在后台启动，访问地址: http://{args.host}:{args.port}")
        print("按 Ctrl+C 停止程序（服务器将继续运行）")
        
        try:
            # 保持主线程运行
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n程序已停止，服务器仍在后台运行")
            print("要停止服务器，请使用 kill 命令或重启终端")
    else:
        print(f"正在启动服务器，访问地址: http://{args.host}:{args.port}")
        print("按 Ctrl+C 停止服务器")
        print("-" * 60)
        
        try:
            start_server(args.port, args.host)
        except OSError as e:
            if "Address already in use" in str(e):
                print(f"错误: 端口 {args.port} 已被占用")
                print("请尝试使用其他端口: python run_html_server.py -p 8888")
                sys.exit(1)
            else:
                raise


if __name__ == "__main__":
    main()
