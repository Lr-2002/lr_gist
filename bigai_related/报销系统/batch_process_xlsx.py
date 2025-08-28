import pandas as pd
import os
import glob
from datetime import datetime

def find_xlsx_files(folder_path):
    """
    在指定文件夹中查找所有xlsx文件
    """
    xlsx_pattern = os.path.join(folder_path, "*.xlsx")
    xlsx_files = glob.glob(xlsx_pattern)
    
    # 也搜索子文件夹
    subdir_pattern = os.path.join(folder_path, "**", "*.xlsx")
    xlsx_files.extend(glob.glob(subdir_pattern, recursive=True))
    
    return list(set(xlsx_files))  # 去重

def process_single_excel(file_path):
    """
    处理单个Excel文件，提取交易成功的订单
    """
    try:
        print(f"\n正在处理: {os.path.basename(file_path)}")
        
        # 读取Excel文件
        df = pd.read_excel(file_path)
        
        # 查找状态列
        status_column = None
        for col in df.columns:
            if '状态' in col or 'status' in col.lower():
                status_column = col
                break
        
        if not status_column:
            print(f"  警告: 未找到订单状态列，跳过文件")
            return []
        
        # 筛选交易成功的订单
        successful_orders = df[df[status_column] == '交易成功']
        print(f"  找到 {len(successful_orders)} 个交易成功的订单")
        
        if len(successful_orders) == 0:
            return []
        
        # 定义字段映射
        field_mapping = {
            '店铺名称': ['店铺名称', '商家', '店铺', '卖家'],
            '商品名称': ['商品名称', '商品', '产品名称', '标题'],
            '型号规格': ['型号规格', '规格', '型号', '规格型号', '型号款式'],
            '商品数量': ['商品数量', '数量', '购买数量'],
            '金额': ['金额', '商品金额', '价格', '总价', '实付金额']
        }
        
        # 找到实际的列名
        actual_columns = {}
        for field, possible_names in field_mapping.items():
            for name in possible_names:
                if name in df.columns:
                    actual_columns[field] = name
                    break
        
        # 提取数据
        extracted_data = []
        for _, row in successful_orders.iterrows():
            order_data = {'文件来源': os.path.basename(file_path)}
            for field, column_name in actual_columns.items():
                order_data[field] = row[column_name] if column_name in row else None
            extracted_data.append(order_data)
        
        return extracted_data
        
    except Exception as e:
        print(f"  错误: 处理文件 {file_path} 时出错: {e}")
        return []

def get_batch_statistics(all_data):
    """
    获取批量处理的统计信息
    """
    if not all_data:
        return
    
    print(f"\n=== 批量处理统计 ===")
    print(f"总订单数: {len(all_data)}")
    
    # 按文件统计
    file_counts = {}
    for order in all_data:
        file_name = order.get('文件来源', '未知')
        file_counts[file_name] = file_counts.get(file_name, 0) + 1
    
    print(f"\n按文件统计:")
    for file_name, count in sorted(file_counts.items()):
        print(f"  {file_name}: {count}个订单")
    
    # 统计店铺
    shops = [order.get('店铺名称', '') for order in all_data if order.get('店铺名称')]
    shop_counts = {}
    for shop in shops:
        shop_counts[shop] = shop_counts.get(shop, 0) + 1
    
    print(f"\n店铺统计 (前10名):")
    for shop, count in sorted(shop_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {shop}: {count}个订单")
    
    # 统计金额
    amounts = []
    for order in all_data:
        amount_str = order.get('金额', '0')
        if amount_str and isinstance(amount_str, str):
            amount_clean = amount_str.replace('￥', '').replace(',', '')
            try:
                amounts.append(float(amount_clean))
            except ValueError:
                continue
    
    if amounts:
        total_amount = sum(amounts)
        avg_amount = total_amount / len(amounts)
        print(f"\n金额统计:")
        print(f"  总金额: ￥{total_amount:.2f}")
        print(f"  平均金额: ￥{avg_amount:.2f}")
        print(f"  最高金额: ￥{max(amounts):.2f}")
        print(f"  最低金额: ￥{min(amounts):.2f}")

def export_batch_results(all_data, output_folder):
    """
    导出批量处理结果
    """
    if not all_data:
        print("没有数据需要导出")
        return
    
    try:
        # 创建输出文件夹
        os.makedirs(output_folder, exist_ok=True)
        
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 导出合并的数据
        df_all = pd.DataFrame(all_data)
        output_file = os.path.join(output_folder, f"批量提取_交易成功订单_{timestamp}.xlsx")
        df_all.to_excel(output_file, index=False, engine='openpyxl')
        print(f"\n合并数据已导出到: {output_file}")
        
        # 按文件分别导出
        file_groups = {}
        for order in all_data:
            file_name = order.get('文件来源', '未知')
            if file_name not in file_groups:
                file_groups[file_name] = []
            file_groups[file_name].append(order)
        
        for file_name, orders in file_groups.items():
            df_file = pd.DataFrame(orders)
            file_output = os.path.join(output_folder, f"{file_name.replace('.xlsx', '')}_交易成功_{timestamp}.xlsx")
            df_file.to_excel(file_output, index=False, engine='openpyxl')
            print(f"  {file_name} 数据已导出到: {os.path.basename(file_output)}")
        
    except Exception as e:
        print(f"导出数据时出错: {e}")

def main():
    # 配置文件夹路径
    input_folder = "/Users/lr-2002/project/lr_gist/bigai_related/报销系统/data_sheet"
    output_folder = "/Users/lr-2002/project/lr_gist/bigai_related/报销系统/batch_output"
    
    print(f"开始批量处理文件夹: {input_folder}")
    
    # 查找所有xlsx文件
    xlsx_files = find_xlsx_files(input_folder)
    
    if not xlsx_files:
        print("未找到任何xlsx文件")
        return
    
    print(f"找到 {len(xlsx_files)} 个xlsx文件:")
    for file_path in xlsx_files:
        print(f"  - {os.path.basename(file_path)}")
    
    # 批量处理所有文件
    all_successful_orders = []
    
    for file_path in xlsx_files:
        orders = process_single_excel(file_path)
        all_successful_orders.extend(orders)
    
    # 显示统计信息
    get_batch_statistics(all_successful_orders)
    
    # 导出结果
    if all_successful_orders:
        export_batch_results(all_successful_orders, output_folder)
    else:
        print("\n没有找到任何交易成功的订单")
    
    return all_successful_orders

if __name__ == "__main__":
    main()
