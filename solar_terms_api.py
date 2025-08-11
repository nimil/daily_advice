import logging
from flask import Blueprint, request, jsonify, current_app, make_response
import os
from solar_terms_query import SolarTermsQuery
from almanac_query import AlmanacQuery
from glm4_query import GLM4Query
from datetime import datetime
import pytz
import json
from life_suggestion_query import LifeSuggestionQuery
from dateutil.relativedelta import relativedelta
from deepseek_query import DeepseekR1Query
import threading
from queue import Queue
import time

# 创建蓝图
solar_terms_bp = Blueprint('solar_terms', __name__, url_prefix='/api')

from config import config

# 初始化查询类
solar_terms = SolarTermsQuery(config.SOLAR_TERMS_API_KEY)
almanac = AlmanacQuery(config.ALMANAC_API_KEY)
glm4 = GLM4Query(config.GLM4_API_KEY)

# 修改缓存数据结构，增加daily_advice的缓存
cache = {
    'solar_terms': {
        'date': None,
        'data': None
    },
    'daily_advice': {
        'date': None,
        'data': None
    }
}

# 创建一个队列来存储待处理的日期
date_queue = Queue()

def get_current_date():
    """获取当前日期"""
    return datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d')

def get_cached_solar_terms(query_date: str):
    """获取缓存的节气数据"""
    if cache['solar_terms']['date'] == query_date and cache['solar_terms']['data']:
        current_app.logger.info("从缓存获取节气数据")
        return cache['solar_terms']['data']
    
    # 查询新数据并更新缓存
    current_app.logger.info("从API获取节气数据")
    result = solar_terms.get_current_solar_term(query_date)
    if result.get('error_code') == 0:
        cache['solar_terms']['date'] = query_date
        cache['solar_terms']['data'] = result
        return result
        
    return None

def get_cached_daily_advice(query_date: str):
    """
    获取缓存的每日建议数据
    
    Args:
        query_date: 查询日期
        
    Returns:
        Dict: 缓存的每日建议数据或None
    """
    if cache['daily_advice']['date'] == query_date and cache['daily_advice']['data']:
        return cache['daily_advice']['data']
    
    # 查询新数据并更新缓存
    current_app.logger.info("从API获取每日建议数据")
    result = glm4.get_daily_advice()
    if result.get('error_code') == 0:
        cache['daily_advice']['date'] = query_date
        cache['daily_advice']['data'] = result
        return result
        
    return None


@solar_terms_bp.route('/daily_advice', methods=['GET'])
def get_daily_advice():
    """
    获取每日建议，包含节气养生和老黄历信息
    
    Returns:
        JSON格式的建议信息
    """
    try:
        # 获取当前日期
        query_date = get_current_date()
        
        # 从缓存获取数据
        result = get_cached_daily_advice(query_date)
        
        if result and result.get('error_code') == 0:
            response_data = {
                'code': 0,
                'message': 'success',
                'data': result['data']
            }
        else:
            response_data = {
                'code': result.get('error_code', -1) if result else -1,
                'message': result.get('message', '获取建议失败') if result else '未找到建议信息',
                'data': None
            }
            
        # 使用 json.dumps 确保中文正确编码
        json_str = json.dumps(response_data, ensure_ascii=False, indent=2)
        response = make_response(json_str)
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response
        
    except Exception as e:
        current_app.logger.error(f"获取每日建议失败: {str(e)}")
        error_response = make_response(json.dumps({
            'code': -1,
            'message': '服务器内部错误',
            'data': None
        }, ensure_ascii=False, indent=2))
        error_response.headers['Content-Type'] = 'application/json; charset=utf-8'
        error_response.status_code = 500
        return error_response 

