# ====================================================
#         警告：不要直接在顶部导入"第三方"依赖！
# 请按照说明，使用正确的方法添加新的依赖，确保防呆机制生效
# ====================================================
import sys 
import platform
import subprocess 
import time 
import os 

# 前排提示：搜索TEMPLATE_TOML，可以快速定位到内置的配置文件模板，方便一键配置。

# 提前检测 Tkinter 是否可用，不然程序启动后直接崩溃会非常糟糕，尤其是对于不熟悉Python环境的小白用户
try:
    import tkinter
except ImportError:
    # 尝试修改终端/控制台标题，如果改不了其实也无伤大雅，主要是为了更显眼
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleTitleW("严重错误：缺少核心组件 Tkinter ！")
    except (ImportError, AttributeError):
        sys.stdout.write("\033]0;严重错误：缺少核心组件 Tkinter ！\007")
        sys.stdout.flush()
    
    # 打印错误信息并退出
    print("\n")
    print("—— 严重错误：缺少核心组件 Tkinter ！")
    print("\n")
    print(" Tkinter 是 Python 的标准 GUI 库，但您的设备缺失 Tkinter ，无法启动该脚本。")
    print("\n")
    print("请上网搜索您的系统如何安装 Tkinter ，然后重新运行脚本。")
    print("\n")
    input("按任意键退出脚本……")
    sys.exit(1)
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

# 通用可选依赖（缺失时仅在必须依赖缺失时尝试安装）
OPTIONAL_DEPENDENCIES = [
    ("tkinterdnd2", "tkinterdnd2"),
    ("tomli", "tomli"),
]

# Windows平台可选依赖
WINDOWS_OPTIONAL_DEPENDENCIES = [
    ("pywin32", "win32clipboard"),
    ("comtypes", "comtypes"),
]

# macOS平台可选依赖（预留）
MACOS_OPTIONAL_DEPENDENCIES = [
    # 例如: ("pyobjc", "Foundation")
]

