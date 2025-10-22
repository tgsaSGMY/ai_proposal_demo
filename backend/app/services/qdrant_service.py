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


    def retrieve_exemplar_ids(self, 
                              query_text: str, 
                              grant_id: str, 
                              template_id: str, 
                              section_id: str, 
                              limit: int = 3) -> List[int]:
        """
        根據語意相似度和精準的元數據過濾條件，從 Qdrant 檢索最相關範例的數據庫 ID 列表。
        """
        if not self.client or not self.embedding_model:
            print("Qdrant 客户端未初始化，无法检索 exemplars。")
            return []
        
        try:
            query_vector = list(self.embedding_model.embed([query_text]))[0]
            
            # 建立一個包含所有精準匹配條件的複合過濾器
            search_filter = models.Filter(
                must=[
                    # 固定的 source_type 篩選
                    models.FieldCondition(
                        key="source_type",
                        match=models.MatchAny(any=["golden_samples", "synthetic_data"])
                    ),
                    # 來自請求的動態過濾條件
                    models.FieldCondition(key="grant_id", match=models.MatchValue(value=grant_id)),
                    models.FieldCondition(key="template_id", match=models.MatchValue(value=template_id)),
                    models.FieldCondition(key="section_id", match=models.MatchValue(value=section_id))
                ]
            )
            
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=search_filter,
                limit=limit,
                with_payload=False, # 優化：我們只需要 ID，不需要 payload
                with_vectors=False   # 優化：我們不需要向量本身
            )
            
            # 只返回數據庫 ID (point.id)
            return [hit.id for hit in search_result]

        except Exception as e:
            print(f"Error retrieving exemplar IDs from Qdrant: {e}")
            return []
        
    def upsert_exemplars(self, points_data: List[Dict[str, Any]]):
        """
        將多個數據點向量化並插入/更新到 Qdrant。
        points_data: 一個字典列表，每個字典至少包含 'db_id', 'text' 和 'payload'。
        """
        if not self.client or not self.embedding_model:
            print("Qdrant 客户端未初始化，无法 upsert exemplars。")
            return
        
        try:
            points_to_upsert = []
            for item in points_data:
                vector = list(self.embedding_model.embed([item['text']]))[0]
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
                    wait=True
                )
                print(f"Upserted {len(points_to_upsert)} points to Qdrant collection '{self.collection_name}'.")

        except Exception as e:
            print(f"Error upserting exemplars to Qdrant: {e}")
    
    def delete_exemplar_by_db_id(self, db_id: int):
        """根據數據庫 ID 從 Qdrant 中刪除 point。"""
        if not self.client:
            print("Qdrant 客户端未初始化。")
            return
        
        try:
            # 直接使用 point id 進行刪除，更高效
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[db_id],
                wait=True
            )
        except Exception as e:
            print(f"Error deleting exemplar from Qdrant: {e}")
            raise

    def update_exemplar_by_db_id(self, db_id: int, new_text: str, new_payload: Dict[str, Any]):
        """
        通過先刪除後新增的方式更新 Qdrant 中的向量，因為文本變了，向量也必須重新計算。
        """
        # 1. 刪除舊的向量
        self.delete_exemplar_by_db_id(db_id)
        
        # 2. 插入新的向量
        print(f"Re-inserting updated data for DB ID {db_id} into Qdrant.")
        if 'db_id' not in new_payload:
            new_payload['db_id'] = db_id

        item_to_upsert = {
            "text": new_text,
            "payload": new_payload,
            "db_id": db_id  
        }
    
        self.upsert_exemplars([item_to_upsert])