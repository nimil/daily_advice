import os
from typing import Optional, List
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

class Config:
    """应用配置类"""
    
    # Flask配置
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'
    
    # 企业微信配置
    CORP_ID = os.getenv('CORP_ID', '')
    CORP_SECRET = os.getenv('CORP_SECRET', '')
    OPEN_KFID = os.getenv('OPEN_KFID', '')
    EXTERNAL_USERID = os.getenv('EXTERNAL_USERID', '')
    
    # API密钥配置
    SOLAR_TERMS_API_KEY = os.getenv('SOLAR_TERMS_API_KEY', '')
    ALMANAC_API_KEY = os.getenv('ALMANAC_API_KEY', '')
    GLM4_API_KEY = os.getenv('GLM4_API_KEY', '')
    LIFE_SUGGESTION_API_KEY = os.getenv('LIFE_SUGGESTION_API_KEY', '')
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
    HOLIDAY_API_KEY = os.getenv('HOLIDAY_API_KEY', '')
    
    # 飞书机器人配置
    FEISHU_APP_ID = os.getenv('FEISHU_APP_ID', '')
    FEISHU_APP_SECRET = os.getenv('FEISHU_APP_SECRET', '')
    FEISHU_CHAT_ID_COIN = os.getenv('FEISHU_CHAT_ID_COIN', '')
    
    # 数据库路径
    SOLAR_TERMS_DB_PATH = os.getenv('SOLAR_TERMS_DB_PATH', 'data/solar_terms.db')
    ALMANAC_DB_PATH = os.getenv('ALMANAC_DB_PATH', 'data/almanac.db')
    HOLIDAY_DB_PATH = os.getenv('HOLIDAY_DB_PATH', 'data/holiday.db')
    
    # 服务器配置
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8090))
    THREADS = int(os.getenv('THREADS', 4))
    
    @classmethod
    def validate_required_keys(cls) -> List[str]:
        """验证必需的配置项"""
        required_keys = [
            'CORP_ID', 'CORP_SECRET', 'OPEN_KFID', 'EXTERNAL_USERID',
            'SOLAR_TERMS_API_KEY', 'ALMANAC_API_KEY', 'GLM4_API_KEY',
            'LIFE_SUGGESTION_API_KEY', 'DEEPSEEK_API_KEY', 'HOLIDAY_API_KEY',
            'FEISHU_APP_ID', 'FEISHU_APP_SECRET', 'FEISHU_CHAT_ID_COIN'
        ]
        
        missing_keys = []
        for key in required_keys:
            if not getattr(cls, key):
                missing_keys.append(key)
        
        return missing_keys

# 创建配置实例
config = Config()
