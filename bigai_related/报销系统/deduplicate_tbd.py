#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tbd文件夹去重工具
功能：
1. 检查tbd文件夹中具有相同发票号码的重复文件
2. 保留一个文件，删除其他重复文件
3. 生成去重报告
"""

import os
import re
import shutil
import hashlib
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import logging
from pathlib import Path
from typing import Set, Dict, List, Optional, Tuple
from collections import defaultdict

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class TBDDeduplicator:
    """TBD文件夹去重器"""

    def __init__(self):
        """初始化去重器"""
        self.base_path = "/Users/lr-2002/Documents/报销材料/"
        self.tbd_folder = os.path.join(self.base_path, "tbd")
        self.duplicates_folder = os.path.join(self.tbd_folder, "duplicates")

        # 创建duplicates文件夹存放重复文件
        Path(self.duplicates_folder).mkdir(parents=True, exist_ok=True)

        # 发票号码的正则表达式模式
        self.invoice_number_patterns = [
            r"发票号码[：:](\d{8,})",
            r"发票代码[：:]?(\d{10,12})",
            r"No[.:]?\s*(\d{8,})",
            r"(\d{20,})",
        ]

    def get_file_hash(self, file_path: str) -> str:
        """计算文件的MD5哈希值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

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
        """获取tbd文件夹中的所有PDF文件（排除done和duplicates文件夹）"""
        tbd_path = Path(self.tbd_folder)
        excluded_folders = ['done', 'duplicates']

        pdf_files = []
        for pdf_file in tbd_path.glob("*.pdf"):
            exclude = False
            for folder in excluded_folders:
                excluded_path = tbd_path / folder
                try:
                    if pdf_file.resolve().is_relative_to(excluded_path.resolve()):
                        exclude = True
                        break
                except AttributeError:
                    # Python < 3.9 没有 is_relative_to 方法
                    if str(pdf_file.resolve()).startswith(str(excluded_path.resolve())):
                        exclude = True
                        break

            if not exclude:
                pdf_files.append(str(pdf_file))

        return sorted(pdf_files)

    def find_duplicates(self) -> Dict:
        """
        查找重复文件

        Returns:
            包含重复文件信息的字典
        """
        logger.info("开始查找tbd文件夹中的重复文件...")

        pdf_files = self.get_tbd_pdf_files()

        if not pdf_files:
            logger.info("tbd文件夹中没有PDF文件")
            return {
                'total_files': 0,
                'files_with_invoices': 0,
                'duplicate_groups': [],
                'exact_duplicates': [],
                'no_invoice_files': []
            }

        logger.info(f"找到 {len(pdf_files)} 个PDF文件")

        # 按发票号码分组
        invoice_to_files = defaultdict(list)
        # 按文件哈希分组（用于查找完全相同的文件）
        hash_to_files = defaultdict(list)

        results = {
            'total_files': len(pdf_files),
            'files_with_invoices': 0,
            'duplicate_groups': [],
            'exact_duplicates': [],
            'no_invoice_files': []
        }

        # 处理每个文件
        for pdf_file in pdf_files:
            try:
                # 计算文件哈希
                file_hash = self.get_file_hash(pdf_file)
                hash_to_files[file_hash].append(pdf_file)

                # 提取发票号码
                invoice_numbers = self.extract_invoice_numbers_from_pdf(pdf_file)

                if invoice_numbers:
                    results['files_with_invoices'] += 1
                    for invoice_number in invoice_numbers:
                        invoice_to_files[invoice_number].append(pdf_file)
                else:
                    results['no_invoice_files'].append(pdf_file)
                    logger.warning(f"文件 {os.path.basename(pdf_file)} 中未找到发票号码")

            except Exception as e:
                logger.error(f"处理文件 {os.path.basename(pdf_file)} 时出错: {e}")

        # 查找发票号码重复的文件
        for invoice_number, files in invoice_to_files.items():
            if len(files) > 1:
                # 创建重复组信息
                duplicate_group = {
                    'invoice_number': invoice_number,
                    'files': []
                }

                for file_path in files:
                    file_info = {
                        'path': file_path,
                        'name': os.path.basename(file_path),
                        'size': os.path.getsize(file_path),
                        'hash': self.get_file_hash(file_path),
                        'modified': os.path.getmtime(file_path)
                    }
                    duplicate_group['files'].append(file_info)

                # 按修改时间排序，最新的文件排在前面
                duplicate_group['files'].sort(key=lambda x: x['modified'], reverse=True)

                results['duplicate_groups'].append(duplicate_group)

        # 查找完全相同的文件
        for file_hash, files in hash_to_files.items():
            if len(files) > 1:
                exact_duplicate = {
                    'hash': file_hash,
                    'files': [os.path.basename(f) for f in files],
                    'paths': files
                }
                results['exact_duplicates'].append(exact_duplicate)

        return results

    def select_file_to_keep(self, files: List[Dict]) -> Dict:
        """
        选择要保留的文件

        Args:
            files: 文件信息列表

        Returns:
            要保留的文件信息
        """
        # 选择最新的文件作为主文件
        return files[0]  # 已经按修改时间降序排列

    def deduplicate_files(self, dry_run: bool = False) -> Dict:
        """
        执行去重操作

        Args:
            dry_run: 是否为演练模式

        Returns:
            处理结果
        """
        # 查找重复文件
        duplicate_results = self.find_duplicates()

        if not duplicate_results['duplicate_groups'] and not duplicate_results['exact_duplicates']:
            logger.info("没有发现重复文件")
            return {
                'duplicate_groups_processed': 0,
                'files_deleted': 0,
                'exact_duplicates_processed': 0,
                'errors': []
            }

        results = {
            'duplicate_groups_processed': 0,
            'files_deleted': 0,
            'exact_duplicates_processed': 0,
            'deleted_files': [],
            'kept_files': [],
            'errors': []
        }

        # 处理发票号码重复的文件
        for group in duplicate_results['duplicate_groups']:
            try:
                files = group['files']
                invoice_number = group['invoice_number']

                logger.info(f"处理发票号码 {invoice_number} 的重复文件:")
                for file_info in files:
                    logger.info(f"  - {file_info['name']} ({file_info['size']} bytes)")

                # 选择要保留的文件
                file_to_keep = self.select_file_to_keep(files)
                files_to_delete = [f for f in files if f['hash'] != file_to_keep['hash']]

                # 如果所有文件都不同（只是发票号码相同），保留最新的，移动其他的
                if not files_to_delete:
                    files_to_delete = files[1:]  # 保留第一个，删除其余的

                logger.info(f"保留: {file_to_keep['name']}")
                logger.info(f"将要移动的重复文件: {len(files_to_delete)} 个")

                results['kept_files'].append(file_to_keep['path'])

                # 移动重复文件
                for file_info in files_to_delete:
                    file_path = file_info['path']
                    file_name = file_info['name']
                    target_path = os.path.join(self.duplicates_folder, f"{invoice_number}_{file_name}")

                    if not dry_run:
                        shutil.move(file_path, target_path)
                        logger.info(f"已移动: {file_name} -> duplicates/{invoice_number}_{file_name}")

                    results['deleted_files'].append({
                        'original_path': file_path,
                        'target_path': target_path,
                        'invoice_number': invoice_number,
                        'reason': '发票号码重复'
                    })
                    results['files_deleted'] += 1

                results['duplicate_groups_processed'] += 1

            except Exception as e:
                error_msg = f"处理发票号码 {group.get('invoice_number', 'unknown')} 的重复文件时出错: {e}"
                logger.error(error_msg)
                results['errors'].append(error_msg)

        # 处理完全相同的文件
        for exact_group in duplicate_results['exact_duplicates']:
            try:
                files = exact_group['paths']
                file_name = exact_group['files'][0]  # 所有文件名应该相同

                if len(files) <= 1:
                    continue

                logger.info(f"处理完全相同的文件: {file_name}")
                for file_path in files:
                    logger.info(f"  - {file_path}")

                # 保留第一个文件，移动其余的
                file_to_keep = files[0]
                files_to_delete = files[1:]

                logger.info(f"保留: {file_to_keep}")

                results['kept_files'].append(file_to_keep)

                # 移动完全相同的文件
                for i, file_path in enumerate(files_to_delete, 1):
                    base_name, ext = os.path.splitext(file_name)
                    target_name = f"{base_name}_duplicate_{i}{ext}"
                    target_path = os.path.join(self.duplicates_folder, target_name)

                    if not dry_run:
                        shutil.move(file_path, target_path)
                        logger.info(f"已移动: {os.path.basename(file_path)} -> duplicates/{target_name}")

                    results['deleted_files'].append({
                        'original_path': file_path,
                        'target_path': target_path,
                        'reason': '文件完全相同'
                    })
                    results['files_deleted'] += 1

                results['exact_duplicates_processed'] += 1

            except Exception as e:
                error_msg = f"处理完全相同的文件时出错: {e}"
                logger.error(error_msg)
                results['errors'].append(error_msg)

        return results

    def generate_report(self, duplicate_results: Dict, dedup_results: Dict) -> None:
        """生成详细报告"""
        print("\n" + "="*60)
        print("🔍 TBD文件夹重复文件检查报告")
        print("="*60)

        print(f"\n📊 文件统计:")
        print(f"  总文件数: {duplicate_results['total_files']}")
        print(f"  包含发票号码的文件: {duplicate_results['files_with_invoices']}")
        print(f"  无发票号码的文件: {len(duplicate_results['no_invoice_files'])}")

        print(f"\n🔄 重复文件统计:")
        print(f"  发票号码重复组数: {len(duplicate_results['duplicate_groups'])}")
        print(f"  完全相同的文件组数: {len(duplicate_results['exact_duplicates'])}")

        if duplicate_results['duplicate_groups']:
            print(f"\n📋 发票号码重复详情:")
            for i, group in enumerate(duplicate_results['duplicate_groups'], 1):
                invoice_number = group['invoice_number']
                files = group['files']
                print(f"  {i}. 发票号码: {invoice_number}")
                print(f"     重复文件数: {len(files)}")
                for j, file_info in enumerate(files, 1):
                    size_mb = file_info['size'] / (1024*1024)
                    modified_time = __import__('datetime').datetime.fromtimestamp(file_info['modified'])
                    print(f"     {j}. {file_info['name']}")
                    print(f"        大小: {size_mb:.2f} MB, 修改时间: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")

        if duplicate_results['exact_duplicates']:
            print(f"\n📋 完全相同的文件:")
            for i, group in enumerate(duplicate_results['exact_duplicates'], 1):
                file_hash = group['hash'][:8]  # 只显示前8位
                files = group['files']
                print(f"  {i}. 哈希 {file_hash}...: {len(files)} 个相同文件")
                for file_name in files:
                    print(f"     - {file_name}")

        print(f"\n🗑️ 去重操作结果:")
        print(f"  处理的发票重复组数: {dedup_results['duplicate_groups_processed']}")
        print(f"  处理的完全相同组数: {dedup_results['exact_duplicates_processed']}")
        print(f"  移动的文件数量: {dedup_results['files_deleted']}")
        print(f"  保留的文件数量: {len(dedup_results['kept_files'])}")

        if dedup_results['errors']:
            print(f"\n❌ 错误信息:")
            for i, error in enumerate(dedup_results['errors'], 1):
                print(f"  {i}. {error}")

        print(f"\n" + "="*60)

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="检查并清理tbd文件夹中的重复文件")
    parser.add_argument("--dry-run", action='store_true',
                       help="演练模式，只检查不移动文件")

    args = parser.parse_args()

    # 创建去重器
    deduplicator = TBDDeduplicator()

    print("🔍 开始检查tbd文件夹中的重复文件...")
    print(f"📁 TBD文件夹: {deduplicator.tbd_folder}")
    print(f"📁 Duplicates文件夹: {deduplicator.duplicates_folder}")

    if args.dry_run:
        print("🧪 演练模式 - 不会实际移动文件")
    else:
        print("🚀 正式模式 - 将移动重复文件")

    print()

    # 查找重复文件
    duplicate_results = deduplicator.find_duplicates()

    # 生成检查报告
    deduplicator.generate_report(duplicate_results, {'duplicate_groups_processed': 0, 'files_deleted': 0, 'exact_duplicates_processed': 0, 'kept_files': [], 'errors': []})

    # 如果没有重复文件，直接退出
    if not duplicate_results['duplicate_groups'] and not duplicate_results['exact_duplicates']:
        print("✅ 没有发现重复文件，无需处理。")
        return

    # 询问是否继续
    if args.dry_run:
        print("\n🧪 演练模式完成，以上为检查结果。")
        return

    print("\n❓ 是否继续执行去重操作？(y/N): ", end="")
    response = input().strip().lower()

    if response not in ['y', 'yes']:
        print("❌ 用户取消操作。")
        return

    # 执行去重
    print("\n🔄 开始执行去重操作...")
    dedup_results = deduplicator.deduplicate_files(dry_run=False)

    # 生成最终报告
    print("\n" + "="*60)
    print("🎉 去重操作完成！")
    deduplicator.generate_report(duplicate_results, dedup_results)

if __name__ == "__main__":
    main()