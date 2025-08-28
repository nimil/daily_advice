#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
汇率查询模块
使用akshare获取USD对JPY和CNY的汇率
"""

import akshare as ak
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import pytz

class CurrencyAPI:
    """汇率查询类"""
    
    def __init__(self, api_key: str):
        """
        初始化汇率查询
        
        Args:
            api_key: API密钥
        """
        self.api_key = api_key
    
    def get_usd_rates(self) -> Dict[str, Any]:
        """
        获取USD对JPY和CNY的汇率
        
        Returns:
            Dict: 包含汇率数据的字典
        """
        try:
            logging.info("开始获取USD汇率数据")
            
            # 获取USD对JPY和CNY的汇率
            currency_df = None
            try:
                # 尝试获取汇率数据
                if self.api_key and self.api_key != "dummy_key":
                    currency_df = ak.currency_latest(base="USD", symbols="JPY,CNY", api_key=self.api_key)
                else:
                    # 如果没有有效的API_KEY，返回错误
                    return {
                        'error_code': 1,
                        'message': '缺少有效的汇率API密钥',
                        'data': {}
                    }
            except Exception as e:
                return {
                    'error_code': 1,
                    'message': f'汇率API调用失败: {str(e)}',
                    'data': {}
                }
            
            # 检查数据是否为空
            if currency_df is None or currency_df.empty:
                return {
                    'error_code': 1,
                    'message': '获取汇率数据失败：数据为空',
                    'data': {}
                }
            
            # 解析汇率数据
            jpy_data = None
            cny_data = None
            
            for _, row in currency_df.iterrows():
                currency = str(row.get('currency', ''))
                if currency == 'JPY':
                    jpy_data = row
                elif currency == 'CNY':
                    cny_data = row
            
            if jpy_data is None or cny_data is None:
                return {
                    'error_code': 1,
                    'message': '获取汇率数据失败：缺少JPY或CNY数据',
                    'data': {}
                }
            
            # 格式化数据
            formatted_data = {
                'jpy': {
                    'currency': str(jpy_data.get('currency', 'JPY')),
                    'rate': float(jpy_data.get('rates', 0)),
                    'date': str(jpy_data.get('date', '')),
                    'base': str(jpy_data.get('base', 'USD'))
                },
                'cny': {
                    'currency': str(cny_data.get('currency', 'CNY')),
                    'rate': float(cny_data.get('rates', 0)),
                    'date': str(cny_data.get('date', '')),
                    'base': str(cny_data.get('base', 'USD'))
                }
            }
            
            logging.info(f"成功获取USD汇率数据，JPY: {formatted_data['jpy']['rate']}, CNY: {formatted_data['cny']['rate']}")
            
            return {
                'error_code': 0,
                'message': '获取成功',
                'data': formatted_data
            }
            
        except Exception as e:
            logging.error(f"获取USD汇率数据异常: {str(e)}")
            return {
                'error_code': 1,
                'message': f'获取汇率数据异常: {str(e)}',
                'data': {}
            }
    
    def get_gold_price(self) -> Dict[str, Any]:
        """
        获取黄金价格数据
        
        Returns:
            Dict: 包含黄金价格数据的字典
        """
        try:
            logging.info("开始获取黄金价格数据")
            
            # 获取Au99.99黄金价格数据
            gold_df = ak.spot_quotations_sge(symbol="Au99.99")
            
            # 检查数据是否为空
            if gold_df.empty:
                return {
                    'error_code': 1,
                    'message': '获取黄金价格数据失败：数据为空',
                    'data': {}
                }
            
            # 获取最新一条数据（最后一条）
            latest_gold_data = gold_df.iloc[-1]
            
            # 解析黄金价格数据
            gold_price = latest_gold_data.get('现价', 0)
            gold_time = latest_gold_data.get('时间', '')
            gold_update_time = latest_gold_data.get('更新时间', '')
            gold_symbol = latest_gold_data.get('品种', 'Au99.99')
            
            # 格式化数据
            formatted_data = {
                'symbol': gold_symbol,
                'price': gold_price,
                'time': gold_time,
                'update_time': gold_update_time
            }
            
            logging.info(f"成功获取黄金价格数据，价格: {gold_price}, 时间: {gold_time}")
            
            return {
                'error_code': 0,
                'message': '获取成功',
                'data': formatted_data
            }
            
        except Exception as e:
            logging.error(f"获取黄金价格数据异常: {str(e)}")
            return {
                'error_code': 1,
                'message': f'获取黄金价格数据异常: {str(e)}',
                'data': {}
            }
    
    def get_all_market_data(self) -> Dict[str, Any]:
        """
        获取所有市场数据（汇率+黄金价格）
        
        Returns:
            Dict: 包含汇率和黄金价格数据的字典
        """
        try:
            logging.info("开始获取所有市场数据")
            
            # 获取汇率数据
            currency_result = self.get_usd_rates()
            # 获取黄金价格数据
            gold_result = self.get_gold_price()
            
            # 整合数据
            all_data = {
                'currency': currency_result.get('data', {}) if currency_result['error_code'] == 0 else {},
                'gold': gold_result.get('data', {}) if gold_result['error_code'] == 0 else {},
                'currency_error': currency_result.get('message', '') if currency_result['error_code'] != 0 else None,
                'gold_error': gold_result.get('message', '') if gold_result['error_code'] != 0 else None
            }
            
            # 判断整体成功状态
            if currency_result['error_code'] == 0 and gold_result['error_code'] == 0:
                return {
                    'error_code': 0,
                    'message': '获取成功',
                    'data': all_data
                }
            elif currency_result['error_code'] == 0 or gold_result['error_code'] == 0:
                return {
                    'error_code': 1,
                    'message': '部分数据获取成功',
                    'data': all_data
                }
            else:
                return {
                    'error_code': 2,
                    'message': '所有数据获取失败',
                    'data': all_data
                }
                
        except Exception as e:
            logging.error(f"获取所有市场数据异常: {str(e)}")
            return {
                'error_code': 1,
                'message': f'获取市场数据异常: {str(e)}',
                'data': {}
            }

# 创建全局实例（需要在config中获取API_KEY）
currency_api = None
