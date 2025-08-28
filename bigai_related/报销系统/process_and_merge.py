"""
改进版图片文字提取脚本
1. 优先中文OCR识别
2. 将所有提取的文字合并到一个txt文件中
"""

from image_text_extractor import batch_extract_and_merge

# 🔥 在这里修改为你的文件夹路径 🔥
FOLDER_PATH = "/Users/lr-2002/Documents/报销材料/7.18/图片"  # 修改这里！

def main():
    """处理指定文件夹并合并所有文字到一个文件"""
    
    print(f"正在处理文件夹: {FOLDER_PATH}")
    print("改进功能:")
    print("✅ 优先中文OCR识别")
    print("✅ 合并所有文字到一个txt文件")
    print("=" * 60)
    
    # 批量处理并合并所有图片的文字
    result = batch_extract_and_merge(FOLDER_PATH)
    
    print("=" * 60)
    print("🎉 处理完成!")
    print(f"✅ 成功处理: {result['success']} 个图片文件")
    print(f"❌ 处理失败: {result['failed']} 个图片文件") 
    print(f"📁 扫描总计: {result['total']} 个图片文件")
    
    if result['success'] > 0:
        print(f"\n📝 所有提取的文字已合并保存到:")
        print(f"📂 {result.get('merged_file', '合并文件')}")
        print(f"\n💡 文件内容包含:")
        print(f"   - 每个图片的文字内容")
        print(f"   - 清晰的文件分隔标识")
        print(f"   - 处理统计信息")
    elif result['total'] == 0:
        print(f"\n⚠️  在该文件夹中没有找到图片文件")
        print(f"支持的格式: jpg, jpeg, png, bmp, tiff, gif")
    else:
        print(f"\n❌ 所有文件处理失败，可能的原因:")
        print(f"   - 图片格式不支持")
        print(f"   - OCR无法识别图片中的文字")
        print(f"   - 图片质量过低")

if __name__ == "__main__":
    main()
