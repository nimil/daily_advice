import requests
import json
import logging
from typing import Dict, Any, List
from flask import Blueprint, jsonify, current_app, render_template_string
from glm4_query import GLM4Query
from config import config
from datetime import datetime
import pytz
from feishu_bot import feishu_bot

# 创建蓝图
news_integration_bp = Blueprint('news_integration', __name__)

class NewsIntegrationAPI:
    """新闻整合API类"""
    
    def __init__(self):
        """初始化新闻整合API"""
        self.news_sources = {
            'jin10': 'https://newsnow.16781678.xyz/api/s?id=jin10&latest',
            'cls_telegraph': 'https://newsnow.16781678.xyz/api/s?id=cls-telegraph&latest',
            'wallstreetcn_hot': 'https://newsnow.16781678.xyz/api/s?id=wallstreetcn-hot&latest'
        }
        
        # 消息来源映射
        self.source_mapping = {
            'jin10': '金十数据',
            'cls_telegraph': '财联社',
            'wallstreetcn_hot': '华尔街见闻',
            'cls-telegraph': '财联社',
            'wallstreetcn-hot': '华尔街见闻'
        }
        
        self.glm4_client = GLM4Query(config.GLM4_API_KEY)
    
    def get_mapped_sources(self, sources: str) -> str:
        """
        获取映射后的多个消息来源名称
        
        Args:
            sources: 原始来源名称，可能包含多个来源（用逗号分隔）
            
        Returns:
            str: 映射后的来源名称
        """
        if not sources:
            return sources
        
        # 分割多个来源
        source_list = [s.strip() for s in sources.split(',')]
        
        # 映射每个来源
        mapped_sources = []
        for source in source_list:
            mapped_source = self.source_mapping.get(source, source)
            mapped_sources.append(mapped_source)
        
        # 返回映射后的来源，用逗号分隔
        return ', '.join(mapped_sources)
        
    def fetch_news_from_source(self, source_name: str, url: str) -> Dict[str, Any]:
        """
        从指定新闻源获取新闻数据
        
        Args:
            source_name: 新闻源名称
            url: API地址
            
        Returns:
            Dict: 新闻数据
        """
        try:
            logging.info(f"🔍 开始获取新闻源: {source_name}")
            logging.info(f"📡 请求URL: {url}")
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            logging.info(f"✅ {source_name} 请求成功，状态码: {response.status_code}")
            logging.info(f"📊 {source_name} 响应大小: {len(response.content)} bytes")
            
            data = response.json()
            
            logging.info(f"📋 {source_name} 原始响应数据结构: {list(data.keys()) if isinstance(data, dict) else '非字典类型'}")
            logging.info(f"📊 {source_name} API状态: {data.get('status', 'unknown')}")
            
            # 检查API状态 - 支持 'success' 和 'cache' 两种正常状态
            # 'cache' 状态表示从缓存返回数据，这是正常的，不是错误
            status = data.get('status')
            if status in ['success', 'cache']:
                items = data.get('items', [])
                logging.info(f"📰 {source_name} 获取到 {len(items)} 条新闻 (状态: {status})")
                
                # 打印前3条新闻的标题用于调试
                for i, item in enumerate(items[:3]):
                    logging.info(f"📄 {source_name} 新闻{i+1}: {item.get('title', '无标题')[:50]}...")
                
                return {
                    'error_code': 0,
                    'message': f'success (状态: {status})',
                    'source': source_name,
                    'data': items
                }
            else:
                logging.error(f"❌ {source_name} API返回错误状态: {status}")
                return {
                    'error_code': -1,
                    'message': f'API返回错误状态: {status}',
                    'source': source_name,
                    'data': []
                }
                
        except requests.RequestException as e:
            logging.error(f"❌ 请求{source_name}新闻源失败: {str(e)}")
            return {
                'error_code': -1,
                'message': f'请求失败: {str(e)}',
                'source': source_name,
                'data': []
            }
        except json.JSONDecodeError as e:
            logging.error(f"❌ 解析{source_name}新闻源JSON失败: {str(e)}")
            return {
                'error_code': -1,
                'message': f'JSON解析失败: {str(e)}',
                'source': source_name,
                'data': []
            }
    
    def fetch_all_news(self) -> Dict[str, Any]:
        """
        获取所有新闻源的数据
        
        Returns:
            Dict: 所有新闻源的数据
        """
        logging.info("🚀 开始获取所有新闻源数据")
        logging.info(f"📋 配置的新闻源: {list(self.news_sources.keys())}")
        
        all_news = {}
        total_news_count = 0
        
        for source_name, url in self.news_sources.items():
            try:
                logging.info(f"🔄 处理新闻源: {source_name}")
                result = self.fetch_news_from_source(source_name, url)
                all_news[source_name] = result
                
                if result['error_code'] == 0:
                    news_count = len(result.get('data', []))
                    total_news_count += news_count
                    current_app.logger.info(f"✅ 成功获取{source_name}新闻源数据，共{news_count}条新闻")
                else:
                    current_app.logger.error(f"❌ {source_name}新闻源获取失败: {result['message']}")
                    
            except Exception as e:
                current_app.logger.error(f"❌ 获取{source_name}新闻源数据异常: {str(e)}")
                all_news[source_name] = {
                    'error_code': -1,
                    'message': f'获取失败: {str(e)}',
                    'source': source_name,
                    'data': []
                }
        
        logging.info(f"📊 所有新闻源获取完成，总计: {total_news_count}条新闻")
        
        # 打印每个新闻源的详细统计
        for source_name, result in all_news.items():
            if result['error_code'] == 0:
                logging.info(f"📈 {source_name}: {len(result.get('data', []))}条新闻")
            else:
                logging.info(f"❌ {source_name}: 获取失败 - {result['message']}")
        
        return all_news
    
    def integrate_news_with_glm4(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用GLM4整合和去重新闻数据
        
        Args:
            news_data: 原始新闻数据
            
        Returns:
            Dict: 整合后的新闻数据
        """
        try:
            logging.info("🤖 开始使用GLM4整合新闻数据")
            
            # 准备新闻数据用于GLM4处理
            news_items = []
            
            logging.info("📋 开始处理各新闻源数据...")
            for source_name, source_data in news_data.items():
                logging.info(f"🔄 处理新闻源: {source_name}")
                
                if source_data.get('error_code') == 0:
                    items = source_data.get('data', [])
                    logging.info(f"📰 {source_name} 有 {len(items)} 条新闻需要处理")
                    
                    for i, item in enumerate(items):
                        # 统一新闻项格式
                        news_item = {
                            'source': source_name,
                            'title': item.get('title', ''),
                            'pubDate': item.get('pubDate', ''),
                            'url': item.get('url', ''),
                            'id': item.get('id', '')
                        }
                        news_items.append(news_item)
                        
                        # 打印前3条新闻的详细信息用于调试
                        if i < 3:
                            logging.info(f"📄 {source_name} 新闻{i+1}: 标题='{news_item['title'][:50]}...', 来源='{news_item['source']}', 时间='{news_item['pubDate']}'")
                else:
                    logging.warning(f"⚠️ {source_name} 新闻源数据无效: {source_data.get('message', '未知错误')}")
            
            logging.info(f"📊 总共收集到 {len(news_items)} 条新闻用于AI处理")
            
            if not news_items:
                logging.error("❌ 没有可用的新闻数据")
                return {
                    'error_code': -1,
                    'message': '没有可用的新闻数据',
                    'data': []
                }
            
            # 构建GLM4提示词
            current_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y年%m月%d日 %H:%M:%S')
            
            logging.info(f"⏰ 当前时间: {current_time}")
            logging.info(f"📝 准备构建GLM4提示词，新闻数据大小: {len(news_items)} 条")
            
            prompt = f"""
            请帮我整合和去重以下来自多个新闻源的新闻数据。当前时间：{current_time}
            
            原始新闻数据：
            {json.dumps(news_items, ensure_ascii=False, indent=2)}
            
           处理要求：
            1. 去除重复的新闻：根据新闻标题的相似性判断重复新闻，并去除重复内容。
            2. 按重要性排序：根据新闻的潜在影响、时效性以及与经济的关联度进行排序。重要新闻优先显示。
            3. 提取关键信息：生成简洁明了的摘要，突显新闻的核心内容，去除冗长和不必要的信息。
            4. 经济影响判断：从投资者的角度，分析新闻对市场的潜在影响。包括股市、行业发展、宏观经济等因素，判断新闻的利好或利空。
            
            请严格按照以下JSON格式返回结果：
            {{
                "summary": "今日新闻概览",
                "news_list": [
                    {{
                        "title": "新闻标题",
                        "summary": "新闻摘要",
                        "source": "新闻来源",
                        "pubDate": "发布时间",
                        "impact": "经济影响判断",
                        "url": "新闻链接"
                    }}
                ],
                "positive_count": "正向新闻数量",
                "negative_count": "负向新闻数量",
                "processed_time": "处理时间"
            }}
    
            """
            
            logging.info(f"📤 构建的提示词长度: {len(prompt)} 字符")
            
            # 打印发送给AI的prompt
            logging.info("=" * 80)
            logging.info("📤 发送给新闻AI的PROMPT:")
            logging.info("=" * 80)
            logging.info(prompt)
            logging.info("=" * 80)
            
            # 调用GLM4处理
            logging.info("🤖 开始调用GLM4处理新闻数据...")
            glm4_start_time = datetime.now()
            
            response = self.glm4_client.query([
                {"role": "system", "content": "你是一个专业的财经信息整合专家，擅长财经新闻整合、去重和分类。请严格按照要求的JSON格式返回结果。"},
                {"role": "user", "content": prompt}
            ])
            
            glm4_end_time = datetime.now()
            glm4_duration = (glm4_end_time - glm4_start_time).total_seconds()
            logging.info(f"⏱️ GLM4处理耗时: {glm4_duration:.2f}秒")
            
            # 打印AI的返回结果
            logging.info("=" * 80)
            logging.info("📥 新闻AI的返回结果:")
            logging.info("=" * 80)
            logging.info(f"响应状态: {response}")
            logging.info("=" * 80)
            
            if response['error_code'] == 0:
                content = response['data'].choices[0].message.content
                
                logging.info(f"📄 AI返回内容长度: {len(content)} 字符")
                
                # 打印AI返回的具体内容
                logging.info("=" * 80)
                logging.info("📄 AI返回的原始内容:")
                logging.info("=" * 80)
                logging.info(content)
                logging.info("=" * 80)
                
                try:
                    # 解析GLM4响应
                    logging.info("🔍 开始解析AI返回的JSON数据...")
                    integrated_data = json.loads(content)
                    
                    logging.info(f"✅ JSON解析成功，数据结构: {list(integrated_data.keys()) if isinstance(integrated_data, dict) else '非字典类型'}")
                    
                    # 检查关键字段
                    if 'news_list' in integrated_data:
                        news_list = integrated_data['news_list']
                        logging.info(f"📰 AI返回的新闻列表数量: {len(news_list)} 条")
                        
                        # 打印前3条新闻的标题用于验证
                        for i, news in enumerate(news_list[:3]):
                            logging.info(f"📄 AI返回新闻{i+1}: 标题='{news.get('title', '无标题')[:50]}...', 来源='{news.get('source', '无来源')}'")
                    
                    # 打印解析后的结构化数据
                    logging.info("=" * 80)
                    logging.info("✅ 解析后的结构化数据:")
                    logging.info("=" * 80)
                    logging.info(json.dumps(integrated_data, ensure_ascii=False, indent=2))
                    logging.info("=" * 80)
                    
                    return {
                        'error_code': 0,
                        'message': 'success',
                        'data': integrated_data,
                        'raw_data': news_data
                    }
                except json.JSONDecodeError as e:
                    logging.error("=" * 80)
                    logging.error("❌ JSON解析失败:")
                    logging.error("=" * 80)
                    logging.error(f"错误信息: {str(e)}")
                    logging.error(f"原始内容长度: {len(content)} 字符")
                    logging.error(f"原始内容前500字符: {content[:500]}")
                    logging.error(f"原始内容后500字符: {content[-500:]}")
                    logging.error("=" * 80)
                    return {
                        'error_code': -1,
                        'message': f'解析AI响应失败: {str(e)}',
                        'data': content,
                        'raw_data': news_data
                    }
            else:
                logging.error("=" * 80)
                logging.error("❌ GLM4处理失败:")
                logging.error("=" * 80)
                logging.error(f"错误响应: {response}")
                logging.error("=" * 80)
                return {
                    'error_code': -1,
                    'message': f'GLM4处理失败: {response["message"]}',
                    'data': None,
                    'raw_data': news_data
                }
                
        except Exception as e:
            logging.error(f"整合新闻数据失败: {str(e)}")
            return {
                'error_code': -1,
                'message': f'整合失败: {str(e)}',
                'data': None,
                'raw_data': news_data
            }

    def generate_html_newsletter(self, news_data: Dict[str, Any]) -> str:
        """
        生成邮箱友好型的HTML新闻网页
        
        Args:
            news_data: 新闻数据
            
        Returns:
            str: HTML网页内容
        """
        try:
            # 获取当前时间
            current_time = datetime.now(pytz.timezone('Asia/Shanghai'))
            date_str = current_time.strftime('%Y年%m月%d日')
            time_str = current_time.strftime('%H:%M:%S')
            
            # 提取新闻数据
            news_list = news_data.get('data', {}).get('news_list', [])
            summary = news_data.get('data', {}).get('summary', '今日新闻概览')
            total_count = news_data.get('data', {}).get('total_count', len(news_list))
            
            # HTML模板
            html_template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>每日新闻汇总 - {{ date_str }}</title>
    <style>
        /* 邮箱友好的CSS样式 */
        body {
            font-family: 'Microsoft YaHei', 'PingFang SC', 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        
        .container {
            background-color: #ffffff;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            margin: 0;
            font-size: 28px;
            font-weight: 300;
        }
        
        .header .date {
            margin-top: 10px;
            font-size: 16px;
            opacity: 0.9;
        }
        
        .header .time {
            font-size: 14px;
            opacity: 0.8;
            margin-top: 5px;
        }
        
        .summary {
            background-color: #f8f9fa;
            padding: 20px;
            border-left: 4px solid #667eea;
            margin: 20px;
            border-radius: 4px;
        }
        
        .summary h2 {
            margin: 0 0 10px 0;
            color: #495057;
            font-size: 18px;
        }
        
        .summary p {
            margin: 0;
            color: #6c757d;
            font-size: 14px;
        }
        
        .stats {
            display: flex;
            justify-content: space-around;
            background-color: #e9ecef;
            padding: 15px;
            margin: 20px;
            border-radius: 6px;
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-number {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }
        
        .stat-label {
            font-size: 12px;
            color: #6c757d;
            margin-top: 5px;
        }
        
        .news-section {
            padding: 0 20px 20px 20px;
        }
        
        .news-item {
            border-bottom: 1px solid #e9ecef;
            padding: 20px 0;
            transition: background-color 0.2s;
        }
        
        .news-item:hover {
            background-color: #f8f9fa;
        }
        
        .news-item:last-child {
            border-bottom: none;
        }
        
        .news-title {
            font-size: 16px;
            font-weight: 600;
            color: #212529;
            margin-bottom: 8px;
            line-height: 1.4;
        }
        
        .news-title a {
            color: #212529;
            text-decoration: none;
        }
        
        .news-title a:hover {
            color: #667eea;
        }
        
        .news-summary {
            color: #6c757d;
            font-size: 14px;
            line-height: 1.5;
            margin-bottom: 10px;
        }
        
        .news-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
            color: #adb5bd;
        }
        
        .news-source {
            background-color: #667eea;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
        }
        
        .news-time {
            color: #adb5bd;
        }
        
        .news-impact {
            margin: 8px 0;
            padding: 8px 12px;
            background-color: #f8f9fa;
            border-left: 3px solid #28a745;
            border-radius: 4px;
        }
        
        .impact-label {
            font-weight: 600;
            color: #495057;
            font-size: 12px;
        }
        
        .impact-content {
            color: #6c757d;
            font-size: 13px;
            margin-left: 5px;
        }
        
        .footer {
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #6c757d;
            font-size: 12px;
            border-top: 1px solid #e9ecef;
        }
        
        .footer p {
            margin: 5px 0;
        }
        
        /* 响应式设计 */
        @media (max-width: 600px) {
            body {
                padding: 10px;
            }
            
            .header {
                padding: 20px;
            }
            
            .header h1 {
                font-size: 24px;
            }
            
            .stats {
                flex-direction: column;
                gap: 10px;
            }
            
            .news-meta {
                flex-direction: column;
                align-items: flex-start;
                gap: 5px;
            }
        }
        
        /* 打印样式 */
        @media print {
            body {
                background-color: white;
                padding: 0;
            }
            
            .container {
                box-shadow: none;
                border: 1px solid #ddd;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📰 每日新闻汇总</h1>
            <div class="date">{{ date_str }}</div>
            <div class="time">{{ time_str }}</div>
        </div>
        
        <div class="summary">
            <h2>📋 今日概览</h2>
            <p>{{ summary }}</p>
        </div>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-number">{{ total_count }}</div>
                <div class="stat-label">新闻总数</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{{ positive_count }}</div>
                <div class="stat-label">正向影响</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{{ negative_count }}</div>
                <div class="stat-label">负向影响</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{{ news_sources_count }}</div>
                <div class="stat-label">新闻源</div>
            </div>
        </div>
        
        <div class="news-section">
            <h2 style="margin: 0 0 20px 0; color: #495057; font-size: 20px;">📰 精选新闻</h2>
            
            {% for news in news_list %}
            <div class="news-item">
                <div class="news-title">
                    <a href="{{ news.url }}" target="_blank">{{ news.title }}</a>
                </div>
                <div class="news-summary">{{ news.summary }}</div>
                {% if news.impact %}
                <div class="news-impact">
                    <span class="impact-label">💡 影响：</span>
                    <span class="impact-content">{{ news.impact }}</span>
                </div>
                {% endif %}
                <div class="news-meta">
                    <span class="news-source">{{ news.mapped_source }}</span>
                    <span class="news-time">{{ news.pubDate }}</span>
                </div>
            </div>
            {% endfor %}
        </div>
        
        <div class="footer">
            <p>🤖 本新闻汇总由AI智能整理生成</p>
            <p>📅 生成时间：{{ date_str }} {{ time_str }}</p>
            <p>📊 数据来源：金十数据、财联社、华尔街见闻</p>
            <p>💡 如有问题，请联系技术支持</p>
        </div>
    </div>
</body>
</html>
            """
            
            # 计算新闻源数量并处理来源映射
            sources = set()
            for news in news_list:
                if 'source' in news:
                    # 添加映射后的来源到新闻对象
                    news['mapped_source'] = self.get_mapped_sources(news['source'])
                    # 统计原始来源数量
                    sources.add(news['source'])
            news_sources_count = len(sources)
            
            # 获取处理时间
            processed_time = news_data.get('data', {}).get('processed_time', 'N/A')
            
            # 获取影响统计
            positive_count = news_data.get('data', {}).get('positive_count', 0)
            negative_count = news_data.get('data', {}).get('negative_count', 0)
            
            # 渲染HTML
            html_content = render_template_string(
                html_template,
                date_str=date_str,
                time_str=time_str,
                summary=summary,
                total_count=total_count,
                positive_count=positive_count,
                negative_count=negative_count,
                news_sources_count=news_sources_count,
                processed_time=processed_time,
                news_list=news_list
            )
            
            return html_content
            
        except Exception as e:
            logging.error(f"生成HTML新闻网页失败: {str(e)}")
            # 返回错误页面
            error_html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>新闻生成错误</title>
    <style>
        body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
        .error {{ color: #dc3545; }}
    </style>
</head>
<body>
    <h1 class="error">❌ 新闻生成失败</h1>
    <p>抱歉，生成新闻网页时出现错误：{str(e)}</p>
    <p>请稍后重试或联系技术支持。</p>
</body>
</html>
            """
            return error_html

# 创建API实例
news_api = NewsIntegrationAPI()

@news_integration_bp.route('/news/integrated', methods=['GET'])
def get_integrated_news():
    """
    获取整合后的新闻数据
    
    Returns:
        JSON: 整合后的新闻数据
    """
    try:
        logging.info("🚀 ========== 开始获取整合新闻数据 ==========")
        start_time = datetime.now()
        
        current_app.logger.info("开始获取整合新闻数据")
        
        # 获取所有新闻源数据
        logging.info("📡 第一步：获取所有新闻源数据")
        news_data = news_api.fetch_all_news()
        
        # 统计原始数据
        total_raw_news = 0
        for source_name, source_data in news_data.items():
            if source_data.get('error_code') == 0:
                total_raw_news += len(source_data.get('data', []))
        logging.info(f"📊 原始新闻数据统计：总计 {total_raw_news} 条新闻")
        
        # 使用GLM4整合和去重
        logging.info("🤖 第二步：使用GLM4整合和去重新闻数据")
        integrated_result = news_api.integrate_news_with_glm4(news_data)
        
        # 统计整合后的数据
        if integrated_result['error_code'] == 0:
            integrated_news_count = len(integrated_result.get('data', {}).get('news_list', []))
            logging.info(f"📈 整合后新闻数据统计：{integrated_news_count} 条新闻")
            
            # 检查是否有新闻被截断
            if integrated_news_count < total_raw_news * 0.5:  # 如果整合后少于原始数据的50%
                logging.warning(f"⚠️ 警告：整合后新闻数量({integrated_news_count})明显少于原始数量({total_raw_news})，可能存在数据截断")
        else:
            logging.error(f"❌ 新闻整合失败：{integrated_result.get('message')}")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logging.info(f"⏱️ 整个处理流程耗时：{duration:.2f}秒")
        
        current_app.logger.info("新闻数据整合完成")
        logging.info("✅ ========== 获取整合新闻数据完成 ==========")
        
        return jsonify(integrated_result)
        
    except Exception as e:
        logging.error(f"❌ 获取整合新闻数据异常：{str(e)}")
        current_app.logger.error(f"获取整合新闻数据失败: {str(e)}")
        return jsonify({
            'error_code': -1,
            'message': f'获取新闻数据失败: {str(e)}',
            'data': None
        }), 500

@news_integration_bp.route('/news/test_ai', methods=['GET'])
def test_news_ai():
    """
    测试新闻AI的prompt和返回结果
    
    Returns:
        JSON: 测试结果，包含prompt和AI返回
    """
    try:
        current_app.logger.info("开始测试新闻AI")
        
        # 获取所有新闻源数据
        news_data = news_api.fetch_all_news()
        
        # 使用GLM4整合和去重（会打印详细的prompt和返回日志）
        integrated_result = news_api.integrate_news_with_glm4(news_data)
        
        # 返回测试结果
        return jsonify({
            'error_code': 0,
            'message': '测试完成，请查看日志获取详细的prompt和返回信息',
            'data': {
                'test_status': 'completed',
                'result': integrated_result
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"测试新闻AI失败: {str(e)}")
        return jsonify({
            'error_code': -1,
            'message': f'测试失败: {str(e)}',
            'data': None
        }), 500

@news_integration_bp.route('/news/raw', methods=['GET'])
def get_raw_news():
    """
    获取原始新闻数据（不经过GLM4处理）
    
    Returns:
        JSON: 原始新闻数据
    """
    try:
        logging.info("🔍 ========== 开始获取原始新闻数据 ==========")
        current_app.logger.info("开始获取原始新闻数据")
        
        # 获取所有新闻源数据
        news_data = news_api.fetch_all_news()
        
        # 详细统计每个新闻源的数据
        logging.info("📊 原始新闻数据详细统计：")
        total_news = 0
        for source_name, source_data in news_data.items():
            if source_data.get('error_code') == 0:
                news_count = len(source_data.get('data', []))
                total_news += news_count
                logging.info(f"  📰 {source_name}: {news_count} 条新闻")
                
                # 打印前3条新闻的标题
                for i, item in enumerate(source_data.get('data', [])[:3]):
                    title = item.get('title', '无标题')
                    logging.info(f"    {i+1}. {title[:60]}...")
            else:
                logging.info(f"  ❌ {source_name}: 获取失败 - {source_data.get('message')}")
        
        logging.info(f"📈 总计: {total_news} 条新闻")
        current_app.logger.info("原始新闻数据获取完成")
        logging.info("✅ ========== 原始新闻数据获取完成 ==========")
        
        return jsonify({
            'error_code': 0,
            'message': 'success',
            'data': news_data,
            'summary': {
                'total_news': total_news,
                'sources_count': len(news_data),
                'successful_sources': len([s for s in news_data.values() if s.get('error_code') == 0])
            }
        })
        
    except Exception as e:
        logging.error(f"❌ 获取原始新闻数据异常：{str(e)}")
        current_app.logger.error(f"获取原始新闻数据失败: {str(e)}")
        return jsonify({
            'error_code': -1,
            'message': f'获取新闻数据失败: {str(e)}',
            'data': None
        }), 500

@news_integration_bp.route('/news/sources', methods=['GET'])
def get_news_sources():
    """
    获取支持的新闻源列表
    
    Returns:
        JSON: 新闻源列表
    """
    return jsonify({
        'error_code': 0,
        'message': 'success',
        'data': {
            'sources': list(news_api.news_sources.keys()),
            'total_count': len(news_api.news_sources)
        }
    })


@news_integration_bp.route('/news/health', methods=['GET'])
def health_check():
    """
    健康检查接口
    
    Returns:
        JSON: 健康状态
    """
    try:
        # 测试一个新闻源
        test_source = list(news_api.news_sources.items())[0]
        result = news_api.fetch_news_from_source(test_source[0], test_source[1])
        
        if result['error_code'] == 0:
            return jsonify({
                'error_code': 0,
                'message': '服务正常',
                'data': {
                    'status': 'healthy',
                    'test_source': test_source[0],
                    'news_count': len(result.get('data', []))
                }
            })
        else:
            return jsonify({
                'error_code': -1,
                'message': '服务异常',
                'data': {
                    'status': 'unhealthy',
                    'error': result['message']
                }
            }), 500
            
    except Exception as e:
        return jsonify({
            'error_code': -1,
            'message': '服务异常',
            'data': {
                'status': 'unhealthy',
                'error': str(e)
            }
        }), 500

@news_integration_bp.route('/news/html', methods=['GET'])
def get_news_html():
    """
    获取邮箱友好型的HTML新闻网页
    
    Returns:
        HTML: 可直接运行的HTML网页
    """
    try:
        current_app.logger.info("开始生成HTML新闻网页")
        
        # 获取所有新闻源数据
        news_data = news_api.fetch_all_news()
        
        # 使用GLM4整合和去重
        integrated_result = news_api.integrate_news_with_glm4(news_data)
        
        if integrated_result['error_code'] == 0:
            # 生成HTML网页
            html_content = news_api.generate_html_newsletter(integrated_result)
            
            current_app.logger.info("HTML新闻网页生成完成")
            
            # 返回HTML内容
            from flask import Response
            return Response(html_content, mimetype='text/html; charset=utf-8')
        else:
            # 返回错误页面
            error_html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>新闻生成错误</title>
    <style>
        body {{ 
            font-family: 'Microsoft YaHei', Arial, sans-serif; 
            text-align: center; 
            padding: 50px; 
            background-color: #f5f5f5;
        }}
        .error-container {{
            background-color: white;
            border-radius: 8px;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            max-width: 600px;
            margin: 0 auto;
        }}
        .error {{ color: #dc3545; font-size: 24px; }}
        .error-message {{ color: #6c757d; margin: 20px 0; }}
        .retry-btn {{
            background-color: #667eea;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="error-container">
        <h1 class="error">❌ 新闻生成失败</h1>
        <p class="error-message">抱歉，生成新闻网页时出现错误：</p>
        <p class="error-message">{integrated_result.get('message', '未知错误')}</p>
        <a href="/news/html" class="retry-btn">🔄 重新生成</a>
    </div>
</body>
</html>
            """
            return Response(error_html, mimetype='text/html; charset=utf-8')
        
    except Exception as e:
        current_app.logger.error(f"生成HTML新闻网页失败: {str(e)}")
        error_html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>新闻生成错误</title>
    <style>
        body {{ 
            font-family: 'Microsoft YaHei', Arial, sans-serif; 
            text-align: center; 
            padding: 50px; 
            background-color: #f5f5f5;
        }}
        .error-container {{
            background-color: white;
            border-radius: 8px;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            max-width: 600px;
            margin: 0 auto;
        }}
        .error {{ color: #dc3545; font-size: 24px; }}
        .error-message {{ color: #6c757d; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="error-container">
        <h1 class="error">❌ 系统错误</h1>
        <p class="error-message">抱歉，系统出现错误：{str(e)}</p>
        <p class="error-message">请稍后重试或联系技术支持。</p>
    </div>
</body>
</html>
        """
        return Response(error_html, mimetype='text/html; charset=utf-8')

@news_integration_bp.route('/news/feishu/test', methods=['POST'])
def test_feishu_news_push():
    """
    测试飞书新闻推送功能
    
    Returns:
        JSON: 推送结果
    """
    try:
        import time
        start_time = time.time()
        current_app.logger.info("开始测试飞书新闻推送")
        
        # 从请求中获取群组ID
        from flask import request
        data = request.get_json() or {}
        chat_id = data.get('chat_id', '')
        
        if not chat_id:
            return jsonify({
                'error_code': -1,
                'message': '请提供群组ID (chat_id)',
                'data': None
            }), 400
        
        print(f"\n🔍 飞书新闻推送测试详情:")
        print(f"📋 群组ID: {chat_id}")
        
        # 获取所有新闻源数据
        print("📰 获取新闻数据...")
        news_start = time.time()
        news_data = news_api.fetch_all_news()
        news_time = time.time() - news_start
        print(f"⏱️ 新闻获取耗时: {news_time:.2f}秒")
        
        # 使用GLM4整合和去重
        print("🤖 整合新闻数据...")
        glm_start = time.time()
        integrated_result = news_api.integrate_news_with_glm4(news_data)
        glm_time = time.time() - glm_start
        print(f"⏱️ GLM4处理耗时: {glm_time:.2f}秒")
        
        if integrated_result['error_code'] == 0:
            print("✅ 新闻整合成功，开始发送到飞书...")
            # 发送新闻消息到飞书
            feishu_start = time.time()
            success = feishu_bot.send_news_message(chat_id, integrated_result)
            feishu_time = time.time() - feishu_start
            print(f"⏱️ 飞书发送耗时: {feishu_time:.2f}秒")
            
            if success:
                total_time = time.time() - start_time
                current_app.logger.info(f"飞书新闻推送测试成功，总耗时: {total_time:.2f}秒")
                print(f"✅ 飞书新闻推送成功，总耗时: {total_time:.2f}秒")
                return jsonify({
                    'error_code': 0,
                    'message': '飞书新闻推送成功',
                    'data': {
                        'chat_id': chat_id,
                        'news_count': len(integrated_result.get('data', {}).get('news_list', [])),
                        'push_time': datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S'),
                        'performance': {
                            'news_fetch_time': f"{news_time:.2f}s",
                            'glm4_process_time': f"{glm_time:.2f}s",
                            'feishu_send_time': f"{feishu_time:.2f}s",
                            'total_time': f"{total_time:.2f}s"
                        }
                    }
                })
            else:
                current_app.logger.error("飞书新闻推送测试失败")
                print("❌ 飞书新闻推送失败")
                return jsonify({
                    'error_code': -1,
                    'message': '飞书新闻推送失败',
                    'data': None
                }), 500
        else:
            current_app.logger.error(f"新闻整合失败: {integrated_result.get('message')}")
            print(f"❌ 新闻整合失败: {integrated_result.get('message')}")
            return jsonify({
                'error_code': -1,
                'message': f'新闻整合失败: {integrated_result.get("message")}',
                'data': None
            }), 500
        
    except Exception as e:
        current_app.logger.error(f"飞书新闻推送测试异常: {str(e)}")
        print(f"❌ 飞书新闻推送测试异常: {str(e)}")
        return jsonify({
            'error_code': -1,
            'message': f'测试异常: {str(e)}',
            'data': None
        }), 500

@news_integration_bp.route('/news/crypto/test', methods=['GET', 'POST'])
def test_crypto_news_push():
    """
    测试加密货币新闻推送功能
    
    Returns:
        JSON: 推送结果
    """
    try:
        import time
        start_time = time.time()
        current_app.logger.info("开始测试加密货币新闻推送")
        
        # 使用配置中的群组ID
        chat_id = config.FEISHU_CHAT_ID_COIN
        if not chat_id:
            return jsonify({
                'error_code': -1,
                'message': '未配置加密货币新闻群组ID (FEISHU_CHAT_ID_COIN)',
                'data': None
            }), 400
        
        print(f"\n🔍 加密货币新闻推送测试详情:")
        print(f"📋 群组ID: {chat_id}")
        
        # 导入加密货币新闻API
        from crypto_news_api import crypto_news_api
        
        # 获取新的加密货币新闻数据
        print("📰 获取新的加密货币新闻数据...")
        crypto_start = time.time()
        crypto_news_result = crypto_news_api.get_new_crypto_news()
        crypto_time = time.time() - crypto_start
        print(f"⏱️ 加密货币新闻获取耗时: {crypto_time:.2f}秒")
        
        if crypto_news_result['error_code'] == 0:
            # 检查是否有新新闻
            news_count = len(crypto_news_result.get('data', {}).get('news_list', []))
            
            if news_count > 0:
                print(f"✅ 发现 {news_count} 条新加密货币新闻，开始发送到飞书...")
                # 发送加密货币新闻消息到飞书
                feishu_start = time.time()
                success = feishu_bot.send_crypto_news_message(chat_id, crypto_news_result)
                feishu_time = time.time() - feishu_start
                print(f"⏱️ 飞书发送耗时: {feishu_time:.2f}秒")
                
                if success:
                    total_time = time.time() - start_time
                    current_app.logger.info(f"加密货币新闻推送测试成功，发送 {news_count} 条新闻，总耗时: {total_time:.2f}秒")
                    print(f"✅ 加密货币新闻推送成功，总耗时: {total_time:.2f}秒")
                    return jsonify({
                        'error_code': 0,
                        'message': f'加密货币新闻推送成功，发送 {news_count} 条新新闻',
                        'data': {
                            'chat_id': chat_id,
                            'news_count': news_count,
                            'max_sent_id': crypto_news_api.get_max_sent_id(),
                            'push_time': datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S'),
                            'performance': {
                                'crypto_news_fetch_time': f"{crypto_time:.2f}s",
                                'feishu_send_time': f"{feishu_time:.2f}s",
                                'total_time': f"{total_time:.2f}s"
                            },
                            'news_summary': crypto_news_result.get('data', {}).get('summary', '')
                        }
                    })
                else:
                    current_app.logger.error("加密货币新闻推送测试失败")
                    print("❌ 加密货币新闻推送失败")
                    return jsonify({
                        'error_code': -1,
                        'message': '加密货币新闻推送失败',
                        'data': None
                    }), 500
            else:
                print("ℹ️ 没有新加密货币新闻，跳过发送")
                return jsonify({
                    'error_code': 0,
                    'message': '没有新加密货币新闻',
                    'data': {
                        'chat_id': chat_id,
                        'news_count': 0,
                        'max_sent_id': crypto_news_api.get_max_sent_id(),
                        'push_time': datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S'),
                        'performance': {
                            'crypto_news_fetch_time': f"{crypto_time:.2f}s",
                            'feishu_send_time': "0.00s",
                            'total_time': f"{time.time() - start_time:.2f}s"
                        },
                        'news_summary': '没有新新闻'
                    }
                })
        else:
            current_app.logger.error(f"获取加密货币新闻失败: {crypto_news_result.get('message')}")
            print(f"❌ 获取加密货币新闻失败: {crypto_news_result.get('message')}")
            return jsonify({
                'error_code': -1,
                'message': f'获取加密货币新闻失败: {crypto_news_result.get("message")}',
                'data': None
            }), 500
        
    except Exception as e:
        current_app.logger.error(f"加密货币新闻推送测试异常: {str(e)}")
        print(f"❌ 加密货币新闻推送测试异常: {str(e)}")
        return jsonify({
            'error_code': -1,
            'message': f'测试异常: {str(e)}',
            'data': None
        }), 500
