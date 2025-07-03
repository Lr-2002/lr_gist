#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化报销信息生成系统
功能：
1. 读取指定路径下的所有PDF发票
2. 使用OCR识别发票信息
3. 按照模板格式生成Excel报销表
"""

import os
import re
import pandas as pd
from datetime import datetime
from pathlib import Path
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import logging
from typing import List, Dict, Optional
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InvoiceProcessor:
    """发票处理器"""
    
    def __init__(self):
        self.project_manager = "马晓健"
        
        # 发票类型选项
        self.invoice_type_options = {
            "1": "增值税专用发票",
            "2": "增值税电子普通发票",
            "3": "增值税普通发票",
            "4": "机动车销售统一发票",
            "5": "其他"
        }
        
        # 付款类型选项
        self.payment_type_options = {
            "1": "科研费用",
            "2": "办公费用",
            "3": "差旅费用",
            "4": "会议费用",
            "5": "培训费用",
            "6": "其他"
        }
        
        # 科目明细选项
        self.subject_detail_options = {
            "1": "科研耗材",
            "2": "办公用品",
            "3": "设备采购",
            "4": "软件服务",
            "5": "咨询服务",
            "6": "其他"
        }
        
        # 默认选择（可以根据需要修改）
        self.invoice_type = self.invoice_type_options["2"]  # 增值税电子普通发票
        self.payment_type = self.payment_type_options["1"]  # 科研费用
        self.subject_detail = self.subject_detail_options["1"]  # 科研耗材
        
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
                ocr_text = pytesseract.image_to_string(img, lang='chi_sim+eng')
                text += ocr_text + "\n"
            
            doc.close()
            return text
        except Exception as e:
            logger.error(f"OCR识别失败 {pdf_path}: {e}")
            return ""
    
    def extract_invoice_info(self, text: str, filename: str) -> Dict[str, str]:
        """从文本中提取发票信息"""
        info = {
            "付款明细原因": "",
            "项目负责人": self.project_manager,
            "发票类型": self.invoice_type,
            "发票号码": "",
            "付款类型": self.payment_type,
            "科目明细": self.subject_detail,
            "金额": ""
        }
        
        # # 提取发票号码 - 通常是数字组合
        invoice_number_patterns = [
            r'发票号码[：:](\d{8,})',
            r'发票代码[：:]?(\d{10,12})',
            r'No[.:]?\s*(\d{8,})',
            r'(\d{20,})'
        ]
        # invoice_number_patterns = [
        #     r'发票号码[：:：\s]*([0-9]{8})',
        #     r'Invoice No[.:]?\s*([0-9]{8})',
        #     r'No[.:]?\s*([0-9]{8})'
        # ] 
        for pattern in invoice_number_patterns:
            match = re.search(pattern, text)
            if match:
                info["发票号码"] = match.group(1)
                break
        

        # 提取金额 - 优先从小写金额中提取
        amount_patterns = [
            # 优先匹配小写后的金额格式
            r'小写[）)]?[：:：\s]*[￥¥]?([\d,]+\.\d{2})',
            r'\(小写\)[：:：\s]*[￥¥]?([\d,]+\.\d{2})',
            # 价税合计后的金额
            r'价税合计[（(]大写[）)]?[：:：\s]*[^\d]*?[￥¥]?([\d,]+\.\d{2})',
            # 直接的金额格式
            r'[￥¥]([\d,]+\.\d{2})(?=\s*$|\s*元|\n)',
            # 合计金额
            r'合计[：:：\s]*[￥¥]?([\d,]+\.\d{2})',
            # 应付金额
            r'应付[：:：\s]*[￥¥]?([\d,]+\.\d{2})'
        ]
        for pattern in amount_patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)
            if matches:
                # 取第一个匹配的金额
                amount_str = matches[0].replace(',', '')
                try:
                    amount = float(amount_str)
                    if amount > 0 and amount < 1000000:  # 合理的金额范围
                        info["金额"] = f"{amount:.2f}"
                        break
                except ValueError:
                    continue
        # 直接使用文件名作为付款明细原因
        base_name = os.path.splitext(filename)[0]
        info["付款明细原因"] = base_name
        
        return info
    
    def validate_amount(self, amount_str: str) -> tuple[bool, str]:
        """验证金额是否合理"""
        if not amount_str:
            return False, "未识别到金额"
        
        try:
            amount = float(amount_str)
            if amount <= 0:
                return False, "金额不能为零或负数"
            if amount > 100000:  # 超过10万的金额需要确认
                return False, f"金额过大({amount:.2f}元)，请确认"
            return True, "金额正常"
        except ValueError:
            return False, "金额格式错误"
    
    def process_invoices(self, folder_path: str) -> List[Dict[str, str]]:
        seen_invoice_numbers = set()  # 用于去重
        """处理文件夹中的所有发票"""
        folder_path = Path(folder_path)
        if not folder_path.exists():
            raise FileNotFoundError(f"路径不存在: {folder_path}")
        
        invoice_data = []
        pdf_files = list(folder_path.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"在 {folder_path} 中未找到PDF文件")
            return invoice_data
        
        logger.info(f"找到 {len(pdf_files)} 个PDF文件")
        
        for pdf_file in pdf_files:
            logger.info(f"处理文件: {pdf_file.name}")
            
            # 首先尝试直接提取文本
            text = self.extract_text_from_pdf(str(pdf_file))
            
            # 如果文本提取效果不好，使用OCR
            if len(text.strip()) < 100:  # 文本太少，可能需要OCR
                logger.info(f"文本提取不足，使用OCR: {pdf_file.name}")
                text = self.pdf_to_image_ocr(str(pdf_file))
            
            if text.strip():
                info = self.extract_invoice_info(text, pdf_file.name)
                
                # 检查发票号码是否重复
                invoice_number = info["发票号码"]
                if invoice_number and invoice_number != "识别失败":
                    if invoice_number in seen_invoice_numbers:
                        logger.warning(f"发现重复发票号码: {invoice_number} (文件: {pdf_file.name})")
                        if "备注" not in info:
                            info["备注"] = ""
                        info["备注"] += f"重复发票号码: {invoice_number}; "
                    else:
                        seen_invoice_numbers.add(invoice_number) 
                # 验证金额
                is_valid, message = self.validate_amount(info["金额"])
                if not is_valid:
                    logger.warning(f"文件 {pdf_file.name} 金额验证失败: {message}")
                    if "备注" not in info:
                        info["备注"] = ""
                    info["备注"] += f"金额验证: {message}; "
                
                invoice_data.append(info)
                logger.info(f"成功处理: {pdf_file.name}, 金额: {info['金额']}")
            else:
                logger.error(f"无法从 {pdf_file.name} 中提取文本")
                # 创建一个基本记录
                info = {
                    "付款明细原因": pdf_file.stem,
                    "项目负责人": self.project_manager,
                    "发票类型": self.invoice_type,
                    "发票号码": "识别失败",
                    "付款类型": self.payment_type,
                    "科目明细": self.subject_detail,
                    "金额": "0.00",
                    "备注": "OCR识别失败，请手动填写"
                }
                invoice_data.append(info)
        
        return invoice_data
    
    def create_excel_report(self, invoice_data: List[Dict[str, str]], output_path: str):
        """创建Excel报销表"""
        if not invoice_data:
            logger.warning("没有数据可以写入Excel")
            return
        
        # 创建DataFrame
        df = pd.DataFrame(invoice_data)
        
        # 确保列的顺序（不包含备注列）
        columns = ["付款明细原因", "项目负责人", "发票类型", "发票号码", "付款类型", "科目明细", "金额"]
        df = df.reindex(columns=columns, fill_value="")
        
        # 写入Excel
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='报销明细', index=False, startrow=1)  # 从第2行开始写入数据
            
            # 获取工作表进行格式化
            worksheet = writer.sheets['报销明细']
            
            # 添加标题行"明细表1"
            worksheet['A1'] = '明细表1'
            # 合并标题行单元格（A1到G1）
            worksheet.merge_cells('A1:G1')
            # 设置标题格式
            title_cell = worksheet['A1']
            title_cell.font = Font(bold=True, size=14)
            title_cell.alignment = Alignment(horizontal='center', vertical='center')
            
            # 设置列宽
            column_widths = {
                'A': 30,  # 付款明细原因
                'B': 15,  # 项目负责人
                'C': 20,  # 发票类型
                'D': 20,  # 发票号码
                'E': 15,  # 付款类型
                'F': 15,  # 科目明细
                'G': 12,  # 金额
            }
            
            for col, width in column_widths.items():
                worksheet.column_dimensions[col].width = width
            
            # 设置表头格式（现在在第2行）
            header_font = Font(bold=True)
            header_alignment = Alignment(horizontal='center', vertical='center')
            
            for cell in worksheet[2]:  # 表头现在在第2行
                cell.font = header_font
                cell.alignment = header_alignment
            
            # 设置边框
            thin_border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
            
            for row in worksheet.iter_rows():
                for cell in row:
                    cell.border = thin_border
                    if cell.column == 7:  # 金额列
                        cell.alignment = Alignment(horizontal='right')
            
            # 添加数据验证（下拉选项）
            from openpyxl.worksheet.datavalidation import DataValidation
            
            # 发票类型下拉选项（C列）
            invoice_type_options = ','.join(self.invoice_type_options.values())
            dv_invoice_type = DataValidation(type="list", formula1=f'"{invoice_type_options}"')
            dv_invoice_type.error = '请选择有效的发票类型'
            dv_invoice_type.errorTitle = '输入错误'
            worksheet.add_data_validation(dv_invoice_type)
            dv_invoice_type.add(f'C3:C{len(df)+2}')  # 从第3行开始到数据结束
            
            # 付款类型下拉选项（E列）
            payment_type_options = ','.join(self.payment_type_options.values())
            dv_payment_type = DataValidation(type="list", formula1=f'"{payment_type_options}"')
            dv_payment_type.error = '请选择有效的付款类型'
            dv_payment_type.errorTitle = '输入错误'
            worksheet.add_data_validation(dv_payment_type)
            dv_payment_type.add(f'E3:E{len(df)+2}')  # 从第3行开始到数据结束
            
            # 科目明细下拉选项（F列）
            subject_detail_options = ','.join(self.subject_detail_options.values())
            dv_subject_detail = DataValidation(type="list", formula1=f'"{subject_detail_options}"')
            dv_subject_detail.error = '请选择有效的科目明细'
            dv_subject_detail.errorTitle = '输入错误'
            worksheet.add_data_validation(dv_subject_detail)
            dv_subject_detail.add(f'F3:F{len(df)+2}')  # 从第3行开始到数据结束
        
        logger.info(f"Excel报表已保存到: {output_path}")
        logger.info("已为发票类型、付款类型、科目明细添加下拉选项")

def main(folder_path: str):
    """主函数"""
    try:
        processor = InvoiceProcessor()
        
        # 处理发票
        logger.info(f"开始处理发票文件夹: {folder_path}")
        invoice_data = processor.process_invoices(folder_path)
        
        if not invoice_data:
            logger.error("没有成功处理任何发票")
            return
        
        # 生成输出文件名
        current_date = datetime.now().strftime("%Y%m%d")
        output_filename = f"{current_date}_报销.xlsx"
        
        # 输出到同一目录
        folder_path_obj = Path(folder_path)
        output_path = folder_path_obj / output_filename
        
        # 创建Excel报表
        processor.create_excel_report(invoice_data, str(output_path))
        
        # 打印摘要
        total_amount = sum(float(item["金额"]) for item in invoice_data if item["金额"] and item["金额"] != "0.00")
        logger.info(f"处理完成！")
        logger.info(f"- 处理发票数量: {len(invoice_data)}")
        logger.info(f"- 总金额: {total_amount:.2f}元")
        logger.info(f"- 输出文件: {output_path}")
        
        # 检查是否有问题需要注意
        problems = [item for item in invoice_data if "备注" in item and item["备注"]]
        if problems:
            logger.warning("以下发票需要手动检查:")
            for item in problems:
                logger.warning(f"- {item['付款明细原因']}: {item['备注']}")
        
    except Exception as e:
        logger.error(f"处理过程中出现错误: {e}")
        raise

if __name__ == "__main__":
    import sys
    
    # if len(sys.argv) != 2:
    #     print("使用方法: python expense_request.py <发票文件夹路径>")
    #     print("示例: python expense_request.py '/Users/lr-2002/Documents/报销材料/6.27/发票'")
    #     sys.exit(1)
    
    # folder_path = sys.argv[1]
    folder_path = '/Users/lr-2002/Documents/报销材料/6.27/发票'
    main(folder_path)