# Linux平台可选依赖（预留）
LINUX_OPTIONAL_DEPENDENCIES = [
    # 例如: ("xclip", "xclip")  注意：xclip是命令行工具，非pip包，此处仅示例
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

# 全局变量：记录缺失的可选依赖（供 UI 显示）
_missing_optional_deps = []

# 主检查与安装函数
def _check_and_handle_dependencies():
    """检查依赖，如果缺失则提示用户并尝试安装"""
    global _missing_optional_deps
    missing_deps = []
    
    # 检查必要依赖
    for pip_name, import_name in REQUIRED_DEPENDENCIES:
        try:
            __import__(import_name)
        except ImportError:
            missing_deps.append((pip_name, import_name))
    
    # 如果有必要依赖缺失，则额外检查所有可选依赖（通用+当前平台）
    if missing_deps:
        # 1. 通用可选依赖
        for pip_name, import_name in OPTIONAL_DEPENDENCIES:
            try:
                __import__(import_name)
            except ImportError:
                missing_deps.append((pip_name, import_name))
        
        # 2. 当前平台特定的可选依赖
        current_platform = platform.system()
        if current_platform == "Windows":
            optional_list = WINDOWS_OPTIONAL_DEPENDENCIES
        elif current_platform == "Darwin":
            optional_list = MACOS_OPTIONAL_DEPENDENCIES
        elif current_platform == "Linux":
            optional_list = LINUX_OPTIONAL_DEPENDENCIES
        else:
            optional_list = []
        
        for pip_name, import_name in optional_list:
            try:
                __import__(import_name)
            except ImportError:
                missing_deps.append((pip_name, import_name))
    
    # 如果没有缺失的必要依赖，则记录缺失的可选依赖（供 UI 显示）并返回
    required_pip_names = [req[0] for req in REQUIRED_DEPENDENCIES]
    if not any(pip_name in required_pip_names for pip_name, _ in missing_deps):
        # 收集缺失的可选依赖（通用+平台，但不包括必须依赖）
        for pip_name, import_name in missing_deps:
            if pip_name not in required_pip_names:
                _missing_optional_deps.append(pip_name)
        return  # 所有必要依赖都已安装
    
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
        if user_input.lower() == 'n':
            print("取消自动安装，程序将在5秒后退出...")
            time.sleep(5)
            sys.exit(1)
        print("\n正在尝试自动安装...")
        for pip_name, import_name in missing_deps:
            cmd = install_commands[missing_deps.index((pip_name, import_name))]
            print(f"安装 {pip_name}...")
            try:
                subprocess.run(cmd.split(), capture_output=True, text=True, check=True)
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

# ------ TOML 库导入（优先内置 tomllib，回退 tomli）------
TOML_AVAILABLE = False
try:
    import tomllib  # Python 3.11+ 内置
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None
if tomllib is not None:
    TOML_AVAILABLE = True

# 尝试导入可选依赖 tkinterdnd2，若失败则设置标志位
TKINTERDND2_AVAILABLE = False
try:
    import tkinterdnd2
    TKINTERDND2_AVAILABLE = True
except ImportError:
    pass

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
import random

# Windows 任务栏进度条支持
if platform.system() == "Windows":
    try:
        import comtypes
        from comtypes import GUID, COMMETHOD, HRESULT
        from comtypes.client import CreateObject
        COMTYPES_AVAILABLE = True
    except ImportError:
        COMTYPES_AVAILABLE = False
else:
    COMTYPES_AVAILABLE = False

# 所有模块加载完成
print("核心模块加载完成")
print("正在初始化图形界面...\n")

class GeminiImageGenerator:
    # ==================== 集中定义的常量 ====================
    # 最大参考图片数量
    MAX_REF_IMAGES = 14

    # 最大提示词长度
    MAX_PROMPT_CHARS = 2000

    # 单张图片大小警告阈值 (MB)，超过此值将提示用户但仍允许使用，可按需修改
    MAX_IMAGE_SIZE_MB = 10
    # 根据作者实测，利用回归函数（y=ax+b）计算左侧面板的宽度
    LEFT_WIDTH_SLOPE = 2.645      # 每增加 1% 缩放，面板宽度增加的像素
    LEFT_WIDTH_INTERCEPT = 220   # 缩放 0% 时的基准宽度（理论值，用于平移）

    # ==================== TOML 配置文件常量 ====================
    # 各字段合法枚举值
    TOML_VALID_VALUES = {
        "import_mode": ["clear_and_overwrite", "overwrite_existing"],
        "model": ["gemini-2.5-flash-image", "gemini-3-pro-image-preview",
                  "gemini-3.1-flash-image-preview", "gpt-image-2-vip"],
        "aspect_ratio": ["16:9", "5:4", "4:3", "3:2", "1:1", "21:9", "2:3", "3:4", "4:5", "9:16"],
        "resolution": ["1K", "2K", "4K"],
        "zoom": ["75%", "100%", "125%", "150%", "175%", "200%", "250%", "300%", "500%"],
        "valid_image_exts": [".jpg", ".jpeg", ".png", ".webp"],
    }
    # 默认值（与 __init__ 中初始化一致）
    TOML_DEFAULTS = {
        "api_key": "",
        "model": "gemini-3.1-flash-image-preview",
        "aspect_ratio": "1:1",
        "resolution": "4K",
        "network_timeout": "1200",
        "confirm_before_generate": True,
        "log_to_file": False,
        "prompt": "",
        "zoom": "100%",
        "prompt_lines": 5,
    }

    # 模型配置
    MODEL_CONFIGS = {
        "gemini-2.5-flash-image": {
            "resolutions": ["1K"],
            "stable": True,
            "backend": "nanobanana",
            "max_ref_images": 14
        },
        "gemini-3-pro-image-preview": {
            "resolutions": ["1K", "2K", "4K"],
            "stable": False,
            "backend": "nanobanana",
            "max_ref_images": 14
        },
        "gemini-3.1-flash-image-preview": {
            "resolutions": ["1K", "2K", "4K"],
            "stable": False,
            "backend": "nanobanana",
            "max_ref_images": 14
        },
        "gpt-image-2-vip": {
            "resolutions": ["1K", "2K", "4K"],
            "stable": False,
            "backend": "gpt_image_vip",
            "max_ref_images": 10
        }
    }

    # GPT Image 2 VIP 纵横比到像素尺寸的映射
    VIP_SIZE_MAP = {
        "1:1":   {"1K": "1280x1280",  "2K": "2048x2048",  "4K": "2880x2880"},
        "2:3":   {"1K": "848x1280",   "2K": "1360x2048",  "4K": "2336x3520"},
        "3:2":   {"1K": "1280x848",   "2K": "2048x1360",  "4K": "3520x2336"},
        "3:4":   {"1K": "960x1280",   "2K": "1536x2048",  "4K": "2480x3312"},
        "4:3":   {"1K": "1280x960",   "2K": "2048x1536",  "4K": "3312x2480"},
        "4:5":   {"1K": "1024x1280",  "2K": "1632x2048",  "4K": "2560x3216"},
        "5:4":   {"1K": "1280x1024",  "2K": "2048x1632",  "4K": "3216x2560"},
        "9:16":  {"1K": "720x1280",   "2K": "1152x2048",  "4K": "2160x3840"},
        "16:9":  {"1K": "1280x720",   "2K": "2048x1152",  "4K": "3840x2160"},
        "21:9":  {"1K": "1280x544",   "2K": "2048x864",   "4K": "3840x1632"}
    }
    
    # 嵌入的图片提取脚本代码
    EXPORT_SCRIPT_CODE = '''import tkinter as tk,tkinter.filedialog as fd,tkinter.messagebox as mb,json,base64
from PIL import Image,ImageTk
import io
class V:
 def __init__(self,r):
  self.r=r;r.title("日志图片查看器");r.geometry("770x364")
  self.b=None;self.d=None;self.t=None;self.c=None;self.n=None;self.s=0;self.j=None
  f=tk.Frame(r,padx=10,pady=3);f.pack(fill=tk.X)
  tk.Button(f,text="打开Log文件",command=self.l).pack(side=tk.LEFT)
  self.e=tk.Button(f,text="保存图片",command=self.v,state=tk.DISABLED);self.e.pack(side=tk.RIGHT,padx=5)
  self.h=tk.Button(f,text="旋转图片",command=self.o,state=tk.DISABLED);self.h.pack(side=tk.RIGHT,padx=5)
  self.i=tk.Label(f,text="等待加载log文件…",fg="blue");self.i.pack(side=tk.RIGHT,padx=10)
  self.g=tk.Label(f,text="未选择文件",fg="gray");self.g.pack(side=tk.LEFT,padx=10)
  m=tk.Frame(r,bg="lightgray");m.pack(fill=tk.BOTH,expand=True,padx=3,pady=0)
  self.a=tk.Canvas(m,bg="white");self.a.pack(fill=tk.BOTH,expand=True);self.a.bind("<Configure>",self.w);self.p=None
 def w(self,event):
  if self.j:self.r.after_cancel(self.j)
  if self.d and event.width>100 and event.height>100:self.j=self.r.after(50,lambda:self.u(event.width,event.height))
 def l(self):
  p=fd.askopenfilename(title="选择日志文件",filetypes=[("success日志","*_success.log"),("所有文件","*.*")])
  if not p:return
  self.i.config(text="正在加载文件...",fg="orange");self.r.update()
  try:
   with open(p,'r',encoding='utf-8')as f:d=json.load(f);b,ext=self.x(d)
   if b:
    self.b=b;self.d=Image.open(io.BytesIO(b));self.s=0;self.t=None;self.c=None
    log_name=p.split('/')[-1].rsplit('.',1)[0]if'.'in p.split('/')[-1]else p.split('/')[-1]
    self.n=f"{log_name}{ext}"
    self.u(self.a.winfo_width(),self.a.winfo_height())
    self.g.config(text=f"已加载: {p.split('/')[-1]}");self.e.config(state=tk.NORMAL);self.h.config(state=tk.NORMAL);self.i.config(fg="blue")
   else:mb.showwarning("警告","未找到有效的图片数据");self.i.config(text="未找到图片数据",fg="red")
  except Exception as e:mb.showerror("错误",f"加载失败: {str(e)}");self.i.config(text="加载失败",fg="red")
 def x(self,d):
  inner = d.get("data", d)
  for c in inner.get("candidates",[]):
   for p in c.get("content",{}).get("parts",[]):
    i=p.get("inlineData",{})
    if i.get("data"):
     mime=i.get("mimeType","image/jpeg")
     ext=".jpg" if "jpeg" in mime or "jpg" in mime else ".png"
     return base64.b64decode(i["data"]), ext
  data_arr=inner.get("data",[])
  if data_arr and isinstance(data_arr,list) and len(data_arr)>0:
   item=data_arr[0]
   b64=item.get("b64_json") or item.get("b64")
   if b64:
    if b64.startswith("data:"):
     b64=b64.split(",",1)[1]
    b64+="="*((4-len(b64)%4)%4)
    return base64.b64decode(b64), ".png"
  return None, None
 def u(self,w,h):
  if not self.d:return
  if self.t is None:
   self.t=self.d.copy()if self.s==0 else self.d.rotate(-self.s,expand=True)
  r=self.t
  if r.width>w or r.height>h:
   s=min(w/r.width,h/r.height);k=int(r.width*s),int(r.height*s)
   if self.c is None or self.c.size!=k:self.c=r.resize(k,Image.Resampling.LANCZOS)
   m=self.c
  else:m=r
  self.i.config(text=f"图片尺寸: {r.width} x {r.height} | 旋转: {self.s}°")
  self.k=ImageTk.PhotoImage(m)
  if self.p:self.a.delete(self.p)
  self.a.delete("all");self.p=self.a.create_image(w//2,h//2,anchor=tk.CENTER,image=self.k)
 def o(self):self.s=(self.s+90)%360;self.t=None;self.c=None;self.u(self.a.winfo_width(),self.a.winfo_height())
 def v(self):
  if not self.b:return
  ext=self.n.split('.')[-1] if self.n and '.' in self.n else 'png'
  p=fd.asksaveasfilename(defaultextension=f".{ext}",filetypes=[("图片文件",f"*.{ext}"),("所有文件","*.*")],initialfile=self.n or f"export_image.{ext}")
  if not p:return
  try:open(p,'wb').write(self.b);mb.showinfo("成功",f"图片已保存: {p}")
  except Exception as e:mb.showerror("错误",f"保存失败: {str(e)}")
if __name__=="__main__":r=tk.Tk();V(r);r.mainloop()
'''

    # ==================== 配置文件模板（供用户复制） ====================
    # 将以下内容保存为 .toml 文件，拖入程序窗口即可导入配置；
    # 命名为 default.toml 放在程序同目录下，可实现自动导入。
    # 后续搜索TEMPLATE_TOML，可以快速定位到这里，方便复制TOML模板。
    # 不要直接修改下面的模板内容，改了也没有用。
    # 正确的做法是复制下面的内容，保存为 .toml 文件，然后拖入程序窗口，
    # 或者命名为 default.toml 放在程序同目录下实现自动导入。

    TEMPLATE_TOML = r""" # 从下面开始是模板内容，注意不要复制这行字走了，这是脚本代码的一部分，不是模板的一部分。



# 老张API-NanoBanana调用器 配置文件
# 将本文件拖入程序窗口，即可自动填写配置。一次只可以拖入一个配置文件。
# 名字改成default.toml并放在程序同目录下，可以实现自动导入配置。

#####################【导入模式 - 必填】#####################

# 决定现在这份toml文件怎么导入到脚本里面。

## clear_and_overwrite：
### 清空全部内容，然后覆盖掉配置文件里有的东西。
### 没写的配置会被还原成默认值，写了但是留空的配置会被清空。
### 如果有无法解析的值（例如写错模型名字），脚本会弹窗报错，并拒绝导入全部内容。

## overwrite_existing(推荐)：
### 覆盖掉配置文件里有的东西。
### 没写的配置不会去动，写了但是留空的配置会被清空。
### 如果有无法解析的值（例如写错模型名字），脚本会弹窗报错，然后询问用户是否继续导入剩下的配置项。

import_mode = "overwrite_existing"

#########################【API配置】#########################
[api]
# 【API密钥】
# 调用API接口的密钥。
# 示例：key = "sk-123456789abcdefghijklmno1234567890abcdef12345678"

key = ""

# ------------------------------------------------------------

# 【模型选择】
# 可选值:
# "gemini-2.5-flash-image", "gemini-3-pro-image-preview",
# "gemini-3.1-flash-image-preview", "gpt-image-2-vip"

model = "gemini-3.1-flash-image-preview"

#########################【生成参数】#########################

[generation]
# 【纵横比】
# 可选值:
# 竖版——"16:9", "5:4", "4:3", "3:2",
# 特殊——"1:1", "21:9",
# 横版——"2:3", "3:4", "4:5", "9:16"

aspect_ratio = "4:3"

# ------------------------------------------------------------

# 【分辨率】
# 可选值: "1K", "2K", "4K"
# 注意: gemini-2.5-flash-image 仅支持 "1K"

resolution = "2K"

# ------------------------------------------------------------

# 【网络超时时间】
# 单位：秒，0表示无限制，默认1200秒

network_timeout = 1800

# ------------------------------------------------------------

# 【生成前确认】
# 生成前是否弹出参数确认弹窗，防止未检查导致误生成
# true = 开启，false = 关闭

confirm_before_generate = false

# ------------------------------------------------------------

# 【自动保存生成日志】
# true = 开启，false = 关闭

log_to_file = false

# ------------------------------------------------------------


######################### 【提示词】 #########################

# 提示词支持多行，只要在前后使用三个单引号包裹，就可以保留换行符。
# 如果忘记加后半段的三个单引号，那么就算作无法解析，脚本会拒绝导入。
# 三个单引号所在的行也是可以写东西的，但是不建议写，因为担心写的时候不小心写到外面，导致无法解析。
# 示例（实际写的时候不用加"#"号）：
# prompt = '''
# 生成一只猫，要求：
# 1. 橘色上肢，紫色下肢；
# 2. 正在玩CSGO。
# 3. 电脑桌面上有一盆猫粮。'''

prompt = '''
生成一只猫，要求：
1. 橘色上肢，紫色下肢；
2. 正在玩CSGO。
3. 电脑桌面上有一盆猫粮。
'''

######################## 【界面设置】 ########################

[ui]
# 界面缩放比例
# 可选值: "75%", "100%", "125%", "150%", "175%", "200%", "250%", "300%", "500%"。
zoom = "125%"

# 提示词输入框行数（2~98）
prompt_lines = 4

######################## 【参考图片】 ########################
# 程序启动时自动加载的参考图片路径列表。如果留空，会导致程序报错，建议不用时加上"#"注释掉，或者后续再添加。
# 支持导入多张图片，程序会自动把它们放在一起作为参考图输入给模型。
# 使用 [[reference_images]] 添加多张，每张一个 path 字段，详见示例。
# 支持绝对路径（完整的图片路径）和相对路径（相对于脚本所在目录），但是新手不建议用相对路径。
# 推荐使用正斜杠（/）作为路径分隔符；
# 如果使用反斜杠（\），要使用两次（\\）来转义toml语法，确保不会识别错误。
# 图片格式仅限: jpg, jpeg, png, webp。
# 文件必须存在且为有效图片，否则视为无法解析。

# 示例1：绝对路径导入多张图片
# [[reference_images]]
# path = "D:/图片生成脚本/素材图片/公司图标.png"
# [[reference_images]]
# path = "D:\\图片生成脚本\\素材图片\\背景图.jpg"
# [[reference_images]]
# path = "D:/图片生成脚本/素材图片/人物照片.webp"
#
# 示例2：相对路径导入多张图片
# [[reference_images]]
# path = ".\\素材图片\\公司图标.png"
# [[reference_images]]
# path = "./素材图片/背景图.jpg"
# [[reference_images]]
# path = ".\\素材图片\\人物照片.webp"

[[reference_images]]
path = ""



""" # 配置模板到此结束，注意这三个引号是脚本代码的一部分（不是模板的一部分），不要复制走了




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
        
        # ————配置变量
        # API密钥，在【value=""】的引号里面填写自己的密钥，就可以启动后自动输入密钥了
        # 示例：
        # self.api_key = tk.StringVar(value="sk-1234567890987654321")
        self.api_key = tk.StringVar(value="")
        # 默认模型选择
        self.model_var = tk.StringVar(value="gemini-3.1-flash-image-preview")
        # 当前模式下的最大参考图片数（由模型决定）
        self.current_max_ref_images = 14
        # 默认生成参数
        self.aspect_ratio = tk.StringVar(value="1:1")
        # 默认分辨率（取决于模型设置）
        self.resolution = tk.StringVar(value="4K")
        # 默认日志记录选项
        self.log_to_file = tk.BooleanVar(value=False)
        # 默认网络超时设置
        self.network_timeout = tk.StringVar(value="1200")
        # 界面缩放
        self.zoom_var = tk.StringVar(value="100%")
        # 默认提示词行数设置
        self.line_count_var = tk.IntVar(value=5)
        # 生成前确认参数开关
        self.confirm_before_generate = tk.BooleanVar(value=True)
        
        # 新增：代理警告抑制状态（临时，不持久化）
        self.proxy_warning_suppressed = False

        # Windows 任务栏进度条
        self.taskbar_progress = None
        if platform.system() == "Windows" and COMTYPES_AVAILABLE:
            self._init_taskbar_progress()
        
        # 检测pywin32可用性（仅Windows平台）
        self.pywin32_available = False
        self._win32clipboard = None
        self._win32con = None
        if platform.system() == "Windows":
            try:
                import win32clipboard
                import win32con
                self._win32clipboard = win32clipboard
                self._win32con = win32con
                self.pywin32_available = True
            except ImportError:
                self.pywin32_available = False
        
        # ————数据存储
        # 参考图片列表，存储格式为 (文件路径, base64字符串, mime类型, 原始PIL图像)
        self.reference_images = []
        # 当前生成的图片数据（base64）
        self.current_image_data = None
        # 当前生成的图片MIME类型
        self.current_image_mime_type = None
        # 生成图片时使用的模型名（用于保存时确定文件名）
        self.current_image_model = None
        # 当前生成的图片预览（PIL ImageTk 对象）
        self.current_image_preview = None
        # 最后一次的原始响应数据
        self.last_raw_response = None
        # UI状态存储（用于缩放切换）
        self._ui_state_cache = {}
        # 线程控制
        self.generate_thread = None
        # 记录上一次通过验证的参数组合（模型, 纵横比, 分辨率）
        self.last_verified_params = None

        # 关闭拦截失败计数器（独立计数，切换弹窗类型时清零）
        self.button_fail_count = 0
        self.slider_fail_count = 0
        # 保底弹窗锁定状态（触发后永久锁定）
        self.fallback_locked = False

                # 构建UI
        self.setup_ui()
        self.setup_window_behavior()
        # 初始化关闭拦截
        self._intercept_close()
        
        # 注册拖放事件（将图片拖入窗口自动添加为参考图片）
        if TKINTERDND2_AVAILABLE:
            self.root.drop_target_register(tkinterdnd2.DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.on_drop)
        else:
            self.update_status("提示: 未安装 tkinterdnd2，拖放添加图片功能不可用")

        # 初始化完成
    def update_status(self, message):
        """更新状态栏文本"""
        if hasattr(self, 'status_text'):
            self.status_text.config(state=tk.NORMAL)
                    
            # 追加新内容（带时间戳）
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        
            # 自动滚动到底部
            self.status_text.see(tk.END)
        
            self.status_text.config(state=tk.DISABLED)
    def _init_taskbar_progress(self):
        """初始化 Windows 任务栏进度条（ITaskbarList3）"""
        if platform.system() != "Windows" or not COMTYPES_AVAILABLE:
            return

        class ITaskbarList3(comtypes.IUnknown):
            _iid_ = GUID('{ea1afb91-9e28-4b86-90e9-9e9f8a5eefaf}')
            _methods_ = [
                COMMETHOD([], HRESULT, 'HrInit'),
                COMMETHOD([], HRESULT, 'AddTab',
                          (['in'], ctypes.c_ulonglong, 'hwnd')),
                COMMETHOD([], HRESULT, 'DeleteTab',
                          (['in'], ctypes.c_ulonglong, 'hwnd')),
                COMMETHOD([], HRESULT, 'ActivateTab',
                          (['in'], ctypes.c_ulonglong, 'hwnd')),
                COMMETHOD([], HRESULT, 'SetActiveAlt',
                          (['in'], ctypes.c_ulonglong, 'hwnd')),
                COMMETHOD([], HRESULT, 'MarkFullscreenWindow',
                          (['in'], ctypes.c_ulonglong, 'hwnd'),
                          (['in'], ctypes.c_int, 'fFullscreen')),
                COMMETHOD([], HRESULT, 'SetProgressValue',
                          (['in'], ctypes.c_ulonglong, 'hwnd'),
                          (['in'], ctypes.c_ulonglong, 'ullCompleted'),
                          (['in'], ctypes.c_ulonglong, 'ullTotal')),
                COMMETHOD([], HRESULT, 'SetProgressState',
                          (['in'], ctypes.c_ulonglong, 'hwnd'),
                          (['in'], ctypes.c_int, 'tbpFlags')),
                COMMETHOD([], HRESULT, 'RegisterTab',
                          (['in'], ctypes.c_ulonglong, 'hwndTab'),
                          (['in'], ctypes.c_ulonglong, 'hwndMDI')),
                COMMETHOD([], HRESULT, 'UnregisterTab',
                          (['in'], ctypes.c_ulonglong, 'hwndTab')),
                COMMETHOD([], HRESULT, 'SetTabOrder',
                          (['in'], ctypes.c_ulonglong, 'hwndTab'),
                          (['in'], ctypes.c_ulonglong, 'hwndInsertBefore')),
                COMMETHOD([], HRESULT, 'SetTabActive',
                          (['in'], ctypes.c_ulonglong, 'hwndTab'),
                          (['in'], ctypes.c_ulonglong, 'hwndMDI'),
                          (['in'], ctypes.c_ulong, 'dwReserved')),
                COMMETHOD([], HRESULT, 'ThumbBarAddButtons',
                          (['in'], ctypes.c_ulonglong, 'hwnd'),
                          (['in'], ctypes.c_uint, 'cButtons'),
                          (['in'], ctypes.POINTER(ctypes.c_void_p), 'pButton')),
                COMMETHOD([], HRESULT, 'ThumbBarUpdateButtons',
                          (['in'], ctypes.c_ulonglong, 'hwnd'),
                          (['in'], ctypes.c_uint, 'cButtons'),
                          (['in'], ctypes.POINTER(ctypes.c_void_p), 'pButton')),
                COMMETHOD([], HRESULT, 'ThumbBarSetImageList',
                          (['in'], ctypes.c_ulonglong, 'hwnd'),
                          (['in'], ctypes.c_void_p, 'himl')),
                COMMETHOD([], HRESULT, 'SetOverlayIcon',
                          (['in'], ctypes.c_ulonglong, 'hwnd'),
                          (['in'], ctypes.c_void_p, 'hIcon'),
                          (['in'], ctypes.c_wchar_p, 'pszDescription')),
                COMMETHOD([], HRESULT, 'SetThumbnailTooltip',
                          (['in'], ctypes.c_ulonglong, 'hwnd'),
                          (['in'], ctypes.c_wchar_p, 'pszTip')),
                COMMETHOD([], HRESULT, 'SetThumbnailClip',
                          (['in'], ctypes.c_ulonglong, 'hwnd'),
                          (['in'], ctypes.c_void_p, 'prcClip')),
            ]

        # 进度条状态常量（Windows SDK 定义）
        TBPF_NOPROGRESS = 0x0
        TBPF_INDETERMINATE = 0x1
        TBPF_NORMAL = 0x2
        TBPF_ERROR = 0x4
        TBPF_PAUSED = 0x8

        class TaskbarProgressHelper:
            def __init__(self, root):
                self.root = root
                self._hwnd = None
                self._taskbar = None
                self._init_taskbar()

            def _init_taskbar(self):
                try:
                    self._taskbar = CreateObject(
                        '{56FDF344-FD6D-11d0-958A-006097C9A090}',
                        interface=ITaskbarList3
                    )
                    self._taskbar.HrInit()
                except Exception:
                    self._taskbar = None

            def _get_hwnd(self):
                if self._hwnd is None:
                    frame = self.root.wm_frame()
                    if frame:
                        self._hwnd = int(frame, 16)
                return self._hwnd

            def set_state(self, state):
                if not self._taskbar:
                    return
                hwnd = self._get_hwnd()
                if hwnd:
                    try:
                        self._taskbar.SetProgressState(hwnd, state)
                    except Exception:
                        pass

            def set_value(self, completed, total):
                if not self._taskbar:
                    return
                hwnd = self._get_hwnd()
                if hwnd:
                    try:
                        self._taskbar.SetProgressValue(hwnd, completed, total)
                    except Exception:
                        pass

            def clear(self):
                self.set_state(TBPF_NOPROGRESS)

            def set_progress(self, percent, state=TBPF_NORMAL):
                self.set_state(state)
                if state != TBPF_INDETERMINATE:
                    self.set_value(int(percent), 100)

        self.taskbar_progress = TaskbarProgressHelper(self.root)

    def _clear_taskbar_on_focus(self, event=None):
        """窗口获得焦点时清除任务栏进度条"""
        if not self.taskbar_progress:
            return
        # 只有在生成按钮恢复可用状态（即生成已结束）时才清除
        # 避免在生成过程中切换窗口导致不确定动画被意外中断
        if str(self.generate_btn.cget("state")) == "disabled":
            return
        self.taskbar_progress.clear()

    def _clear_taskbar_before_error(self):
        """在弹出错误弹窗前清除任务栏进度条并刷新UI"""
        if self.taskbar_progress:
            self.taskbar_progress.clear()
        self.root.update_idletasks()

    # ==================== 界面构建函数 ====================
    def setup_ui(self):
        """构建左右分区的用户界面"""
        # 主分区
        self.main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=8, bg="#ffd2dc")
        self.main_paned.pack(fill=tk.BOTH, expand=True)
        # 左侧面板
        left_panel = ttk.Frame(self.main_paned)
        self.main_paned.add(left_panel) 

        # 右侧面板
        right_panel = ttk.Frame(self.main_paned)
        self.main_paned.add(right_panel, width=500)

        # ===== 左侧面板内容 =====
        # 一个无框容器，单独放在最顶上。不要自己加框，免得导致界面缩放的控件因为奇葩屏幕而被遮挡/溢出
        zoom_frame = ttk.Frame(left_panel)
        zoom_frame.pack(fill=tk.BOTH, padx=2, pady=(2,2))

        # 界面缩放选项（左侧）
        ttk.Label(zoom_frame, text="界面缩放:").pack(side=tk.LEFT, padx=(0,4), pady=(0,0))
        zoom_combo = ttk.Combobox(zoom_frame, textvariable=self.zoom_var, 
                                  values=["75%", "100%", "125%", "150%", "175%", "200%", "250%", "300%", "500%"],
                                  state="readonly", width=5)
        zoom_combo.bind("<<ComboboxSelected>>", self.on_zoom_change)
        zoom_combo.pack(side=tk.LEFT)

        # 日志记录选项（右侧）
        log_check = ttk.Checkbutton(zoom_frame, text="保存日志到文件", variable=self.log_to_file,
                                   command=self.on_log_toggle)
        log_check.pack(side=tk.RIGHT, padx=(5, 5))

        # 网络超时设置（居中，特殊处理，或许可以再优化一下）
            # 0. 放一个空的容器，置于zoom_frame的中上
        ttk.Frame(zoom_frame, height=0).pack(side=tk.TOP, fill=tk.Y, expand=True)
            # 1. 在zoom_frame里面新建timeout_frame，并置于中上
        timeout_frame = ttk.Frame(zoom_frame)
        timeout_frame.pack(side=tk.TOP, fill=tk.Y)
            # 2. 把文本和输入框放在timeout_frame里面，一个左一个右
        ttk.Label(timeout_frame, text="网络超时(秒):").pack(side=tk.LEFT)
        timeout_entry = ttk.Entry(timeout_frame, textvariable=self.network_timeout, width=8, validate='key',
                                 validatecommand=(self.root.register(self._validate_timeout), '%P'))
        timeout_entry.pack(side=tk.RIGHT)
            # 3. 放一个空的容器，置于zoom_frame的中下
        ttk.Frame(zoom_frame, height=0).pack(side=tk.BOTTOM, fill=tk.Y, expand=True)

        # API配置区域
        api_frame = ttk.LabelFrame(left_panel, text="API配置", padding=10)
        api_frame.pack(fill=tk.X, pady=5, padx=5)

        # 先计算模型下拉框的宽度，让API密钥输入框与之对齐
        model_values = list(self.MODEL_CONFIGS.keys())
        combo_width = max(len(v) for v in model_values) + 1 if model_values else 10
        
        # API密钥输入（内嵌按钮样式）
        ttk.Label(api_frame, text="API密钥:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        # 创建带边框的容器Frame，伪装成输入框外观
        key_container = tk.Frame(api_frame, bd=1, relief=tk.SUNKEN, bg="white")
        key_container.grid(row=0, column=1, sticky=tk.W)
        self.api_key_entry = key_container
        
        api_entry = tk.Entry(key_container, textvariable=self.api_key, show="草",
                             bd=0, highlightthickness=0, bg="white", width=combo_width)
        api_entry.pack(side=tk.LEFT, fill=tk.Y, padx=(2, 0))
        
        def toggle_key_visibility():
            if api_entry['show'] == '草':
                api_entry.config(show='')
                toggle_btn.config(text='隐藏')
            else:
                api_entry.config(show='草')
                toggle_btn.config(text='显示')
        
        toggle_btn = tk.Button(key_container, text='显示', command=toggle_key_visibility,
                               bd=0, highlightthickness=0, bg="#e0e0e0",
                               activebackground="#d0d0d0", cursor="hand2",
                               padx=6, pady=0, font=("TkDefaultFont", 9))
        toggle_btn.pack(side=tk.RIGHT, fill=tk.Y)
        # 模型选择
        ttk.Label(api_frame, text="模型:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0), padx=(0, 10))
        model_combo = ttk.Combobox(api_frame, textvariable=self.model_var, 
                                   values=model_values,
                                   state="readonly", width=combo_width)
        # 绑定模型选择事件
        model_combo.grid(row=1, column=1, sticky=tk.W, pady=(10, 0), padx=(0, 10))
        model_combo.bind("<<ComboboxSelected>>", self.on_model_change)
        self.model_combo = model_combo

        

        
        
        # 提示词区域
        prompt_frame = ttk.LabelFrame(left_panel, text="提示词 (必填)", padding=10)
        prompt_frame.pack(fill=tk.X, pady=5, padx=5)

        # 提示词控制栏（行数设置和字符计数）
        control_frame = ttk.Frame(prompt_frame)
        control_frame.pack(fill=tk.X)

        # 行数控制（左侧）
        ttk.Label(control_frame, text="行数:").pack(side=tk.LEFT)
        
        def update_line_count(delta):
            current = self.line_count_var.get()
            new_val = max(2, min(98, current + delta))
            self.line_count_var.set(new_val)
            self.prompt_text.config(height=new_val)
        ttk.Label(control_frame, textvariable=self.line_count_var).pack(side=tk.LEFT, padx=(2,8))        
        ttk.Button(control_frame, text="-1", width=3, command=lambda: update_line_count(-1)).pack(side=tk.LEFT, padx=1)
        ttk.Button(control_frame, text="+1", width=3, command=lambda: update_line_count(1)).pack(side=tk.LEFT, padx=1)

        # 字符计数标签（右侧）
        def update_char_count(event=None):
            count = len(self.prompt_text.get("1.0", "end-1c"))
            self.char_label.config(text=f"{count}/{self.MAX_PROMPT_CHARS}")
            self.char_label.config(foreground="red" if count > self.MAX_PROMPT_CHARS else "green")
        
        self.char_label = ttk.Label(control_frame, text=f"0/{self.MAX_PROMPT_CHARS}", font=("TkDefaultFont", 9), anchor=tk.E)
        self.char_label.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        # 提示词输入框
        self.prompt_text = tk.Text(
            prompt_frame, 
            height=self.line_count_var.get(), 
            font=("TkDefaultFont", 10),
            undo=True,
            maxundo=50,
            autoseparators=True
        )
        self.prompt_text.pack(fill=tk.BOTH, expand=True)
        self.prompt_text.bind('<KeyRelease>', update_char_count)
        update_char_count()
        
        # 参考图片区域
        self.ref_frame = ttk.LabelFrame(left_panel, text="参考图片 (可选)", padding=10)
        self.ref_frame.pack(fill=tk.X, pady=5, padx=5)
        # 参考图片按钮和计数
        ref_btn_frame = ttk.Frame(self.ref_frame)
        ref_btn_frame.pack(fill=tk.X)
        # 添加图片和清空按钮
        ttk.Button(ref_btn_frame, text="添加图片", command=self.add_images, width=12).pack(side=tk.LEFT)
        ttk.Button(ref_btn_frame, text="清空全部", command=self.clear_images, width=12).pack(side=tk.LEFT, padx=10)
        # 参考图片计数标签
        self.ref_count_label = ttk.Label(ref_btn_frame, text="已选择: 0/14张", font=("TkDefaultFont", 9, "bold"))
        self.ref_count_label.pack(side=tk.LEFT, padx=20)
        # 参考图片预览区域（带水平滚动条）
        ref_canvas_container = ttk.Frame(self.ref_frame)
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
        ttk.Label(param_grid, text="纵横比:").grid(row=0, column=0, sticky=tk.W, padx=(0, 2))
        aspect_combo = ttk.Combobox(param_grid, textvariable=self.aspect_ratio,
                                   values=["16:9", "5:4", "4:3", "3:2", "", "1:1", "21:9", "", "2:3", "3:4", "4:5", "9:16"], # 空字符串表示分隔线，删除会导致用户不易分辨
                                   state="readonly", width=5, height=9999)
        aspect_combo.grid(row=0, column=1, sticky=tk.W)
        # 分辨率选择
        ttk.Label(param_grid, text="分辨率:").grid(row=0, column=2, sticky=tk.W, padx=(10, 2))
        self.resolution_combo = ttk.Combobox(param_grid, textvariable=self.resolution,
                                            values=["1K"], state="readonly", width=5)
        self.resolution_combo.grid(row=0, column=3, sticky=tk.W)

        # 每次生成前确认参数（变量已在 __init__ 中定义，此处直接复用）
        ttk.Checkbutton(param_grid, text="生成前确认", variable=self.confirm_before_generate).grid(row=0, column=4, sticky=tk.W, padx=(10, 0))

        # 生成按钮（底部，自动调整大小）
        self.generate_btn = ttk.Button(param_frame, text="生成图片", 
                                      command=self.generate_image)
        self.generate_btn.pack(fill=tk.X, padx=5, pady=(10, 5))


        # 状态栏
        status_frame = ttk.Frame(left_panel)
        status_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)

        # 改用Text组件以支持多行和动态高度
        self.status_text = tk.Text(status_frame, height=2, wrap=tk.WORD, 
                                  font=("TkDefaultFont", 9), relief=tk.SUNKEN, 
                                  bg="#f0f0f0", fg="black")
        self.status_text.pack(fill=tk.BOTH, expand=True)
        self.status_text.insert("1.0", "就绪")
        self.status_text.config(state=tk.DISABLED)  # 设为只读
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
        if platform.system() == "Windows" and not self.pywin32_available:
            preview_text = "生成的图片将在此显示\n\n当前环境未安装pywin32，仅支持复制BMP图片（文件体积极大）\n安装命令：pip install --user pywin32"
            self.img_preview = ttk.Label(img_tab, text=preview_text, 
                                        relief=tk.SUNKEN, anchor=tk.CENTER, background="white",
                                        foreground="red")
        else:
            self.img_preview = ttk.Label(img_tab, text="生成的图片将在此显示", 
                                        relief=tk.SUNKEN, anchor=tk.CENTER, background="white")
        self.img_preview.pack(fill=tk.BOTH, expand=True)
        # 图片操作按钮
        btn_frame = ttk.Frame(img_tab)
        btn_frame.pack(pady=10)
        self.save_btn = ttk.Button(btn_frame, text="保存图片", 
                                  command=self.save_image, state=tk.DISABLED, width=18)
        self.save_btn.pack(side=tk.LEFT, padx=5)

        # 根据平台和pywin32可用性设置复制按钮文案
        if platform.system() == "Windows":
            if self.pywin32_available:
                copy_text = "复制图片"
            else:
                copy_text = "复制图片 (BMP)"
        else:
            copy_text = "复制图片"
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
        # 设置只读模式，阻止编辑但允许选择和复制
        self.response_text.bind('<Key>', lambda e: "break")
        self.response_text.bind('<Button-1>', lambda e: "break")
        self._create_context_menu(self.response_text)

        # 根据当前模型更新UI状态，确保启动时分辨率选项正确
        self.on_model_change()
        
        # 首次启动时按回归函数设置左侧宽度
        self.root.after(50, self._apply_zoom)
        
        # 自动导入 default.toml（如存在）
        if TOML_AVAILABLE:
            default_toml = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "default.toml"
            )
            if os.path.isfile(default_toml):
                self.root.after(100, lambda: self._import_toml_file(
                    default_toml, is_auto_import=True
                ))
        
        # 为提示词文本框添加右键菜单
        self._create_context_menu(self.prompt_text)
        
        # 绑定窗口获得焦点事件，清除任务栏进度条
        self.root.bind("<FocusIn>", self._clear_taskbar_on_focus)

    # ==================== 文本框增强功能 ====================
    def _create_context_menu(self, text_widget):
        """为指定Text组件创建右键菜单"""
        menu = tk.Menu(self.root, tearoff=0)
        
        menu.add_command(label="撤销", command=text_widget.edit_undo, 
                        accelerator="Ctrl+Z")
        menu.add_command(label="重做", command=text_widget.edit_redo,
                        accelerator="Ctrl+Y")
        menu.add_separator()
        menu.add_command(label="剪切", 
                        command=lambda: self._cut_text(text_widget),
                        accelerator="Ctrl+X")
        menu.add_command(label="复制", 
                        command=lambda: self._copy_text(text_widget),
                        accelerator="Ctrl+C")
        menu.add_command(label="粘贴", 
                        command=lambda: self._paste_text(text_widget),
                        accelerator="Ctrl+V")
        menu.add_separator()
        menu.add_command(label="全选", 
                        command=lambda: text_widget.tag_add('sel', '1.0', 'end'),
                        accelerator="Ctrl+A")
        
        text_widget.bind("<Button-3>", lambda e: self._show_menu(e, menu))
        if platform.system() == "Darwin":
            text_widget.bind("<Button-2>", lambda e: self._show_menu(e, menu))
            text_widget.bind("<Control-Button-1>", lambda e: self._show_menu(e, menu))

    def _show_menu(self, event, menu):
        """显示右键菜单"""
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _cut_text(self, text_widget):
        """剪切文本"""
        try:
            selected = text_widget.selection_get()
            text_widget.clipboard_clear()
            text_widget.clipboard_append(selected)
            text_widget.delete("sel.first", "sel.last")
        except tk.TclError:
            pass

    def _copy_text(self, text_widget):
        """复制文本"""
        try:
            selected = text_widget.selection_get()
            text_widget.clipboard_clear()
            text_widget.clipboard_append(selected)
        except tk.TclError:
            pass

    def _paste_text(self, text_widget):
        """粘贴文本"""
        try:
            clipboard = text_widget.clipboard_get()
            try:
                text_widget.delete("sel.first", "sel.last")
            except tk.TclError:
                pass
            text_widget.insert(tk.INSERT, clipboard)
        except tk.TclError:
            pass

    # ==================== 核心功能实现 ====================
    # 检测系统代理状态
    def _check_system_proxy(self):
        """检测Windows系统代理状态（其他系统默认返回False）"""
        system = platform.system()
        
        # Windows平台：通过注册表检测系统代理
        if system == "Windows":
            try:
                import ctypes
                from ctypes import wintypes
                import winreg
                
                # 打开注册表键值
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                   r"Software\Microsoft\Windows\CurrentVersion\Internet Settings")
                # 读取代理启用值
                proxy_enable, _ = winreg.QueryValueEx(key, "ProxyEnable")
                winreg.CloseKey(key)
                return proxy_enable == 1
            except Exception:
                return False
        
        # macOS平台预留接口（暂未实现）  
        elif system == "Darwin":
            # TODO: macOS系统代理检测实现
            # 可通过networksetup或scutil命令检测
            return False
        
        # Linux平台预留接口（暂未实现）
        elif system == "Linux":
            # TODO: Linux系统代理检测实现
            # 可通过环境变量或gsettings检测
            return False
        
        # 其他系统默认无代理
        return False
    
    # 获取当前模型的 API 端点
    def get_api_url(self):
        """获取当前模型的 API 端点"""
        model_id = self.model_var.get()
        config = self.MODEL_CONFIGS.get(model_id, {})
        backend = config.get("backend", "nanobanana")
        if backend == "gpt_image_vip":
            return "https://api.laozhang.ai/v1"
        return f"https://api.laozhang.ai/v1beta/models/{model_id}:generateContent"

    # 获取当前后端类型
    def get_backend_type(self):
        """获取当前模型的后端类型"""
        model_id = self.model_var.get()
        config = self.MODEL_CONFIGS.get(model_id, {})
        return config.get("backend", "nanobanana")
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
    def add_images(self, filepaths_without_dialog=None):
        """添加多张参考图片
        
        参数:
            filepaths_without_dialog: 可选，直接传入文件路径列表（用于拖放导入），
                                     为None时弹出文件对话框
        """
        if filepaths_without_dialog is None:
            # 打开文件对话框选择图片
            filepaths = filedialog.askopenfilenames(
                title="选择参考图片",
                filetypes=[("图片文件", "*.jpg *.jpeg *.png *.webp"), ("所有文件", "*.*")]
            )
        else:
            # 拖放导入：直接使用传入的文件路径列表，过滤非图片文件和不存在的文件
            filepaths = [
                fp for fp in filepaths_without_dialog 
                if os.path.isfile(fp) and 
                os.path.splitext(fp)[1].lower() in ['.jpg', '.jpeg', '.png', '.webp']
            ]
            if not filepaths:
                self.update_status("拖放内容中未找到有效的图片文件")
                return
        
        # 没有选择图片则返回
        if not filepaths:
            return
        # 检查是否超过当前模式的最大数量
        available_slots = self.current_max_ref_images - len(self.reference_images)
        if len(filepaths) > available_slots:
            messagebox.showwarning(
                "警告",
                f"当前模型最多支持 {self.current_max_ref_images} 张参考图片，"
                f"当前已选择 {len(self.reference_images)} 张，还可添加 {available_slots} 张"
            )
            filepaths = filepaths[:available_slots]
        added_count = 0
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
                added_count += 1
            # 捕获异常并提示
            except Exception as e:
                messagebox.showerror("错误", f"加载图片失败: {filepath}\n{str(e)}")
        # 更新预览
        self.update_reference_preview()
        self.update_status(f"已添加 {added_count} 张参考图片")

    # 处理拖放事件：将拖入窗口的图片文件自动导入为参考图片
    def on_drop(self, event):
        """处理拖放事件：优先检测 TOML 配置文件，否则导入图片"""
        # tkinterdnd2 传入的 event.data 通常为文件URL格式或路径列表，需解析
        # 多文件格式示例：{C:\path with spaces\a.jpg} {C:\path\b.jpg}
        raw = event.data
        toml_files = []
        supported_paths = []
        unsupported_exts = set()
        # 按花括号分组解析，避免带空格路径被空格拆散
        import re
        items = re.findall(r'\{([^}]*)\}|(\S+)', raw)
        for match in items:
            # re.findall 返回元组，取第一个非空分组
            item = match[0] if match[0] else match[1]
            if not item:
                continue
            # 去掉 file:// 前缀（如有）
            if item.startswith('file://'):
                item = item[7:]
            # 去掉花括号和引号
            item = item.strip('{}"')
            ext = os.path.splitext(item)[1].lower()
            # --- TOML 配置文件检测 ---
            if ext == '.toml':
                toml_files.append(item)
                continue
            # --- 图片文件 ---
            if ext in ['.jpg', '.jpeg', '.png', '.webp']:
                supported_paths.append(item)
            else:
                if ext:
                    unsupported_exts.add(ext)
                else:
                    # 无扩展名（如文件夹）标记为 "[文件夹]"
                    unsupported_exts.add("[文件夹]")

        # --- TOML 配置文件优先处理 ---
        if toml_files:
            if supported_paths or unsupported_exts:
                messagebox.showwarning("提示", "请分开导入图片和配置文件。")
                return
            if len(toml_files) > 1:
                messagebox.showwarning("提示", "一次只可以拖入一个配置文件。")
                return
            if not TOML_AVAILABLE:
                messagebox.showwarning("提示", "配置导入功能不可用，因为缺少 tomllib/tomli 库。")
                return
            self._import_toml_file(toml_files[0], is_auto_import=False)
            return
        # --- 以下为原有的图片导入逻辑 ---
        
        # 如果有不支持的格式，弹出确认对话框
        if unsupported_exts:
            # 构建弹窗
            dialog = tk.Toplevel(self.root)
            dialog.title("提示")
            dialog.transient(self.root)
            dialog.grab_set()
            dialog.resizable(True, True)
            dialog.bind("<Escape>", lambda e: dialog.destroy())
            
            # 文案
            ext_list = ", ".join(sorted(unsupported_exts))
            message = f"暂不支持以下格式：\n\n{ext_list}\n\n若您需要导入其他格式的图片，\n请先使用工具将其转换为JPG、PNG、WEBP格式。"
            label = tk.Label(dialog, text=message, justify=tk.LEFT, wraplength=400)
            label.pack(padx=20, pady=15, fill=tk.BOTH, expand=True)
            
            # 按钮框架
            btn_frame = tk.Frame(dialog)
            btn_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
            
            result = {"import_supported": False}
            
            def on_import_supported():
                result["import_supported"] = True
                dialog.destroy()
            
            def on_cancel_all():
                result["import_supported"] = False
                dialog.destroy()
            
            # 两个按钮水平均分
            import_btn = ttk.Button(btn_frame, text="仅导入支持的图片", command=on_import_supported)
            import_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
            cancel_btn = ttk.Button(btn_frame, text="取消全部导入", command=on_cancel_all)
            cancel_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
            
            # 设置关闭按钮行为
            dialog.protocol("WM_DELETE_WINDOW", on_import_supported)
            
            # 居中弹窗
            dialog.update_idletasks()
            x = self.root.winfo_rootx() + self.root.winfo_width() // 2 - dialog.winfo_width() // 2
            y = self.root.winfo_rooty() + self.root.winfo_height() // 2 - dialog.winfo_height() // 2
            dialog.geometry(f"+{x}+{y}")
            
            self.root.wait_window(dialog)
            
            if not result["import_supported"]:
                self.update_status("用户取消全部导入")
                return
        
        # 导入支持的图片
        if supported_paths:
            self.update_status(f"正在导入拖放的 {len(supported_paths)} 张图片...")
            self.add_images(filepaths_without_dialog=supported_paths)
        else:
            self.update_status("拖放内容中未找到有效的图片文件")

    # ==================== TOML 配置文件解析与校验 ====================
    def _parse_toml(self, filepath):
        """解析 TOML 文件，返回 (config_dict, None) 或 (None, error_msg)"""
        if not TOML_AVAILABLE:
            return None, "缺少 tomllib/tomli 库，配置导入功能不可用"
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                raw = f.read()
            config = tomllib.loads(raw)
            return config, None
        except Exception as e:
            return None, f"TOML 解析失败: {str(e)}"

    def _validate_reference_path(self, path):
        """校验单个参考图片路径，返回 (is_valid, error_msg)"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 解析路径：绝对路径直接用，否则相对于脚本目录
        if os.path.isabs(path):
            resolved = path
        else:
            resolved = os.path.join(script_dir, path)
        resolved = os.path.normpath(resolved)
        if not os.path.isfile(resolved):
            return False, f"参考图片路径不存在: {path}"
        ext = os.path.splitext(resolved)[1].lower()
        if ext not in self.TOML_VALID_VALUES["valid_image_exts"]:
            return False, f"参考图片格式不支持 ({ext}): {path}"
        try:
            img = Image.open(resolved)
            img.verify()
        except Exception as e:
            return False, f"参考图片不是有效图片: {path} ({str(e)})"
        return True, resolved

    def _validate_toml_config(self, config_dict):
        """校验 TOML 配置的所有字段，返回 (is_valid, errors_list)"""
        errors = []

        # ---- import_mode（必填）----
        import_mode = config_dict.get("import_mode", None)
        if not import_mode or not isinstance(import_mode, str):
            errors.append("import_mode 不存在或为空")
        elif import_mode not in self.TOML_VALID_VALUES["import_mode"]:
            errors.append(f"import_mode 值不合法: {import_mode}")
        valid_mode = (import_mode in self.TOML_VALID_VALUES["import_mode"]) if isinstance(import_mode, str) else False

        # ---- [api] ----
        api = config_dict.get("api", {})
        if isinstance(api, dict):
            # api.key：可为空字符串
            api_key = api.get("key", None)
            if api_key is not None and not isinstance(api_key, str):
                errors.append("api.key 必须是字符串")
            # api.model
            model = api.get("model", None)
            if model is not None:
                if not isinstance(model, str) or model not in self.TOML_VALID_VALUES["model"]:
                    errors.append(f"api.model 值不合法: {model}")
        else:
            if api is not None:
                errors.append("[api] 段格式错误")

        # ---- [generation] ----
        gen = config_dict.get("generation", {})
        if isinstance(gen, dict):
            ar = gen.get("aspect_ratio", None)
            if ar is not None:
                if not isinstance(ar, str) or ar not in self.TOML_VALID_VALUES["aspect_ratio"]:
                    errors.append(f"generation.aspect_ratio 值不合法: {ar}")
            res = gen.get("resolution", None)
            if res is not None:
                if not isinstance(res, str) or res not in self.TOML_VALID_VALUES["resolution"]:
                    errors.append(f"generation.resolution 值不合法: {res}")
            nto = gen.get("network_timeout", None)
            if nto is not None:
                try:
                    nto_int = int(nto)
                    if nto_int < 0:
                        errors.append(f"generation.network_timeout 不能为负数: {nto}")
                except (ValueError, TypeError):
                    errors.append(f"generation.network_timeout 格式错误: {nto}")
            cbg = gen.get("confirm_before_generate", None)
            if cbg is not None and not isinstance(cbg, bool):
                errors.append("generation.confirm_before_generate 必须是 true/false")
            ltf = gen.get("log_to_file", None)
            if ltf is not None and not isinstance(ltf, bool):
                errors.append("generation.log_to_file 必须是 true/false")
        else:
            if gen is not None:
                errors.append("[generation] 段格式错误")

        # ---- prompt（位于 [generation] 段内或顶层）----
        prompt = config_dict.get("prompt", None)
        if prompt is None and isinstance(gen, dict):
            prompt = gen.get("prompt", None)
        if prompt is not None and not isinstance(prompt, str):
            errors.append("prompt 必须是字符串")

        # ---- [ui] ----
        ui = config_dict.get("ui", {})
        if isinstance(ui, dict):
            zoom = ui.get("zoom", None)
            if zoom is not None:
                if not isinstance(zoom, str) or zoom not in self.TOML_VALID_VALUES["zoom"]:
                    errors.append(f"ui.zoom 值不合法: {zoom}")
            pl = ui.get("prompt_lines", None)
            if pl is not None:
                try:
                    pl_int = int(pl)
                    if pl_int < 2 or pl_int > 98:
                        errors.append(f"ui.prompt_lines 必须在 2~98 之间: {pl}")
                except (ValueError, TypeError):
                    errors.append(f"ui.prompt_lines 格式错误: {pl}")
        else:
            if ui is not None:
                errors.append("[ui] 段格式错误")

        # ---- [[reference_images]] ----
        refs = config_dict.get("reference_images", [])
        if refs and isinstance(refs, list):
            for i, ref in enumerate(refs):
                if isinstance(ref, dict):
                    path = ref.get("path", "")
                    if not path:
                        continue
                    is_ok, msg = self._validate_reference_path(path)
                    if not is_ok:
                        errors.append(msg)
                else:
                    errors.append(f"reference_images[{i}] 格式错误")

        return (len(errors) == 0, errors)

    # ==================== TOML 配置应用 ====================
    def _reset_all_to_defaults(self):
        """将所有可配置项恢复到默认值"""
        defaults = self.TOML_DEFAULTS
        self.api_key.set(defaults["api_key"])
        self.model_var.set(defaults["model"])
        self.aspect_ratio.set(defaults["aspect_ratio"])
        self.resolution.set(defaults["resolution"])
        self.network_timeout.set(defaults["network_timeout"])
        self.confirm_before_generate.set(defaults["confirm_before_generate"])
        self.log_to_file.set(defaults["log_to_file"])
        self.zoom_var.set(defaults["zoom"])
        self.line_count_var.set(defaults["prompt_lines"])
        self.prompt_text.delete("1.0", tk.END)
        self.prompt_text.config(height=defaults["prompt_lines"])
        self.reference_images.clear()
        self.ref_canvas.delete("all")
        self.update_ref_count_label()
        self.last_verified_params = None
        self.on_model_change()
        self._apply_zoom()

    def _apply_toml_config(self, config_dict, mode):
        """根据模式将 TOML 配置写入 UI 控件"""
        if mode == "clear_and_overwrite":
            self._reset_all_to_defaults()

        # ---- [api] ----
        api = config_dict.get("api", {})
        if isinstance(api, dict):
            if "key" in api:
                self.api_key.set(str(api["key"]) if api["key"] is not None else "")
            if "model" in api and api["model"]:
                self.model_var.set(str(api["model"]))

        # ---- [generation] ----
        gen = config_dict.get("generation", {})
        if isinstance(gen, dict):
            if "aspect_ratio" in gen and gen["aspect_ratio"]:
                self.aspect_ratio.set(str(gen["aspect_ratio"]))
            if "resolution" in gen and gen["resolution"]:
                self.resolution.set(str(gen["resolution"]))
            if "network_timeout" in gen:
                self.network_timeout.set(str(gen["network_timeout"]))
            if "confirm_before_generate" in gen:
                self.confirm_before_generate.set(bool(gen["confirm_before_generate"]))
            if "log_to_file" in gen:
                self.log_to_file.set(bool(gen["log_to_file"]))

        # ---- prompt（位于 [generation] 段内或顶层）----
        prompt_val = config_dict.get("prompt", None)
        if prompt_val is None and isinstance(gen, dict):
            prompt_val = gen.get("prompt", None)
        if prompt_val is not None:
            self.prompt_text.delete("1.0", tk.END)
            if prompt_val:
                self.prompt_text.insert("1.0", str(prompt_val))

        # ---- [ui] ----
        ui = config_dict.get("ui", {})
        zoom_changed = False
        if isinstance(ui, dict):
            if "zoom" in ui and ui["zoom"]:
                new_zoom = str(ui["zoom"])
                if self.zoom_var.get() != new_zoom:
                    zoom_changed = True
                self.zoom_var.set(new_zoom)
            if "prompt_lines" in ui:
                lines = int(ui["prompt_lines"])
                self.line_count_var.set(lines)
                self.prompt_text.config(height=lines)

        # ---- [[reference_images]] ----
        refs = config_dict.get("reference_images", None)
        if refs is not None and isinstance(refs, list):
            self.reference_images.clear()
            for ref in refs:
                if isinstance(ref, dict):
                    path = ref.get("path", "")
                    if not path:
                        continue
                    is_ok, resolved = self._validate_reference_path(path)
                    if not is_ok:
                        continue
                    try:
                        mime_type = self.get_mime_type(resolved)
                        with open(resolved, "rb") as f:
                            image_b64 = base64.b64encode(f.read()).decode("utf-8")
                        original_img = Image.open(resolved)
                        self.reference_images.append(
                            (resolved, image_b64, mime_type, original_img)
                        )
                    except Exception:
                        continue
            self.update_reference_preview()

        # UI 同步
        self.on_model_change()
        if zoom_changed:
            self._apply_zoom()
            self._update_model_combo_width()

    def _import_toml_file(self, filepath, is_auto_import=False):
        """导入 TOML 配置文件的主入口

        参数:
            filepath: TOML 文件路径
            is_auto_import: True 表示由 default.toml 自动触发，跳过确认弹窗
        """
        if not TOML_AVAILABLE:
            self.update_status("配置导入失败: 缺少 tomllib/tomli 库")
            return

        basename = os.path.basename(filepath)

        # 1. 解析
        config, parse_err = self._parse_toml(filepath)
        if config is None:
            self.update_status(f"配置导入失败 ({basename}): {parse_err}")
            messagebox.showerror("配置文件错误",
                f"您导入的配置文件无效，因为格式错误、不是配置文件，或者其它未知错误。\n\n详情: {parse_err}")
            return

        # 2. 提取 import_mode
        import_mode = config.get("import_mode", None)
        if not import_mode or not isinstance(import_mode, str) or \
           import_mode not in self.TOML_VALID_VALUES["import_mode"]:
            self.update_status(f"配置导入失败 ({basename}): import_mode 无效")
            messagebox.showerror("配置文件错误",
                "您导入的配置文件无效，因为格式错误、不是配置文件，或者其它未知错误。")
            return

        # 3. 校验所有字段
        is_valid, errors = self._validate_toml_config(config)
        file_label = f"[自动导入] {basename}" if is_auto_import else basename

        # 4. 按模式分流
        if import_mode == "clear_and_overwrite":
            if not is_valid:
                self.update_status(f"配置导入失败 ({file_label}): 存在 {len(errors)} 处错误")
                err_text = "\n".join(f"  - {e}" for e in errors[:10])
                if len(errors) > 10:
                    err_text += f"\n  ... 还有 {len(errors) - 10} 处错误"
                messagebox.showerror("配置文件校验失败",
                    f"配置文件存在 {len(errors)} 处错误，已拒绝导入以保护数据安全。\n\n{err_text}")
                return
            # 无错误：确认弹窗（自动导入时跳过）
            if not is_auto_import:
                if not messagebox.askyesno("确认导入配置",
                        "这会清空全部内容，然后应用配置文件。\n此操作无法撤销，是否继续？"):
                    self.update_status(f"用户取消配置导入: {basename}")
                    return
            self._apply_toml_config(config, "clear_and_overwrite")
            self.update_status(f"已导入配置文件 ({file_label}) — 模式: 清空并覆盖")

        elif import_mode == "overwrite_existing":
            if not is_valid:
                err_text = "\n".join(f"  - {e}" for e in errors[:10])
                if len(errors) > 10:
                    err_text += f"\n  ... 还有 {len(errors) - 10} 处错误"
                user_choice = messagebox.askyesno("配置文件校验失败",
                    f"配置文件存在 {len(errors)} 处错误。\n\n{err_text}\n\n是否强行导入（跳过错误项）？\n选「是」强行导入，「否」取消全部导入。")
                if user_choice:
                    self._apply_toml_config(config, "overwrite_existing")
                    self.update_status(
                        f"已部分导入配置文件 ({file_label}) — 模式: 覆盖已有（跳过 {len(errors)} 处错误）")
                else:
                    self.update_status(f"用户取消配置导入: {basename}")
                return
            # 无错误：确认弹窗（自动导入时跳过）
            if not is_auto_import:
                if not messagebox.askyesno("确认导入配置",
                        "这会应用配置文件里已有的配置（值留空的配置项一样会被清空），"
                        "没有写的配置不会改变。\n此操作无法撤销，是否继续？"):
                    self.update_status(f"用户取消配置导入: {basename}")
                    return
            self._apply_toml_config(config, "overwrite_existing")
            self.update_status(f"已导入配置文件 ({file_label}) — 模式: 覆盖已有")

    # ==================== 原有方法 ====================
    def update_ref_count_label(self):
        """更新参考图片计数标签"""
        self.ref_count_label.config(
            text=f"已选择: {len(self.reference_images)}/{self.current_max_ref_images}张"
        )

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
        self.update_ref_count_label()
    # 删除参考图片
    def remove_reference(self, index):
        """删除指定参考图片"""
        if 0 <= index < len(self.reference_images):
            del self.reference_images[index]
            self.update_reference_preview()
            self.update_status(f"已删除第 {index+1} 张参考图片")
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
            self.update_status("已清空所有参考图片")
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
        
        # 验证纵横比是否已选择
        if not self.aspect_ratio.get():
            messagebox.showwarning("提示", "请选择比例")
            return
        
        # 检查参考图片文件是否存在
        missing_files = []
        for filepath, _, _, _ in self.reference_images:
            if not os.path.exists(filepath):
                missing_files.append(filepath)
        if missing_files:
            missing_names = "\n".join(os.path.basename(p) for p in missing_files)
            messagebox.showerror("文件错误", f"以下参考图片文件不存在或已被移动/重命名：\n{missing_names}\n\n请重新添加这些图片。")
            self.update_status("生成失败：参考图片文件缺失")
            return

        # 生成前参数确认弹窗（优先于代理检测）
        if self.confirm_before_generate.get():
            current_params = (self.model_var.get(), self.aspect_ratio.get(), self.resolution.get())
            if current_params == self.last_verified_params:
                self.update_status("参数未变化，跳过确认")
            else:
                if not self._show_param_confirm_dialog():
                    self.update_status("用户取消生成（参数确认未通过）")
                    return
                self.last_verified_params = current_params
        else:
            # 关闭总开关时清空已验证记录，避免下次开启后错误跳过
            self.last_verified_params = None
        
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
                self.update_status("用户取消生成")
                return
        
        # 新增：检测系统代理并提示（如果未抑制）
        if not self.proxy_warning_suppressed and self._check_system_proxy():
            if not self._show_proxy_warning_dialog():
                self.update_status("用户取消生成（检测到代理启用）")
                return
        
        # 禁用生成按钮
        self.generate_btn.config(state=tk.DISABLED, text="生成中...")
        self.update_status("正在生成图片...")
        
        # Windows 任务栏进度条：显示不确定动画
        if self.taskbar_progress:
            self.taskbar_progress.set_progress(0, 0x1)  # TBPF_INDETERMINATE
        
        # 根据后端类型选择线程函数
        backend = self.get_backend_type()
        if backend == "gpt_image_vip":
            self.generate_thread = threading.Thread(
                target=self._generate_thread_gpt_vip,
                args=(self.api_key.get(), prompt),
                daemon=True
            )
        else:
            self.generate_thread = threading.Thread(
                target=self._generate_thread,
                args=(self.api_key.get(), prompt),
                daemon=True
            )
        self.generate_thread.start()
    # 后台线程生成图片 (NanoBanana)
    def _generate_thread(self, api_key, prompt):
        """后台线程执行NanoBanana API调用"""
        try:
            # 构建请求数据
            parts = [{"text": prompt}]
            
            # 添加参考图片
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
            if self.model_var.get() in ["gemini-3-pro-image-preview", "gemini-3.1-flash-image-preview"]:
                payload["generationConfig"]["imageConfig"]["imageSize"] = self.resolution.get()
            
            # 发送请求
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # 获取超时设置，0表示无超时
            timeout_val = int(self.network_timeout.get()) if self.network_timeout.get().isdigit() else 1200
            timeout = None if timeout_val == 0 else timeout_val
            
            full_url = self.get_api_url()
            response = requests.post(
                full_url,
                headers=headers,
                json=payload,
                timeout=timeout
            )
            
            # 确定实际发送的 imageSize（stable 模型不发送）
            actual_image_size = None
            if self.model_var.get() in ["gemini-3-pro-image-preview", "gemini-3.1-flash-image-preview"]:
                actual_image_size = self.resolution.get()
            
            # 在主线程中处理响应
            self.root.after(0, self._handle_response, response, full_url, actual_image_size)
        except Exception as e:
            self.root.after(0, self._handle_error, str(e), full_url)

    # 后台线程生成图片 (GPT Image 2 VIP)
    def _generate_thread_gpt_vip(self, api_key, prompt):
        """后台线程执行GPT Image 2 VIP API调用"""
        # 获取超时设置
        timeout_val = int(self.network_timeout.get()) if self.network_timeout.get().isdigit() else 1200
        timeout = None if timeout_val == 0 else timeout_val
        
        # 计算size参数
        aspect = self.aspect_ratio.get()
        resolution = self.resolution.get()
        size = self.VIP_SIZE_MAP.get(aspect, {}).get(resolution, "2048x2048")
        
        base_url = self.get_api_url()
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        full_url = None
        response = None
        opened_files = []
        
        try:
            # 有参考图片时调用 edits，否则调用 generations
            if self.reference_images:
                # 图改图：使用 multipart/form-data
                full_url = f"{base_url}/images/edits"
                files = []
                data = {
                    "model": "gpt-image-2-vip",
                    "prompt": prompt,
                    "size": size
                }
                # 发送所有参考图片
                for filepath, _, mime_type, _ in self.reference_images:
                    f = open(filepath, "rb")
                    opened_files.append(f)
                    files.append(("image", (os.path.basename(filepath), f, mime_type)))
                
                response = requests.post(
                    full_url,
                    headers=headers,
                    data=data,
                    files=files,
                    timeout=timeout
                )
            else:
                # 文生图：使用 JSON
                full_url = f"{base_url}/images/generations"
                payload = {
                    "model": "gpt-image-2-vip",
                    "prompt": prompt,
                    "size": size
                }
                
                response = requests.post(
                    full_url,
                    headers={**headers, "Content-Type": "application/json"},
                    json=payload,
                    timeout=timeout
                )
            
            # 确定 GPT 调用类型
            gpt_endpoint_type = "edits" if self.reference_images else "generations"
            
            # 在主线程中处理响应
            self.root.after(0, self._handle_response_gpt_vip, response, full_url, gpt_endpoint_type)
        except Exception as e:
            self.root.after(0, self._handle_error, str(e), full_url if full_url else base_url)
        finally:
            # 确保所有打开的文件句柄都被关闭
            for f in opened_files:
                try:
                    f.close()
                except Exception:
                    pass
    # 处理API响应 (NanoBanana)
    def _handle_response(self, response, url=None, actual_image_size=None):
        """处理NanoBanana API响应"""
        try:
            # 检查HTTP状态码
            if response.status_code != 200:
                error_msg = f"HTTP错误 {response.status_code}: {response.text}"
                self._clear_taskbar_before_error()
                messagebox.showerror("API错误", error_msg)
                self.update_status(f"生成失败: HTTP {response.status_code}")
                if self.log_to_file.get():
                    self._save_log({"error": error_msg, "status_code": response.status_code}, "error", url=url, actual_image_size=actual_image_size)
                return
            # 解析JSON响应
            result = response.json()
            self.last_raw_response = result
            
            # 检查API错误
            if "error" in result:
                error_msg = result["error"].get("message", str(result["error"]))
                self._clear_taskbar_before_error()
                messagebox.showerror("API错误", error_msg)
                self.update_status("生成失败: API错误")
                if self.log_to_file.get():
                    self._save_log({"error": error_msg, "raw_response": result}, "error", url=url, actual_image_size=actual_image_size)
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
                
                if "parts" not in candidate["content"] or not candidate["content"]["parts"]:
                    raise ValueError("响应中未找到图片数据")
                
                image_data = candidate["content"]["parts"][0]["inlineData"]["data"]
                mime_type = candidate["content"]["parts"][0]["inlineData"].get("mimeType", "image/png")
                self.current_image_data = image_data
                self.current_image_mime_type = mime_type
                self.current_image_model = self.model_var.get()  # 记录生成时使用的模型
                
                self._show_image()
                
                display_data = self._optimize_display_data(result)
                self.response_text.delete("1.0", tk.END)
                self.response_text.insert("1.0", json.dumps(display_data, indent=2, ensure_ascii=False))
                
                self.save_btn.config(state=tk.NORMAL)
                self.copy_btn.config(state=tk.NORMAL)
                self.update_status("生成成功")
                
                # Windows 任务栏进度条：显示 100% 绿色确定进度
                if self.taskbar_progress:
                    self.taskbar_progress.set_progress(100, 0x2)  # TBPF_NORMAL
                
                if self.log_to_file.get():
                    self._save_log(result, "success", url=url, actual_image_size=actual_image_size)
            except (KeyError, IndexError, ValueError) as e:
                self._clear_taskbar_before_error()
                messagebox.showerror("响应错误", f"处理API响应失败:\n{str(e)}")
                self.response_text.delete("1.0", tk.END)
                self.response_text.insert("1.0", json.dumps(result, indent=2, ensure_ascii=False))
                self.update_status(f"生成失败: {str(e)[:50]}...")
        finally:
            self.generate_btn.config(state=tk.NORMAL, text="生成图片")

    # 处理API响应 (GPT Image 2 VIP)
    def _handle_response_gpt_vip(self, response, url=None, gpt_endpoint_type=None):
        """处理GPT Image 2 VIP API响应"""
        try:
            # 检查HTTP状态码
            if response.status_code != 200:
                error_msg = f"HTTP错误 {response.status_code}: {response.text}"
                self._clear_taskbar_before_error()
                messagebox.showerror("API错误", error_msg)
                self.update_status(f"生成失败: HTTP {response.status_code}")
                if self.log_to_file.get():
                    self._save_log({"error": error_msg, "status_code": response.status_code}, "error", url=url, gpt_endpoint_type=gpt_endpoint_type)
                return
            
            # 解析JSON响应
            result = response.json()
            self.last_raw_response = result
            
            # 检查API错误
            if "error" in result:
                error_msg = result["error"].get("message", str(result["error"]))
                self._clear_taskbar_before_error()
                messagebox.showerror("API错误", error_msg)
                self.update_status("生成失败: API错误")
                if self.log_to_file.get():
                    self._save_log({"error": error_msg, "raw_response": result}, "error", url=url, gpt_endpoint_type=gpt_endpoint_type)
                return
            
            # 提取图片数据
            try:
                if "data" not in result or not result["data"]:
                    raise ValueError("响应中未找到 data 数据")
                
                image_item = result["data"][0]
                
                # 优先使用 b64_json
                if "b64_json" in image_item and image_item["b64_json"]:
                    image_data = image_item["b64_json"]
                    # 处理可能的前缀
                    if image_data.startswith("data:"):
                        image_data = image_data.split(",", 1)[1]
                    # 补齐padding
                    image_data += "=" * ((4 - len(image_data) % 4) % 4)
                elif "url" in image_item and image_item["url"]:
                    # 如果是URL，下载图片
                    self.update_status("检测到URL返回，正在下载图片...")
                    img_response = requests.get(image_item["url"], timeout=60)
                    img_response.raise_for_status()
                    image_data = base64.b64encode(img_response.content).decode("utf-8")
                else:
                    raise ValueError("响应中未找到图片数据（b64_json 或 url）")
                
                self.current_image_data = image_data
                self.current_image_mime_type = "image/png"
                self.current_image_model = self.model_var.get()  # 记录生成时使用的模型
                
                self._show_image()
                
                display_data = self._optimize_display_data(result)
                self.response_text.delete("1.0", tk.END)
                self.response_text.insert("1.0", json.dumps(display_data, indent=2, ensure_ascii=False))
                
                self.save_btn.config(state=tk.NORMAL)
                self.copy_btn.config(state=tk.NORMAL)
                self.update_status("生成成功")
                
                # Windows 任务栏进度条：显示 100% 绿色确定进度
                if self.taskbar_progress:
                    self.taskbar_progress.set_progress(100, 0x2)  # TBPF_NORMAL
                
                if self.log_to_file.get():
                    self._save_log(result, "success", url=url, gpt_endpoint_type=gpt_endpoint_type)
            except (KeyError, IndexError, ValueError) as e:
                self._clear_taskbar_before_error()
                messagebox.showerror("响应错误", f"处理API响应失败:\n{str(e)}")
                self.response_text.delete("1.0", tk.END)
                self.response_text.insert("1.0", json.dumps(result, indent=2, ensure_ascii=False))
                self.update_status(f"生成失败: {str(e)[:50]}...")
        finally:
            self.generate_btn.config(state=tk.NORMAL, text="生成图片")
    # 处理异常错误
    def _handle_error(self, error_msg, url=None):
        """处理异常错误"""
        # 没有做错误的进度条，是因为错误弹窗自带变色显示，不需要额外的进度条了
        
        # 先清除任务栏进度条，避免弹窗期间进度条残留
        if self.taskbar_progress:
            self.taskbar_progress.clear()
        
        # 再恢复按钮状态
        self.update_status("生成失败: 异常错误")
        self.generate_btn.config(state=tk.NORMAL, text="生成图片")
        
        # 强制刷新 UI，让按钮恢复和进度条清除在模态弹窗阻塞前立即生效
        self.root.update_idletasks()
        
        messagebox.showerror("错误", f"生成过程中发生异常:\n{error_msg}")
        
        # **改进：记录错误日志**
        if self.log_to_file.get():
            self._save_log({"error": error_msg, "exception": True}, "error", url=url)
    
    # 参数确认弹窗
    def _show_param_confirm_dialog(self):
        """显示生成前参数确认弹窗，返回用户是否通过验证"""
        dialog = tk.Toplevel(self.root)
        dialog.title("参数确认")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(True, True)
        # 绑定Esc关闭弹窗（视为取消/返回）
        dialog.bind("<Escape>", lambda e: dialog.destroy())
        
        # 根据主窗口当前大小动态计算弹窗尺寸
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()
        dialog_width = max(320, int(root_width * 0.35))
        dialog_height = max(240, int(root_height * 0.30))
        dialog.geometry(f"{dialog_width}x{dialog_height}")
        
        result = False
        
        # 获取当前参数
        model = self.model_var.get()
        aspect = self.aspect_ratio.get()
        resolution = self.resolution.get()
        
        # 随机选择要验证的参数项
        verify_target = random.choice(["分辨率", "纵横比", "模型"])
        
        # 构建显示文案
        info_text = f"模型：{model}\n纵横比：{aspect}     分辨率：{resolution}"
        question_text = f"请选择正确的{verify_target}以继续生成：\n如果下一次生成时参数未改变，本窗口将不出现，直到改变参数。"
        
        # 生成正确和错误选项
        if verify_target == "分辨率":
            correct_answer = resolution
            wrong_candidates = [r for r in ["1K", "2K", "4K"] if r != resolution]
            wrong_answer = random.choice(wrong_candidates) if wrong_candidates else "8K"
        elif verify_target == "纵横比":
            correct_answer = aspect
            all_aspects = ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"]
            wrong_candidates = [a for a in all_aspects if a != aspect]
            wrong_answer = random.choice(wrong_candidates) if wrong_candidates else "1:2"
        else:  # 模型
            correct_answer = model
            all_models = list(self.MODEL_CONFIGS.keys())
            wrong_candidates = [m for m in all_models if m != model]
            wrong_answer = random.choice(wrong_candidates) if wrong_candidates else "unknown-model"
        
        # 随机打乱正确和错误的位置
        answers = [(correct_answer, True), (wrong_answer, False)]
        random.shuffle(answers)
        
        # 标题和信息
        tk.Label(dialog, text="参数确认", font=("TkDefaultFont", 12, "bold")).pack(pady=(10, 5))
        tk.Label(dialog, text=info_text, justify=tk.LEFT).pack(pady=5, padx=20)
        tk.Label(dialog, text=question_text, justify=tk.LEFT).pack(pady=(10, 5), padx=20)
        
        # 答案按钮区域
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=5, padx=20, fill=tk.X)
        
        def on_answer(is_correct):
            nonlocal result
            if is_correct:
                result = True
                dialog.destroy()
            else:
                dialog.destroy()
                messagebox.showerror("参数不一致", "参数不一致！请检查参数后重新生成。")
                result = False
        
        # 两个答案按钮（长条）
        for answer_text, is_correct in answers:
            btn = ttk.Button(btn_frame, text=answer_text, command=lambda c=is_correct: on_answer(c))
            btn.pack(fill=tk.X, pady=3)
        
        # 返回按钮
        back_btn = ttk.Button(dialog, text="返回", command=dialog.destroy)
        back_btn.pack(fill=tk.X, pady=(5, 10), padx=20)
        
        # 居中显示
        dialog.update_idletasks()
        x = self.root.winfo_rootx() + self.root.winfo_width() // 2 - dialog.winfo_width() // 2
        y = self.root.winfo_rooty() + self.root.winfo_height() // 2 - dialog.winfo_height() // 2
        dialog.geometry(f"+{x}+{y}")
        
        self.root.wait_window(dialog)
        return result

    # 代理警告弹窗
    def _show_proxy_warning_dialog(self):
        """显示代理警告弹窗，返回用户是否选择继续"""
        dialog = tk.Toplevel(self.root)
        dialog.title("网络环境检测")
        dialog.geometry("400x150")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(True, True)
        # 绑定Esc关闭弹窗
        dialog.bind("<Escape>", lambda e: dialog.destroy())
        
        result = False
        suppress_var = tk.BooleanVar(value=False)
        
        # 提示文本
        message = "检测到您已开启系统代理，请确保网络环境稳定，否则图片会传输失败，无法续传。是否继续生成？"
        label = tk.Label(dialog, text=message, wraplength=350, justify=tk.LEFT, padx=10, pady=10)
        label.pack(fill=tk.X)
        
        # 复选框
        check_btn = tk.Checkbutton(dialog, text="本次不再提示", variable=suppress_var)
        check_btn.pack(pady=5)
        
        # 按钮区域
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        def on_continue():
            nonlocal result, suppress_var
            result = True
            self.proxy_warning_suppressed = suppress_var.get()
            dialog.destroy()
        
        def on_cancel():
            nonlocal result
            result = False
            dialog.destroy()
        
        continue_btn = ttk.Button(btn_frame, text="继续生成", command=on_continue, width=12)
        continue_btn.pack(side=tk.LEFT, padx=10)
        
        cancel_btn = ttk.Button(btn_frame, text="取消", command=on_cancel, width=12)
        cancel_btn.pack(side=tk.LEFT, padx=10)
        
        # 居中显示
        dialog.update_idletasks()
        x = self.root.winfo_rootx() + self.root.winfo_width() // 2 - dialog.winfo_width() // 2
        y = self.root.winfo_rooty() + self.root.winfo_height() // 2 - dialog.winfo_height() // 2
        dialog.geometry(f"+{x}+{y}")
        
        self.root.wait_window(dialog)
        return result
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
        
        # 根据MIME类型确定默认扩展名
        mime_to_ext = {
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/png": ".png"
        }
        default_ext = mime_to_ext.get(self.current_image_mime_type, ".png")
        
        # 生成默认文件名，使用生成图片时的模型名（而非当前下拉框选中的模型）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 优先使用生成时记录的模型，如果没有则回退到当前选中模型
        saved_model = getattr(self, 'current_image_model', self.model_var.get())
        saved_config = self.MODEL_CONFIGS.get(saved_model, {})
        saved_backend = saved_config.get("backend", "nanobanana")
        
        if saved_backend == "gpt_image_vip":
            model_short = "vip"
            prefix = "gpt_images2"
        else:
            model_short = saved_model.split("-")[1] if "-" in saved_model else saved_model
            prefix = "gemini"
        default_filename = f"{prefix}_{model_short}_{self.resolution.get()}_{timestamp}{default_ext}"
        
        # 设置文件类型选项
        if self.current_image_mime_type == "image/jpeg":
            file_types = [("JPEG图片", "*.jpg"), ("所有文件", "*.*")]
        else:
            file_types = [("PNG图片", "*.png"), ("所有文件", "*.*")]
        
        # 打开保存对话框
        filepath = filedialog.asksaveasfilename(
            title="保存图片",
            defaultextension=default_ext,
            filetypes=file_types,
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
            self.update_status(f" 图片已保存: {os.path.basename(filepath)}")
            
            # 记录日志
            if self.log_to_file.get():
                self._save_log({"saved_file": filepath}, "save")
                # 可选：提示保存成功
                # messagebox.showinfo("成功", f"图片已保存: {filepath}")
                # 或者改为状态栏提示，避免频繁弹窗
                # self.update_status(f" 图片已保存: {os.path.basename(filepath)}")
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
        """Windows平台复制图片（优先使用pywin32实现多格式支持）"""
        if self.pywin32_available and self._win32clipboard and self._win32con:
            try:
                output_bmp = io.BytesIO()
                img.convert("RGB").save(output_bmp, "BMP")
                bmp_data = output_bmp.getvalue()[14:]
                output_bmp.close()
                
                output_png = io.BytesIO()
                img.save(output_png, "PNG")
                png_data = output_png.getvalue()
                output_png.close()
                
                self._win32clipboard.OpenClipboard()
                self._win32clipboard.EmptyClipboard()
                
                self._win32clipboard.SetClipboardData(self._win32con.CF_DIB, bmp_data)
                
                self._win32clipboard.SetClipboardData(self._win32clipboard.RegisterClipboardFormat("PNG"), png_data)
                
                self._win32clipboard.CloseClipboard()
                return
            except Exception as e:
                print(f"pywin32复制失败，回退到ctypes方案: {e}")
        
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        
        user32.OpenClipboard(0)
        user32.EmptyClipboard()
        
        output = io.BytesIO()
        img.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]
        output.close()
        
        hMem = kernel32.GlobalAlloc(0x0002, len(data))
        locked_mem = kernel32.GlobalLock(hMem)
        ctypes.memmove(locked_mem, data, len(data))
        kernel32.GlobalUnlock(hMem)
        
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
            
            self.update_status(f" 响应数据已保存")
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
        detail_window.resizable(True, True)
        # 绑定Esc关闭弹窗
        detail_window.bind("<Escape>", lambda e: detail_window.destroy())
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
    def _save_log(self, data, log_type, url=None, actual_image_size=None, gpt_endpoint_type=None):
        """保存日志到文件"""
        try:
            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)
            
            # 获取当前模型信息
            model = self.model_var.get()
            config = self.MODEL_CONFIGS.get(model, {})
            backend = config.get("backend", "nanobanana")
            
            # 根据后端类型和模型名构建文件名前缀
            if backend == "gpt_image_vip":
                file_prefix = "GPT-image-2"
            else:
                parts = model.split("-")
                if len(parts) >= 2:
                    version_str = parts[1]
                    if "." not in version_str:
                        version_str = version_str + ".0"
                    file_prefix = "Gemini-" + version_str
                else:
                    file_prefix = "Gemini-unknown"
            
            # 生成日志文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(log_dir, f"{file_prefix}_{timestamp}_{log_type}.log")
            
            # 修复：隐藏 API Key，不保存明文
            hidden_api_key = "SK_HIDDEN_API_KEY"
            
            # III.A.3: 只有实际发送了 imageSize 才记录，否则为 null
            # actual_image_size 由调用方传入，None 表示未发送
            image_size_to_log = actual_image_size
            
            # 构建日志数据
            log_data = {
                "timestamp": timestamp,
                "model": model,
                "backend": backend,
                "prompt": self.prompt_text.get("1.0", tk.END).strip(),
                "aspect_ratio": self.aspect_ratio.get(),
                "image_size": image_size_to_log,
                "network_timeout": self.network_timeout.get(),
                "reference_images": len(self.reference_images),
                "api_key": hidden_api_key,
                "url": url,
                "data": data
            }
            
            # III.A.5: GPT 模式下补充 endpoint 类型
            if gpt_endpoint_type:
                log_data["gpt_endpoint_type"] = gpt_endpoint_type
            
            # 保存日志文件
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False, default=str)
        # 捕获异常但不影响主流程
        except Exception as e:
            print(f"日志记录失败: {e}")
    # 验证超时输入
    def _validate_timeout(self, value):
        """验证超时输入：只允许非负整数（空字符串临时允许输入，但会回退到默认值）"""
        if value == "":
            return True
        if not value.isdigit():
            return False
        return int(value) >= 0
    # 日志开关切换处理
    def on_log_toggle(self):
        """日志开关切换时的处理"""
        if self.log_to_file.get():
            os.makedirs("logs", exist_ok=True)
            try:
                target_script = os.path.join("logs", "export_images_from_log（从Log中提取图片）.py")
                with open(target_script, "w", encoding="utf-8") as f:
                    f.write(self.EXPORT_SCRIPT_CODE)
                self.update_status("已启用日志记录（敏感信息已脱敏）- 已生成图片提取工具")
            except Exception as e:
                self.update_status(f"已启用日志记录，但生成提取工具失败: {str(e)}")
        else:
            self.update_status("已禁用日志记录")

    # 模型切换处理
    def on_model_change(self, event=None):
        """模型切换时更新分辨率选项、参考图片上限和界面状态"""
        model = self.model_var.get().strip()
        config = self.MODEL_CONFIGS.get(model, {})
        backend = config.get("backend", "nanobanana")
        # 更新参考图片上限
        self.current_max_ref_images = config.get("max_ref_images", 14)
        # 更新参考图片区域标题和计数显示
        self.ref_frame.config(text=f"参考图片 (可选, 最多{self.current_max_ref_images}张)")
        self.update_ref_count_label()
        # 如果当前已选图片超过新上限，提示用户
        if len(self.reference_images) > self.current_max_ref_images:
            excess = len(self.reference_images) - self.current_max_ref_images
            messagebox.showwarning(
                "参考图片超限",
                f"当前模型最多支持 {self.current_max_ref_images} 张参考图片，\n"
                f"将自动移除多余的 {excess} 张图片（从最后一张开始）。"
            )
            self.reference_images = self.reference_images[:self.current_max_ref_images]
            self.update_reference_preview()
        # 根据模型配置更新分辨率选项
        if config.get("stable"):  # gemini-2.5-flash-image
            self.resolution_combo.config(values=["1K"], state="readonly")
            self.resolution.set("1K")
        else:
            self.resolution_combo.config(values=["1K", "2K", "4K"], state="readonly")
            self.resolution.set("4K")  # 默认4K
    # 缩放比例变化处理
    def on_zoom_change(self, event=None):
        self._apply_zoom()
        # 同步更新模型下拉框宽度以确保始终适配内容
        self._update_model_combo_width()

    def _update_model_combo_width(self):
        """根据当前模型选项列表更新下拉框宽度"""
        if hasattr(self, 'model_combo'):
            values = self.model_combo.cget("values")
            if values:
                max_len = max(len(str(v)) for v in values)
                new_width = max_len + 1
                self.model_combo.config(width=new_width)
                # 同步更新API密钥输入框宽度以保持对齐
                if hasattr(self, 'api_key_entry'):
                    self.api_key_entry.config(width=new_width)
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
            'confirm_before_generate': self.confirm_before_generate.get(),
            'reference_images': self.reference_images.copy(),
            'current_image_data': self.current_image_data,
            'current_image_mime_type': getattr(self, 'current_image_mime_type', 'image/png'),
            'current_image_model': getattr(self, 'current_image_model', None),
            'last_raw_response': self.last_raw_response,
            'response_text': self.response_text.get("1.0", tk.END).strip(),
            'status_text': self.status_text.get("1.0", tk.END).strip()
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
        
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete("1.0", tk.END)
        self.status_text.insert("1.0", state.get('status_text', ''))
        self.status_text.config(state=tk.DISABLED)
        
        self.confirm_before_generate.set(state.get('confirm_before_generate', True))
        self.reference_images = state['reference_images']
        self.update_reference_preview()
        
        self.current_image_data = state['current_image_data']
        self.current_image_mime_type = state.get('current_image_mime_type', 'image/png')
        self.current_image_model = state.get('current_image_model', None)
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
        zoom_percent = int(zoom_str)
        min_left_panel_width = int(round(self.LEFT_WIDTH_SLOPE * zoom_percent + self.LEFT_WIDTH_INTERCEPT))
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
            
            try:
                self.status_text.config(font=(family, int(new_font_size * 0.75)))
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

    # ==================== 关闭拦截功能 ====================
    def _intercept_close(self):
        """拦截窗口关闭请求"""
        self.root.protocol("WM_DELETE_WINDOW", self._on_close_request)

    def _on_close_request(self):
        """统一关闭入口，根据状态触发不同弹窗"""
        if self.fallback_locked:
            self._show_fallback_dialog()
            return

        has_prompt = len(self.prompt_text.get("1.0", "end-1c").strip()) > 0
        has_images = len(self.reference_images) > 0
        is_generating = self.generate_thread is not None and self.generate_thread.is_alive()

        if is_generating:
            # 高优先级：生成中，清空按钮弹窗计数
            self.button_fail_count = 0
            self._show_slider_confirm_dialog()
        elif has_prompt or has_images:
            # 低优先级：有内容未清空，清空滑块弹窗计数
            self.slider_fail_count = 0
            self._show_close_confirm_dialog()
        else:
            # 无风险状态，直接退出
            self.root.destroy()

    def _show_close_confirm_dialog(self):
        """四按钮随机确认弹窗（1确定3取消）"""
        dialog = tk.Toplevel(self.root)
        dialog.title("确认关闭")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        dialog.bind("<Escape>", lambda e: dialog.destroy())

        tk.Label(dialog, text="是否确认关闭？", font=("TkDefaultFont", 11, "bold")).pack(pady=(15, 10))

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10, padx=20)

        buttons = [("确定", True), ("取消", False), ("取消", False), ("取消", False)]
        random.shuffle(buttons)

        def on_click(is_confirm):
            dialog.destroy()
            if is_confirm:
                self.root.destroy()
            else:
                self.button_fail_count += 1
                if self.button_fail_count >= 3:
                    self.fallback_locked = True

        for i, (text, is_confirm) in enumerate(buttons):
            row, col = divmod(i, 2)
            btn = ttk.Button(btn_frame, text=text, width=12,
                           command=lambda c=is_confirm: on_click(c))
            btn.grid(row=row, column=col, padx=5, pady=5)

        ttk.Button(dialog, text="返回", command=dialog.destroy, width=20).pack(pady=(5, 15))
        self._center_dialog(dialog)

    def _show_slider_confirm_dialog(self):
        """滑块验证弹窗"""
        dialog = tk.Toplevel(self.root)
        dialog.title("验证退出")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        dialog.bind("<Escape>", lambda e: dialog.destroy())

        target = random.randint(1, 7)

        tk.Label(dialog, text=f"滑动到 {target}，再按下确定。",
                font=("TkDefaultFont", 11, "bold")).pack(pady=(15, 5), padx=20)

        tk.Label(dialog, text="注意：一旦开始生成就不能取消，强行关闭脚本仍然会扣费！",
                foreground="red", wraplength=380).pack(pady=5, padx=20)

        slider_var = tk.IntVar(value=0)

        value_label = tk.Label(dialog, text="当前值：0", font=("TkDefaultFont", 10))
        value_label.pack(pady=5)

        slider = ttk.Scale(dialog, from_=0, to=7, orient=tk.HORIZONTAL,
                          variable=slider_var, length=350)
        slider.pack(padx=20, pady=5, fill=tk.X)

        def on_slide(*args):
            value_label.config(text=f"当前值：{slider_var.get()}")
        slider_var.trace_add("write", on_slide)

        def on_confirm():
            if slider_var.get() == target:
                dialog.destroy()
                self.root.destroy()
            else:
                self.slider_fail_count += 1
                dialog.destroy()
                if self.slider_fail_count >= 3:
                    self.fallback_locked = True

        ttk.Button(dialog, text="确定", command=on_confirm, width=20).pack(pady=10)
        ttk.Button(dialog, text="返回", command=dialog.destroy, width=20).pack(pady=(0, 15))
        self._center_dialog(dialog)

    def _show_fallback_dialog(self):
        """保底弹窗（触发后永久锁定）"""
        dialog = tk.Toplevel(self.root)
        dialog.title("退出确认")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)

        tk.Label(dialog, text="检测到多次退出失败，现在可以按下“确定”按钮退出。",
                font=("TkDefaultFont", 11), wraplength=380).pack(pady=(20, 15), padx=20)

        ttk.Button(dialog, text="确定", command=lambda: (dialog.destroy(), self.root.destroy()),
                  width=20).pack(pady=(0, 20))
        self._center_dialog(dialog)

    def _center_dialog(self, dialog):
        """将弹窗居中于主窗口"""
        dialog.update_idletasks()
        x = self.root.winfo_rootx() + self.root.winfo_width() // 2 - dialog.winfo_width() // 2
        y = self.root.winfo_rooty() + self.root.winfo_height() // 2 - dialog.winfo_height() // 2
        dialog.geometry(f"+{x}+{y}")

    def _insert_data_warning(self):
        """**改进：防止用户编辑只读文本框**"""
        return "break"  # 阻止事件继续传递，防止文本框获得焦点
# ==================== 主程序入口 ====================
def main():
    # ========== 关键修复：切换到脚本所在目录 ==========
    # 获取脚本文件的绝对路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"脚本所在目录: {script_dir}")
    
    # 切换到脚本所在目录
    os.chdir(script_dir)
    print(f"工作目录已切换到: {os.getcwd()}")
    # ===================================================

    # 设置独立 AppUserModelID，每次启动生成唯一ID，防止任务栏合并窗口（仅 Windows）
    if platform.system() == "Windows":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                f"laozhang.nanobanana.{os.getpid()}"
            )
        except Exception:
            pass
    
    if TKINTERDND2_AVAILABLE:
        root = tkinterdnd2.TkinterDnD.Tk()
    else:
        root = tk.Tk()
    root.minsize(1000, 800)
    app = GeminiImageGenerator(root)
    
    # 输出缺失的可选依赖到状态栏
    if _missing_optional_deps:
        missing_names = ", ".join(_missing_optional_deps)
        app.update_status(f"提示: 以下可选依赖未安装，部分功能可能不可用: {missing_names}")
    
    root.mainloop()
# ==================== 运行主程序 ====================
if __name__ == "__main__":
    main()
# ================== 代码结束 ====================