# 自动化报销信息生成系统

## 功能介绍

这个系统可以自动处理PDF发票文件，提取关键信息并生成Excel报销表格。

### 主要功能
- 自动读取指定文件夹中的所有PDF发票
- 使用OCR技术识别发票内容
- 提取发票号码、金额、商品名称等关键信息
- 按照标准模板格式生成Excel报销表
- 自动验证金额合理性
- 生成处理日志和错误提示

## 安装依赖

### 1. 安装Python包
```bash
pip install -r requirements.txt
```

### 2. 安装Tesseract OCR
**macOS:**
```bash
brew install tesseract tesseract-lang
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim
```

## 使用方法

### 命令行使用
```bash
python expense_request.py "/path/to/invoice/folder"
```

### 示例
```bash
python expense_request.py "/Users/lr-2002/Documents/报销材料/6.27/发票"
```

### 程序化使用
```python
from expense_request import main

# 处理发票文件夹
main("/path/to/invoice/folder")
```

## 输出格式

生成的Excel文件包含以下列：
- **付款明细原因**: 从发票中提取的商品/服务名称，或使用文件名
- **项目负责人**: 马晓健（固定值）
- **发票类型**: 增值税电子普通发票（固定值）
- **发票号码**: 从发票中OCR识别的号码
- **付款类型**: 科研费用（固定值）
- **科目明细**: 科研耗材（固定值）
- **金额**: 从发票中识别的总金额
- **备注**: 如有识别问题会显示相关提示

## 文件命名规则

输出的Excel文件命名格式：`YYYYMMDD_报销.xlsx`
例如：`20240702_报销.xlsx`

## 注意事项

1. **PDF质量**: 确保PDF发票清晰可读，模糊的发票可能影响OCR识别效果
2. **金额验证**: 系统会自动验证金额合理性，超过10万元的金额会标记为需要确认
3. **手动检查**: 建议在提交前手动检查生成的Excel文件，特别是有备注提示的条目
4. **文件格式**: 目前只支持PDF格式的发票文件

## 错误处理

- 如果OCR识别失败，系统会创建基本记录并在备注中标注
- 金额识别异常时会在备注中提示
- 所有处理过程都会记录在日志中

## 技术特性

- **智能文本提取**: 优先使用PDF原生文本，必要时使用OCR
- **多模式识别**: 支持多种发票号码和金额格式的正则表达式匹配
- **格式化输出**: 自动设置Excel表格格式，包括列宽、边框、对齐等
- **错误恢复**: 单个文件处理失败不会影响其他文件的处理

## 系统要求

- Python 3.7+
- macOS/Linux/Windows
- 足够的内存处理PDF文件（建议4GB+）

## 故障排除

### 常见问题

1. **OCR识别率低**
   - 检查PDF文件质量
   - 确保Tesseract正确安装并配置中文语言包

2. **金额识别错误**
   - 检查发票格式是否标准
   - 手动验证识别结果

3. **依赖包安装失败**
   - 使用conda环境管理
   - 检查网络连接和包源配置
