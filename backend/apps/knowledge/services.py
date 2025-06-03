"""
知识库管理服务类
提供知识检索、文档处理、向量化、智能推荐等功能
"""

import hashlib
import os
import re
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

from django.conf import settings
from django.db.models import Q, Count, Avg, F
from django.utils import timezone
from django.core.files.storage import default_storage
from django.db import transaction

# 文档处理相关依赖
try:
    import PyPDF2
    from docx import Document as DocxDocument
    import pandas as pd
except ImportError:
    PyPDF2 = None
    DocxDocument = None
    pd = None

# NLP和向量化依赖
try:
    from sentence_transformers import SentenceTransformer
    import jieba
    import numpy as np
except ImportError:
    SentenceTransformer = None
    jieba = None
    np = None

from .models import (
    KnowledgeBase, Document, FAQ, Product, Script, KnowledgeVector,
    KnowledgeAccessRecord, KnowledgeRecommendation, DocumentCategory, DocumentTag
)

logger = logging.getLogger('knowledge')


class DocumentProcessorService:
    """文档处理服务"""
    
    def __init__(self):
        self.supported_types = {
            '.pdf': self._process_pdf,
            '.docx': self._process_docx,
            '.doc': self._process_docx,
            '.txt': self._process_text,
            '.md': self._process_markdown,
            '.xlsx': self._process_excel,
            '.xls': self._process_excel,
        }
    
    def process_document(self, document: Document) -> Dict[str, Any]:
        """
        处理文档，提取文本内容
        """
        try:
            document.process_status = Document.ProcessStatus.PROCESSING
            document.save()
            
            if not document.file_path:
                raise ValueError("文档文件路径为空")
            
            file_path = document.file_path.path
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext not in self.supported_types:
                raise ValueError(f"不支持的文件类型: {file_ext}")
            
            # 计算文件哈希
            document.file_hash = self._calculate_file_hash(file_path)
            document.file_size = os.path.getsize(file_path)
            
            # 提取文本内容
            processor = self.supported_types[file_ext]
            extracted_text = processor(file_path)
            
            document.extracted_text = extracted_text
            
            # 自动生成摘要
            if not document.summary and extracted_text:
                document.summary = self._generate_summary(extracted_text)
            
            # 自动提取关键词
            if document.knowledge_base.auto_extract_keywords:
                keywords = self._extract_keywords(extracted_text)
                document.keywords = keywords
            
            document.process_status = Document.ProcessStatus.COMPLETED
            document.process_message = "文档处理成功"
            document.save()
            
            logger.info(f"文档处理成功: {document.title}")
            
            return {
                'success': True,
                'extracted_text': extracted_text,
                'summary': document.summary,
                'keywords': document.keywords,
                'file_size': document.file_size,
                'file_hash': document.file_hash
            }
            
        except Exception as e:
            document.process_status = Document.ProcessStatus.FAILED
            document.process_message = str(e)
            document.save()
            
            logger.error(f"文档处理失败: {document.title} - {str(e)}")
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def _process_pdf(self, file_path: str) -> str:
        """处理PDF文件"""
        if not PyPDF2:
            raise ImportError("PyPDF2 库未安装")
        
        text = ""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        
        return text.strip()
    
    def _process_docx(self, file_path: str) -> str:
        """处理Word文档"""
        if not DocxDocument:
            raise ImportError("python-docx 库未安装")
        
        doc = DocxDocument(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return text.strip()
    
    def _process_text(self, file_path: str) -> str:
        """处理文本文件"""
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    
    def _process_markdown(self, file_path: str) -> str:
        """处理Markdown文件"""
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            # 简单的Markdown清理
            content = re.sub(r'#+ ', '', content)  # 移除标题标记
            content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)  # 移除粗体标记
            content = re.sub(r'\*(.*?)\*', r'\1', content)  # 移除斜体标记
            content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)  # 移除链接标记
            return content
    
    def _process_excel(self, file_path: str) -> str:
        """处理Excel文件"""
        if not pd:
            raise ImportError("pandas 库未安装")
        
        df = pd.read_excel(file_path)
        return df.to_string(index=False)
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件MD5哈希值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _generate_summary(self, text: str, max_length: int = 200) -> str:
        """生成文档摘要"""
        # 简单的摘要生成：取前几句话
        sentences = text.split('。')
        summary = ""
        for sentence in sentences:
            if len(summary + sentence) < max_length:
                summary += sentence + "。"
            else:
                break
        
        return summary.strip() or text[:max_length] + "..."
    
    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """提取关键词"""
        if not jieba:
            return []
        
        # 使用jieba分词
        words = jieba.cut(text)
        
        # 过滤停用词和短词
        stopwords = {'的', '是', '在', '了', '和', '有', '就', '不', '人', '都', '一', '这', '我', '你', '他', '她', '它'}
        keywords = [word for word in words if len(word) > 1 and word not in stopwords]
        
        # 统计词频
        word_freq = {}
        for word in keywords:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # 按频率排序并返回前N个
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:max_keywords]]


