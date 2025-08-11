#!/usr/bin/env python3
"""
简化的GLM4测试脚本
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_glm4_simple():
    """简单的GLM4测试"""
    try:
        from zai import ZhipuAiClient
        print("✅ zai-sdk 导入成功")
        
        # 获取API密钥
        api_key = os.getenv('GLM4_API_KEY')
        if not api_key:
            print("❌ GLM4_API_KEY 环境变量未设置")
            return False
            
        print(f"✅ API密钥已设置: {api_key[:10]}...")
        
        # 创建客户端
        client = ZhipuAiClient(api_key=api_key)
        print("✅ ZhipuAiClient 创建成功")
        
        # 测试基础对话
        print("\n🔍 测试基础对话...")
        response = client.chat.completions.create(
            model="glm-4.5",
            messages=[
                {"role": "user", "content": "你好，请简单介绍一下自己"}
            ]
        )
        
        print("✅ 基础对话测试成功")
        print(f"响应内容: {response.choices[0].message.content}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_glm4_query_class():
    """测试更新后的GLM4Query类"""
    try:
        from glm4_query import GLM4Query
        from config import config
        
        print("\n🔍 测试GLM4Query类...")
        
        # 创建GLM4Query实例
        glm4 = GLM4Query(config.GLM4_API_KEY)
        print("✅ GLM4Query 实例创建成功")
        
        # 测试简单对话
        print("\n🔍 测试简单对话...")
        response = glm4.chat("你好，请简单介绍一下自己")
        print(f"✅ 简单对话测试成功: {response[:100]}...")
        
        print("\n🎉 GLM4Query类测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ GLM4Query类测试失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("GLM4 简化测试工具")
    print("=" * 50)
    
    # 测试zai-sdk
    sdk_test = test_glm4_simple()
    
    # 测试GLM4Query类
    class_test = test_glm4_query_class()
    
    print("\n" + "=" * 50)
    if sdk_test and class_test:
        print("🎉 所有测试通过！新的zai-sdk迁移成功")
        print("\n📋 更新总结:")
        print("✅ 从 zhipuai 迁移到 zai-sdk")
        print("✅ 使用 ZhipuAiClient 替代 ZhipuAI")
        print("✅ 支持最新的 GLM-4.5 模型")
        print("✅ 配置管理已更新")
    else:
        print("❌ 部分测试失败，请检查配置")

if __name__ == "__main__":
    main()
