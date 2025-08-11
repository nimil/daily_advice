import requests
import logging
from datetime import datetime
import pytz
import sqlite3
import json
from typing import Dict, Any, Optional
import os

class HolidayQuery:
    """节假日查询类"""
    
    def __init__(self, api_key: str, db_path: str = "data/holiday.db"):
        """
        初始化节假日查询类
        
        Args:
            api_key: 聚合数据API密钥
            db_path: SQLite数据库路径
        """
        self.api_key = api_key
        self.db_path = db_path
        self.base_url = "http://apis.juhe.cn/fapig/calendar/day"
        # 确保数据目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_db()
        
    def init_db(self):
        """初始化数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 创建假日信息表，包含所有字段
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS holiday_cache (
                        date TEXT PRIMARY KEY,
                        week TEXT,
                        status_desc TEXT,
                        status TEXT,
                        animal TEXT,
                        avoid TEXT,
                        cn_day TEXT,
                        day TEXT,
                        desc TEXT,
                        gz_date TEXT,
                        gz_month TEXT,
                        gz_year TEXT,
                        is_big_month TEXT,
                        l_date TEXT,
                        l_month TEXT,
                        lunar_date TEXT,
                        lunar_month TEXT,
                        lunar_year TEXT,
                        month TEXT,
                        suit TEXT,
                        term TEXT,
                        value TEXT,
                        year TEXT,
                        raw_data TEXT,  -- 存储原始JSON数据
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
        except Exception as e:
            logging.error(f"初始化数据库失败: {str(e)}")

    def get_current_date(self) -> str:
        """获取中国时区的当前日期"""
        cn_tz = pytz.timezone('Asia/Shanghai')
        return datetime.now(cn_tz).strftime('%Y-%m-%d')

    def get_from_cache(self, date: str) -> Optional[Dict]:
        """从缓存中获取数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT raw_data FROM holiday_cache WHERE date = ?', (date,))
                result = cursor.fetchone()
                if result and result[0]:
                    return {
                        'error_code': 0,
                        'reason': 'success (from cache)',
                        'result': json.loads(result[0])
                    }
                return None
        except Exception as e:
            logging.error(f"从缓存获取数据失败: {str(e)}")
            return None

    def save_to_cache(self, date: str, data: Dict):
        """保存数据到缓存"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 准备所有字段的数据
                fields = {
                    'date': date,
                    'week': data.get('week'),
                    'status_desc': data.get('statusDesc'),
                    'status': data.get('status'),
                    'animal': data.get('animal'),
                    'avoid': data.get('avoid'),
                    'cn_day': data.get('cnDay'),
                    'day': data.get('day'),
                    'desc': data.get('desc'),
                    'gz_date': data.get('gzDate'),
                    'gz_month': data.get('gzMonth'),
                    'gz_year': data.get('gzYear'),
                    'is_big_month': data.get('isBigMonth'),
                    'l_date': data.get('lDate'),
                    'l_month': data.get('lMonth'),
                    'lunar_date': data.get('lunarDate'),
                    'lunar_month': data.get('lunarMonth'),
                    'lunar_year': data.get('lunarYear'),
                    'month': data.get('month'),
                    'suit': data.get('suit'),
                    'term': data.get('term'),
                    'value': data.get('value'),
                    'year': data.get('year'),
                    'raw_data': json.dumps(data, ensure_ascii=False)  # 存储完整的JSON数据
                }
                
                # 构建SQL语句
                columns = ', '.join(fields.keys())
                placeholders = ', '.join(['?' for _ in fields])
                sql = f'''
                    INSERT OR REPLACE INTO holiday_cache 
                    ({columns}, created_at)
                    VALUES ({placeholders}, CURRENT_TIMESTAMP)
                '''
                
                cursor.execute(sql, list(fields.values()))
                conn.commit()
        except Exception as e:
            logging.error(f"保存数据到缓存失败: {str(e)}")

    def query_today(self, current_date: str) -> Dict[str, Any]:
        """查询今天的节假日信息"""


        # 先从缓存中查询
        cached_data = self.get_from_cache(current_date)
        if cached_data:
            return cached_data
            
        # 缓存中没有，从API获取
        params = {
            'key': self.api_key,
            'date': current_date
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            result = response.json()
            
            if result.get('error_code') == 0:
                # 保存到缓存
                self.save_to_cache(current_date, result.get('result', {}))
                return result
            else:
                logging.error(f"查询失败: {result.get('reason')}")
                return result
                
        except Exception as e:
            logging.error(f"请求异常: {str(e)}")
            return {'error_code': -1, 'reason': '请求发生错误'}

def test_query():
    """测试查询功能"""
    from config import config
    
    # 初始化查询类
    holiday = HolidayQuery(config.HOLIDAY_API_KEY)
    
    # 测试查询今天的节假日信息
    result = holiday.query_today('2025-02-07')
    print("\n查询今天的节假日信息:")
    print(result)

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    test_query() 