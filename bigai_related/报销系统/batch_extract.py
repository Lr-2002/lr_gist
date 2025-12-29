"""
简单的批量图片文字提取脚本
直接处理指定文件夹中的所有图片
"""

from image_text_extractor import batch_extract_text_from_folder
import sys
import os

def main():
    """主函数 - 批量处理文件夹"""
    
    # 如果命令行提供了文件夹路径
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
    else:
        # 否则询问用户
        folder_path = input("请输入要处理的文件夹路径: ").strip()
    
    # 去除引号（如果有的话）
    folder_path = folder_path.strip('"').strip("'")
    
    # 检查文件夹是否存在
    if not os.path.exists(folder_path):
        print(f"错误: 文件夹不存在 - {folder_path}")
        return
    
    if not os.path.isdir(folder_path):
        print(f"错误: 路径不是文件夹 - {folder_path}")
        return
    
    print(f"开始处理文件夹: {folder_path}")
    print("=" * 50)
    
    # 批量处理
    result = batch_extract_text_from_folder(folder_path)
    
    print("=" * 50)
    print("处理完成!")
    print(f"✅ 成功: {result['success']} 个文件")
    print(f"❌ 失败: {result['failed']} 个文件")
    print(f"📁 总计: {result['total']} 个文件")
    
    if result['total'] > 0:
        print(f"\n所有提取的文字已保存为对应的 *_extracted_text.txt 文件")

if __name__ == "__main__":
    main()
