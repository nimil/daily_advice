#!/usr/bin/env python3
"""
测试新的zai-sdk
根据智谱AI官方文档：https://docs.bigmodel.cn/cn/guide/develop/python/introduction
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_zai_sdk():
    """测试zai-sdk的基本功能"""
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
        
        # 测试流式对话
        print("\n🔍 测试流式对话...")
        stream_response = client.chat.completions.create(
            model="glm-4.5",
            messages=[
                {"role": "user", "content": "请用一句话介绍Python"}
            ],
            stream=True
        )
        
        print("✅ 流式对话测试成功")
        print("流式响应内容: ", end="")
        for chunk in stream_response:
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="")
        print()
        
        # 测试多轮对话
        print("\n🔍 测试多轮对话...")
        multi_response = client.chat.completions.create(
            model="glm-4.5",
            messages=[
                {"role": "user", "content": "什么是人工智能？"},
                {"role": "assistant", "content": "人工智能是计算机科学的一个分支，旨在创建能够执行通常需要人类智能的任务的系统。"},
                {"role": "user", "content": "请详细解释一下"}
            ]
        )
        
        print("✅ 多轮对话测试成功")
        print(f"多轮响应: {multi_response.choices[0].message.content}")
        
        print("\n🎉 所有测试通过！zai-sdk 工作正常")
        return True
        
    except ImportError as e:
        print(f"❌ zai-sdk 导入失败: {e}")
        print("请运行: pip install zai-sdk")
        return False
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
        
        # 测试query方法
        print("\n🔍 测试query方法...")
        messages = [
            {"role": "user", "content": "什么是机器学习？"}
        ]
        result = glm4.query(messages)
        
        if result['error_code'] == 0:
            print("✅ query方法测试成功")
            print(f"响应: {result['data'].choices[0].message.content[:100]}...")
        else:
            print(f"❌ query方法测试失败: {result['message']}")
            return False
        
        print("\n🎉 GLM4Query类测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ GLM4Query类测试失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("zai-sdk 测试工具")
    print("=" * 50)
    
    # 测试zai-sdk
    sdk_test = test_zai_sdk()
    
    # 测试GLM4Query类
    class_test = test_glm4_query_class()
    
    print("\n" + "=" * 50)
    if sdk_test and class_test:
        print("🎉 所有测试通过！可以正常使用新的zai-sdk")
        sys.exit(0)
    else:
        print("❌ 部分测试失败，请检查配置")
        sys.exit(1)

if __name__ == "__main__":
    main()
