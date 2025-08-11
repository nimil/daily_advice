import requests
import logging
from datetime import datetime
import pytz
import json
import os
from typing import Dict, Any, Optional

class LifeSuggestionQuery:
    """生活建议和天气查询类"""
    
    def __init__(self, api_key: str):
        """
        初始化查询类
        
        Args:
            api_key: 心知天气API密钥
        """
        self.api_key = api_key
        self.suggestion_url = "https://api.seniverse.com/v3/life/suggestion.json"
        self.weather_url = "https://api.seniverse.com/v3/weather/now.json"

    def get_current_date(self) -> str:
        """获取中国时区的当前日期"""
        cn_tz = pytz.timezone('Asia/Shanghai')
        return datetime.now(cn_tz).strftime('%Y-%m-%d')

    def query_suggestion(self, location: str = "jinan") -> Dict[str, Any]:
        """
        查询生活建议信息
        
        Args:
            location: 城市名称，默认为济南
            
        Returns:
            Dict: 生活建议信息
        """
        try:
            params = {
                'key': self.api_key,
                'location': location,
                'language': 'zh-Hans',
                'days': 1
            }
            
            response = requests.get(self.suggestion_url, params=params)
            result = response.json()
            
            if 'results' in result:
                return result
            else:
                logging.error(f"查询生活建议失败: {result}")
                return {'error': '查询生活建议失败', 'data': result}
                
        except Exception as e:
            logging.error(f"生活建议请求异常: {str(e)}")
            return {'error': '请求发生错误', 'data': str(e)}

    def query_weather(self, location: str = "jinan") -> Dict[str, Any]:
        """
        查询实时天气信息
        
        Args:
            location: 城市名称，默认为济南
            
        Returns:
            Dict: 天气信息
        """
        try:
            params = {
                'key': self.api_key,
                'location': location,
                'language': 'zh-Hans',
                'unit': 'c'
            }
            
            response = requests.get(self.weather_url, params=params)
            result = response.json()
            
            if 'results' in result:
                return result
            else:
                logging.error(f"查询天气失败: {result}")
                return {'error': '查询天气失败', 'data': result}
                
        except Exception as e:
            logging.error(f"天气请求异常: {str(e)}")
            return {'error': '请求发生错误', 'data': str(e)}

    def get_all_info(self, location: str = "jinan") -> Dict[str, Any]:
        """
        获取所有天气相关信息
        
        Args:
            location: 城市名称，默认为济南
            
        Returns:
            Dict: 包含天气和生活建议的完整信息
        """
        weather = self.query_weather(location)
        suggestion = self.query_suggestion(location)
        
        # 提取天气文本
        weather_text = ""
        temperature = ""
        if 'results' in weather and weather['results']:
            now = weather['results'][0].get('now', {})
            weather_text = now.get('text', '')
            temperature = now.get('temperature', '')
            
        # 提取指定的生活建议字段
        suggestion_data = {}
        if ('results' in suggestion and suggestion['results'] and 
            suggestion['results'][0].get('suggestion') and 
            isinstance(suggestion['results'][0]['suggestion'], list) and 
            suggestion['results'][0]['suggestion']):
            # 获取第一天的建议
            suggestion_info = suggestion['results'][0]['suggestion'][0]
            fields_to_extract = {
                'air_pollution': '空气污染扩散条件',
                'dressing': '穿衣',
                'mood': '心情',
                'sport': '运动'
            }
            
            for field, desc in fields_to_extract.items():
                if field in suggestion_info:
                    field_data = suggestion_info[field]
                    suggestion_data[field] = {
                        'name': desc,
                        'brief': field_data.get('brief', ''),
                        'details': field_data.get('details', '')
                    }
        
        return {
            'weather': {
                'text': weather_text,
                'temperature': temperature
            },
            'suggestion': suggestion_data
        }

def test_query():
    """测试查询功能"""
    from config import config
    
    # 初始化查询类
    query = LifeSuggestionQuery(config.LIFE_SUGGESTION_API_KEY)
    
    # 测试获取所有信息
    result = query.get_all_info()
    print("\n查询天气和生活建议信息:")
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    test_query() 