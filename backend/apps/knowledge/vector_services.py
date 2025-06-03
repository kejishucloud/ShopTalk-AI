"""
向量数据库服务
支持多种向量数据库：Milvus, Pinecone, Qdrant, Chroma
"""
import json
import logging
import numpy as np
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
import hashlib
import time

from .config import (
    get_vector_db_config, 
    get_embedding_model_config,
    get_chunking_config,
    CACHE_CONFIG
)

logger = logging.getLogger(__name__)

class EmbeddingService:
    """向量化服务"""
    
    def __init__(self, model_name: str = 'default'):
        self.model_config = get_embedding_model_config(model_name)
        self.model = None
        self.model_name = model_name
        self._load_model()
    
    def _load_model(self):
        """加载向量化模型"""
        try:
            self.model = SentenceTransformer(
                self.model_config['model_name'],
                device=self.model_config['device']
            )
            logger.info(f"加载向量化模型成功: {self.model_config['model_name']}")
        except Exception as e:
            logger.error(f"加载向量化模型失败: {e}")
            raise
    
    def encode(self, texts: List[str]) -> np.ndarray:
        """文本向量化"""
        if not self.model:
            raise RuntimeError("向量化模型未加载")
        
        try:
            # 预处理文本
            processed_texts = []
            for text in texts:
                # 截断过长文本
                if len(text) > self.model_config['max_seq_length']:
                    text = text[:self.model_config['max_seq_length']]
                processed_texts.append(text.strip())
            
            # 生成向量
            embeddings = self.model.encode(
                processed_texts,
                batch_size=32,
                normalize_embeddings=True,
                show_progress_bar=False
            )
            
            return embeddings
        except Exception as e:
            logger.error(f"文本向量化失败: {e}")
            raise
    
    def encode_single(self, text: str) -> np.ndarray:
        """单个文本向量化"""
        return self.encode([text])[0]
    
    def get_dimension(self) -> int:
        """获取向量维度"""
        return self.model_config['dimension']

class BaseVectorStore(ABC):
    """向量数据库基类"""
    
    def __init__(self):
        self.config = get_vector_db_config()
    
    @abstractmethod
    def create_collection(self, collection_name: str, dimension: int) -> bool:
        """创建集合"""
        pass
    
    @abstractmethod
    def insert_vectors(self, collection_name: str, vectors: List[Dict]) -> bool:
        """插入向量数据"""
        pass
    
    @abstractmethod
    def search_vectors(self, collection_name: str, query_vector: np.ndarray, 
                      top_k: int = 10, filter_expr: str = None) -> List[Dict]:
        """搜索向量"""
        pass
    
    @abstractmethod
    def delete_vectors(self, collection_name: str, ids: List[str]) -> bool:
        """删除向量"""
        pass
    
    @abstractmethod
    def collection_exists(self, collection_name: str) -> bool:
        """检查集合是否存在"""
        pass

