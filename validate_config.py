#!/usr/bin/env python3
"""
配置验证脚本
用于验证所有必需的配置项是否已正确设置
"""

import os
import sys
from config import config

def validate_config():
    """验证配置项"""
    print("🔍 开始验证配置...")
    
    # 检查缺失的配置项
    missing_keys = config.validate_required_keys()
    
    if missing_keys:
        print("❌ 发现缺失的配置项:")
        for key in missing_keys:
            print(f"   - {key}")
        print("\n请检查以下文件:")
        print("1. .env 文件（如果存在）")
        print("2. 环境变量")
        print("3. 参考 env.example 文件设置正确的值")
        return False
    
    print("✅ 所有必需的配置项都已设置")
    
    # 显示配置摘要（隐藏敏感信息）
    print("\n📋 配置摘要:")
    print(f"   - Flask环境: {config.FLASK_ENV}")
    print(f"   - 服务器地址: {config.HOST}:{config.PORT}")
    print(f"   - 企业微信配置: {'已设置' if config.CORP_ID else '未设置'}")
    print(f"   - API密钥配置: {'已设置' if config.SOLAR_TERMS_API_KEY else '未设置'}")
    
    return True

def check_env_file():
    """检查环境变量文件"""
    env_file = '.env'
    if os.path.exists(env_file):
        print(f"✅ 找到 {env_file} 文件")
        return True
    else:
        print(f"⚠️  未找到 {env_file} 文件")
        print("建议创建 .env 文件并设置环境变量")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("配置验证工具")
    print("=" * 50)
    
    # 检查环境变量文件
    env_exists = check_env_file()
    
    # 验证配置
    config_valid = validate_config()
    
    print("\n" + "=" * 50)
    if config_valid:
        print("🎉 配置验证通过！")
        sys.exit(0)
    else:
        print("❌ 配置验证失败！")
        print("\n请按照以下步骤操作:")
        print("1. 复制 env.example 为 .env")
        print("2. 在 .env 文件中填入正确的配置值")
        print("3. 重新运行此脚本验证")
        sys.exit(1)

if __name__ == "__main__":
    main()
