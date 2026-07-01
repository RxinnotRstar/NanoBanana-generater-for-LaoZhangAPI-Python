import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import time
import threading
import traceback
from pathlib import Path

# ============ 缩略图 ============
try:
    from PIL import Image, ImageTk, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# 可用 PIL 直接打开的图片后缀
_PIL_IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tiff', '.tif', '.ico'}

def _pil_thumbnail(path, size):
    """用 PIL 直接打开图片文件并缩略。返回 RGB 模式的 PIL Image，失败返回 None。"""
    if not HAS_PIL:
        return None
    try:
        img = Image.open(path)
        img.thumbnail(size, Image.LANCZOS)
        if img.mode in ('RGBA', 'LA'):
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[-1])
            img = bg
        elif img.mode == 'P':
            img = img.convert('RGBA')
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[-1])
            img = bg
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        return img
    except Exception:
        print(f"[缩略图] PIL 加载失败: {path}")
        traceback.print_exc()
        return None

def get_system_thumbnail(path, size=(64, 64)):
    if sys.platform != 'win32':
        return None
    try:
        import pythoncom
        import win32com.client
        pythoncom.CoInitialize()
        try:
            shell = win32com.client.Dispatch("Shell.Application")
            folder = shell.Namespace(str(Path(path).parent))
            if folder is None:
                return None
            item = folder.ParseName(Path(path).name)
            if item is None:
                return None
            img = item.GetThumbnail(size[0], size[1])
            if img:
                tmp = os.path.join(os.environ.get('TEMP', '.'),
                                   f'_tkthumb_{os.getpid()}_{threading.get_ident()}_{id(img)}.png')
                img.Save(tmp)
                try:
                    pil_img = Image.open(tmp).resize(size, Image.LANCZOS)
                    return pil_img
                finally:
                    try:
                        os.remove(tmp)
                    except OSError:
                        pass
        finally:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass
    except Exception:
        print(f"[缩略图] 系统缩略图获取失败: {path}")
        traceback.print_exc()
    return None

def generate_fallback_thumbnail(path, size=(64, 64)):
    if not HAS_PIL:
        return None
    img = Image.new('RGB', size, (240, 240, 240))
    draw = ImageDraw.Draw(img)
    if os.path.isdir(path):
        draw.rectangle([8, 12, size[0]-8, size[1]-8], fill=(255, 220, 100), outline=(200, 180, 60), width=2)
        draw.rectangle([8, 8, size[0]-20, 20], fill=(255, 220, 100), outline=(200, 180, 60), width=2)
    else:
        ext = Path(path).suffix.lower()
        color_map = {
            '.png': (100, 200, 100), '.jpg': (100, 200, 100), '.jpeg': (100, 200, 100),
            '.gif': (100, 200, 100), '.bmp': (100, 200, 100),
            '.txt': (200, 200, 200), '.md': (200, 200, 200),
            '.py': (100, 160, 255), '.js': (255, 220, 100), '.html': (255, 160, 100),
            '.exe': (200, 100, 100), '.zip': (180, 140, 255), '.rar': (180, 140, 255),
        }
        color = color_map.get(ext, (180, 180, 180))
        draw.rectangle([8, 8, size[0]-8, size[1]-8], fill=color, outline=(120, 120, 120), width=2)
        draw.polygon([(size[0]-20, 8), (size[0]-8, 20), (size[0]-20, 20)], fill=(255, 255, 255), outline=(120, 120, 120))
        if ext:
            try:
                font = ImageFont.truetype("arial.ttf", 10)
            except:
                font = ImageFont.load_default()
            draw.text((12, size[1]-18), ext[1:4].upper(), fill=(80, 80, 80), font=font)
    return img

def get_thumbnail(path, size=(64, 64)):
    """获取缩略图，返回 PIL Image 或 None。
    优先用 PIL 直接打开图片文件，其次尝试系统缩略图，最后用生成图标。"""
    if not HAS_PIL:
        return None
    ext = Path(path).suffix.lower()
    if ext in _PIL_IMAGE_EXTS:
        result = _pil_thumbnail(path, size)
        if result is not None:
            return result
    thumb = get_system_thumbnail(path, size)
    if thumb is not None:
        return thumb
    return generate_fallback_thumbnail(path, size)

