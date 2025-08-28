"""
图片文字提取功能测试脚本
"""

from image_text_extractor import extract_text_from_image, batch_extract_text_from_folder
import os

def test_single_image():
    """测试单个图片文字提取"""
    print("=== 测试单个图片文字提取 ===")
    
    # 这里可以替换为实际的图片路径
    image_path = "test_image.png"
    
    if os.path.exists(image_path):
        text = extract_text_from_image(image_path)
        if text:
            print(f"提取的文字内容:\n{text}")
        else:
            print("文字提取失败")
    else:
        print(f"测试图片不存在: {image_path}")
        print("请将测试图片放在当前目录下，或修改image_path变量")

def test_batch_processing():
    """测试批量处理文件夹"""
    print("\n=== 测试批量处理文件夹 ===")
    
    # 使用当前目录作为测试
    current_dir = os.getcwd()
    print(f"当前目录: {current_dir}")
    
    # 批量处理当前目录中的所有图片
    result = batch_extract_text_from_folder(current_dir)
    
    print(f"\n处理结果:")
    print(f"- 成功: {result['success']} 个")
    print(f"- 失败: {result['failed']} 个") 
    print(f"- 总计: {result['total']} 个")

def main():
    """主测试函数"""
    print("图片文字提取功能测试")
    print("=" * 50)
    
    # 测试单个图片
    test_single_image()
    
    # 测试批量处理
    test_batch_processing()
    
    print("\n测试完成!")

if __name__ == "__main__":
    main()
