"""
知识库同步服务
用于定时或手动同步数据库中的数据到向量库和RAGFlow
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from celery import shared_task

from .models import (
    KnowledgeBase, Script, Product, Document, FAQ, 
    KnowledgeVector
)
from .vector_services import KnowledgeVectorService
from .ragflow_client import KnowledgeRAGFlowSync
from .config import get_ragflow_config, is_ragflow_enabled

logger = logging.getLogger(__name__)

class KnowledgeBaseSyncService:
    """知识库同步服务"""
    
    def __init__(self):
        self.vector_service = KnowledgeVectorService()
        self.ragflow_sync = KnowledgeRAGFlowSync()
    
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