from flask import make_response, request, jsonify
import json
from scheduler import init_scheduler
import logging
import pytz
from datetime import datetime
from app_context import app  # 导入应用实例

# 注册蓝图
from solar_terms_api import solar_terms_bp
from news_integration_api import news_integration_bp

app.register_blueprint(solar_terms_bp)
app.register_blueprint(news_integration_bp)

class CustomJSONEncoder(json.JSONEncoder):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    def default(self, obj):
        try:
            return str(obj)
        except TypeError:
            return str(obj)
            
    def encode(self, obj):
        # 确保中文不被转义
        return json.dumps(obj, ensure_ascii=False, indent=2)

class ChinaTimeFormatter(logging.Formatter):
    """自定义日志格式化器，使用中国时区"""
    
    def converter(self, timestamp):
        dt = datetime.fromtimestamp(timestamp)
        china_tz = pytz.timezone('Asia/Shanghai')
        return dt.astimezone(china_tz)
        
    def formatTime(self, record, datefmt=None):
        dt = self.converter(record.created)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime('%Y-%m-%d %H:%M:%S')

# 配置自定义JSON编码器
app.json_encoder = CustomJSONEncoder

# 配置 JSON 编码
app.config.update(
    JSON_AS_ASCII=False,
    JSONIFY_PRETTYPRINT_REGULAR=True,
    JSONIFY_MIMETYPE='application/json; charset=utf-8'
)

# 配置日志
if not app.debug:    # 创建一个按日期滚动的文件处理器，用于记录访问日志
    from logging.handlers import TimedRotatingFileHandler
    file_handler = TimedRotatingFileHandler(
        'logs/access.log', 
        when='midnight',  # 每天午夜滚动
        interval=1,       # 间隔1天
        backupCount=30,   # 保留30天的日志
        encoding='utf-8'  # 确保中文正确显示
    )
    file_handler.setFormatter(ChinaTimeFormatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
 
    # 创建一个控制台处理器，用于在控制台显示日志
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ChinaTimeFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    console_handler.setLevel(logging.INFO)
    app.logger.addHandler(console_handler)
 
    app.logger.setLevel(logging.INFO)
    app.logger.info('Application startup')

# 添加全局响应处理
@app.after_request
def after_request(response):
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    # 记录每个请求的信息
    app.logger.info(f"Request: {request.method} {request.url} - Response: {response.status}")
    return response

# 初始化汇率API
from config import config
if config.init_currency_api():
    app.logger.info("✅ 汇率API初始化成功")
else:
    app.logger.warning("⚠️ 汇率API初始化失败（缺少GOLD_API_KEY）")

# 初始化定时任务
init_scheduler(app)

# 测试越南指数API接口
@app.route('/api/test/vietnam-index', methods=['GET'])
def test_vietnam_index():
    """测试越南胡志明指数API"""
    use_mock = request.args.get('mock', 'false').lower() == 'true'

    try:
        from vietnam_index_api import vietnam_index_api
        if use_mock:
            result = vietnam_index_api.get_vnindex_data_mock()
        else:
            result = vietnam_index_api.get_vnindex_data()
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"测试越南指数API异常: {str(e)}")
        return jsonify({
            'error_code': 1,
            'message': f'测试异常: {str(e)}',
            'data': {}
        })


# 仅测试越南指数格式化接口
@app.route('/api/test/vietnam-only', methods=['GET'])
def test_vietnam_only():
    """仅测试越南指数在消息中的显示"""
    try:
        from stock_market_flow import stock_market_flow
        from vietnam_index_api import vietnam_index_api

        # 模拟基础资金流向数据
        mock_flow_data = {
            'error_code': 0,
            'data': {
                'date': '2026-01-14',
                'shanghai': {
                    'close': 3200.50,
                    'change': 15.30
                },
                'fund_flow': {
                    'main': {'net_inflow': 5000000000, 'net_ratio': 2.5},
                    'super_large': {'net_inflow': 3000000000, 'net_ratio': 1.5},
                    'large': {'net_inflow': 2000000000, 'net_ratio': 1.0},
                    'medium': {'net_inflow': -500000000, 'net_ratio': -0.25},
                    'small': {'net_inflow': -1000000000, 'net_ratio': -0.5}
                }
            }
        }

        # 获取越南指数数据（真实API）
        vietnam_result = vietnam_index_api.get_vnindex_data()

        # 格式化消息（不包含汇率和黄金，仅越南指数）
        formatted_result = stock_market_flow.format_fund_flow_message(
            mock_flow_data,
            None,  # 不包含汇率和黄金
            vietnam_result
        )

        return jsonify(formatted_result)

    except Exception as e:
        app.logger.error(f"测试越南指数仅显示异常: {str(e)}")
        return jsonify({
            'error_code': 1,
            'message': f'测试异常: {str(e)}',
            'data': {}
        })

# 专门测试越南指数发送功能的接口
@app.route('/api/test/vietnam-market-send', methods=['GET'])
def test_vietnam_market_send():
    """专门测试越南指数市场消息发送功能（使用真实越南指数数据）"""
    try:
        from stock_market_flow import stock_market_flow
        from vietnam_index_api import vietnam_index_api

        # 创建模拟的完整市场数据（包含资金流向）
        mock_flow_data = {
            'error_code': 0,
            'data': {
                'date': '2026-01-14',
                'shanghai': {
                    'close': 3200.50,
                    'change': 15.30
                },
                'fund_flow': {
                    'main': {'net_inflow': 5000000000, 'net_ratio': 2.5},
                    'super_large': {'net_inflow': 3000000000, 'net_ratio': 1.5},
                    'large': {'net_inflow': 2000000000, 'net_ratio': 1.0},
                    'medium': {'net_inflow': -500000000, 'net_ratio': -0.25},
                    'small': {'net_inflow': -1000000000, 'net_ratio': -0.5}
                }
            }
        }

        # 获取越南指数数据（真实API）
        vietnam_result = vietnam_index_api.get_vnindex_data()

        # 格式化消息（仅包含资金流向和越南指数）
        formatted_result = stock_market_flow.format_fund_flow_message(
            mock_flow_data,
            None,  # 不包含汇率和黄金
            vietnam_result
        )

        if formatted_result['error_code'] == 0:
            # 返回格式化的消息内容，模拟飞书发送的消息格式
            message_content = formatted_result['data']['content']

            return jsonify({
                'error_code': 0,
                'message': '越南指数市场消息格式化成功',
                'data': {
                    'content': message_content,
                    'preview': message_content,
                    'description': '此消息将包含越南胡志明指数数据，每天下午3:10自动发送到飞书群组'
                }
            })
        else:
            return jsonify({
                'error_code': 1,
                'message': '消息格式化失败',
                'data': {}
            })

    except Exception as e:
        app.logger.error(f"测试越南指数发送功能异常: {str(e)}")
        return jsonify({
            'error_code': 1,
            'message': f'测试异常: {str(e)}',
            'data': {}
        })

# 启动Flask应用
if __name__ == '__main__':
    app.logger.info('Starting Flask application...')
    from waitress import serve
    serve(app, host='0.0.0.0', port=8090, threads=4)