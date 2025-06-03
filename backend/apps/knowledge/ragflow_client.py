"""
RAGFlow客户端 - 与RAGFlow API交互
"""

import json
import requests
import logging
from typing import Dict, List, Optional, Any, Union
from django.conf import settings
from django.core.files.base import ContentFile
import io
import tempfile
import os

logger = logging.getLogger(__name__)


class RAGFlowError(Exception):
    """RAGFlow API错误"""
    pass


class RAGFlowClient:
    """RAGFlow客户端"""
    
    def __init__(self, api_url: str = None, api_key: str = None):
        """
        初始化RAGFlow客户端
        
        Args:
            api_url: RAGFlow API地址
            api_key: RAGFlow API密钥
        """
        self.api_url = api_url or getattr(settings, 'RAGFLOW_API_URL', 'http://localhost')
        self.api_key = api_key or getattr(settings, 'RAGFLOW_API_KEY', '')
        
        # 设置默认headers
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}' if self.api_key else '',
        }
        
        # 设置超时时间
        self.timeout = getattr(settings, 'RAGFLOW_TIMEOUT', 30)
        
    def _make_request(self, method: str, endpoint: str, data: Dict = None, 
                     files: Dict = None, params: Dict = None) -> Dict:
        """
        发送HTTP请求
        
        Args:
            method: HTTP方法
            endpoint: API端点
            data: 请求数据
            files: 文件数据
            params: URL参数
            
        Returns:
            响应数据
            
        Raises:
            RAGFlowError: API请求失败
        """
        url = f"{self.api_url.rstrip('/')}/api/v1/{endpoint.lstrip('/')}"
        
        try:
            headers = self.headers.copy()
            if files:
                # 如果上传文件，不设置Content-Type，让requests自动设置
                headers.pop('Content-Type', None)
            
            response = requests.request(
                method=method,
                url=url,
                json=data if not files else None,
                files=files,
                params=params,
                headers=headers,
                timeout=self.timeout
            )
            
            # 记录请求日志
            logger.debug(f"RAGFlow {method} {url} - Status: {response.status_code}")
            
            if response.status_code >= 400:
                error_msg = f"RAGFlow API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise RAGFlowError(error_msg)
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            error_msg = f"RAGFlow API request failed: {str(e)}"
            logger.error(error_msg)
            raise RAGFlowError(error_msg)
    
    def get_knowledge_bases(self) -> List[Dict]:
        """获取知识库列表"""
        try:
            return self._make_request('GET', 'knowledge_bases')
        except Exception as e:
            logger.error(f"获取知识库列表失败: {e}")
            return []
    
    def create_knowledge_base(self, name: str, description: str = "", 
                            embedding_model: str = "BAAI/bge-large-zh-v1.5",
                            chunk_method: str = "intelligent") -> Dict:
        """
        创建知识库
        
        Args:
            name: 知识库名称
            description: 描述
            embedding_model: 向量化模型
            chunk_method: 分块方法
            
        Returns:
            创建的知识库信息
        """
        data = {
            "name": name,
            "description": description,
            "embedding_model": embedding_model,
            "chunk_method": chunk_method,
            "language": "Chinese"
        }
        
        try:
            result = self._make_request('POST', 'knowledge_bases', data=data)
            logger.info(f"成功创建RAGFlow知识库: {name}")
            return result
        except Exception as e:
            logger.error(f"创建RAGFlow知识库失败: {e}")
            raise
    
    def delete_knowledge_base(self, kb_id: str) -> bool:
        """删除知识库"""
        try:
            self._make_request('DELETE', f'knowledge_bases/{kb_id}')
            logger.info(f"成功删除RAGFlow知识库: {kb_id}")
            return True
        except Exception as e:
            logger.error(f"删除RAGFlow知识库失败: {e}")
            return False
    
    def upload_document(self, kb_id: str, file_name: str, file_content: Union[str, bytes],
                       file_type: str = "text") -> Dict:
        """
        上传文档到知识库
        
        Args:
            kb_id: 知识库ID
            file_name: 文件名
            file_content: 文件内容
            file_type: 文件类型
            
        Returns:
            上传结果
        """
        try:
            # 准备文件数据
            if isinstance(file_content, str):
                file_content = file_content.encode('utf-8')
            
            files = {
                'file': (file_name, io.BytesIO(file_content), 'text/plain')
            }
            
            data = {
                'knowledge_base_id': kb_id,
                'file_type': file_type
            }
            
            result = self._make_request('POST', f'knowledge_bases/{kb_id}/documents', 
                                      files=files, params=data)
            logger.info(f"成功上传文档到RAGFlow: {file_name}")
            return result
        except Exception as e:
            logger.error(f"上传文档到RAGFlow失败: {e}")
            raise
    
    def delete_document(self, kb_id: str, doc_id: str) -> bool:
        """删除文档"""
        try:
            self._make_request('DELETE', f'knowledge_bases/{kb_id}/documents/{doc_id}')
            logger.info(f"成功从RAGFlow删除文档: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"从RAGFlow删除文档失败: {e}")
            return False
    
    def get_document_status(self, kb_id: str, doc_id: str) -> Dict:
        """获取文档处理状态"""
        try:
            return self._make_request('GET', f'knowledge_bases/{kb_id}/documents/{doc_id}/status')
        except Exception as e:
            logger.error(f"获取文档状态失败: {e}")
            return {"status": "unknown", "error": str(e)}
    
    def search_knowledge_base(self, kb_id: str, query: str, top_k: int = 10,
                            similarity_threshold: float = 0.1) -> Dict:
        """
        搜索知识库
        
        Args:
            kb_id: 知识库ID
            query: 查询文本
            top_k: 返回结果数量
            similarity_threshold: 相似度阈值
            
        Returns:
            搜索结果
        """
        data = {
            "query": query,
            "top_k": top_k,
            "similarity_threshold": similarity_threshold
        }
        
        try:
            return self._make_request('POST', f'knowledge_bases/{kb_id}/search', data=data)
        except Exception as e:
            logger.error(f"搜索知识库失败: {e}")
            return {"chunks": [], "total": 0}
    
    def get_retrieval_result(self, kb_id: str, query: str, top_k: int = 5) -> List[Dict]:
        """
        获取检索结果
        
        Args:
            kb_id: 知识库ID
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            检索结果列表
        """
        try:
            result = self.search_knowledge_base(kb_id, query, top_k)
            return result.get('chunks', [])
        except Exception as e:
            logger.error(f"获取检索结果失败: {e}")
            return []
    
    def create_chat_session(self, kb_ids: List[str], model_name: str = "deepseek-chat") -> Dict:
        """
        创建聊天会话
        
        Args:
            kb_ids: 知识库ID列表
            model_name: 模型名称
            
        Returns:
            会话信息
        """
        data = {
            "knowledge_base_ids": kb_ids,
            "model_name": model_name,
            "temperature": 0.1,
            "top_p": 0.3,
            "max_tokens": 512
        }
        
        try:
            return self._make_request('POST', 'chat/sessions', data=data)
        except Exception as e:
            logger.error(f"创建聊天会话失败: {e}")
            raise
    
    def chat(self, session_id: str, query: str, stream: bool = False) -> Dict:
        """
        进行对话
        
        Args:
            session_id: 会话ID
            query: 查询文本
            stream: 是否流式返回
            
        Returns:
            对话结果
        """
        data = {
            "query": query,
            "stream": stream
        }
        
        try:
            return self._make_request('POST', f'chat/sessions/{session_id}/messages', data=data)
        except Exception as e:
            logger.error(f"对话失败: {e}")
            raise
    
    def get_statistics(self, kb_id: str) -> Dict:
        """获取知识库统计信息"""
        try:
            return self._make_request('GET', f'knowledge_bases/{kb_id}/statistics')
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}


# 创建全局客户端实例
ragflow_client = RAGFlowClient() 