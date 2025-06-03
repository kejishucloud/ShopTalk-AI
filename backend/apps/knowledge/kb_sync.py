"""
知识库同步服务 - 将数据同步到RAGFlow
"""

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from django.utils import timezone
from django.db import transaction
from django.db import models
from celery import shared_task

from .models import KnowledgeBase, Script, Product, KnowledgeVector
from .ragflow_client import ragflow_client, RAGFlowError

logger = logging.getLogger(__name__)

class KnowledgeBaseSyncService:
    """知识库同步服务"""
    
    def __init__(self):
        self.vector_service = KnowledgeVectorService()
        self.ragflow_sync = KnowledgeRAGFlowSync()
        self.client = ragflow_client
    
    def sync_all_knowledge_bases(self) -> Dict[str, int]:
        """同步所有知识库"""
        results = {
            'synced_kbs': 0,
            'synced_scripts': 0,
            'synced_products': 0,
            'synced_documents': 0,
            'synced_faqs': 0,
            'errors': 0
        }
        
        knowledge_bases = KnowledgeBase.objects.filter(is_active=True)
        
        for kb in knowledge_bases:
            try:
                self.sync_knowledge_base(kb.id)
                results['synced_kbs'] += 1
                
                # 同步各类内容
                script_count = self.sync_scripts(kb.id)
                product_count = self.sync_products(kb.id)
                document_count = self.sync_documents(kb.id)
                faq_count = self.sync_faqs(kb.id)
                
                results['synced_scripts'] += script_count
                results['synced_products'] += product_count
                results['synced_documents'] += document_count
                results['synced_faqs'] += faq_count
                
            except Exception as e:
                logger.error(f"同步知识库{kb.id}失败: {e}")
                results['errors'] += 1
        
        return results
    
    def sync_knowledge_base(self, kb_id: int) -> bool:
        """同步单个知识库"""
        try:
            kb = KnowledgeBase.objects.get(id=kb_id)
            
            # 创建向量集合
            self.vector_service.create_knowledge_base_collection(kb.id, kb.name)
            
            # 同步到RAGFlow
            if is_ragflow_enabled():
                self.ragflow_sync.sync_knowledge_base(
                    kb.id, kb.name, kb.knowledge_type
                )
            
            logger.info(f"知识库{kb.id}同步成功")
            return True
            
        except Exception as e:
            logger.error(f"同步知识库{kb_id}失败: {e}")
            return False
    
    def sync_scripts(self, kb_id: int, script_ids: List[int] = None) -> int:
        """同步话术数据"""
        try:
            # 获取要同步的话术
            queryset = Script.objects.filter(
                knowledge_base_id=kb_id,
                is_active=True
            )
            
            if script_ids:
                queryset = queryset.filter(id__in=script_ids)
            
            synced_count = 0
            
            for script in queryset:
                try:
                    # 分块文本
                    chunks = self.vector_service.chunk_text(script.content, 'scripts')
                    
                    # 准备元数据
                    metadata = {
                        'script_type': script.script_type,
                        'name': script.name,
                        'priority': script.priority,
                        'usage_count': script.usage_count,
                        'created_at': script.created_at.isoformat(),
                        'updated_at': script.updated_at.isoformat(),
                    }
                    
                    # 添加到向量库
                    self.vector_service.add_content_vectors(
                        kb_id, 'script', script.id, chunks, metadata
                    )
                    
                    # 同步到RAGFlow
                    if is_ragflow_enabled():
                        self.ragflow_sync.sync_script(
                            kb_id, script.id, script.name, 
                            script.script_type, script.content, metadata
                        )
                    
                    synced_count += 1
                    logger.info(f"话术{script.id}同步成功")
                    
                except Exception as e:
                    logger.error(f"同步话术{script.id}失败: {e}")
            
            return synced_count
            
        except Exception as e:
            logger.error(f"同步知识库{kb_id}话术失败: {e}")
            return 0
    
    def sync_products(self, kb_id: int, product_ids: List[int] = None) -> int:
        """同步产品数据"""
        try:
            # 获取要同步的产品
            queryset = Product.objects.filter(
                knowledge_base_id=kb_id,
                status='active'
            )
            
            if product_ids:
                queryset = queryset.filter(id__in=product_ids)
            
            synced_count = 0
            
            for product in queryset:
                try:
                    # 构建产品文本内容
                    product_text = f"""
                    产品名称: {product.name}
                    产品SKU: {product.sku}
                    品牌: {product.brand}
                    分类: {product.product_category}
                    价格: {product.price}
                    描述: {product.description}
                    简短描述: {product.short_description}
                    """
                    
                    # 添加规格信息
                    if product.specifications:
                        product_text += "\n规格参数:\n"
                        for key, value in product.specifications.items():
                            product_text += f"- {key}: {value}\n"
                    
                    # 添加属性信息
                    if product.attributes:
                        product_text += "\n产品属性:\n"
                        for key, value in product.attributes.items():
                            product_text += f"- {key}: {value}\n"
                    
                    # 添加卖点
                    if product.sales_points:
                        product_text += "\n产品卖点:\n"
                        for point in product.sales_points:
                            product_text += f"- {point}\n"
                    
                    # 分块文本
                    chunks = self.vector_service.chunk_text(product_text, 'products')
                    
                    # 准备元数据
                    metadata = {
                        'sku': product.sku,
                        'name': product.name,
                        'brand': product.brand,
                        'category': product.product_category,
                        'price': float(product.price),
                        'stock_quantity': product.stock_quantity,
                        'status': product.status,
                        'sales_count': product.sales_count,
                        'view_count': product.view_count,
                        'created_at': product.created_at.isoformat(),
                        'updated_at': product.updated_at.isoformat(),
                    }
                    
                    # 添加到向量库
                    self.vector_service.add_content_vectors(
                        kb_id, 'product', product.id, chunks, metadata
                    )
                    
                    # 同步到RAGFlow
                    if is_ragflow_enabled():
                        self.ragflow_sync.sync_product(
                            kb_id, product.id, product.name, 
                            product.description, product.specifications, metadata
                        )
                    
                    synced_count += 1
                    logger.info(f"产品{product.id}同步成功")
                    
                except Exception as e:
                    logger.error(f"同步产品{product.id}失败: {e}")
            
            return synced_count
            
        except Exception as e:
            logger.error(f"同步知识库{kb_id}产品失败: {e}")
            return 0
    
    def sync_documents(self, kb_id: int, document_ids: List[int] = None) -> int:
        """同步文档数据"""
        try:
            # 获取要同步的文档
            queryset = Document.objects.filter(
                knowledge_base_id=kb_id,
                is_active=True,
                process_status='completed'
            )
            
            if document_ids:
                queryset = queryset.filter(id__in=document_ids)
            
            synced_count = 0
            
            for document in queryset:
                try:
                    # 使用提取的文本或原始内容
                    content = document.extracted_text or document.content
                    if not content:
                        logger.warning(f"文档{document.id}没有可用内容")
                        continue
                    
                    # 分块文本
                    chunks = self.vector_service.chunk_text(content, 'documents')
                    
                    # 准备元数据
                    metadata = {
                        'title': document.title,
                        'document_type': document.document_type,
                        'file_size': document.file_size,
                        'language': document.language,
                        'view_count': document.view_count,
                        'rating': document.rating,
                        'is_featured': document.is_featured,
                        'is_public': document.is_public,
                        'created_at': document.created_at.isoformat(),
                        'updated_at': document.updated_at.isoformat(),
                    }
                    
                    # 添加关键词
                    if document.keywords:
                        metadata['keywords'] = document.keywords
                    
                    # 添加到向量库
                    self.vector_service.add_content_vectors(
                        kb_id, 'document', document.id, chunks, metadata
                    )
                    
                    # 同步到RAGFlow
                    if is_ragflow_enabled():
                        self.ragflow_sync.sync_document(
                            kb_id, document.id, document.title, content, metadata
                        )
                    
                    synced_count += 1
                    logger.info(f"文档{document.id}同步成功")
                    
                except Exception as e:
                    logger.error(f"同步文档{document.id}失败: {e}")
            
            return synced_count
            
        except Exception as e:
            logger.error(f"同步知识库{kb_id}文档失败: {e}")
            return 0
    
    def sync_faqs(self, kb_id: int, faq_ids: List[int] = None) -> int:
        """同步FAQ数据"""
        try:
            # 获取要同步的FAQ
            queryset = FAQ.objects.filter(
                knowledge_base_id=kb_id,
                is_active=True,
                status='published'
            )
            
            if faq_ids:
                queryset = queryset.filter(id__in=faq_ids)
            
            synced_count = 0
            
            for faq in queryset:
                try:
                    # 构建FAQ文本
                    faq_text = f"问题: {faq.question}\n\n答案: {faq.answer}"
                    
                    # 分块文本
                    chunks = self.vector_service.chunk_text(faq_text, 'faqs')
                    
                    # 准备元数据
                    metadata = {
                        'question': faq.question,
                        'faq_category': faq.faq_category,
                        'priority': faq.priority,
                        'view_count': faq.view_count,
                        'helpful_count': faq.helpful_count,
                        'unhelpful_count': faq.unhelpful_count,
                        'confidence_score': faq.confidence_score,
                        'auto_generated': faq.auto_generated,
                        'created_at': faq.created_at.isoformat(),
                        'updated_at': faq.updated_at.isoformat(),
                    }
                    
                    # 添加关键词
                    if faq.keywords:
                        metadata['keywords'] = faq.keywords
                    
                    # 添加到向量库
                    self.vector_service.add_content_vectors(
                        kb_id, 'faq', faq.id, chunks, metadata
                    )
                    
                    # 同步到RAGFlow
                    if is_ragflow_enabled():
                        self.ragflow_sync.sync_faq(
                            kb_id, faq.id, faq.question, faq.answer, metadata
                        )
                    
                    synced_count += 1
                    logger.info(f"FAQ{faq.id}同步成功")
                    
                except Exception as e:
                    logger.error(f"同步FAQ{faq.id}失败: {e}")
            
            return synced_count
            
        except Exception as e:
            logger.error(f"同步知识库{kb_id} FAQ失败: {e}")
            return 0
    
    def sync_updated_content(self, hours: int = 24) -> Dict[str, int]:
        """同步最近更新的内容"""
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        results = {
            'synced_scripts': 0,
            'synced_products': 0,
            'synced_documents': 0,
            'synced_faqs': 0,
            'errors': 0
        }
        
        try:
            # 获取活跃的知识库
            active_kbs = KnowledgeBase.objects.filter(is_active=True)
            
            for kb in active_kbs:
                try:
                    # 同步更新的话术
                    updated_scripts = Script.objects.filter(
                        knowledge_base=kb,
                        is_active=True,
                        updated_at__gte=cutoff_time
                    ).values_list('id', flat=True)
                    
                    if updated_scripts:
                        results['synced_scripts'] += self.sync_scripts(
                            kb.id, list(updated_scripts)
                        )
                    
                    # 同步更新的产品
                    updated_products = Product.objects.filter(
                        knowledge_base=kb,
                        status='active',
                        updated_at__gte=cutoff_time
                    ).values_list('id', flat=True)
                    
                    if updated_products:
                        results['synced_products'] += self.sync_products(
                            kb.id, list(updated_products)
                        )
                    
                    # 同步更新的文档
                    updated_documents = Document.objects.filter(
                        knowledge_base=kb,
                        is_active=True,
                        process_status='completed',
                        updated_at__gte=cutoff_time
                    ).values_list('id', flat=True)
                    
                    if updated_documents:
                        results['synced_documents'] += self.sync_documents(
                            kb.id, list(updated_documents)
                        )
                    
                    # 同步更新的FAQ
                    updated_faqs = FAQ.objects.filter(
                        knowledge_base=kb,
                        is_active=True,
                        status='published',
                        updated_at__gte=cutoff_time
                    ).values_list('id', flat=True)
                    
                    if updated_faqs:
                        results['synced_faqs'] += self.sync_faqs(
                            kb.id, list(updated_faqs)
                        )
                        
                except Exception as e:
                    logger.error(f"同步知识库{kb.id}更新内容失败: {e}")
                    results['errors'] += 1
            
        except Exception as e:
            logger.error(f"同步更新内容失败: {e}")
            results['errors'] += 1
        
        return results
    
    def delete_content_vectors(self, kb_id: int, content_type: str, content_id: int):
        """删除内容向量"""
        try:
            # 从向量库删除
            self.vector_service.delete_content_vectors(kb_id, content_type, content_id)
            
            # 从数据库删除向量记录
            KnowledgeVector.objects.filter(
                knowledge_base_id=kb_id,
                content_type=content_type,
                content_id=content_id
            ).delete()
            
            logger.info(f"删除{content_type}_{content_id}的向量成功")
            
        except Exception as e:
            logger.error(f"删除{content_type}_{content_id}的向量失败: {e}")

