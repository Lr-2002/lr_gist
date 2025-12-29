"""
最简单的文件夹批量处理脚本
只需要修改 FOLDER_PATH 变量为你的文件夹路径即可
"""

from image_text_extractor import batch_extract_text_from_folder

# 🔥 在这里修改为你的文件夹路径 🔥
FOLDER_PATH = "/Users/lr-2002/Documents/报销材料/7.18/图片"  # 修改这里！

def main():
    """直接处理指定文件夹"""
    
    print(f"正在处理文件夹: {FOLDER_PATH}")
    print("=" * 60)
    
    # 批量处理所有图片
    result = batch_extract_text_from_folder(FOLDER_PATH)
    
    print("=" * 60)
    print("🎉 处理完成!")
    print(f"✅ 成功处理: {result['success']} 个图片文件")
    print(f"❌ 处理失败: {result['failed']} 个图片文件") 
    print(f"📁 扫描总计: {result['total']} 个图片文件")
    
    if result['success'] > 0:
        print(f"\n📝 所有提取的文字已保存为 *_extracted_text.txt 文件")
        print(f"📂 保存位置: {FOLDER_PATH}")
    elif result['total'] == 0:
        print(f"\n⚠️  在该文件夹中没有找到图片文件")
        print(f"支持的格式: jpg, jpeg, png, bmp, tiff, gif")
    else:
        print(f"\n❌ 所有文件处理失败，请检查图片格式或OCR配置")

if __name__ == "__main__":
    main()
