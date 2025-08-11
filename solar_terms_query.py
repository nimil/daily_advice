import requests
import logging
from datetime import datetime, date
import pytz
import sqlite3
import json
import os
from typing import Dict, Any, Optional, List

class SolarTermsQuery:
    """二十四节气查询类"""
    
    def __init__(self, api_key: str, db_path: str = "data/solar_terms.db"):
        """
        初始化二十四节气查询类
        
        Args:
            api_key: 聚合数据API密钥
            db_path: SQLite数据库路径
        """
        self.api_key = api_key
        self.db_path = db_path
        self.base_url = "http://apis.juhe.cn/fapig/solarTerms/query"
        # 确保数据目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_db()
        
    def init_db(self):
        """初始化数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 创建节气信息表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS solar_terms_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pub_year TEXT,
                        name TEXT,
                        pub_date TEXT,
                        pub_time TEXT,
                        pri_date TEXT,
                        des TEXT,
                        you_lai TEXT,
                        xi_su TEXT,
                        heath TEXT,
                        raw_data TEXT,  -- 存储原始JSON数据
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(pub_year, name)
                    )
                ''')
                # 创建时令食材表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS seasonal_food_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        term TEXT,
                        product_type TEXT,
                        product_area TEXT,
                        vegatables TEXT,
                        nutrition TEXT,
                        cooding_tips TEXT,
                        storage_advice TEXT,
                        food_advice TEXT,
                        province TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(term, province, vegatables)
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

    def convert_date_format(self, date_str: str, year: str) -> str:
        """
        转换日期格式
        
        Args:
            date_str: 原始日期字符串，如 "2月3日"
            year: 年份
            
        Returns:
            str: 转换后的日期字符串，如 "2024-02-03"
        """
        try:
            month, day = date_str.replace('日', '').split('月')
            return f"{year}-{int(month):02d}-{int(day):02d}"
        except Exception as e:
            logging.error(f"日期格式转换失败: {str(e)}")
            return date_str

    def format_date_for_display(self, date_str: str) -> str:
        """
        将标准日期格式转换为显示格式
        
        Args:
            date_str: 标准日期字符串，如 "2024-02-03"
            
        Returns:
            str: 显示格式日期，如 "2月3日"
        """
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return f"{date_obj.month}月{date_obj.day}日"
        except Exception as e:
            logging.error(f"日期格式转换失败: {str(e)}")
            return date_str

    def get_from_cache(self, year: str, name: Optional[str] = None) -> Optional[Dict]:
        """从缓存中获取数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if name:
                    cursor.execute(
                        'SELECT raw_data FROM solar_terms_cache WHERE pub_year = ? AND name = ?', 
                        (year, name)
                    )
                else:
                    cursor.execute(
                        'SELECT raw_data FROM solar_terms_cache WHERE pub_year = ?', 
                        (year,)
                    )
                results = cursor.fetchall()
                if results:
                    return {
                        'error_code': 0,
                        'reason': 'success (from cache)',
                        'result': [json.loads(row[0]) for row in results]
                    }
                return None
        except Exception as e:
            logging.error(f"从缓存获取数据失败: {str(e)}")
            return None

    def save_to_cache(self, data: Dict):
        """保存数据到缓存"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 转换日期格式
                pub_date = self.convert_date_format(data.get('pub_date', ''), data.get('pub_year', ''))
                
                fields = {
                    'pub_year': data.get('pub_year'),
                    'name': data.get('name'),
                    'pub_date': pub_date,  # 使用转换后的日期
                    'pub_time': data.get('pub_time'),
                    'pri_date': data.get('pri_date'),
                    'des': data.get('des'),
                    'you_lai': data.get('youLai'),
                    'xi_su': data.get('xiSu'),
                    'heath': data.get('heath'),
                    'raw_data': json.dumps({
                        **data,
                        'pub_date': pub_date  # 更新JSON中的日期格式
                    }, ensure_ascii=False)
                }
                
                columns = ', '.join(fields.keys())
                placeholders = ', '.join(['?' for _ in fields])
                sql = f'''
                    INSERT OR REPLACE INTO solar_terms_cache 
                    ({columns}, created_at)
                    VALUES ({placeholders}, CURRENT_TIMESTAMP)
                '''
                
                cursor.execute(sql, list(fields.values()))
                conn.commit()
        except Exception as e:
            logging.error(f"保存数据到缓存失败: {str(e)}")

    def query(self, year: Optional[str] = None, name: Optional[str] = None) -> Dict[str, Any]:
        """
        查询节气信息
        
        Args:
            year: 查询年份，如：2024（可选，默认当年）
            name: 节气名称，如：惊蛰、白露（可选，默认查询所有节气）
        """
        # 如果未指定年份，使用当前年份
        if not year:
            year = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y')
            
        # 先从缓存中查询
        cached_data = self.get_from_cache(year, name)
        if cached_data:
            return cached_data
            
        # 缓存中没有，从API获取
        params = {
            'key': self.api_key,
            'year': year,
            'name': name if name else ''
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            result = response.json()
            
            if result.get('error_code') == 0:
                # 保存到缓存
                for item in result.get('result', []):
                    self.save_to_cache(item)
                return result
            else:
                logging.error(f"查询失败: {result.get('reason')}")
                return result
                
        except Exception as e:
            logging.error(f"请求异常: {str(e)}")
            return {'error_code': -1, 'reason': '请求发生错误'}

    def get_current_solar_term(self, query_date: Optional[str] = None) -> Dict[str, Any]:
        """
        获取指定日期的节气信息
        
        Args:
            query_date: 查询日期，格式：YYYY-MM-DD（可选，默认当天）
            
        Returns:
            Dict: 节气信息，包含当前节气和下一个节气
        """
        # 如果未指定日期，使用当前日期
        if not query_date:
            query_date = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d')
            
        # 解析日期
        query_year = query_date[:4]
        query_date_obj = datetime.strptime(query_date, '%Y-%m-%d').date()
        
        try:
            # 先检查数据库中是否有当年数据
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT COUNT(*) FROM solar_terms_cache WHERE pub_year = ?',
                    (query_year,)
                )
                count = cursor.fetchone()[0]
                
                # 如果没有当年数据，从API获取
                if count == 0:
                    result = self.query(year=query_year)
                    if result.get('error_code') != 0:
                        return {
                            'error': '获取节气数据失败',
                            'error_code': result.get('error_code'),
                            'reason': result.get('reason')
                        }
                
                # 获取所有节气数据并按日期排序
                cursor.execute('''
                    SELECT pub_date, name, raw_data 
                    FROM solar_terms_cache 
                    WHERE pub_year = ? 
                    ORDER BY pub_date
                ''', (query_year,))
                
                solar_terms = cursor.fetchall()
                
                # 找到当前节气和下一个节气
                current_term = None
                next_term = None
                
                for i, term in enumerate(solar_terms):
                    term_date = datetime.strptime(term[0], '%Y-%m-%d').date()
                    
                    if term_date <= query_date_obj:
                        raw_data = json.loads(term[2])
                        # 转换日期格式为显示格式
                        raw_data['pub_date'] = self.format_date_for_display(raw_data['pub_date'])
                        current_term = raw_data
                        # 如果不是最后一个节气，获取下一个
                        if i < len(solar_terms) - 1:
                            next_raw_data = json.loads(solar_terms[i + 1][2])
                            next_raw_data['pub_date'] = self.format_date_for_display(next_raw_data['pub_date'])
                            next_term = next_raw_data
                    else:
                        if not current_term:  # 如果还没有找到当前节气
                            if i > 0:  # 如果不是第一个节气
                                raw_data = json.loads(solar_terms[i - 1][2])
                                raw_data['pub_date'] = self.format_date_for_display(raw_data['pub_date'])
                                current_term = raw_data
                            next_raw_data = json.loads(term[2])
                            next_raw_data['pub_date'] = self.format_date_for_display(next_raw_data['pub_date'])
                            next_term = next_raw_data
                        break
                
                # 计算距离下一个节气的天数（使用标准格式的日期）
                days_to_next = None
                if next_term:
                    next_date = datetime.strptime(
                        self.convert_date_format(next_term['pub_date'], query_year), 
                        '%Y-%m-%d'
                    ).date()
                    days_to_next = (next_date - query_date_obj).days
                
                return {
                    'error_code': 0,
                    'query_date': query_date,
                    'current_term': current_term,
                    'next_term': next_term,
                    'days_to_next': days_to_next
                }
                
        except Exception as e:
            logging.error(f"获取当前节气信息失败: {str(e)}")
            return {'error': '获取节气信息失败', 'error_code': -1}

    def save_seasonal_food(self, foods: List[Dict], province: str):
        """保存时令食材数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for food in foods:
                    fields = {
                        'term': food.get('term'),
                        'product_type': food.get('product_type'),
                        'product_area': food.get('product_area'),
                        'vegatables': food.get('vegatables'),
                        'nutrition': food.get('nutrition'),
                        'cooding_tips': food.get('cooding_tips'),
                        'storage_advice': food.get('storage_advice'),
                        'food_advice': food.get('food_advice'),
                        'province': province
                    }
                    
                    columns = ', '.join(fields.keys())
                    placeholders = ', '.join(['?' for _ in fields])
                    sql = f'''
                        INSERT OR REPLACE INTO seasonal_food_cache 
                        ({columns}, created_at)
                        VALUES ({placeholders}, CURRENT_TIMESTAMP)
                    '''
                    
                    cursor.execute(sql, list(fields.values()))
                conn.commit()
        except Exception as e:
            logging.error(f"保存时令食材数据失败: {str(e)}")
            raise e

    def get_seasonal_food(self, term: Optional[str] = None, province: str = "山东") -> List[Dict]:
        """
        获取时令食材数据
        
        Args:
            term: 节气名称，如果不传则获取当前节气
            province: 省份名称，默认山东
            
        Returns:
            List[Dict]: 时令食材数据列表
        """
        try:
            # 如果没有传入节气，获取当前节气
            if term is None:
                current_result = self.get_current_solar_term()
                if current_result.get('error_code') != 0 or not current_result.get('current_term'):
                    logging.error("获取当前节气失败")
                    return []
                term = current_result['current_term']['name']
            
            logging.info(f"查询时令食材数据: term={term}, province={province}")
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT term, product_type, product_area, vegatables, 
                           nutrition, cooding_tips, storage_advice, food_advice
                    FROM seasonal_food_cache 
                    WHERE term = ? AND province = ?
                    ORDER BY created_at DESC
                ''', (term, province))
                
                results = cursor.fetchall()
                logging.info(f"查询结果数量: {len(results)}")
                if results:
                    return [{
                        'term': row[0],
                        'product_type': row[1],
                        'product_area': row[2],
                        'vegatables': row[3],
                        'nutrition': row[4],
                        'cooding_tips': row[5],
                        'storage_advice': row[6],
                        'food_advice': row[7]
                    } for row in results]
                return []
        except Exception as e:
            logging.error(f"获取时令食材数据失败: {str(e)}")
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

    def get_all_almanac_dates(self, start_date: Optional[str] = None) -> List[str]:
        """获取所有老黄历日期"""
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

def test_query():
    """测试查询功能"""
    from config import config
    
    # 初始化查询类
    solar = SolarTermsQuery(config.SOLAR_TERMS_API_KEY)
    
    # 测试查询2024年所有节气
    result = solar.query(year="2025")
    print("\n查询2024年所有节气:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 测试查询2024年惊蛰
    result = solar.query(year="2025", name="惊蛰")
    print("\n查询2024年惊蛰:")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 测试获取当前节气
    result = solar.get_current_solar_term("2025-02-05")
    print("\n查询2025-02-05的节气信息:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 测试获取今天的节气
    result = solar.get_current_solar_term()
    print("\n查询今天的节气信息:")
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    test_query() 