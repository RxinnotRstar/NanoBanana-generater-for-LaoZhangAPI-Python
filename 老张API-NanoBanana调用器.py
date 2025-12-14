# ====================================================
#         警告：不要直接在顶部导入"第三方"依赖！
# 请按照说明，使用正确的方法添加新的依赖，确保防呆机制生效
# ====================================================
import sys
import platform
import subprocess
import time
import os

# ================ 依赖检查与自动安装模块 ================
# 这是一个针对用户的防呆设计，可以自动检测并安装缺失的依赖
# 如果缺依赖，程序会提示用户，并尝试自动安装，而不是直接崩溃
# 这样可以提升用户体验，尤其是对于不熟悉Python环境的小白用户
# 
# 添加新依赖的方式：
#
# 1. 在下面列表中添加：("pip包名", "import名")
#
# 2. 搜索"现在可以安全导入第三方库"，添加 import 语句，
#    大约在第200行附近，根据需要添加新的 import。
#
#    【两处都要改，缺一不可！】
#
# ================= 在这里定义所需依赖 =================

REQUIRED_DEPENDENCIES = [
    ("requests", "requests"),
    ("Pillow", "PIL"),
]

# ==============以下是依赖检查与安装逻辑=================

# 获取系统信息的辅助函数
def _get_system_info():
    """获取详细的系统信息"""
    system = platform.system()
    # 针对Windows系统
    if system == "Windows":
        version = platform.version()
        return f"Windows {platform.release()} (版本: {version})"
    # 针对macOS系统
    elif system == "Darwin":
        mac_version = platform.mac_ver()[0]
        return f"macOS {mac_version}"
    # 针对Linux系统
    elif system == "Linux":
        # 尝试识别Linux发行版
        try:
            with open("/etc/os-release", "r") as f:
                os_info = f.read().lower()
            # 简单判断常见发行版
            if "ubuntu" in os_info:
                return "Ubuntu Linux"
            elif "debian" in os_info:
                return "Debian Linux"
            elif "centos" in os_info:
                return "CentOS Linux"
            elif "fedora" in os_info:
                return "Fedora Linux"
            elif "arch" in os_info:
                return "Arch Linux"
            else:
                return "Linux (发行版未知)"
        except:
            # 检查常见的包管理器，进一步推测发行版
            try:
                if subprocess.run(["which", "apt"], capture_output=True).returncode == 0:
                    return "Linux (基于Debian/Ubuntu)"
                elif subprocess.run(["which", "yum"], capture_output=True).returncode == 0:
                    return "Linux (基于RHEL/CentOS)"
                elif subprocess.run(["which", "dnf"], capture_output=True).returncode == 0:
                    return "Linux (基于Fedora/RHEL)"
                elif subprocess.run(["which", "pacman"], capture_output=True).returncode == 0:
                    return "Linux (基于Arch)"
                else:
                    return "Linux (未知发行版)"
            except:
                return "Linux (检测失败)"
    
    return system

# 生成安装命令的辅助函数
def _get_install_command(package_name, system_info):
    """根据系统生成安装命令"""
    # Windows 系统
    if "Windows" in system_info:
        return f"pip install --user {package_name}"
    # macOS 系统
    elif "macOS" in system_info:
        return f"pip3 install --user {package_name}"
    # Linux 和其他系统
    else:
        return f"pip3 install --user {package_name}"

# 主检查与安装函数
def _check_and_handle_dependencies():
    """检查依赖，如果缺失则提示用户并尝试安装"""
    missing_deps = []
    
    # 检查每个依赖
    for pip_name, import_name in REQUIRED_DEPENDENCIES:
        # 尝试导入模块
        try:
            __import__(import_name)
        # 捕获导入错误
        except ImportError:
            missing_deps.append((pip_name, import_name))
    # 如果没有缺失的依赖，直接返回
    if not missing_deps:
        return  # 所有依赖都已安装
    
    # 获取系统信息
    system_info = _get_system_info()
    
    # 构建错误消息
    error_lines = [
        "缺少必要的依赖包！",
        "",
        f"系统: {system_info}", 
        "",
        "缺失的依赖包:",
    ]
    # 生成安装命令列表
    install_commands = []
    # 列出缺失的依赖
    for pip_name, import_name in missing_deps:
        error_lines.append(f"  - {pip_name}")
        install_commands.append(_get_install_command(pip_name, system_info))
    # 添加安装提示
    error_lines.extend([
        "",
        "您可以手动运行以下命令安装:",
        "  " + " && ".join(install_commands),
        "",
        "或者按Enter键尝试自动安装 (将安装到用户目录)",
    ])
    
    # 显示错误信息
    print("\n" + "="*60)
    print("\n".join(error_lines))
    print("="*60 + "\n")
    
    # 询问是否尝试自动安装
    try:
        user_input = input("是否尝试自动安装缺失的包? (按Enter开始，输入n取消): ")
        # 用户选择取消
        if user_input.lower() == 'n':
            print("取消自动安装，程序将在5秒后退出...")
            time.sleep(5)
            sys.exit(1)
        # 尝试自动安装缺失的依赖
        print("\n正在尝试自动安装...")
        for pip_name, import_name in missing_deps:
            cmd = install_commands[missing_deps.index((pip_name, import_name))]
            print(f"安装 {pip_name}...")
            # 执行安装命令
            try:
                result = subprocess.run(cmd.split(), capture_output=True, text=True, check=True)
                print(f"[OK] {pip_name} 安装成功")
            
            except subprocess.CalledProcessError as e:
                print(f"[FAIL] {pip_name} 安装失败: {e.stderr}")
                print("\n建议手动运行命令安装，或联系系统管理员")
                time.sleep(5)
                sys.exit(1)
    
        print("\n所有依赖安装完成！正在启动程序...")
        time.sleep(2)
        
        # 重新检查是否安装成功
        for pip_name, import_name in missing_deps:
            try:
                __import__(import_name)
            except ImportError:
                print(f"警告: 安装后仍然无法导入 {pip_name}")
                print("请手动检查安装")
                time.sleep(3)
                sys.exit(1)
    # 捕获用户中断和其他异常
    except KeyboardInterrupt:
        print("\n用户中断，程序退出")
        sys.exit(1)
    except Exception as e:
        print(f"\n发生错误: {e}")
        print("程序将在5秒后退出...")
        time.sleep(5)
        sys.exit(1)

