# -*- coding: utf-8 -*-
"""
AI提示词调试工具
用于快速测试不同的System提示词和User输入的效果
"""

import json
import logging
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import configparser
import os
import traceback
from datetime import datetime
import requests
from enum import Enum
from pydantic import BaseModel, ConfigDict
import threading
import time
import base64
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ===== PDF处理函数 =====

def pdf_to_images(pdf_path: str) -> list[str]:
    """将PDF转换为图片的base64编码列表
    
    使用 PyMuPDF (fitz) 进行转换，原生支持中文路径，无需外部依赖
    
    :param pdf_path: PDF文件路径
    :return: 图片base64编码列表
    """
    try:
        import fitz  # PyMuPDF
        from PIL import Image
        import io
        
        # 打开PDF文档
        doc = fitz.open(pdf_path)
        base64_images = []
        
        # 遍历每一页
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # 渲染为图片 (matrix参数控制分辨率, 2倍约等于200DPI)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            
            # 转换为PIL Image对象
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # 压缩图片以减小大小
            # 如果图片太大，缩小尺寸
            max_size = 2048
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # 转换为base64
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            base64_images.append(img_base64)
        
        # 关闭文档
        doc.close()
        return base64_images
        
    except ImportError:
        raise ImportError("需要安装 PyMuPDF 和 Pillow 库。请运行: pip install PyMuPDF Pillow")
    except Exception as e:
        raise Exception(f"PDF转换失败: {str(e)}")

# ===== 从example.py复制的必要类定义 =====

class LlmMessageRole(Enum):
    USER = 'user'
    ASSISTANT = 'assistant'
    SYSTEM = 'system'


class LlmMessage(BaseModel):
    role: LlmMessageRole
    content: str | list[dict]

    model_config = ConfigDict(
        json_encoders={
            LlmMessageRole: lambda v: v.value,
        },
    )


class _Model(BaseModel):
    model: str
    provider: str


class LlmModel(Enum):
    DEEPSEEK_V3 = _Model(model="deepseek-chat", provider="deepseek")
    DEEPSEEK_R1 = _Model(model="DeepSeek-R1", provider="deepseek")
    QWEN_PLUS = _Model(model="qwen-plus", provider="qwen")
    QWEN_235B = _Model(model="qwen3-235b-a22b-instruct-2507", provider="qwen")
    DOUBAO_1_6 = _Model(model="doubao-seed-1-6-250615", provider="doubao")
    DOUBAO_1_5 = _Model(model="doubao-1-5-pro-32k-250115", provider="doubao")
    DOUBAO_IMAGE_1_6 = _Model(model="doubao-seed-1-6-251015", provider="doubao")
    DOUBAO_1_6_FLASH = _Model(model="doubao-seed-1-6-flash-250828", provider="doubao")


# ===== 配置管理 =====

