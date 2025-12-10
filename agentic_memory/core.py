import chromadb
import uuid
import json
import time
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from .prompts import NOTE_CONSTRUCTION_PROMPT, LINK_GENERATION_PROMPT, MEMORY_EVOLUTION_PROMPT
from utils import call_llm 

class AgenticMemorySystem:
    def __init__(self, agent_name: str, db_path: str = "./db"):
        self.agent_name = agent_name
        
        # 1. 初始化向量模型 (论文推荐使用 dense retriever)
        # 第一次运行会自动下载模型 (约 80MB)
        print(f"[{self.agent_name}] 正在加载 Embedding 模型...")
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # 2. 初始化 ChromaDB
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(name=f"amem_{agent_name}")

    def _get_embedding(self, text: str) -> List[float]:
        return self.encoder.encode(text).tolist()

    def _parse_json_response(self, response: str) -> Dict:
        """鲁棒的 JSON 解析器"""
        try:
            # 尝试清洗 markdown 标记
            clean_str = response.replace("```json", "").replace("```", "").strip()
            if not clean_str: return {}
            return json.loads(clean_str)
        except json.JSONDecodeError:
            print(f"⚠️ JSON Parsing Failed. Raw: {response[:50]}...")
            return {}

    def add_memory(self, content: str, timestamp: float = None):
        """
        A-MEM 核心写入流程：Note -> Link -> Evolve -> Store
        """
        if timestamp is None:
            timestamp = time.time()

        print(f"🧠 [{self.agent_name}] 正在构建结构化笔记 (A-MEM Processing)...")
        
        # === Phase 1: Note Construction (笔记构造) ===
        # 调用 LLM 生成 Context, Keywords, Tags
        prompt = NOTE_CONSTRUCTION_PROMPT.format(content=content)
        
        # [修改点 1] 传入 system_prompt 防止模型角色扮演
        raw_analysis = call_llm(
            prompt, 
            system_prompt="You are a helpful AI assistant specialized in text analysis and JSON generation.",
            json_mode=True
        )
        
        note_data = self._parse_json_response(raw_analysis)
        
        # 兜底逻辑：如果解析失败，使用默认值
        context = note_data.get("context", content[:50])
        keywords = note_data.get("keywords", [])
        tags = note_data.get("tags", [])
        
        # 构建富文本用于 Embedding (Content + Context + Keywords)
        rich_text = f"{content} | Context: {context} | Keywords: {', '.join(keywords)}"
        embedding = self._get_embedding(rich_text)
        new_id = str(uuid.uuid4())

        # === Phase 2: Link Generation (动态链接) ===
        # 先检索最近的 k 个记忆
        neighbors = self.retrieve(query=rich_text, k=3)
        linked_ids = []
        
        if neighbors:
            neighbors_info = json.dumps([{ 'id': n['id'], 'content': n['content'], 'context': n['context'] } for n in neighbors], ensure_ascii=False)
            link_prompt = LINK_GENERATION_PROMPT.format(
                new_context=context, new_content=content, new_keywords=keywords, neighbors_info=neighbors_info
            )
            
            # [修改点 2] 传入 system_prompt
            link_res_raw = call_llm(
                link_prompt,
                system_prompt="You are a helpful AI assistant specialized in text analysis and JSON generation.",
                json_mode=True
            )
            link_res = self._parse_json_response(link_res_raw)
            linked_ids = link_res.get("linked_memory_ids", [])

        # === Phase 3: Memory Evolution (记忆进化) ===
        # 检查是否需要更新邻居的 Tags 或 Context
        if neighbors:
            evolve_prompt = MEMORY_EVOLUTION_PROMPT.format(new_content=content, neighbors_info=neighbors_info)
            
            # [修改点 3] 传入 system_prompt
            evolve_res_raw = call_llm(
                evolve_prompt,
                system_prompt="You are a helpful AI assistant specialized in text analysis and JSON generation.",
                json_mode=True
            )
            evolve_res = self._parse_json_response(evolve_res_raw)
            updates = evolve_res.get("updates", [])
            
            for update in updates:
                target_id = update.get("id")
                if target_id:
                    print(f"🧬 [{self.agent_name}] 记忆进化: 更新记忆 {target_id[:4]} 的 Context -> {str(update.get('new_context'))[:20]}...")
                    # 注意：在真实生产环境中，ChromaDB 更新 metadata 需要获取原始数据并覆盖，这里仅作演示打印
                    # self.collection.update(...)

        # === Phase 4: Storage (落库) ===
        self.collection.add(
            documents=[content],
            embeddings=[embedding],
            metadatas=[{
                "context": context,
                "keywords": ",".join(keywords),
                "tags": ",".join(tags),
                "linked_ids": ",".join(linked_ids),
                "timestamp": timestamp
            }],
            ids=[new_id]
        )
        print(f"✅ 记忆已存储 [Tags: {tags}]")

    def retrieve(self, query: str, k: int = 5) -> List[Dict]:
        """
        检索逻辑：Embedding Search
        """
        query_embedding = self._get_embedding(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k
        )
        
        cleaned_results = []
        if results['ids']:
            for i in range(len(results['ids'][0])):
                # 处理 metadata 可能为空的情况
                meta = results['metadatas'][0][i] if results['metadatas'][0][i] else {}
                cleaned_results.append({
                    "id": results['ids'][0][i],
                    "content": results['documents'][0][i],
                    "context": meta.get("context", ""),
                    "tags": meta.get("tags", "").split(","),
                    "score": results['distances'][0][i] if 'distances' in results else 0
                })
        return cleaned_results