# Celery任务定义
@shared_task(bind=True)
def sync_all_knowledge_bases_task(self):
    """同步所有知识库的Celery任务"""
    try:
        sync_service = KnowledgeBaseSyncService()
        results = sync_service.sync_all_knowledge_bases()
        
        logger.info(f"知识库全量同步完成: {results}")
        return results
        
    except Exception as e:
        logger.error(f"知识库全量同步任务失败: {e}")
        raise

@shared_task(bind=True)
def sync_updated_content_task(self, hours=24):
    """同步更新内容的Celery任务"""
    try:
        sync_service = KnowledgeBaseSyncService()
        results = sync_service.sync_updated_content(hours)
        
        logger.info(f"知识库增量同步完成: {results}")
        return results
        
    except Exception as e:
        logger.error(f"知识库增量同步任务失败: {e}")
        raise

@shared_task(bind=True)
def sync_knowledge_base_task(self, kb_id):
    """同步单个知识库的Celery任务"""
    try:
        sync_service = KnowledgeBaseSyncService()
        
        # 同步知识库
        sync_service.sync_knowledge_base(kb_id)
        
        # 同步所有内容
        results = {
            'synced_scripts': sync_service.sync_scripts(kb_id),
            'synced_products': sync_service.sync_products(kb_id),
            'synced_documents': sync_service.sync_documents(kb_id),
            'synced_faqs': sync_service.sync_faqs(kb_id),
        }
        
        logger.info(f"知识库{kb_id}同步完成: {results}")
        return results
        
    except Exception as e:
        logger.error(f"知识库{kb_id}同步任务失败: {e}")
        raise

