from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pytz
import logging
from solar_terms_api import get_cached_daily_advice, get_current_date
from almanac_query import AlmanacQuery
from feishu_bot import feishu_bot
from news_integration_api import NewsIntegrationAPI
from crypto_news_api import crypto_news_api
from config import config
import os
import threading

def init_scheduler(app):
    """
    初始化定时任务调度器
    
    Args:
        app: Flask应用实例
    """
    scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Shanghai'))
    
    def fetch_daily_advice():
        """获取每日建议的任务，用于刷新缓存"""
        with app.app_context():
            try:
                app.logger.info(f"开始执行定时任务刷新缓存: {datetime.now()}")
                
                # 直接调用缓存函数刷新数据
                query_date = get_current_date()
                result = get_cached_daily_advice(query_date)
                
                if result and result.get('error_code') == 0:
                    app.logger.info("定时任务执行成功")
                else:
                    app.logger.error(f"定时任务执行失败: {result}")
                    
            except Exception as e:
                app.logger.error(f"定时任务执行异常: {str(e)}")

    def fetch_almanac_data():
        """获取老黄历数据的任务"""
        with app.app_context():
            try:
                app.logger.info(f"开始执行老黄历数据获取任务: {datetime.now()}")
                
                # 初始化查询类
                from config import config
                almanac = AlmanacQuery(config.ALMANAC_API_KEY)
                
                # 查询未来7天的数据
                results = almanac.query_next_n_days(50)
                
                if results:
                    app.logger.info(f"成功获取 {len(results)} 天的老黄历数据")
                else:
                    app.logger.error("获取老黄历数据失败")
                    
            except Exception as e:
                app.logger.error(f"老黄历数据获取任务异常: {str(e)}")
    
    def send_daily_news_to_feishu():
        """发送每日新闻到飞书的任务"""
        with app.app_context():
            try:
                current_time = datetime.now(pytz.timezone('Asia/Shanghai'))
                app.logger.info(f"开始执行飞书新闻推送任务: {current_time}")
                
                # 获取群组ID（可以从环境变量或配置中获取）
                chat_id = os.getenv('FEISHU_CHAT_ID', '')
                if not chat_id:
                    app.logger.error("未配置飞书群组ID，跳过新闻推送")
                    return
                
                # 初始化新闻整合API
                news_api = NewsIntegrationAPI()
                
                # 获取所有新闻源数据
                news_data = news_api.fetch_all_news()
                
                # 使用GLM4整合和去重
                integrated_result = news_api.integrate_news_with_glm4(news_data)
                
                if integrated_result['error_code'] == 0:
                    # 发送新闻消息到飞书
                    success = feishu_bot.send_news_message(chat_id, integrated_result)
                    
                    if success:
                        app.logger.info(f"成功发送每日新闻到飞书 - {current_time.strftime('%H:%M')}")
                    else:
                        app.logger.error("发送每日新闻到飞书失败")
                else:
                    app.logger.error(f"新闻整合失败: {integrated_result.get('message')}")
                    
            except Exception as e:
                app.logger.error(f"飞书新闻推送任务异常: {str(e)}")
    
    def send_crypto_news_to_feishu():
        """发送加密货币新闻到飞书的任务"""
        with app.app_context():
            try:
                current_time = datetime.now(pytz.timezone('Asia/Shanghai'))
                
                # 检查是否为工作日（周一至周五）
                weekday = current_time.weekday()  # 0=周一, 6=周日
                if weekday >= 5:  # 周六(5)和周日(6)
                    app.logger.info(f"当前为周末，跳过加密货币新闻推送任务: {current_time.strftime('%Y-%m-%d %H:%M')}")
                    return
                
                # 检查时间是否在工作时间内（8:30-17:30）
                current_hour = current_time.hour
                current_minute = current_time.minute
                current_time_minutes = current_hour * 60 + current_minute
                
                start_time_minutes = 8 * 60 + 30  # 8:30
                end_time_minutes = 17 * 60 + 30   # 17:30
                
                if current_time_minutes < start_time_minutes or current_time_minutes > end_time_minutes:
                    app.logger.info(f"当前时间不在工作时间内，跳过加密货币新闻推送任务: {current_time.strftime('%Y-%m-%d %H:%M')}")
                    return
                
                app.logger.info(f"开始执行加密货币新闻推送任务: {current_time}")
                
                # 获取加密货币新闻群组ID
                chat_id = config.FEISHU_CHAT_ID_COIN
                if not chat_id:
                    app.logger.error("未配置加密货币新闻群组ID，跳过新闻推送")
                    return
                
                # 获取新的加密货币新闻（过滤已发送的）
                crypto_news_result = crypto_news_api.get_new_crypto_news()
                
                if crypto_news_result['error_code'] == 0:
                    # 检查是否有新新闻
                    news_count = len(crypto_news_result.get('data', {}).get('news_list', []))
                    
                    if news_count > 0:
                        # 发送加密货币新闻消息到飞书
                        success = feishu_bot.send_crypto_news_message(chat_id, crypto_news_result)
                        
                        if success:
                            app.logger.info(f"成功发送 {news_count} 条新加密货币新闻到飞书 - {current_time.strftime('%H:%M')}")
                        else:
                            app.logger.error("发送加密货币新闻到飞书失败")
                    else:
                        app.logger.info(f"没有新加密货币新闻，跳过发送 - {current_time.strftime('%H:%M')}")
                else:
                    app.logger.error(f"获取加密货币新闻失败: {crypto_news_result.get('message')}")
                    
            except Exception as e:
                app.logger.error(f"加密货币新闻推送任务异常: {str(e)}")
    
    # 添加每小时刷新缓存的任务
    scheduler.add_job(
        func=fetch_daily_advice,
        trigger=CronTrigger(minute='10'),  # 每小时的第10分钟执行
        id='fetch_daily_advice',
        name='获取每日建议',
        replace_existing=True
    )
    
    # 添加每天早上10点发送新闻到飞书的任务
    scheduler.add_job(
        func=send_daily_news_to_feishu,
        trigger=CronTrigger(hour='10', minute='0'),  # 每天早上10点执行
        id='send_daily_news_to_feishu_morning',
        name='发送每日新闻到飞书（早10点）',
        replace_existing=True
    )
    
    # 添加每天下午3点半发送新闻到飞书的任务
    scheduler.add_job(
        func=send_daily_news_to_feishu,
        trigger=CronTrigger(hour='15', minute='30'),  # 每天下午3点半执行
        id='send_daily_news_to_feishu_afternoon',
        name='发送每日新闻到飞书（下午3点半）',
        replace_existing=True
    )
    
    # 添加每10分钟发送加密货币新闻到飞书的任务（仅工作日8:30-17:30）
    scheduler.add_job(
        func=send_crypto_news_to_feishu,
        trigger=CronTrigger(minute='*/20'),  # 每20分钟执行一次
        id='send_crypto_news_to_feishu',
        name='发送加密货币新闻到飞书（工作日8:30-17:30，每20分钟）',
        replace_existing=True
    )
    
    #添加每天获取老黄历数据的任务
    # scheduler.add_job(
    #     func=fetch_almanac_data,
    #     trigger=CronTrigger(hour='0', minute='5'),  # 每天凌晨0点5分执行
    #     id='fetch_almanac_data',
    #     name='获取老黄历数据',
    #     replace_existing=True
    # )
    
    # 启动调度器
    scheduler.start()
    # 异步执行每日建议缓存，避免阻塞应用启动
    def run_fetch_daily_advice_async():
        try:
            fetch_daily_advice()
        except Exception as e:
            app.logger.error(f"异步执行每日建议缓存失败: {str(e)}")
    
    thread = threading.Thread(target=run_fetch_daily_advice_async, daemon=True)
    thread.start()
    app.logger.info("定时任务调度器已启动，每日建议缓存将在后台异步执行")
    
    # 保存调度器实例到应用配置中
    app.scheduler = scheduler 