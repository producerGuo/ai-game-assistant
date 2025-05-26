import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pyautogui
import requests
import base64
import json
import os
import time
import threading
from PIL import Image, ImageTk, ImageDraw
import mss
import cv2
import numpy as np

# 导入Windows API用于窗口置顶
try:
    import ctypes
    from ctypes import wintypes
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False

class RegionSelector:
    """区域选择器"""
    
    def __init__(self):
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.rect_id = None
        self.selecting = False
        
    def select_region(self, callback=None):
        """选择屏幕区域"""
        self.callback = callback
        
        # 创建全屏透明窗口
        self.selector_window = tk.Toplevel()
        self.selector_window.attributes('-fullscreen', True)
        self.selector_window.attributes('-alpha', 0.3)
        self.selector_window.attributes('-topmost', True)
        self.selector_window.configure(bg='black')
        
        # 创建画布
        self.canvas = tk.Canvas(
            self.selector_window,
            highlightthickness=0,
            bg='black'
        )
        self.canvas.pack(fill='both', expand=True)
        
        # 绑定鼠标事件
        self.canvas.bind('<Button-1>', self.start_selection)
        self.canvas.bind('<B1-Motion>', self.update_selection)
        self.canvas.bind('<ButtonRelease-1>', self.end_selection)
        self.canvas.bind('<Escape>', lambda e: self.cancel_selection())
        
        # 设置焦点以接收键盘事件
        self.canvas.focus_set()
        
        # 显示提示
        self.canvas.create_text(
            self.selector_window.winfo_screenwidth()//2,
            50,
            text="拖拽鼠标选择区域，ESC取消",
            fill='white',
            font=('Arial', 16)
        )
    
    def start_selection(self, event):
        """开始选择"""
        self.start_x = event.x
        self.start_y = event.y
        self.selecting = True
        
        if self.rect_id:
            self.canvas.delete(self.rect_id)
    
    def update_selection(self, event):
        """更新选择框"""
        if not self.selecting:
            return
            
        if self.rect_id:
            self.canvas.delete(self.rect_id)
            
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, event.x, event.y,
            outline='red', width=2
        )
    
    def end_selection(self, event):
        """结束选择"""
        if not self.selecting:
            return
            
        self.end_x = event.x
        self.end_y = event.y
        self.selecting = False
        
        # 确保坐标正确（左上角到右下角）
        x1 = min(self.start_x, self.end_x)
        y1 = min(self.start_y, self.end_y)
        x2 = max(self.start_x, self.end_x)
        y2 = max(self.start_y, self.end_y)
        
        region = (x1, y1, x2-x1, y2-y1)  # (x, y, width, height)
        
        self.selector_window.destroy()
        
        if self.callback:
            self.callback(region)
    
    def cancel_selection(self):
        """取消选择"""
        self.selecting = False
        self.selector_window.destroy()
        
        if self.callback:
            self.callback(None)

class WindowTopMost:
    """窗口置顶控制器"""
    
    def __init__(self):
        self.is_topmost = False
        
    def set_window_topmost(self, root, topmost=True):
        """设置窗口置顶"""
        try:
            if WINDOWS_AVAILABLE:
                # 使用Windows API设置置顶
                hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
                if topmost:
                    ctypes.windll.user32.SetWindowPos(
                        hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002
                    )
                else:
                    ctypes.windll.user32.SetWindowPos(
                        hwnd, -2, 0, 0, 0, 0, 0x0001 | 0x0002
                    )
            else:
                # 使用tkinter的attributes方法
                root.attributes('-topmost', topmost)
                
            self.is_topmost = topmost
            return True
            
        except Exception as e:
            print(f"设置窗口置顶失败: {e}")
            # 降级到tkinter方法
            try:
                root.attributes('-topmost', topmost)
                self.is_topmost = topmost
                return True
            except:
                return False

