import json
import os
import chromadb
import uuid
from typing import List
from sentence_transformers import SentenceTransformer

class ExperienceManager:
    def __init__(self, filepath="tips.json", db_path="./db"):
        self.filepath = filepath
        self.db_path = db_path
        
        # 1. 初始化向量模型 (与 A-MEM 保持一致，复用缓存)
        print("📚 [ExperienceManager] 正在加载 Embedding 模型...")
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # 2. 初始化 ChromaDB (专门用于存储 Tips)
        self.client = chromadb.PersistentClient(path=self.db_path)
        self.collection = self.client.get_or_create_collection(name="cfgm_tips_store")
        
        # 3. 启动时自动同步 tips.json 到数据库
        self._sync_tips_to_db()

    def _sync_tips_to_db(self):
        """
        将 tips.json 中的内容向量化并存入 ChromaDB
        (实现了 CFGM 论文中的 Offline Knowledge Construction)
        """
        if not os.path.exists(self.filepath):
            print(f"⚠️ Warning: {self.filepath} not found.")
            return

        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                tips_data = json.load(f)
            
            # 检查当前库里有多少数据，如果数量为0则全部写入
            # (生产环境可以做更复杂的增量更新，这里做简单全量检查)
            if self.collection.count() == 0:
                print(f"📥 [ExperienceManager] 正在将 {len(tips_data)} 条经验锦囊注入向量库...")
                
                documents = []
                metadatas = []
                ids = []
                embeddings = []

                for tip in tips_data:
                    # 组合 content 和 tags 以获得更丰富的语义表示
                    # 例如: "Tags: 闪电, 慢. Content: 不要催促..."
                    combined_text = f"Tags: {', '.join(tip.get('tags', []))}. Content: {tip['content']}"
                    
                    documents.append(tip['content'])
                    metadatas.append({"tags": ",".join(tip.get('tags', []))})
                    ids.append(str(uuid.uuid4()))
                    # 生成向量
                    embeddings.append(self.encoder.encode(combined_text).tolist())

                # 批量写入
                self.collection.add(
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    ids=ids
                )
                print("✅ 经验库构建完成！")
            else:
                print("📚 经验库已就绪 (无需重复注入).")

        except Exception as e:
            print(f"❌ Error loading tips: {e}")

    def retrieve_relevant_tips(self, context: str, current_agent_name: str, k: int = 2) -> List[str]:
        """
        基于语义检索相关的 Tips
        (CFGM Online Retrieval Phase)
        """
        if self.collection.count() == 0:
            return []

        # 1. 将当前的上下文 (Current Context) 转化为向量
        # 我们把 agent 的名字也加进去，增加上下文相关性
        query_text = f"Current Agent: {current_agent_name}. Situation: {context}"
        query_embedding = self.encoder.encode(query_text).tolist()

        # 2. 在向量库中搜索最相似的 k 条 Tip
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k
        )

        relevant_tips = []
        if results['documents']:
            # results['documents'] 是一个列表的列表 [[doc1, doc2]]
            for i, tip_content in enumerate(results['documents'][0]):
                # 可选：根据距离过滤 (distance 越小越相似)
                # score = results['distances'][0][i]
                # if score < 1.5: ...
                relevant_tips.append(tip_content)
        
        return relevant_tips

# 测试代码
if __name__ == "__main__":
    mgr = ExperienceManager()
    # 测试语义泛化能力：注意这里没提“闪电”，只提了“慢”和“车管所”
    tips = mgr.retrieve_relevant_tips("我在车管所办事，办事员动作特别慢，我快急死了", "Judy")
    print("\n🔍 检索测试结果:")
    for t in tips:
        print(f"- {t}")