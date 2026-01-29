#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发票号码查询工具
功能：
1. 遍历指定文件夹中的所有PDF文件提取发票号码
2. 根据输入（文件夹/PDF文件/发票号码）查询发票号码是否存在
"""

import os
import re
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import json
import pickle
from pathlib import Path
from typing import Set, Dict, List, Optional
import argparse
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class InvoiceNumberExtractor:
    """发票号码提取器"""

    def __init__(self, cache_file: str = "invoice_numbers_cache.pkl"):
        """
        初始化提取器

        Args:
            cache_file: 缓存文件路径，用于存储已提取的发票号码
        """
        self.cache_file = cache_file
        self.invoice_number_set: Set[str] = set()
        self.invoice_to_files: Dict[str, List[str]] = {}  # 发票号码到文件路径的映射
        self.base_path = "/Users/lr-2002/Documents/报销材料/"
        self.exclude_folder = "/Users/lr-2002/Documents/报销材料/tbd"

        # 发票号码的正则表达式模式（参考 expense_request.py）
        self.invoice_number_patterns = [
            r"发票号码[：:](\d{8,})",
            r"发票代码[：:]?(\d{10,12})",
            r"No[.:]?\s*(\d{8,})",
            r"(\d{20,})",
        ]

        # 加载缓存
        self.load_cache()

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """从PDF中提取文本"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            logger.error(f"PDF文本提取失败 {pdf_path}: {e}")
            return ""

    def pdf_to_image_ocr(self, pdf_path: str) -> str:
        """将PDF转换为图像并进行OCR识别"""
        try:
            doc = fitz.open(pdf_path)
            text = ""

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                # 将页面转换为图像
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 提高分辨率
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))

                # 使用OCR识别
                ocr_text = pytesseract.image_to_string(img, lang="chi_sim+eng")
                text += ocr_text + "\n"

            doc.close()
            return text
        except Exception as e:
            logger.error(f"OCR识别失败 {pdf_path}: {e}")
            return ""

    def extract_invoice_numbers_from_text(self, text: str) -> List[str]:
        """从文本中提取发票号码"""
        numbers = []
        for pattern in self.invoice_number_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) >= 8:  # 发票号码通常至少8位
                    numbers.append(match)
        return numbers

    def extract_invoice_numbers_from_pdf(self, pdf_path: str) -> List[str]:
        """从单个PDF文件中提取发票号码"""
        logger.info(f"正在处理: {pdf_path}")

        # 首先尝试直接提取文本
        text = self.extract_text_from_pdf(pdf_path)

        # 如果文本提取效果不好，使用OCR
        if len(text.strip()) < 100:  # 文本太少，可能需要OCR
            logger.info(f"文本提取不足，使用OCR: {pdf_path}")
            text = self.pdf_to_image_ocr(pdf_path)

        if text.strip():
            return self.extract_invoice_numbers_from_text(text)
        else:
            logger.warning(f"无法从 {pdf_path} 中提取文本")
            return []

    def find_all_pdfs(self, folder_path: str, include_excluded: bool = False) -> List[str]:
        """
        查找文件夹中的所有PDF文件，可选择是否排除指定文件夹

        Args:
            folder_path: 要搜索的文件夹路径
            include_excluded: 是否包含排除的文件夹中的文件

        Returns:
            PDF文件路径列表
        """
        pdf_files = []
        folder_path = Path(folder_path)

        if not folder_path.exists():
            logger.error(f"路径不存在: {folder_path}")
            return pdf_files

        # 转换为绝对路径进行比较
        exclude_path = Path(self.exclude_folder).resolve()

        # 递归查找所有PDF文件
        for pdf_file in folder_path.rglob("*.pdf"):
            pdf_file_resolved = pdf_file.resolve()

            # 检查是否在排除的文件夹中
            if not include_excluded:
                try:
                    if pdf_file_resolved.is_relative_to(exclude_path):
                        logger.debug(f"跳过排除文件夹中的文件: {pdf_file}")
                        continue
                except AttributeError:
                    # Python < 3.9 没有 is_relative_to 方法，使用字符串比较
                    if str(pdf_file_resolved).startswith(str(exclude_path)):
                        logger.debug(f"跳过排除文件夹中的文件: {pdf_file}")
                        continue

            pdf_files.append(str(pdf_file))

        return pdf_files

    def extract_all_invoice_numbers(self, force_refresh: bool = False, include_tbd: bool = True) -> None:
        """
        遍历所有PDF文件提取发票号码

        Args:
            force_refresh: 是否强制重新提取（忽略缓存）
            include_tbd: 是否包含tbd文件夹中的发票（为了完整性，默认包含）
        """
        if not force_refresh and self.invoice_number_set:
            logger.info("使用缓存的发票号码数据")
            return

        logger.info("开始提取所有PDF文件的发票号码...")
        # 为了完整性，提取所有文件夹的发票号码，包括tbd
        pdf_files = self.find_all_pdfs(self.base_path, include_tbd)

        if not pdf_files:
            logger.warning(f"在 {self.base_path} 中未找到PDF文件")
            return

        logger.info(f"找到 {len(pdf_files)} 个PDF文件")

        # 清空现有数据
        self.invoice_number_set.clear()
        self.invoice_to_files.clear()

        for pdf_file in pdf_files:
            numbers = self.extract_invoice_numbers_from_pdf(pdf_file)
            for number in numbers:
                self.invoice_number_set.add(number)
                if number not in self.invoice_to_files:
                    self.invoice_to_files[number] = []
                self.invoice_to_files[number].append(pdf_file)

        logger.info(f"提取完成，共找到 {len(self.invoice_number_set)} 个唯一发票号码")

        # 保存缓存
        self.save_cache()

    def save_cache(self) -> None:
        """保存发票号码到缓存文件"""
        try:
            cache_data = {
                'invoice_number_set': self.invoice_number_set,
                'invoice_to_files': self.invoice_to_files
            }
            with open(self.cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            logger.info(f"缓存已保存到: {self.cache_file}")
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")

    def load_cache(self) -> None:
        """从缓存文件加载发票号码"""
        if not os.path.exists(self.cache_file):
            logger.info("缓存文件不存在，将重新提取")
            return

        try:
            with open(self.cache_file, 'rb') as f:
                cache_data = pickle.load(f)
                self.invoice_number_set = cache_data.get('invoice_number_set', set())
                self.invoice_to_files = cache_data.get('invoice_to_files', {})
            logger.info(f"从缓存加载了 {len(self.invoice_number_set)} 个发票号码")
        except Exception as e:
            logger.error(f"加载缓存失败: {e}")
            self.invoice_number_set = set()
            self.invoice_to_files = {}

    def check_invoice_number(self, invoice_number: str, include_tbd: bool = False) -> Dict:
        """
        检查发票号码是否存在（是否已报销）

        Args:
            invoice_number: 要查询的发票号码
            include_tbd: 是否包含tbd文件夹中的发票

        Returns:
            包含查询结果的字典
        """
        # 获取所有包含该发票号码的文件
        all_files = self.invoice_to_files.get(invoice_number, [])

        # 过滤掉tbd文件夹中的文件（除非明确要求包含）
        if not include_tbd:
            tbd_path = Path(self.exclude_folder).resolve()
            filtered_files = []
            for file_path in all_files:
                file_resolved = Path(file_path).resolve()
                try:
                    if not file_resolved.is_relative_to(tbd_path):
                        filtered_files.append(file_path)
                except AttributeError:
                    # Python < 3.9 没有 is_relative_to 方法
                    if not str(file_resolved).startswith(str(tbd_path)):
                        filtered_files.append(file_path)
            all_files = filtered_files

        result = {
            'invoice_number': invoice_number,
            'exists': len(all_files) > 0,
            'is_reimbursed': len(all_files) > 0,  # 是否已报销
            'files': all_files,
            'include_tbd': include_tbd
        }

        return result

    def check_folder(self, folder_path: str, include_excluded: bool = False) -> Dict:
        """
        检查文件夹中的PDF文件包含哪些发票号码

        Args:
            folder_path: 文件夹路径
            include_excluded: 是否包含排除的文件夹中的文件

        Returns:
            包含文件夹中发票号码信息的字典
        """
        folder_path = Path(folder_path).resolve()
        pdf_files = self.find_all_pdfs(str(folder_path), include_excluded)

        result = {
            'folder_path': str(folder_path),
            'pdf_count': len(pdf_files),
            'invoice_numbers': {},
            'total_unique_numbers': 0
        }

        all_numbers = set()

        for pdf_file in pdf_files:
            numbers = self.extract_invoice_numbers_from_pdf(pdf_file)
            if numbers:
                result['invoice_numbers'][pdf_file] = numbers
                all_numbers.update(numbers)

        result['total_unique_numbers'] = len(all_numbers)

        return result

    def check_pdf_file(self, pdf_path: str) -> Dict:
        """
        检查单个PDF文件包含的发票号码

        Args:
            pdf_path: PDF文件路径

        Returns:
            包含PDF文件中发票号码信息的字典
        """
        pdf_path = Path(pdf_path).resolve()

        if not pdf_path.exists():
            return {
                'pdf_path': str(pdf_path),
                'exists': False,
                'error': '文件不存在'
            }

        if not pdf_path.suffix.lower() == '.pdf':
            return {
                'pdf_path': str(pdf_path),
                'exists': True,
                'error': '不是PDF文件'
            }

        numbers = self.extract_invoice_numbers_from_pdf(str(pdf_path))

        return {
            'pdf_path': str(pdf_path),
            'exists': True,
            'invoice_numbers': numbers,
            'count': len(numbers)
        }

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return {
            'total_unique_numbers': len(self.invoice_number_set),
            'total_files_with_invoices': len(self.invoice_to_files),
            'base_path': self.base_path,
            'exclude_folder': self.exclude_folder,
            'cache_file': self.cache_file
        }

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="发票号码查询工具")
    parser.add_argument("input", help="输入：文件夹路径、PDF文件路径或发票号码")
    parser.add_argument("--type", choices=['auto', 'folder', 'file', 'number'],
                       default='auto', help="输入类型，默认为自动检测")
    parser.add_argument("--refresh", action='store_true', help="强制刷新缓存")
    parser.add_argument("--stats", action='store_true', help="显示统计信息")
    parser.add_argument("--export", help="导出所有发票号码到指定文件")
    parser.add_argument("--include-excluded", action='store_true',
                       help="包含被排除的文件夹（如tbd文件夹）中的文件")
    parser.add_argument("--include-tbd", action='store_true',
                       help="查询发票号码时包含tbd文件夹中的发票（默认只查询已报销的发票）")

    args = parser.parse_args()

    # 创建提取器
    extractor = InvoiceNumberExtractor()

    # 提取所有发票号码（包括tbd文件夹，为了完整性）
    extractor.extract_all_invoice_numbers(force_refresh=args.refresh, include_tbd=True)

    # 显示统计信息
    if args.stats:
        stats = extractor.get_statistics()
        print("\n=== 统计信息 ===")
        print(f"总发票号码数量: {stats['total_unique_numbers']}")
        print(f"包含发票的文件数量: {stats['total_files_with_invoices']}")
        print(f"扫描路径: {stats['base_path']}")
        print(f"排除路径: {stats['exclude_folder']}")
        print(f"缓存文件: {stats['cache_file']}")
        print()

    # 导出发票号码
    if args.export:
        try:
            with open(args.export, 'w', encoding='utf-8') as f:
                for number in sorted(extractor.invoice_number_set):
                    files = extractor.invoice_to_files.get(number, [])
                    f.write(f"{number}: {len(files)} files\n")
                    for file_path in files:
                        f.write(f"  - {file_path}\n")
                    f.write("\n")
            print(f"发票号码已导出到: {args.export}")
        except Exception as e:
            logger.error(f"导出失败: {e}")

    # 处理输入
    input_path = Path(args.input).resolve()

    # 自动检测输入类型
    if args.type == 'auto':
        if input_path.is_file() and input_path.suffix.lower() == '.pdf':
            input_type = 'file'
        elif input_path.is_dir():
            input_type = 'folder'
        else:
            input_type = 'number'
    else:
        input_type = args.type

    # 根据类型处理
    if input_type == 'number':
        # 查询发票号码
        result = extractor.check_invoice_number(args.input, args.include_tbd)
        print(f"\n=== 发票号码查询结果 ===")
        print(f"发票号码: {result['invoice_number']}")
        print(f"是否已报销: {'是' if result['is_reimbursed'] else '否'}")
        print(f"查询范围: {'包含待处理发票' if result['include_tbd'] else '仅已报销发票'}")

        if result['exists']:
            print(f"出现次数: {len(result['files'])}")
            print("相关文件:")
            for file_path in result['files']:
                print(f"  - {file_path}")
        else:
            print("该发票号码未在报销记录中找到")

    elif input_type == 'file':
        # 查询PDF文件
        result = extractor.check_pdf_file(str(input_path))
        print(f"\n=== PDF文件查询结果 ===")
        print(f"文件路径: {result['pdf_path']}")
        print(f"文件存在: {'是' if result['exists'] else '否'}")

        if 'error' in result:
            print(f"错误: {result['error']}")
        else:
            print(f"发票号码数量: {result['count']}")
            if result['invoice_numbers']:
                print("发票号码:")
                for number in result['invoice_numbers']:
                    files = extractor.invoice_to_files.get(number, [])
                    print(f"  - {number} (在 {len(files)} 个文件中)")

    elif input_type == 'folder':
        # 查询文件夹
        result = extractor.check_folder(str(input_path), args.include_excluded)
        print(f"\n=== 文件夹查询结果 ===")
        print(f"文件夹路径: {result['folder_path']}")
        print(f"PDF文件数量: {result['pdf_count']}")
        print(f"唯一发票号码数量: {result['total_unique_numbers']}")
        if args.include_excluded:
            print(f"包含排除文件夹: 是")

        if result['invoice_numbers']:
            print("\n文件及发票号码:")
            for pdf_file, numbers in result['invoice_numbers'].items():
                print(f"  {pdf_file}:")
                for number in numbers:
                    print(f"    - {number}")

if __name__ == "__main__":
    main()