# ============ 文件选择器弹窗 ============
class FileBrowserDialog(tk.Toplevel):
    _last_view_mode = "details"

    def __init__(self, parent, initial_path=None, multi_select=False,
                 last_path=None, on_select=None, on_cancel=None,
                 zoom=1.0, filetypes=None):
        super().__init__(parent)
        self.zoom = max(0.75, min(5.0, zoom))
        self.filetypes = filetypes  # None=全部, 如 ['.jpg','.png']
        self.title("打开文件")
        geo_w = self._s(900)
        geo_h = self._s(600)
        self.geometry(f"{geo_w}x{geo_h}")
        self.transient(parent)
        self.grab_set()

        self.multi_select = multi_select
        self.on_select = on_select
        self.on_cancel = on_cancel
        self.last_opened_path = last_path

        if initial_path:
            self.current_path = Path(initial_path).resolve()
        elif last_path and os.path.exists(last_path):
            self.current_path = Path(last_path).resolve()
        else:
            self.current_path = Path(sys.argv[0]).parent.resolve()

        self.selected_items = set()
        self.view_mode = FileBrowserDialog._last_view_mode
        self.thumbnail_cache = {}
        self.sort_key = "name"
        self.sort_reverse = False
        self.all_entries = []
        self._thumb_items = {}  # idx -> {bg_id, img_id, text_id, photo_ref, loaded}
        self._thumb_cols = 1
        self._thumb_item_w = self._s(110)
        self._thumb_item_h = self._s(110)

        self._nav_back_stack = []
        self._nav_forward_stack = []
        self._nav_navigating = False
        self._range_anchor = None
        self._blink_timer = None
        self._blink_on = False
        self._thumb_cancel_token = 0
        self._thumb_lock = threading.Lock()
        self._thumb_visible_range = (0, 0)
        self._thumb_loader_token = 0
        self._batch_timer = None
        self._configure_timer = None
        self._batch_insert_token = 0

        self._build_ui()
        self._load_directory(self.current_path)

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.bind("<Escape>", lambda e: self._on_cancel())
        self.bind("<Configure>", self._on_window_configure)
        self.bind("<Control-a>", self._on_select_all)
        self.after(50, self._adjust_breadcrumb_width)

    def _s(self, value):
        """按缩放比例计算像素值"""
        return max(1, int(value * self.zoom))

    def _fs(self, base_size):
        """按缩放比例计算字号"""
        return max(6, int(base_size * self.zoom))

    def _build_ui(self):
        # 顶部工具栏
        toolbar = tk.Frame(self, bg="#f0f0f0", height=self._s(32))
        toolbar.pack(fill=tk.X, padx=self._s(2), pady=self._s(2))
        toolbar.pack_propagate(False)

        btn_kw = dict(borderwidth=1, relief=tk.RAISED, highlightthickness=1,
                      highlightbackground="#cccccc")
        self.btn_back = tk.Button(toolbar, text="◀", width=3, command=self._navigate_back, **btn_kw)
        self.btn_back.pack(side=tk.LEFT, padx=self._s(2), pady=self._s(5))

        self.btn_forward = tk.Button(toolbar, text="▶", width=3, command=self._navigate_forward, **btn_kw)
        self.btn_forward.pack(side=tk.LEFT, padx=self._s(2), pady=self._s(5))

        self.btn_up = tk.Button(toolbar, text="▲", width=3, command=self._go_parent, **btn_kw)
        self.btn_up.pack(side=tk.LEFT, padx=self._s(2), pady=self._s(5))

        self.path_var = tk.StringVar()
        self.path_entry = tk.Entry(toolbar, textvariable=self.path_var, font=("微软雅黑", self._fs(9)))
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=self._s(3), pady=self._s(5))
        self.path_entry.bind("<Return>", self._on_path_enter)

        self.btn_details = tk.Button(toolbar, text="详细", width=5,
                                      command=lambda: self._set_view("details"), **btn_kw)
        self.btn_details.pack(side=tk.LEFT, padx=self._s(2), pady=self._s(5))
        self.btn_thumbs = tk.Button(toolbar, text="缩略图", width=5,
                                     command=lambda: self._set_view("thumbnails"), **btn_kw)
        self.btn_thumbs.pack(side=tk.LEFT, padx=self._s(2), pady=self._s(5))

        # 主内容区
        paned = tk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=self._s(2), pady=self._s(2))

        # 左侧面包屑导航
        left_frame = tk.Frame(paned, bg="white")
        paned.add(left_frame)
        self.paned = paned

        self.breadcrumb_canvas = tk.Canvas(left_frame, bg="white", highlightthickness=0)
        self.breadcrumb_scroll = tk.Scrollbar(left_frame, orient=tk.VERTICAL,
                                             command=self.breadcrumb_canvas.yview)
        self.breadcrumb_canvas.configure(yscrollcommand=self.breadcrumb_scroll.set)
        self.breadcrumb_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.breadcrumb_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.breadcrumb_frame = tk.Frame(self.breadcrumb_canvas, bg="white")
        self.breadcrumb_canvas.create_window((0, 0), window=self.breadcrumb_frame, anchor="nw")
        self.breadcrumb_frame.bind("<Configure>", lambda e: self.breadcrumb_canvas.configure(
            scrollregion=self.breadcrumb_canvas.bbox("all")))

        # 右侧文件列表
        right_frame = tk.Frame(paned, bg="white")
        paned.add(right_frame)

        # 详细信息视图
        columns = ("name", "size", "modified")
        self.file_list = ttk.Treeview(right_frame, columns=columns, show="headings",
                                       selectmode="none")
        self.file_list.heading("name", text="名称", command=lambda: self._sort_by("name"))
        self.file_list.heading("size", text="大小", command=lambda: self._sort_by("size"))
        self.file_list.heading("modified", text="修改日期", command=lambda: self._sort_by("modified"))
        self.file_list.column("name", width=self._s(300))
        self.file_list.column("size", width=self._s(100))
        self.file_list.column("modified", width=self._s(150))

        self.file_scroll = tk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.file_list.yview)
        self.file_list.configure(yscrollcommand=self.file_scroll.set)
        self.file_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.file_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.file_list.bind("<Button-1>", self._on_file_click)
        self.file_list.bind("<Double-1>", self._on_file_double)
        self.file_list.bind("<Button-3>", self._on_file_right_click)

        # 缩略图视图
        self.thumb_canvas = tk.Canvas(right_frame, bg="white", highlightthickness=0)
        self.thumb_scroll = tk.Scrollbar(right_frame, orient=tk.VERTICAL)
        self.thumb_canvas.configure(yscrollcommand=self.thumb_scroll.set)
        self.thumb_scroll.config(command=self._on_thumb_scrollbar)

        self.thumb_inner = tk.Frame(self.thumb_canvas, bg="white")
        self.thumb_canvas.create_window((0, 0), window=self.thumb_inner, anchor="nw")
        self.thumb_inner.bind("<Configure>", lambda e: self.thumb_canvas.configure(
            scrollregion=self.thumb_canvas.bbox("all")))

        # 鼠标滚轮
        self.thumb_canvas.bind("<MouseWheel>", self._on_thumb_scroll)

        # 底部
        bottom = tk.Frame(self, height=self._s(40), bg="#f0f0f0")
        bottom.pack(fill=tk.X, side=tk.BOTTOM, padx=self._s(2), pady=self._s(2))
        bottom.pack_propagate(False)

        self.status_label = tk.Label(bottom, text="就绪", bg="#f0f0f0", anchor="w")
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=self._s(5))

        tk.Button(bottom, text="取消", width=10, command=self._on_cancel).pack(
            side=tk.RIGHT, padx=self._s(5), pady=self._s(5))
        self.btn_open = tk.Button(bottom, text="打开", width=10, command=self._on_open)
        self.btn_open.pack(side=tk.RIGHT, padx=self._s(5), pady=self._s(5))

        if self.multi_select:
            self.multi_mode_var = tk.BooleanVar(value=False)
            self.multi_mode_cb = tk.Checkbutton(bottom, text="多选模式",
                variable=self.multi_mode_var, bg="#f0f0f0",
                command=self._on_multi_mode_toggle)
            self.multi_mode_cb.pack(side=tk.RIGHT, padx=self._s(10), pady=self._s(5))

    def _build_breadcrumbs(self):
        for widget in self.breadcrumb_frame.winfo_children():
            widget.destroy()

        parts = []
        p = self.current_path
        while True:
            parts.insert(0, p)
            parent = p.parent
            if parent == p:
                break
            p = parent

        root = Path("/") if sys.platform != "win32" else Path(self.current_path.anchor)
        if root.is_dir():
            btn = tk.Button(self.breadcrumb_frame, text="（根目录）",
                           anchor="w", bg="white", relief=tk.RAISED,
                           borderwidth=1, highlightthickness=1,
                           highlightbackground="#cccccc",
                           command=lambda: self._load_directory(root))
            btn.pack(fill=tk.X, padx=self._s(2), pady=self._s(1))

        for i, part in enumerate(parts):
            indent = "  " * i
            btn = tk.Button(self.breadcrumb_frame, text=f"{indent}{part.name or str(part)}",
                           anchor="w", bg="white", relief=tk.RAISED,
                           borderwidth=1, highlightthickness=1,
                           highlightbackground="#cccccc",
                           command=lambda p=part: self._load_directory(p))
            btn.pack(fill=tk.X, padx=self._s(2), pady=self._s(1))

    def _load_directory(self, path):
        path = Path(path)
        if not path.exists() or not path.is_dir():
            return

        if not self._nav_navigating:
            old_path = str(self.current_path) if self.current_path else ""
            new_path = str(path)
            if old_path and old_path != new_path:
                self._nav_back_stack.append(self.current_path)
            self._nav_forward_stack.clear()
        self._nav_navigating = False

        self.current_path = path
        self.path_var.set(str(path))
        self._build_breadcrumbs()

        self.file_list.delete(*self.file_list.get_children())
        self.file_list.selection_set()
        self.thumb_canvas.delete("all")
        self.thumbnail_cache.clear()
        self._thumb_items.clear()
        self._stop_blink_anchor()
        self._cancel_batch_timer()
        self._thumb_cancel_token += 1
        self._thumb_loader_token += 1
        self.selected_items.clear()
        self._range_anchor = None

        try:
            entries = list(path.iterdir())
        except PermissionError:
            self.status_label.config(text="权限不足")
            self.all_entries = []
            return

        dirs = [e for e in entries if e.is_dir()]
        files = [e for e in entries if e.is_file()]
        if self.filetypes is not None:
            files = [f for f in files if f.suffix.lower() in self.filetypes]
        dirs = self._sort_entries(dirs)
        files = self._sort_entries(files)
        self.all_entries = dirs + files

        self._batch_index = 0
        self._batch_insert_token += 1
        self._batch_insert_details(self._batch_insert_token)

        if self.view_mode == "thumbnails":
            self._show_thumbnails()

        self._update_status()

    def _batch_insert_details(self, token=None):
        if token is not None and token != self._batch_insert_token:
            return
        batch_size = 100
        start = self._batch_index
        end = min(start + batch_size, len(self.all_entries))

        for entry in self.all_entries[start:end]:
            name = entry.name
            is_dir = entry.is_dir()

            if is_dir:
                size_str = ""
                mod_time = ""
                display_name = f"▶ {name}"
            else:
                try:
                    st = entry.stat()
                    size_str = self._format_size(st.st_size)
                    mod_time = time.strftime("%Y/%m/%d %H:%M", time.localtime(st.st_mtime))
                except OSError:
                    size_str = ""
                    mod_time = ""
                display_name = f"▦ {name}"

            self.file_list.insert("", "end", iid=str(entry),
                                  values=(display_name, size_str, mod_time),
                                  tags=("placeholder",))

        self._batch_index = end
        if end < len(self.all_entries):
            self._batch_timer = self.after(5, lambda: self._batch_insert_details(token))

    def _sort_entries(self, entries):
        def _safe_stat(x):
            try:
                return x.stat()
            except (OSError, PermissionError):
                return None

        if self.sort_key == "name":
            return sorted(entries, key=lambda x: x.name.lower(), reverse=self.sort_reverse)
        elif self.sort_key == "size":
            return sorted(entries,
                          key=lambda x: (_safe_stat(x) or type("S", (), {"st_size": 0})()).st_size,
                          reverse=self.sort_reverse)
        elif self.sort_key == "modified":
            return sorted(entries,
                          key=lambda x: (_safe_stat(x) or type("S", (), {"st_mtime": 0})()).st_mtime,
                          reverse=self.sort_reverse)
        return entries

    _THUMB_CACHE_MAX = 200  # LRU 缓存上限

    def _thumb_layout(self):
        """计算缩略图网格布局参数。"""
        canvas_width = self.thumb_canvas.winfo_width()
        if canvas_width < self._s(100):
            canvas_width = self._s(600)
        self._thumb_cols = max(1, canvas_width // self._thumb_item_w)
        if self._thumb_cols:
            self._thumb_item_w = canvas_width // self._thumb_cols

    def _thumb_index_at(self, canvas_x, canvas_y):
        """返回 (canvas_x, canvas_y) 处的条目索引，无则返回 None。"""
        col = int(canvas_x // self._thumb_item_w)
        row = int(canvas_y // self._thumb_item_h)
        idx = row * self._thumb_cols + col
        if 0 <= idx < len(self.all_entries):
            return idx
        return None

    def _thumb_entry_str(self, idx):
        """返回第 idx 个条目的字符串路径。"""
        return str(self.all_entries[idx])

    def _thumb_render_viewport(self):
        """渲染可见区域内的缩略图项目（每次全量重绘，避免孤儿 item）。"""
        canvas = self.thumb_canvas
        canvas.delete("all")
        self._thumb_items.clear()
        total = len(self.all_entries)
        if total == 0:
            return

        iw = self._thumb_item_w
        ih = self._thumb_item_h
        cols = self._thumb_cols

        # 计算可见范围（加上 extra 缓冲行）
        cy = int(canvas.canvasy(0))
        ch = canvas.winfo_height() or self._s(600)
        extra = 2
        first_visible = max(0, (cy // ih) - extra) * cols
        last_visible = min(total, ((cy + ch) // ih + 1 + extra) * cols)

        for idx in range(first_visible, last_visible):
            entry = self.all_entries[idx]
            row = idx // cols
            col = idx % cols
            x = col * iw + iw // 2
            entry_str = str(entry)
            is_selected = entry_str in self.selected_items
            is_dir = entry.is_dir()

            # 背景矩形（选中高亮）
            bg_color = "#cce8ff" if is_selected else "white"
            bg_id = canvas.create_rectangle(
                col * iw + 2, row * ih + 2,
                (col + 1) * iw - 2, (row + 1) * ih - 2,
                fill=bg_color, outline="", tags="thumb_bg"
            )

            # 缩略图或占位符
            thumb_y = row * ih + ih * 0.38
            cached = self.thumbnail_cache.get(entry)
            if cached is not None and HAS_PIL and isinstance(cached, ImageTk.PhotoImage):
                img_id = canvas.create_image(x, thumb_y, image=cached, tags="thumb_img")
                photo_ref = cached
                loaded = True
            else:
                img_id = None
                photo_ref = None
                loaded = False
                placeholder = "▶" if is_dir else "▦"
                canvas.create_text(x, thumb_y, text=placeholder,
                                   font=("微软雅黑", self._fs(18)), fill="#aaa",
                                   tags="thumb_placeholder")

            # 文件名文字
            canvas.create_text(
                x, row * ih + ih - self._s(8),
                text=entry.name,
                font=("微软雅黑", self._fs(8)),
                fill="black",
                width=iw - self._s(8),
                tags="thumb_text"
            )

            self._thumb_items[idx] = {
                'bg_id': bg_id,
                'img_id': img_id,
                'photo_ref': photo_ref,
                'loaded': loaded,
            }

        # 记录可见范围，启动/确保全局加载器运行
        self._thumb_visible_range = (first_visible, last_visible)
        self._ensure_thumb_loader()

    def _show_thumbnails(self):
        """Canvas 虚拟化缩略图视图 —— 只渲染可见区域。"""
        canvas = self.thumb_canvas
        canvas.delete("all")
        self._thumb_items.clear()

        if not self.all_entries:
            return

        self._thumb_layout()

        total = len(self.all_entries)
        cols = self._thumb_cols
        total_height = ((total + cols - 1) // cols) * self._thumb_item_h + self._s(20)
        canvas.configure(scrollregion=(0, 0, self._thumb_item_w * cols, total_height))

        # 移除旧的绑定，添加新的
        canvas.unbind("<Button-1>")
        canvas.unbind("<Double-Button-1>")
        canvas.unbind("<Button-3>")
        canvas.unbind("<Configure>")
        canvas.bind("<Button-1>", self._on_thumb_canvas_click)
        canvas.bind("<Double-Button-1>", self._on_thumb_canvas_double)
        canvas.bind("<Button-3>", self._on_thumb_canvas_right)
        canvas.bind("<Configure>", self._on_thumb_canvas_configure)

        self._thumb_render_viewport()

    def _ensure_thumb_loader(self):
        """确保全局缩略图加载线程在运行（切换目录后 token 变化，旧线程自动消亡）。"""
        if not hasattr(self, '_thumb_loader_thread') or self._thumb_loader_thread is None \
                or not self._thumb_loader_thread.is_alive():
            t = threading.Thread(target=self._thumb_loader_loop, daemon=True,
                                 args=(self._thumb_loader_token,))
            self._thumb_loader_thread = t
            t.start()

    def _load_one_thumb(self, idx):
        """加载单个缩略图到缓存，返回是否已加载。在主线程 or 后台线程均可调用。"""
        if idx >= len(self.all_entries):
            return False
        entry = self.all_entries[idx]
        with self._thumb_lock:
            cached = self.thumbnail_cache.get(entry)
        if cached is not None and HAS_PIL and isinstance(cached, ImageTk.PhotoImage):
            return True
        thumb = get_thumbnail(str(entry), (self._s(64), self._s(64)))
        with self._thumb_lock:
            if len(self.thumbnail_cache) >= self._THUMB_CACHE_MAX:
                try:
                    self.thumbnail_cache.pop(next(iter(self.thumbnail_cache)))
                except (StopIteration, KeyError):
                    pass
            self.thumbnail_cache[entry] = thumb
        return False  # 刚加载完，还不是 PhotoImage

    def _thumb_loader_loop(self, token):
        """全局加载器：先刷可见区域，再逐个加载剩余文件。
        滚动时自动响应 _thumb_visible_range 的变化。"""
        total = len(self.all_entries)
        if total == 0:
            return
        walk_pos = 0  # 顺序扫描位置
        while True:
            if token != self._thumb_loader_token:
                return
            if total == 0:
                break
            vis_start, vis_end = self._thumb_visible_range

            # Phase 1: 优先刷可见区域（如果有漏网之鱼）
            did_visible = False
            for idx in range(vis_start, min(vis_end, total)):
                if token != self._thumb_loader_token:
                    return
                if self._load_one_thumb(idx):
                    # 缓存中已有 PhotoImage，尝试刷新画布
                    if idx in self._thumb_items and not self._thumb_items[idx]['loaded']:
                        self.after(0, lambda e=idx, t=token: self._update_thumb_icon_from_cache(e, t))
                else:
                    did_visible = True  # 刚加载了一个，需要再刷一轮
                    if idx in self._thumb_items and not self._thumb_items[idx]['loaded']:
                        self.after(0, lambda e=idx, t=token: self._update_thumb_icon_from_cache(e, t))

            if did_visible:
                continue  # 可见区域还有待加载，下一轮继续

            # Phase 2: 顺序加载剩余（每次批量前进）
            batch = 0
            while batch < 30 and walk_pos < total:
                if token != self._thumb_loader_token:
                    return
                if vis_start <= walk_pos < vis_end:
                    walk_pos += 1
                    continue  # 跳过可见区域（已处理）
                self._load_one_thumb(walk_pos)
                batch += 1
                walk_pos += 1

            if walk_pos >= total:
                break  # 全部加载完毕

    def _update_thumb_icon_from_cache(self, idx, token):
        """从缓存中取出 PhotoImage 更新到 Canvas（主线程）。"""
        if token != self._thumb_loader_token:
            return
        if idx not in self._thumb_items:
            return
        entry = self.all_entries[idx]
        with self._thumb_lock:
            cached = self.thumbnail_cache.get(entry)
        if cached is None or not HAS_PIL:
            return
        if not isinstance(cached, ImageTk.PhotoImage):
            photo = self._pil_to_photo(cached)
            with self._thumb_lock:
                if token == self._thumb_loader_token:
                    self.thumbnail_cache[entry] = photo if photo else cached
        else:
            photo = cached
        if photo is None:
            return
        info = self._thumb_items[idx]
        canvas = self.thumb_canvas
        if info.get('img_id') is not None:
            canvas.itemconfig(info['img_id'], image=photo)
            info['photo_ref'] = photo
            info['loaded'] = True
            return
        # 创建新 image item
        iw = self._thumb_item_w
        ih = self._thumb_item_h
        cols = self._thumb_cols
        row = idx // cols
        col = idx % cols
        x = col * iw + iw // 2
        thumb_y = row * ih + ih * 0.38
        img_id = canvas.create_image(x, thumb_y, image=photo, tags="thumb_img")
        info['img_id'] = img_id
        info['photo_ref'] = photo
        info['loaded'] = True
        # 删占位符
        for cid in canvas.find_all():
            if canvas.type(cid) == "text":
                coords = canvas.coords(cid)
                if abs(coords[0] - x) < 5 and abs(coords[1] - thumb_y) < 5:
                    if canvas.itemcget(cid, "text") in ("▶", "▦"):
                        canvas.delete(cid)
                        break

    def _pil_to_photo(self, pil_img):
        """将 PIL Image 转为 PhotoImage（必须在主线程调用）。"""
        if pil_img is None or not HAS_PIL:
            return None
        return ImageTk.PhotoImage(pil_img)

    def _update_thumb_icon(self, entry, idx, token):
        """在 Canvas 上更新指定条目的缩略图（主线程调用）。"""
        if token != self._thumb_cancel_token:
            return
        if idx not in self._thumb_items:
            return
        with self._thumb_lock:
            pil_img = self.thumbnail_cache.get(entry)
        if pil_img is None:
            return
        if isinstance(pil_img, ImageTk.PhotoImage):
            photo = pil_img
        else:
            photo = self._pil_to_photo(pil_img)
            with self._thumb_lock:
                if token == self._thumb_cancel_token:
                    self.thumbnail_cache[entry] = photo
        if photo is None:
            return
        info = self._thumb_items[idx]
        canvas = self.thumb_canvas
        cols = self._thumb_cols
        iw = self._thumb_item_w
        ih = self._thumb_item_h
        row = idx // cols
        col = idx % cols
        x = col * iw + iw // 2
        thumb_y = row * ih + ih * 0.38
        if info.get('img_id') is not None:
            # 已有 image item，替换图片
            canvas.itemconfig(info['img_id'], image=photo)
            info['photo_ref'] = photo
            info['loaded'] = True
            return
        # 创建新的 image item
        img_id = canvas.create_image(x, thumb_y, image=photo, tags="thumb_img")
        info['img_id'] = img_id
        info['photo_ref'] = photo
        info['loaded'] = True
        # 删除旧的占位符文字
        for cid in canvas.find_all():
            if canvas.type(cid) == "text":
                coords = canvas.coords(cid)
                if abs(coords[0] - x) < 5 and abs(coords[1] - thumb_y) < 5:
                    if canvas.itemcget(cid, "text") in ("▶", "▦"):
                        canvas.delete(cid)
                        break

    # ---- Canvas 事件处理 ----
    def _thumb_idx_from_event(self, event):
        """从 Canvas 鼠标事件中获取条目索引。"""
        x = self.thumb_canvas.canvasx(event.x)
        y = self.thumb_canvas.canvasy(event.y)
        return self._thumb_index_at(x, y)

    def _on_thumb_canvas_click(self, event):
        idx = self._thumb_idx_from_event(event)
        if idx is None:
            return
        entry_str = self._thumb_entry_str(idx)
        if self.multi_select and self.multi_mode_var.get():
            if entry_str in self.selected_items:
                self.selected_items.discard(entry_str)
            else:
                self.selected_items.add(entry_str)
        else:
            self.selected_items = {entry_str}
        self._thumb_render_viewport()
        self._update_status()

    def _on_thumb_canvas_double(self, event):
        if self.multi_select and self.multi_mode_var.get():
            return
        idx = self._thumb_idx_from_event(event)
        if idx is None:
            return
        entry_str = self._thumb_entry_str(idx)
        if os.path.isdir(entry_str):
            self._load_directory(entry_str)
        else:
            self._on_open()

    def _on_thumb_canvas_right(self, event):
        if not (self.multi_select and self.multi_mode_var.get()):
            return "break"
        idx = self._thumb_idx_from_event(event)
        if idx is None:
            return "break"
        entry_str = self._thumb_entry_str(idx)
        if self._range_anchor is None:
            self._range_anchor = entry_str
            self._blink_on = True
            self._start_blink_anchor()
            count = len(self.selected_items)
            self.status_label.config(
                text=f"多选模式已启用，左键单个选择（可取消），右键范围选择（仅选定）。"
                     f"当前已选择{count}个文件，已进入范围模式",
                fg="blue")
        else:
            try:
                idx1 = next(i for i, e in enumerate(self.all_entries)
                            if str(e) == self._range_anchor)
                idx2 = idx
            except StopIteration:
                self._range_anchor = None
                self.status_label.config(
                    text="多选模式已启用，左键单个选择（可取消），右键范围选择（仅选定）。",
                    fg="black")
                return "break"
            lo, hi = min(idx1, idx2), max(idx1, idx2)
            for i in range(lo, hi + 1):
                eiid = str(self.all_entries[i])
                self.selected_items.add(eiid)
            self._stop_blink_anchor()
            self._thumb_render_viewport()
            self._range_anchor = None
            self.status_label.config(
                text="多选模式已启用，左键单个选择（可取消），右键范围选择（仅选定）。",
                fg="black")
        return "break"

    def _on_thumb_canvas_configure(self, event):
        """画布大小变化时重新布局。"""
        self._thumb_layout()
        total = len(self.all_entries)
        cols = self._thumb_cols
        total_height = ((total + cols - 1) // cols) * self._thumb_item_h + self._s(20)
        self.thumb_canvas.configure(scrollregion=(
            0, 0, self._thumb_item_w * cols, total_height))
        self._thumb_render_viewport()

    def _on_file_click(self, event):
        iid = self.file_list.identify_row(event.y)
        if not iid:
            return
        if self.multi_select and self.multi_mode_var.get():
            if iid in self.selected_items:
                self.selected_items.discard(iid)
                self.file_list.selection_remove(iid)
            else:
                self.selected_items.add(iid)
                self.file_list.selection_add(iid)
        else:
            self.file_list.selection_set(iid)
            self.selected_items = {iid}
        self._update_status()
        return "break"

    def _on_file_double(self, event):
        if self.multi_select and self.multi_mode_var.get():
            return
        iid = self.file_list.identify_row(event.y)
        if not iid:
            return
        if os.path.isdir(iid):
            self._load_directory(iid)
        else:
            self._on_open()

    def _on_file_right_click(self, event):
        if not (self.multi_select and self.multi_mode_var.get()):
            return "break"
        iid = self.file_list.identify_row(event.y)
        if not iid:
            return "break"
        if self._range_anchor is None:
            self._range_anchor = iid
            self.file_list.selection_add(iid)
            self._blink_on = True
            self._start_blink_anchor()
            count = len(self.selected_items)
            self.status_label.config(
                text=f"多选模式已启用，左键单个选择（可取消），右键范围选择（仅选定）。"
                     f"当前已选择{count}个文件，已进入范围模式",
                fg="blue")
        else:
            try:
                idx1 = next(i for i, e in enumerate(self.all_entries)
                            if str(e) == self._range_anchor)
                idx2 = next(i for i, e in enumerate(self.all_entries)
                            if str(e) == iid)
            except StopIteration:
                self._range_anchor = None
                self.status_label.config(
                    text="多选模式已启用，左键单个选择（可取消），右键范围选择（仅选定）",
                    fg="black")
                return "break"
            lo, hi = min(idx1, idx2), max(idx1, idx2)
            for i in range(lo, hi + 1):
                eiid = str(self.all_entries[i])
                self.selected_items.add(eiid)
                self.file_list.selection_add(eiid)
            self._stop_blink_anchor()
            self._range_anchor = None
            self.status_label.config(
                text="多选模式已启用，左键单个选择（可取消），右键范围选择（仅选定）",
                fg="black")
        return "break"

    def _on_select_all(self, event=None):
        if not (self.multi_select and self.multi_mode_var.get()):
            return "break"
        self._stop_blink_anchor()
        self._range_anchor = None
        for entry in self.all_entries:
            iid = str(entry)
            self.selected_items.add(iid)
            self.file_list.selection_add(iid)
        if self.view_mode == "thumbnails":
            self._thumb_render_viewport()
        self.status_label.config(
            text=f"多选模式已启用，左键单个选择（可取消），右键范围选择（仅选定）。"
                 f"当前已选择{len(self.selected_items)}个文件",
            fg="blue")
        return "break"

    def _start_blink_anchor(self):
        if self._blink_timer is not None:
            self.after_cancel(self._blink_timer)
        self._blink_timer = self.after(667, self._blink_anchor_tick)

    def _blink_anchor_tick(self):
        if self._range_anchor is None:
            self._blink_on = False
            self._blink_timer = None
            return
        if self.view_mode == "thumbnails":
            canvas = self.thumb_canvas
            if self._blink_on:
                # 找到 anchor 对应的 idx 并更新 bg 为白色
                for idx, info in self._thumb_items.items():
                    if idx >= len(self.all_entries):
                        continue
                    if str(self.all_entries[idx]) == self._range_anchor:
                        if info.get('bg_id'):
                            canvas.itemconfig(info['bg_id'], fill="white")
                        break
                self._blink_on = False
            else:
                for idx, info in self._thumb_items.items():
                    if idx >= len(self.all_entries):
                        continue
                    if str(self.all_entries[idx]) == self._range_anchor:
                        if info.get('bg_id'):
                            canvas.itemconfig(info['bg_id'], fill="#cce8ff")
                        break
                self._blink_on = True
        else:
            if self._blink_on:
                self.file_list.selection_remove(self._range_anchor)
                self._blink_on = False
            else:
                self.file_list.selection_add(self._range_anchor)
                self._blink_on = True
        self._blink_timer = self.after(667, self._blink_anchor_tick)
        self.update_idletasks()

    def _stop_blink_anchor(self):
        if self._blink_timer is not None:
            self.after_cancel(self._blink_timer)
            self._blink_timer = None
        self._blink_on = False
        if self.view_mode == "thumbnails" and self._range_anchor:
            self._thumb_render_viewport()

    def _cancel_batch_timer(self):
        if self._batch_timer is not None:
            try:
                self.after_cancel(self._batch_timer)
            except Exception:
                pass
            self._batch_timer = None

    def _on_multi_mode_toggle(self):
        if self.multi_mode_var.get():
            self._range_anchor = None
            self.status_label.config(
                text="多选模式已启用，左键单个选择（可取消），右键范围选择（仅选定）",
                fg="black")
        else:
            self._stop_blink_anchor()
            self._update_status()

    def _update_status(self):
        if self.multi_select and self.multi_mode_var.get():
            return
        count = len(self.selected_items)
        if count == 0:
            self.status_label.config(text="未选择")
        elif count == 1:
            self.status_label.config(text=f"已选择: {os.path.basename(list(self.selected_items)[0])}")
        else:
            self.status_label.config(text=f"已选择 {count} 项")

    def _on_path_enter(self, event):
        path = self.path_var.get()
        if os.path.isdir(path):
            self._load_directory(path)

    def _navigate_back(self):
        if not self._nav_back_stack:
            return
        self._nav_forward_stack.append(self.current_path)
        target = self._nav_back_stack.pop()
        self._nav_navigating = True
        self._load_directory(target)

    def _navigate_forward(self):
        if not self._nav_forward_stack:
            return
        self._nav_back_stack.append(self.current_path)
        target = self._nav_forward_stack.pop()
        self._nav_navigating = True
        self._load_directory(target)

    def _go_parent(self):
        parent = self.current_path.parent
        if parent != self.current_path:
            self._load_directory(parent)

    def _adjust_breadcrumb_width(self):
        self.update_idletasks()
        w = self.paned.winfo_width()
        if w > self._s(100):
            pos = max(self._s(100), int(w * 0.1))
            self.paned.sash_place(0, pos, 1)

    def _on_window_configure(self, event):
        if event.widget == self and self.winfo_viewable():
            if self._configure_timer is not None:
                self.after_cancel(self._configure_timer)
            self._configure_timer = self.after(150, self._adjust_breadcrumb_width)

    def _sort_by(self, key):
        if self.sort_key == key:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_key = key
            self.sort_reverse = False
        self._load_directory(self.current_path)

    def _set_view(self, mode):
        self.view_mode = mode
        FileBrowserDialog._last_view_mode = mode
        if mode == "details":
            self.thumb_canvas.pack_forget()
            self.thumb_scroll.pack_forget()
            self.file_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            self.file_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        else:
            self.file_list.pack_forget()
            self.file_scroll.pack_forget()
            self.thumb_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            self.thumb_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            self._show_thumbnails()

    def _on_thumb_scroll(self, event):
        self.thumb_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self._thumb_render_viewport()

    def _on_thumb_scrollbar(self, *args):
        """滚动条拖动/点击时同步刷新视口。"""
        self.thumb_canvas.yview(*args)
        self._thumb_render_viewport()

    def _format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def _on_open(self):
        files_only = {f for f in self.selected_items if os.path.isfile(f)}
        if not files_only:
            messagebox.showwarning("提示", "请先选择文件")
            return
        last_path = str(self.current_path)
        self._stop_blink_anchor()
        if self.on_select:
            self.on_select(list(files_only), last_path)
        self.destroy()

    def _on_cancel(self):
        if self.selected_items:
            count = len(self.selected_items)
            if not messagebox.askyesno("取消选择",
                    f"您已选择 {count} 个文件，要取消选择吗？"):
                return
        self._stop_blink_anchor()
        if self.on_cancel:
            self.on_cancel()
        self.destroy()


# ============ 母窗口 ============
class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("文件选择器 Demo")
        self.geometry("600x400")

        self.last_path = None
        self.selected_files = []

        self._build_ui()

    def _build_ui(self):
        ctrl = tk.Frame(self, padx=20, pady=20)
        ctrl.pack(fill=tk.X)

        tk.Label(ctrl, text="选择模式:", font=("微软雅黑", 12)).pack(side=tk.LEFT)

        self.mode_var = tk.StringVar(value="single")
        tk.Radiobutton(ctrl, text="单选", variable=self.mode_var,
                      value="single", font=("微软雅黑", 11)).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(ctrl, text="多选", variable=self.mode_var,
                      value="multi", font=("微软雅黑", 11)).pack(side=tk.LEFT, padx=10)

        tk.Button(self, text="选择文件...", font=("微软雅黑", 12),
                 command=self._open_browser, width=15).pack(pady=20)

        result_frame = tk.Frame(self, padx=20, pady=10)
        result_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(result_frame, text="已选择的文件:", font=("微软雅黑", 11), anchor="w").pack(
            fill=tk.X)

        self.result_list = tk.Listbox(result_frame, font=("Consolas", 10))
        scrollbar = tk.Scrollbar(result_frame, command=self.result_list.yview)
        self.result_list.configure(yscrollcommand=scrollbar.set)

        self.result_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.path_label = tk.Label(self, text="上次打开路径: 无",
                                  font=("微软雅黑", 9), fg="gray", anchor="w")
        self.path_label.pack(fill=tk.X, padx=20, pady=5)

    def _open_browser(self):
        multi = self.mode_var.get() == "multi"
        dialog = FileBrowserDialog(
            self,
            initial_path=None,
            multi_select=multi,
            last_path=self.last_path,
            on_select=self._on_select,
            on_cancel=self._on_cancel
        )
        self.wait_window(dialog)

    def _on_select(self, files, last_path):
        self.selected_files = files
        self.last_path = last_path
        self.result_list.delete(0, tk.END)
        for f in files:
            self.result_list.insert(tk.END, f)
        self.path_label.config(text=f"上次打开路径: {last_path}")

    def _on_cancel(self):
        pass


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()