#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试SiliconFlow API连接
"""

import os
from openai import OpenAI

def test_siliconflow_api():
    """测试SiliconFlow API是否配置正确"""
    
    # 检查API密钥
    api_key = os.getenv("SILICONFLOW_API_KEY")
    if not api_key:
        print("❌ 未找到SILICONFLOW_API_KEY环境变量")
        print("\n请设置API密钥：")
        print("  export SILICONFLOW_API_KEY='your-api-key'")
        print("\n获取API密钥：https://cloud.siliconflow.cn/account/ak")
        return False
    
    print("✅ 找到API密钥")
    print(f"   密钥前缀: {api_key[:10]}...")
    
    # 测试API连接
    try:
        print("\n🔄 测试API连接...")
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.siliconflow.cn/v1"
        )
        
        # 发送测试请求
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-7B-Instruct",
            messages=[
                {"role": "user", "content": "你好，请用一句话介绍你自己。"}
            ],
            max_tokens=100
        )
        
        result = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        
        print("✅ API连接成功！")
        print(f"\n📝 测试响应: {result}")
        print(f"🔢 使用Token: {tokens_used}")
        
        return True
        
    except Exception as e:
        print(f"❌ API连接失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("SiliconFlow API 连接测试")
    print("=" * 60)
    
    if test_siliconflow_api():
        print("\n" + "=" * 60)
        print("✅ 配置正确，可以开始使用PDF分析工具！")
        print("=" * 60)
        print("\n运行示例：")
        print("  python example_usage.py")
        print("  python pdf_reader.py /path/to/pdfs -m")
    else:
        print("\n" + "=" * 60)
        print("❌ 配置有误，请检查API密钥设置")
        print("=" * 60)
