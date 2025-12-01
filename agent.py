from memory import MemoryStream
from utils import call_llm
import time
import re

class ZootopiaAgent:
    def __init__(self, name, persona, speech_style, is_slow=False):
        self.name = name
        self.persona = persona
        self.speech_style = speech_style
        self.is_slow = is_slow
        self.memory = MemoryStream(name)

    def perceive(self, event):
        """感知环境并存入记忆"""
        clean_event = re.sub(r"\*\*Thought:\*\*.*?\*\*Response:\*\*", "", event, flags=re.DOTALL).strip()
        self.memory.add_memory(clean_event)

    def think_and_act(self, current_context):
        """
        核心循环：检索记忆 -> 思考(CoT) -> 说话
        """
        # 1. 检索相关记忆
        related_memories = self.memory.retrieve(current_context)
        memory_text = "\n".join([f"- {m}" for m in related_memories])

        # 2. 构建 Prompt
        prompt = f"""
        【角色设定】
        你是 {self.name}。
        你的性格设定: {self.persona}
        你的说话风格: {self.speech_style}

        【相关记忆】
        {memory_text}

        【当前情况】
        {current_context}

        【指令】
        1. 请首先进行内心思考 (Thought)，结合记忆分析局势。
        2. 然后输出口头回复 (Response)。
        3. 必须使用中文。
        4. 严格遵守格式：
        **Thought:**
        (你的思考)
        **Response:**
        (你的回复)
        """

        # 3. 调用大模型
        full_response = call_llm(prompt)
        
        # 4. 解析输出 (Robust Parsing)
        thought = "（未检测到思考过程）"
        speech = full_response # 默认值为原始内容，防止正则匹配失败

        # 正则表达式解释：
        # \*\*Thought:\*\* -> 匹配 **Thought:** 标签
        # (.*?)             -> 非贪婪匹配思考内容 (Group 1)
        # \*\*Response:\*\* -> 匹配 **Response:** 标签
        # (.*)              -> 匹配剩余所有内容作为回复 (Group 2)
        # re.DOTALL         -> 让 . 号也能匹配换行符
        pattern = re.compile(r"\*\*Thought:\*\*(.*?)\*\*Response:\*\*(.*)", re.DOTALL | re.IGNORECASE)
        
        match = pattern.search(full_response)
        
        if match:
            thought = match.group(1).strip()
            speech = match.group(2).strip()
        else:
            # 备用方案：如果 LLM 没写**，只写了 Response:
            if "Response:" in full_response:
                parts = full_response.split("Response:", 1)
                thought = parts[0].replace("Thought:", "").strip()
                speech = parts[1].strip()

        print(f"\n💭 [{self.name} 的内心独白]: {thought}")
        
        # 模拟闪电的反应慢
        if self.is_slow:
            time.sleep(2)
            print(f"🕒 ...{self.name} 反应非常缓慢...")
            time.sleep(2)

        return speech