#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查tbd文件夹中已报销的发票并移动到done文件夹
功能：
1. 提取tbd文件夹中所有发票的发票号码
2. 检查这些发票号码是否已经在已报销文件夹中出现过
3. 如果已报销过，将对应的PDF移动到tbd/done文件夹
"""

import os
import re
import shutil
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import logging
from pathlib import Path
from typing import Set, Dict, List, Optional
from invoice_number_checker import InvoiceNumberExtractor

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class ReimbursedInvoiceChecker:
    """已报销发票检查器"""

    def __init__(self):
        """初始化检查器"""
        self.base_path = "/Users/lr-2002/Documents/报销材料/"
        self.tbd_folder = os.path.join(self.base_path, "tbd")
        self.done_folder = os.path.join(self.tbd_folder, "done")

        # 创建done文件夹
        Path(self.done_folder).mkdir(parents=True, exist_ok=True)

        # 使用现有的发票号码提取器
        self.extractor = InvoiceNumberExtractor()

        # 发票号码的正则表达式模式（参考 expense_request.py）
        self.invoice_number_patterns = [
            r"发票号码[：:](\d{8,})",
            r"发票代码[：:]?(\d{10,12})",
            r"No[.:]?\s*(\d{8,})",
            r"(\d{20,})",
        ]

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
        logger.info(f"正在处理: {os.path.basename(pdf_path)}")

        # 首先尝试直接提取文本
        text = self.extract_text_from_pdf(pdf_path)

        # 如果文本提取效果不好，使用OCR
        if len(text.strip()) < 100:  # 文本太少，可能需要OCR
            logger.info(f"文本提取不足，使用OCR: {os.path.basename(pdf_path)}")
            text = self.pdf_to_image_ocr(pdf_path)

        if text.strip():
            return self.extract_invoice_numbers_from_text(text)
        else:
            logger.warning(f"无法从 {os.path.basename(pdf_path)} 中提取文本")
            return []

    def get_tbd_pdf_files(self) -> List[str]:
        """获取tbd文件夹中的所有PDF文件（排除done文件夹）"""
        tbd_path = Path(self.tbd_folder)
        done_path = Path(self.done_folder)

        pdf_files = []
        for pdf_file in tbd_path.glob("*.pdf"):
            # 排除done文件夹中的文件
            try:
                if not pdf_file.resolve().is_relative_to(done_path.resolve()):
                    pdf_files.append(str(pdf_file))
            except AttributeError:
                # Python < 3.9 没有 is_relative_to 方法
                if not str(pdf_file.resolve()).startswith(str(done_path.resolve())):
                    pdf_files.append(str(pdf_file))

        return pdf_files

    def check_invoice_numbers_reimbursed(self, invoice_numbers: List[str]) -> Dict[str, bool]:
        """
        检查发票号码是否已经报销过

        Args:
            invoice_numbers: 发票号码列表

        Returns:
            发票号码到是否已报销的映射
        """
        results = {}

        for invoice_number in invoice_numbers:
            # 使用现有的提取器查询该发票号码是否已报销（不包括tbd）
            result = self.extractor.check_invoice_number(invoice_number, include_tbd=False)
            results[invoice_number] = result['is_reimbursed']

        return results

    def move_reimbursed_invoices(self, dry_run: bool = False) -> Dict:
        """
        检查并移动已报销的发票

        Args:
            dry_run: 是否为演练模式（不实际移动文件）

        Returns:
            处理结果统计
        """
        logger.info("开始检查tbd文件夹中的发票...")

        # 确保已有所有已报销发票的缓存
        self.extractor.extract_all_invoice_numbers(force_refresh=False, include_tbd=True)

        # 获取tbd文件夹中的PDF文件
        tbd_pdfs = self.get_tbd_pdf_files()

        if not tbd_pdfs:
            logger.info("tbd文件夹中没有PDF文件")
            return {
                'total_files': 0,
                'reimbursed_files': 0,
                'non_reimbursed_files': 0,
                'moved_files': [],
                'errors': []
            }

        logger.info(f"找到 {len(tbd_pdfs)} 个PDF文件待检查")

        results = {
            'total_files': len(tbd_pdfs),
            'reimbursed_files': 0,
            'non_reimbursed_files': 0,
            'moved_files': [],
            'errors': []
        }

        # 处理每个PDF文件
        for pdf_file in tbd_pdfs:
            try:
                # 提取发票号码
                invoice_numbers = self.extract_invoice_numbers_from_pdf(pdf_file)

                if not invoice_numbers:
                    logger.warning(f"文件 {os.path.basename(pdf_file)} 中未找到发票号码")
                    continue

                # 检查是否已报销
                reimbursed_status = self.check_invoice_numbers_reimbursed(invoice_numbers)

                # 如果任何一个发票号码已报销，则移动文件
                if any(reimbursed_status.values()):
                    file_name = os.path.basename(pdf_file)
                    target_path = os.path.join(self.done_folder, file_name)

                    results['reimbursed_files'] += 1

                    # 获取已报销的发票号码
                    reimbursed_numbers = [num for num, is_reimbursed in reimbursed_status.items() if is_reimbursed]

                    logger.info(f"发票 {file_name} 已报销，发票号码: {reimbursed_numbers}")

                    if not dry_run:
                        # 移动文件
                        shutil.move(pdf_file, target_path)
                        logger.info(f"已移动: {file_name} -> done/{file_name}")

                        # 创建符号链接/记录
                        record_file = os.path.join(self.done_folder, f"{os.path.splitext(file_name)[0]}_info.txt")
                        with open(record_file, 'w', encoding='utf-8') as f:
                            f.write(f"原文件路径: {pdf_file}\n")
                            f.write(f"已报销的发票号码: {', '.join(reimbursed_numbers)}\n")
                            f.write(f"移动时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

                    results['moved_files'].append({
                        'original_path': pdf_file,
                        'target_path': target_path,
                        'invoice_numbers': reimbursed_numbers
                    })
                else:
                    results['non_reimbursed_files'] += 1
                    logger.info(f"发票 {os.path.basename(pdf_file)} 未报销，发票号码: {invoice_numbers}")

            except Exception as e:
                error_msg = f"处理文件 {os.path.basename(pdf_file)} 时出错: {e}"
                logger.error(error_msg)
                results['errors'].append(error_msg)

        return results

    def summary_report(self, results: Dict) -> None:
        """生成处理结果报告"""
        print("\n" + "="*50)
        print("📊 处理结果报告")
        print("="*50)
        print(f"📁 总文件数: {results['total_files']}")
        print(f"✅ 已报销文件数: {results['reimbursed_files']}")
        print(f"⏳ 未报销文件数: {results['non_reimbursed_files']}")
        print(f"📦 已移动文件数: {len(results['moved_files'])}")

        if results['errors']:
            print(f"❌ 错误数量: {len(results['errors'])}")

        if results['moved_files']:
            print(f"\n📋 已移动的文件:")
            for i, file_info in enumerate(results['moved_files'], 1):
                file_name = os.path.basename(file_info['original_path'])
                invoice_numbers = ', '.join(file_info['invoice_numbers'])
                print(f"  {i}. {file_name}")
                print(f"     发票号码: {invoice_numbers}")

        if results['errors']:
            print(f"\n❌ 错误信息:")
            for i, error in enumerate(results['errors'], 1):
                print(f"  {i}. {error}")

        print("\n" + "="*50)

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="检查tbd文件夹中已报销的发票并移动到done文件夹")
    parser.add_argument("--dry-run", action='store_true',
                       help="演练模式，只检查不移动文件")
    parser.add_argument("--refresh-cache", action='store_true',
                       help="强制刷新发票号码缓存")

    args = parser.parse_args()

    # 创建检查器
    checker = ReimbursedInvoiceChecker()

    # 强制刷新缓存（如果需要）
    if args.refresh_cache:
        print("🔄 强制刷新缓存...")
        checker.extractor.extract_all_invoice_numbers(force_refresh=True, include_tbd=True)

    print("🔍 开始检查tbd文件夹中的发票...")
    print(f"📁 TBD文件夹: {checker.tbd_folder}")
    print(f"📁 Done文件夹: {checker.done_folder}")

    if args.dry_run:
        print("🧪 演练模式 - 不会实际移动文件")
    else:
        print("🚀 正式模式 - 将移动已报销的文件")

    print()

    # 执行检查和移动
    results = checker.move_reimbursed_invoices(dry_run=args.dry_run)

    # 生成报告
    checker.summary_report(results)

if __name__ == "__main__":
    main()