@shared_task(bind=True)
def sync_single_content_task(self, kb_id, content_type, content_id):
    """同步单个内容的Celery任务"""
    try:
        sync_service = KnowledgeBaseSyncService()
        
        if content_type == 'script':
            result = sync_service.sync_scripts(kb_id, [content_id])
        elif content_type == 'product':
            result = sync_service.sync_products(kb_id, [content_id])
        elif content_type == 'document':
            result = sync_service.sync_documents(kb_id, [content_id])
        elif content_type == 'faq':
            result = sync_service.sync_faqs(kb_id, [content_id])
        else:
            raise ValueError(f"不支持的内容类型: {content_type}")
        
        logger.info(f"内容{content_type}_{content_id}同步完成")
        return {'synced_count': result}
        
    except Exception as e:
        logger.error(f"内容{content_type}_{content_id}同步任务失败: {e}")
        raise

class KnowledgeBaseSync:
    """知识库同步服务"""
    
    def __init__(self):
        self.client = ragflow_client
    
    def sync_knowledge_base_to_ragflow(self, kb: KnowledgeBase) -> bool:
        """
        将知识库同步到RAGFlow
        
        Args:
            kb: 知识库实例
            
        Returns:
            同步是否成功
        """
        try:
            # 如果已有RAGFlow知识库ID，先检查是否存在
            if kb.ragflow_kb_id:
                logger.info(f"知识库 {kb.name} 已有RAGFlow ID: {kb.ragflow_kb_id}")
                return True
            
            # 创建RAGFlow知识库
            result = self.client.create_knowledge_base(
                name=f"{kb.name}_{kb.id}",
                description=kb.description,
                embedding_model=kb.embedding_model,
                chunk_method=kb.chunk_method
            )
            
            # 保存RAGFlow知识库ID
            if result and 'id' in result:
                kb.ragflow_kb_id = result['id']
                kb.save(update_fields=['ragflow_kb_id'])
                logger.info(f"成功创建RAGFlow知识库: {kb.name} -> {result['id']}")
                return True
            else:
                logger.error(f"创建RAGFlow知识库失败: {kb.name}")
                return False
                
        except Exception as e:
            logger.error(f"同步知识库到RAGFlow失败: {e}")
            return False
    
    def sync_script_to_ragflow(self, script: Script) -> bool:
        """
        将话术同步到RAGFlow
        
        Args:
            script: 话术实例
            
        Returns:
            同步是否成功
        """
        try:
            # 确保知识库已同步
            if not script.knowledge_base.ragflow_kb_id:
                if not self.sync_knowledge_base_to_ragflow(script.knowledge_base):
                    return False
            
            # 准备文档内容
            content = script.get_text_for_vectorization()
            file_name = f"script_{script.id}_{script.name}.txt"
            
            # 上传到RAGFlow
            result = self.client.upload_document(
                kb_id=script.knowledge_base.ragflow_kb_id,
                file_name=file_name,
                file_content=content,
                file_type="text"
            )
            
            if result and 'id' in result:
                # 保存RAGFlow文档ID
                script.ragflow_document_id = result['id']
                script.mark_vector_synced()
                
                logger.info(f"成功同步话术到RAGFlow: {script.name} -> {result['id']}")
                return True
            else:
                logger.error(f"同步话术到RAGFlow失败: {script.name}")
                return False
                
        except Exception as e:
            logger.error(f"同步话术到RAGFlow失败: {e}")
            return False
    
    def sync_product_to_ragflow(self, product: Product) -> bool:
        """
        将产品同步到RAGFlow
        
        Args:
            product: 产品实例
            
        Returns:
            同步是否成功
        """
        try:
            # 确保知识库已同步
            if not product.knowledge_base.ragflow_kb_id:
                if not self.sync_knowledge_base_to_ragflow(product.knowledge_base):
                    return False
            
            # 准备文档内容
            content = product.get_text_for_vectorization()
            file_name = f"product_{product.id}_{product.sku}.txt"
            
            # 上传到RAGFlow
            result = self.client.upload_document(
                kb_id=product.knowledge_base.ragflow_kb_id,
                file_name=file_name,
                file_content=content,
                file_type="text"
            )
            
            if result and 'id' in result:
                # 保存RAGFlow文档ID
                product.ragflow_document_id = result['id']
                product.mark_vector_synced()
                
                logger.info(f"成功同步产品到RAGFlow: {product.name} -> {result['id']}")
                return True
            else:
                logger.error(f"同步产品到RAGFlow失败: {product.name}")
                return False
                
        except Exception as e:
            logger.error(f"同步产品到RAGFlow失败: {e}")
            return False
    
    def batch_sync_scripts(self, knowledge_base_id: int, limit: int = 50) -> Dict[str, int]:
        """
        批量同步话术
        
        Args:
            knowledge_base_id: 知识库ID
            limit: 每次同步的数量限制
            
        Returns:
            同步结果统计
        """
        try:
            kb = KnowledgeBase.objects.get(id=knowledge_base_id)
            
            # 获取需要同步的话术
            scripts = Script.objects.filter(
                knowledge_base=kb,
                status='active'
            ).filter(
                models.Q(vector_synced=False) | 
                models.Q(updated_at__gt=models.F('last_sync_time'))
            )[:limit]
            
            success_count = 0
            failed_count = 0
            
            for script in scripts:
                if self.sync_script_to_ragflow(script):
                    success_count += 1
                else:
                    failed_count += 1
            
            logger.info(f"批量同步话术完成: 成功 {success_count}, 失败 {failed_count}")
            
            return {
                'success': success_count,
                'failed': failed_count,
                'total': success_count + failed_count
            }
            
        except Exception as e:
            logger.error(f"批量同步话术失败: {e}")
            return {'success': 0, 'failed': 0, 'total': 0}
    
    def batch_sync_products(self, knowledge_base_id: int, limit: int = 50) -> Dict[str, int]:
        """
        批量同步产品
        
        Args:
            knowledge_base_id: 知识库ID
            limit: 每次同步的数量限制
            
        Returns:
            同步结果统计
        """
        try:
            kb = KnowledgeBase.objects.get(id=knowledge_base_id)
            
            # 获取需要同步的产品
            products = Product.objects.filter(
                knowledge_base=kb,
                status='active'
            ).filter(
                models.Q(vector_synced=False) | 
                models.Q(updated_at__gt=models.F('last_sync_time'))
            )[:limit]
            
            success_count = 0
            failed_count = 0
            
            for product in products:
                if self.sync_product_to_ragflow(product):
                    success_count += 1
                else:
                    failed_count += 1
            
            logger.info(f"批量同步产品完成: 成功 {success_count}, 失败 {failed_count}")
            
            return {
                'success': success_count,
                'failed': failed_count,
                'total': success_count + failed_count
            }
            
        except Exception as e:
            logger.error(f"批量同步产品失败: {e}")
            return {'success': 0, 'failed': 0, 'total': 0}
    
    def search_ragflow(self, knowledge_base_id: int, query: str, top_k: int = 10) -> List[Dict]:
        """
        在RAGFlow中搜索知识
        
        Args:
            knowledge_base_id: 知识库ID
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        try:
            kb = KnowledgeBase.objects.get(id=knowledge_base_id)
            
            if not kb.ragflow_kb_id:
                logger.warning(f"知识库 {kb.name} 未同步到RAGFlow")
                return []
            
            # 在RAGFlow中搜索
            results = self.client.get_retrieval_result(
                kb_id=kb.ragflow_kb_id,
                query=query,
                top_k=top_k
            )
            
            return results
            
        except Exception as e:
            logger.error(f"RAGFlow搜索失败: {e}")
            return []
    
    def delete_from_ragflow(self, ragflow_kb_id: str, ragflow_doc_id: str) -> bool:
        """
        从RAGFlow删除文档
        
        Args:
            ragflow_kb_id: RAGFlow知识库ID
            ragflow_doc_id: RAGFlow文档ID
            
        Returns:
            删除是否成功
        """
        try:
            return self.client.delete_document(ragflow_kb_id, ragflow_doc_id)
        except Exception as e:
            logger.error(f"从RAGFlow删除文档失败: {e}")
            return False
    
    def get_sync_status(self, knowledge_base_id: int) -> Dict[str, Any]:
        """
        获取知识库同步状态
        
        Args:
            knowledge_base_id: 知识库ID
            
        Returns:
            同步状态信息
        """
        try:
            kb = KnowledgeBase.objects.get(id=knowledge_base_id)
            
            # 统计话术同步状态
            total_scripts = Script.objects.filter(knowledge_base=kb, status='active').count()
            synced_scripts = Script.objects.filter(
                knowledge_base=kb, 
                status='active',
                vector_synced=True
            ).count()
            
            # 统计产品同步状态
            total_products = Product.objects.filter(knowledge_base=kb, status='active').count()
            synced_products = Product.objects.filter(
                knowledge_base=kb,
                status='active', 
                vector_synced=True
            ).count()
            
            return {
                'knowledge_base': {
                    'id': kb.id,
                    'name': kb.name,
                    'ragflow_kb_id': kb.ragflow_kb_id,
                    'ragflow_synced': bool(kb.ragflow_kb_id)
                },
                'scripts': {
                    'total': total_scripts,
                    'synced': synced_scripts,
                    'pending': total_scripts - synced_scripts,
                    'sync_rate': (synced_scripts / total_scripts * 100) if total_scripts > 0 else 0
                },
                'products': {
                    'total': total_products,
                    'synced': synced_products,
                    'pending': total_products - synced_products,
                    'sync_rate': (synced_products / total_products * 100) if total_products > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"获取同步状态失败: {e}")
            return {}

# 创建全局同步服务实例
kb_sync_service = KnowledgeBaseSync()

# Celery任务
@shared_task(bind=True, max_retries=3)
def sync_knowledge_base_task(self, kb_id: int):
    """异步同步知识库任务"""
    try:
        kb = KnowledgeBase.objects.get(id=kb_id)
        success = kb_sync_service.sync_knowledge_base_to_ragflow(kb)
        
        if success:
            logger.info(f"知识库同步任务完成: {kb.name}")
            return {"status": "success", "kb_id": kb_id}
        else:
            raise Exception("同步失败")
            
    except Exception as e:
        logger.error(f"知识库同步任务失败: {e}")
        raise self.retry(countdown=60 * (self.request.retries + 1))

@shared_task(bind=True, max_retries=3)
def sync_script_task(self, script_id: int):
    """异步同步话术任务"""
    try:
        script = Script.objects.get(id=script_id)
        success = kb_sync_service.sync_script_to_ragflow(script)
        
        if success:
            logger.info(f"话术同步任务完成: {script.name}")
            return {"status": "success", "script_id": script_id}
        else:
            raise Exception("同步失败")
            
    except Exception as e:
        logger.error(f"话术同步任务失败: {e}")
        raise self.retry(countdown=60 * (self.request.retries + 1))

@shared_task(bind=True, max_retries=3)
def sync_product_task(self, product_id: int):
    """异步同步产品任务"""
    try:
        product = Product.objects.get(id=product_id)
        success = kb_sync_service.sync_product_to_ragflow(product)
        
        if success:
            logger.info(f"产品同步任务完成: {product.name}")
            return {"status": "success", "product_id": product_id}
        else:
            raise Exception("同步失败")
            
    except Exception as e:
        logger.error(f"产品同步任务失败: {e}")
        raise self.retry(countdown=60 * (self.request.retries + 1))

@shared_task
def batch_sync_knowledge_base_task(kb_id: int):
    """批量同步知识库内容任务"""
    try:
        # 同步话术
        script_result = kb_sync_service.batch_sync_scripts(kb_id, limit=100)
        
        # 同步产品
        product_result = kb_sync_service.batch_sync_products(kb_id, limit=100)
        
        logger.info(f"批量同步完成 - 话术: {script_result}, 产品: {product_result}")
        
        return {
            "status": "success",
            "kb_id": kb_id,
            "scripts": script_result,
            "products": product_result
        }
        
    except Exception as e:
        logger.error(f"批量同步任务失败: {e}")
        return {"status": "failed", "error": str(e)} 