class EnhancedAIGameAssistant:
    """增强版AI游戏助手"""
    
    def __init__(self, root):
        self.root = root
        self.setup_window()
        
        # 核心组件
        self.region_selector = RegionSelector()
        self.window_controller = WindowTopMost()
        
        # 配置和状态
        self.config = self.load_config()
        self.monitoring = False
        self.selected_region = None  # 选定的识别区域
        self.full_screen_mode = True  # 是否全屏识别
        
        self.setup_ui()
        
        # 加载保存的设置
        self.load_settings()
    
    def setup_window(self):
        """设置窗口"""
        self.root.title("AI游戏助手 - 增强版")
        self.root.geometry("500x700")
        self.root.resizable(True, True)
        
        # 设置窗口图标（如果有的话）
        try:
            # self.root.iconbitmap('icon.ico')
            pass
        except:
            pass
    
    def setup_ui(self):
        """设置用户界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # ===================
        # 窗口控制区域
        # ===================
        window_frame = ttk.LabelFrame(main_frame, text="窗口控制", padding="10")
        window_frame.pack(fill='x', pady=(0, 10))
        
        # 置顶控制
        topmost_frame = ttk.Frame(window_frame)
        topmost_frame.pack(fill='x', pady=(0, 5))
        
        self.topmost_var = tk.BooleanVar()
        self.topmost_checkbox = ttk.Checkbutton(
            topmost_frame,
            text="保持窗口在最上方",
            variable=self.topmost_var,
            command=self.toggle_topmost
        )
        self.topmost_checkbox.pack(side='left')
        
        # 透明度控制
        alpha_frame = ttk.Frame(window_frame)
        alpha_frame.pack(fill='x', pady=(5, 0))
        
        ttk.Label(alpha_frame, text="窗口透明度:").pack(side='left')
        
        self.alpha_var = tk.DoubleVar(value=1.0)
        alpha_scale = ttk.Scale(
            alpha_frame,
            from_=0.3,
            to=1.0,
            variable=self.alpha_var,
            orient='horizontal',
            command=self.update_alpha
        )
        alpha_scale.pack(side='left', fill='x', expand=True, padx=(5, 5))
        
        self.alpha_label = ttk.Label(alpha_frame, text="100%")
        self.alpha_label.pack(side='right')
        
        # ===================
        # 识别区域设置
        # ===================
        region_frame = ttk.LabelFrame(main_frame, text="识别区域设置", padding="10")
        region_frame.pack(fill='x', pady=(0, 10))
        
        # 区域选择模式
        mode_frame = ttk.Frame(region_frame)
        mode_frame.pack(fill='x', pady=(0, 10))
        
        self.region_mode_var = tk.StringVar(value="fullscreen")
        
        fullscreen_radio = ttk.Radiobutton(
            mode_frame,
            text="全屏识别",
            variable=self.region_mode_var,
            value="fullscreen",
            command=self.update_region_mode
        )
        fullscreen_radio.pack(side='left', padx=(0, 20))
        
        region_radio = ttk.Radiobutton(
            mode_frame,
            text="指定区域识别",
            variable=self.region_mode_var,
            value="region",
            command=self.update_region_mode
        )
        region_radio.pack(side='left')
        
        # 区域选择按钮
        region_btn_frame = ttk.Frame(region_frame)
        region_btn_frame.pack(fill='x', pady=(0, 10))
        
        self.select_region_btn = ttk.Button(
            region_btn_frame,
            text="🎯 选择识别区域",
            command=self.start_region_selection,
            state='disabled'
        )
        self.select_region_btn.pack(side='left', padx=(0, 10))
        
        self.preview_region_btn = ttk.Button(
            region_btn_frame,
            text="👁️ 预览区域",
            command=self.preview_selected_region,
            state='disabled'
        )
        self.preview_region_btn.pack(side='left')
        
        # 区域信息显示
        self.region_info_label = ttk.Label(
            region_frame,
            text="当前：全屏识别",
            foreground='blue'
        )
        self.region_info_label.pack(anchor='w')
        
        # ===================
        # API设置 (保持原有的)
        # ===================
        api_frame = ttk.LabelFrame(main_frame, text="API设置", padding="10")
        api_frame.pack(fill='x', pady=(0, 10))
        
        # API Key
        ttk.Label(api_frame, text="OpenAI API Key:").pack(anchor='w')
        self.api_key_var = tk.StringVar(value=self.config.get('api_key', ''))
        api_key_entry = ttk.Entry(api_frame, textvariable=self.api_key_var, show='*', width=50)
        api_key_entry.pack(fill='x', pady=(2, 5))
        
        # Base URL
        ttk.Label(api_frame, text="Base URL (可选):").pack(anchor='w')
        self.base_url_var = tk.StringVar(value=self.config.get('base_url', 'https://api.openai.com/v1'))
        base_url_entry = ttk.Entry(api_frame, textvariable=self.base_url_var, width=50)
        base_url_entry.pack(fill='x', pady=(2, 5))
        
        # 模型选择
        ttk.Label(api_frame, text="模型:").pack(anchor='w')
        self.model_var = tk.StringVar(value=self.config.get('model', 'gpt-4o'))
        model_combo = ttk.Combobox(
            api_frame, 
            textvariable=self.model_var,
            values=['gpt-4o', 'gpt-4o-mini', 'gpt-4-vision-preview', 'gpt-4-turbo'],
            width=47
        )
        model_combo.pack(fill='x', pady=(2, 10))
        
        save_config_btn = ttk.Button(api_frame, text="保存配置", command=self.save_config)
        save_config_btn.pack(anchor='w')
        
        # ===================
        # 游戏提示设置
        # ===================
        game_frame = ttk.LabelFrame(main_frame, text="游戏提示设置", padding="10")
        game_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(game_frame, text="游戏类型/提示词:").pack(anchor='w')
        self.game_prompt_var = tk.StringVar(value=self.config.get('game_prompt', 
            '你是一个专业的游戏助手。请分析这个游戏画面，给出具体的操作建议。'))
        game_prompt_text = tk.Text(game_frame, height=3, width=50, wrap='word')
        game_prompt_text.pack(fill='x', pady=(2, 5))
        game_prompt_text.insert('1.0', self.game_prompt_var.get())
        
        def update_prompt(*args):
            self.game_prompt_var.set(game_prompt_text.get('1.0', 'end-1c'))
        
        game_prompt_text.bind('<KeyRelease>', update_prompt)
        
        # ===================
        # 控制按钮
        # ===================
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill='x', pady=(0, 10))
        
        self.start_btn = ttk.Button(
            control_frame, 
            text="🎮 开始监控", 
            command=self.toggle_monitoring,
            style='Accent.TButton'
        )
        self.start_btn.pack(side='left', padx=(0, 10))
        
        self.manual_btn = ttk.Button(
            control_frame,
            text="📸 手动识别",
            command=self.manual_recognition
        )
        self.manual_btn.pack(side='left', padx=(0, 10))
        
        test_btn = ttk.Button(control_frame, text="🧪 测试API", command=self.test_api)
        test_btn.pack(side='left')
        
        # ===================
        # 结果显示区域
        # ===================
        result_frame = ttk.LabelFrame(main_frame, text="AI建议", padding="10")
        result_frame.pack(fill='both', expand=True)
        
        # 创建文本区域和滚动条
        text_frame = ttk.Frame(result_frame)
        text_frame.pack(fill='both', expand=True)
        
        self.result_text = tk.Text(
            text_frame, 
            height=15, 
            wrap='word',
            font=('Consolas', 10)
        )
        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar.set)
        
        self.result_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 清除按钮
        clear_btn = ttk.Button(result_frame, text="清除记录", command=self.clear_results)
        clear_btn.pack(anchor='e', pady=(5, 0))
        
        # 状态栏
        self.status_label = ttk.Label(self.root, text="就绪", relief='sunken')
        self.status_label.pack(side='bottom', fill='x')
    
    def toggle_topmost(self):
        """切换窗口置顶状态"""
        topmost = self.topmost_var.get()
        
        if self.window_controller.set_window_topmost(self.root, topmost):
            status = "已开启" if topmost else "已关闭"
            self.update_status(f"窗口置顶 {status}")
        else:
            self.update_status("设置窗口置顶失败")
            # 还原复选框状态
            self.topmost_var.set(not topmost)
    
    def update_alpha(self, value):
        """更新窗口透明度"""
        try:
            alpha = float(value)
            self.root.attributes('-alpha', alpha)
            self.alpha_label.config(text=f"{int(alpha*100)}%")
        except Exception as e:
            print(f"设置透明度失败: {e}")
    
    def update_region_mode(self):
        """更新区域识别模式"""
        mode = self.region_mode_var.get()
        
        if mode == "fullscreen":
            self.full_screen_mode = True
            self.selected_region = None
            self.select_region_btn.config(state='disabled')
            self.preview_region_btn.config(state='disabled')
            self.region_info_label.config(text="当前：全屏识别")
        else:
            self.full_screen_mode = False
            self.select_region_btn.config(state='normal')
            if self.selected_region:
                self.preview_region_btn.config(state='normal')
            self.update_region_info()
    
    def start_region_selection(self):
        """开始区域选择"""
        self.update_status("请在屏幕上拖拽选择识别区域...")
        
        # 临时取消置顶以便选择
        was_topmost = self.window_controller.is_topmost
        if was_topmost:
            self.window_controller.set_window_topmost(self.root, False)
        
        # 最小化窗口
        self.root.withdraw()
        
        def on_region_selected(region):
            # 恢复窗口
            self.root.deiconify()
            
            # 恢复置顶状态
            if was_topmost:
                self.window_controller.set_window_topmost(self.root, True)
            
            if region and region[2] > 10 and region[3] > 10:  # 确保区域足够大
                self.selected_region = region
                self.preview_region_btn.config(state='normal')
                self.update_region_info()
                self.update_status("区域选择完成")
            else:
                self.update_status("区域选择已取消或区域过小")
        
        # 延迟启动选择器，确保窗口隐藏完成
        self.root.after(100, lambda: self.region_selector.select_region(on_region_selected))
    
    def preview_selected_region(self):
        """预览选中的区域"""
        if not self.selected_region:
            messagebox.showwarning("警告", "尚未选择区域")
            return
        
        try:
            # 截取选定区域
            screenshot = self.capture_region(self.selected_region)
            
            # 创建预览窗口
            preview_window = tk.Toplevel(self.root)
            preview_window.title("区域预览")
            preview_window.attributes('-topmost', True)
            
            # 调整图片大小以适应显示
            img = screenshot.copy()
            max_size = 600
            if img.width > max_size or img.height > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # 显示图片
            photo = ImageTk.PhotoImage(img)
            label = ttk.Label(preview_window, image=photo)
            label.image = photo  # 保持引用
            label.pack(padx=10, pady=10)
            
            # 信息标签
            info_text = f"区域: {self.selected_region[0]},{self.selected_region[1]} - {self.selected_region[0]+self.selected_region[2]},{self.selected_region[1]+self.selected_region[3]}"
            info_text += f"\n大小: {self.selected_region[2]}x{self.selected_region[3]}"
            info_label = ttk.Label(preview_window, text=info_text)
            info_label.pack(pady=(0, 10))
            
            # 关闭按钮
            ttk.Button(preview_window, text="关闭", command=preview_window.destroy).pack(pady=(0, 10))
            
        except Exception as e:
            messagebox.showerror("错误", f"预览失败: {e}")
    
    def update_region_info(self):
        """更新区域信息显示"""
        if self.selected_region:
            x, y, w, h = self.selected_region
            info_text = f"当前：区域识别 ({x},{y}) 大小 {w}x{h}"
            self.region_info_label.config(text=info_text)
        else:
            self.region_info_label.config(text="当前：区域识别 (未选择区域)")
    
    def capture_region(self, region=None):
        """截取指定区域的屏幕"""
        try:
            with mss.mss() as sct:
                if region:
                    # 截取指定区域
                    monitor = {
                        "top": region[1],
                        "left": region[0], 
                        "width": region[2],
                        "height": region[3]
                    }
                else:
                    # 截取全屏
                    monitor = sct.monitors[1]  # 主显示器
                
                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                return img
        except Exception as e:
            print(f"截屏失败: {e}")
            return None
    
    def manual_recognition(self):
        """手动识别"""
        if not self.validate_config():
            return
        
        self.update_status("正在截图和识别...")
        
        # 在新线程中执行识别
        def recognize():
            try:
                # 根据模式截取屏幕
                if self.full_screen_mode:
                    screenshot = self.capture_region()
                else:
                    if not self.selected_region:
                        self.root.after(0, lambda: messagebox.showwarning("警告", "请先选择识别区域"))
                        return
                    screenshot = self.capture_region(self.selected_region)
                
                if screenshot:
                    result = self.analyze_image(screenshot)
                    self.root.after(0, lambda: self.display_result(f"手动识别结果:\n{result}"))
                    self.root.after(0, lambda: self.update_status("手动识别完成"))
                else:
                    self.root.after(0, lambda: self.update_status("截图失败"))
                    
            except Exception as e:
                self.root.after(0, lambda: self.display_result(f"识别出错: {e}"))
                self.root.after(0, lambda: self.update_status("识别失败"))
        
        threading.Thread(target=recognize, daemon=True).start()
    
    # 继续原有的其他方法...
    def load_config(self):
        """加载配置"""
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def save_config(self):
        """保存配置"""
        config = {
            'api_key': self.api_key_var.get(),
            'base_url': self.base_url_var.get(),
            'model': self.model_var.get(),
            'game_prompt': self.game_prompt_var.get(),
            'topmost': self.topmost_var.get(),
            'alpha': self.alpha_var.get(),
            'region_mode': self.region_mode_var.get(),
            'selected_region': self.selected_region
        }
        
        try:
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self.update_status("配置已保存")
            self.config = config
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {e}")
    
    def load_settings(self):
        """加载保存的设置"""
        if 'topmost' in self.config:
            self.topmost_var.set(self.config['topmost'])
            if self.config['topmost']:
                self.toggle_topmost()
        
        if 'alpha' in self.config:
            self.alpha_var.set(self.config['alpha'])
            self.update_alpha(self.config['alpha'])
        
        if 'region_mode' in self.config:
            self.region_mode_var.set(self.config['region_mode'])
            self.update_region_mode()
        
        if 'selected_region' in self.config and self.config['selected_region']:
            self.selected_region = self.config['selected_region']
            if not self.full_screen_mode:
                self.preview_region_btn.config(state='normal')
                self.update_region_info()
    
    def validate_config(self):
        """验证配置"""
        if not self.api_key_var.get().strip():
            messagebox.showerror("配置错误", "请先配置OpenAI API Key")
            return False
        return True
    
    def analyze_image(self, image):
        """分析图像"""
        try:
            # 转换图像为base64
            from io import BytesIO
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            # 准备API请求
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key_var.get()}"
            }
            
            data = {
                "model": self.model_var.get(),
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": self.game_prompt_var.get()
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 500
            }
            
            # 发送请求
            response = requests.post(
                f"{self.base_url_var.get()}/chat/completions",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"API请求失败: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"分析失败: {e}"
    
    def test_api(self):
        """测试API连接"""
        if not self.validate_config():
            return
            
        self.update_status("正在测试API连接...")
        
        def test():
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key_var.get()}"
                }
                
                response = requests.get(
                    f"{self.base_url_var.get()}/models",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.root.after(0, lambda: self.update_status("API连接成功"))
                    self.root.after(0, lambda: self.display_result("✅ API测试成功，连接正常"))
                else:
                    self.root.after(0, lambda: self.update_status("API连接失败"))
                    self.root.after(0, lambda: self.display_result(f"❌ API测试失败: {response.status_code}"))
                    
            except Exception as e:
                self.root.after(0, lambda: self.update_status("API测试失败"))
                self.root.after(0, lambda: self.display_result(f"❌ API测试出错: {e}"))
        
        threading.Thread(target=test, daemon=True).start()
    
    def toggle_monitoring(self):
        """切换监控状态"""
        if not self.monitoring:
            if not self.validate_config():
                return
            self.start_monitoring()
        else:
            self.stop_monitoring()
    
    def start_monitoring(self):
        """开始监控"""
        self.monitoring = True
        self.start_btn.config(text="⏹️ 停止监控")
        self.update_status("开始监控游戏画面...")
        
        def monitor():
            while self.monitoring:
                try:
                    # 根据模式截取屏幕
                    if self.full_screen_mode:
                        screenshot = self.capture_region()
                    else:
                        if not self.selected_region:
                            self.root.after(0, lambda: self.display_result("⚠️ 请先选择识别区域"))
                            break
                        screenshot = self.capture_region(self.selected_region)
                    
                    if screenshot:
                        result = self.analyze_image(screenshot)
                        self.root.after(0, lambda r=result: self.display_result(f"🤖 AI建议:\n{r}\n{'-'*50}"))
                    
                    # 等待5秒或直到停止监控
                    for _ in range(50):
                        if not self.monitoring:
                            break
                        time.sleep(0.1)
                        
                except Exception as e:
                    self.root.after(0, lambda e=e: self.display_result(f"监控出错: {e}"))
                    break
            
            # 监控结束
            self.root.after(0, self.stop_monitoring)
        
        threading.Thread(target=monitor, daemon=True).start()
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        self.start_btn.config(text="🎮 开始监控")
        self.update_status("监控已停止")
    
    def display_result(self, text):
        """显示结果"""
        self.result_text.insert(tk.END, f"\n[{time.strftime('%H:%M:%S')}] {text}\n")
        self.result_text.see(tk.END)
    
    def clear_results(self):
        """清除结果"""
        self.result_text.delete(1.0, tk.END)
        self.update_status("结果已清除")
    
    def update_status(self, text):
        """更新状态"""
        self.status_label.config(text=text)

def main():
    """主函数"""
    root = tk.Tk()
    
    # 设置主题样式
    try:
        style = ttk.Style()
        # 尝试使用现代主题
        available_themes = style.theme_names()
        if 'winnative' in available_themes:
            style.theme_use('winnative')
        elif 'clam' in available_themes:
            style.theme_use('clam')
        
        # 自定义按钮样式
        style.configure('Accent.TButton', foreground='white')
        
    except Exception as e:
        print(f"设置主题失败: {e}")
    
    app = EnhancedAIGameAssistant(root)
    
    # 程序退出时保存配置
    def on_closing():
        app.monitoring = False  # 停止监控
        app.save_config()  # 保存配置
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
