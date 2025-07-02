#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试自动化报销系统
"""

import os
import sys
from pathlib import Path
from expense_request import InvoiceProcessor, main

def test_basic_functionality():
    """测试基本功能"""
    print("=== 测试自动化报销系统 ===")
    
    # 创建处理器实例
    processor = InvoiceProcessor()
    print(f"✓ 处理器初始化成功")
    print(f"  - 项目负责人: {processor.project_manager}")
    print(f"  - 发票类型: {processor.invoice_type}")
    print(f"  - 付款类型: {processor.payment_type}")
    print(f"  - 科目明细: {processor.subject_detail}")
    
    # 测试文本提取功能
    test_text = """
    增值税电子普通发票
    发票号码：12345678901234567890
    货物或应税劳务名称：科研设备采购
    价税合计（大写）：壹仟贰佰叁拾肆元伍角陆分
    ￥1234.56
    """
    
    info = processor.extract_invoice_info(test_text, "test_invoice.pdf")
    print(f"\n✓ 信息提取测试:")
    for key, value in info.items():
        print(f"  - {key}: {value}")
    
    # 测试金额验证
    is_valid, message = processor.validate_amount("1234.56")
    print(f"\n✓ 金额验证测试: {message} ({'通过' if is_valid else '失败'})")
    
    print("\n=== 系统测试完成 ===")

def check_dependencies():
    """检查依赖包"""
    print("=== 检查系统依赖 ===")
    
    dependencies = [
        ('pandas', 'pandas'),
        ('openpyxl', 'openpyxl'),
        ('fitz', 'PyMuPDF'),
        ('pytesseract', 'pytesseract'),
        ('PIL', 'Pillow')
    ]
    
    missing_deps = []
    
    for module_name, package_name in dependencies:
        try:
            __import__(module_name)
            print(f"✓ {package_name}")
        except ImportError:
            print(f"✗ {package_name} - 未安装")
            missing_deps.append(package_name)
    
    # 检查Tesseract
    import subprocess
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"✓ Tesseract OCR - {version}")
        else:
            print("✗ Tesseract OCR - 未正确安装")
            missing_deps.append("tesseract")
    except FileNotFoundError:
        print("✗ Tesseract OCR - 未安装")
        missing_deps.append("tesseract")
    
    if missing_deps:
        print(f"\n缺少依赖: {', '.join(missing_deps)}")
        print("请运行以下命令安装:")
        if 'tesseract' in missing_deps:
            print("  brew install tesseract tesseract-lang")
        python_deps = [dep for dep in missing_deps if dep != 'tesseract']
        if python_deps:
            print(f"  pip install {' '.join(python_deps)}")
        return False
    else:
        print("\n✓ 所有依赖已安装")
        return True

def show_usage():
    """显示使用说明"""
    print("\n=== 使用说明 ===")
    print("1. 准备PDF发票文件，放在一个文件夹中")
    print("2. 运行命令:")
    print("   python expense_request.py '/path/to/invoice/folder'")
    print("3. 系统会在同一文件夹生成 YYYYMMDD_报销.xlsx 文件")
    print("\n示例:")
    print("   python expense_request.py '/Users/lr-2002/Documents/报销材料/6.27/发票'")

if __name__ == "__main__":
    # 检查依赖
    deps_ok = check_dependencies()
    
    if deps_ok:
        # 测试基本功能
        test_basic_functionality()
        
        # 显示使用说明
        show_usage()
    else:
        print("\n请先安装缺少的依赖包")
        sys.exit(1)
