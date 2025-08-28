#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
采购申请系统测试脚本
测试空默认值功能
"""

from caigou import ProcurementProcessor
import os

def test_empty_defaults():
    """测试空默认值功能"""
    print("=== 采购申请系统空默认值测试 ===\n")
    
    # 创建处理器实例
    processor = ProcurementProcessor()
    
    print("1. 测试图片不存在时的空默认值")
    try:
        # 使用不存在的图片路径，系统会使用默认信息
        excel_path, info = processor.process_image_to_excel("non_existent_image.png", "test_empty_defaults.xlsx")
        
        print(f"✅ 采购申请表生成成功!")
        print(f"📄 文件路径: {excel_path}")
        print(f"\n📋 采购信息详情:")
        for key, value in info.items():
            print(f"   {key}: {value}")
        
        # 验证文件是否真的创建了
        if os.path.exists(excel_path):
            print(f"✅ Excel文件确认存在: {excel_path}")
        else:
            print("❌ Excel文件未找到")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    
    print("\n" + "="*50)
    print("测试完成!")
    
    # 清理生成的测试文件
    try:
        if os.path.exists("test_empty_defaults.xlsx"):
            os.remove("test_empty_defaults.xlsx")
            print("已清理测试文件: test_empty_defaults.xlsx")
    except Exception as e:
        print(f"清理测试文件时出错: {e}")

if __name__ == "__main__":
    test_empty_defaults()
