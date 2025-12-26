# AI调试工具 (AI Debug Tool)

一个用于快速测试不同的System提示词和User输入效果的图形化工具，支持多种AI模型和PDF文档分析。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)

## 功能特性

- ✅ **图形化界面**: 基于Tkinter的友好GUI，易于使用
- 🤖 **多模型支持**: 支持DeepSeek、通义千问、豆包等多种AI模型
- 📄 **PDF文档分析**: 上传PDF文件，自动转换为图片并发送给AI分析
- 🔄 **流式响应**: 支持流式和非流式两种响应模式，实时查看AI输出
- ⚙️ **灵活配置**: 支持自定义API地址、Temperature参数、超时时间等
- 📝 **JSON格式输出**: 支持结构化JSON响应格式
- 💾 **配置持久化**: 自动保存配置，下次使用无需重新设置
- 📊 **详细日志**: 实时显示请求日志和响应时间统计

## 系统要求

- Python 3.8 或更高版本
- Windows / Linux / macOS
- 如果需要使用PDF上传功能，需要安装Poppler（详见下方）

## 安装步骤

### 1. 克隆或下载项目

```bash
git clone <项目地址>
cd ai_debug_tool
```

或直接下载ZIP并解压。

### 2. 创建虚拟环境（推荐）

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装Python依赖

```bash
pip install -r requirements.txt
```

依赖包说明：
- `requests>=2.31.0` - HTTP请求库
- `pydantic>=2.0.0` - 数据验证和序列化
- `pdf2image>=1.16.0` - PDF转图片（仅PDF功能需要）
- `Pillow>=10.0.0` - 图像处理（仅PDF功能需要）

### 4. 安装Poppler（仅PDF功能需要）

**⚠️ 重要**: 如果您需要使用PDF上传功能，必须安装Poppler工具。pdf2image库依赖Poppler来转换PDF文件。

#### Windows系统

**方法一：手动安装（推荐）**

1. 下载Poppler for Windows: 
   - 访问 https://github.com/oschwartz10612/poppler-windows/releases
   - 下载最新的 `Release-xx.xx.x.zip` 文件

2. 解压到合适的目录，例如：
   ```
   C:\Program Files\poppler-24.08.0\
   ```

3. 将Poppler的bin目录添加到系统环境变量PATH：
   - 右键点击"此电脑" → "属性" → "高级系统设置"
   - 点击"环境变量"
   - 在"系统变量"中找到"Path"，点击"编辑"
   - 点击"新建"，添加路径：`C:\Program Files\poppler-24.08.0\Library\bin`
   - 点击"确定"保存

4. 重启命令行窗口，验证安装：
   ```bash
   pdftoppm -h
   ```
   如果显示帮助信息，说明安装成功。

**方法二：使用Conda安装**

如果您使用Anaconda或Miniconda：

```bash
conda install -c conda-forge poppler
```

#### Linux系统

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install poppler-utils

# CentOS/RHEL
sudo yum install poppler-utils

# Fedora
sudo dnf install poppler-utils

# Arch Linux
sudo pacman -S poppler
```

验证安装：
```bash
pdftoppm -h
```

#### macOS系统

使用Homebrew安装：

```bash
brew install poppler
```

验证安装：
```bash
pdftoppm -h
```

### 5. 验证安装

运行以下Python代码验证所有依赖是否正确安装：

```python
# 验证基本依赖
import requests
import pydantic
print("✅ 基本依赖安装成功")

# 验证PDF依赖
try:
    import pdf2image
    from PIL import Image
    print("✅ PDF处理依赖安装成功")
    
    # 测试Poppler
    pdf2image.convert_from_path('test.pdf', dpi=200)
    print("✅ Poppler安装成功")
except ImportError as e:
    print(f"⚠️ PDF依赖缺失: {e}")
except Exception as e:
    print(f"⚠️ Poppler未安装或配置不正确")
```

## 使用说明

### 启动程序

```bash
# 激活虚拟环境（如果使用）
# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

