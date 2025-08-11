from flask import make_response, request
import json
from scheduler import init_scheduler
import logging
from logging.handlers import RotatingFileHandler
import pytz
from datetime import datetime
from app_context import app  # 导入应用实例

# 注册蓝图
from solar_terms_api import solar_terms_bp
app.register_blueprint(solar_terms_bp)

class CustomJSONEncoder:
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
if not app.debug:
    # 创建一个文件处理器，用于记录访问日志
    file_handler = RotatingFileHandler('logs/access.log', maxBytes=10240, backupCount=10)
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

# 初始化定时任务
init_scheduler(app)

# 启动Flask应用
if __name__ == '__main__':
    app.logger.info('Starting Flask application...')
    from waitress import serve
    serve(app, host='0.0.0.0', port=8090, threads=4)