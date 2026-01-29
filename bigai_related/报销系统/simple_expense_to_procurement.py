#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版支出申请表转采购申请表转换工具
功能：
1. 读取通过expense_request.py生成的支出申请表
2. 将报销明细转换为采购申请表格式
3. 生成标准格式的采购申请Excel文件
"""

import pandas as pd
from datetime import datetime
import os
import logging
from typing import List, Dict, Optional
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SimpleExpenseToProcurementConverter:
    """简化版支出申请表转采购申请表转换器"""

    def __init__(self):
        """初始化转换器"""
        # 固定配置信息
        self.project_manager = "马晓健"
        self.department = "人工智能研究院"

    def read_expense_excel(self, excel_path: str) -> List[Dict[str, str]]:
        """
        读取支出申请表Excel文件

        Args:
            excel_path: 支出申请表Excel文件路径

        Returns:
            包含支出明细的列表
        """
        try:
            logger.info(f"正在读取支出申请表: {excel_path}")

            # 使用pandas读取
            df = pd.read_excel(excel_path, header=None)

            # 查找表头行
            header_row = None
            for idx, row in df.iterrows():
                if any("付款明细原因" in str(cell) for cell in row if pd.notna(cell)):
                    header_row = idx
                    break

            if header_row is None:
                raise ValueError("未找到表头行")

            # 重新读取，使用找到的表头行
            df = pd.read_excel(excel_path, header=header_row)

            expense_data = []

            # 获取列名映射
            column_mapping = {}
            for col in df.columns:
                col_str = str(col)
                if "付款明细原因" in col_str:
                    column_mapping["付款明细原因"] = col
                elif "金额" in col_str:
                    column_mapping["金额"] = col
                elif "发票号码" in col_str:
                    column_mapping["发票号码"] = col
                elif "发票类型" in col_str:
                    column_mapping["发票类型"] = col
                elif "项目负责人" in col_str:
                    column_mapping["项目负责人"] = col

            logger.info(f"找到表头，列映射: {column_mapping}")

            # 处理每一行数据
            for idx, row in df.iterrows():
                # 跳过空行
                if row.isna().all():
                    continue

                # 提取数据
                expense_item = {}

                # 付款明细原因（必需）
                reason = (
                    row[column_mapping["付款明细原因"]]
                    if "付款明细原因" in column_mapping
                    else None
                )
                if pd.notna(reason) and str(reason).strip():
                    expense_item["付款明细原因"] = str(reason).strip()
                else:
                    continue  # 跳过没有付款明细原因的行

                # 金额（必需）
                amount = (
                    row[column_mapping["金额"]] if "金额" in column_mapping else None
                )
                if pd.notna(amount):
                    try:
                        expense_item["金额"] = float(str(amount).replace(",", ""))
                    except (ValueError, TypeError):
                        logger.warning(f"第{idx}行金额格式错误: {amount}")
                        continue
                else:
                    continue  # 跳过没有金额的行

                # 可选字段
                if "发票号码" in column_mapping and pd.notna(
                    row[column_mapping["发票号码"]]
                ):
                    expense_item["发票号码"] = str(
                        row[column_mapping["发票号码"]]
                    ).strip()

                if "发票类型" in column_mapping and pd.notna(
                    row[column_mapping["发票类型"]]
                ):
                    expense_item["发票类型"] = str(
                        row[column_mapping["发票类型"]]
                    ).strip()

                if "项目负责人" in column_mapping and pd.notna(
                    row[column_mapping["项目负责人"]]
                ):
                    expense_item["项目负责人"] = str(
                        row[column_mapping["项目负责人"]]
                    ).strip()

                if expense_item:
                    expense_data.append(expense_item)

            logger.info(f"成功读取 {len(expense_data)} 条支出记录")
            return expense_data

        except Exception as e:
            logger.error(f"读取Excel文件失败 {excel_path}: {e}")
            return []

    def convert_to_procurement_format(
        self, expense_data: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """
        将支出数据转换为采购申请表格式

        Args:
            expense_data: 支出明细数据

        Returns:
            采购申请表格式数据
        """
        logger.info("开始转换支出数据为采购申请表格式")

        procurement_data = []

        for idx, item in enumerate(expense_data, 1):
            # 基本映射
            procurement_item = {
                "序号": idx,
                "采购类型": self.determine_procurement_type(
                    item.get("付款明细原因", "")
                ),
                "物品名称": item.get("付款明细原因", ""),
                "规格型号": item.get("付款明细原因", ""),  # 默认使用物品名称作为规格
                "单位": self.determine_unit(item.get("付款明细原因", "")),
                "数量": 1,  # 默认数量为1
                "单价(元)": item.get("金额", 0),
                "金额(元)": item.get("金额", 0),
                "二级分类": self.determine_secondary_category(
                    item.get("付款明细原因", "")
                ),
                "备注": f"来源：支出申请表，发票号码：{item.get('发票号码', '未知')}",
            }

            # 如果金额较大，可能需要调整数量和单价
            amount = procurement_item["金额(元)"]
            if amount > 1000:
                # 对于大额物品，假设可能是多个相同物品
                procurement_item["数量"] = self.estimate_quantity(
                    item.get("付款明细原因", "")
                )
                procurement_item["单价(元)"] = round(
                    amount / procurement_item["数量"], 2
                )

            procurement_data.append(procurement_item)

        logger.info(f"转换完成，生成 {len(procurement_data)} 条采购记录")
        return procurement_data

    def determine_procurement_type(self, item_name: str) -> str:
        """
        根据物品名称确定采购类型

        Args:
            item_name: 物品名称

        Returns:
            采购类型
        """
        item_name_lower = item_name.lower()

        # 设备相关
        if any(
            keyword in item_name_lower
            for keyword in ["轴承", "电机", "舵机", "充电器", "设备", "电机线", "转轴"]
        ):
            return "科研设备"

        # 耗材相关
        if any(
            keyword in item_name_lower
            for keyword in ["螺丝", "胶带", "扎带", "焊", "双面胶", "热熔胶", "耗材"]
        ):
            return "耗材用品"

        # 软件相关
        if any(keyword in item_name_lower for keyword in ["软件", "许可", "系统"]):
            return "软件许可"

        # 办公相关
        if any(
            keyword in item_name_lower for keyword in ["办公", "纸", "笔", "桌", "椅"]
        ):
            return "办公设备"

        # 默认为科研设备
        return "科研设备"

    def determine_secondary_category(self, item_name: str) -> str:
        """
        根据物品名称确定二级分类

        Args:
            item_name: 物品名称

        Returns:
            二级分类
        """
        # 统一返回"低值易耗品"
        return "低值易耗品"

    def determine_unit(self, item_name: str) -> str:
        """
        根据物品名称确定单位

        Args:
            item_name: 物品名称

        Returns:
            单位
        """
        item_name_lower = item_name.lower()

        # 常见单位映射
        if "螺丝" in item_name_lower or "轴承" in item_name_lower:
            return "个"
        elif "线" in item_name_lower or "缆" in item_name_lower:
            return "米"
        elif "胶带" in item_name_lower:
            return "卷"
        elif "充电器" in item_name_lower or "设备" in item_name_lower:
            return "台"
        elif "砝码" in item_name_lower:
            return "套"
        elif "推车" in item_name_lower:
            return "辆"

        return "个"

    def estimate_quantity(self, item_name: str) -> int:
        """
        根据物品名称和常见情况估算数量

        Args:
            item_name: 物品名称

        Returns:
            估算数量
        """
        item_name_lower = item_name.lower()

        # 螺丝类通常批量购买
        if "螺丝" in item_name_lower:
            # 根据规格估算数量
            if any(size in item_name for size in ["2.5", "3", "4", "5", "6"]):
                return 100  # 标准螺丝通常是100个装
            return 50

        # 轴承类
        if "轴承" in item_name_lower:
            return 10

        # 胶带类
        if "胶带" in item_name_lower:
            return 5

        # 连接器类
        if any(keyword in item_name_lower for keyword in ["连接器", "转接", "usb"]):
            return 5

        return 1

    def create_simple_procurement_excel(
        self, procurement_data: List[Dict[str, str]], output_path: str
    ) -> None:
        """
        创建采购申请Excel表格（按照模板格式）

        Args:
            procurement_data: 采购申请数据
            output_path: 输出文件路径
        """
        if not procurement_data:
            logger.warning("没有数据可以写入Excel")
            return

        # 转换数据格式以匹配模板
        template_data = []
        for item in procurement_data:
            template_item = {
                "物资二级分类": item.get("二级分类", ""),
                "物资名称": item.get("物品名称", ""),
                "规格型号": item.get("规格型号", ""),
                "单位": item.get("单位", ""),
                "数量": item.get("数量", 1),
                "估算单价-元": item.get("单价(元)", 0),
                "估算总价-元": item.get("金额(元)", 0),
            }
            template_data.append(template_item)

        # 创建DataFrame
        df = pd.DataFrame(template_data)

        # 使用openpyxl创建符合模板格式的Excel文件
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            # 写入数据，从第3行开始（前两行是标题和表头）
            df.to_excel(
                writer, sheet_name="明细表1", index=False, startrow=2, header=False
            )

            # 获取工作表进行格式化
            worksheet = writer.sheets["明细表1"]

            # 第1行：标题 "明细表1"（合并A1:G1）
            worksheet["A1"] = "明细表1"
            worksheet.merge_cells("A1:G1")

            # 第2行：表头
            headers = [
                "物资二级分类",
                "物资名称",
                "规格型号",
                "单位",
                "数量",
                "估算单价-元",
                "估算总价-元",
            ]
            for col, header in enumerate(headers, 1):
                worksheet.cell(row=2, column=col, value=header)

        logger.info(f"采购申请表已生成: {output_path}")

    def convert_expense_to_procurement(
        self, expense_excel_path: str, output_path: Optional[str] = None
    ) -> str:
        """
        将支出申请表转换为采购申请表

        Args:
            expense_excel_path: 支出申请表Excel文件路径
            output_path: 输出文件路径，如果为None则自动生成

        Returns:
            生成的采购申请表文件路径
        """
        # 读取支出申请表
        expense_data = self.read_expense_excel(expense_excel_path)

        if not expense_data:
            raise ValueError("支出申请表中没有有效数据")

        # 转换为采购申请表格式
        procurement_data = self.convert_to_procurement_format(expense_data)

        # 生成输出文件名
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            expense_file = Path(expense_excel_path)
            output_filename = f"{timestamp}_采购申请_{expense_file.stem}.xlsx"
            output_path = expense_file.parent / output_filename

        # 创建采购申请表
        self.create_simple_procurement_excel(procurement_data, str(output_path))

        # 打印摘要
        total_amount = sum(item["金额(元)"] for item in procurement_data)
        logger.info(f"转换完成！")
        logger.info(f"- 处理项目数量: {len(procurement_data)}")
        logger.info(f"- 总金额: {total_amount:.2f}元")
        logger.info(f"- 输出文件: {output_path}")

        return str(output_path)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="简化版支出申请表转采购申请表转换工具")
    parser.add_argument("expense_excel", help="支出申请表Excel文件路径")
    parser.add_argument("-o", "--output", help="输出文件路径，如果不指定则自动生成")

    args = parser.parse_args()

    # 检查输入文件
    if not os.path.exists(args.expense_excel):
        logger.error(f"输入文件不存在: {args.expense_excel}")
        return

    # 创建转换器
    converter = SimpleExpenseToProcurementConverter()

    try:
        # 执行转换
        output_path = converter.convert_expense_to_procurement(
            args.expense_excel, args.output
        )
        print(f"\n✅ 转换成功！")
        print(f"📄 输出文件: {output_path}")

    except Exception as e:
        logger.error(f"转换过程中出现错误: {e}")
        print(f"\n❌ 转换失败: {e}")


if __name__ == "__main__":
    # 如果直接运行，使用默认文件
    import sys

    if len(sys.argv) == 1:
        default_file = "/Users/lr-2002/Documents/报销材料/结构/20260123_报销.xlsx"
        if os.path.exists(default_file):
            print(f"使用默认文件: {default_file}")
            converter = SimpleExpenseToProcurementConverter()
            try:
                output_path = converter.convert_expense_to_procurement(default_file)
                print(f"\n✅ 转换成功！")
                print(f"📄 输出文件: {output_path}")
            except Exception as e:
                logger.error(f"转换失败: {e}")
                print(f"\n❌ 转换失败: {e}")
        else:
            print(f"默认文件不存在: {default_file}")
            print("请指定支出申请表文件路径")
    else:
        main()
