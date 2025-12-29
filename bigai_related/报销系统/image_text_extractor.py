"""
图片文字提取工具
从图片中提取所有文字并保存为txt文件
支持批量处理文件夹中的所有图片
"""

import os
import glob
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError as e:
    print(f"OCR依赖导入失败: {e}")
    print("请安装: pip install pytesseract pillow")
    OCR_AVAILABLE = False

def extract_text_from_image(image_path, output_txt_path=None):
    """
    从单个图片中提取所有文字并保存为txt文件
    
    Args:
        image_path (str): 图片文件路径
        output_txt_path (str): 输出txt文件路径，如果为None则自动生成
    
    Returns:
        str: 提取的文字内容
    """
    # 检查OCR是否可用
    if not OCR_AVAILABLE:
        print("OCR功能不可用，请先安装依赖")
        return None
        
    try:
        # 打开图片
        image = Image.open(image_path)
        
        # 使用OCR提取文本（优先中文识别）
        text = pytesseract.image_to_string(image, lang='chi_sim')
        
        # 如果没有指定输出路径，自动生成
        if output_txt_path is None:
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            output_dir = os.path.dirname(image_path)
            output_txt_path = os.path.join(output_dir, f"{base_name}_extracted_text.txt")
        
        # 保存文字到txt文件
        with open(output_txt_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        print(f"已提取图片文字: {image_path} -> {output_txt_path}")
        return text
        
    except Exception as e:
        print(f"处理图片 {image_path} 时出错: {e}")
        return None

def batch_extract_text_from_folder(folder_path, supported_formats=None):
    """
    批量处理文件夹中的所有图片，提取文字并保存为txt文件
    
    Args:
        folder_path (str): 包含图片的文件夹路径
        supported_formats (list): 支持的图片格式列表，默认为常见格式
    
    Returns:
        dict: 处理结果统计
    """
    if supported_formats is None:
        supported_formats = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.gif']
    
    # 检查文件夹是否存在
    if not os.path.exists(folder_path):
        print(f"文件夹不存在: {folder_path}")
        return {"success": 0, "failed": 0, "total": 0}
    
    # 获取所有支持格式的图片文件
    image_files = []
    for format_pattern in supported_formats:
        pattern = os.path.join(folder_path, format_pattern)
        image_files.extend(glob.glob(pattern, recursive=False))
        # 同时搜索大写扩展名
        pattern_upper = os.path.join(folder_path, format_pattern.upper())
        image_files.extend(glob.glob(pattern_upper, recursive=False))
    
    # 去重并排序
    image_files = sorted(list(set(image_files)))
    
    if not image_files:
        print(f"在文件夹 {folder_path} 中没有找到支持的图片文件")
        print(f"支持的格式: {supported_formats}")
        return {"success": 0, "failed": 0, "total": 0}
    
    print(f"找到 {len(image_files)} 个图片文件，开始批量处理...")
    
    success_count = 0
    failed_count = 0
    
    # 逐个处理图片
    for i, image_path in enumerate(image_files, 1):
        print(f"\n处理进度: {i}/{len(image_files)}")
        
        text = extract_text_from_image(image_path)
        if text is not None:
            success_count += 1
        else:
            failed_count += 1
    
    # 输出处理结果
    print(f"\n批量处理完成!")
    print(f"成功处理: {success_count} 个文件")
    print(f"处理失败: {failed_count} 个文件")
    print(f"总计文件: {len(image_files)} 个")
    
    return {
        "success": success_count,
        "failed": failed_count,
        "total": len(image_files),
        "processed_files": image_files
    }

def batch_extract_and_merge(folder_path, merged_output_path=None, supported_formats=None):
    """
    批量处理文件夹中的所有图片，提取文字并合并到一个txt文件中
    
    Args:
        folder_path (str): 包含图片的文件夹路径
        merged_output_path (str): 合并后的txt文件路径，默认为"merged_extracted_text.txt"
        supported_formats (list): 支持的图片格式列表
    
    Returns:
        dict: 处理结果统计
    """
    if supported_formats is None:
        supported_formats = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.gif']
    
    # 检查OCR是否可用
    if not OCR_AVAILABLE:
        print("OCR功能不可用，请先安装依赖")
        return {"success": 0, "failed": 0, "total": 0}
    
    # 检查文件夹是否存在
    if not os.path.exists(folder_path):
        print(f"文件夹不存在: {folder_path}")
        return {"success": 0, "failed": 0, "total": 0}
    
    # 获取所有支持格式的图片文件
    image_files = []
    for format_pattern in supported_formats:
        pattern = os.path.join(folder_path, format_pattern)
        image_files.extend(glob.glob(pattern, recursive=False))
        # 同时搜索大写扩展名
        pattern_upper = os.path.join(folder_path, format_pattern.upper())
        image_files.extend(glob.glob(pattern_upper, recursive=False))
    
    # 去重并排序
    image_files = sorted(list(set(image_files)))
    
    if not image_files:
        print(f"在文件夹 {folder_path} 中没有找到支持的图片文件")
        return {"success": 0, "failed": 0, "total": 0}
    
    # 设置合并输出文件路径
    if merged_output_path is None:
        merged_output_path = os.path.join(folder_path, "merged_extracted_text.txt")
    
    print(f"找到 {len(image_files)} 个图片文件，开始批量处理并合并...")
    
    success_count = 0
    failed_count = 0
    all_extracted_text = []
    
    # 逐个处理图片
    for i, image_path in enumerate(image_files, 1):
        print(f"\n处理进度: {i}/{len(image_files)}")
        
        try:
            # 打开图片
            image = Image.open(image_path)
            
            # 使用OCR提取文本（优先中文识别）
            text = pytesseract.image_to_string(image, lang='chi_sim')
            
            if text.strip():  # 如果提取到文字
                # 添加文件信息和分隔符
                filename = os.path.basename(image_path)
                separator = "=" * 50
                file_header = f"\n{separator}\n文件: {filename}\n{separator}\n"
                all_extracted_text.append(file_header + text.strip())
                
                print(f"✅ 成功提取: {filename}")
                success_count += 1
            else:
                print(f"⚠️  未提取到文字: {os.path.basename(image_path)}")
                failed_count += 1
                
        except Exception as e:
            print(f"❌ 处理失败: {os.path.basename(image_path)} - {e}")
            failed_count += 1
    
    # 将所有提取的文字写入合并文件
    try:
        with open(merged_output_path, 'w', encoding='utf-8') as f:
            f.write(f"图片文字提取结果合并文件\n")
            f.write(f"处理时间: {os.path.basename(folder_path)}\n")
            f.write(f"总计图片: {len(image_files)} 个\n")
            f.write(f"成功提取: {success_count} 个\n")
            f.write(f"处理失败: {failed_count} 个\n")
            f.write("\n" + "=" * 80 + "\n")
            
            if all_extracted_text:
                f.write("\n".join(all_extracted_text))
            else:
                f.write("\n未提取到任何文字内容")
        
        print(f"\n📝 所有提取的文字已合并保存到: {merged_output_path}")
        
    except Exception as e:
        print(f"❌ 保存合并文件失败: {e}")
    
    # 输出处理结果
    print(f"\n批量处理完成!")
    print(f"成功处理: {success_count} 个文件")
    print(f"处理失败: {failed_count} 个文件")
    print(f"总计文件: {len(image_files)} 个")
    
    return {
        "success": success_count,
        "failed": failed_count,
        "total": len(image_files),
        "processed_files": image_files,
        "merged_file": merged_output_path
    }

def main():
    """主函数 - 示例用法"""
    # 示例1: 处理单个图片
    # image_path = "example.png"
    # extract_text_from_image(image_path)
    
    # 示例2: 批量处理文件夹中的所有图片
    folder_path = input("请输入包含图片的文件夹路径: ").strip()
    if folder_path:
        batch_extract_text_from_folder(folder_path)
    else:
        print("未输入文件夹路径，程序退出")

if __name__ == "__main__":
    main()
