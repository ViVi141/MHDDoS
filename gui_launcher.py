#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MHDDoS GUI启动器 - 检查依赖并启动GUI"""

import sys
import os
from pathlib import Path

def is_admin():
    """检查是否已有管理员权限"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def run_as_admin():
    """请求管理员权限并重新启动程序"""
    if is_admin():
        return True
    
    try:
        import ctypes
        # 获取当前脚本的完整路径
        script_path = os.path.abspath(__file__)
        # 使用ShellExecute以管理员权限重新运行
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, script_path, None, 1
        )
        return False  # 返回False表示已请求提升，原进程应退出
    except Exception as e:
        print(f"请求管理员权限失败: {e}")
        print("请手动以管理员身份运行此程序")
        return False

def check_dependencies():
    """检查依赖"""
    missing = []
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("错误: 需要Python 3.8或更高版本")
        return False
    
    # 检查必要的模块
    required_modules = [
        ("tkinter", "tkinter"),
        ("yarl", "yarl"),
        ("requests", "requests"),
        ("dnspython", "dns"),
        ("cloudscraper", "cloudscraper"),
        ("psutil", "psutil"),
        ("icmplib", "icmplib"),
    ]
    
    for module_name, import_name in required_modules:
        try:
            __import__(import_name)
        except ImportError:
            missing.append(module_name)
    
    if missing:
        print("缺少以下依赖模块:")
        for m in missing:
            print(f"  - {m}")
        print("\n请运行: pip install -r requirements.txt")
        return False
    
    # 检查start.py
    if not Path("start.py").exists():
        print("错误: 找不到start.py文件")
        print("请确保在MHDDoS项目根目录下运行")
        return False
    
    return True

def main():
    """主函数"""
    # Windows系统：检查并请求管理员权限
    if sys.platform == "win32":
        if not is_admin():
            print("MHDDoS GUI工具启动器")
            print("=" * 50)
            print("检测到需要管理员权限...")
            print("正在请求管理员权限...")
            print()
            
            if not run_as_admin():
                # 如果请求成功，当前进程应该退出
                sys.exit(0)
            else:
                # 如果已经是管理员，继续执行
                pass
    
    print("MHDDoS GUI工具启动器")
    print("=" * 50)
    
    # 显示权限状态
    if sys.platform == "win32":
        if is_admin():
            print("✓ 已获得管理员权限")
        else:
            print("⚠ 警告: 未获得管理员权限，某些功能可能无法使用")
            print("  (SYN、ICMP等原始套接字方法需要管理员权限)")
        print()
    
    if not check_dependencies():
        print("\n依赖检查失败，请安装缺失的依赖后重试")
        input("按Enter键退出...")
        sys.exit(1)
    
    print("依赖检查通过，启动GUI...")
    print()
    
    # 启动GUI
    try:
        import gui
        gui.main()
    except Exception as e:
        print(f"启动GUI失败: {e}")
        import traceback
        traceback.print_exc()
        input("按Enter键退出...")
        sys.exit(1)

if __name__ == "__main__":
    main()