class VectorizeService:
    """向量化服务"""
    
    def __init__(self):
        self.model = None
        self.model_name = getattr(settings, 'KNOWLEDGE_EMBEDDING_MODEL', 'paraphrase-multilingual-MiniLM-L12-v2')
        self.chunk_size = getattr(settings, 'KNOWLEDGE_CHUNK_SIZE', 512)
        self.chunk_overlap = getattr(settings, 'KNOWLEDGE_CHUNK_OVERLAP', 50)
    
    def get_embedding_model(self):
        """获取向量化模型"""
        if not SentenceTransformer:
            raise ImportError("sentence-transformers 库未安装")
        
        if self.model is None:
            try:
                self.model = SentenceTransformer(self.model_name)
            except Exception as e:
                logger.error(f"加载向量模型失败: {str(e)}")
                raise
        
        return self.model
    
    def vectorize_document(self, document: Document) -> Dict[str, Any]:
        """
        对文档进行向量化
        """
        try:
            if not document.extracted_text and not document.content:
                return {'success': False, 'error': '文档没有可向量化的文本内容'}
            
            text = document.extracted_text or document.content
            
            # 文本分块
            chunks = self._split_text(text)
            
            # 获取向量模型
            model = self.get_embedding_model()
            
            # 删除旧的向量
            KnowledgeVector.objects.filter(
                knowledge_base=document.knowledge_base,
                content_type='document',
                content_id=document.id
            ).delete()
            
            vectors_created = 0
            
            for i, chunk in enumerate(chunks):
                try:
                    # 生成向量
                    embedding = model.encode(chunk)
                    
                    # 保存向量
                    KnowledgeVector.objects.create(
                        knowledge_base=document.knowledge_base,
                        content_type='document',
                        content_id=document.id,
                        text_chunk=chunk,
                        chunk_index=i,
                        chunk_size=len(chunk),
                        embedding_model=self.model_name,
                        vector_data=embedding.tolist(),
                        vector_dimension=len(embedding),
                        keywords=self._extract_chunk_keywords(chunk),
                        language=document.language,
                        metadata={
                            'document_title': document.title,
                            'document_type': document.document_type,
                            'category': document.category.name if document.category else None
                        }
                    )
                    vectors_created += 1
                    
                except Exception as e:
                    logger.error(f"向量化文档块失败: {document.title} - 块{i} - {str(e)}")
                    continue
            
            logger.info(f"文档向量化完成: {document.title} - 创建{vectors_created}个向量")
            
            return {
                'success': True,
                'vectors_created': vectors_created,
                'total_chunks': len(chunks)
            }
            
        except Exception as e:
            logger.error(f"文档向量化失败: {document.title} - {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def vectorize_faq(self, faq: FAQ) -> Dict[str, Any]:
        """对FAQ进行向量化"""
        try:
            model = self.get_embedding_model()
            
            # 合并问题和答案
            text = f"{faq.question}\n{faq.answer}"
            
            # 生成向量
            embedding = model.encode(text)
            
            # 删除旧向量
            KnowledgeVector.objects.filter(
                knowledge_base=faq.knowledge_base,
                content_type='faq',
                content_id=faq.id
            ).delete()
            
            # 保存向量
            KnowledgeVector.objects.create(
                knowledge_base=faq.knowledge_base,
                content_type='faq',
                content_id=faq.id,
                text_chunk=text,
                chunk_index=0,
                chunk_size=len(text),
                embedding_model=self.model_name,
                vector_data=embedding.tolist(),
                vector_dimension=len(embedding),
                keywords=faq.keywords,
                metadata={
                    'question': faq.question,
                    'category': faq.faq_category,
                    'priority': faq.priority
                }
            )
            
            logger.info(f"FAQ向量化完成: {faq.question[:50]}")
            
            return {'success': True, 'vectors_created': 1}
            
        except Exception as e:
            logger.error(f"FAQ向量化失败: {faq.question[:50]} - {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _split_text(self, text: str) -> List[str]:
        """将文本分割成块"""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # 如果不是最后一块，尝试在句号处断开
            if end < len(text):
                # 向后查找句号
                for i in range(min(100, len(text) - end)):
                    if text[end + i] in '。！？.!?':
                        end = end + i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.chunk_overlap
            if start >= len(text):
                break
        
        return chunks
    
    def _extract_chunk_keywords(self, text: str) -> List[str]:
        """提取文本块的关键词"""
        if not jieba:
            return []
        
        words = jieba.cut(text)
        stopwords = {'的', '是', '在', '了', '和', '有', '就', '不', '人', '都', '一', '这', '我', '你', '他', '她', '它'}
        keywords = [word for word in words if len(word) > 1 and word not in stopwords]
        
        # 返回前5个不重复的关键词
        unique_keywords = list(dict.fromkeys(keywords))
        return unique_keywords[:5]


class KnowledgeSearchService:
    """知识搜索服务"""
    
    def __init__(self):
        self.vectorize_service = VectorizeService()
    
    def search(self, query: str, knowledge_base_id: Optional[int] = None, 
               content_types: Optional[List[str]] = None,
               categories: Optional[List[int]] = None,
               tags: Optional[List[int]] = None,
               limit: int = 20,
               include_vectors: bool = False,
               similarity_threshold: float = 0.5) -> Dict[str, Any]:
        """
        执行知识搜索
        """
        try:
            start_time = time.time()
            
            # 构建查询条件
            search_results = []
            
            # 1. 文本搜索
            text_results = self._text_search(
                query, knowledge_base_id, content_types, categories, tags, limit
            )
            search_results.extend(text_results)
            
            # 2. 向量搜索（如果启用）
            if include_vectors and SentenceTransformer:
                try:
                    vector_results = self._vector_search(
                        query, knowledge_base_id, content_types, 
                        similarity_threshold, limit // 2
                    )
                    search_results.extend(vector_results)
                except Exception as e:
                    logger.warning(f"向量搜索失败: {str(e)}")
            
            # 去重并排序
            search_results = self._deduplicate_and_rank(search_results)
            
            # 限制结果数量
            search_results = search_results[:limit]
            
            response_time = time.time() - start_time
            
            # 记录搜索访问
            self._record_search_access(
                query, knowledge_base_id, len(search_results), response_time
            )
            
            return {
                'success': True,
                'query': query,
                'total_results': len(search_results),
                'results': search_results,
                'response_time': response_time,
                'search_types': ['text'] + (['vector'] if include_vectors else [])
            }
            
        except Exception as e:
            logger.error(f"知识搜索失败: {query} - {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'query': query,
                'results': []
            }
    
    def _text_search(self, query: str, knowledge_base_id: Optional[int],
                     content_types: Optional[List[str]], categories: Optional[List[int]],
                     tags: Optional[List[int]], limit: int) -> List[Dict]:
        """文本搜索"""
        results = []
        
        # 搜索文档
        if not content_types or 'document' in content_types:
            documents = Document.objects.filter(is_active=True)
            if knowledge_base_id:
                documents = documents.filter(knowledge_base_id=knowledge_base_id)
            if categories:
                documents = documents.filter(category_id__in=categories)
            if tags:
                documents = documents.filter(tags__id__in=tags).distinct()
            
            documents = documents.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query) |
                Q(summary__icontains=query) |
                Q(extracted_text__icontains=query)
            )[:limit // 4]
            
            for doc in documents:
                results.append({
                    'content_type': 'document',
                    'content_id': doc.id,
                    'title': doc.title,
                    'summary': doc.summary or doc.content[:200] + '...',
                    'score': self._calculate_text_score(query, doc.title, doc.summary or doc.content),
                    'source': 'text_search',
                    'url': f'/knowledge/documents/{doc.id}/',
                    'highlights': self._get_highlights(query, doc.title + ' ' + (doc.summary or doc.content)),
                    'metadata': {
                        'document_type': doc.document_type,
                        'category': doc.category.name if doc.category else None,
                        'created_at': doc.created_at.isoformat()
                    }
                })
        
        # 搜索FAQ
        if not content_types or 'faq' in content_types:
            faqs = FAQ.objects.filter(is_active=True, status='published')
            if knowledge_base_id:
                faqs = faqs.filter(knowledge_base_id=knowledge_base_id)
            if categories:
                faqs = faqs.filter(category_id__in=categories)
            if tags:
                faqs = faqs.filter(tags__id__in=tags).distinct()
            
            faqs = faqs.filter(
                Q(question__icontains=query) |
                Q(answer__icontains=query)
            )[:limit // 4]
            
            for faq in faqs:
                results.append({
                    'content_type': 'faq',
                    'content_id': faq.id,
                    'title': faq.question,
                    'summary': faq.answer[:200] + '...',
                    'score': self._calculate_text_score(query, faq.question, faq.answer),
                    'source': 'text_search',
                    'url': f'/knowledge/faqs/{faq.id}/',
                    'highlights': self._get_highlights(query, faq.question + ' ' + faq.answer),
                    'metadata': {
                        'category': faq.faq_category,
                        'priority': faq.priority,
                        'helpful_count': faq.helpful_count
                    }
                })
        
        # 搜索商品
        if not content_types or 'product' in content_types:
            products = Product.objects.filter(status='active')
            if knowledge_base_id:
                products = products.filter(knowledge_base_id=knowledge_base_id)
            if categories:
                products = products.filter(category_id__in=categories)
            if tags:
                products = products.filter(tags__id__in=tags).distinct()
            
            products = products.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(sku__icontains=query)
            )[:limit // 4]
            
            for product in products:
                results.append({
                    'content_type': 'product',
                    'content_id': product.id,
                    'title': product.name,
                    'summary': product.short_description or product.description[:200] + '...',
                    'score': self._calculate_text_score(query, product.name, product.description),
                    'source': 'text_search',
                    'url': f'/knowledge/products/{product.id}/',
                    'highlights': self._get_highlights(query, product.name + ' ' + product.description),
                    'metadata': {
                        'sku': product.sku,
                        'price': str(product.price),
                        'brand': product.brand,
                        'category': product.product_category
                    }
                })
        
        return results
    
    def _vector_search(self, query: str, knowledge_base_id: Optional[int],
                       content_types: Optional[List[str]], 
                       similarity_threshold: float, limit: int) -> List[Dict]:
        """向量搜索"""
        try:
            model = self.vectorize_service.get_embedding_model()
            query_embedding = model.encode(query)
            
            # 获取所有向量
            vectors = KnowledgeVector.objects.all()
            if knowledge_base_id:
                vectors = vectors.filter(knowledge_base_id=knowledge_base_id)
            if content_types:
                vectors = vectors.filter(content_type__in=content_types)
            
            results = []
            
            for vector in vectors[:1000]:  # 限制向量数量以提高性能
                try:
                    vector_data = np.array(vector.vector_data)
                    similarity = np.dot(query_embedding, vector_data) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(vector_data)
                    )
                    
                    if similarity >= similarity_threshold:
                        results.append({
                            'content_type': vector.content_type,
                            'content_id': vector.content_id,
                            'title': vector.metadata.get('document_title', f'{vector.content_type}:{vector.content_id}'),
                            'summary': vector.text_chunk[:200] + '...',
                            'score': float(similarity),
                            'source': 'vector_search',
                            'url': f'/knowledge/{vector.content_type}s/{vector.content_id}/',
                            'highlights': [vector.text_chunk[:100] + '...'],
                            'metadata': vector.metadata
                        })
                        
                except Exception as e:
                    logger.warning(f"向量相似度计算失败: {str(e)}")
                    continue
            
            # 按相似度排序
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"向量搜索执行失败: {str(e)}")
            return []
    
    def _calculate_text_score(self, query: str, title: str, content: str) -> float:
        """计算文本相关性评分"""
        score = 0.0
        query_lower = query.lower()
        title_lower = title.lower()
        content_lower = content.lower()
        
        # 标题匹配权重更高
        if query_lower in title_lower:
            score += 10.0
        
        # 内容匹配
        if query_lower in content_lower:
            score += 5.0
        
        # 词汇匹配
        query_words = query_lower.split()
        for word in query_words:
            if word in title_lower:
                score += 2.0
            if word in content_lower:
                score += 1.0
        
        return score
    
    def _get_highlights(self, query: str, text: str, max_highlights: int = 3) -> List[str]:
        """获取搜索高亮片段"""
        highlights = []
        query_lower = query.lower()
        text_lower = text.lower()
        
        # 查找查询词在文本中的位置
        positions = []
        start = 0
        while True:
            pos = text_lower.find(query_lower, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1
        
        # 生成高亮片段
        for pos in positions[:max_highlights]:
            start = max(0, pos - 50)
            end = min(len(text), pos + len(query) + 50)
            snippet = text[start:end]
            
            # 高亮查询词
            highlighted = re.sub(
                re.escape(query),
                f'<mark>{query}</mark>',
                snippet,
                flags=re.IGNORECASE
            )
            highlights.append(highlighted)
        
        return highlights
    
    def _deduplicate_and_rank(self, results: List[Dict]) -> List[Dict]:
        """去重并重新排序结果"""
        # 使用(content_type, content_id)作为去重键
        seen = set()
        unique_results = []
        
        for result in results:
            key = (result['content_type'], result['content_id'])
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        # 按评分排序
        unique_results.sort(key=lambda x: x['score'], reverse=True)
        return unique_results
    
    def _record_search_access(self, query: str, knowledge_base_id: Optional[int],
                              results_count: int, response_time: float):
        """记录搜索访问"""
        try:
            KnowledgeAccessRecord.objects.create(
                knowledge_base_id=knowledge_base_id,
                access_type='search',
                query_text=query,
                search_results_count=results_count,
                response_time=response_time,
                success=True
            )
        except Exception as e:
            logger.warning(f"记录搜索访问失败: {str(e)}")


class RecommendationService:
    """知识推荐服务"""
    
    def __init__(self):
        self.vectorize_service = VectorizeService()
    
    def generate_recommendations(self, content_type: str, content_id: int,
                                knowledge_base_id: int, limit: int = 10) -> List[Dict]:
        """
        生成内容推荐
        """
        try:
            recommendations = []
            
            # 1. 基于相似内容的推荐
            similar_recommendations = self._get_similar_content_recommendations(
                content_type, content_id, knowledge_base_id, limit // 2
            )
            recommendations.extend(similar_recommendations)
            
            # 2. 基于标签的推荐
            tag_recommendations = self._get_tag_based_recommendations(
                content_type, content_id, knowledge_base_id, limit // 4
            )
            recommendations.extend(tag_recommendations)
            
            # 3. 热门内容推荐
            popular_recommendations = self._get_popular_recommendations(
                content_type, knowledge_base_id, limit // 4
            )
            recommendations.extend(popular_recommendations)
            
            # 去重并排序
            recommendations = self._deduplicate_recommendations(recommendations)
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"生成推荐失败: {content_type}:{content_id} - {str(e)}")
            return []
    
    def _get_similar_content_recommendations(self, content_type: str, content_id: int,
                                             knowledge_base_id: int, limit: int) -> List[Dict]:
        """基于相似内容的推荐"""
        try:
            # 获取源内容的向量
            source_vectors = KnowledgeVector.objects.filter(
                knowledge_base_id=knowledge_base_id,
                content_type=content_type,
                content_id=content_id
            )
            
            if not source_vectors.exists():
                return []
            
            source_vector = source_vectors.first()
            source_embedding = np.array(source_vector.vector_data)
            
            # 查找相似向量
            similar_vectors = KnowledgeVector.objects.filter(
                knowledge_base_id=knowledge_base_id
            ).exclude(
                content_type=content_type,
                content_id=content_id
            )
            
            recommendations = []
            
            for vector in similar_vectors[:500]:  # 限制计算量
                try:
                    vector_embedding = np.array(vector.vector_data)
                    similarity = np.dot(source_embedding, vector_embedding) / (
                        np.linalg.norm(source_embedding) * np.linalg.norm(vector_embedding)
                    )
                    
                    if similarity > 0.7:  # 相似度阈值
                        recommendations.append({
                            'content_type': vector.content_type,
                            'content_id': vector.content_id,
                            'score': float(similarity),
                            'reason': 'similar_content',
                            'similarity': float(similarity)
                        })
                        
                except Exception:
                    continue
            
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            return recommendations[:limit]
            
        except Exception as e:
            logger.warning(f"相似内容推荐失败: {str(e)}")
            return []
    
    def _get_tag_based_recommendations(self, content_type: str, content_id: int,
                                       knowledge_base_id: int, limit: int) -> List[Dict]:
        """基于标签的推荐"""
        try:
            recommendations = []
            
            # 获取源内容的标签
            source_tags = []
            if content_type == 'document':
                doc = Document.objects.get(id=content_id)
                source_tags = list(doc.tags.values_list('id', flat=True))
            elif content_type == 'faq':
                faq = FAQ.objects.get(id=content_id)
                source_tags = list(faq.tags.values_list('id', flat=True))
            elif content_type == 'product':
                product = Product.objects.get(id=content_id)
                source_tags = list(product.tags.values_list('id', flat=True))
            
            if not source_tags:
                return []
            
            # 查找有相同标签的其他内容
            for model_class, model_type in [(Document, 'document'), (FAQ, 'faq'), (Product, 'product')]:
                if model_type == content_type:
                    # 排除自己
                    related_items = model_class.objects.filter(
                        knowledge_base_id=knowledge_base_id,
                        tags__id__in=source_tags,
                        is_active=True
                    ).exclude(id=content_id).distinct()
                else:
                    related_items = model_class.objects.filter(
                        knowledge_base_id=knowledge_base_id,
                        tags__id__in=source_tags,
                        is_active=True
                    ).distinct()
                
                for item in related_items[:limit // 3]:
                    # 计算标签重叠度
                    item_tags = list(item.tags.values_list('id', flat=True))
                    overlap = len(set(source_tags) & set(item_tags))
                    score = overlap / len(source_tags) if source_tags else 0
                    
                    recommendations.append({
                        'content_type': model_type,
                        'content_id': item.id,
                        'score': score,
                        'reason': 'shared_tags',
                        'tag_overlap': overlap
                    })
            
            return recommendations
            
        except Exception as e:
            logger.warning(f"标签推荐失败: {str(e)}")
            return []
    
    def _get_popular_recommendations(self, exclude_content_type: str,
                                     knowledge_base_id: int, limit: int) -> List[Dict]:
        """热门内容推荐"""
        try:
            recommendations = []
            
            # 推荐热门文档
            if exclude_content_type != 'document':
                popular_docs = Document.objects.filter(
                    knowledge_base_id=knowledge_base_id,
                    is_active=True
                ).order_by('-view_count', '-rating')[:limit // 3]
                
                for doc in popular_docs:
                    score = (doc.view_count * 0.01) + (doc.rating * 0.2)
                    recommendations.append({
                        'content_type': 'document',
                        'content_id': doc.id,
                        'score': score,
                        'reason': 'popular_content',
                        'view_count': doc.view_count,
                        'rating': doc.rating
                    })
            
            # 推荐热门FAQ
            if exclude_content_type != 'faq':
                popular_faqs = FAQ.objects.filter(
                    knowledge_base_id=knowledge_base_id,
                    is_active=True,
                    status='published'
                ).order_by('-view_count', '-helpful_count')[:limit // 3]
                
                for faq in popular_faqs:
                    score = (faq.view_count * 0.01) + (faq.helpful_count * 0.1)
                    recommendations.append({
                        'content_type': 'faq',
                        'content_id': faq.id,
                        'score': score,
                        'reason': 'popular_content',
                        'view_count': faq.view_count,
                        'helpful_count': faq.helpful_count
                    })
            
            return recommendations
            
        except Exception as e:
            logger.warning(f"热门推荐失败: {str(e)}")
            return []
    
    def _deduplicate_recommendations(self, recommendations: List[Dict]) -> List[Dict]:
        """去重推荐结果"""
        seen = set()
        unique_recommendations = []
        
        for rec in recommendations:
            key = (rec['content_type'], rec['content_id'])
            if key not in seen:
                seen.add(key)
                unique_recommendations.append(rec)
        
        return unique_recommendations


class KnowledgeAnalyticsService:
    """知识分析统计服务"""
    
    def get_knowledge_base_analytics(self, knowledge_base_id: int,
                                     date_from: Optional[datetime] = None,
                                     date_to: Optional[datetime] = None) -> Dict[str, Any]:
        """获取知识库分析数据"""
        try:
            if not date_from:
                date_from = timezone.now() - timedelta(days=30)
            if not date_to:
                date_to = timezone.now()
            
            knowledge_base = KnowledgeBase.objects.get(id=knowledge_base_id)
            
            # 基础统计
            total_documents = knowledge_base.documents.filter(is_active=True).count()
            total_faqs = knowledge_base.faqs.filter(is_active=True).count()
            total_products = knowledge_base.products.count()
            total_scripts = knowledge_base.scripts.filter(is_active=True).count()
            
            # 访问统计
            access_records = KnowledgeAccessRecord.objects.filter(
                knowledge_base=knowledge_base,
                created_at__range=[date_from, date_to]
            )
            
            total_views = access_records.filter(access_type='view').count()
            total_searches = access_records.filter(access_type='search').count()
            total_downloads = access_records.filter(access_type='download').count()
            
            # 热门内容
            popular_documents = Document.objects.filter(
                knowledge_base=knowledge_base,
                is_active=True
            ).order_by('-view_count')[:10]
            
            popular_faqs = FAQ.objects.filter(
                knowledge_base=knowledge_base,
                is_active=True
            ).order_by('-view_count')[:10]
            
            # 搜索热词
            search_queries = access_records.filter(
                access_type='search',
                query_text__isnull=False
            ).values_list('query_text', flat=True)
            
            # 简单的热词统计
            query_freq = {}
            for query in search_queries:
                query_freq[query] = query_freq.get(query, 0) + 1
            
            top_queries = sorted(query_freq.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                'knowledge_base_id': knowledge_base_id,
                'knowledge_base_name': knowledge_base.name,
                'period': {
                    'from': date_from.isoformat(),
                    'to': date_to.isoformat()
                },
                'content_stats': {
                    'total_documents': total_documents,
                    'total_faqs': total_faqs,
                    'total_products': total_products,
                    'total_scripts': total_scripts
                },
                'access_stats': {
                    'total_views': total_views,
                    'total_searches': total_searches,
                    'total_downloads': total_downloads
                },
                'popular_content': {
                    'documents': [{'id': doc.id, 'title': doc.title, 'views': doc.view_count} for doc in popular_documents],
                    'faqs': [{'id': faq.id, 'question': faq.question[:100], 'views': faq.view_count} for faq in popular_faqs]
                },
                'top_search_queries': [{'query': query, 'count': count} for query, count in top_queries]
            }
            
        except Exception as e:
            logger.error(f"知识库分析统计失败: {knowledge_base_id} - {str(e)}")
            return {
                'error': str(e),
                'knowledge_base_id': knowledge_base_id
            } 