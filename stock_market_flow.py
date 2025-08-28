#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票市场资金流向模块
使用akshare获取大盘资金流向数据
"""

import akshare as ak
import pandas as pd
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import pytz

class StockMarketFlow:
    """股票市场资金流向类"""
    
    def __init__(self):
        """初始化股票市场资金流向"""
        pass
    
    def get_market_fund_flow(self) -> Dict[str, Any]:
        """
        获取大盘资金流向数据（仅今日）
        
        Returns:
            Dict: 包含资金流向数据的字典
        """
        try:
            logging.info("开始获取今日大盘资金流向数据")
            
            # 获取大盘资金流向数据
            df = ak.stock_market_fund_flow()
            
            if df.empty:
                return {
                    'error_code': 1,
                    'message': '获取资金流向数据失败：数据为空',
                    'data': {}
                }
            
            # 获取最新一天的数据（akshare数据按日期正序排列，最新数据在最后）
            latest_data = df.iloc[-1]
            
            # 检查是否为今日数据
            latest_date = latest_data.get('日期', '')
            today = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d')
            
            # 将latest_date转换为字符串进行比较
            if isinstance(latest_date, datetime):
                latest_date_str = latest_date.strftime('%Y-%m-%d')
            else:
                latest_date_str = str(latest_date)
            
            if latest_date_str != today:
                logging.info(f"最新数据日期 {latest_date_str} 不是今日 {today}，跳过发送")
                return {
                    'error_code': 2,
                    'message': f'最新数据不是今日数据（最新：{latest_date_str}，今日：{today}）',
                    'data': {}
                }
            
            # 解析数据
            date = latest_date_str  # 使用已经格式化的日期字符串
            shanghai_close = latest_data.get('上证-收盘价', 0)
            shanghai_change = latest_data.get('上证-涨跌幅', 0)
            
            # 主力资金流向
            main_net_inflow = latest_data.get('主力净流入-净额', 0)
            main_net_ratio = latest_data.get('主力净流入-净占比', 0)
            
            # 超大单资金流向
            super_large_net_inflow = latest_data.get('超大单净流入-净额', 0)
            super_large_net_ratio = latest_data.get('超大单净流入-净占比', 0)
            
            # 大单资金流向
            large_net_inflow = latest_data.get('大单净流入-净额', 0)
            large_net_ratio = latest_data.get('大单净流入-净占比', 0)
            
            # 中单资金流向
            medium_net_inflow = latest_data.get('中单净流入-净额', 0)
            medium_net_ratio = latest_data.get('中单净流入-净占比', 0)
            
            # 小单资金流向
            small_net_inflow = latest_data.get('小单净流入-净额', 0)
            small_net_ratio = latest_data.get('小单净流入-净占比', 0)
            
            # 格式化数据
            formatted_data = {
                'date': date,
                'shanghai': {
                    'close': shanghai_close,
                    'change': shanghai_change
                },
                'fund_flow': {
                    'main': {
                        'net_inflow': main_net_inflow,
                        'net_ratio': main_net_ratio
                    },
                    'super_large': {
                        'net_inflow': super_large_net_inflow,
                        'net_ratio': super_large_net_ratio
                    },
                    'large': {
                        'net_inflow': large_net_inflow,
                        'net_ratio': large_net_ratio
                    },
                    'medium': {
                        'net_inflow': medium_net_inflow,
                        'net_ratio': medium_net_ratio
                    },
                    'small': {
                        'net_inflow': small_net_inflow,
                        'net_ratio': small_net_ratio
                    }
                }
            }
            
            logging.info(f"成功获取大盘资金流向数据，日期：{date}")
            
            return {
                'error_code': 0,
                'message': '获取成功',
                'data': formatted_data
            }
            
        except Exception as e:
            logging.error(f"获取大盘资金流向数据异常: {str(e)}")
            return {
                'error_code': 1,
                'message': f'获取资金流向数据异常: {str(e)}',
                'data': {}
            }
    
    def format_fund_flow_message(self, flow_data: Dict[str, Any], market_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        格式化资金流向消息（包含汇率和黄金价格信息）
        
        Args:
            flow_data: 资金流向数据
            market_data: 市场数据（汇率+黄金价格，可选）
            
        Returns:
            Dict: 格式化后的消息数据
        """
        try:
            data = flow_data.get('data', {})
            date = data.get('date', '')
            shanghai = data.get('shanghai', {})
            fund_flow = data.get('fund_flow', {})
            
            # 格式化金额（亿元）
            def format_amount(amount):
                if pd.isna(amount):
                    return 0
                return round(amount / 100000000, 2)
            
            # 格式化比例
            def format_ratio(ratio):
                if pd.isna(ratio):
                    return 0
                return round(ratio, 2)
            
            # 获取涨跌符号
            def get_change_symbol(change):
                if change > 0:
                    return "📈"
                elif change < 0:
                    return "📉"
                else:
                    return "➡️"
            
            # 获取资金流向符号
            def get_flow_symbol(amount):
                if amount > 0:
                    return "💰"
                elif amount < 0:
                    return "💸"
                else:
                    return "➡️"
            
            # 构建消息内容
            shanghai_close = shanghai.get('close', 0)
            shanghai_change = shanghai.get('change', 0)
            change_symbol = get_change_symbol(shanghai_change)
            
            # 主力资金
            main_flow = fund_flow.get('main', {})
            main_amount = format_amount(main_flow.get('net_inflow', 0))
            main_ratio = format_ratio(main_flow.get('net_ratio', 0))
            main_symbol = get_flow_symbol(main_flow.get('net_inflow', 0))
            
            # 超大单资金
            super_large_flow = fund_flow.get('super_large', {})
            super_large_amount = format_amount(super_large_flow.get('net_inflow', 0))
            super_large_ratio = format_ratio(super_large_flow.get('net_ratio', 0))
            super_large_symbol = get_flow_symbol(super_large_flow.get('net_inflow', 0))
            
            # 大单资金
            large_flow = fund_flow.get('large', {})
            large_amount = format_amount(large_flow.get('net_inflow', 0))
            large_ratio = format_ratio(large_flow.get('net_ratio', 0))
            large_symbol = get_flow_symbol(large_flow.get('net_inflow', 0))
            
            # 中单资金
            medium_flow = fund_flow.get('medium', {})
            medium_amount = format_amount(medium_flow.get('net_inflow', 0))
            medium_ratio = format_ratio(medium_flow.get('net_ratio', 0))
            medium_symbol = get_flow_symbol(medium_flow.get('net_inflow', 0))
            
            # 小单资金
            small_flow = fund_flow.get('small', {})
            small_amount = format_amount(small_flow.get('net_inflow', 0))
            small_ratio = format_ratio(small_flow.get('net_ratio', 0))
            small_symbol = get_flow_symbol(small_flow.get('net_inflow', 0))
            
            # 构建消息内容
            message_content = f"""📊 **今日大盘资金流向** - {date}

**上证指数：** {change_symbol} {shanghai_close} ({shanghai_change:+.2f}%)

**资金流向详情：**
• 主力资金：{main_symbol} {main_amount:+.2f}亿 ({main_ratio:+.2f}%)
• 超大单：{super_large_symbol} {super_large_amount:+.2f}亿 ({super_large_ratio:+.2f}%)
• 大单：{large_symbol} {large_amount:+.2f}亿 ({large_ratio:+.2f}%)
• 中单：{medium_symbol} {medium_amount:+.2f}亿 ({medium_ratio:+.2f}%)
• 小单：{small_symbol} {small_amount:+.2f}亿 ({small_ratio:+.2f}%)"""
            
            # 添加市场信息（汇率+黄金价格）
            if market_data and market_data.get('error_code') in [0, 1]:  # 0=完全成功，1=部分成功
                market_info = market_data.get('data', {})
                
                # 添加汇率信息
                currency_info = market_info.get('currency', {})
                if currency_info:
                    jpy_rate = currency_info.get('jpy', {}).get('rate', 0)
                    cny_rate = currency_info.get('cny', {}).get('rate', 0)
                    
                    message_content += f"""

**💱 汇率信息：**
• USD/JPY：{jpy_rate:.4f}
• USD/CNY：{cny_rate:.4f}"""
                
                # 添加黄金价格信息
                gold_info = market_info.get('gold', {})
                if gold_info:
                    gold_price = gold_info.get('price', 0)
                    gold_time = gold_info.get('time', '')
                    gold_symbol = gold_info.get('symbol', 'Au99.99')
                    
                    message_content += f"""

**🥇 黄金价格：**
• {gold_symbol}：{gold_price:.2f}元/克 ({gold_time})"""
            
            return {
                'error_code': 0,
                'message': '格式化成功',
                'data': {
                    'content': message_content,
                    'date': date,
                    'shanghai_close': shanghai_close,
                    'shanghai_change': shanghai_change,
                    'fund_flow_summary': {
                        'main': main_amount,
                        'super_large': super_large_amount,
                        'large': large_amount,
                        'medium': medium_amount,
                        'small': small_amount
                    }
                }
            }
            
        except Exception as e:
            logging.error(f"格式化资金流向消息失败: {str(e)}")
            return {
                'error_code': 1,
                'message': f'格式化失败: {str(e)}',
                'data': {}
            }

# 创建全局实例
stock_market_flow = StockMarketFlow()
