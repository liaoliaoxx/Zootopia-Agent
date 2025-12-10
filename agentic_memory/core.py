import chromadb
import uuid
import json
import time
import os
from typing import List, Dict, Any
# 强制使用国内镜像
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
from sentence_transformers import SentenceTransformer
from .prompts import NOTE_CONSTRUCTION_PROMPT, LINK_GENERATION_PROMPT, MEMORY_EVOLUTION_PROMPT
from utils import call_llm 

class AgenticMemorySystem:
    def __init__(self, agent_name: str, db_path: str = "./db"):
        self.agent_name = agent_name
        
        print(f"[{self.agent_name}] 正在加载 Embedding 模型...")
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(name=f"amem_{agent_name}")

    def _get_embedding(self, text: str) -> List[float]:
        return self.encoder.encode(text).tolist()

    def _parse_json_response(self, response: str) -> Dict:
        """鲁棒的 JSON 解析器 (增强版)"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            try:
                if "```" in response:
                    start = response.find("{")
                    end = response.rfind("}") + 1
                    if start != -1 and end != 0:
                        return json.loads(response[start:end])
                
                start = response.find("{")
                end = response.rfind("}") + 1
                if start != -1 and end != 0:
                    return json.loads(response[start:end])
                
                print(f"⚠️ JSON Parsing Failed. Raw: {response}")
                return {}
            except Exception as e:
                print(f"⚠️ Critical JSON Error: {e}")
                return {}

    def add_memory(self, content: str, timestamp: float = None):
        """
        A-MEM 核心写入流程：Note -> Link -> Evolve -> Store
        """
        if timestamp is None:
            timestamp = time.time()

        print(f"🧠 [{self.agent_name}] 正在构建结构化笔记 (A-MEM Processing)...")
        
        # === Phase 1: Note Construction (笔记构造) ===
        prompt = NOTE_CONSTRUCTION_PROMPT.format(content=content)
        raw_analysis = call_llm(
            prompt, 
            system_prompt="You are a helpful AI assistant specialized in text analysis and JSON generation.",
            json_mode=True
        )
        note_data = self._parse_json_response(raw_analysis)
        
        context = note_data.get("context", content[:50])
        keywords = note_data.get("keywords", [])
        tags = note_data.get("tags", [])
        
        # 构建 Embedding
        rich_text = f"{content} | Context: {context} | Keywords: {', '.join(keywords)}"
        embedding = self._get_embedding(rich_text)
        new_id = str(uuid.uuid4())

        # === Phase 2: Link Generation (动态链接) ===
        neighbors = self.retrieve(query=rich_text, k=3)
        linked_ids = []
        
        if neighbors:
            neighbors_info = json.dumps([{ 'id': n['id'], 'content': n['content'], 'context': n['context'] } for n in neighbors], ensure_ascii=False)
            link_prompt = LINK_GENERATION_PROMPT.format(
                new_context=context, new_content=content, new_keywords=keywords, neighbors_info=neighbors_info
            )
            
            link_res_raw = call_llm(
                link_prompt,
                system_prompt="You are a helpful AI assistant specialized in text analysis and JSON generation.",
                json_mode=True
            )
            link_res = self._parse_json_response(link_res_raw)
            linked_ids = link_res.get("linked_memory_ids", [])

        # === Phase 3: Memory Evolution (记忆进化 - 真实更新版) ===
        if neighbors:
            evolve_prompt = MEMORY_EVOLUTION_PROMPT.format(new_content=content, neighbors_info=neighbors_info)
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
                    # 1. 先从数据库获取当前的完整 Metadata (防止覆盖丢失 timestamp 等字段)
                    existing_record = self.collection.get(ids=[target_id])
                    
                    if existing_record and existing_record['metadatas']:
                        current_metadata = existing_record['metadatas'][0]
                        
                        # 2. 准备更新的数据
                        new_context_val = update.get('new_context')
                        new_tags_val = update.get('new_tags')
                        
                        has_change = False
                        
                        # 更新 Context
                        if new_context_val and new_context_val != current_metadata.get('context'):
                            print(f"🧬 [{self.agent_name}] 记忆进化: ID:{target_id[:4]} Context 更新 -> {str(new_context_val)[:30]}...")
                            current_metadata['context'] = new_context_val
                            has_change = True
                            
                        # 更新 Tags
                        if new_tags_val:
                            # 确保格式统一为逗号分隔的字符串
                            if isinstance(new_tags_val, list):
                                new_tags_str = ",".join(new_tags_val)
                            else:
                                new_tags_str = str(new_tags_val)
                                
                            if new_tags_str != current_metadata.get('tags'):
                                print(f"🏷️ [{self.agent_name}] 标签进化: ID:{target_id[:4]} Tags 更新 -> {new_tags_str}")
                                current_metadata['tags'] = new_tags_str
                                has_change = True
                        
                        # 3. 执行真实的 Update 操作
                        if has_change:
                            self.collection.update(
                                ids=[target_id],
                                metadatas=[current_metadata]
                                # 注意：我们只更新 metadata，保持原始 embedding 不变，
                                # 这样既保留了原始记忆的“物理位置”，又更新了它的“语义解释”。
                            )

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
        query_embedding = self._get_embedding(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k
        )
        
        cleaned_results = []
        if results['ids']:
            for i in range(len(results['ids'][0])):
                meta = results['metadatas'][0][i] if results['metadatas'][0][i] else {}
                cleaned_results.append({
                    "id": results['ids'][0][i],
                    "content": results['documents'][0][i],
                    "context": meta.get("context", ""),
                    "tags": meta.get("tags", "").split(","),
                    "score": results['distances'][0][i] if 'distances' in results else 0
                })
        return cleaned_results