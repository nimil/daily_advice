from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pytz
import logging
from solar_terms_api import get_cached_daily_advice, get_current_date
from almanac_query import AlmanacQuery
import os

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
    
    # 添加每小时刷新缓存的任务
    scheduler.add_job(
        func=fetch_daily_advice,
        trigger=CronTrigger(minute='10'),  # 每小时的第10分钟执行
        id='fetch_daily_advice',
        name='获取每日建议',
        replace_existing=True
    )
    
    # 添加每天获取老黄历数据的任务
    # scheduler.add_job(
    #     func=fetch_almanac_data,
    #     trigger=CronTrigger(hour='0', minute='5'),  # 每天凌晨0点5分执行
    #     id='fetch_almanac_data',
    #     name='获取老黄历数据',
    #     replace_existing=True
    # )
    
    # 启动调度器
    scheduler.start()
    # 立即执行每日建议缓存
    fetch_daily_advice()
    app.logger.info("定时任务调度器已启动")
    
    # 保存调度器实例到应用配置中
    app.scheduler = scheduler 