class MilvusVectorStore(BaseVectorStore):
    """Milvus向量数据库服务"""
    
    def __init__(self):
        super().__init__()
        self.client = None
        self._connect()
    
    def _connect(self):
        """连接Milvus"""
        try:
            from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType
            
            connections.connect(
                alias="default",
                host=self.config['host'],
                port=self.config['port'],
                user=self.config.get('user', ''),
                password=self.config.get('password', ''),
                secure=self.config.get('secure', False)
            )
            logger.info("连接Milvus成功")
            
        except Exception as e:
            logger.error(f"连接Milvus失败: {e}")
            raise
    
    def create_collection(self, collection_name: str, dimension: int) -> bool:
        """创建Milvus集合"""
        try:
            from pymilvus import FieldSchema, CollectionSchema, DataType, Collection
            
            full_name = f"{self.config['collection_prefix']}{collection_name}"
            
            if self.collection_exists(full_name):
                return True
            
            # 定义字段结构
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=64, is_primary=True),
                FieldSchema(name="content_type", dtype=DataType.VARCHAR, max_length=50),
                FieldSchema(name="content_id", dtype=DataType.INT64),
                FieldSchema(name="text_chunk", dtype=DataType.VARCHAR, max_length=8192),
                FieldSchema(name="chunk_index", dtype=DataType.INT64),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dimension),
                FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=4096),
                FieldSchema(name="created_at", dtype=DataType.INT64),
            ]
            
            schema = CollectionSchema(fields=fields, description=f"知识库向量集合: {collection_name}")
            collection = Collection(name=full_name, schema=schema)
            
            # 创建索引
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024}
            }
            collection.create_index(field_name="embedding", index_params=index_params)
            
            logger.info(f"创建Milvus集合成功: {full_name}")
            return True
            
        except Exception as e:
            logger.error(f"创建Milvus集合失败: {e}")
            return False
    
    def insert_vectors(self, collection_name: str, vectors: List[Dict]) -> bool:
        """插入向量到Milvus"""
        try:
            from pymilvus import Collection
            
            full_name = f"{self.config['collection_prefix']}{collection_name}"
            collection = Collection(full_name)
            
            # 准备数据
            data = []
            for vector_data in vectors:
                data.append([
                    vector_data['id'],
                    vector_data['content_type'],
                    vector_data['content_id'],
                    vector_data['text_chunk'],
                    vector_data['chunk_index'],
                    vector_data['embedding'].tolist(),
                    json.dumps(vector_data.get('metadata', {})),
                    int(time.time() * 1000)
                ])
            
            # 插入数据
            collection.insert(data)
            collection.flush()
            
            logger.info(f"插入{len(vectors)}个向量到{full_name}")
            return True
            
        except Exception as e:
            logger.error(f"插入向量到Milvus失败: {e}")
            return False
    
    def search_vectors(self, collection_name: str, query_vector: np.ndarray, 
                      top_k: int = 10, filter_expr: str = None) -> List[Dict]:
        """在Milvus中搜索向量"""
        try:
            from pymilvus import Collection
            
            full_name = f"{self.config['collection_prefix']}{collection_name}"
            collection = Collection(full_name)
            collection.load()
            
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10}
            }
            
            results = collection.search(
                data=[query_vector.tolist()],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                expr=filter_expr,
                output_fields=["content_type", "content_id", "text_chunk", "chunk_index", "metadata"]
            )
            
            search_results = []
            for hits in results:
                for hit in hits:
                    result = {
                        'id': hit.entity.get('id'),
                        'content_type': hit.entity.get('content_type'),
                        'content_id': hit.entity.get('content_id'),
                        'text_chunk': hit.entity.get('text_chunk'),
                        'chunk_index': hit.entity.get('chunk_index'),
                        'metadata': json.loads(hit.entity.get('metadata', '{}')),
                        'score': hit.score
                    }
                    search_results.append(result)
            
            return search_results
            
        except Exception as e:
            logger.error(f"Milvus向量搜索失败: {e}")
            return []
    
    def delete_vectors(self, collection_name: str, ids: List[str]) -> bool:
        """从Milvus删除向量"""
        try:
            from pymilvus import Collection
            
            full_name = f"{self.config['collection_prefix']}{collection_name}"
            collection = Collection(full_name)
            
            id_expr = f"id in {ids}"
            collection.delete(id_expr)
            collection.flush()
            
            logger.info(f"从{full_name}删除{len(ids)}个向量")
            return True
            
        except Exception as e:
            logger.error(f"从Milvus删除向量失败: {e}")
            return False
    
    def collection_exists(self, collection_name: str) -> bool:
        """检查Milvus集合是否存在"""
        try:
            from pymilvus import utility
            
            full_name = f"{self.config['collection_prefix']}{collection_name}"
            return utility.has_collection(full_name)
            
        except Exception as e:
            logger.error(f"检查Milvus集合存在性失败: {e}")
            return False

