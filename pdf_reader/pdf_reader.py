#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF批量分析工具
功能：
1. 扫描指定文件夹中的所有PDF文件
2. 使用OpenAI API对每个PDF进行分析
3. 根据自定义prompt提取关键信息
4. 生成汇总报告
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional
import logging
from datetime import datetime
import PyPDF2
from openai import OpenAI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PDFAnalyzer:
    """PDF批量分析器"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        初始化PDF分析器
        
        Args:
            api_key: SiliconFlow API密钥，如果为None则从环境变量读取
            base_url: API基础URL，默认为SiliconFlow
        """
        self.api_key = api_key or os.getenv("SILICONFLOW_API_KEY")
        if not self.api_key:
            raise ValueError("未找到SiliconFlow API密钥，请设置SILICONFLOW_API_KEY环境变量或传入api_key参数")
        
        self.base_url = base_url or "https://api.siliconflow.cn/v1"
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.default_model = "Qwen/Qwen2.5-7B-Instruct"
    
    def find_all_pdfs(self, folder_path: str) -> List[Path]:
        """
        查找文件夹中所有PDF文件
        
        Args:
            folder_path: 文件夹路径
            
        Returns:
            PDF文件路径列表
        """
        folder = Path(folder_path)
        if not folder.exists():
            raise ValueError(f"文件夹不存在: {folder_path}")
        
        pdf_files = list(folder.glob("**/*.pdf"))
        logger.info(f"在 {folder_path} 中找到 {len(pdf_files)} 个PDF文件")
        
        return sorted(pdf_files)
    
    def extract_text_from_pdf(self, pdf_path: Path, max_pages: int = 10) -> str:
        """
        从PDF中提取文本内容
        
        Args:
            pdf_path: PDF文件路径
            max_pages: 最多提取的页数（避免token过多）
            
        Returns:
            提取的文本内容
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                pages_to_read = min(total_pages, max_pages)
                
                text_content = []
                for page_num in range(pages_to_read):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    if text.strip():
                        text_content.append(text)
                
                full_text = "\n\n".join(text_content)
                
                if total_pages > max_pages:
                    logger.warning(f"{pdf_path.name}: 只提取了前{max_pages}页（共{total_pages}页）")
                
                return full_text
                
        except Exception as e:
            logger.error(f"提取PDF文本失败 {pdf_path.name}: {e}")
            return ""
    
    def analyze_pdf_with_prompt(
        self, 
        pdf_text: str, 
        prompt: str,
        pdf_name: str,
        model: Optional[str] = None
    ) -> Dict[str, str]:
        """
        使用OpenAI API分析PDF内容
        
        Args:
            pdf_text: PDF文本内容
            prompt: 分析提示词
            pdf_name: PDF文件名
            model: 使用的模型，默认为gpt-4o-mini
            
        Returns:
            分析结果字典
        """
        if not pdf_text.strip():
            return {
                "status": "error",
                "error": "PDF文本为空",
                "response": ""
            }
        
        try:
            # SiliconFlow API 使用 OpenAI 兼容格式
            messages = [
                {
                    "role": "system",
                    "content": "你是一个专业的学术论文分析助手，擅长提取论文的关键信息。请用中文回答。"
                },
                {
                    "role": "user",
                    "content": f"以下是PDF文件《{pdf_name}》的内容：\n\n{pdf_text}\n\n{prompt}"
                }
            ]
            
            logger.info(f"正在分析 {pdf_name}...")
            
            response = self.client.chat.completions.create(
                model=model or self.default_model,
                messages=messages,
                temperature=0.3,
                max_tokens=2000
            )
            
            result = response.choices[0].message.content
            
            return {
                "status": "success",
                "response": result,
                "tokens_used": response.usage.total_tokens
            }
            
        except Exception as e:
            logger.error(f"SiliconFlow API调用失败 {pdf_name}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "response": ""
            }
    
    def batch_analyze_pdfs(
        self,
        folder_path: str,
        prompt: str,
        output_file: Optional[str] = None,
        max_pages: int = 10,
        model: Optional[str] = None
    ) -> Dict[str, Dict]:
        """
        批量分析文件夹中的所有PDF
        
        Args:
            folder_path: PDF文件夹路径
            prompt: 分析提示词
            output_file: 输出文件路径（JSON格式），如果为None则自动生成
            max_pages: 每个PDF最多提取的页数
            model: 使用的SiliconFlow模型
            
        Returns:
            所有PDF的分析结果
        """
        # 查找所有PDF文件
        pdf_files = self.find_all_pdfs(folder_path)
        
        if not pdf_files:
            logger.warning(f"在 {folder_path} 中没有找到PDF文件")
            return {}
        
        # 生成输出文件名
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"pdf_analysis_{timestamp}.json"
        
        # 分析每个PDF（增量保存模式）
        results = {}
        total_tokens = 0
        
        for idx, pdf_path in enumerate(pdf_files, 1):
            logger.info(f"处理 [{idx}/{len(pdf_files)}]: {pdf_path.name}")
            
            # 提取文本
            pdf_text = self.extract_text_from_pdf(pdf_path, max_pages=max_pages)
            
            if not pdf_text.strip():
                logger.warning(f"跳过空文件: {pdf_path.name}")
                results[pdf_path.name] = {
                    "status": "skipped",
                    "reason": "无法提取文本内容"
                }
                # 立即保存
                self.save_results(results, output_file, total_tokens)
                continue
            
            # 调用API分析
            analysis = self.analyze_pdf_with_prompt(
                pdf_text=pdf_text,
                prompt=prompt,
                pdf_name=pdf_path.name,
                model=model
            )
            
            results[pdf_path.name] = {
                "file_path": str(pdf_path),
                "analysis": analysis,
                "text_length": len(pdf_text)
            }
            
            if analysis.get("tokens_used"):
                total_tokens += analysis["tokens_used"]
            
            # 每处理完一个PDF就立即保存
            self.save_results(results, output_file, total_tokens)
            logger.info(f"✅ 已保存进度: {idx}/{len(pdf_files)}")
        
        logger.info(f"🎉 全部处理完成！结果已保存到: {output_file}")
        return results
    
    def save_results(self, results: Dict, output_file: str, total_tokens: int):
        """
        保存分析结果到JSON文件（增量保存）
        
        Args:
            results: 分析结果
            output_file: 输出文件路径
            total_tokens: 总token使用量
        """
        output_data = {
            "timestamp": datetime.now().isoformat(),
            "total_files": len(results),
            "total_tokens_used": total_tokens,
            "results": results
        }
        
        # 使用临时文件，避免写入过程中断导致文件损坏
        temp_file = output_file + ".tmp"
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        # 原子性替换
        import shutil
        shutil.move(temp_file, output_file)
    
    def generate_markdown_report(self, results: Dict, output_file: str):
        """
        生成Markdown格式的分析报告
        
        Args:
            results: 分析结果
            output_file: 输出文件路径
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# PDF批量分析报告\n\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"总计分析: {len(results)} 个PDF文件\n\n")
            f.write("---\n\n")
            
            for idx, (pdf_name, data) in enumerate(results.items(), 1):
                f.write(f"## {idx}. {pdf_name}\n\n")
                
                if data.get("status") == "skipped":
                    f.write(f"**状态**: 跳过\n\n")
                    f.write(f"**原因**: {data.get('reason', '未知')}\n\n")
                else:
                    analysis = data.get("analysis", {})
                    if analysis.get("status") == "success":
                        f.write(f"**分析结果**:\n\n")
                        f.write(f"{analysis.get('response', '无结果')}\n\n")
                        f.write(f"*Token使用: {analysis.get('tokens_used', 0)}*\n\n")
                    else:
                        f.write(f"**错误**: {analysis.get('error', '未知错误')}\n\n")
                
                f.write("---\n\n")
        
        logger.info(f"Markdown报告已生成: {output_file}")


