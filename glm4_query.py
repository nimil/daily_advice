import logging
from zhipuai import ZhipuAI
from typing import Dict, Any, List
import json
from solar_terms_query import SolarTermsQuery
from almanac_query import AlmanacQuery
from datetime import datetime
from holiday_query import HolidayQuery
from flask import current_app
import pytz
from life_suggestion_query import LifeSuggestionQuery

class GLM4Query:
    """智谱AI GLM-4 查询类"""
    
    def __init__(self, api_key: str):
        """
        初始化GLM-4查询类
        
        Args:
            api_key: 智谱AI API Key
        """
        self.client = ZhipuAI(api_key=api_key)
        self.model = "glm-4.5"  # 使用最新的GLM-4模型
        
    def query(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        发送查询请求
        
        Args:
            messages: 对话历史，格式为[{"role": "user", "content": "你好"}, ...]
            **kwargs: 其他参数，如temperature、top_p等
            
        Returns:
            Dict: API返回的结果
        """
        try:
            current_app.logger.info(f"开始发送请求: {messages}")
            # 发送请求
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
                **kwargs
            )
            
            return {
                'error_code': 0,
                'message': 'success',
                'data': response
            }
                
        except Exception as e:
            logging.error(f"请求异常: {str(e)}")
            return {
                'error_code': -1,
                'message': f'请求发生错误: {str(e)}',
                'data': None
            }

    def get_daily_advice(self) -> Dict[str, Any]:
        """
        获取每日建议，包含节气养生和老黄历信息
        
        Returns:
            Dict: 整合后的建议信息
        """
        try:
            # 获取当前日期
            current_date = datetime.now(pytz.timezone('Asia/Shanghai'))
            date_str = current_date.strftime('%Y-%m-%d')
            
            # 初始化查询类
            solar_terms = SolarTermsQuery("5b71ee4243a804d6601641093d8a4cbe")
            almanac = AlmanacQuery("68c8a6c0be8e9cd53cd92235fb99b287")
            holiday = HolidayQuery("1a14f196bfb12cb84b609a8272f750d4")
            life_suggestion = LifeSuggestionQuery("SEuAOXtlQ5l9R7URP")

            # 获取节气信息
            solar_result = solar_terms.get_current_solar_term(date_str)
            # 获取老黄历信息
            almanac_result = almanac.query_almanac(date_str)
            # 获取节假日信息
            holiday_result = holiday.query_today(date_str)
            # 获取生活建议信息
            weather_info = life_suggestion.get_all_info()

            if solar_result.get('error_code') == 0 and almanac_result.get('error_code') == 0:
                # 检查是否是节假日
                is_holiday = holiday_result.get('result', {}).get('status') == '1'
                
                # 准备提示信息
                prompt = f"""
                下面我会给你若干材料，结合当前日期{current_date.strftime('%Y年%m月%d日')}
                请注意:在desc字段中，不要直接表述当前日期,因为日期我已知道不要浪费篇幅，
                根据当前日期，结合节气养生知识与老黄历的相关知识，介绍下今天的情况,
                请用中文响应我，
                我给你的材料如下所示：
                
                第一个材料关于当前节气和下一个节气的信息：
                {json.dumps(solar_result, ensure_ascii=False, indent=4)}
                
                第二个材料关于今天的老黄历信息：
                {json.dumps(almanac_result['result'], ensure_ascii=False, indent=4)}

                第三个材料关于今天的天气信息：
                {json.dumps(weather_info, ensure_ascii=False, indent=4)}
                
                {f'''
                第四个材料关于今天的节假日信息：
                {json.dumps(holiday_result['result'], ensure_ascii=False, indent=4)}
                ''' if is_holiday else ''}
                
                请严格按照该格式给我响应：
                {{
                    "date": "{current_date.strftime('%Y年%m月%d日')}",
                    "nongli": "当前日期的农历日期",
                    "food": "当前日期的饮食建议",
                    "yi": "今日宜",
                    "ji": "今日忌",
                    "desc": "当前日期材料的总结"
                }}
                其中desc字段可以加入自己的理解
                """
                
                # 调用GLM-4生成建议
                response = self.query([
                    {"role": "system", "content": "你是一个乐于归纳总结的小助手，请根据信息，结合你自身的专业知识，为用户提供专业，准确，有见地的建议，尽量不要出现难以理解的词语或者句子"},
                    {"role": "user", "content": prompt}
                    ])
                
                if response['error_code'] == 0:
                    # 解析GLM-4的响应
                    content = response['data'].choices[0].message.content
                    try:
                        # 尝试解析JSON响应
                        # 确保使用UTF-8编码解析和返回JSON
                        content = content.encode('utf-8').decode('utf-8')
                        return {
                            'error_code': 0,
                            'message': 'success',
                            'data': json.loads(content)
                        }
                    except json.JSONDecodeError:
                        return {
                            'error_code': -1,
                            'message': '解析AI响应失败',
                            'data': content
                        }
                else:
                    return response
            else:
                return {
                    'error_code': -1,
                    'message': '获取基础数据失败',
                    'data': None
                }
                
        except Exception as e:
            logging.error(f"生成每日建议失败: {str(e)}")
            return {
                'error_code': -1,
                'message': f'生成建议失败: {str(e)}',
                'data': None
            }

    def chat(self, content: str) -> str:
        """
        简单的对话接口
        
        Args:
            content: 用户输入内容
            
        Returns:
            str: 响应内容
        """
        messages = [{"role": "system", "content": "我现在是某APP的后端开发,需要读取结构化的数据，不需要考虑可读写,不需要markdown标记"},{"role": "user", "content": content}]
        response = self.query(messages)
        if response['error_code'] == 0:
            return response['data'].choices[0].message.content
        return f"请求失败: {response['message']}"

def test_query():
    """测试查询功能"""
    from config import config
    
    # 初始化查询类
    glm4 = GLM4Query(config.GLM4_API_KEY)
    
    # 测试获取每日建议
    result = glm4.get_daily_advice()
    print("\n每日建议:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 测试对话
    messages = [
        {"role": "user", "content": "你好，请介绍一下你自己"},
        {"role": "assistant", "content": "我是GLM-4，一个由智谱AI开发的大语言模型。"},
        {"role": "user", "content": "你能做什么？"}
    ]
    
    # 基本调用
    result = glm4.query(messages)
    print("\n基本调用结果:")
    if result['error_code'] == 0:
        print(result['data'].choices[0].message)
    else:
        print(result['message'])
    
    # 带参数调用
    result = glm4.query(
        messages,
        temperature=0.7,
        top_p=0.8,
        max_tokens=1024
    )
    print("\n带参数调用结果:")
    if result['error_code'] == 0:
        print(result['data'].choices[0].message)
    else:
        print(result['message'])

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    test_query() 