class PineconeVectorStore(BaseVectorStore):
    """Pinecone向量数据库服务"""
    
    def __init__(self):
        super().__init__()
        self.client = None
        self._connect()
    
    def _connect(self):
        """连接Pinecone"""
        try:
            import pinecone
            
            pinecone.init(
                api_key=self.config['api_key'],
                environment=self.config['environment']
            )
            self.client = pinecone
            logger.info("连接Pinecone成功")
            
        except Exception as e:
            logger.error(f"连接Pinecone失败: {e}")
            raise
    
    def create_collection(self, collection_name: str, dimension: int) -> bool:
        """创建Pinecone索引"""
        try:
            index_name = f"{self.config['index_prefix']}{collection_name}"
            
            if index_name in self.client.list_indexes():
                return True
            
            self.client.create_index(
                name=index_name,
                dimension=dimension,
                metric='cosine'
            )
            
            logger.info(f"创建Pinecone索引成功: {index_name}")
            return True
            
        except Exception as e:
            logger.error(f"创建Pinecone索引失败: {e}")
            return False
    
    def insert_vectors(self, collection_name: str, vectors: List[Dict]) -> bool:
        """插入向量到Pinecone"""
        try:
            index_name = f"{self.config['index_prefix']}{collection_name}"
            index = self.client.Index(index_name)
            
            # 准备数据
            upsert_data = []
            for vector_data in vectors:
                metadata = {
                    'content_type': vector_data['content_type'],
                    'content_id': vector_data['content_id'],
                    'text_chunk': vector_data['text_chunk'][:1000],  # Pinecone元数据长度限制
                    'chunk_index': vector_data['chunk_index'],
                    **vector_data.get('metadata', {})
                }
                
                upsert_data.append((
                    vector_data['id'],
                    vector_data['embedding'].tolist(),
                    metadata
                ))
            
            # 批量插入
            index.upsert(vectors=upsert_data)
            
            logger.info(f"插入{len(vectors)}个向量到{index_name}")
            return True
            
        except Exception as e:
            logger.error(f"插入向量到Pinecone失败: {e}")
            return False
    
    def search_vectors(self, collection_name: str, query_vector: np.ndarray, 
                      top_k: int = 10, filter_expr: str = None) -> List[Dict]:
        """在Pinecone中搜索向量"""
        try:
            index_name = f"{self.config['index_prefix']}{collection_name}"
            index = self.client.Index(index_name)
            
            # 转换过滤表达式为Pinecone格式
            filter_dict = None
            if filter_expr:
                # 这里需要根据具体需求转换过滤表达式
                pass
            
            results = index.query(
                vector=query_vector.tolist(),
                top_k=top_k,
                filter=filter_dict,
                include_metadata=True
            )
            
            search_results = []
            for match in results['matches']:
                result = {
                    'id': match['id'],
                    'content_type': match['metadata'].get('content_type'),
                    'content_id': match['metadata'].get('content_id'),
                    'text_chunk': match['metadata'].get('text_chunk'),
                    'chunk_index': match['metadata'].get('chunk_index'),
                    'metadata': match['metadata'],
                    'score': match['score']
                }
                search_results.append(result)
            
            return search_results
            
        except Exception as e:
            logger.error(f"Pinecone向量搜索失败: {e}")
            return []
    
    def delete_vectors(self, collection_name: str, ids: List[str]) -> bool:
        """从Pinecone删除向量"""
        try:
            index_name = f"{self.config['index_prefix']}{collection_name}"
            index = self.client.Index(index_name)
            
            index.delete(ids=ids)
            
            logger.info(f"从{index_name}删除{len(ids)}个向量")
            return True
            
        except Exception as e:
            logger.error(f"从Pinecone删除向量失败: {e}")
            return False
    
    def collection_exists(self, collection_name: str) -> bool:
        """检查Pinecone索引是否存在"""
        try:
            index_name = f"{self.config['index_prefix']}{collection_name}"
            return index_name in self.client.list_indexes()
            
        except Exception as e:
            logger.error(f"检查Pinecone索引存在性失败: {e}")
            return False

class VectorStoreFactory:
    """向量数据库工厂类"""
    
    @staticmethod
    def create_vector_store() -> BaseVectorStore:
        """根据配置创建向量数据库实例"""
        db_type = get_vector_db_config().get('type', 'milvus')
        
        if db_type == 'milvus':
            return MilvusVectorStore()
        elif db_type == 'pinecone':
            return PineconeVectorStore()
        else:
            raise ValueError(f"不支持的向量数据库类型: {db_type}")

