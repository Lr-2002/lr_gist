#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF分析工具使用示例
"""

import os
from pdf_reader import PDFAnalyzer

def main():
    # 检查API密钥
    if not os.getenv("SILICONFLOW_API_KEY"):
        print("❌ 请先设置SILICONFLOW_API_KEY环境变量")
        print("   export SILICONFLOW_API_KEY='your-api-key'")
        print("   获取API密钥: https://cloud.siliconflow.cn/account/ak")
        return
    
    # 设置PDF文件夹路径
    pdf_folder = "/Users/lr-2002/Downloads/Exported Items/files"
    
    # 检查文件夹是否存在
    if not os.path.exists(pdf_folder):
        print(f"❌ 文件夹不存在: {pdf_folder}")
        print("请修改 pdf_folder 变量为实际的PDF文件夹路径")
        return
    
    # 创建分析器
    print("🚀 初始化PDF分析器...")
    analyzer = PDFAnalyzer()
    
    # 自定义分析提示词
    custom_prompt = """请分析这篇论文，回答以下问题：

1. 做了什么东西？（例如：一套基于UMI的数据采集方案）
2. 用了什么metric，比较了什么能力？（例如：数据采集质量、数据采集效率等）
3. 做了什么实验？（例如：在冰箱中进行探索）
4. 结论是什么？（例如：能够提高数据采集效率，或者操作空间更加灵活）

请用简洁的中文回答，每个问题用一段话概括。"""
    
    print(f"📁 分析文件夹: {pdf_folder}")
    print(f"🤖 使用模型: Qwen/Qwen2.5-7B-Instruct")
    print(f"📄 每个PDF提取: 15页")
    print("\n开始分析...\n")
    
    # 批量分析PDF
    results = analyzer.batch_analyze_pdfs(
        folder_path=pdf_folder,
        prompt=custom_prompt,
        max_pages=15,
        model="Qwen/Qwen2.5-7B-Instruct"  # 可选其他模型：Qwen/Qwen2.5-72B-Instruct, deepseek-ai/DeepSeek-V3
    )
    
    # 生成Markdown报告
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    md_file = f"pdf_analysis_{timestamp}.md"
    analyzer.generate_markdown_report(results, md_file)
    
    print(f"\n✅ 分析完成！")
    print(f"📊 处理文件数: {len(results)}")
    print(f"📝 Markdown报告: {md_file}")
    
    # 显示简要统计
    success_count = sum(1 for r in results.values() 
                       if r.get('analysis', {}).get('status') == 'success')
    total_tokens = sum(r.get('analysis', {}).get('tokens_used', 0) 
                      for r in results.values())
    
    print(f"✅ 成功分析: {success_count}/{len(results)}")
    print(f"🔢 总Token使用: {total_tokens}")

if __name__ == "__main__":
    main()
