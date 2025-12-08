import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font
import os
from datetime import datetime
import requests
import base64
import threading
import json
from PIL import Image, ImageTk
import io

class GeminiImageGenerator:
    # ==================== 集中定义的常量 ====================
    MAX_REF_IMAGES = 14
    MAX_PROMPT_CHARS = 2000
    MAX_IMAGE_SIZE_MB = 10
    
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
    
    def __init__(self, root):
        self.root = root
        
        # 高DPI支持
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            pass
        
        self.root.title("Gemini Flash 图像生成器 - Nano Banana 系列")
        self.root.geometry("1200x850")
        
        # 配置变量
        self.api_key = tk.StringVar()
        self.model_var = tk.StringVar(value="gemini-3-pro-image-preview")
        self.aspect_ratio = tk.StringVar(value="1:1")
        self.resolution = tk.StringVar(value="4K")
        self.log_to_file = tk.BooleanVar(value=False)
        self.network_timeout = tk.StringVar(value="1200")
        self.zoom_var = tk.StringVar(value="100%")
        
        # 数据存储
        self.reference_images = []  # 存储 (文件路径, base64数据, mime_type, 原始PIL图像, 缩略图)
        self.current_image_data = None
        self.current_image_preview = None
        self.last_raw_response = None
        
        # UI状态存储（用于缩放切换）
        self._ui_state_cache = {}
        
        # 线程控制
        self.generate_thread = None
        
        self.setup_ui()
        self.minimize_console()
        
    def setup_ui(self):
        """构建左右分区的用户界面"""
        main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=4, bg="#ccc")
        main_paned.pack(fill=tk.BOTH, expand=True)
        
        left_panel = ttk.Frame(main_paned)
        main_paned.add(left_panel, width=600)
        
        right_panel = ttk.Frame(main_paned)
        main_paned.add(right_panel, width=500)
        
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
        
        api_frame = ttk.LabelFrame(left_panel, text="API配置", padding=10)
        api_frame.pack(fill=tk.X, pady=5, padx=5)
        
        ttk.Label(api_frame, text="API密钥:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        api_entry = ttk.Entry(api_frame, textvariable=self.api_key, show="*", width=40)
        api_entry.grid(row=0, column=1, sticky=tk.W)
        self.api_key_entry = api_entry
        def toggle_key_visibility():
            if api_entry['show'] == '*':
                api_entry.config(show='')
                toggle_btn.config(text='隐藏')
            else:
                api_entry.config(show='*')
                toggle_btn.config(text='显示')
        
        toggle_btn = ttk.Button(api_frame, text='显示', command=toggle_key_visibility, width=4)
        toggle_btn.grid(row=0, column=2, padx=(5, 0))
        
        ttk.Label(api_frame, text="模型:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0), padx=(0, 10))
        model_combo = ttk.Combobox(api_frame, textvariable=self.model_var, 
                                   values=list(self.MODEL_CONFIGS.keys()),
                                   state="readonly", width=30)
        model_combo.grid(row=1, column=1, sticky=tk.W, pady=(10, 0), padx=(0, 10))
        model_combo.bind("<<ComboboxSelected>>", self.on_model_change)
        
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
        
        self.prompt_text = tk.Text(prompt_frame, height=4, font=("TkDefaultFont", 10))
        self.prompt_text.pack(fill=tk.BOTH, expand=True)
        
        def update_char_count(event=None):
            count = len(self.prompt_text.get("1.0", tk.END)) - 1
            char_label.config(text=f"{count}/{self.MAX_PROMPT_CHARS}")
            char_label.config(foreground="red" if count > self.MAX_PROMPT_CHARS else "green")
        
        char_label = ttk.Label(prompt_frame, text=f"0/{self.MAX_PROMPT_CHARS}", font=("TkDefaultFont", 9))
        char_label.pack(anchor=tk.E)
        self.prompt_text.bind('<KeyRelease>', update_char_count)
        
        # 参考图片区域
        ref_frame = ttk.LabelFrame(left_panel, text=f"参考图片 (可选, 最多{self.MAX_REF_IMAGES}张)", padding=10)
        ref_frame.pack(fill=tk.X, pady=5, padx=5)
        
        ref_btn_frame = ttk.Frame(ref_frame)
        ref_btn_frame.pack(fill=tk.X)
        
        ttk.Button(ref_btn_frame, text="添加图片", command=self.add_images, width=12).pack(side=tk.LEFT)
        ttk.Button(ref_btn_frame, text="清空全部", command=self.clear_images, width=12).pack(side=tk.LEFT, padx=10)
        
        self.ref_count_label = ttk.Label(ref_btn_frame, text=f"已选择: 0/{self.MAX_REF_IMAGES}张", font=("TkDefaultFont", 9, "bold"))
        self.ref_count_label.pack(side=tk.LEFT, padx=20)
        
        ref_canvas_container = ttk.Frame(ref_frame)
        ref_canvas_container.pack(fill=tk.X, pady=5, expand=True)
        
        self.ref_canvas = tk.Canvas(ref_canvas_container, height=100, bg="#f0f0f0", relief=tk.SUNKEN)
        self.ref_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ref_scrollbar = ttk.Scrollbar(ref_canvas_container, orient=tk.HORIZONTAL, command=self.ref_canvas.xview)
        ref_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.ref_canvas.config(xscrollcommand=ref_scrollbar.set)
        
        # 参数设置区域
        param_frame = ttk.LabelFrame(left_panel, text="生成参数", padding=10)
        param_frame.pack(fill=tk.X, pady=5, padx=5)
        
        param_grid = ttk.Frame(param_frame)
        param_grid.pack(fill=tk.X)
        
        ttk.Label(param_grid, text="纵横比:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        aspect_combo = ttk.Combobox(param_grid, textvariable=self.aspect_ratio,
                                   values=["21:9", "16:9", "4:3", "3:2", "1:1", 
                                           "9:16", "3:4", "2:3", "5:4", "4:5"],
                                   state="readonly", width=10)
        aspect_combo.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(param_grid, text="分辨率:").grid(row=0, column=2, sticky=tk.W, padx=(30, 10))
        self.resolution_combo = ttk.Combobox(param_grid, textvariable=self.resolution,
                                            values=["1K"], state="readonly", width=10)
        self.resolution_combo.grid(row=0, column=3, sticky=tk.W)
        
        self.generate_btn = ttk.Button(param_grid, text="生成图片", 
                                      command=self.generate_image, width=25)
        self.generate_btn.grid(row=0, column=4, padx=(30, 0))
        
        status_frame = ttk.Frame(left_panel)
        status_frame.pack(fill=tk.X, pady=5, padx=5)
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(status_frame, textvariable=self.status_var, relief=tk.SUNKEN, 
                 font=("TkDefaultFont", 9)).pack(fill=tk.X)
        
        # ===== 右侧面板内容 =====
        output_frame = ttk.LabelFrame(right_panel, text="输出预览", padding=10)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.output_notebook = ttk.Notebook(output_frame)
        self.output_notebook.pack(fill=tk.BOTH, expand=True)
        
        img_tab = ttk.Frame(self.output_notebook)
        self.output_notebook.add(img_tab, text="生成的图片")
        
        self.img_preview = ttk.Label(img_tab, text="生成的图片将在此显示", 
                                    relief=tk.SUNKEN, anchor=tk.CENTER, background="white")
        self.img_preview.pack(fill=tk.BOTH, expand=True)
        
        btn_frame = ttk.Frame(img_tab)
        btn_frame.pack(pady=10)
        self.save_btn = ttk.Button(btn_frame, text="保存图片", 
                                  command=self.save_image, state=tk.DISABLED, width=18)
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="复制图片", 
                  command=self.copy_to_clipboard, width=18).pack(side=tk.LEFT, padx=5)
        
        response_tab = ttk.Frame(self.output_notebook)
        self.output_notebook.add(response_tab, text="原始响应")
        
        response_container = ttk.Frame(response_tab)
        response_container.pack(fill=tk.BOTH, expand=True)
        
        self.response_text = tk.Text(response_container, wrap=tk.WORD, font=("Consolas", 9), height=12)
        self.response_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scroll_y = ttk.Scrollbar(response_container, orient=tk.VERTICAL, command=self.response_text.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        scroll_x = ttk.Scrollbar(response_tab, orient=tk.HORIZONTAL, command=self.response_text.xview)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.response_text.config(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        
        resp_btn_frame = ttk.Frame(response_tab)
        resp_btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        ttk.Button(resp_btn_frame, text="保存原始JSON", 
                  command=self.save_raw_response, width=18).pack(side=tk.LEFT)
        
        ttk.Button(resp_btn_frame, text="显示完整数据", 
                  command=self.show_full_data, width=18).pack(side=tk.LEFT, padx=10)
        
        self.response_text.bind('<Button-1>', lambda e: self._insert_data_warning())

    # ==================== 核心功能实现 ====================

    def get_api_url(self):
        """获取当前模型的 API 端点"""
        model_id = self.model_var.get()
        return f"https://api.laozhang.ai/v1beta/models/{model_id}:generateContent"

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

    def add_images(self):
        """添加多张参考图片"""
        filepaths = filedialog.askopenfilenames(
            title="选择参考图片",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.webp"), ("所有文件", "*.*")]
        )
        
        if not filepaths:
            return
        
        available_slots = self.MAX_REF_IMAGES - len(self.reference_images)
        if len(filepaths) > available_slots:
            messagebox.showwarning("警告", f"最多只能添加{self.MAX_REF_IMAGES}张参考图片，当前已选择{len(self.reference_images)}张")
            filepaths = filepaths[:available_slots]
        
        for filepath in filepaths:
            try:
                # 验证文件大小
                file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
                if file_size_mb > self.MAX_IMAGE_SIZE_MB:
                    messagebox.showwarning("警告", f"图片过大: {filepath}\n请使用小于{self.MAX_IMAGE_SIZE_MB}MB的图片")
                    continue
                
                # 读取并编码图片
                with open(filepath, "rb") as f:
                    image_b64 = base64.b64encode(f.read()).decode("utf-8")
                
                # 读取原始图片并生成缩略图
                original_img = Image.open(filepath)
                thumb_img = original_img.copy()
                thumb_img.thumbnail((80, 80), Image.Resampling.LANCZOS)
                
                mime_type = self.get_mime_type(filepath)
                
                # 存储：文件路径, base64, mime类型, 原始图片对象, 缩略图
                self.reference_images.append((filepath, image_b64, mime_type, original_img, thumb_img))
                
            except Exception as e:
                messagebox.showerror("错误", f"加载图片失败: {filepath}\n{str(e)}")
        
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
        
        # 动态计算缩略图尺寸
        thumb_size = int(80 * scale)
        if thumb_size < 40:
            thumb_size = 40
        
        for idx, (filepath, _, _, original_img, _) in enumerate(self.reference_images):
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
            self.ref_canvas.image_dict = getattr(self.ref_canvas, 'image_dict', {})
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

    def remove_reference(self, index):
        """删除指定参考图片"""
        if 0 <= index < len(self.reference_images):
            del self.reference_images[index]
            self.update_reference_preview()
            self.status_var.set(f"已删除第 {index+1} 张参考图片")

    def clear_images(self):
        """清空所有参考图片"""
        if not self.reference_images:
            return
        
        if messagebox.askyesno("确认", f"确定要清空 {len(self.reference_images)} 张参考图片吗？"):
            self.reference_images.clear()
            self.ref_canvas.delete("all")
            self.ref_count_label.config(text=f"已选择: 0/{self.MAX_REF_IMAGES}张")
            self.status_var.set("已清空所有参考图片")

    def generate_image(self):
        """开始生成图片"""
        # 验证输入
        if not self.api_key.get().strip():
            messagebox.showerror("错误", "请先填写 API 密钥")
            return
        
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showerror("错误", "提示词不能为空")
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

    def _generate_thread(self, api_key, prompt):
        """后台线程执行API调用"""
        try:
            # 构建请求数据
            parts = [{"text": prompt}]
            
            # 添加参考图片
            for filepath, image_b64, mime_type, _ in self.reference_images:
                parts.append({
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": image_b64
                    }
                })
            
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
            
        except Exception as e:
            self.root.after(0, self._handle_error, str(e))

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
                
                if "parts" not in candidate["content"] or not candidate["content"]["parts"]:
                    raise ValueError("响应中未找到图片数据")
                
                image_data = candidate["content"]["parts"][0]["inlineData"]["data"]
                self.current_image_data = image_data
                
                # 显示图片
                self._show_image()
                
                # **改进：使用优化的数据显示**
                display_data = self._optimize_display_data(result)
                self.response_text.delete("1.0", tk.END)
                self.response_text.insert("1.0", json.dumps(display_data, indent=2, ensure_ascii=False))
                
                self.save_btn.config(state=tk.NORMAL)
                self.status_var.set("✅ 生成成功")
                
                # 记录日志
                if self.log_to_file.get():
                    self._save_log(result, "success")
                
            except (KeyError, IndexError, ValueError) as e:
                messagebox.showerror("响应错误", f"处理API响应失败:\n{str(e)}")
                self.response_text.delete("1.0", tk.END)
                self.response_text.insert("1.0", json.dumps(result, indent=2, ensure_ascii=False))
                self.status_var.set(f"生成失败: {str(e)[:50]}...")
                
        finally:
            self.generate_btn.config(state=tk.NORMAL, text="生成图片")

    def _handle_error(self, error_msg):
        """处理异常错误"""
        messagebox.showerror("错误", f"生成过程中发生异常:\n{error_msg}")
        self.status_var.set("生成失败: 异常错误")
        self.generate_btn.config(state=tk.NORMAL, text="生成图片")
        
        # **改进：记录错误日志**
        if self.log_to_file.get():
            self._save_log({"error": error_msg, "exception": True}, "error")

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

    def _is_likely_base64(self, s):
        """检测字符串是否可能是base64编码"""
        return len(s) > 100 and len(s) % 4 == 0 and all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=' for c in s[:100])

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
            
        except Exception as e:
            messagebox.showerror("显示错误", f"无法显示生成的图片:\n{str(e)}")
            self.img_preview.config(text="显示失败", image="")

    def _resize_image(self, event=None):
        """根据预览区域大小调整图片"""
        if not hasattr(self, 'original_image') or not self.original_image:
            return
        
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
        
        filepath = filedialog.asksaveasfilename(
            title="保存图片",
            defaultextension=".png",
            filetypes=[("PNG图片", "*.png"), ("所有文件", "*.*")],
            initialfile=default_filename
        )
        
        if not filepath:
            return
        
        try:
            image_bytes = base64.b64decode(self.current_image_data)
            with open(filepath, "wb") as f:
                f.write(image_bytes)
            
            self.status_var.set(f" 图片已保存: {os.path.basename(filepath)}")
            
            # 记录日志
            if self.log_to_file.get():
                self._save_log({"saved_file": filepath}, "save")
                
        except Exception as e:
            messagebox.showerror("保存错误", f"无法保存图片:\n{str(e)}")

    def copy_to_clipboard(self):
        """**改进：真正复制图片到剪贴板（支持Windows/macOS）**"""
        if not self.current_image_data:
            messagebox.showwarning("警告", "没有可复制的图片")
            return
        
        try:
            # 解码图片
            image_bytes = base64.b64decode(self.current_image_data)
            img = Image.open(io.BytesIO(image_bytes))
            
            # **改进：尝试使用PIL的剪贴板功能**
            try:
                from PIL import ImageGrab
                if hasattr(ImageGrab, 'send_image'):  # PIL 9.0+ 支持直接发送
                    ImageGrab.send_image(img)
                    messagebox.showinfo("成功", "图片已复制到剪贴板！")
                    return
            except Exception as e:
                print(f"PIL剪贴板功能失败: {e}")
            
            # **回退方案：复制完整base64数据**
            import pyperclip
            pyperclip.copy(self.current_image_data)
            messagebox.showinfo("提示", "图片Base64数据已完整复制到剪贴板")
            
        except ImportError:
            messagebox.showerror("错误", "需要安装 pyperclip 库: pip install pyperclip")
        except Exception as e:
            messagebox.showerror("复制错误", f"复制失败:\n{str(e)}")

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
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self.last_raw_response, f, indent=2, ensure_ascii=False)
            
            self.status_var.set(f" 响应数据已保存")
        except Exception as e:
            messagebox.showerror("保存错误", f"无法保存响应数据:\n{str(e)}")

    def show_full_data(self):
        """在新窗口显示完整数据"""
        if not self.last_raw_response:
            messagebox.showwarning("警告", "没有可显示的数据")
            return
        
        # 创建新窗口
        detail_window = tk.Toplevel(self.root)
        detail_window.title("完整响应数据")
        detail_window.geometry("800x600")
        
        text_widget = tk.Text(detail_window, wrap=tk.NONE, font=("Consolas", 9))
        text_widget.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scroll_y = ttk.Scrollbar(detail_window, orient=tk.VERTICAL, command=text_widget.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        scroll_x = ttk.Scrollbar(detail_window, orient=tk.HORIZONTAL, command=text_widget.xview)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        text_widget.config(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        
        # 显示完整数据
        text_widget.insert("1.0", json.dumps(self.last_raw_response, indent=2, ensure_ascii=False))
        text_widget.config(state=tk.DISABLED)

    def _save_log(self, data, log_type):
        """保存日志到文件"""
        try:
            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(log_dir, f"gemini_{timestamp}_{log_type}.log")
            
            log_data = {
                "timestamp": timestamp,
                "model": self.model_var.get(),
                "prompt": self.prompt_text.get("1.0", tk.END).strip(),
                "aspect_ratio": self.aspect_ratio.get(),
                "resolution": self.resolution.get(),
                "network_timeout": self.network_timeout.get(),
                "reference_images": len(self.reference_images),
                "data": data
            }
            
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False, default=str)
            
        except Exception as e:
            print(f"日志记录失败: {e}")

    def _validate_timeout(self, value):
        """验证超时输入：只允许自然数"""
        if value == "" or value == "0":
            return True
        return value.isdigit() and int(value) >= 0

    def on_log_toggle(self):
        """日志开关切换时的处理"""
        if self.log_to_file.get():
            self.status_var.set(" 已启用日志记录")
        else:
            self.status_var.set(" 已禁用日志记录")

    def on_model_change(self, event=None):
        """模型切换时更新分辨率选项"""
        model = self.model_var.get().strip()
        config = self.MODEL_CONFIGS.get(model, {})
        
        if config.get("stable"):  # gemini-2.5-flash-image
            self.resolution_combo.config(values=["1K"], state="readonly")
            self.resolution.set("1K")
        else:  # gemini-3-pro-image-preview
            self.resolution_combo.config(values=["1K", "2K", "4K"], state="readonly")
            self.resolution.set("2K")  # 默认2K

    def on_zoom_change(self, event=None):
        """界面缩放切换事件"""
        self._save_ui_state()
        self._apply_zoom()
        self._restore_ui_state()

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

    def _restore_ui_state(self):
        """恢复所有UI状态"""
        state = self._ui_state_cache
        if not state:
            return
        
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

    def _apply_zoom(self):
        """应用缩放设置到所有UI元素"""
        zoom_str = self.zoom_var.get().rstrip('%')
        try:
            scale = int(zoom_str) / 100.0
        except:
            scale = 1.0
        
        # 更新主窗口大小
        base_width, base_height = 1200, 850
        new_width = int(base_width * scale)
        new_height = int(base_height * scale)
        self.root.geometry(f"{new_width}x{new_height}")
        
        # 更新全局字体大小
        try:
            default_font = tk.font.nametofont("TkDefaultFont")
            base_font_size = 10
            new_font_size = int(base_font_size * scale)
            if new_font_size < 8:
                new_font_size = 8
            default_font.configure(size=new_font_size)
            
            # 更新样式
            style = ttk.Style()
            style.configure(".", font=("TkDefaultFont", new_font_size))
            
            # 特殊控件字体调整
            self.model_hint.config(font=("TkDefaultFont", new_font_size - 1))
            self.char_label.config(font=("TkDefaultFont", new_font_size - 1))
        except:
            pass

    def minimize_console(self):
        """自动最小化终端窗口（仅Windows）"""
        try:
            import platform
            system = platform.system()
            
            if system == "Windows":
                import ctypes
                hwnd = ctypes.windll.kernel32.GetConsoleWindow()
                if hwnd:
                    ctypes.windll.user32.ShowWindow(hwnd, 6)
            elif system in ["Linux", "Darwin"]:
                # macOS和Linux系统暂不支持自动最小化
                pass
            else:
                # 未知系统不做处理
                pass
        except Exception:
            # 任何异常都不影响主程序
            pass
    
    # ==================== 新增方法 ====================
    def _insert_data_warning(self):
        """**改进：防止用户编辑只读文本框**"""
        return "break"  # 阻止事件继续传递，防止文本框获得焦点

def main():
    root = tk.Tk()
    root.minsize(1000, 800)
    app = GeminiImageGenerator(root)
    root.mainloop()

if __name__ == "__main__":
    main()