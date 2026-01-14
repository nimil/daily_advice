#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
越南胡志明指数API模块
获取越南胡志明指数数据
"""

import requests
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import pytz

class VietnamIndexAPI:
    """越南胡志明指数API类"""

    def __init__(self):
        """初始化越南指数API"""
        self.base_url = "https://api.hsx.vn/l/api/v1/indicies/hoseindexinfo/homepage"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://api.hsx.vn/"
        })

    def get_vnindex_data(self) -> Dict[str, Any]:
        """
        获取越南胡志明指数(VNINDEX)数据

        Returns:
            Dict: 包含指数数据的字典
        """
        try:
            logging.info("开始获取越南胡志明指数数据")

            # 构建请求参数
            params = {
                "type": "VNINDEX"
            }

            # 发送请求（增加超时时间）
            response = self.session.get(
                self.base_url,
                params=params,
                timeout=30
            )

            # 打印请求详情（用于调试）
            print(f"\n🔍 获取越南胡志明指数API请求:")
            print(f"📤 URL: {response.url}")
            print(f"📊 状态码: {response.status_code}")

            response.raise_for_status()

            # 解析响应
            result = response.json()

            # 打印原始响应（用于调试）
            print(f"📄 原始响应: {json.dumps(result, ensure_ascii=False, indent=2)}")

            # 检查响应是否成功
            if not result.get('success', False):
                return {
                    'error_code': 1,
                    'message': result.get('message', 'API返回失败'),
                    'data': {}
                }

            # 提取数据
            data_list = result.get('data', [])
            if not data_list:
                return {
                    'error_code': 1,
                    'message': 'API返回数据为空',
                    'data': {}
                }

            # 获取VNIndex数据
            vnindex_data = data_list[0]  # 第一个元素就是VNIndex数据

            # 格式化数据
            formatted_data = self._parse_vnindex_data(vnindex_data)

            logging.info(f"成功获取越南胡志明指数数据: {formatted_data}")

            return {
                'error_code': 0,
                'message': '获取成功',
                'data': formatted_data
            }

        except requests.exceptions.RequestException as e:
            logging.error(f"请求越南指数API异常: {str(e)}")
            return {
                'error_code': 1,
                'message': f'请求异常: {str(e)}',
                'data': {}
            }
        except json.JSONDecodeError as e:
            logging.error(f"解析越南指数API响应异常: {str(e)}")
            return {
                'error_code': 1,
                'message': f'解析异常: {str(e)}',
                'data': {}
            }
        except Exception as e:
            logging.error(f"获取越南胡志明指数异常: {str(e)}")
            return {
                'error_code': 1,
                'message': f'获取异常: {str(e)}',
                'data': {}
            }

    def _parse_vnindex_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析越南胡志明指数原始数据

        Args:
            raw_data: API返回的原始数据

        Returns:
            Dict: 格式化后的指数数据
        """
        try:
            # 根据提供的结构解析：
            # {
            #     "id": 22,
            #     "name": "VNIndex",
            #     "value": "1901.02",
            #     "status": -1,
            #     "percent": "-0.1%"
            # }

            name = raw_data.get('name', 'VNIndex')
            value_str = raw_data.get('value', '0')
            status = raw_data.get('status', 0)
            percent_str = raw_data.get('percent', '0%')

            # 解析数值
            try:
                current_value = float(value_str)
            except:
                current_value = 0

            # 解析百分比
            try:
                # 移除百分号并转换为浮点数
                percent_clean = percent_str.replace('%', '').strip()
                change_percent = float(percent_clean)

                # 计算涨跌值（假设当前值是已知的，通过百分比反推变化值）
                # 如果百分比是 -0.1%，那么变化值 = 当前值 * (-0.1/100)
                change = current_value * (change_percent / 100)
            except:
                change_percent = 0
                change = 0

            # 根据status判断涨跌状态
            # status: -1表示下跌，1表示上涨，0表示平盘
            if status == -1:
                trend = "下跌"
                emoji = "📉"
            elif status == 1:
                trend = "上涨"
                emoji = "📈"
            else:
                trend = "平盘"
                emoji = "➡️"

            # 获取当前时间
            current_time = datetime.now(pytz.timezone('Asia/Ho_Chi_Minh')).strftime('%Y-%m-%d %H:%M:%S')

            # 格式化数据
            formatted_data = {
                'index_code': 'VNINDEX',
                'index_name': name,
                'current_value': current_value,
                'change': change,
                'change_percent': change_percent,
                'trend': trend,
                'emoji': emoji,
                'time': current_time,
                'status': status
            }

            return formatted_data

        except Exception as e:
            logging.error(f"解析越南指数数据异常: {str(e)}")
            # 返回空数据结构
            return {
                'index_code': 'VNINDEX',
                'index_name': 'VNIndex',
                'current_value': 0,
                'change': 0,
                'change_percent': 0,
                'trend': '未知',
                'emoji': '➡️',
                'time': datetime.now(pytz.timezone('Asia/Ho_Chi_Minh')).strftime('%Y-%m-%d %H:%M:%S'),
                'status': 0
            }

    def get_vnindex_data_mock(self) -> Dict[str, Any]:
        """
        获取越南胡志明指数的模拟数据（用于测试）

        Returns:
            Dict: 包含指数数据的字典
        """
        import random
        import time

        # 模拟当前指数值在1900附近波动
        base_value = 1900.0
        change = round(random.uniform(-10, 10), 2)
        current_value = base_value + change
        change_percent = round((change / base_value) * 100, 2)

        # 确定涨跌状态
        if change > 0:
            status = 1
            trend = "上涨"
            emoji = "📈"
        elif change < 0:
            status = -1
            trend = "下跌"
            emoji = "📉"
        else:
            status = 0
            trend = "平盘"
            emoji = "➡️"

        # 当前时间
        current_time = datetime.now(pytz.timezone('Asia/Ho_Chi_Minh')).strftime('%Y-%m-%d %H:%M:%S')

        formatted_data = {
            'index_code': 'VNINDEX',
            'index_name': 'VNIndex',
            'current_value': current_value,
            'change': change,
            'change_percent': change_percent,
            'trend': trend,
            'emoji': emoji,
            'time': current_time,
            'status': status
        }

        return {
            'error_code': 0,
            'message': '获取成功（模拟数据）',
            'data': formatted_data
        }

# 创建全局实例
vietnam_index_api = VietnamIndexAPI()