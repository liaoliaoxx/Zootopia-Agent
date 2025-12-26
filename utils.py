from openai import OpenAI
import os

# 1. 消除并行警告
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# 2. 配置 Client
client = OpenAI(
    api_key="ms-7c52c0a5-85e6-49fb-931c-9fea5a1212ce", # 你的 API KEY
    base_url="https://api-inference.modelscope.cn/v1" 
)

def call_llm(prompt, system_prompt=None, json_mode=False):
    """
    通用 LLM 调用函数
    :param prompt: 用户输入的指令
    :param system_prompt: 系统提示词 (默认为 Zootopia 设定)
    :param json_mode: 是否强制要求 JSON 格式 (对某些支持的 API 有效，这里主要作为标记)
    """
    
    # 默认的 Zootopia 设定 (用于对话)
    default_system = "You are a roleplay actor in Zootopia. Please use Chinese for thinking and speaking."
    
    # 如果没传 system_prompt，就用默认的；如果传了(比如记忆整理时)，就用传进来的
    final_system = system_prompt if system_prompt else default_system

    messages = [
        {"role": "system", "content": final_system},
        {"role": "user", "content": prompt}
    ]

    try:
        # 针对需要输出 JSON 的情况，可以在这里微调 parameters
        # 虽然 ModelScope 可能不完全支持 response_format={"type": "json_object"}
        # 但我们可以通过 prompt 强化它
        
        completion = client.chat.completions.create(
            model="Qwen/Qwen2.5-7B-Instruct", # 建议确认模型名称，Qwen2.5 指令遵循能力更好
            messages=messages,
            extra_body={
                "enable_thinking": False,
            },
            temperature=0.7 if not json_mode else 0.1, # 提取数据时温度低一点更稳定
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"❌ LLM Call Error: {e}")
        return "{}" if json_mode else f"Error: {e}"