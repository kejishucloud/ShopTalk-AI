"""
RAGFlow集成客户端
用于与RAGFlow系统进行数据同步和集成
"""
import json
import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import time

from .config import get_ragflow_config, is_ragflow_enabled

logger = logging.getLogger(__name__)

class RAGFlowClient:
    """RAGFlow API客户端"""
    
    def __init__(self):
        self.config = get_ragflow_config()
        self.base_url = self.config['base_url'].rstrip('/')
        self.api_key = self.config['api_key']
        self.user_id = self.config['user_id']
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'User-Agent': 'ShopTalk-Knowledge-Sync/1.0'
        })
    
    def test_connection(self) -> bool:
        """测试RAGFlow连接"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"RAGFlow连接测试失败: {e}")
            return False
    
    def create_dataset(self, dataset_name: str, description: str = "") -> Optional[str]:
        """创建RAGFlow数据集"""
        try:
            data = {
                "name": f"{self.config['dataset_prefix']}{dataset_name}",
                "description": description,
                "language": "Chinese",
                "embedding_model": "BAAI/bge-large-zh-v1.5",
                "chunk_method": "manual",
                "chunk_size": self.config['chunk_size'],
                "chunk_overlap": self.config['chunk_overlap'],
                "permission": "me"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/datasets",
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                dataset_id = result.get('data', {}).get('dataset_id')
                logger.info(f"创建RAGFlow数据集成功: {dataset_name} -> {dataset_id}")
                return dataset_id
            else:
                logger.error(f"创建RAGFlow数据集失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"创建RAGFlow数据集异常: {e}")
            return None
    
    def get_dataset(self, dataset_name: str) -> Optional[str]:
        """获取RAGFlow数据集"""
        try:
            full_name = f"{self.config['dataset_prefix']}{dataset_name}"
            response = self.session.get(f"{self.base_url}/api/v1/datasets")
            
            if response.status_code == 200:
                datasets = response.json().get('data', [])
                for dataset in datasets:
                    if dataset.get('name') == full_name:
                        return dataset.get('dataset_id')
            
            return None
            
        except Exception as e:
            logger.error(f"获取RAGFlow数据集异常: {e}")
            return None
    
    def get_or_create_dataset(self, dataset_name: str, description: str = "") -> Optional[str]:
        """获取或创建RAGFlow数据集"""
        dataset_id = self.get_dataset(dataset_name)
        if dataset_id:
            return dataset_id
        return self.create_dataset(dataset_name, description)
    
    def upload_document(self, dataset_id: str, title: str, content: str, 
                       metadata: Dict = None) -> Optional[str]:
        """上传文档到RAGFlow"""
        try:
            data = {
                "dataset_id": dataset_id,
                "name": title,
                "type": "text",
                "content": content,
                "metadata": metadata or {},
                "chunk_method": "manual",
                "chunk_size": self.config['chunk_size'],
                "chunk_overlap": self.config['chunk_overlap']
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/documents",
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                document_id = result.get('data', {}).get('document_id')
                logger.info(f"上传文档到RAGFlow成功: {title} -> {document_id}")
                return document_id
            else:
                logger.error(f"上传文档到RAGFlow失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"上传文档到RAGFlow异常: {e}")
            return None
    
    def update_document(self, document_id: str, title: str, content: str, 
                       metadata: Dict = None) -> bool:
        """更新RAGFlow文档"""
        try:
            data = {
                "name": title,
                "content": content,
                "metadata": metadata or {}
            }
            
            response = self.session.put(
                f"{self.base_url}/api/v1/documents/{document_id}",
                json=data
            )
            
            if response.status_code == 200:
                logger.info(f"更新RAGFlow文档成功: {document_id}")
                return True
            else:
                logger.error(f"更新RAGFlow文档失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"更新RAGFlow文档异常: {e}")
            return False
    
    def delete_document(self, document_id: str) -> bool:
        """删除RAGFlow文档"""
        try:
            response = self.session.delete(f"{self.base_url}/api/v1/documents/{document_id}")
            
            if response.status_code == 200:
                logger.info(f"删除RAGFlow文档成功: {document_id}")
                return True
            else:
                logger.error(f"删除RAGFlow文档失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"删除RAGFlow文档异常: {e}")
            return False
    
    def process_document(self, document_id: str) -> bool:
        """处理RAGFlow文档（分块和向量化）"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/documents/{document_id}/process"
            )
            
            if response.status_code == 200:
                logger.info(f"处理RAGFlow文档成功: {document_id}")
                return True
            else:
                logger.error(f"处理RAGFlow文档失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"处理RAGFlow文档异常: {e}")
            return False
    
    def get_document_status(self, document_id: str) -> Optional[str]:
        """获取RAGFlow文档状态"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/documents/{document_id}")
            
            if response.status_code == 200:
                result = response.json()
                return result.get('data', {}).get('status')
            else:
                logger.error(f"获取RAGFlow文档状态失败: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"获取RAGFlow文档状态异常: {e}")
            return None
    
    def wait_for_processing(self, document_id: str, timeout: int = 300) -> bool:
        """等待RAGFlow文档处理完成"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_document_status(document_id)
            
            if status == 'completed':
                return True
            elif status == 'failed':
                return False
            
            time.sleep(5)  # 等待5秒后重试
        
        logger.warning(f"RAGFlow文档处理超时: {document_id}")
        return False
    
    def search_documents(self, dataset_id: str, query: str, top_k: int = 10) -> List[Dict]:
        """在RAGFlow中搜索文档"""
        try:
            data = {
                "dataset_id": dataset_id,
                "question": query,
                "top_k": top_k,
                "similarity_threshold": 0.1
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/retrieval",
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('data', {}).get('chunks', [])
            else:
                logger.error(f"RAGFlow搜索失败: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"RAGFlow搜索异常: {e}")
            return []

class KnowledgeRAGFlowSync:
    """知识库RAGFlow同步服务"""
    
    def __init__(self):
        self.client = RAGFlowClient() if is_ragflow_enabled() else None
        self.dataset_mapping = {}  # 知识库ID到RAGFlow数据集ID的映射
    
    def sync_knowledge_base(self, kb_id: int, kb_name: str, kb_type: str) -> bool:
        """同步知识库到RAGFlow"""
        if not self.client:
            logger.info("RAGFlow未启用，跳过同步")
            return True
        
        try:
            # 创建或获取数据集
            dataset_name = f"{kb_type}_{kb_id}"
            description = f"ShopTalk知识库: {kb_name} (类型: {kb_type})"
            
            dataset_id = self.client.get_or_create_dataset(dataset_name, description)
            if not dataset_id:
                return False
            
            self.dataset_mapping[kb_id] = dataset_id
            logger.info(f"知识库同步成功: KB{kb_id} -> Dataset{dataset_id}")
            return True
            
        except Exception as e:
            logger.error(f"同步知识库到RAGFlow失败: {e}")
            return False
    
    def sync_script(self, kb_id: int, script_id: int, script_name: str, 
                   script_type: str, content: str, metadata: Dict = None) -> bool:
        """同步话术到RAGFlow"""
        if not self.client:
            return True
        
        try:
            dataset_id = self.dataset_mapping.get(kb_id)
            if not dataset_id:
                logger.warning(f"知识库{kb_id}未同步到RAGFlow")
                return False
            
            # 准备文档内容
            title = f"话术_{script_type}_{script_name}"
            doc_content = f"话术名称: {script_name}\n话术类型: {script_type}\n\n话术内容:\n{content}"
            
            # 准备元数据
            doc_metadata = {
                'content_type': 'script',
                'content_id': script_id,
                'script_type': script_type,
                'script_name': script_name
            }
            if metadata:
                doc_metadata.update(metadata)
            
            # 上传文档
            document_id = self.client.upload_document(
                dataset_id, title, doc_content, doc_metadata
            )
            
            if document_id:
                # 处理文档
                self.client.process_document(document_id)
                logger.info(f"话术同步成功: {script_name} -> {document_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"同步话术到RAGFlow失败: {e}")
            return False
    
    def sync_product(self, kb_id: int, product_id: int, product_name: str, 
                    description: str, specifications: Dict = None, 
                    metadata: Dict = None) -> bool:
        """同步产品到RAGFlow"""
        if not self.client:
            return True
        
        try:
            dataset_id = self.dataset_mapping.get(kb_id)
            if not dataset_id:
                logger.warning(f"知识库{kb_id}未同步到RAGFlow")
                return False
            
            # 准备文档内容
            title = f"产品_{product_name}"
            doc_content = f"产品名称: {product_name}\n\n产品描述:\n{description}"
            
            # 添加规格信息
            if specifications:
                doc_content += "\n\n产品规格:\n"
                for key, value in specifications.items():
                    doc_content += f"- {key}: {value}\n"
            
            # 准备元数据
            doc_metadata = {
                'content_type': 'product',
                'content_id': product_id,
                'product_name': product_name
            }
            if metadata:
                doc_metadata.update(metadata)
            
            # 上传文档
            document_id = self.client.upload_document(
                dataset_id, title, doc_content, doc_metadata
            )
            
            if document_id:
                # 处理文档
                self.client.process_document(document_id)
                logger.info(f"产品同步成功: {product_name} -> {document_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"同步产品到RAGFlow失败: {e}")
            return False
    
    def sync_document(self, kb_id: int, doc_id: int, title: str, content: str, 
                     metadata: Dict = None) -> bool:
        """同步文档到RAGFlow"""
        if not self.client:
            return True
        
        try:
            dataset_id = self.dataset_mapping.get(kb_id)
            if not dataset_id:
                logger.warning(f"知识库{kb_id}未同步到RAGFlow")
                return False
            
            # 准备元数据
            doc_metadata = {
                'content_type': 'document',
                'content_id': doc_id
            }
            if metadata:
                doc_metadata.update(metadata)
            
            # 上传文档
            document_id = self.client.upload_document(
                dataset_id, title, content, doc_metadata
            )
            
            if document_id:
                # 处理文档
                self.client.process_document(document_id)
                logger.info(f"文档同步成功: {title} -> {document_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"同步文档到RAGFlow失败: {e}")
            return False
    
    def sync_faq(self, kb_id: int, faq_id: int, question: str, answer: str, 
                metadata: Dict = None) -> bool:
        """同步FAQ到RAGFlow"""
        if not self.client:
            return True
        
        try:
            dataset_id = self.dataset_mapping.get(kb_id)
            if not dataset_id:
                logger.warning(f"知识库{kb_id}未同步到RAGFlow")
                return False
            
            # 准备文档内容
            title = f"FAQ_{question[:50]}"
            doc_content = f"问题: {question}\n\n答案: {answer}"
            
            # 准备元数据
            doc_metadata = {
                'content_type': 'faq',
                'content_id': faq_id,
                'question': question
            }
            if metadata:
                doc_metadata.update(metadata)
            
            # 上传文档
            document_id = self.client.upload_document(
                dataset_id, title, doc_content, doc_metadata
            )
            
            if document_id:
                # 处理文档
                self.client.process_document(document_id)
                logger.info(f"FAQ同步成功: {question[:50]} -> {document_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"同步FAQ到RAGFlow失败: {e}")
            return False
    
    def search_ragflow(self, kb_id: int, query: str, top_k: int = 10) -> List[Dict]:
        """在RAGFlow中搜索知识"""
        if not self.client:
            return []
        
        try:
            dataset_id = self.dataset_mapping.get(kb_id)
            if not dataset_id:
                logger.warning(f"知识库{kb_id}未同步到RAGFlow")
                return []
            
            return self.client.search_documents(dataset_id, query, top_k)
            
        except Exception as e:
            logger.error(f"RAGFlow搜索失败: {e}")
            return []
    
    def delete_from_ragflow(self, document_id: str) -> bool:
        """从RAGFlow删除文档"""
        if not self.client:
            return True
        
        return self.client.delete_document(document_id)
    
    def get_dataset_id(self, kb_id: int) -> Optional[str]:
        """获取知识库对应的RAGFlow数据集ID"""
        return self.dataset_mapping.get(kb_id)
    
    def load_dataset_mapping(self, mapping: Dict[int, str]):
        """加载数据集映射"""
        self.dataset_mapping.update(mapping) 