# 處理 Qdrant 的交互，包括初始化和向量檢索。

from qdrant_client import QdrantClient, models
from qdrant_client.models import PointStruct, PayloadSchemaType
from fastembed import TextEmbedding
from typing import List, Dict, Any
import uuid 
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
            self.embedding_model = TextEmbedding(QDRANT_EMBEDDING_MODEL_NAME)
            
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
        

    def upsert_exemplars(self, points_data: List[Dict[str, Any]]):
        """
        將多個數據點向量化並插入/更新到 Qdrant。
        points_data: 一個字典列表，每個字典至少包含 'text' 和 'payload'。
        """
        if not self.client or not self.embedding_model:
            print("Qdrant 客户端未初始化，无法 upsert exemplars。")
            return
        
        try:
            points_to_upsert = []
            for item in points_data:
                vector = self.embedding_model.encode(item['text']).tolist()
                payload = item.get('payload', {})
                
                point_id = item.get('db_id')
                if not point_id:
                    print(f"Skipping item because it has no 'db_id': {item}")
                    continue
                
                points_to_upsert.append(
                    PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=payload
                    )
                )

            if points_to_upsert:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points_to_upsert,
                    wait=True # 確保操作完成
                )
                print(f"Upserted {len(points_to_upsert)} points to Qdrant collection '{self.collection_name}'.")

        except Exception as e:
            print(f"Error upserting exemplars to Qdrant: {e}")

    async def delete_exemplar_by_db_id(self, db_id: int):
        """根據數據庫 ID 從 Qdrant 中刪除 point。"""
        if not self.client:
            print("Qdrant 客户端未初始化。")
            return
        
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="db_id", # 假設你在 payload 存了這個 key
                                match=models.MatchValue(value=db_id),
                            )
                        ]
                    )
                ),
            )
            print(f"Deleted points with DB ID {db_id} from Qdrant.")
        except Exception as e:
            print(f"Error deleting exemplar from Qdrant: {e}")
            raise

    async def update_exemplar_by_db_id(self, db_id: int, new_text: str, new_payload: Dict[str, Any]):
        """
        通過先刪除後新增的方式更新 Qdrant 中的向量，因為文本變了，向量也必須重新計算。
        """
        # 1. 刪除舊的向量
        await self.delete_exemplar_by_db_id(db_id)
        
        # 2. 插入新的向量
        print(f"Re-inserting updated data for DB ID {db_id} into Qdrant.")
        # 確保新的 payload 裡也有 db_id
        if 'db_id' not in new_payload:
            new_payload['db_id'] = db_id
            
        self.upsert_exemplars([{"text": new_text, "payload": new_payload}])