@solar_terms_bp.route('/daily_advice_html', methods=['GET'])
def get_daily_advice_html():
    """
    获取每日建议的HTML格式，适合邮件查看
    
    Returns:
        HTML格式的建议信息，包含小程序二维码广告
    """
    try:
        # 获取当前日期
        query_date = get_current_date()
        
        # 从缓存获取数据
        result = get_cached_daily_advice(query_date)
        
        if result and result.get('error_code') == 0:
            data = result['data']
            
            # 生成HTML内容
            html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>每日建议 - {data.get('date', '')}</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', 'PingFang SC', 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: #ffffff;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 20px;
            margin-bottom: 25px;
        }}
        .date {{
            font-size: 24px;
            font-weight: bold;
            color: #2E7D32;
            margin-bottom: 10px;
        }}
        .nongli {{
            font-size: 16px;
            color: #666;
            margin-bottom: 15px;
        }}
        .section {{
            margin-bottom: 25px;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 8px;
            border-left: 4px solid #4CAF50;
        }}
        .section-title {{
            font-size: 18px;
            font-weight: bold;
            color: #2E7D32;
            margin-bottom: 10px;
        }}
        .content {{
            font-size: 14px;
            line-height: 1.8;
            color: #555;
        }}
        .yi-ji {{
            display: flex;
            gap: 20px;
        }}
        .yi, .ji {{
            flex: 1;
            padding: 15px;
            border-radius: 8px;
        }}
        .yi {{
            background-color: #E8F5E8;
            border-left: 4px solid #4CAF50;
        }}
        .ji {{
            background-color: #FFEBEE;
            border-left: 4px solid #F44336;
        }}
        .yi-title, .ji-title {{
            font-weight: bold;
            margin-bottom: 8px;
        }}
        .yi-title {{
            color: #2E7D32;
        }}
        .ji-title {{
            color: #C62828;
        }}
        .ad-section {{
            margin-top: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            text-align: center;
            color: white;
        }}
        .ad-title {{
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 15px;
        }}
        .ad-desc {{
            font-size: 14px;
            line-height: 1.6;
            margin-bottom: 20px;
        }}
        .qr-code {{
            width: 120px;
            height: 120px;
            margin: 0 auto;
            border-radius: 8px;
            overflow: hidden;
        }}
        .qr-code img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        .footer {{
            margin-top: 30px;
            text-align: center;
            font-size: 12px;
            color: #999;
            border-top: 1px solid #eee;
            padding-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="date">{data.get('date', '')}</div>
            <div class="nongli">{data.get('nongli', '')}</div>
        </div>
        
        <div class="section">
            <div class="section-title">🍽️ 今日饮食建议</div>
            <div class="content">{data.get('food', '')}</div>
        </div>
        
        <div class="yi-ji">
            <div class="yi">
                <div class="yi-title">✅ 今日宜</div>
                <div class="content">{data.get('yi', '')}</div>
            </div>
            <div class="ji">
                <div class="ji-title">❌ 今日忌</div>
                <div class="content">{data.get('ji', '')}</div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">📝 今日详情</div>
            <div class="content">{data.get('desc', '')}</div>
        </div>
        
        <div class="ad-section">
            <div class="ad-title">🌟 扫码体验更多功能</div>
            <div class="ad-desc">
                想要获取更多个性化建议和实时天气信息吗？<br>
                扫描下方二维码，下载我们的微信小程序，享受更丰富的功能体验！
            </div>
            <div class="qr-code">
                <img src="https://api.aminbk.top/wxgramcode.jpg" alt="小程序二维码">
            </div>
        </div>
        
        <div class="footer">
            <p>本建议基于传统节气养生知识和老黄历信息生成</p>
            <p>© 2025 时令智能老黄历微信小程序 - 让生活更有智慧</p>
        </div>
    </div>
    
    <script>
        // 分享到微信
        function shareToWeChat() {{
            if (navigator.share) {{
                navigator.share({{
                    title: '每日建议 - 让生活更有智慧',
                    text: '获取今日养生建议、老黄历宜忌、天气信息等',
                    url: window.location.href
                }});
            }} else {{
                // 复制链接到剪贴板
                copyLink();
                alert('链接已复制到剪贴板，请手动分享到微信');
            }}
        }}
        
        // 复制链接
        function copyLink() {{
            const url = window.location.href;
            if (navigator.clipboard) {{
                navigator.clipboard.writeText(url).then(() => {{
                    showToast('链接已复制到剪贴板');
                }});
            }} else {{
                // 兼容旧浏览器
                const textArea = document.createElement('textarea');
                textArea.value = url;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                showToast('链接已复制到剪贴板');
            }}
        }}
        
        // 显示提示信息
        function showToast(message) {{
            const toast = document.createElement('div');
            toast.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: rgba(0,0,0,0.8);
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                z-index: 1000;
                font-size: 14px;
            `;
            toast.textContent = message;
            document.body.appendChild(toast);
            
            setTimeout(() => {{
                document.body.removeChild(toast);
            }}, 2000);
        }}
        
        // 二维码点击放大
        document.addEventListener('DOMContentLoaded', function() {{
            const qrCode = document.querySelector('.qr-code img');
            if (qrCode) {{
                qrCode.addEventListener('click', function() {{
                    const modal = document.createElement('div');
                    modal.style.cssText = `
                        position: fixed;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        background: rgba(0,0,0,0.8);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        z-index: 1000;
                        cursor: pointer;
                    `;
                    
                    const img = document.createElement('img');
                    img.src = this.src;
                    img.style.cssText = `
                        max-width: 80%;
                        max-height: 80%;
                        border-radius: 10px;
                        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                    `;
                    
                    modal.appendChild(img);
                    document.body.appendChild(modal);
                    
                    modal.addEventListener('click', function() {{
                        document.body.removeChild(modal);
                    }});
                }});
            }}
        }});
    </script>
</body>
</html>
            """
            
            # 返回HTML响应
            response = make_response(html_content)
            response.headers['Content-Type'] = 'text/html; charset=utf-8'
            return response
            
        else:
            error_html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>获取建议失败</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', sans-serif;
            text-align: center;
            padding: 50px;
            color: #666;
        }}
        .error {{
            color: #f44336;
            font-size: 18px;
        }}
    </style>
</head>
<body>
    <div class="error">
        <h2>获取建议失败</h2>
        <p>{result.get('message', '未知错误') if result else '未找到建议信息'}</p>
    </div>
</body>
</html>
            """
            response = make_response(error_html)
            response.headers['Content-Type'] = 'text/html; charset=utf-8'
            response.status_code = 500
            return response
        
    except Exception as e:
        current_app.logger.error(f"获取每日建议HTML失败: {str(e)}")
        error_html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>服务器错误</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', sans-serif;
            text-align: center;
            padding: 50px;
            color: #666;
        }}
        .error {{
            color: #f44336;
            font-size: 18px;
        }}
    </style>
</head>
<body>
    <div class="error">
        <h2>服务器内部错误</h2>
        <p>抱歉，服务器暂时无法处理您的请求</p>
    </div>
</body>
</html>
        """
        response = make_response(error_html)
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        response.status_code = 500
        return response

@solar_terms_bp.route('/weather', methods=['GET'])
def get_weather():
    """
    获取当前天气信息
    
    Returns:
        JSON格式的天气信息，包含天气描述和温度
    """
    try:
        # 初始化查询类
        life_suggestion = LifeSuggestionQuery(config.LIFE_SUGGESTION_API_KEY)
        
        # 获取天气信息
        weather = life_suggestion.query_weather()
        
        if 'results' in weather and weather['results']:
            now = weather['results'][0].get('now', {})
            response_data = {
                'code': 0,
                'message': 'success',
                'data': {
                    'text': now.get('text', ''),
                    'temperature': now.get('temperature', '')
                }
            }
        else:
            response_data = {
                'code': -1,
                'message': '获取天气信息失败',
                'data': None
            }
            
        return jsonify(response_data)
        
    except Exception as e:
        current_app.logger.error(f"获取天气信息失败: {str(e)}")
        return jsonify({
            'code': -1,
            'message': '服务器内部错误',
            'data': None
        }), 500 

@solar_terms_bp.route('/sync_almanac', methods=['POST'])
def sync_almanac():
    """
    手动同步未来N天的老黄历数据
    
    Request parameters:
        days: int, optional, the number of days to sync, default 7 days
    """
    try:
        # 获取请求参数
        data = request.get_json() or {}
        days = int(data.get('days', 7))  # default 7 days
        
        # 验证参数
        if days <= 0:
            return jsonify({
                'code': -1,
                'message': '天数必须大于0',
                'data': None
            }), 400
        
        # 初始化查询类
        almanac = AlmanacQuery(config.ALMANAC_API_KEY)
        
        # 查询未来N天的数据
        results = almanac.query_next_n_days(days)
        
        if results:
            return jsonify({
                'code': 0,
                'message': f'成功同步未来 {days} 天的数据',
                'data': results
            })
        else:
            return jsonify({
                'code': -1,
                'message': '同步数据失败',
                'data': None
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"同步老黄历数据失败: {str(e)}")
        return jsonify({
            'code': -1,
            'message': f'同步数据出错: {str(e)}',
            'data': None
        }), 500 

@solar_terms_bp.route('/almanac', methods=['GET'])
def get_almanac():
    """
    获取指定月份的老黄历数据
    
    请求参数：
         date: str, 查询日期，格式：YYYY-MM-DD，默认当天
     
    返回：
         该月所有老黄历数据
    """
    try:
        # 获取请求参数
        query_date = request.args.get('date')
        if not query_date:
            query_date = datetime.now().strftime('%Y-%m-%d')
            
        # 解析日期
        date_obj = datetime.strptime(query_date, '%Y-%m-%d')
        
        # 计算月初和月末
        start_date = date_obj.replace(day=1)
        end_date = (start_date + relativedelta(months=1)) - relativedelta(days=1)
        
        # 初始化查询类
        almanac = AlmanacQuery(config.ALMANAC_API_KEY)
        
        # 从数据库查询该月数据
        with almanac.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT date, raw_data 
                FROM almanac_cache 
                WHERE date BETWEEN ? AND ?
                ORDER BY date
            ''', (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
            
            results = cursor.fetchall()
            
            # 转换查询结果
            almanac_data = []
            for row in results:
                date, raw_data = row
                data = json.loads(raw_data)
                almanac_data.append({
                    'date': date,
                    'data': data.get('result', {})
                })
            
            return jsonify({
                'code': 0,
                'message': 'success',
                'data': {
                    'year': date_obj.year,
                    'month': date_obj.month,
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'almanac_list': almanac_data
                }
            })
            
    except ValueError:
        return jsonify({
            'code': -1,
            'message': '日期格式错误，请使用YYYY-MM-DD格式',
            'data': None
        }), 400
    except Exception as e:
        current_app.logger.error(f"获取老黄历数据失败: {str(e)}")
        return jsonify({
            'code': -1,
            'message': f'获取数据失败: {str(e)}',
            'data': None
        }), 500 

@solar_terms_bp.route('/food_advice', methods=['GET'])
def get_food_advice():
    """获取时令饮食建议"""
    try:
        # 获取请求参数
        province = request.args.get('province', '山东')  # 默认山东
        term = request.args.get('term')  # 如果不传，则使用当前节气
        
        # 先从缓存获取数据
        cached_data = solar_terms.get_seasonal_food(term, province)
        logging.info(f"缓存数据: {cached_data}")
        if cached_data:
            return jsonify({
                'code': 0,
                'message': 'success (from cache)',
                'data': cached_data
            })
        
        # 如果没有传入节气，获取当前节气用于提示语
        if term is None:
            solar_result = solar_terms.get_current_solar_term()
            if solar_result.get('error_code') != 0 or not solar_result.get('current_term'):
                return jsonify({
                    'code': -1,
                    'message': '获取节气信息失败',
                    'data': None
                }), 500
            term = solar_result['current_term']['name']
        
        logging.info(f"使用节气: {term}")
        
        # 初始化 DeepseekR1 查询类
        deepseek = DeepseekR1Query(config.DEEPSEEK_API_KEY)
        
        # 构造提示语
        prompt = f"""
        请根据{province}地区的{term}节气，为我推荐应季蔬菜的饮食建议，要求：
        1. 考虑当前节气特点
        2. 注重{province}地区的本地特色
        3. 包含具体的营养和烹饪建议
        我现在是某APP的后端开发,需要读取结构化的数据，不需要考虑可读写,不需要markdown标记
        请严格按照以下JSON格式返回：
        [
            {{
                "term": "{term}",  // 固定为指定节气
                "product_type": "栽种方式(露天，大棚)",
                "product_area": "{province}具体产地",
                "vegatables": "蔬菜名称",
                "nutrition": "营养含量",
                "cooding_tips": "烹饪方法推荐",
                "storage_advice": "储存建议",
                "food_advice": "本种蔬菜的饮食建议"
            }}
        ]
        """
        
        logging.info(f"发送到AI的提示语: {prompt}")
        # 调用 AI 获取建议
        result = deepseek.chat(prompt)
        logging.info(f"AI返回结果: {result}")
        
        try:
            # 处理 markdown 格式
            if '```json' in result and '```' in result:
                # 找到第一个 ```json 和最后一个 ``` 之间的内容
                start = result.find('```json') + 7
                end = result.rfind('```')
                json_str = result[start:end].strip()
            else:
                json_str = result
            
            logging.info(f"解析后的JSON字符串: {json_str}")
            # 解析返回的JSON字符串
            food_data = json.loads(json_str)
            
            # 验证返回数据的节气是否正确
            for item in food_data:
                if item.get('term') != term:
                    raise ValueError(f"AI返回的节气({item.get('term')})与当前节气({term})不匹配")
            
            # 保存到缓存
            solar_terms.save_seasonal_food(food_data, province)
            
            return jsonify({
                'code': 0,
                'message': 'success',
                'data': food_data
            })
        except json.JSONDecodeError as e:
            logging.error(f"JSON解析失败: {str(e)}\n原始数据: {result}")
            return jsonify({
                'code': -1,
                'message': f'AI返回数据格式错误: {str(e)}',
                'data': result
            }), 500
        except ValueError as e:
            logging.error(f"数据验证失败: {str(e)}")
            return jsonify({
                'code': -1,
                'message': str(e),
                'data': None
            }), 500
        
    except Exception as e:
        current_app.logger.error(f"获取饮食建议失败: {str(e)}")
        return jsonify({
            'code': -1,
            'message': f'获取饮食建议失败: {str(e)}',
            'data': None
        }), 500 

@solar_terms_bp.route('/almanac_explanation', methods=['GET'])
def get_almanac_explanation():
    """获取老黄历解释"""
    try:
        # 获取请求参数
        date = request.args.get('date')
        if not date:
            return jsonify({
                'code': -1,
                'message': '日期参数不能为空',
                'data': None
            }), 400
            
        # 从老黄历表获取数据
        almanac_data = almanac.query_almanac(date)
        if not almanac_data or almanac_data.get('error_code') != 0:
            return jsonify({
                'code': -1,
                'message': '获取老黄历数据失败',
                'data': None
            }), 500
            
        # 需要解释的字段
        fields = ['wuxing', 'chongsha', 'baiji', 'jishen', 'yi', 'xiongshen', 'ji']
        
        # 构建字段值字典
        field_values = {
            field: almanac_data.get('result', {}).get(field)
            for field in fields
        }
        
        # 获取已有的解释
        cached_explanations = almanac.get_almanac_explanation(field_values)
        
        # 初始化 GLM4 查询类
        glm = GLM4Query(config.GLM4_API_KEY)
        
        result = {}
        # 处理每个字段
        for field, field_value in field_values.items():
            if not field_value:
                continue
                
            # 分词处理
            values = field_value.split()
            result[field] = []
            
            for value in values:
                # 检查是否已有解释
                cached_explanation = next(
                    (item['explanation'] for item in cached_explanations.get(field, [])
                     if item['value'] == value and item['explanation']),
                    None
                )
                
                if cached_explanation:
                    explanation = cached_explanation
                else:
                    # 构造提示语
                    prompt = f"""
                    请解释老黄历中的这个概念：{value}
                    这个概念出现在{field}字段中。
                    请用通俗易懂的语言解释其含义和作用。
                    直接返回解释文本，不需要任何多余的格式。
                    """
                    
                    # 调用 AI 获取解释
                    explanation = glm.chat(prompt)
                    
                    # 保存到缓存
                    almanac.save_almanac_explanation(field, value, explanation)
                
                # 添加到结果
                result[field].append({
                    'value': value,
                    'explanation': explanation
                })
                
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': result
        })
        
    except Exception as e:
        current_app.logger.error(f"获取老黄历解释失败: {str(e)}")
        return jsonify({
            'code': -1,
            'message': f'获取老黄历解释失败: {str(e)}',
            'data': None
        }), 500 

@solar_terms_bp.route('/almanac_explanation_batch', methods=['GET'])
def batch_almanac_explanation():
    """批量处理老黄历解释"""
    try:
        # 获取请求参数
        start_date = request.args.get('start_date')
        
        # 初始化 GLM4 查询类
        glm = GLM4Query(config.GLM4_API_KEY)
        
        # 调用 almanac 类的批量处理方法
        result = almanac.start_batch_explanation(start_date, glm)
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"批量处理老黄历解释失败: {str(e)}")
        return jsonify({
            'code': -1,
            'message': f'批量处理老黄历解释失败: {str(e)}',
            'data': None
        }), 500 