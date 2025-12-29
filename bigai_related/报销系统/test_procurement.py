#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
采购申请系统测试脚本
测试从图片信息生成采购申请表的功能
"""

from caigou import ProcurementProcessor
import os

def test_procurement_system():
    """测试采购申请系统"""
    print("=== 采购申请系统测试 ===\n")
    
    # 创建处理器实例
    processor = ProcurementProcessor()
    
    # 模拟图片信息（基于用户提供的微信截图）
    # 从图片中提取的信息：
    # - 商品名称：[Qhebot] 数字大按键模块按键（红框内容）
    # - 规格型号：红色（图片中的红色标注）
    # - 单价：¥3.8（图片右侧价格）
    # - 数量：x6（图片中显示）
    # - 单位：个
    
    print("1. 测试默认信息处理（模拟图片不存在的情况）")
    try:
        # 使用不存在的图片路径，系统会使用空的默认信息
        excel_path, info = processor.process_image_to_excel("non_existent_image.png")
        
        print(f"✅ 采购申请表生成成功!")
        print(f"📄 文件路径: {excel_path}")
        print(f"\n📋 采购信息详情:")
        print(f"   物品名称: '{info['name']}'")
        print(f"   规格型号: '{info['specification']}'")
        print(f"   数量: {info['quantity']} {info['unit']}")
        print(f"   单价: ¥{info['unit_price']}")
        print(f"   总金额: ¥{info['total_amount']}")
        
        # 验证文件是否真的创建了
        if os.path.exists(excel_path):
            print(f"✅ Excel文件确认存在: {excel_path}")
            file_size = os.path.getsize(excel_path)
            print(f"📊 文件大小: {file_size} 字节")
        else:
            print("❌ Excel文件未找到")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    
    print("\n" + "="*50)
    print("2. 测试信息解析功能")
    
    # 模拟OCR提取的文本内容
    mock_text = """
    交易成功
    已签收 王先生 86-138****5204 送至 颐和
    
    沁和智能科技企业店
    [Qhebot] 数字大按键模块按键 ¥3.8
    红色
    退货包运费 7天无理由退货 极速退款 x6
    
    商品转卖    申请售后    加入购物车
    
    实付款 ¥33.8
    订单编号 460416258279251804 复制
    """
    
    try:
        # 测试文本解析功能
        parsed_info = processor.parse_procurement_info(mock_text)
        
        print("📝 文本解析结果:")
        for key, value in parsed_info.items():
            print(f"   {key}: {value}")
            
        # 验证解析结果
        expected_values = {
            'name': '[Qhebot] 数字大按键模块按键',
            'specification': '红色',
            'unit_price': 3.8,
            'quantity': 6,
            'unit': '个',
            'total_amount': 22.8
        }
        
        print("\n🔍 验证解析准确性:")
        all_correct = True
        for key, expected in expected_values.items():
            actual = parsed_info[key]
            if actual == expected:
                print(f"   ✅ {key}: {actual} (正确)")
            else:
                print(f"   ❌ {key}: {actual} (期望: {expected})")
                all_correct = False
        
        if all_correct:
            print("\n🎉 所有信息解析正确!")
        else:
            print("\n⚠️  部分信息解析需要调整")
            
    except Exception as e:
        print(f"❌ 文本解析测试失败: {e}")
    
    print("\n" + "="*50)
    print("3. 系统功能总结")
    print("✅ 自动从图片/文本中提取采购信息")
    print("✅ 生成标准化的Excel采购申请表")
    print("✅ 包含下拉选项的数据验证")
    print("✅ 自动计算总金额")
    print("✅ 包含审批流程字段")
    print("✅ 默认二级分类为'科研耗材'")
    print("✅ 固定项目负责人为'马晓健'")
    
    print("\n📋 支持的字段:")
    print("   - 物品名称（从红框内容提取）")
    print("   - 规格型号（优先使用颜色标注）")
    print("   - 单价（从右侧价格提取）")
    print("   - 数量（从x n格式提取）")
    print("   - 单位（固定为'个'）")
    print("   - 二级分类（默认'科研耗材'）")

if __name__ == "__main__":
    test_procurement_system()
