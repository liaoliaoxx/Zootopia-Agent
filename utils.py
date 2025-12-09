from openai import OpenAI
import os

client = OpenAI(
    api_key="", # 设置你的 API KEY
    base_url="https://api-inference.modelscope.cn/v1" 
)

def call_llm(prompt):
    try:
        completion = client.chat.completions.create(
            model="Qwen/Qwen3-8B", 
            messages=[
                {"role": "system", "content": "You are a roleplay actor in Zootopia."},
                {"role": "user", "content": prompt}
            ],
            extra_body = {
                "enable_thinking": False,
            },
            temperature=0.7
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error calling LLM: {e}"