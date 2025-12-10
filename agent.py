from agentic_memory.core import AgenticMemorySystem
from utils import call_llm
from experience import ExperienceManager
import time
import re

class ZootopiaAgent:
    def __init__(self, name, persona, speech_style, is_slow=False):
        self.name = name
        self.persona = persona
        self.speech_style = speech_style
        self.is_slow = is_slow
        
        safe_name = name.replace(" ", "_")
        
        # 1. 记忆系统 (A-MEM)
        self.memory = AgenticMemorySystem(agent_name=safe_name)
        
        # 2. 经验系统 (CFGM)
        # 注意：ExperienceManager 内部会加载模型，如果创建多个 Agent，
        # 为了节省内存，可以在 main.py 创建一个全局 manager 传进来。
        # 但为了代码解耦，这里每个 Agent 实例化一个也可以，
        # 因为 SentenceTransformer 内部有缓存机制，不会重复下载模型。
        self.exp_manager = ExperienceManager()

    def perceive(self, event):
        """
        感知环境并存入记忆
        包含：数据清洗（去除思维链、去除冗余省略号）
        """
        # 1. 清洗思维链
        clean_event = re.sub(r"\*\*Thought:\*\*.*?\*\*Response:\*\*", "", event, flags=re.DOTALL).strip()
        
        # 2. 清洗口癖
        clean_event = re.sub(r"[\.。…]{2,}", "", clean_event)
        clean_event = clean_event.replace("  ", " ").strip()

        # 3. 存入 A-MEM (Core Logic)
        self.memory.add_memory(clean_event)

    def think_and_act(self, current_context):
        """
        核心循环：检索记忆 -> 思考(CoT) -> 说话
        """
        # 1. A-MEM 记忆检索 (Retrieve Relevant Memories)
        related_memories = self.memory.retrieve(current_context, k=3)
        memory_text = "\n".join([
            f"- [标签:{','.join(m['tags'])}] {m['content']} (背景:{m['context']})" 
            for m in related_memories
        ])

        # 2. CFGM 经验检索 (Retrieve Relevant Tips via Vector Search)
        # 这里的 k=2 表示只取最相关的 2 条锦囊，避免 Prompt 过长
        retrieved_tips = self.exp_manager.retrieve_relevant_tips(current_context, self.name, k=2)
        
        tips_text = ""
        if retrieved_tips:
            tips_text = "【🌟 经验锦囊 (Relevant Tips)】\n" + "\n".join([f"💡 {tip}" for tip in retrieved_tips])
        else:
            tips_text = "（暂无相关经验提示）"

        # 3. 构建 Prompt
        prompt = f"""
        【角色设定】
        你是 {self.name}。
        你的性格设定: {self.persona}
        你的说话风格: {self.speech_style}

        {tips_text}

        【相关记忆】
        {memory_text}

        【当前情况】
        {current_context}

        【指令】
        1. 请首先进行内心思考 (Thought)。**请务必参考【经验锦囊】中的建议**（如果有），调整你的策略。
        2. 然后输出口头回复 (Response)。
        3. 必须使用中文。
        4. 严格遵守格式：
        **Thought:**
        (你的思考，如果参考了Tips请明确提到)
        **Response:**
        (你的回复)
        """

        # 4. 调用大模型
        full_response = call_llm(prompt)
        
        # 5. 解析输出
        thought = "（未检测到思考过程）"
        speech = full_response

        pattern = re.compile(r"\*\*Thought:\*\*(.*?)\*\*Response:\*\*(.*)", re.DOTALL | re.IGNORECASE)
        match = pattern.search(full_response)
        
        if match:
            thought = match.group(1).strip()
            speech = match.group(2).strip()
        else:
            if "Response:" in full_response:
                parts = full_response.split("Response:", 1)
                thought = parts[0].replace("Thought:", "").strip()
                speech = parts[1].strip()

        print(f"\n💭 [{self.name} 的内心独白]: {thought}")
        
        if self.is_slow:
            time.sleep(2)
            print(f"🕒 ...{self.name} 反应非常缓慢...")
            time.sleep(2)

        return thought, speech