class Config:
    """配置管理类"""
    def __init__(self, config_file='debug_tool_config.ini'):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            self.config.read(self.config_file, encoding='utf-8')
        else:
            # 创建默认配置
            self.config['DEFAULT'] = {
                'api_url': '',  # 留空，由用户配置
                'application': '',
                'api_key': '',
                'timeout': '60',
                'response_format': 'text',
                'model': 'QWEN_235B',
                'temperature': '0.7',
                'use_stream': 'true'
            }
            self.save_config()
    
    def save_config(self):
        """保存配置文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            self.config.write(f)
    
    def get(self, key, default=None):
        """获取配置值"""
        return self.config['DEFAULT'].get(key, default)
    
    def set(self, key, value):
        """设置配置值"""
        self.config['DEFAULT'][key] = str(value)
        self.save_config()


# ===== AI调用函数 =====

def call_ai(api_url: str, application: str, messages: list[LlmMessage], 
            model: LlmModel, api_key: str = None, timeout: int = 60, **kwargs) -> str:
    """调用AI接口（非流式）
    
    :param api_url: API地址
    :param application: 应用标识
    :param messages: 消息列表
    :param model: 模型
    :param api_key: API密钥（可选，用于OpenAI等第三方API）
    :param timeout: 超时时间
    :param kwargs: 其他参数
    :return: AI回复内容
    """
    # 构建请求数据（与example.py保持一致）
    requests_data = {
        "messages": [m.model_dump(mode='json') for m in messages],
        "model": model.value.model,
        **kwargs
    }
    payload = {
        "application": application,
        "provider": model.value.provider,
        "requests_data": requests_data,
    }
    
    logging.info(f"AI请求数据: {payload}")
    
    # 准备请求参数
    request_kwargs = {
        "json": payload,
        "timeout": timeout
    }
    
    # 如果提供了API Key，添加到请求头（用于OpenAI等第三方API）
    if api_key:
        request_kwargs["headers"] = {'Authorization': f'Bearer {api_key}'}
    
    # 发送请求（与example.py保持一致的调用方式）
    response = requests.request("POST", api_url, **request_kwargs)
    
    logging.info(f"AI响应数据: {response.text}")
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']


def call_ai_stream(api_url: str, application: str, messages: list[LlmMessage], 
                   model: LlmModel, api_key: str = None, timeout: int = 60, 
                   callback=None, **kwargs):
    """调用AI接口（流式响应）
    
    :param api_url: API地址
    :param application: 应用标识
    :param messages: 消息列表
    :param model: 模型
    :param api_key: API密钥（可选，用于OpenAI等第三方API）
    :param timeout: 超时时间
    :param callback: 回调函数，用于接收流式数据片段 callback(chunk_text)
    :param kwargs: 其他参数
    :return: 完整的AI回复内容
    """
    # 构建请求数据
    requests_data = {
        "messages": [m.model_dump(mode='json') for m in messages],
        "model": model.value.model,
        "stream": True,  # 启用流式响应
        **kwargs
    }
    payload = {
        "application": application,
        "provider": model.value.provider,
        "requests_data": requests_data,
    }
    
    logging.info(f"AI流式请求数据: {payload}")
    
    # 准备请求参数
    request_kwargs = {
        "json": payload,
        "timeout": timeout,
        "stream": True  # 启用流式响应
    }
    
    # 如果提供了API Key，添加到请求头
    if api_key:
        request_kwargs["headers"] = {'Authorization': f'Bearer {api_key}'}
    
    # 发送请求
    response = requests.request("POST", api_url, **request_kwargs)
    response.raise_for_status()
    
    # 处理流式响应
    full_content = ""
    for line in response.iter_lines():
        if not line:
            continue
            
        line = line.decode('utf-8')
        
        # 跳过事件类型行
        if line.startswith('event:'):
            continue
        
        # 处理数据行
        if line.startswith('data:'):
            data_str = line[5:].strip()
            
            # 检查是否是结束标记
            if data_str == '[DONE]':
                break
            
            try:
                data = json.loads(data_str)
                # 提取内容
                if 'choices' in data and len(data['choices']) > 0:
                    delta = data['choices'][0].get('delta', {})
                    content = delta.get('content', '')
                    
                    if content:
                        full_content += content
                        # 调用回调函数，实时传递内容片段
                        if callback:
                            callback(content)
            except json.JSONDecodeError as e:
                logging.warning(f"解析流式数据失败: {data_str}, 错误: {e}")
                continue
    
    logging.info(f"AI流式响应完成，总长度: {len(full_content)}")
    return full_content


# ===== GUI界面 =====

class AIDebugTool:
    """AI调试工具GUI"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("AI提示词调试工具")
        self.root.geometry("1200x800")
        
        # 加载配置
        self.config = Config()
        
        # 存储上传的PDF图片
        self.uploaded_images = []
        self.uploaded_pdf_name = None
        
        # 创建界面
        self.create_widgets()
        
        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        """创建界面组件"""
        
        # ===== 顶部配置区域 =====
        config_frame = ttk.LabelFrame(self.root, text="配置", padding=10)
        config_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # API地址
        ttk.Label(config_frame, text="API地址:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.api_url_var = tk.StringVar(value=self.config.get('api_url'))
        api_url_entry = ttk.Entry(config_frame, textvariable=self.api_url_var, width=50)
        api_url_entry.grid(row=0, column=1, columnspan=2, sticky=tk.W+tk.E, padx=5, pady=2)
        
        # API Key
        ttk.Label(config_frame, text="API Key:").grid(row=0, column=3, sticky=tk.W, padx=5, pady=2)
        self.api_key_var = tk.StringVar(value=self.config.get('api_key', ''))
        api_key_entry = ttk.Entry(config_frame, textvariable=self.api_key_var, width=30, show='*')
        api_key_entry.grid(row=0, column=4, sticky=tk.W+tk.E, padx=5, pady=2)
        
        # 应用标识
        ttk.Label(config_frame, text="应用标识:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.application_var = tk.StringVar(value=self.config.get('application'))
        app_entry = ttk.Entry(config_frame, textvariable=self.application_var, width=20)
        app_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # 模型选择
        ttk.Label(config_frame, text="选择模型:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)
        self.model_var = tk.StringVar()
        model_combo = ttk.Combobox(config_frame, textvariable=self.model_var, width=25, state='readonly')
        model_combo['values'] = [model.name for model in LlmModel]
        
        # 从配置读取上次选择的模型
        saved_model = self.config.get('model', 'QWEN_235B')
        try:
            # 尝试设置为保存的模型
            model_index = [model.name for model in LlmModel].index(saved_model)
            model_combo.current(model_index)
        except (ValueError, IndexError):
            # 如果保存的模型不存在，使用默认值
            model_combo.current(3)  # 默认选择 QWEN_235B
        
        model_combo.grid(row=1, column=3, sticky=tk.W, padx=5, pady=2)
        
        # 超时时间
        ttk.Label(config_frame, text="超时(秒):").grid(row=1, column=4, sticky=tk.W, padx=5, pady=2)
        self.timeout_var = tk.StringVar(value=self.config.get('timeout', '60'))
        timeout_entry = ttk.Entry(config_frame, textvariable=self.timeout_var, width=10)
        timeout_entry.grid(row=1, column=5, sticky=tk.W, padx=5, pady=2)
        
        # Temperature参数
        ttk.Label(config_frame, text="Temperature:").grid(row=1, column=6, sticky=tk.W, padx=5, pady=2)
        self.temperature_var = tk.StringVar(value=self.config.get('temperature', '0.7'))
        temperature_entry = ttk.Entry(config_frame, textvariable=self.temperature_var, width=8)
        temperature_entry.grid(row=1, column=7, sticky=tk.W, padx=5, pady=2)
        
        # Temperature说明
        temp_help = ttk.Label(
            config_frame, 
            text="(0-1, 越高越随机)",
            font=('Arial', 7),
            foreground='gray'
        )
        temp_help.grid(row=1, column=8, sticky=tk.W, padx=2, pady=2)
        
        # 流式响应选项
        ttk.Label(config_frame, text="流式响应:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.use_stream_var = tk.BooleanVar(value=self.config.get('use_stream', 'true').lower() == 'true')
        stream_check = ttk.Checkbutton(
            config_frame, 
            text="启用(实时显示,避免超时)",
            variable=self.use_stream_var
        )
        stream_check.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        # 响应格式
        ttk.Label(config_frame, text="响应格式:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        self.response_format_var = tk.StringVar(value=self.config.get('response_format', 'text'))
        response_format_combo = ttk.Combobox(
            config_frame, 
            textvariable=self.response_format_var, 
            width=20, 
            state='readonly'
        )
        response_format_combo['values'] = ['text', 'json_object']
        response_format_combo.grid(row=3, column=1, sticky=tk.W, padx=5, pady=2)
        
        # 响应格式说明
        format_help = ttk.Label(
            config_frame, 
            text="提示: 选择json_object时，需在System提示词中要求返回JSON格式",
            font=('Arial', 8),
            foreground='gray'
        )
        format_help.grid(row=3, column=2, columnspan=5, sticky=tk.W, padx=5, pady=2)
        
        # 保存配置按钮
        save_config_btn = ttk.Button(config_frame, text="保存配置", command=self.save_config)
        save_config_btn.grid(row=3, column=7, columnspan=2, padx=5, pady=2)
        
        # ===== 主要内容区域（分为左右两部分） =====
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # ===== 左侧输入区域 =====
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
        
        # System提示词
        system_frame = ttk.LabelFrame(left_frame, text="System提示词", padding=5)
        system_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.system_text = scrolledtext.ScrolledText(
            system_frame, 
            wrap=tk.WORD, 
            width=50, 
            height=12,
            font=('Consolas', 10)
        )
        self.system_text.pack(fill=tk.BOTH, expand=True)
        self.system_text.insert('1.0', '你是一个有帮助的AI助手。')
        
        # User输入
        user_frame = ttk.LabelFrame(left_frame, text="User输入", padding=5)
        user_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.user_text = scrolledtext.ScrolledText(
            user_frame, 
            wrap=tk.WORD, 
            width=50, 
            height=12,
            font=('Consolas', 10)
        )
        self.user_text.pack(fill=tk.BOTH, expand=True)
        self.user_text.insert('1.0', '你好，请介绍一下自己。')
        
        # 文件上传区域
        upload_frame = ttk.LabelFrame(left_frame, text="文件上传 (PDF)", padding=5)
        upload_frame.pack(fill=tk.X, pady=5)
        
        # 上传按钮和状态
        upload_btn_frame = ttk.Frame(upload_frame)
        upload_btn_frame.pack(fill=tk.X)
        
        self.upload_button = ttk.Button(
            upload_btn_frame,
            text="选择PDF文件",
            command=self.upload_pdf
        )
        self.upload_button.pack(side=tk.LEFT, padx=5)
        
        self.upload_status_label = ttk.Label(
            upload_btn_frame,
            text="未上传文件",
            foreground='gray'
        )
        self.upload_status_label.pack(side=tk.LEFT, padx=10)
        
        self.clear_upload_button = ttk.Button(
            upload_btn_frame,
            text="清除",
            command=self.clear_upload,
            state=tk.DISABLED
        )
        self.clear_upload_button.pack(side=tk.LEFT, padx=5)
        
        # 按钮区域
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        self.send_button = ttk.Button(
            button_frame, 
            text="发送请求", 
            command=self.send_request,
            style='Accent.TButton'
        )
        self.send_button.pack(side=tk.LEFT, padx=5)
        
        clear_button = ttk.Button(
            button_frame, 
            text="清空输出", 
            command=self.clear_output
        )
        clear_button.pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(button_frame, text="就绪", foreground='green')
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # ===== 右侧输出区域 =====
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=1)
        
        # AI响应输出
        output_frame = ttk.LabelFrame(right_frame, text="AI响应", padding=5)
        output_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.output_text = scrolledtext.ScrolledText(
            output_frame, 
            wrap=tk.WORD, 
            width=50, 
            height=25,
            font=('Consolas', 10),
            state=tk.DISABLED
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # 配置文本标签样式
        self.output_text.tag_config('timestamp', foreground='gray')
        self.output_text.tag_config('success', foreground='green')
        self.output_text.tag_config('error', foreground='red')
        self.output_text.tag_config('response', foreground='black')
        self.output_text.tag_config('info', foreground='blue')
        
        # 日志区域
        log_frame = ttk.LabelFrame(right_frame, text="请求日志", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            wrap=tk.WORD, 
            width=50, 
            height=10,
            font=('Consolas', 9),
            state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def save_config(self):
        """保存配置"""
        try:
            self.config.set('api_url', self.api_url_var.get())
            self.config.set('application', self.application_var.get())
            self.config.set('api_key', self.api_key_var.get())
            self.config.set('timeout', self.timeout_var.get())
            self.config.set('response_format', self.response_format_var.get())
            self.config.set('model', self.model_var.get())
            self.config.set('temperature', self.temperature_var.get())
            self.config.set('use_stream', 'true' if self.use_stream_var.get() else 'false')
            messagebox.showinfo("成功", "配置已保存！")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")
    
    def append_output(self, text, tag=None):
        """追加输出文本"""
        self.output_text.config(state=tk.NORMAL)
        if tag:
            self.output_text.insert(tk.END, text, tag)
        else:
            self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)
    
    def append_log(self, text):
        """追加日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, text + '\n')
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def clear_output(self):
        """清空输出"""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete('1.0', tk.END)
        self.output_text.config(state=tk.DISABLED)
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def upload_pdf(self):
        """上传PDF文件"""
        file_path = filedialog.askopenfilename(
            title="选择PDF文件",
            filetypes=[("PDF文件", "*.pdf"), ("所有文件", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            # 显示处理中状态
            self.upload_status_label.config(text="处理中...", foreground='orange')
            self.upload_button.config(state=tk.DISABLED)
            self.root.update()
            
            # 转换PDF为图片
            base64_images = pdf_to_images(file_path)
            
            # 保存结果
            self.uploaded_images = base64_images
            self.uploaded_pdf_name = Path(file_path).name
            
            # 更新UI状态
            status_text = f"已上传: {self.uploaded_pdf_name} ({len(base64_images)} 页)"
            self.upload_status_label.config(text=status_text, foreground='green')
            self.clear_upload_button.config(state=tk.NORMAL)
            
            messagebox.showinfo("成功", f"PDF已转换为 {len(base64_images)} 张图片")
            
        except Exception as e:
            error_msg = str(e)
            self.upload_status_label.config(text="上传失败", foreground='red')
            messagebox.showerror("错误", f"处理PDF失败:\n{error_msg}")
            self.uploaded_images = []
            self.uploaded_pdf_name = None
        
        finally:
            self.upload_button.config(state=tk.NORMAL)
    
    def clear_upload(self):
        """清除已上传的文件"""
        self.uploaded_images = []
        self.uploaded_pdf_name = None
        self.upload_status_label.config(text="未上传文件", foreground='gray')
        self.clear_upload_button.config(state=tk.DISABLED)
    
    def send_request(self):
        """发送AI请求"""
        # 禁用发送按钮
        self.send_button.config(state=tk.DISABLED)
        self.status_label.config(text="请求中...", foreground='orange')
        self.root.update()
        
        # 初始化计时变量
        self.request_start_time = time.time()
        self.first_chunk_time = None
        
        # 在单独的线程中执行请求,避免卡死界面
        thread = threading.Thread(target=self._send_request_thread, daemon=True)
        thread.start()
    
    def _stream_callback(self, chunk: str):
        """流式响应回调函数,在主线程中更新UI"""
        # 记录首字响应时间
        if self.first_chunk_time is None:
            self.first_chunk_time = time.time()
            first_chunk_delay = self.first_chunk_time - self.request_start_time
            
            def show_first_chunk_time():
                self.append_output(f"[首字响应: {first_chunk_delay:.2f}秒]\n", 'info')
            
            self.root.after(0, show_first_chunk_time)
        
        def update_ui():
            self.append_output(chunk, 'response')
        
        # 确保在主线程中更新UI
        self.root.after(0, update_ui)
    
    def _send_request_thread(self):
        """在线程中发送请求"""
        try:
            # 获取输入
            system_content = self.system_text.get('1.0', tk.END).strip()
            user_content = self.user_text.get('1.0', tk.END).strip()
            
            if not user_content:
                self.root.after(0, lambda: messagebox.showwarning("警告", "User输入不能为空！"))
                return
            
            # 构建消息
            messages = []
            if system_content:
                messages.append(LlmMessage(role=LlmMessageRole.SYSTEM, content=system_content))
            
            # 构建User消息内容
            if self.uploaded_images:
                # 如果有上传的PDF图片，使用多模态格式
                user_message_content = [
                    {
                        "type": "text",
                        "text": user_content
                    }
                ]
                
                # 添加所有PDF页面的图片
                for img_base64 in self.uploaded_images:
                    user_message_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{img_base64}"
                        }
                    })
                
                messages.append(LlmMessage(role=LlmMessageRole.USER, content=user_message_content))
            else:
                # 纯文本消息
                messages.append(LlmMessage(role=LlmMessageRole.USER, content=user_content))
            
            # 获取配置
            api_url = self.api_url_var.get()
            application = self.application_var.get()
            api_key = self.api_key_var.get().strip()
            model_name = self.model_var.get()
            model = LlmModel[model_name]
            timeout = int(self.timeout_var.get())
            response_format = self.response_format_var.get()
            use_stream = self.use_stream_var.get()
            
            # 记录请求信息
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.root.after(0, lambda: self.append_output(f"\n{'='*60}\n", 'timestamp'))
            self.root.after(0, lambda: self.append_output(f"[{timestamp}] ", 'timestamp'))
            self.root.after(0, lambda: self.append_output(f"请求模型: {model_name} ({'流式' if use_stream else '非流式'})\n", 'success'))
            
            # 如果有上传PDF，显示信息
            if self.uploaded_images:
                pdf_info = f"已附加PDF: {self.uploaded_pdf_name} ({len(self.uploaded_images)} 页)\n"
                self.root.after(0, lambda: self.append_output(pdf_info, 'info'))
            
            self.root.after(0, lambda: self.append_log(f"{'='*60}"))
            self.root.after(0, lambda: self.append_log(f"[{timestamp}] 开始请求"))
            self.root.after(0, lambda: self.append_log(f"模型: {model_name}"))
            self.root.after(0, lambda: self.append_log(f"API: {api_url}"))
            self.root.after(0, lambda: self.append_log(f"API Key: {'已设置' if api_key else '未设置'}"))
            self.root.after(0, lambda: self.append_log(f"响应格式: {response_format}"))
            self.root.after(0, lambda: self.append_log(f"Temperature: {self.temperature_var.get()}"))
            self.root.after(0, lambda: self.append_log(f"流式响应: {'启用' if use_stream else '禁用'}"))
            
            # 记录PDF信息
            if self.uploaded_images:
                self.root.after(0, lambda: self.append_log(f"PDF文件: {self.uploaded_pdf_name} ({len(self.uploaded_images)} 页)"))
            
            log_system = f"System: {system_content[:50]}..." if len(system_content) > 50 else f"System: {system_content}"
            log_user = f"User: {user_content[:50]}..." if len(user_content) > 50 else f"User: {user_content}"
            self.root.after(0, lambda: self.append_log(log_system))
            self.root.after(0, lambda: self.append_log(log_user))
            
            # 构建额外参数
            extra_kwargs = {}
            if response_format == 'json_object':
                extra_kwargs['response_format'] = {'type': 'json_object'}
            
            # 添加temperature参数
            try:
                temperature = float(self.temperature_var.get())
                if 0 <= temperature <= 2:  # OpenAI标准范围是0-2
                    extra_kwargs['temperature'] = temperature
                else:
                    self.root.after(0, lambda: self.append_log(f"警告: Temperature值 {temperature} 超出范围(0-2)，使用默认值"))
            except ValueError:
                self.root.after(0, lambda: self.append_log(f"警告: Temperature值格式错误，使用默认值"))
            
            # 显示响应标题
            self.root.after(0, lambda: self.append_output("响应内容:\n", 'success'))
            
            # 调用AI
            if use_stream:
                # 流式响应
                response = call_ai_stream(
                    api_url=api_url,
                    application=application,
                    messages=messages,
                    model=model,
                    api_key=api_key if api_key else None,
                    timeout=timeout,
                    callback=self._stream_callback,
                    **extra_kwargs
                )
            else:
                # 非流式响应
                response = call_ai(
                    api_url=api_url,
                    application=application,
                    messages=messages,
                    model=model,
                    api_key=api_key if api_key else None,
                    timeout=timeout,
                    **extra_kwargs
                )
                
                # 显示响应
                # 如果是JSON格式，尝试格式化显示
                if response_format == 'json_object':
                    try:
                        json_obj = json.loads(response)
                        formatted_response = json.dumps(json_obj, ensure_ascii=False, indent=2)
                        self.root.after(0, lambda: self.append_output(f"{formatted_response}\n", 'response'))
                    except:
                        # 如果解析失败，直接显示原文
                        self.root.after(0, lambda: self.append_output(f"{response}\n", 'response'))
                else:
                    self.root.after(0, lambda: self.append_output(f"{response}\n", 'response'))
            
            # 计算总用时
            total_time = time.time() - self.request_start_time
            
            # 记录成功
            response_len = len(response)
            self.root.after(0, lambda: self.append_output(f"\n[总用时: {total_time:.2f}秒]\n", 'info'))
            self.root.after(0, lambda: self.append_log(f"响应长度: {response_len} 字符"))
            self.root.after(0, lambda: self.append_log(f"总用时: {total_time:.2f}秒"))
            if use_stream and self.first_chunk_time is not None:
                first_chunk_delay = self.first_chunk_time - self.request_start_time
                self.root.after(0, lambda: self.append_log(f"首字响应: {first_chunk_delay:.2f}秒"))
            self.root.after(0, lambda: self.append_log("请求成功！"))
            self.root.after(0, lambda: self.status_label.config(text=f"请求成功 (用时{total_time:.2f}秒)", foreground='green'))
            
        except Exception as e:
            error_msg = traceback.format_exc()
            error_str = str(e)
            self.root.after(0, lambda: self.append_output(f"\n错误:\n{error_str}\n", 'error'))
            self.root.after(0, lambda: self.append_log(f"请求失败: {error_str}"))
            self.root.after(0, lambda: self.append_log(error_msg))
            self.root.after(0, lambda: self.status_label.config(text="请求失败", foreground='red'))
            self.root.after(0, lambda: messagebox.showerror("错误", f"请求失败:\n{error_str}"))
        
        finally:
            # 恢复发送按钮
            self.root.after(0, lambda: self.send_button.config(state=tk.NORMAL))
    
    def on_closing(self):
        """窗口关闭事件"""
        if messagebox.askokcancel("退出", "确定要退出吗？"):
            self.root.destroy()


# ===== 主程序入口 =====

def main():
    """主函数"""
    root = tk.Tk()
    app = AIDebugTool(root)
    root.mainloop()


if __name__ == '__main__':
    main()
