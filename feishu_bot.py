#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书机器人服务模块
"""

import requests
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import time
import pytz
from config import config

class FeishuBot:
    """飞书机器人服务类"""
    
    def __init__(self):
        """初始化飞书机器人"""
        self.app_id = config.FEISHU_APP_ID
        self.app_secret = config.FEISHU_APP_SECRET
        self.access_token = None
        self.token_expires_at = None
        self.base_url = "https://open.feishu.cn/open-apis"
        
        # 消息来源映射
        self.source_mapping = {
            'jin10': '金十数据',
            'cls_telegraph': '财联社',
            'wallstreetcn_hot': '华尔街见闻',
            'cls-telegraph': '财联社',
            'wallstreetcn-hot': '华尔街见闻'
        }
        
    def get_mapped_source(self, source: str) -> str:
        """
        获取映射后的消息来源名称
        
        Args:
            source: 原始来源名称
            
        Returns:
            str: 映射后的来源名称
        """
        return self.source_mapping.get(source, source)
    
    def get_mapped_sources(self, sources: str) -> str:
        """
        获取映射后的多个消息来源名称
        
        Args:
            sources: 原始来源名称，可能包含多个来源（用逗号分隔）
            
        Returns:
            str: 映射后的来源名称
        """
        if not sources:
            return sources
        
        # 分割多个来源
        source_list = [s.strip() for s in sources.split(',')]
        
        # 映射每个来源
        mapped_sources = []
        for source in source_list:
            mapped_source = self.source_mapping.get(source, source)
            mapped_sources.append(mapped_source)
        
        # 返回映射后的来源，用逗号分隔
        return ', '.join(mapped_sources)
    
    def get_access_token(self) -> Optional[str]:
        """
        获取访问令牌
        
        Returns:
            str: 访问令牌
        """
        try:
            # 检查令牌是否还有效
            if self.access_token and self.token_expires_at and datetime.now(pytz.timezone('Asia/Shanghai')) < self.token_expires_at:
                return self.access_token
            
            # 获取新的访问令牌
            url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
            headers = {
                "Content-Type": "application/json"
            }
            data = {
                "app_id": self.app_id,
                "app_secret": self.app_secret
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('code') == 0:
                self.access_token = result.get('tenant_access_token')
                # 设置过期时间（提前5分钟过期）
                expires_in = result.get('expire', 7200) - 300
                self.token_expires_at = datetime.now(pytz.timezone('Asia/Shanghai')) + timedelta(seconds=expires_in)
                
                logging.info("成功获取飞书访问令牌")
                return self.access_token
            else:
                logging.error(f"获取飞书访问令牌失败: {result.get('msg')}")
                return None
                
        except Exception as e:
            logging.error(f"获取飞书访问令牌异常: {str(e)}")
            return None
    
    def send_message(self, chat_id: str, content: Dict[str, Any]) -> bool:
        """
        发送消息到指定群组
        
        Args:
            chat_id: 群组ID
            content: 消息内容
            
        Returns:
            bool: 是否发送成功
        """
        try:
            access_token = self.get_access_token()
            if not access_token:
                logging.error("获取访问令牌失败")
                return False
            
            url = f"{self.base_url}/im/v1/messages?receive_id_type=chat_id"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "receive_id": chat_id,
                "msg_type": "post",
                "content": json.dumps(content, ensure_ascii=False, separators=(',', ':'))
            }
            
            # 打印详细请求信息
            print(f"\n🔍 发送飞书消息详情:")
            print(f"📤 URL: {url}")
            print(f"📋 Headers: {json.dumps(headers, ensure_ascii=False)}")
            print(f"📄 Data: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            response = requests.post(url, headers=headers, json=data, timeout=10)
            
            # 打印响应信息
            print(f"📊 响应状态码: {response.status_code}")
            print(f"📄 响应内容: {response.text}")
            
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('code') == 0:
                logging.info(f"成功发送消息到群组 {chat_id}")
                print(f"✅ 消息发送成功")
                return True
            else:
                logging.error(f"发送消息失败: {result.get('msg')}")
                print(f"❌ 发送失败: {result.get('msg')}")
                return False
                
        except Exception as e:
            logging.error(f"发送消息异常: {str(e)}")
            print(f"❌ 发送异常: {str(e)}")
            return False
    
    def send_text_message(self, chat_id: str, text: str) -> bool:
        """
        发送文本消息
        
        Args:
            chat_id: 群组ID
            text: 文本内容
            
        Returns:
            bool: 是否发送成功
        """
        try:
            access_token = self.get_access_token()
            if not access_token:
                logging.error("获取访问令牌失败")
                return False
            
            url = f"{self.base_url}/im/v1/messages?receive_id_type=chat_id"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "receive_id": chat_id,
                "msg_type": "text",
                "content": json.dumps({"text": text}, ensure_ascii=False, separators=(',', ':'))
            }
            
            # 打印详细请求信息
            print(f"\n🔍 发送飞书文本消息详情:")
            print(f"📤 URL: {url}")
            print(f"📋 Headers: {json.dumps(headers, ensure_ascii=False)}")
            print(f"📄 Data: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            response = requests.post(url, headers=headers, json=data, timeout=10)
            
            # 打印响应信息
            print(f"📊 响应状态码: {response.status_code}")
            print(f"📄 响应内容: {response.text}")
            
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('code') == 0:
                logging.info(f"成功发送文本消息到群组 {chat_id}")
                print(f"✅ 文本消息发送成功")
                return True
            else:
                logging.error(f"发送文本消息失败: {result.get('msg')}")
                print(f"❌ 文本消息发送失败: {result.get('msg')}")
                return False
                
        except Exception as e:
            logging.error(f"发送文本消息异常: {str(e)}")
            print(f"❌ 文本消息发送异常: {str(e)}")
            return False
    
    def create_news_post_message(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建新闻富文本消息
        
        Args:
            news_data: 新闻数据
            
        Returns:
            Dict: 飞书富文本消息格式
        """
        try:
            current_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y年%m月%d日 %H:%M:%S')
            
            # 提取新闻数据 - 参照HTML格式的取值方式
            news_list = news_data.get('data', {}).get('news_list', [])
            summary = news_data.get('data', {}).get('summary', '今日新闻概览')
            total_count = news_data.get('data', {}).get('total_count', len(news_list))
            
            # 构建飞书富文本消息
            content = {
                "post": {
                    "zh_cn": {
                        "title": f"📰 每日新闻汇总 - {current_time}",
                        "content": []
                    }
                }
            }
            
            # 添加概览 - 参照HTML格式的样式
            content["post"]["zh_cn"]["content"].append([
                {
                    "tag": "text",
                    "text": f"📋 今日概览：{summary}"
                }
            ])
            
            # 添加统计信息
            positive_count = news_data.get('data', {}).get('positive_count', 0)
            negative_count = news_data.get('data', {}).get('negative_count', 0)
            
            content["post"]["zh_cn"]["content"].append([
                {
                    "tag": "text",
                    "text": f"📊 新闻统计：共 {total_count} 条精选新闻"
                }
            ])
            
            # 添加影响统计
            content["post"]["zh_cn"]["content"].append([
                {
                    "tag": "text",
                    "text": f"📈 正向影响：{positive_count} 条 | 📉 负向影响：{negative_count} 条"
                }
            ])
            
            # 添加分隔线
            content["post"]["zh_cn"]["content"].append([
                {
                    "tag": "text",
                    "text": "──────────────────────────────"
                }
            ])
            
            # 添加新闻列表（最多10条）
            for i, news in enumerate(news_list[:10], 1):
                title = news.get('title', '')
                news_summary = news.get('summary', '')
                source = news.get('source', '')
                pub_date = news.get('pubDate', '')
                url = news.get('url', '')
                
                # 使用映射后的消息来源（支持多个来源）
                mapped_source = self.get_mapped_sources(source)
                
                # 新闻标题（可点击）
                content["post"]["zh_cn"]["content"].append([
                    {
                        "tag": "text",
                        "text": f"{i}. "
                    },
                    {
                        "tag": "a",
                        "text": title,
                        "href": url
                    }
                ])
                
                # 新闻摘要
                if news_summary:
                    content["post"]["zh_cn"]["content"].append([
                        {
                            "tag": "text",
                            "text": f"   {news_summary}"
                        }
                    ])
                
                # 新闻元信息 - 使用映射后的来源
                # 处理pub_date，可能是字符串或整数
                if pub_date:
                    if isinstance(pub_date, str):
                        time_display = pub_date.strip() if pub_date.strip() else "未知时间"
                    elif isinstance(pub_date, int):
                        # 如果是时间戳，转换为可读格式
                        try:
                            time_display = datetime.fromtimestamp(pub_date).strftime('%Y-%m-%d %H:%M:%S')
                        except (ValueError, OSError):
                            time_display = "未知时间"
                    else:
                        time_display = str(pub_date)
                else:
                    time_display = "未知时间"
                impact = news.get('impact', '')
                
                content["post"]["zh_cn"]["content"].append([
                    {
                        "tag": "text",
                        "text": f"   📍 来源：{mapped_source} | ⏰ 时间：{time_display}"
                    }
                ])
                
                # 添加影响信息
                if impact:
                    content["post"]["zh_cn"]["content"].append([
                        {
                            "tag": "text",
                            "text": f"   💡 影响：{impact}"
                        }
                    ])
                
                # 添加空行（除了最后一条新闻）
                if i < min(len(news_list), 10):
                    content["post"]["zh_cn"]["content"].append([
                        {
                            "tag": "text",
                            "text": ""
                        }
                    ])
            
            # 添加页脚
            content["post"]["zh_cn"]["content"].append([
                {
                    "tag": "text",
                    "text": "──────────────────────────────"
                }
            ])
            
            content["post"]["zh_cn"]["content"].append([
                {
                    "tag": "text",
                    "text": "🤖 本新闻汇总由AI智能整理生成"
                }
            ])
            
            content["post"]["zh_cn"]["content"].append([
                {
                    "tag": "text",
                    "text": f"📅 生成时间：{current_time}"
                }
            ])
            
            return content
            
        except Exception as e:
            logging.error(f"创建新闻消息失败: {str(e)}")
            # 返回简单的错误消息
            return {
                "post": {
                    "zh_cn": {
                        "title": "📰 每日新闻汇总",
                        "content": [
                            [
                                {
                                    "tag": "text",
                                    "text": "抱歉，生成新闻消息时出现错误，请稍后重试。"
                                }
                            ]
                        ]
                    }
                }
            }
    
    def create_news_interactive_message(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建新闻交互式消息格式
        
        Args:
            news_data: 新闻数据
            
        Returns:
            Dict: 飞书交互式消息格式
        """
        try:
            current_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y年%m月%d日 %H:%M:%S')
            
            # 提取新闻数据
            news_list = news_data.get('data', {}).get('news_list', [])
            summary = news_data.get('data', {}).get('summary', '今日新闻概览')
            total_count = news_data.get('data', {}).get('total_count', len(news_list))
            
            # 构建交互式消息内容
            elements = []
            
            # 添加概览
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"📋 **今日概览：**{summary}"
                }
            })
            
            # 添加统计信息
            positive_count = news_data.get('data', {}).get('positive_count', 0)
            negative_count = news_data.get('data', {}).get('negative_count', 0)
            
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"📊 **新闻统计：**共 {total_count} 条精选新闻"
                }
            })
            
            # 添加影响统计
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"📈 **正向影响：**{positive_count} 条 | 📉 **负向影响：**{negative_count} 条"
                }
            })
            
            # 添加分隔线
            elements.append({
                "tag": "hr"
            })
            
            # 添加新闻列表（最多10条）
            for i, news in enumerate(news_list[:10], 1):
                title = news.get('title', '')
                news_summary = news.get('summary', '')
                source = news.get('source', '')
                pub_date = news.get('pubDate', '')
                url = news.get('url', '')
                
                # 使用映射后的消息来源（支持多个来源）
                mapped_source = self.get_mapped_sources(source)
                
                # 新闻标题和链接
                # 处理pub_date，可能是字符串或整数
                if pub_date:
                    if isinstance(pub_date, str):
                        time_display = pub_date.strip() if pub_date.strip() else "未知时间"
                    elif isinstance(pub_date, int):
                        # 如果是时间戳，转换为可读格式
                        try:
                            time_display = datetime.fromtimestamp(pub_date).strftime('%Y-%m-%d %H:%M:%S')
                        except (ValueError, OSError):
                            time_display = "未知时间"
                    else:
                        time_display = str(pub_date)
                else:
                    time_display = "未知时间"
                impact = news.get('impact', '')
                news_content = f"{i}. **{title}**\n"
                if news_summary:
                    news_content += f"   {news_summary}\n"
                news_content += f"   📍 来源：{mapped_source} | ⏰ 时间：{time_display}"
                if impact:
                    news_content += f"\n   💡 影响：{impact}"
                
                elements.append({
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": news_content
                    }
                })
                
                # 添加链接按钮
                if url:
                    elements.append({
                        "tag": "action",
                        "actions": [
                            {
                                "tag": "button",
                                "text": {
                                    "tag": "plain_text",
                                    "content": "查看详情"
                                },
                                "url": url,
                                "type": "default"
                            }
                        ]
                    })
                
                # 添加空行（除了最后一条新闻）
                if i < min(len(news_list), 10):
                    elements.append({
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": ""
                        }
                    })
            
            # 添加页脚
            elements.append({
                "tag": "hr"
            })
            
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "🤖 本新闻汇总由AI智能整理生成"
                }
            })
            
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"📅 生成时间：{current_time}"
                }
            })
            
            # 构建交互式消息
            content = {
                "config": {
                    "wide_screen_mode": True
                },
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"📰 每日新闻汇总 - {current_time}"
                    }
                },
                "elements": elements
            }
            
            return content
            
        except Exception as e:
            logging.error(f"创建新闻交互式消息失败: {str(e)}")
            # 返回简单的错误消息
            return {
                "config": {
                    "wide_screen_mode": True
                },
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": "📰 每日新闻汇总"
                    }
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": "抱歉，生成新闻消息时出现错误，请稍后重试。"
                        }
                    }
                ]
            }
    
    def _create_default_news_message(self, news_data: Dict[str, Any], current_time: str) -> Dict[str, Any]:
        """
        创建默认的新闻消息格式（备用方案）
        
        Args:
            news_data: 新闻数据
            current_time: 当前时间
            
        Returns:
            Dict: 飞书富文本消息格式
        """
        try:
            # 提取新闻数据
            news_list = news_data.get('data', {}).get('news_list', [])
            summary = news_data.get('data', {}).get('summary', '今日新闻概览')
            total_count = news_data.get('data', {}).get('total_count', len(news_list))
            
            # 构建消息内容
            content = {
                "post": {
                    "zh_cn": {
                        "title": f"📰 每日新闻汇总 - {current_time}",
                        "content": []
                    }
                }
            }
            
            # 添加概览
            content["post"]["zh_cn"]["content"].append([
                {
                    "tag": "text",
                    "text": f"📋 今日概览：{summary}"
                }
            ])
            
            # 添加统计信息
            positive_count = news_data.get('data', {}).get('positive_count', 0)
            negative_count = news_data.get('data', {}).get('negative_count', 0)
            
            content["post"]["zh_cn"]["content"].append([
                {
                    "tag": "text",
                    "text": f"📊 新闻统计：共 {total_count} 条精选新闻"
                }
            ])
            
            # 添加影响统计
            content["post"]["zh_cn"]["content"].append([
                {
                    "tag": "text",
                    "text": f"📈 正向影响：{positive_count} 条 | 📉 负向影响：{negative_count} 条"
                }
            ])
            
            # 添加分隔线
            content["post"]["zh_cn"]["content"].append([
                {
                    "tag": "text",
                    "text": "─" * 30
                }
            ])
            
            # 添加新闻列表
            for i, news in enumerate(news_list[:10], 1):  # 最多显示10条
                title = news.get('title', '')
                summary = news.get('summary', '')
                source = news.get('source', '')
                pub_date = news.get('pubDate', '')
                url = news.get('url', '')
                
                # 使用映射后的消息来源（支持多个来源）
                mapped_source = self.get_mapped_sources(source)
                
                # 新闻标题
                content["post"]["zh_cn"]["content"].append([
                    {
                        "tag": "text",
                        "text": f"{i}. "
                    },
                    {
                        "tag": "a",
                        "text": title,
                        "href": url
                    }
                ])
                
                # 新闻摘要
                if summary:
                    content["post"]["zh_cn"]["content"].append([
                        {
                            "tag": "text",
                            "text": f"   {summary}"
                        }
                    ])
                
                # 新闻元信息 - 使用映射后的来源
                impact = news.get('impact', '')
                
                content["post"]["zh_cn"]["content"].append([
                    {
                        "tag": "text",
                        "text": f"   📍 来源：{mapped_source} | ⏰ 时间：{pub_date}"
                    }
                ])
                
                # 添加影响信息
                if impact:
                    content["post"]["zh_cn"]["content"].append([
                        {
                            "tag": "text",
                            "text": f"   💡 影响：{impact}"
                        }
                    ])
                
                # 添加空行
                if i < len(news_list[:10]):
                    content["post"]["zh_cn"]["content"].append([
                        {
                            "tag": "text",
                            "text": ""
                        }
                    ])
            
            # 添加页脚
            content["post"]["zh_cn"]["content"].append([
                {
                    "tag": "text",
                    "text": "─" * 30
                }
            ])
            
            content["post"]["zh_cn"]["content"].append([
                {
                    "tag": "text",
                    "text": "🤖 本新闻汇总由AI智能整理生成"
                }
            ])
            
            content["post"]["zh_cn"]["content"].append([
                {
                    "tag": "text",
                    "text": f"📅 生成时间：{current_time}"
                }
            ])
            
            return content
            
        except Exception as e:
            logging.error(f"创建新闻消息失败: {str(e)}")
            # 返回简单的错误消息
            return {
                "post": {
                    "zh_cn": {
                        "title": "📰 每日新闻汇总",
                        "content": [
                            [
                                {
                                    "tag": "text",
                                    "text": "抱歉，生成新闻消息时出现错误，请稍后重试。"
                                }
                            ]
                        ]
                    }
                }
            }
    
    def send_interactive_message(self, chat_id: str, content: Dict[str, Any]) -> bool:
        """
        发送交互式消息
        
        Args:
            chat_id: 群组ID
            content: 交互式消息内容
            
        Returns:
            bool: 是否发送成功
        """
        try:
            access_token = self.get_access_token()
            if not access_token:
                logging.error("获取访问令牌失败")
                return False
            
            url = f"{self.base_url}/im/v1/messages?receive_id_type=chat_id"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "receive_id": chat_id,
                "msg_type": "interactive",
                "content": json.dumps(content, ensure_ascii=False, separators=(',', ':'))
            }
            
            # 打印详细请求信息
            print(f"\n🔍 发送飞书交互式消息详情:")
            print(f"📤 URL: {url}")
            print(f"📋 Headers: {json.dumps(headers, ensure_ascii=False)}")
            print(f"📄 Data: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            response = requests.post(url, headers=headers, json=data, timeout=10)
            
            # 打印响应信息
            print(f"📊 响应状态码: {response.status_code}")
            print(f"📄 响应内容: {response.text}")
            
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('code') == 0:
                logging.info(f"成功发送交互式消息到群组 {chat_id}")
                print(f"✅ 交互式消息发送成功")
                return True
            else:
                logging.error(f"发送交互式消息失败: {result.get('msg')}")
                print(f"❌ 交互式消息发送失败: {result.get('msg')}")
                return False
                
        except Exception as e:
            logging.error(f"发送交互式消息异常: {str(e)}")
            print(f"❌ 交互式消息发送异常: {str(e)}")
            return False
    
    def send_news_message(self, chat_id: str, news_data: Dict[str, Any]) -> bool:
        """
        发送新闻消息到飞书群组
        
        Args:
            chat_id: 群组ID
            news_data: 新闻数据
            
        Returns:
            bool: 是否发送成功
        """
        try:
            # 创建新闻交互式消息格式
            content = self.create_news_interactive_message(news_data)
            
            # 发送交互式消息
            return self.send_interactive_message(chat_id, content)
            
        except Exception as e:
            logging.error(f"发送新闻消息失败: {str(e)}")
            return False
    
    def send_crypto_news_message(self, chat_id: str, news_data: Dict[str, Any]) -> bool:
        """
        发送加密货币新闻消息到飞书群组
        
        Args:
            chat_id: 群组ID
            news_data: 新闻数据
            
        Returns:
            bool: 是否发送成功
        """
        try:
            # 创建加密货币新闻交互式消息格式
            content = self.create_crypto_news_interactive_message(news_data)
            
            # 发送交互式消息
            return self.send_interactive_message(chat_id, content)
            
        except Exception as e:
            logging.error(f"发送加密货币新闻消息失败: {str(e)}")
            return False
    
    def create_crypto_news_interactive_message(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建加密货币新闻交互式消息格式
        
        Args:
            news_data: 新闻数据
            
        Returns:
            Dict: 飞书交互式消息格式
        """
        try:
            current_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y年%m月%d日 %H:%M:%S')
            
            # 提取新闻数据
            news_list = news_data.get('data', {}).get('news_list', [])
            
            # 构建交互式消息内容
            elements = []
            
            # 添加新闻列表（最多10条）
            for i, news in enumerate(news_list[:10], 1):
                title = news.get('title', '')
                news_summary = news.get('summary', '')
                pub_date = news.get('pubDate', '')
                url = news.get('url', '')
                
                # 新闻标题和链接
                time_display = pub_date if pub_date else "未知时间"
                
                news_content = f"{i}. **{title}**\n"
                if news_summary:
                    news_content += f"   {news_summary}\n"
                news_content += f"   ⏰ 时间：{time_display}"
                
                elements.append({
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": news_content
                    }
                })
                
                # 添加链接按钮
                if url:
                    elements.append({
                        "tag": "action",
                        "actions": [
                            {
                                "tag": "button",
                                "text": {
                                    "tag": "plain_text",
                                    "content": "查看详情"
                                },
                                "url": url,
                                "type": "default"
                            }
                        ]
                    })
                
                # 添加空行（除了最后一条新闻）
                if i < min(len(news_list), 10):
                    elements.append({
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": ""
                        }
                    })
            
            # 构建交互式消息
            content = {
                "config": {
                    "wide_screen_mode": True
                },
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"🚀 加密货币市场动态 - {current_time}"
                    }
                },
                "elements": elements
            }
            
            return content
            
        except Exception as e:
            logging.error(f"创建加密货币新闻交互式消息失败: {str(e)}")
            # 返回简单的错误消息
            return {
                "config": {
                    "wide_screen_mode": True
                },
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": "🚀 加密货币市场动态"
                    }
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": "抱歉，生成加密货币新闻消息时出现错误，请稍后重试。"
                        }
                    }
                ]
            }

# 创建飞书机器人实例
feishu_bot = FeishuBot()
