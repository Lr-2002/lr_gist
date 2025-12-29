"""
图片文字提取工具使用示例
"""

from image_text_extractor import extract_text_from_image, batch_extract_text_from_folder

def example_single_image():
    """单个图片处理示例"""
    print("=== 单个图片处理示例 ===")
    
    # 处理单个图片
    image_path = "your_image.png"  # 替换为你的图片路径
    
    # 方法1: 自动生成txt文件名
    text = extract_text_from_image(image_path)
    
    # 方法2: 指定txt文件名
    # text = extract_text_from_image(image_path, "custom_output.txt")
    
    if text:
        print(f"提取成功! 文字内容预览:")
        print(text[:200] + "..." if len(text) > 200 else text)
    else:
        print("提取失败或图片不存在")

def example_batch_processing():
    """批量处理示例"""
    print("\n=== 批量处理示例 ===")
    
    # 处理指定文件夹中的所有图片
    folder_path = "/path/to/your/images"  # 替换为你的图片文件夹路径
    
    # 使用默认支持的格式
    result = batch_extract_text_from_folder(folder_path)
    
    # 或者指定特定格式
    # custom_formats = ['*.png', '*.jpg', '*.jpeg']
    # result = batch_extract_text_from_folder(folder_path, custom_formats)
    
    print(f"批量处理完成:")
    print(f"- 成功处理: {result['success']} 个文件")
    print(f"- 处理失败: {result['failed']} 个文件")
    print(f"- 总计文件: {result['total']} 个文件")

def interactive_mode():
    """交互模式"""
    print("\n=== 交互模式 ===")
    
    while True:
        print("\n请选择操作:")
        print("1. 处理单个图片")
        print("2. 批量处理文件夹")
        print("3. 退出")
        
        choice = input("请输入选择 (1-3): ").strip()
        
        if choice == '1':
            image_path = input("请输入图片路径: ").strip()
            if image_path:
                extract_text_from_image(image_path)
            else:
                print("未输入图片路径")
                
        elif choice == '2':
            folder_path = input("请输入文件夹路径: ").strip()
            if folder_path:
                batch_extract_text_from_folder(folder_path)
            else:
                print("未输入文件夹路径")
                
        elif choice == '3':
            print("退出程序")
            break
            
        else:
            print("无效选择，请重新输入")

if __name__ == "__main__":
    print("图片文字提取工具使用示例")
    print("=" * 50)
    
    # 运行示例
    example_single_image()
    example_batch_processing()
    
    # 启动交互模式
    interactive_mode()
