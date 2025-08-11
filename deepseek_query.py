from openai import OpenAI
import logging
from typing import Dict, Any, List

class DeepseekR1Query:
    """DeepseekR1 查询类"""
    
    def __init__(self, api_key: str):
        """
        初始化 DeepseekR1 查询类
        
        Args:
            api_key: API密钥
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.lkeap.cloud.tencent.com/v1"
        )
        self.model = "deepseek-r1"
        
    def query(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        发送查询请求
        
        Args:
            messages: 对话历史，格式为[{"role": "user", "content": "你好"}, ...]
            **kwargs: 其他参数
            
        Returns:
            str: 响应内容
        """
        try:
            logging.info(f"开始发送请求: {messages}")
            
            chat_completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
                stream=False,
                **kwargs
            )
            
            return chat_completion.choices[0].message.content
                
        except Exception as e:
            error_msg = f"请求异常: {str(e)}"
            logging.error(error_msg)
            return error_msg
            
    def chat(self, content: str) -> str:
        """
        简单的对话接口
        
        Args:
            content: 用户输入内容
            
        Returns:
            str: 响应内容
        """
        messages = [{"role": "system", "content": "我现在是某APP的后端开发,需要读取结构化的数据，不需要考虑可读写,不需要markdown标记"},{"role": "user", "content": content}]
        return self.query(messages)

def test_query():
    """测试查询功能"""
    from config import config
    
    # 初始化查询类
    deepseek = DeepseekR1Query(config.DEEPSEEK_API_KEY)
    
    # 测试单轮对话
    print("\n测试单轮对话:")
    result = deepseek.chat("你是谁?")
    print(f"响应: {result}")
    
    # 测试多轮对话
    print("\n测试多轮对话:")
    messages = [
        {"role": "user", "content": "今天天气怎么样?"},
        {"role": "assistant", "content": "我是AI助手，无法直接感知天气，建议您查看天气预报。"},
        {"role": "user", "content": "那你能做什么?"}
    ]
    result = deepseek.query(messages)
    print(f"响应: {result}")

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    test_query() 