import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import time
import json
import os
import base64
import requests
from datetime import datetime
import pyautogui
from PIL import Image, ImageTk
import random
import io

class GameAIAssistant:
    def __init__(self, root):
        self.root = root
        self.root.title("AI游戏助手 v1.0")
        self.root.geometry("800x700")
        
        # 配置文件路径
        self.config_file = "config.json"
        self.diary_folder = "game_diaries"
        
        # 确保日记文件夹存在
        os.makedirs(self.diary_folder, exist_ok=True)
        
        # 加载配置
        self.config = self.load_config()
        
        # 运行状态
        self.is_monitoring = False
        self.last_comment_time = time.time()
        
        # 创建UI
        self.create_ui()
        
        # 启动监控线程
        self.monitor_thread = None
        
    def load_config(self):
        """加载配置文件"""
        default_config = {
            "openrouter_api_key": "",
            "current_model": "openai/gpt-4-vision-preview",
            "ai_personality": "你是一个幽默风趣的游戏解说员，会对游戏剧情和玩家操作进行吐槽和点评。保持轻松愉快的语调，偶尔开点小玩笑。",
            "comment_frequency": {
                "random_probability": 15,  # 15%概率主动吐槽
                "silence_timeout": 30      # 30秒无对话时主动发言
            },
            "models": [
                "openai/gpt-4-vision-preview",
                "openai/gpt-4o",
                "anthropic/claude-3-sonnet",
                "google/gemini-pro-vision"
            ]
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并默认配置和加载的配置
                    default_config.update(loaded_config)
            except:
                pass
        
        return default_config
    
    def save_config(self):
        """保存配置文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def create_ui(self):
        """创建用户界面"""
        # 创建笔记本控件（标签页）
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 主界面标签页
        main_frame = ttk.Frame(notebook)
        notebook.add(main_frame, text="主界面")
        
        # 配置标签页
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="配置")
        
        # 日记标签页
        diary_frame = ttk.Frame(notebook)
        notebook.add(diary_frame, text="游戏日记")
        
        self.create_main_interface(main_frame)
        self.create_config_interface(config_frame)
        self.create_diary_interface(diary_frame)
    
    def create_main_interface(self, parent):
        """创建主界面"""
        # 控制区域
        control_frame = ttk.LabelFrame(parent, text="控制面板", padding=10)
        control_frame.pack(fill='x', padx=5, pady=5)
        
        # 开始/停止按钮
        self.start_btn = ttk.Button(control_frame, text="开始监控", command=self.toggle_monitoring)
        self.start_btn.pack(side='left', padx=5)
        
        # 手动截图分析按钮
        ttk.Button(control_frame, text="立即分析屏幕", command=self.manual_analyze).pack(side='left', padx=5)
        
        # 状态标签
        self.status_label = ttk.Label(control_frame, text="状态: 未启动")
        self.status_label.pack(side='right', padx=5)
        
        # 聊天区域
        chat_frame = ttk.LabelFrame(parent, text="AI对话", padding=10)
        chat_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 对话显示区
        self.chat_display = scrolledtext.ScrolledText(chat_frame, height=15, state='disabled')
        self.chat_display.pack(fill='both', expand=True, pady=(0, 10))
        
        # 输入区域
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill='x')
        
        self.user_input = ttk.Entry(input_frame)
        self.user_input.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self.user_input.bind('<Return>', self.send_message)
        
        ttk.Button(input_frame, text="发送", command=self.send_message).pack(side='right')
    
    def create_config_interface(self, parent):
        """创建配置界面"""
        # API配置
        api_frame = ttk.LabelFrame(parent, text="API配置", padding=10)
        api_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(api_frame, text="OpenRouter API Key:").pack(anchor='w')
        self.api_key_entry = ttk.Entry(api_frame, width=60, show="*")
        self.api_key_entry.pack(fill='x', pady=(0, 10))
        self.api_key_entry.insert(0, self.config.get("openrouter_api_key", ""))
        
        ttk.Label(api_frame, text="选择模型:").pack(anchor='w')
        self.model_combo = ttk.Combobox(api_frame, values=self.config["models"])
        self.model_combo.pack(fill='x', pady=(0, 10))
        self.model_combo.set(self.config.get("current_model", ""))
        
        # AI人设配置
        personality_frame = ttk.LabelFrame(parent, text="AI人设配置", padding=10)
        personality_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        ttk.Label(personality_frame, text="AI人设提示词:").pack(anchor='w')
        self.personality_text = scrolledtext.ScrolledText(personality_frame, height=8)
        self.personality_text.pack(fill='both', expand=True, pady=(0, 10))
        self.personality_text.insert('1.0', self.config.get("ai_personality", ""))
        
        # 频率配置
        freq_frame = ttk.LabelFrame(parent, text="吐槽频率配置", padding=10)
        freq_frame.pack(fill='x', padx=5, pady=5)
        
        # 随机概率
        prob_frame = ttk.Frame(freq_frame)
        prob_frame.pack(fill='x', pady=5)
        ttk.Label(prob_frame, text="随机吐槽概率 (%):").pack(side='left')
        self.prob_scale = ttk.Scale(prob_frame, from_=0, to=100, orient='horizontal')
        self.prob_scale.pack(side='right', fill='x', expand=True, padx=(10, 0))
        self.prob_scale.set(self.config["comment_frequency"]["random_probability"])
        self.prob_value = ttk.Label(prob_frame, text=f"{self.config['comment_frequency']['random_probability']}%")
        self.prob_value.pack(side='right')
        self.prob_scale.configure(command=self.update_prob_label)
        
        # 静默超时
        timeout_frame = ttk.Frame(freq_frame)
        timeout_frame.pack(fill='x', pady=5)
        ttk.Label(timeout_frame, text="静默超时 (秒):").pack(side='left')
        self.timeout_scale = ttk.Scale(timeout_frame, from_=10, to=120, orient='horizontal')
        self.timeout_scale.pack(side='right', fill='x', expand=True, padx=(10, 0))
        self.timeout_scale.set(self.config["comment_frequency"]["silence_timeout"])
        self.timeout_value = ttk.Label(timeout_frame, text=f"{self.config['comment_frequency']['silence_timeout']}s")
        self.timeout_value.pack(side='right')
        self.timeout_scale.configure(command=self.update_timeout_label)
        
        # 保存按钮
        ttk.Button(parent, text="保存配置", command=self.save_settings).pack(pady=10)
    
    def create_diary_interface(self, parent):
        """创建日记界面"""
        # 日记列表
        list_frame = ttk.LabelFrame(parent, text="日记列表", padding=10)
        list_frame.pack(fill='x', padx=5, pady=5)
        
        self.diary_listbox = tk.Listbox(list_frame, height=6)
        self.diary_listbox.pack(fill='x', pady=(0, 5))
        self.diary_listbox.bind('<Double-1>', self.load_diary)
        
        # 按钮区域
        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(fill='x')
        ttk.Button(btn_frame, text="新建日记", command=self.new_diary).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="刷新列表", command=self.refresh_diary_list).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="导出日记", command=self.export_diary).pack(side='left', padx=5)
        
        # 日记编辑区域
        edit_frame = ttk.LabelFrame(parent, text="日记内容", padding=10)
        edit_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 日记标题
        title_frame = ttk.Frame(edit_frame)
        title_frame.pack(fill='x', pady=(0, 5))
        ttk.Label(title_frame, text="标题:").pack(side='left')
        self.diary_title = ttk.Entry(title_frame)
        self.diary_title.pack(side='left', fill='x', expand=True, padx=(5, 0))
        
        # 日记内容
        self.diary_content = scrolledtext.ScrolledText(edit_frame, height=15)
        self.diary_content.pack(fill='both', expand=True, pady=(0, 5))
        
        # 保存按钮
        ttk.Button(edit_frame, text="保存日记", command=self.save_diary).pack(anchor='e')
        
        # 初始化日记列表
        self.refresh_diary_list()
    
    def update_prob_label(self, value):
        """更新概率标签"""
        self.prob_value.config(text=f"{int(float(value))}%")
    
    def update_timeout_label(self, value):
        """更新超时标签"""
        self.timeout_value.config(text=f"{int(float(value))}s")
    
    def save_settings(self):
        """保存设置"""
        self.config["openrouter_api_key"] = self.api_key_entry.get()
        self.config["current_model"] = self.model_combo.get()
        self.config["ai_personality"] = self.personality_text.get('1.0', 'end-1c')
        self.config["comment_frequency"]["random_probability"] = int(self.prob_scale.get())
        self.config["comment_frequency"]["silence_timeout"] = int(self.timeout_scale.get())
        
        self.save_config()
        messagebox.showinfo("成功", "配置已保存!")
    
    def toggle_monitoring(self):
        """切换监控状态"""
        if not self.is_monitoring:
            if not self.config.get("openrouter_api_key"):
                messagebox.showerror("错误", "请先配置API Key!")
                return
            
            self.is_monitoring = True
            self.start_btn.config(text="停止监控")
            self.status_label.config(text="状态: 监控中...")
            
            # 启动监控线程
            self.monitor_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
            self.monitor_thread.start()
            
            self.add_chat_message("系统", "AI游戏助手已启动!", "system")
        else:
            self.is_monitoring = False
            self.start_btn.config(text="开始监控")
            self.status_label.config(text="状态: 已停止")
            self.add_chat_message("系统", "AI游戏助手已停止!", "system")
    
    def monitoring_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                current_time = time.time()
                
                # 检查是否需要主动发言
                should_comment = False
                
                # 随机概率检查
                if random.randint(1, 100) <= self.config["comment_frequency"]["random_probability"]:
                    should_comment = True
                
                # 静默超时检查
                if current_time - self.last_comment_time >= self.config["comment_frequency"]["silence_timeout"]:
                    should_comment = True
                
                if should_comment:
                    self.analyze_screen(auto_comment=True)
                    self.last_comment_time = current_time
                
                time.sleep(5)  # 每5秒检查一次
                
            except Exception as e:
                print(f"监控循环错误: {e}")
                time.sleep(5)
    
    def manual_analyze(self):
        """手动分析屏幕"""
        self.analyze_screen(auto_comment=False)
    
    def analyze_screen(self, auto_comment=True):
        """分析屏幕内容"""
        try:
            # 截图
            screenshot = pyautogui.screenshot()
            
            # 压缩图片以减少API调用成本
            screenshot = screenshot.resize((800, 600), Image.Resampling.LANCZOS)
            
            # 转换为base64
            buffered = io.BytesIO()
            screenshot.save(buffered, format="PNG")
            image_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            # 构建prompt
            if auto_comment:
                prompt = f"{self.config['ai_personality']}\n\n请分析这个游戏画面，并进行简短的吐槽或点评（1-2句话即可）。"
            else:
                prompt = f"{self.config['ai_personality']}\n\n请详细分析这个游戏画面，描述你看到的内容和你的想法。"
            
            # 调用API
            response = self.call_openrouter_api(prompt, image_base64)
            
            if response:
                message_type = "auto" if auto_comment else "analysis"
                self.add_chat_message("AI助手", response, message_type)
                
                # 自动保存到日记
                self.auto_save_to_diary(f"AI分析: {response}")
                
        except Exception as e:
            self.add_chat_message("系统", f"分析失败: {str(e)}", "error")
    
    def call_openrouter_api(self, prompt, image_base64=None):
        """调用OpenRouter API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.config['openrouter_api_key']}",
                "Content-Type": "application/json"
            }
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
            
            if image_base64:
                messages[0]["content"].append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_base64}"}
                })
            
            data = {
                "model": self.config["current_model"],
                "messages": messages,
                "max_tokens": 500
            }
            
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                                   headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return f"API调用失败: {response.status_code}"
                
        except Exception as e:
            return f"API调用出错: {str(e)}"
    
    def send_message(self, event=None):
        """发送用户消息"""
        message = self.user_input.get().strip()
        if not message:
            return
        
        self.user_input.delete(0, tk.END)
        self.add_chat_message("用户", message, "user")
        
        # 重置最后发言时间
        self.last_comment_time = time.time()
        
        # 在后台处理AI回复
        threading.Thread(target=self.process_user_message, args=(message,), daemon=True).start()
    
    def process_user_message(self, message):
        """处理用户消息"""
        try:
            # 构建上下文prompt
            prompt = f"{self.config['ai_personality']}\n\n用户说: {message}\n\n请回复用户。如果用户询问游戏相关问题，可以要求截图分析。"
            
            response = self.call_openrouter_api(prompt)
            
            if response:
                self.add_chat_message("AI助手", response, "ai")
                
                # 自动保存对话到日记
                self.auto_save_to_diary(f"用户: {message}\nAI: {response}")
                
        except Exception as e:
            self.add_chat_message("系统", f"处理消息失败: {str(e)}", "error")
    
    def add_chat_message(self, sender, message, msg_type):
        """添加聊天消息"""
        self.chat_display.config(state='normal')
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 根据消息类型设置颜色
        if msg_type == "user":
            color = "blue"
        elif msg_type == "ai" or msg_type == "auto":
            color = "green"
        elif msg_type == "system":
            color = "gray"
        elif msg_type == "error":
            color = "red"
        else:
            color = "black"
        
        self.chat_display.insert(tk.END, f"[{timestamp}] {sender}: {message}\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')
    
    def refresh_diary_list(self):
        """刷新日记列表"""
        self.diary_listbox.delete(0, tk.END)
        if os.path.exists(self.diary_folder):
            for filename in os.listdir(self.diary_folder):
                if filename.endswith('.txt'):
                    self.diary_listbox.insert(tk.END, filename[:-4])  # 去掉.txt后缀
    
    def new_diary(self):
        """新建日记"""
        today = datetime.now().strftime("%Y-%m-%d")
        self.diary_title.delete(0, tk.END)
        self.diary_title.insert(0, f"游戏日记_{today}")
        self.diary_content.delete('1.0', tk.END)
        self.diary_content.insert('1.0', f"日期: {today}\n\n")
    
    def load_diary(self, event=None):
        """加载选中的日记"""
        selection = self.diary_listbox.curselection()
        if not selection:
            return
        
        filename = self.diary_listbox.get(selection[0]) + '.txt'
        filepath = os.path.join(self.diary_folder, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                # 分离标题和内容
                lines = content.split('\n', 1)
                title = lines[0].replace('标题: ', '') if lines else filename[:-4]
                content = lines[1] if len(lines) > 1 else content
                
                self.diary_title.delete(0, tk.END)
                self.diary_title.insert(0, title)
                self.diary_content.delete('1.0', tk.END)
                self.diary_content.insert('1.0', content)
        except Exception as e:
            messagebox.showerror("错误", f"加载日记失败: {str(e)}")
    
    def save_diary(self):
        """保存日记"""
        title = self.diary_title.get().strip()
        content = self.diary_content.get('1.0', 'end-1c')
        
        if not title:
            messagebox.showerror("错误", "请输入日记标题!")
            return
        
        filename = f"{title}.txt"
        filepath = os.path.join(self.diary_folder, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"标题: {title}\n{content}")
            messagebox.showinfo("成功", "日记已保存!")
            self.refresh_diary_list()
        except Exception as e:
            messagebox.showerror("错误", f"保存日记失败: {str(e)}")
    
    def auto_save_to_diary(self, content):
        """自动保存内容到今日日记"""
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"游戏日记_{today}.txt"
        filepath = os.path.join(self.diary_folder, filename)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"\n[{timestamp}] {content}\n"
        
        try:
            # 如果文件存在，追加内容；否则创建新文件
            mode = 'a' if os.path.exists(filepath) else 'w'
            with open(filepath, mode, encoding='utf-8') as f:
                if mode == 'w':
                    f.write(f"标题: 游戏日记_{today}\n日期: {today}\n\n")
                f.write(entry)
        except Exception as e:
            print(f"自动保存日记失败: {e}")
    
    def export_diary(self):
        """导出日记"""
        selection = self.diary_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要导出的日记!")
            return
        
        filename = self.diary_listbox.get(selection[0])
        source_path = os.path.join(self.diary_folder, f"{filename}.txt")
        
        export_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("Markdown文件", "*.md"), ("所有文件", "*.*")],
            initialvalue=f"{filename}.txt"
        )
        
        if export_path:
            try:
                with open(source_path, 'r', encoding='utf-8') as src:
                    content = src.read()
                with open(export_path, 'w', encoding='utf-8') as dst:
                    dst.write(content)
                messagebox.showinfo("成功", "日记导出成功!")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {str(e)}")

def main():
    root = tk.Tk()
    app = GameAIAssistant(root)
    root.mainloop()

if __name__ == "__main__":
    main()