class KnowledgeVectorService:
    """知识库向量服务"""
    
    def __init__(self, model_name: str = 'default'):
        self.embedding_service = EmbeddingService(model_name)
        self.vector_store = VectorStoreFactory.create_vector_store()
        self.dimension = self.embedding_service.get_dimension()
    
    def create_knowledge_base_collection(self, kb_id: int, kb_name: str) -> bool:
        """为知识库创建向量集合"""
        collection_name = f"kb_{kb_id}"
        return self.vector_store.create_collection(collection_name, self.dimension)
    
    def add_content_vectors(self, kb_id: int, content_type: str, content_id: int, 
                           texts: List[str], metadata: Dict = None) -> bool:
        """添加内容向量"""
        try:
            collection_name = f"kb_{kb_id}"
            
            # 确保集合存在
            if not self.vector_store.collection_exists(collection_name):
                self.create_knowledge_base_collection(kb_id, f"kb_{kb_id}")
            
            # 生成向量
            embeddings = self.embedding_service.encode(texts)
            
            # 准备向量数据
            vectors = []
            for i, (text, embedding) in enumerate(zip(texts, embeddings)):
                vector_id = self._generate_vector_id(content_type, content_id, i)
                vector_data = {
                    'id': vector_id,
                    'content_type': content_type,
                    'content_id': content_id,
                    'text_chunk': text,
                    'chunk_index': i,
                    'embedding': embedding,
                    'metadata': metadata or {}
                }
                vectors.append(vector_data)
            
            # 插入向量
            return self.vector_store.insert_vectors(collection_name, vectors)
            
        except Exception as e:
            logger.error(f"添加内容向量失败: {e}")
            return False
    
    def search_knowledge(self, kb_id: int, query: str, top_k: int = 10, 
                        content_types: List[str] = None) -> List[Dict]:
        """搜索知识库"""
        try:
            collection_name = f"kb_{kb_id}"
            
            # 生成查询向量
            query_vector = self.embedding_service.encode_single(query)
            
            # 构建过滤条件
            filter_expr = None
            if content_types:
                type_filter = " or ".join([f"content_type == '{ct}'" for ct in content_types])
                filter_expr = f"({type_filter})"
            
            # 搜索向量
            results = self.vector_store.search_vectors(
                collection_name, query_vector, top_k, filter_expr
            )
            
            return results
            
        except Exception as e:
            logger.error(f"搜索知识库失败: {e}")
            return []
    
    def delete_content_vectors(self, kb_id: int, content_type: str, content_id: int) -> bool:
        """删除内容向量"""
        try:
            collection_name = f"kb_{kb_id}"
            
            # 生成要删除的向量ID列表（假设我们知道chunk数量）
            # 这里需要根据实际情况调整
            vector_ids = []
            for i in range(100):  # 假设最多100个chunk
                vector_id = self._generate_vector_id(content_type, content_id, i)
                vector_ids.append(vector_id)
            
            return self.vector_store.delete_vectors(collection_name, vector_ids)
            
        except Exception as e:
            logger.error(f"删除内容向量失败: {e}")
            return False
    
    def update_content_vectors(self, kb_id: int, content_type: str, content_id: int, 
                              texts: List[str], metadata: Dict = None) -> bool:
        """更新内容向量"""
        # 先删除旧向量
        self.delete_content_vectors(kb_id, content_type, content_id)
        # 添加新向量
        return self.add_content_vectors(kb_id, content_type, content_id, texts, metadata)
    
    def _generate_vector_id(self, content_type: str, content_id: int, chunk_index: int) -> str:
        """生成向量ID"""
        return f"{content_type}_{content_id}_{chunk_index}"
    
    def chunk_text(self, text: str, content_type: str = 'documents') -> List[str]:
        """文本分块"""
        chunk_config = get_chunking_config(content_type)
        
        chunks = []
        chunk_size = chunk_config['chunk_size']
        overlap = chunk_config['chunk_overlap']
        separators = chunk_config['separators']
        
        # 按分隔符分割文本
        current_text = text
        for separator in separators:
            if separator in current_text:
                parts = current_text.split(separator)
                break
        else:
            parts = [current_text]
        
        # 组合成适当大小的块
        current_chunk = ""
        for part in parts:
            if len(current_chunk) + len(part) <= chunk_size:
                current_chunk += part + " "
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = part + " "
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # 处理重叠
        if overlap > 0 and len(chunks) > 1:
            overlapped_chunks = []
            for i, chunk in enumerate(chunks):
                if i == 0:
                    overlapped_chunks.append(chunk)
                else:
                    # 添加与前一个chunk的重叠部分
                    prev_chunk = chunks[i-1]
                    overlap_text = prev_chunk[-overlap:] if len(prev_chunk) > overlap else prev_chunk
                    overlapped_chunk = overlap_text + " " + chunk
                    overlapped_chunks.append(overlapped_chunk)
            chunks = overlapped_chunks
        
        return [chunk for chunk in chunks if len(chunk) >= chunk_config['min_chunk_size']] 