# 依赖检查结束，开始加载程序

# 在导入第三方依赖之前先执行检查
_check_and_handle_dependencies()

# 依赖检查通过，开始加载程序
print("\n" + "="*60)
print("正在加载核心模块，请稍候...")
print("="*60)

# ================= 现在可以安全导入第三方库 ==================
import requests
from PIL import Image, ImageTk

# 开始程序主逻辑
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font
from datetime import datetime
import base64
import threading
import json
import io
import ctypes
import tempfile

# 所有模块加载完成
print("核心模块加载完成")
print("正在初始化图形界面...\n")

class GeminiImageGenerator:
    # ==================== 集中定义的常量 ====================
    # 最大参考图片数量
    MAX_REF_IMAGES = 14
    # 最大提示词长度
    MAX_PROMPT_CHARS = 2000
    # 单张图片大小警告阈值 (MB)，超过此值将提示用户但仍允许使用
    # 开发者可根据需要修改此数值
    MAX_IMAGE_SIZE_MB = 10
    # 模型配置
    MODEL_CONFIGS = {
        "gemini-2.5-flash-image": {
            "resolutions": ["1K"],
            "stable": True,
            "display_name": "稳定版"
        },
        "gemini-3-pro-image-preview": {
            "resolutions": ["1K", "2K", "4K"],
            "stable": False,
            "display_name": "最新版"
        }
    }
    # ==================== 初始化与UI构建 ====================
    def __init__(self, root):
        self.root = root
        
        # 高DPI支持
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            pass
        # 设置窗口标题和大小
        self.root.title("老张API-NanoBanana图片生成器")
        self.root.geometry("1100x700")
        
        # 配置变量
        # API密钥
        self.api_key = tk.StringVar()
        # 默认选择最新版模型
        self.model_var = tk.StringVar(value="gemini-3-pro-image-preview")
        # 生成参数
        self.aspect_ratio = tk.StringVar(value="1:1")
        # 默认分辨率4K（如果模型支持）
        self.resolution = tk.StringVar(value="4K")
        # 日志记录选项
        self.log_to_file = tk.BooleanVar(value=False)
        # 网络超时设置
        self.network_timeout = tk.StringVar(value="1200")
        # 界面缩放
        self.zoom_var = tk.StringVar(value="100%")
        
        # 数据存储
        # 参考图片列表，存储格式为 (文件路径, base64字符串, mime类型, 原始PIL图像)
        self.reference_images = []
        # 当前生成的图片数据（base64）
        self.current_image_data = None
        # 当前生成的图片预览（PIL ImageTk 对象）
        self.current_image_preview = None
        # 最后一次的原始响应数据
        self.last_raw_response = None
        
        # UI状态存储（用于缩放切换）
        self._ui_state_cache = {}
        
        # 线程控制
        self.generate_thread = None
        # 构建UI
        self.setup_ui()
        self.setup_window_behavior()
        # 初始化完成

    # ==================== 界面构建函数 ====================
    def setup_ui(self):
        """构建左右分区的用户界面"""
        # 主分区
        self.main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=4, bg="#ccc")
        self.main_paned.pack(fill=tk.BOTH, expand=True)
        # 左侧面板
        left_panel = ttk.Frame(self.main_paned)
        self.main_paned.add(left_panel, width=600)
        # 右侧面板
        right_panel = ttk.Frame(self.main_paned)
        self.main_paned.add(right_panel, width=500)

        # ===== 左侧面板内容 =====
        # 界面缩放控制（无框，独立显示在API配置上方）
        zoom_frame = ttk.Frame(left_panel)
        zoom_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
        ttk.Label(zoom_frame, text="界面缩放:").pack(side=tk.LEFT, padx=(0, 5))
        zoom_combo = ttk.Combobox(zoom_frame, textvariable=self.zoom_var, 
                                  values=["75%", "100%", "125%", "150%", "175%", "200%", "250%", "300%"],
                                  state="readonly", width=6)
        zoom_combo.bind("<<ComboboxSelected>>", self.on_zoom_change)
        zoom_combo.pack(side=tk.LEFT)
        # API配置区域
        api_frame = ttk.LabelFrame(left_panel, text="API配置", padding=10)
        api_frame.pack(fill=tk.X, pady=5, padx=5)
        # API密钥输入
        ttk.Label(api_frame, text="API密钥:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        api_entry = ttk.Entry(api_frame, textvariable=self.api_key, show="*", width=40)
        api_entry.grid(row=0, column=1, sticky=tk.W)
        self.api_key_entry = api_entry
        # 显示/隐藏API密钥按钮
        def toggle_key_visibility():
            if api_entry['show'] == '*':
                api_entry.config(show='')
                toggle_btn.config(text='隐藏')
            else:
                api_entry.config(show='*')
                toggle_btn.config(text='显示')
        # 绑定回车键触发生成
        toggle_btn = ttk.Button(api_frame, text='显示', command=toggle_key_visibility, width=4)
        toggle_btn.grid(row=0, column=2, padx=(5, 0))
        # 模型选择
        ttk.Label(api_frame, text="模型:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0), padx=(0, 10))
        model_combo = ttk.Combobox(api_frame, textvariable=self.model_var, 
                                   values=list(self.MODEL_CONFIGS.keys()),
                                   state="readonly", width=30)
        # 绑定模型选择事件
        model_combo.grid(row=1, column=1, sticky=tk.W, pady=(10, 0), padx=(0, 10))
        model_combo.bind("<<ComboboxSelected>>", self.on_model_change)
        # 日志记录选项
        ttk.Label(api_frame, text="日志记录:").grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        log_check = ttk.Checkbutton(api_frame, text="保存日志到文件", variable=self.log_to_file,
                                   command=self.on_log_toggle)
        log_check.grid(row=2, column=1, sticky=tk.W, pady=(10, 0))
        
        # 网络超时设置
        ttk.Label(api_frame, text="网络超时(秒):").grid(row=2, column=2, sticky=tk.W, padx=(20, 5), pady=(10, 0))
        timeout_entry = ttk.Entry(api_frame, textvariable=self.network_timeout, width=8, validate='key',
                                 validatecommand=(self.root.register(self._validate_timeout), '%P'))
        timeout_entry.grid(row=2, column=3, sticky=tk.W, pady=(10, 0))
        
        
        # 提示词区域
        prompt_frame = ttk.LabelFrame(left_panel, text="提示词 (必填)", padding=10)
        prompt_frame.pack(fill=tk.X, pady=5, padx=5)
        # 提示词输入框
        self.prompt_text = tk.Text(prompt_frame, height=12, font=("TkDefaultFont", 10))
        self.prompt_text.pack(fill=tk.BOTH, expand=True)
        # 字符计数标签
        def update_char_count(event=None):
            count = len(self.prompt_text.get("1.0", "end-1c"))
            self.char_label.config(text=f"{count}/{self.MAX_PROMPT_CHARS}")
            self.char_label.config(foreground="red" if count > self.MAX_PROMPT_CHARS else "green")
        # 初始字符计数
        self.char_label = ttk.Label(prompt_frame, text=f"0/{self.MAX_PROMPT_CHARS}", font=("TkDefaultFont", 9))
        self.char_label.pack(anchor=tk.E)
        self.prompt_text.bind('<KeyRelease>', update_char_count)
        
        # 参考图片区域
        ref_frame = ttk.LabelFrame(left_panel, text=f"参考图片 (可选, 最多{self.MAX_REF_IMAGES}张)", padding=10)
        ref_frame.pack(fill=tk.X, pady=5, padx=5)
        # 参考图片按钮和计数
        ref_btn_frame = ttk.Frame(ref_frame)
        ref_btn_frame.pack(fill=tk.X)
        # 添加图片和清空按钮
        ttk.Button(ref_btn_frame, text="添加图片", command=self.add_images, width=12).pack(side=tk.LEFT)
        ttk.Button(ref_btn_frame, text="清空全部", command=self.clear_images, width=12).pack(side=tk.LEFT, padx=10)
        # 参考图片计数标签
        self.ref_count_label = ttk.Label(ref_btn_frame, text=f"已选择: 0/{self.MAX_REF_IMAGES}张", font=("TkDefaultFont", 9, "bold"))
        self.ref_count_label.pack(side=tk.LEFT, padx=20)
        # 参考图片预览区域（带水平滚动条）
        ref_canvas_container = ttk.Frame(ref_frame)
        ref_canvas_container.pack(fill=tk.X, pady=5, expand=True)
        # 参考图片Canvas
        self.ref_canvas = tk.Canvas(ref_canvas_container, height=100, bg="#f0f0f0", relief=tk.SUNKEN)
        self.ref_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True)
        # 水平滚动条
        ref_scrollbar = ttk.Scrollbar(ref_canvas_container, orient=tk.HORIZONTAL, command=self.ref_canvas.xview)
        ref_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.ref_canvas.config(xscrollcommand=ref_scrollbar.set)
        # 初始化参考图片预览
        # 参数设置区域
        param_frame = ttk.LabelFrame(left_panel, text="生成参数", padding=10)
        param_frame.pack(fill=tk.X, pady=5, padx=5)
        # 参数设置网格
        param_grid = ttk.Frame(param_frame)
        param_grid.pack(fill=tk.X)
        # 纵横比和分辨率选择
        ttk.Label(param_grid, text="纵横比:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        aspect_combo = ttk.Combobox(param_grid, textvariable=self.aspect_ratio,
                                   values=["21:9", "16:9", "4:3", "3:2", "1:1", 
                                           "9:16", "3:4", "2:3", "5:4", "4:5"],
                                   state="readonly", width=10)
        aspect_combo.grid(row=0, column=1, sticky=tk.W)
        # 分辨率选择
        ttk.Label(param_grid, text="分辨率:").grid(row=0, column=2, sticky=tk.W, padx=(30, 10))
        self.resolution_combo = ttk.Combobox(param_grid, textvariable=self.resolution,
                                            values=["1K"], state="readonly", width=10)
        self.resolution_combo.grid(row=0, column=3, sticky=tk.W)

        # 生成按钮（底部，自动调整大小）
        self.generate_btn = ttk.Button(param_frame, text="生成图片", 
                                      command=self.generate_image)
        self.generate_btn.pack(fill=tk.X, padx=5, pady=(10, 5))
        # 状态栏
        status_frame = ttk.Frame(left_panel)
        status_frame.pack(fill=tk.X, pady=5, padx=5)
        self.status_var = tk.StringVar(value="就绪")
        # 旧的状态栏实现，会导致标签宽度不自适应，改为expand=True
        # ttk.Label(status_frame, textvariable=self.status_var, relief=tk.SUNKEN, 
        #          font=("TkDefaultFont", 9)).pack(fill=tk.X)
        ttk.Label(status_frame, textvariable=self.status_var, relief=tk.SUNKEN,
                 font=("TkDefaultFont", 9)).pack(fill=tk.X, expand=True)

        # ===== 右侧面板内容 =====
        # 输出预览区域
        output_frame = ttk.LabelFrame(right_panel, text="输出预览", padding=10)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        # 输出选项卡
        self.output_notebook = ttk.Notebook(output_frame)
        self.output_notebook.pack(fill=tk.BOTH, expand=True)
        # 图片预览标签页
        img_tab = ttk.Frame(self.output_notebook)
        self.output_notebook.add(img_tab, text="生成的图片")
        # 图片预览区域
        self.img_preview = ttk.Label(img_tab, text="生成的图片将在此显示", 
                                    relief=tk.SUNKEN, anchor=tk.CENTER, background="white")
        self.img_preview.pack(fill=tk.BOTH, expand=True)
        # 图片操作按钮
        btn_frame = ttk.Frame(img_tab)
        btn_frame.pack(pady=10)
        self.save_btn = ttk.Button(btn_frame, text="保存图片", 
                                  command=self.save_image, state=tk.DISABLED, width=18)
        self.save_btn.pack(side=tk.LEFT, padx=5)

        # 根据平台设置复制按钮文案
        copy_text = "复制图片 (BMP)" if platform.system() == "Windows" else "复制图片"
        self.copy_btn = ttk.Button(btn_frame, text=copy_text, 
                                  command=self.copy_to_clipboard, state=tk.DISABLED, width=18)
        self.copy_btn.pack(side=tk.LEFT, padx=5)
        # 原始响应标签页
        response_tab = ttk.Frame(self.output_notebook)
        self.output_notebook.add(response_tab, text="原始响应")
        # 响应文本区域（带滚动条）
        response_container = ttk.Frame(response_tab)
        response_container.pack(fill=tk.BOTH, expand=True)
        # 响应文本框
        self.response_text = tk.Text(response_container, wrap=tk.WORD, font=("Consolas", 9), height=12)
        self.response_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        # 垂直滚动条
        scroll_y = ttk.Scrollbar(response_container, orient=tk.VERTICAL, command=self.response_text.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        # 水平滚动条
        scroll_x = ttk.Scrollbar(response_tab, orient=tk.HORIZONTAL, command=self.response_text.xview)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        # 绑定滚动条
        self.response_text.config(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        # 响应操作按钮
        resp_btn_frame = ttk.Frame(response_tab)
        resp_btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        # 保存原始JSON按钮
        ttk.Button(resp_btn_frame, text="保存原始JSON", 
                  command=self.save_raw_response, width=18).pack(side=tk.LEFT)
        # 显示完整数据按钮
        ttk.Button(resp_btn_frame, text="显示完整数据", 
                  command=self.show_full_data, width=18).pack(side=tk.LEFT, padx=10)
        # 插入数据警告按钮
        self.response_text.bind('<Button-1>', lambda e: self._insert_data_warning())

        # 根据当前模型更新UI状态，确保启动时分辨率选项正确
        self.on_model_change()

    # ==================== 核心功能实现 ====================
    # 获取当前模型的 API 端点
    def get_api_url(self):
        """获取当前模型的 API 端点"""
        model_id = self.model_var.get()
        return f"https://api.laozhang.ai/v1beta/models/{model_id}:generateContent"
    # 根据文件扩展名获取 MIME 类型
    def get_mime_type(self, filepath):
        """根据文件扩展名获取 MIME 类型"""
        ext = os.path.splitext(filepath)[1].lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp'
        }
        return mime_types.get(ext, 'image/jpeg')
    # 添加参考图片
    def add_images(self):
        """添加多张参考图片"""
        # 打开文件对话框选择图片
        filepaths = filedialog.askopenfilenames(
            title="选择参考图片", # 这里是文件对话框的标题
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.webp"), ("所有文件", "*.*")] # 只允许选择图片文件
        )
        # 没有选择图片则返回
        if not filepaths:
            return
        # 检查是否超过最大数量
        available_slots = self.MAX_REF_IMAGES - len(self.reference_images)
        if len(filepaths) > available_slots: 
            messagebox.showwarning("警告", f"最多只能添加{self.MAX_REF_IMAGES}张参考图片，当前已选择{len(self.reference_images)}张")
            filepaths = filepaths[:available_slots]
        # 逐个处理选择的图片
        for filepath in filepaths:
            try:
                # 验证文件大小并发出警告
                file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
                if file_size_mb > self.MAX_IMAGE_SIZE_MB:
                    warning_msg = f"图片较大: {os.path.basename(filepath)}\n大小: {file_size_mb:.1f}MB (警告阈值: {self.MAX_IMAGE_SIZE_MB}MB)\n\n大图片可能导致上传速度变慢或API调用失败。\n\n是否仍要导入这张图片？"
                    if not messagebox.askyesno("图片大小警告", warning_msg, icon=messagebox.WARNING):
                        continue
                
                # 读取并编码图片
                with open(filepath, "rb") as f:
                    image_b64 = base64.b64encode(f.read()).decode("utf-8")
                
                # 读取原始图片并生成缩略图
                mime_type = self.get_mime_type(filepath)
                # 修复：正确读取原始图片对象
                original_img = Image.open(filepath)
                # 存储：文件路径, base64, mime类型, 原始PIL图像
                self.reference_images.append((filepath, image_b64, mime_type, original_img))
                
            # 捕获异常并提示
            except Exception as e:
                messagebox.showerror("错误", f"加载图片失败: {filepath}\n{str(e)}")
        # 更新预览
        self.update_reference_preview()
        self.status_var.set(f"已添加 {len(filepaths)} 张参考图片")

    def update_reference_preview(self):
        """更新参考图片预览"""
        self.ref_canvas.delete("all")
        x_offset = 5
        
        # 获取当前缩放比例
        zoom_str = self.zoom_var.get().rstrip('%')
        try:
            scale = int(zoom_str) / 100.0
        except:
            scale = 1.0
        
        # 固定缩略图尺寸为120x120，确保高缩放倍率下清晰可见
        thumb_size = 120
        # 根据缩放比例调整显示尺寸
        for idx, (filepath, _, _, original_img) in enumerate(self.reference_images):
            # 从缓存的原始图像重新生成缩略图
            thumb_img = original_img.copy()
            thumb_img.thumbnail((thumb_size, thumb_size), Image.Resampling.LANCZOS)
            
            # 将 PIL 图像转换为 Tkinter 可用格式
            tk_img = ImageTk.PhotoImage(thumb_img)
            
            # 在 canvas 上创建图像
            img_id = self.ref_canvas.create_image(
                x_offset, 5, anchor=tk.NW, image=tk_img
            )
            
            # 保存引用防止被垃圾回收
            if idx == 0:
                self.ref_canvas.image_dict = {}
            self.ref_canvas.image_dict[img_id] = tk_img
            
            # 删除按钮位置动态计算
            btn_x = x_offset + thumb_size - 18
            del_btn = tk.Button(
                self.ref_canvas, text="×", fg="red", bg="white",
                command=lambda i=idx: self.remove_reference(i),
                font=("TkDefaultFont", 8), width=2, height=1,
                bd=1, relief=tk.RAISED, activebackground="#ffd4d4"
            )
            self.ref_canvas.create_window(btn_x, 5, anchor=tk.NW, window=del_btn)
            
            x_offset += thumb_size + 10  # 每张图占用的宽度
        
        # 更新滚动区域
        self.ref_canvas.config(scrollregion=(0, 0, x_offset, thumb_size + 10))
        self.ref_count_label.config(text=f"已选择: {len(self.reference_images)}/{self.MAX_REF_IMAGES}张")
    # 删除参考图片
    def remove_reference(self, index):
        """删除指定参考图片"""
        if 0 <= index < len(self.reference_images):
            del self.reference_images[index]
            self.update_reference_preview()
            self.status_var.set(f"已删除第 {index+1} 张参考图片")
    # 清空参考图片
    def clear_images(self):
        """清空所有参考图片"""
        if not self.reference_images:
            return
        # 确认清空
        if messagebox.askyesno("确认", f"确定要清空 {len(self.reference_images)} 张参考图片吗？"):
            self.reference_images.clear()
            self.ref_canvas.delete("all")
            self.ref_count_label.config(text=f"已选择: 0/{self.MAX_REF_IMAGES}张")
            self.status_var.set("已清空所有参考图片")
    # 生成图片
    def generate_image(self):
        """开始生成图片"""
        # 验证输入
        if not self.api_key.get().strip():
            messagebox.showerror("错误", "请先填写 API 密钥")
            return
        # 获取提示词
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showerror("错误", "提示词不能为空")
            return
        
        # 检查是否存在大图片并二次警告
        large_images = []
        for filepath, _, _, _ in self.reference_images:
            file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
            if file_size_mb > self.MAX_IMAGE_SIZE_MB:
                large_images.append((os.path.basename(filepath), file_size_mb))
        
        if large_images:
            file_list = "\n".join([f"  - {name} ({size:.1f}MB)" for name, size in large_images])
            warning_msg = f"检测到 {len(large_images)} 张图片超过警告阈值 ({self.MAX_IMAGE_SIZE_MB}MB):\n\n{file_list}\n\n大图片可能导致:\n  - 上传时间增加\n  - API响应变慢\n  - 请求超时或失败\n\n是否仍要继续生成？"
            if not messagebox.askyesno("最终确认", warning_msg, icon=messagebox.WARNING):
                self.status_var.set("用户取消生成")
                return
        
        # 禁用生成按钮
        self.generate_btn.config(state=tk.DISABLED, text="生成中...")
        self.status_var.set("正在生成图片...")
        
        # 在后台线程中执行
        self.generate_thread = threading.Thread(
            target=self._generate_thread,
            args=(self.api_key.get(), prompt),
            daemon=True
        )
        self.generate_thread.start()
    # 后台线程生成图片
    def _generate_thread(self, api_key, prompt):
        """后台线程执行API调用"""
        try:
            # 构建请求数据
            parts = [{"text": prompt}]
            
            # 添加参考图片 - 修复：改为4项解包（文件路径、base64、mime_type、原始PIL图像）
            for filepath, image_b64, mime_type, original_img in self.reference_images:
                parts.append({
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": image_b64
                    }
                })
            # 构建完整请求负载
            payload = {
                "contents": [{
                    "parts": parts
                }],
                "generationConfig": {
                    "responseModalities": ["IMAGE"],
                    "imageConfig": {
                        "aspectRatio": self.aspect_ratio.get()
                    }
                }
            }
            
            # Nano Banana 2 支持分辨率参数
            if self.model_var.get() == "gemini-3-pro-image-preview":
                payload["generationConfig"]["imageConfig"]["imageSize"] = self.resolution.get()
            
            # 发送请求
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # 获取超时设置，0表示无超时
            timeout_val = int(self.network_timeout.get()) if self.network_timeout.get().isdigit() else 1200
            timeout = None if timeout_val == 0 else timeout_val
            
            response = requests.post(
                self.get_api_url(),
                headers=headers,
                json=payload,
                timeout=timeout
            )
            
            # 在主线程中处理响应
            self.root.after(0, self._handle_response, response)
        # 捕获异常并在主线程中处理
        except Exception as e:
            self.root.after(0, self._handle_error, str(e))
    # 处理API响应
    def _handle_response(self, response):
        """处理API响应"""
        try:
            # 检查HTTP状态码
            if response.status_code != 200:
                error_msg = f"HTTP错误 {response.status_code}: {response.text}"
                messagebox.showerror("API错误", error_msg)
                self.status_var.set(f"生成失败: HTTP {response.status_code}")
                # **改进：记录错误日志**
                if self.log_to_file.get():
                    self._save_log({"error": error_msg, "status_code": response.status_code}, "error")
                return
            # 解析JSON响应
            result = response.json()
            self.last_raw_response = result  # 保存原始响应
            
            # 检查API错误
            if "error" in result:
                error_msg = result["error"].get("message", str(result["error"]))
                messagebox.showerror("API错误", error_msg)
                self.status_var.set("生成失败: API错误")
                # **改进：记录错误日志**
                if self.log_to_file.get():
                    self._save_log({"error": error_msg, "raw_response": result}, "error")
                return
            
            # 提取图片数据
            try:
                if "candidates" not in result or not result["candidates"]:
                    raise ValueError("响应中未找到 candidates 数据")
                
                candidate = result["candidates"][0]
                if "content" not in candidate or candidate["content"] is None:
                    finish_reason = candidate.get("finishReason", "未知")
                    safety_ratings = candidate.get("safetyRatings", [])
                    raise ValueError(
                        f"内容生成失败，finishReason: {finish_reason}\n"
                        f"安全评级: {safety_ratings}"
                    )
                # 提取图片Base64数据
                if "parts" not in candidate["content"] or not candidate["content"]["parts"]:
                    raise ValueError("响应中未找到图片数据")
                
                image_data = candidate["content"]["parts"][0]["inlineData"]["data"]
                self.current_image_data = image_data
                
                # 显示图片
                self._show_image()
                
                # 优化显示数据
                display_data = self._optimize_display_data(result)
                self.response_text.delete("1.0", tk.END)
                self.response_text.insert("1.0", json.dumps(display_data, indent=2, ensure_ascii=False))
                
                self.save_btn.config(state=tk.NORMAL)
                self.copy_btn.config(state=tk.NORMAL)
                self.status_var.set("生成成功")
                
                # 记录日志
                if self.log_to_file.get():
                    self._save_log(result, "success")
            # 捕获解析错误
            except (KeyError, IndexError, ValueError) as e:
                messagebox.showerror("响应错误", f"处理API响应失败:\n{str(e)}")
                self.response_text.delete("1.0", tk.END)
                self.response_text.insert("1.0", json.dumps(result, indent=2, ensure_ascii=False))
                self.status_var.set(f"生成失败: {str(e)[:50]}...")
        # 捕获异常并提示
        finally:
            self.generate_btn.config(state=tk.NORMAL, text="生成图片")
    # 处理异常错误
    def _handle_error(self, error_msg):
        """处理异常错误"""
        messagebox.showerror("错误", f"生成过程中发生异常:\n{error_msg}")
        self.status_var.set("生成失败: 异常错误")
        self.generate_btn.config(state=tk.NORMAL, text="生成图片")
        
        # **改进：记录错误日志**
        if self.log_to_file.get():
            self._save_log({"error": error_msg, "exception": True}, "error")
    # 优化显示数据
    def _optimize_display_data(self, data, max_str_len=500):
        """**改进：统一处理数据优化，避免重复检测**"""
        if isinstance(data, dict):
            return {k: self._optimize_display_data(v, max_str_len) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._optimize_display_data(item, max_str_len) for item in data]
        elif isinstance(data, str):
            # **统一检测：先判Base64，再判长度**
            if self._is_likely_base64(data):
                return f"<BASE64_IMAGE({len(data)} chars)>"
            if len(data) > max_str_len:
                return data[:max_str_len] + f"...({len(data)} chars)"
            return data
        else:
            return data
    # 检测Base64字符串
    def _is_likely_base64(self, s):
        """检测字符串是否可能是base64编码"""
        return len(s) > 100 and len(s) % 4 == 0 and all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=' for c in s[:100])
    # 显示生成的图片
    def _show_image(self):
        """显示生成的图片"""
        if not self.current_image_data:
            return

        try:
            # 解码Base64数据并保存原始图片
            image_bytes = base64.b64decode(self.current_image_data)
            self.original_image = Image.open(io.BytesIO(image_bytes))
            
            # 初始显示图片
            self._resize_image()
            
            # 绑定窗口大小变化事件
            self.img_preview.bind('<Configure>', lambda e: self._resize_image())
        # 捕获异常并提示
        except Exception as e:
            messagebox.showerror("显示错误", f"无法显示生成的图片:\n{str(e)}")
            self.img_preview.config(text="显示失败", image="")
    # 根据预览区域大小调整图片
    def _resize_image(self, event=None):
        """根据预览区域大小调整图片"""
        if not hasattr(self, 'original_image') or not self.original_image:
            return
        # 调整图片大小以适应预览区域
        try:
            # 获取预览区域尺寸
            preview_width = self.img_preview.winfo_width()
            preview_height = self.img_preview.winfo_height()
            
            if preview_width <= 1 or preview_height <= 1:
                return
            
            # 创建副本并调整大小
            img_copy = self.original_image.copy()
            img_copy.thumbnail((preview_width - 20, preview_height - 20), Image.Resampling.LANCZOS)
            
            # 转换为Tkinter格式
            tk_img = ImageTk.PhotoImage(img_copy)
            self.current_image_preview = tk_img  # 保持引用
            
            # 显示图片
            self.img_preview.config(image=tk_img, text="")
            
        except Exception as e:
            # 静默处理缩放过程中的错误，避免频繁弹窗
            print(f"图片缩放失败: {e}")

    def save_image(self):
        """保存生成的图片"""
        if not self.current_image_data:
            messagebox.showwarning("警告", "没有可保存的图片")
            return
        
        # 生成默认文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_short = self.model_var.get().split("-")[1]  # "2.5" 或 "3"
        default_filename = f"gemini_{model_short}_{self.resolution.get()}_{timestamp}.png"
        # 打开保存对话框
        filepath = filedialog.asksaveasfilename(
            title="保存图片",
            defaultextension=".png",
            filetypes=[("PNG图片", "*.png"), ("所有文件", "*.*")],
            initialfile=default_filename
        )
        # 用户取消保存
        if not filepath:
            return
        # 保存图片文件
        try:
            image_bytes = base64.b64decode(self.current_image_data)
            with open(filepath, "wb") as f:
                f.write(image_bytes)
            # 更新状态栏
            self.status_var.set(f" 图片已保存: {os.path.basename(filepath)}")
            
            # 记录日志
            if self.log_to_file.get():
                self._save_log({"saved_file": filepath}, "save")
                # 可选：提示保存成功
                # messagebox.showinfo("成功", f"图片已保存: {filepath}")
                # 或者改为状态栏提示，避免频繁弹窗
                # self.status_var.set(f" 图片已保存: {os.path.basename(filepath)}")
        except Exception as e:
            messagebox.showerror("保存错误", f"无法保存图片:\n{str(e)}")
    # 复制图片到剪贴板
    def copy_to_clipboard(self):
        """复制图片到系统剪贴板（支持多平台）"""
        if not self.current_image_data:
            messagebox.showwarning("警告", "没有可复制的图片")
            return
        # 根据平台调用不同方法
        try:
            image_bytes = base64.b64decode(self.current_image_data)
            img = Image.open(io.BytesIO(image_bytes))
            # 检测平台
            system = platform.system()
            # 调用对应方法
            if system == "Windows":
                self._copy_image_windows(img)
            elif system == "Darwin":
                self._copy_image_macos(image_bytes)
            else:
                self._copy_image_linux(image_bytes)
            
            messagebox.showinfo("成功", "图片已复制到剪贴板！")
            
        except Exception as e:
            messagebox.showerror("复制错误", f"复制失败:\n{str(e)}")
    # Windows平台复制图片
    def _copy_image_windows(self, img):
        """Windows平台使用Win32 API复制图片"""
        from ctypes import wintypes
        # 使用ctypes调用Win32 API
        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32
        kernel32 = ctypes.windll.kernel32
        # 打开剪贴板
        user32.OpenClipboard(0)
        user32.EmptyClipboard()
        # 转换图片为BMP格式，文件的体积会比PNG大很多
        output = io.BytesIO()
        img.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]
        output.close()
        # 分配全局内存并复制数据
        hMem = kernel32.GlobalAlloc(0x0002, len(data))
        locked_mem = kernel32.GlobalLock(hMem)
        ctypes.memmove(locked_mem, data, len(data))
        kernel32.GlobalUnlock(hMem)
        # 设置剪贴板数据
        user32.SetClipboardData(8, hMem)
        user32.CloseClipboard()
    # macOS平台复制图片
    def _copy_image_macos(self, image_bytes):
        """macOS平台使用命令行工具复制图片"""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name
        
        try:
            subprocess.run([
                "osascript", "-e",
                f'set the clipboard to (read (POSIX file "{tmp_path}") as PNG picture)'
            ], check=True, capture_output=True)
        finally:
            os.unlink(tmp_path)
    # Linux平台复制图片
    def _copy_image_linux(self, image_bytes):
        """Linux平台使用命令行工具复制图片"""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name
        
        try:
            if os.environ.get("WAYLAND_DISPLAY"):
                subprocess.run(["wl-copy", "-t", "image/png", tmp_path], check=True)
            else:
                subprocess.run(["xclip", "-selection", "clipboard", "-t", "image/png", tmp_path], check=True)
        finally:
            os.unlink(tmp_path)
    # 保存原始JSON响应
    def save_raw_response(self):
        """保存原始JSON响应到文件"""
        if not self.last_raw_response:
            messagebox.showwarning("警告", "没有可保存的响应数据")
            return
        
        filepath = filedialog.asksaveasfilename(
            title="保存响应数据",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
            initialfile=f"response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        if not filepath:
            return
        # 保存JSON文件
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self.last_raw_response, f, indent=2, ensure_ascii=False)
            
            self.status_var.set(f" 响应数据已保存")
        except Exception as e:
            messagebox.showerror("保存错误", f"无法保存响应数据:\n{str(e)}")
    # 显示完整数据
    def show_full_data(self):
        """在新窗口显示完整数据"""
        if not self.last_raw_response:
            messagebox.showwarning("警告", "没有可显示的数据")
            return
        
        # 创建新窗口
        detail_window = tk.Toplevel(self.root)
        detail_window.title("完整响应数据")
        detail_window.geometry("800x600")
        # 文本区域（带滚动条）
        text_widget = tk.Text(detail_window, wrap=tk.NONE, font=("Consolas", 9))
        text_widget.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        # 垂直滚动条
        scroll_y = ttk.Scrollbar(detail_window, orient=tk.VERTICAL, command=text_widget.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        # 横向滚动条
        scroll_x = ttk.Scrollbar(detail_window, orient=tk.HORIZONTAL, command=text_widget.xview)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        # 绑定滚动条
        text_widget.config(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        
        # 显示完整数据
        text_widget.insert("1.0", json.dumps(self.last_raw_response, indent=2, ensure_ascii=False))
        text_widget.config(state=tk.DISABLED)
    # 保存日志到文件
    def _save_log(self, data, log_type):
        """保存日志到文件"""
        try:
            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)
            # 生成日志文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(log_dir, f"gemini_{timestamp}_{log_type}.log")
            
            # 修复：隐藏 API Key，不保存明文
            hidden_api_key = "SK_HIDDEN_API_KEY"
            # 构建日志数据
            log_data = {
                "timestamp": timestamp,
                "model": self.model_var.get(),
                "prompt": self.prompt_text.get("1.0", tk.END).strip(),
                "aspect_ratio": self.aspect_ratio.get(),
                "resolution": self.resolution.get(),
                "network_timeout": self.network_timeout.get(),
                "reference_images": len(self.reference_images),
                "api_key": hidden_api_key,  # 修复：使用占位符代替真实密钥
                "data": data
            }
            # 保存日志文件
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False, default=str)
        # 捕获异常但不影响主流程
        except Exception as e:
            print(f"日志记录失败: {e}")
    # 验证超时输入
    def _validate_timeout(self, value):
        """验证超时输入：只允许自然数"""
        if value == "" or value == "0":
            return True
        return value.isdigit() and int(value) >= 0
    # 日志开关切换处理
    def on_log_toggle(self):
        """日志开关切换时的处理"""
        if self.log_to_file.get():
            self.status_var.set("✓ 已启用日志记录（敏感信息已脱敏）")
        else:
            self.status_var.set("✗ 已禁用日志记录")
    # 模型切换处理
    def on_model_change(self, event=None):
        """模型切换时更新分辨率选项"""
        model = self.model_var.get().strip()
        config = self.MODEL_CONFIGS.get(model, {})
        # 根据模型配置更新分辨率选项
        # Gemini 2.5 仅支持 1K，Gemini 3 Pro 支持多分辨率
        if config.get("stable"):  # gemini-2.5-flash-image
            self.resolution_combo.config(values=["1K"], state="readonly")
            self.resolution.set("1K")
        # Nano Banana 2 支持多分辨率
        else:  # gemini-3-pro-image-preview
            self.resolution_combo.config(values=["1K", "2K", "4K"], state="readonly")
            self.resolution.set("4K")  # 默认4K
    # 缩放比例变化处理
    def on_zoom_change(self, event=None):
        self._apply_zoom()
    # 保存UI状态
    def _save_ui_state(self):
        """保存所有UI状态以便缩放后恢复"""
        state = {
            'prompt': self.prompt_text.get("1.0", tk.END).strip(),
            'api_key': self.api_key.get(),
            'model': self.model_var.get(),
            'aspect_ratio': self.aspect_ratio.get(),
            'resolution': self.resolution.get(),
            'log_to_file': self.log_to_file.get(),
            'network_timeout': self.network_timeout.get(),
            'reference_images': self.reference_images.copy(),
            'current_image_data': self.current_image_data,
            'last_raw_response': self.last_raw_response,
            'response_text': self.response_text.get("1.0", tk.END).strip()
        }
        self._ui_state_cache = state
    # 恢复UI状态
    def _restore_ui_state(self):
        """恢复所有UI状态"""
        state = self._ui_state_cache
        if not state:
            return
        # 恢复各项设置
        self.api_key.set(state['api_key'])
        self.model_var.set(state['model'])
        self.aspect_ratio.set(state['aspect_ratio'])
        self.resolution.set(state['resolution'])
        self.log_to_file.set(state['log_to_file'])
        self.network_timeout.set(state['network_timeout'])

        self.prompt_text.delete("1.0", tk.END)
        self.prompt_text.insert("1.0", state['prompt'])
        
        self.response_text.delete("1.0", tk.END)
        self.response_text.insert("1.0", state['response_text'])
        
        self.reference_images = state['reference_images']
        self.update_reference_preview()
        
        self.current_image_data = state['current_image_data']
        if self.current_image_data:
            self._show_image()
            self.save_btn.config(state=tk.NORMAL)
        else:
            self.save_btn.config(state=tk.DISABLED)
        
        self.last_raw_response = state['last_raw_response']
