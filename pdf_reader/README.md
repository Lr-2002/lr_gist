# PDF批量分析工具

使用SiliconFlow API批量分析PDF文件，提取关键信息。

## 功能特性

1. **自动扫描** - 递归扫描文件夹中的所有PDF文件
2. **文本提取** - 从PDF中提取文本内容
3. **AI分析** - 使用OpenAI GPT模型分析每个PDF
4. **自定义提示词** - 支持自定义分析问题
5. **结果保存** - 生成JSON和Markdown格式的分析报告

## 安装依赖

```bash
pip install -r requirements.txt
```

或使用conda：

```bash
conda install -c conda-forge pypdf2
pip install openai
```

## 配置API密钥

设置SiliconFlow API密钥环境变量：

```bash
export SILICONFLOW_API_KEY='your-api-key-here'
```

获取API密钥：[https://cloud.siliconflow.cn/account/ak](https://cloud.siliconflow.cn/account/ak)

## 快速开始

### 1. 测试API连接

```bash
python test_api.py
```

### 2. 运行示例脚本

```bash
python example_usage.py
```

## 使用方法

### 1. 直接运行（使用默认路径）

```bash
python pdf_reader.py
```

默认会分析 `/Users/lr-2002/Downloads/Exported Items/files` 文件夹中的PDF。

### 2. 指定文件夹路径

```bash
python pdf_reader.py /path/to/pdf/folder
```

### 3. 自定义提示词

```bash
python pdf_reader.py /path/to/pdf/folder -p "你的自定义提示词"
```

### 4. 生成Markdown报告

```bash
python pdf_reader.py /path/to/pdf/folder -m
```

### 5. 完整参数示例

```bash
python pdf_reader.py /path/to/pdf/folder \
  -p "请分析这篇论文的核心贡献" \
  -o analysis_results.json \
  -m \
  --max-pages 15 \
  --model Qwen/Qwen2.5-72B-Instruct
```

## 参数说明

- `folder_path` - PDF文件夹路径（必需）
- `-p, --prompt` - 自定义分析提示词
- `-o, --output` - 输出JSON文件路径
- `-m, --markdown` - 生成Markdown格式报告
- `--max-pages` - 每个PDF最多提取的页数（默认10页）
- `--model` - SiliconFlow模型（默认Qwen/Qwen2.5-7B-Instruct）

### 可用模型

SiliconFlow支持多种模型，推荐使用：
- `Qwen/Qwen2.5-7B-Instruct` - 快速、经济（默认）
- `Qwen/Qwen2.5-72B-Instruct` - 更强大的理解能力
- `deepseek-ai/DeepSeek-V3` - 顶级性能
- `Pro/deepseek-ai/DeepSeek-V3` - Pro版本，更快响应

完整模型列表：[https://cloud.siliconflow.cn/models](https://cloud.siliconflow.cn/models)

## 默认分析问题

工具会针对每个PDF回答以下问题：

1. **做了什么？** - 论文的主要工作和贡献
2. **用了什么metric？** - 评估指标和比较的能力
3. **做了什么实验？** - 实验场景和测试方法
4. **结论是什么？** - 主要发现和结论

## 输出文件

### JSON格式（`pdf_analysis_YYYYMMDD_HHMMSS.json`）

```json
{
  "timestamp": "2025-11-24T10:54:00",
  "total_files": 5,
  "total_tokens_used": 15000,
  "results": {
    "paper1.pdf": {
      "file_path": "/path/to/paper1.pdf",
      "analysis": {
        "status": "success",
        "response": "分析结果...",
        "tokens_used": 3000
      },
      "text_length": 12000
    }
  }
}
```

### Markdown格式（`pdf_analysis_YYYYMMDD_HHMMSS.md`）

生成易读的报告，包含每个PDF的分析结果。

## 代码示例

```python
from pdf_reader import PDFAnalyzer

# 创建分析器
analyzer = PDFAnalyzer()

# 自定义提示词
custom_prompt = """请分析这篇论文：
1. 主要创新点是什么？
2. 使用了什么技术方案？
3. 实验结果如何？
"""

# 批量分析
results = analyzer.batch_analyze_pdfs(
    folder_path="/path/to/pdfs",
    prompt=custom_prompt,
    max_pages=15,
    model="Qwen/Qwen2.5-7B-Instruct"
)

# 生成报告
analyzer.generate_markdown_report(results, "report.md")
```

## 注意事项

1. **API费用** - 使用SiliconFlow API会产生费用，但比OpenAI便宜很多，建议先用少量文件测试
2. **Token限制** - 默认每个PDF只提取前10页，避免超过token限制
3. **文本质量** - 扫描版PDF可能无法提取文本，需要OCR处理
4. **API密钥** - 确保设置了正确的SILICONFLOW_API_KEY环境变量

## 常见问题

### Q: 如何处理大量PDF？

A: 可以分批处理，或增加`--max-pages`参数限制每个PDF的页数。

### Q: 如何使用更强大的模型？

A: 使用`--model Qwen/Qwen2.5-72B-Instruct`或`--model deepseek-ai/DeepSeek-V3`参数。

### Q: 提取的文本乱码怎么办？

A: 可能是PDF编码问题，建议使用OCR工具预处理。

## 示例输出

```
2025-11-24 10:54:00 - INFO - 在 /path/to/pdfs 中找到 5 个PDF文件
2025-11-24 10:54:01 - INFO - 处理 [1/5]: paper1.pdf
2025-11-24 10:54:05 - INFO - 正在分析 paper1.pdf...
2025-11-24 10:54:10 - INFO - 处理 [2/5]: paper2.pdf
...
2025-11-24 10:55:00 - INFO - 分析结果已保存到: pdf_analysis_20251124_105400.json
2025-11-24 10:55:00 - INFO - 总计处理: 5 个文件
2025-11-24 10:55:00 - INFO - 总计使用: 15000 tokens

✅ 分析完成！处理了 5 个PDF文件
```
