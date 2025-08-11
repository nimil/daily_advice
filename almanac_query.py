import requests
import logging
from datetime import datetime, timedelta
import pytz
import sqlite3
import json
import os
from typing import Dict, Any, Optional, List
import threading
from queue import Queue
from flask import current_app
from app_context import app  # 改用新的导入

# 创建一个队列来存储待处理的日期
date_queue = Queue()

class AlmanacQuery:
    """老黄历查询类"""
    
    def __init__(self, api_key: str, db_path: str = "data/almanac.db"):
        """
        初始化老黄历查询类
        
        Args:
            api_key: 聚合数据API密钥
            db_path: SQLite数据库路径
        """
        self.api_key = api_key
        self.db_path = db_path
        self.base_url = "http://v.juhe.cn/laohuangli/d"
        # 确保数据目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_db()
        
    def init_db(self):
        """初始化数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 创建老黄历信息表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS almanac_cache (
                        date TEXT PRIMARY KEY,
                        yangli TEXT,           -- 阳历
                        yinli TEXT,            -- 阴历
                        wuxing TEXT,           -- 五行
                        chongsha TEXT,         -- 冲煞
                        baiji TEXT,            -- 彭祖百忌
                        jishen TEXT,           -- 吉神宜趋
                        yi TEXT,               -- 宜
                        xiongshen TEXT,        -- 凶神宜忌
                        ji TEXT,               -- 忌
                        raw_data TEXT,         -- 原始JSON数据
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                # 创建老黄历解释表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS almanac_explanation_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        field_name TEXT,  -- 字段名称(wuxing/chongsha等)
                        field_value TEXT, -- 原始值
                        explanation TEXT, -- AI解释
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(field_name, field_value)
                    )
                ''')
                conn.commit()
        except Exception as e:
            logging.error(f"初始化数据库失败: {str(e)}")

    def get_from_cache(self, date: str) -> Optional[Dict]:
        """从缓存中获取数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT raw_data FROM almanac_cache WHERE date = ?', 
                    (date,)
                )
                result = cursor.fetchone()
                if result:
                    return json.loads(result[0])
                return None
        except Exception as e:
            logging.error(f"从缓存获取数据失败: {str(e)}")
            return None

    def save_to_cache(self, date: str, data: Dict):
        """保存数据到缓存"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                result = data.get('result', {})
                fields = {
                    'date': date,
                    'yangli': result.get('yangli'),
                    'yinli': result.get('yinli'),
                    'wuxing': result.get('wuxing'),
                    'chongsha': result.get('chongsha'),
                    'baiji': result.get('baiji'),
                    'jishen': result.get('jishen'),
                    'yi': result.get('yi'),
                    'xiongshen': result.get('xiongshen'),
                    'ji': result.get('ji'),
                    'raw_data': json.dumps(data, ensure_ascii=False)
                }
                
                columns = ', '.join(fields.keys())
                placeholders = ', '.join(['?' for _ in fields])
                sql = f'''
                    INSERT OR REPLACE INTO almanac_cache 
                    ({columns}, created_at)
                    VALUES ({placeholders}, CURRENT_TIMESTAMP)
                '''
                
                cursor.execute(sql, list(fields.values()))
                conn.commit()
        except Exception as e:
            logging.error(f"保存数据到缓存失败: {str(e)}")

    def get_current_date(self) -> str:
        """获取中国时区的当前日期"""
        cn_tz = pytz.timezone('Asia/Shanghai')
        return datetime.now(cn_tz).strftime('%Y-%m-%d')

    def get_max_date(self) -> Optional[str]:
        """获取数据库中最大的日期"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT MAX(date) FROM almanac_cache')
                result = cursor.fetchone()
                return result[0] if result and result[0] else None
        except Exception as e:
            logging.error(f"获取最大日期失败: {str(e)}")
            return None

    def query_next_n_days(self, n: int = 7) -> List[Dict[str, Any]]:
        """
        查询从最大日期开始的后N天数据
        
        Args:
            n: 要查询的天数
            
        Returns:
            List[Dict]: 查询结果列表
        """
        try:
            # 获取最大日期
            max_date = self.get_max_date()
            if not max_date:
                max_date = self.get_current_date()

            # 计算后N天的日期
            max_date_obj = datetime.strptime(max_date, '%Y-%m-%d')
            dates = [(max_date_obj + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, n+1)]
            
            results = []
            for date in dates:
                result = self.query_almanac(date)
                if result.get('error_code') == 0:
                    results.append(result)
                else:
                    logging.error(f"查询日期 {date} 失败: {result.get('reason')}")
            
            return results
        except Exception as e:
            logging.error(f"查询后续日期失败: {str(e)}")
            return []

    def query_almanac(self, query_date: Optional[str] = None) -> Dict[str, Any]:
        """
        查询老黄历信息
        
        Args:
            query_date: 可选，查询日期，格式：YYYY-MM-DD，默认为当天
            
        Returns:
            Dict: 老黄历信息
        """
        # 如果未指定日期，使用当前日期
        if not query_date:
            query_date = self.get_current_date()
            
        # 先从缓存中查询
        cached_data = self.get_from_cache(query_date)
        if cached_data:
            return cached_data
            
        # 缓存中没有，从API获取
        try:
            params = {
                'key': self.api_key,
                'date': query_date.replace('-', '')  # API要求日期格式为YYYYMMDD
            }
            
            response = requests.get(self.base_url, params=params)
            result = response.json()
            
            if result.get('error_code') == 0:
                # 保存到缓存
                self.save_to_cache(query_date, result)
                return result
            else:
                logging.error(f"查询失败: {result.get('reason')}")
                return result
                
        except Exception as e:
            logging.error(f"请求异常: {str(e)}")
            return {'error_code': -1, 'reason': '请求发生错误'}

    def get_db_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)

    def get_all_almanac_dates(self, start_date: Optional[str] = None) -> List[str]:
        """获取所有老黄历日期
        
        Args:
            start_date: 开始日期，格式：YYYY-MM-DD（可选）
            
        Returns:
            List[str]: 日期列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if start_date:
                    cursor.execute('''
                        SELECT DISTINCT date 
                        FROM almanac_cache 
                        WHERE date >= ? 
                        ORDER BY date
                    ''', (start_date,))
                else:
                    cursor.execute('''
                        SELECT DISTINCT date 
                        FROM almanac_cache 
                        ORDER BY date
                    ''')
                
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"获取老黄历日期失败: {str(e)}")
            return []

    def get_almanac_explanation(self, field_values: Dict[str, str]) -> Dict[str, Any]:
        """获取老黄历解释数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                explanations = {}
                
                for field_name, field_value in field_values.items():
                    if not field_value:
                        continue
                        
                    values = field_value.split()
                    explanations[field_name] = []
                    
                    for value in values:
                        cursor.execute('''
                            SELECT explanation
                            FROM almanac_explanation_cache 
                            WHERE field_name = ? AND field_value = ?
                        ''', (field_name, value))
                        
                        result = cursor.fetchone()
                        if result:
                            explanations[field_name].append({
                                'value': value,
                                'explanation': result[0]
                            })
                        else:
                            explanations[field_name].append({
                                'value': value,
                                'explanation': None
                            })
                            
                return explanations
        except Exception as e:
            logging.error(f"获取老黄历解释失败: {str(e)}")
            return {}

    def save_almanac_explanation(self, field_name: str, field_value: str, explanation: str):
        """保存老黄历解释数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO almanac_explanation_cache 
                    (field_name, field_value, explanation, created_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (field_name, field_value, explanation))
                conn.commit()
        except Exception as e:
            logging.error(f"保存老黄历解释失败: {str(e)}")
            raise e

    def process_explanations(self, glm: Any):
        """异步处理日期的函数"""
        try:
            # 需要解释的字段
            fields = ['wuxing', 'chongsha', 'baiji', 'jishen', 'yi', 'xiongshen', 'ji']
            
            with app.app_context():  # 创建应用上下文
                while not date_queue.empty():
                    date = date_queue.get()
                    try:
                        # 从老黄历表获取数据
                        almanac_data = self.query_almanac(date)
                        if not almanac_data or almanac_data.get('error_code') != 0:
                            app.logger.error(f"获取老黄历数据失败: {date}")
                            continue
                        
                        # 构建字段值字典
                        field_values = {
                            field: almanac_data.get('result', {}).get(field)
                            for field in fields
                        }
                        
                        # 获取已有的解释
                        cached_explanations = self.get_almanac_explanation(field_values)
                        
                        # 处理每个字段
                        for field, field_value in field_values.items():
                            if not field_value:
                                continue
                            
                            # 分词处理
                            values = field_value.split()
                            
                            for value in values:
                                # 检查是否已有解释
                                cached_explanation = next(
                                    (item['explanation'] for item in cached_explanations.get(field, [])
                                     if item['value'] == value and item['explanation']),
                                    None
                                )
                                
                                if not cached_explanation:
                                    # 构造提示语
                                    prompt = f"""
                                    请解释老黄历中的这个概念：{value}
                                    这个概念出现在{field}字段中。
                                    请用通俗易懂的语言解释其含义和作用。
                                    直接返回解释文本，不需要任何多余的格式。
                                    格式为{{"answer": "解释文本"}}
                                    """
                                    
                                    # 调用 AI 获取解释
                                    explanation = glm.chat(prompt)
                                    
                                    if explanation and isinstance(explanation, str):
                                        try:
                                            # 尝试解析JSON
                                            explanation_data = json.loads(explanation)
                                            if isinstance(explanation_data, dict) and 'answer' in explanation_data:
                                                # 保存到缓存
                                                self.save_almanac_explanation(field, value, explanation_data['answer'])
                                        except json.JSONDecodeError:
                                            app.logger.error(f"解析AI响应失败: {explanation}")
                                    else:
                                        app.logger.error(f"AI返回格式错误: {explanation}")
                        
                        app.logger.info(f"处理完成日期: {date}")
                        
                    except Exception as e:
                        app.logger.error(f"处理日期 {date} 失败: {str(e)}")
                    
                    # 标记任务完成
                    date_queue.task_done()
            
        except Exception as e:
            logging.error(f"处理线程异常: {str(e)}")

    def start_batch_explanation(self, start_date: Optional[str] = None, glm: Any = None) -> Dict[str, Any]:
        """启动批量解释处理"""
        try:
            # 获取所有需要处理的日期
            dates = self.get_all_almanac_dates(start_date)
            if not dates:
                return {
                    'code': -1,
                    'message': '没有找到需要处理的日期',
                    'data': None
                }
            
            # 清空队列
            while not date_queue.empty():
                date_queue.get()
            
            # 将日期添加到队列
            for date in dates:
                date_queue.put(date)
            
            # 启动新的处理线程
            thread = threading.Thread(target=self.process_explanations, args=(glm,))
            thread.daemon = True
            thread.start()
            
            return {
                'code': 0,
                'message': '处理已启动',
                'data': {
                    'total_dates': len(dates)
                }
            }
            
        except Exception as e:
            logging.error(f"启动批量处理失败: {str(e)}")
            return {
                'code': -1,
                'message': f'启动批量处理失败: {str(e)}',
                'data': None
            }

def test_query():
    """测试查询功能"""
    from config import config
    
    # 初始化查询类
    almanac = AlmanacQuery(config.ALMANAC_API_KEY)
    
    # 测试查询今天的老黄历
    result = almanac.query_almanac()
    print("\n查询今天的老黄历信息:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 测试查询指定日期的老黄历
    result = almanac.query_almanac("2024-02-05")
    print("\n查询2024-02-05的老黄历信息:")
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    test_query() 