# ==================== 窗口缩放与行为设置 ====================
    def _apply_zoom(self):
        """应用缩放设置到所有UI元素，并保存/恢复UI状态"""
        # 先保存当前UI状态
        self._save_ui_state()
        # 获取缩放比例
        zoom_str = self.zoom_var.get().rstrip('%')
        try:
            scale = int(zoom_str) / 100.0
        except:
            scale = 1.0
        
        # 更新主窗口大小
        try:
            prev_state = self.root.state()
        except Exception:
            prev_state = None
        # 先恢复正常状态以调整大小
        try:
            if prev_state == 'zoomed':
                self.root.state('normal')
        except Exception:
            pass
        # 更新窗口大小
        base_width, base_height = 1200, 850 # 基础尺寸
        new_width = int(base_width * scale)
        new_height = int(base_height * scale)
        try:
            self.root.geometry(f"{new_width}x{new_height}") # 设置新尺寸
        except Exception:
            pass
        # 最后恢复最大化状态
        try:
            if prev_state == 'zoomed': 
                self.root.state('zoomed')
        except Exception:
            pass

        # 调整左侧面板宽度
        min_left_panel_width = int(550 * scale)
        self.root.after(50, lambda: self.main_paned.sash_place(0, min_left_panel_width, 0))
        
        # 更新全局字体大小
        try:
            default_font = font.nametofont("TkDefaultFont")
            base_font_size = 10
            new_font_size = int(base_font_size * scale)
            if new_font_size < 8:
                new_font_size = 8
            default_font.configure(size=new_font_size)

            style = ttk.Style()
            family = default_font.cget("family")
            style.configure(".", font=(family, new_font_size))

            try:
                small_size = max(new_font_size - 1, 8)
                self.char_label.config(font=(family, small_size))
            except Exception:
                pass

            try:
                self.prompt_text.config(font=(family, new_font_size))
            except Exception:
                pass
            try:
                self.response_text.config(font=(family, new_font_size))
            except Exception:
                pass
        except Exception:
            pass
        
        # 缩放完成后恢复UI状态
        self.root.after(100, self._restore_ui_state)
    # 设置窗口行为
    def setup_window_behavior(self):
        """设置窗口行为：最大化tkinter并最小化终端"""
        # 在tk窗口显示前获取终端窗口ID（此时终端肯定是活动窗口）
        self.terminal_window_id = None
        try:
            if platform.system() == "Linux":
                result = subprocess.run(
                    ['xdotool', 'getactivewindow'], 
                    capture_output=True, text=True, check=False
                )
                if result.returncode == 0:
                    self.terminal_window_id = result.stdout.strip()
        except Exception:
            self.terminal_window_id = None
        
        # 最大化tkinter窗口
        self._maximize_tkinter_window()
        
        # 延迟最小化终端，使用之前捕获的窗口ID
        self.root.after(2000, self._minimize_terminal_window)
    # 最大化tkinter窗口
    def _maximize_tkinter_window(self):
        """根据操作系统最大化tkinter窗口"""
        system = platform.system()
        try:
            
            if system == "Windows":
                self.root.state('zoomed')
            elif system == "Darwin":
                self.root.attributes('-fullscreen', True)
            else:
                self.root.state('zoomed')
        except Exception:
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            self.root.geometry(f"{screen_width}x{screen_height}+0+0")

    # 最小化终端窗口
    def _minimize_terminal_window(self):
        """根据操作系统最小化终端窗口"""
        try:
            system = platform.system()
            
            if system == "Windows":
                hwnd = ctypes.windll.kernel32.GetConsoleWindow()
                if hwnd:
                    ctypes.windll.user32.ShowWindow(hwnd, 6)
            
            elif system == "Darwin":
                subprocess.run([
                    'osascript', '-e', 
                    'tell application "Terminal" to set miniaturized of window 1 to true'
                ], stderr=subprocess.DEVNULL, check=False)
            
            else:
                try:
                    if self.terminal_window_id:
                        subprocess.run(
                            ['xdotool', 'windowminimize', self.terminal_window_id],
                            stderr=subprocess.DEVNULL, check=False
                        )
                except FileNotFoundError:
                    pass
                except Exception:
                    pass
                    
        except Exception:
            pass # 没关系，反正最小化失败也不影响使用，就是终端还在那儿而已
    

    def _insert_data_warning(self):
        """**改进：防止用户编辑只读文本框**"""
        return "break"  # 阻止事件继续传递，防止文本框获得焦点
# ==================== 主程序入口 ====================
def main():
    root = tk.Tk()
    root.minsize(1000, 800)
    app = GeminiImageGenerator(root)
    root.mainloop()
# ==================== 运行主程序 ====================
if __name__ == "__main__":
    main()
# ================== 代码结束 ====================