# 运行程序
python ai_debug_tool.py
```

或在Windows系统上双击 `run.bat` 文件。

### 基本配置

首次运行需要配置以下参数：

1. **API地址**: AI服务的API端点URL
2. **应用标识**: 您的应用标识符（Application ID）
3. **API Key**: API密钥（某些服务需要）
4. **选择模型**: 从下拉菜单选择要使用的AI模型
5. **超时时间**: 请求超时时间（秒），默认60秒
6. **Temperature**: 控制输出随机性，范围0-1，越高越随机
7. **流式响应**: 建议启用，可实时查看输出并避免超时
8. **响应格式**: 选择`text`或`json_object`

配置完成后点击"保存配置"按钮。

### 基本使用流程

1. **输入System提示词**（可选）：在左上方文本框输入系统提示词，定义AI的角色和行为
2. **输入User问题**：在左下方文本框输入您的问题或指令
3. **点击"发送请求"**：等待AI响应
4. **查看结果**：右侧上方显示AI响应内容，下方显示详细日志

### PDF上传功能

1. **选择PDF文件**：
   - 点击左下方"选择PDF文件"按钮
   - 在弹出对话框中选择PDF文件
   - 工具会自动将PDF每一页转换为图片

2. **输入分析指令**：
   - 在"User输入"框中输入问题，例如：
     - "请分析这个PDF文档的内容"
     - "总结这份文件的要点"
     - "提取文档中的关键数据"

3. **选择支持视觉的模型**：
   - ⚠️ 注意：必须选择支持图片输入的模型，如 `DOUBAO_IMAGE_1_6`
   - 不是所有模型都支持图片分析

4. **发送请求**：
   - 点击"发送请求"
   - PDF的所有页面会作为图片附加到消息中

5. **清除上传**（可选）：
   - 点击"清除"按钮移除已上传的PDF

### JSON格式输出

如果需要AI返回结构化的JSON数据：

1. 在配置中选择响应格式为 `json_object`
2. 在System提示词中明确要求返回JSON格式，例如：
   ```
   你是一个数据分析助手。请以JSON格式返回分析结果，包含以下字段：
   {
     "summary": "总结",
     "key_points": ["要点1", "要点2"],
     "conclusion": "结论"
   }
   ```
3. 发送请求后，工具会自动格式化显示JSON输出

## 支持的模型

工具内置支持以下AI模型：

- **DeepSeek系列**:
  - `DEEPSEEK_V3` - DeepSeek Chat V3
  - `DEEPSEEK_R1` - DeepSeek R1

- **通义千问系列**:
  - `QWEN_PLUS` - 通义千问Plus
  - `QWEN_235B` - 通义千问3-235B

- **豆包系列**:
  - `DOUBAO_1_6` - 豆包1.6
  - `DOUBAO_1_5` - 豆包1.5 Pro
  - `DOUBAO_IMAGE_1_6` - 豆包1.6 图像版（支持图片）
  - `DOUBAO_1_6_FLASH` - 豆包1.6 Flash

## 技术细节

### PDF处理流程

1. 使用`pdf2image`库将PDF转换为PIL图像对象
2. 自动调整图片大小（最大2048px），压缩以减小传输体积
3. 转换为JPEG格式的base64编码
4. 按照OpenAI Vision API标准构建消息格式：
   ```json
   {
     "role": "user",
     "content": [
       {"type": "text", "text": "用户问题"},
       {
         "type": "image_url", 
         "image_url": {"url": "data:image/jpeg;base64,..."}
       }
     ]
   }
   ```

### 流式响应

启用流式响应后：
- AI会逐字返回内容，实时显示在界面上
- 显示首字响应时间（TTFB - Time To First Byte）
- 适合长文本生成，避免等待超时
- 提供更好的用户体验

### 配置文件

配置保存在 `debug_tool_config.ini` 文件中，采用INI格式：

```ini
[DEFAULT]
api_url = https://your-api-endpoint
application = your-app-id
api_key = your-api-key
timeout = 60
response_format = text
model = QWEN_235B
temperature = 0.7
use_stream = true
```

## 故障排除

### 问题1: 提示"需要安装 pdf2image 和 Pillow 库"

**原因**: PDF处理依赖未安装

**解决方案**:
```bash
pip install pdf2image Pillow
```

### 问题2: "Unable to get page count. Is poppler installed and in PATH?"

**原因**: Poppler未正确安装或未添加到系统PATH

**解决方案**:
- Windows: 按照上方"安装Poppler"章节重新安装，确保添加到PATH
- Linux/macOS: 运行 `sudo apt-get install poppler-utils` 或 `brew install poppler`
- 验证: 在命令行运行 `pdftoppm -h`，应该显示帮助信息

### 问题3: PDF转换失败

**可能原因及解决方案**:
- PDF文件损坏：尝试用其他PDF阅读器打开验证
- 磁盘空间不足：清理磁盘空间
- 内存不足：尝试较小的PDF文件
- PDF加密保护：先解除PDF保护

### 问题4: 模型不支持图片

**原因**: 选择的模型不支持视觉/图片输入

**解决方案**: 切换到支持图片的模型，如 `DOUBAO_IMAGE_1_6`

### 问题5: 请求超时

**解决方案**:
1. 启用"流式响应"选项（推荐）
2. 增加超时时间设置
3. 检查网络连接
4. 尝试较短的提示词或较小的PDF

### 问题6: API Key错误

**解决方案**:
- 检查API Key是否正确
- 确认API Key有对应模型的权限
- 如果是内部API，可能不需要API Key，留空即可

## 使用场景示例

### 场景1: 测试提示词效果

快速测试不同的System提示词对AI回答的影响：

**测试1 - 友好助手**:
```
System: 你是一个友好、耐心的AI助手。
User: 什么是机器学习？
```

**测试2 - 专业导师**:
```
System: 你是一位经验丰富的机器学习教授，用学术但易懂的语言解释概念。
User: 什么是机器学习？
```

### 场景2: PDF文档分析

分析合同、报告、论文等PDF文档：

```
System: 你是一个专业的文档分析助手。
User: 请分析这份合同，提取关键条款、权利义务和需要注意的风险点。
[上传PDF文件]
```

### 场景3: 数据提取

从PDF中提取结构化数据：

```
System: 你是数据提取专家。请以JSON格式返回结果。
响应格式: json_object
User: 从这份发票中提取：发票号、日期、金额、税额、公司名称。
[上传发票PDF]
```

### 场景4: 多轮对话测试

测试AI的上下文理解能力（手动进行多轮）：

第一轮：
```
User: 请给我介绍一下Python的列表推导式。
```

第二轮（复制上轮回答到System中）：
```
System: [上一轮的对话历史]
User: 能给个实际例子吗？
```

## 项目结构

```
ai_debug_tool/
├── ai_debug_tool.py          # 主程序文件
├── requirements.txt          # Python依赖列表
├── debug_tool_config.ini     # 配置文件（首次运行自动生成）
├── run.bat                   # Windows启动脚本
├── docs/
│   └── PDF_UPLOAD_README.md  # PDF功能详细说明
└── README.md                 # 本文件
```

## 开发计划

- [ ] 支持多轮对话历史管理
- [ ] 支持图片直接上传（非PDF）
- [ ] 支持导出对话记录
- [ ] 添加提示词模板库
- [ ] 支持批量测试
- [ ] 添加Token统计功能

## 常见问题 (FAQ)

**Q: 工具支持哪些API？**

A: 理论上支持所有兼容OpenAI格式的API。已测试支持DeepSeek、通义千问、豆包等。

**Q: 是否支持本地模型？**

A: 如果您的本地模型提供了兼容的HTTP API接口，可以配置API地址指向本地服务。

**Q: PDF转换需要多长时间？**

A: 取决于PDF大小和页数。通常每页处理时间在1-3秒。50页的文档大约需要1-2分钟。

**Q: 转换的图片质量如何？**

A: 默认使用200 DPI，JPEG质量85%，最大尺寸2048px。可在代码的`pdf_to_images`函数中调整。

**Q: 是否会保存上传的PDF？**

A: 不会。PDF仅在内存中处理，转换为base64后立即发送，不会保存到磁盘。

**Q: 可以同时上传多个PDF吗？**

A: 目前仅支持单个PDF。如需分析多个文档，请分别上传。

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交Issue。

---

**祝使用愉快！Happy Debugging! 🚀**

