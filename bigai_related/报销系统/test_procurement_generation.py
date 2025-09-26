#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试采购申请表生成功能
"""

from load_caigou_from_xlsx import generate_procurement_request
from datetime import datetime

def test_procurement_generation():
    """
    测试采购申请表生成功能
    """
    # 模拟订单数据（测试不同的金额格式）
    test_orders = [
        {
            '店铺名称': '测试店铺1',
            '商品名称': 'Arduino开发板套件',
            '型号规格': 'UNO R3',
            '商品数量': '2',
            '金额': '￥89.50'  # 带￥符号
        },
        {
            '店铺名称': '测试店铺2', 
            '商品名称': '杜邦线40根装',
            '型号规格': '公对公',
            '商品数量': '1',
            '金额': '15.80'   # 纯数字
        },
        {
            '店铺名称': '测试店铺3',
            '商品名称': '面包板实验板',
            '型号规格': '830孔',
            '商品数量': '3',
            '金额': 25.00     # 数值类型
        },
        {
            '店铺名称': '测试店铺4',
            '商品名称': '电阻套装',
            '型号规格': '1/4W',
            '商品数量': '1',
            '金额': 'RMB 12.30'  # 带RMB前缀
        }
    ]
    
    # 生成测试采购申请表
    today = datetime.now().strftime("%Y%m%d")
    test_file = f"/Users/lr-2002/project/lr_gist/bigai_related/报销系统/test_{today}_采购申请表.xlsx"
    
    print("开始生成测试采购申请表...")
    generate_procurement_request(test_orders, test_file)
    
    print(f"\n测试完成！")
    print(f"生成的测试文件: {test_file}")
    print("\n请检查生成的Excel文件是否符合要求：")
    print("1. 表头包含：物资一级分类、物资名称、规格型号、单位、数量、估算单价/元、估算总价/元")
    print("2. 物资一级分类都是'科研耗材'")
    print("3. 物资名称和规格型号都是商品名称")
    print("4. 单位都是'批'")
    print("5. 数量都是1")
    print("6. 估算单价和总价都是订单金额")

if __name__ == "__main__":
    test_procurement_generation()
