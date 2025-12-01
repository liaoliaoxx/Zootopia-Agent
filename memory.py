import chromadb
from chromadb.utils import embedding_functions
import uuid
import time
import re

class MemoryStream:
    def __init__(self, agent_name):
        self.agent_name = agent_name
        
        # 只保留字母、数字和下划线
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', agent_name)
        
        # 使用本地持久化存储
        self.client = chromadb.PersistentClient(path=f"./db/{safe_name}")
        
        # 使用默认 embedding 模型
        self.emb_fn = embedding_functions.DefaultEmbeddingFunction()
        
        # 创建 collection 时使用清洗后的 safe_name
        self.collection = self.client.get_or_create_collection(
            name=f"memory_{safe_name}",
            embedding_function=self.emb_fn
        )

    def add_memory(self, description, importance=1.0):
        """
        写入记忆
        """
        self.collection.add(
            documents=[description],
            metadatas=[{
                "timestamp": time.time(),
                "importance": importance,
                "type": "observation"
            }],
            ids=[str(uuid.uuid4())]
        )
        print(f"🧠 [{self.agent_name} 记住了]: {description}")

    def retrieve(self, query, n_results=3):
        """
        检索记忆
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        memories = results['documents'][0] if results['documents'] else []
        return memories