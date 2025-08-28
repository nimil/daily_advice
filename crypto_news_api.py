#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
加密货币新闻API模块
用于获取BlockBeats的加密货币新闻
"""

import requests
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import pytz
from config import config

class CryptoNewsAPI:
    """加密货币新闻API类"""
    
    def __init__(self):
        """初始化加密货币新闻API"""
        self.base_url = "https://api.theblockbeats.news/v1/open-api/open-flash"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # 记录已发送的最大ID，避免重复发送
        self.max_sent_id = 0
    
    def fetch_crypto_news(self, size: int = 10, page: int = 1) -> Dict[str, Any]:
        """
        获取加密货币新闻
        
        Args:
            size: 获取的新闻数量，默认10条
            page: 页码，默认第1页
            
        Returns:
            Dict: 包含新闻数据的字典
        """
        try:
            params = {
                'size': size,
                'page': page,
                'type': 'push'
            }
            
            response = requests.get(
                self.base_url, 
                params=params, 
                headers=self.headers, 
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 0:
                return {
                    'error_code': 0,
                    'message': '获取成功',
                    'data': data.get('data', {})
                }
            else:
                return {
                    'error_code': 1,
                    'message': f"API返回错误: {data.get('message', '未知错误')}",
                    'data': {}
                }
                
        except requests.exceptions.RequestException as e:
            logging.error(f"请求加密货币新闻API失败: {str(e)}")
            return {
                'error_code': 1,
                'message': f"网络请求失败: {str(e)}",
                'data': {}
            }
        except json.JSONDecodeError as e:
            logging.error(f"解析加密货币新闻API响应失败: {str(e)}")
            return {
                'error_code': 1,
                'message': f"响应解析失败: {str(e)}",
                'data': {}
            }
        except Exception as e:
            logging.error(f"获取加密货币新闻异常: {str(e)}")
            return {
                'error_code': 1,
                'message': f"获取新闻异常: {str(e)}",
                'data': {}
            }
    
    def format_news_for_feishu(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化新闻数据为飞书消息格式
        
        Args:
            news_data: 原始新闻数据
            
        Returns:
            Dict: 格式化后的新闻数据
        """
        try:
            news_list = news_data.get('data', [])
            if not news_list:
                return {
                    'error_code': 1,
                    'message': '没有获取到新闻数据',
                    'data': {}
                }
            
            # 格式化新闻列表
            formatted_news = []
            for news in news_list:
                # 解析HTML内容，提取纯文本
                content = news.get('content', '')
                if content:
                    # 简单的HTML标签清理
                    import re
                    content = re.sub(r'<[^>]+>', '', content)
                    content = content.replace('&nbsp;', ' ').strip()
                
                formatted_news.append({
                    'title': news.get('title', ''),
                    'summary': content[:200] + '...' if len(content) > 200 else content,
                    'pubDate': self._format_timestamp(news.get('create_time', '')),
                    'url': news.get('link', '')
                })
            
            return {
                'error_code': 0,
                'message': '格式化成功',
                'data': {
                    'news_list': formatted_news,
                    'total_count': len(formatted_news),
                    'summary': f'加密货币市场最新动态 - 共{len(formatted_news)}条重要新闻',
                    'positive_count': 0,  # 可以根据内容分析设置
                    'negative_count': 0   # 可以根据内容分析设置
                }
            }
            
        except Exception as e:
            logging.error(f"格式化加密货币新闻失败: {str(e)}")
            return {
                'error_code': 1,
                'message': f"格式化失败: {str(e)}",
                'data': {}
            }
    
    def _format_timestamp(self, timestamp: Any) -> str:
        """
        格式化时间戳
        
        Args:
            timestamp: 时间戳（可能是字符串或整数）
            
        Returns:
            str: 格式化后的时间字符串
        """
        try:
            if isinstance(timestamp, str):
                timestamp = int(timestamp)
            
            if isinstance(timestamp, int):
                # 假设是Unix时间戳
                dt = datetime.fromtimestamp(timestamp, pytz.timezone('Asia/Shanghai'))
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            else:
                return str(timestamp)
        except (ValueError, TypeError, OSError):
            return "未知时间"
    
    def get_latest_crypto_news(self) -> Dict[str, Any]:
        """
        获取最新的加密货币新闻（完整流程）
        
        Returns:
            Dict: 包含格式化新闻数据的字典
        """
        # 获取原始新闻数据
        raw_news = self.fetch_crypto_news(size=10, page=1)
        
        if raw_news['error_code'] != 0:
            return raw_news
        
        # 格式化新闻数据
        return self.format_news_for_feishu(raw_news['data'])
    
    def get_new_crypto_news(self) -> Dict[str, Any]:
        """
        获取新的加密货币新闻（过滤已发送的）
        
        Returns:
            Dict: 包含格式化新闻数据的字典，如果没有新新闻则返回空列表
        """
        # 获取原始新闻数据
        raw_news = self.fetch_crypto_news(size=10, page=1)
        
        if raw_news['error_code'] != 0:
            return raw_news
        
        # 过滤出新的新闻（ID大于已发送的最大ID）
        news_list = raw_news['data'].get('data', [])
        new_news_list = []
        new_max_id = self.max_sent_id
        
        for news in news_list:
            news_id = news.get('id', 0)
            if news_id > self.max_sent_id:
                new_news_list.append(news)
                new_max_id = max(new_max_id, news_id)
        
        # 更新最大ID
        if new_news_list:
            self.max_sent_id = new_max_id
            logging.info(f"发现 {len(new_news_list)} 条新新闻，最大ID: {self.max_sent_id}")
        else:
            logging.info(f"没有新新闻，当前最大ID: {self.max_sent_id}")
        
        # 创建新的数据结构，只包含新新闻
        filtered_data = {
            'data': new_news_list
        }
        
        # 格式化新闻数据
        return self.format_news_for_feishu(filtered_data)
    
    def get_max_sent_id(self) -> int:
        """
        获取已发送的最大ID
        
        Returns:
            int: 最大ID
        """
        return self.max_sent_id
    
    def reset_max_sent_id(self) -> None:
        """
        重置最大ID（用于测试或特殊情况）
        """
        self.max_sent_id = 0
        logging.info("已重置最大ID")

# 创建全局实例
crypto_news_api = CryptoNewsAPI()
