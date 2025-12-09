import json
import os

class ExperienceManager:
    def __init__(self, filepath="tips.json"):
        self.filepath = filepath
        self.tips = self._load_tips()

    def _load_tips(self):
        """加载经验库"""
        if not os.path.exists(self.filepath):
            return []
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading tips: {e}")
            return []

    def retrieve_relevant_tips(self, context, current_agent_name):
        """
        根据上下文检索相关的 Tips (Coarse-to-Fine Retrieval)
        论文核心：Retrieve task-relevant experiences and tips to support planning.
        """
        relevant_tips = []
        
        # 简单的关键词匹配逻辑 (可升级为向量检索)
        # 1. 检查当前对话上下文里是否提到了某些关键词
        # 2. 检查是否有针对当前角色的 Tip (比如我是朱迪，我应该看关于尼克的Tip)
        
        for tip in self.tips:
            # 检查 tags 是否出现在 context 中
            for tag in tip["tags"]:
                if tag in context:
                    relevant_tips.append(tip["content"])
                    break
        
        return relevant_tips

# 测试代码
if __name__ == "__main__":
    mgr = ExperienceManager()
    print(mgr.retrieve_relevant_tips("我正在和闪电说话，他太慢了", "Judy"))