def main():
    """主函数示例"""
    import argparse
    
    parser = argparse.ArgumentParser(description="PDF批量分析工具")
    parser.add_argument("folder_path", help="PDF文件夹路径")
    parser.add_argument("-p", "--prompt", help="分析提示词", default=None)
    parser.add_argument("-o", "--output", help="输出文件路径（JSON）", default=None)
    parser.add_argument("-m", "--markdown", help="生成Markdown报告", action="store_true")
    parser.add_argument("--max-pages", type=int, default=10, help="每个PDF最多提取的页数")
    parser.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct", help="SiliconFlow模型")
    
    args = parser.parse_args()
    
    # 默认提示词
    if args.prompt is None:
        args.prompt = """请分析这篇论文，回答以下问题：

1. 这篇论文做了什么？主要贡献是什么？
2. 使用了什么评估指标（metrics）？比较了什么能力？
3. 进行了什么实验？在什么场景下测试？
4. 主要结论是什么？

请用简洁的中文回答，每个问题用一段话概括。"""
    
    # 创建分析器
    analyzer = PDFAnalyzer()
    
    # 批量分析
    results = analyzer.batch_analyze_pdfs(
        folder_path=args.folder_path,
        prompt=args.prompt,
        output_file=args.output,
        max_pages=args.max_pages,
        model=args.model
    )
    
    # 生成Markdown报告
    if args.markdown:
        md_output = args.output.replace('.json', '.md') if args.output else f"pdf_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        analyzer.generate_markdown_report(results, md_output)
    
    print(f"\n✅ 分析完成！处理了 {len(results)} 个PDF文件")


if __name__ == "__main__":
    # 示例用法
    example_folder = "/Users/lr-2002/Downloads/Exported Items/files"
    
    if os.path.exists(example_folder):
        analyzer = PDFAnalyzer()
        
        custom_prompt = """请分析这篇论文，回答以下问题：

1. 做了什么东西？（例如：一套基于UMI的数据采集方案）
2. 用了什么metric，比较了什么能力？（例如：数据采集质量、数据采集效率等）
3. 做了什么实验？（例如：在冰箱中进行探索）
4. 结论是什么？（例如：能够提高数据采集效率，或者操作空间更加灵活）

请用简洁的中文回答，每个问题用一段话概括。"""
        
        results = analyzer.batch_analyze_pdfs(
            folder_path=example_folder,
            prompt=custom_prompt,
            max_pages=15
        )
        
        # 生成Markdown报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        analyzer.generate_markdown_report(results, f"pdf_analysis_{timestamp}.md")
        
        print(f"\n✅ 分析完成！")
    else:
        print(f"示例文件夹不存在: {example_folder}")
        print("请使用命令行参数指定文件夹路径")
        print("\n使用方法:")
        print("  python pdf_reader.py <文件夹路径>")
        print("  python pdf_reader.py <文件夹路径> -p '自定义提示词' -m")
