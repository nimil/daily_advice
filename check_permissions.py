#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查飞书应用权限
"""

import requests
import json
from config import config

def get_access_token():
    """获取访问令牌"""
    try:
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json"}
        data = {
            "app_id": config.FEISHU_APP_ID,
            "app_secret": config.FEISHU_APP_SECRET
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                return result.get('tenant_access_token')
            else:
                print(f"❌ 获取访问令牌失败: {result.get('msg')}")
                return None
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        return None

def check_app_info(access_token):
    """检查应用信息"""
    print("\n🔍 检查应用信息...")
    
    try:
        url = "https://open.feishu.cn/open-apis/application/v6/applications/me"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                app_info = result.get('data', {})
                print(f"✅ 应用名称: {app_info.get('name', '未知')}")
                print(f"✅ 应用描述: {app_info.get('description', '未知')}")
                print(f"✅ 应用状态: {app_info.get('status', '未知')}")
                return app_info
            else:
                print(f"❌ 获取应用信息失败: {result.get('msg')}")
                return None
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        return None

def check_permissions(access_token):
    """检查应用权限"""
    print("\n🔍 检查应用权限...")
    
    try:
        url = "https://open.feishu.cn/open-apis/application/v6/applications/me/permissions"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                permissions = result.get('data', {})
                print("✅ 应用权限列表:")
                for perm in permissions.get('permissions', []):
                    print(f"   - {perm.get('name', '未知')}: {perm.get('status', '未知')}")
                return permissions
            else:
                print(f"❌ 获取权限失败: {result.get('msg')}")
                return None
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        return None

def test_interactive_message(access_token, chat_id):
    """测试交互式消息（可能不需要富文本权限）"""
    print("\n🔍 测试交互式消息...")
    
    try:
        url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # 测试交互式消息
        data = {
            "receive_id": chat_id,
            "msg_type": "interactive",
            "content": json.dumps({
                "config": {
                    "wide_screen_mode": True
                },
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": "测试卡片"
                    }
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "plain_text",
                            "content": "这是一个测试卡片消息"
                        }
                    }
                ]
            }, ensure_ascii=False, separators=(',', ':'))
        }
        
        print(f"📤 请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
        print(f"📊 状态码: {response.status_code}")
        print(f"📄 响应: {response.text}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("检查飞书应用权限")
    print("=" * 60)
    
    # 获取访问令牌
    print("🔍 获取访问令牌...")
    access_token = get_access_token()
    if not access_token:
        return
    
    print("✅ 成功获取访问令牌")
    
    # 检查应用信息
    app_info = check_app_info(access_token)
    
    # 检查权限
    permissions = check_permissions(access_token)
    
    # 测试交互式消息
    import os
    chat_id = os.getenv('FEISHU_CHAT_ID', '')
    if chat_id:
        test_interactive_message(access_token, chat_id)
    
    print("\n💡 建议:")
    print("1. 检查飞书开发者后台的应用权限配置")
    print("2. 确保应用具有 'im:message:send_as_bot' 权限")
    print("3. 确保应用具有发送富文本消息的权限")
    print("4. 检查应用是否已添加到目标群组")

if __name__ == "__main__":
    main()
