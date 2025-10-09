# 處理 Qdrant 的交互，包括初始化和向量檢索。

from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
from app.config import QDRANT_URL, QDRANT_KEY, QDRANT_COLLECTION_NAME, QDRANT_EMBEDDING_MODEL_NAME

class QdrantService:
    def __init__(self):
        self.client = None
        self.embedding_model = None
        self.collection_name = QDRANT_COLLECTION_NAME

        # 检查配置是否存在
        if not QDRANT_URL or not QDRANT_KEY:
            print("警告: QDRANT_URL 或 QDRANT_KEY 未在 .env 中设置。向量检索将不可用。")
            return

        try:
            self.client = QdrantClient(
                url=QDRANT_URL, 
                api_key=QDRANT_KEY,
                timeout=20
            )
            
            # 检查 collection 是否真实存在
            if not self.client.collection_exists(collection_name=self.collection_name):
                raise RuntimeError(f"Qdrant collection '{self.collection_name}' does not exist on the cloud. Please run the seed script first.")
            
            # 嵌入模型
            self.embedding_model = SentenceTransformer(QDRANT_EMBEDDING_MODEL_NAME)
            
            print(f"Qdrant client initialized and connected to existing collection '{self.collection_name}'.")
        
        except RuntimeError as r_err:
             print(f"配置错误: {r_err}")
             self.client = None

        except Exception as e:
            print(f"无法连接到 Qdrant Cloud。向量检索将不可用: {repr(e)}")
            self.client = None

    def retrieve_exemplars(self, query_text: str, limit: int = 3) -> List[Dict[str, Any]]:
        if not self.client or not self.embedding_model:
            print("Qdrant 客户端未初始化，无法检索 exemplars。")
            return []
        
        try:
            query_vector = self.embedding_model.encode(query_text).tolist()
            search_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="source",
                        match=models.MatchAny(any=["golden_samples", "synthetic_data"])
                    )
                ]
            )
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=search_filter,
                limit=limit
            )
            return [hit.payload for hit in search_result if hit.payload]
        except Exception as e:
            print(f"Error retrieving exemplars from Qdrant: {e}")
            return []