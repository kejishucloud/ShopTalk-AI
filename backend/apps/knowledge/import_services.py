"""
知识库批量导入服务
支持CSV、JSON、Excel格式的话术和产品数据导入
"""
import json
import csv
import io
import logging
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.utils import timezone
from celery import shared_task

from .models import KnowledgeBase, Script, Product, DocumentTag
from .config import get_import_config
from .kb_sync import sync_single_content_task

logger = logging.getLogger(__name__)

class ImportResult:
    """导入结果"""
    def __init__(self):
        self.success_count = 0
        self.error_count = 0
        self.warnings = []
        self.errors = []
        self.created_items = []
    
    def add_success(self, item_id: int, item_name: str):
        """添加成功记录"""
        self.success_count += 1
        self.created_items.append({'id': item_id, 'name': item_name})
    
    def add_error(self, row_num: int, error: str):
        """添加错误记录"""
        self.error_count += 1
        self.errors.append({'row': row_num, 'error': error})
    
    def add_warning(self, row_num: int, warning: str):
        """添加警告记录"""
        self.warnings.append({'row': row_num, 'warning': warning})
    
    def to_dict(self) -> Dict:
        """转为字典"""
        return {
            'success_count': self.success_count,
            'error_count': self.error_count,
            'total_processed': self.success_count + self.error_count,
            'warnings': self.warnings,
            'errors': self.errors,
            'created_items': self.created_items
        }

class BaseImportService:
    """导入服务基类"""
    
    def __init__(self, knowledge_base_id: int, user_id: int):
        self.knowledge_base_id = knowledge_base_id
        self.user_id = user_id
        self.config = get_import_config()
        
        try:
            self.knowledge_base = KnowledgeBase.objects.get(id=knowledge_base_id)
        except KnowledgeBase.DoesNotExist:
            raise ValueError(f"知识库{knowledge_base_id}不存在")
    
    def validate_file(self, file: UploadedFile, allowed_formats: List[str]) -> bool:
        """验证文件"""
        # 检查文件大小
        if file.size > self.config['max_file_size']:
            raise ValueError(f"文件大小超过限制: {file.size} > {self.config['max_file_size']}")
        
        # 检查文件格式
        file_ext = file.name.split('.')[-1].lower()
        if file_ext not in allowed_formats:
            raise ValueError(f"不支持的文件格式: {file_ext}, 支持的格式: {allowed_formats}")
        
        return True
    
    def parse_file(self, file: UploadedFile) -> List[Dict]:
        """解析文件内容"""
        file_ext = file.name.split('.')[-1].lower()
        
        if file_ext == 'csv':
            return self._parse_csv(file)
        elif file_ext == 'json':
            return self._parse_json(file)
        elif file_ext in ['xlsx', 'xls']:
            return self._parse_excel(file)
        else:
            raise ValueError(f"不支持的文件格式: {file_ext}")
    
    def _parse_csv(self, file: UploadedFile) -> List[Dict]:
        """解析CSV文件"""
        try:
            # 检测编码
            file.seek(0)
            sample = file.read(1024)
            file.seek(0)
            
            encoding = 'utf-8'
            if self.config['encoding_detection']:
                try:
                    import chardet
                    detected = chardet.detect(sample)
                    if detected['confidence'] > 0.7:
                        encoding = detected['encoding']
                except ImportError:
                    pass
            
            # 读取CSV
            content = file.read().decode(encoding)
            csv_file = io.StringIO(content)
            reader = csv.DictReader(csv_file)
            
            return [row for row in reader]
            
        except Exception as e:
            raise ValueError(f"CSV文件解析失败: {e}")
    
    def _parse_json(self, file: UploadedFile) -> List[Dict]:
        """解析JSON文件"""
        try:
            content = file.read().decode('utf-8')
            data = json.loads(content)
            
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]
            else:
                raise ValueError("JSON文件格式错误，应为数组或对象")
                
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON文件解析失败: {e}")
    
    def _parse_excel(self, file: UploadedFile) -> List[Dict]:
        """解析Excel文件"""
        try:
            df = pd.read_excel(file, engine='openpyxl')
            return df.to_dict('records')
            
        except Exception as e:
            raise ValueError(f"Excel文件解析失败: {e}")
    
    def get_or_create_tags(self, tag_names: List[str]) -> List[DocumentTag]:
        """获取或创建标签"""
        tags = []
        
        for tag_name in tag_names:
            tag_name = tag_name.strip()
            if not tag_name:
                continue
                
            tag, created = DocumentTag.objects.get_or_create(
                knowledge_base=self.knowledge_base,
                name=tag_name,
                defaults={'usage_count': 0}
            )
            
            if not created:
                tag.usage_count += 1
                tag.save(update_fields=['usage_count'])
            
            tags.append(tag)
        
        return tags

class ScriptImportService(BaseImportService):
    """话术导入服务"""
    
    REQUIRED_FIELDS = ['name', 'script_type', 'content']
    OPTIONAL_FIELDS = ['priority', 'status', 'tags', 'variables', 'conditions']
    
    def import_from_file(self, file: UploadedFile) -> ImportResult:
        """从文件导入话术"""
        result = ImportResult()
        
        try:
            # 验证文件
            allowed_formats = self.config['allowed_formats']['scripts']
            self.validate_file(file, allowed_formats)
            
            # 解析文件
            data = self.parse_file(file)
            
            # 批量导入
            result = self.batch_import(data)
            
        except Exception as e:
            result.add_error(0, f"文件处理失败: {e}")
        
        return result
    
    def batch_import(self, data: List[Dict]) -> ImportResult:
        """批量导入话术数据"""
        result = ImportResult()
        batch_size = self.config['batch_size']
        
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            batch_result = self._import_batch(batch, i)
            
            # 合并结果
            result.success_count += batch_result.success_count
            result.error_count += batch_result.error_count
            result.warnings.extend(batch_result.warnings)
            result.errors.extend(batch_result.errors)
            result.created_items.extend(batch_result.created_items)
        
        return result
    
    def _import_batch(self, batch: List[Dict], start_index: int) -> ImportResult:
        """导入单个批次"""
        result = ImportResult()
        
        with transaction.atomic():
            for idx, row in enumerate(batch):
                row_num = start_index + idx + 1
                
                try:
                    script = self._create_script_from_row(row, row_num, result)
                    if script:
                        result.add_success(script.id, script.name)
                        
                        # 异步同步到向量库和RAGFlow
                        sync_single_content_task.delay(
                            self.knowledge_base_id, 'script', script.id
                        )
                        
                except Exception as e:
                    result.add_error(row_num, str(e))
        
        return result
    
    def _create_script_from_row(self, row: Dict, row_num: int, result: ImportResult) -> Optional[Script]:
        """从行数据创建话术"""
        # 验证必填字段
        for field in self.REQUIRED_FIELDS:
            if not row.get(field):
                raise ValueError(f"缺少必填字段: {field}")
        
        # 验证话术类型
        script_type = row['script_type']
        valid_types = [choice[0] for choice in Script.ScriptType.choices]
        if script_type not in valid_types:
            raise ValueError(f"无效的话术类型: {script_type}")
        
        # 检查重复
        if Script.objects.filter(
            knowledge_base=self.knowledge_base,
            name=row['name'],
            script_type=script_type
        ).exists():
            result.add_warning(row_num, f"话术已存在，跳过: {row['name']}")
            return None
        
        # 创建话术
        script_data = {
            'knowledge_base': self.knowledge_base,
            'name': row['name'],
            'script_type': script_type,
            'content': row['content'],
            'priority': int(row.get('priority', 0)),
            'status': row.get('status', 'draft'),
            'created_by_id': self.user_id,
        }
        
        # 处理变量
        if row.get('variables'):
            try:
                if isinstance(row['variables'], str):
                    script_data['variables'] = json.loads(row['variables'])
                else:
                    script_data['variables'] = row['variables']
            except (json.JSONDecodeError, TypeError):
                result.add_warning(row_num, "变量格式错误，使用默认值")
                script_data['variables'] = {}
        
        # 处理条件
        if row.get('conditions'):
            try:
                if isinstance(row['conditions'], str):
                    script_data['conditions'] = json.loads(row['conditions'])
                else:
                    script_data['conditions'] = row['conditions']
            except (json.JSONDecodeError, TypeError):
                result.add_warning(row_num, "条件格式错误，使用默认值")
                script_data['conditions'] = {}
        
        script = Script.objects.create(**script_data)
        
        # 处理标签
        if row.get('tags'):
            tag_names = []
            if isinstance(row['tags'], str):
                tag_names = [tag.strip() for tag in row['tags'].split(',')]
            elif isinstance(row['tags'], list):
                tag_names = row['tags']
            
            if tag_names:
                tags = self.get_or_create_tags(tag_names)
                script.tags.add(*tags)
        
        return script

class ProductImportService(BaseImportService):
    """产品导入服务"""
    
    REQUIRED_FIELDS = ['sku', 'name', 'price']
    OPTIONAL_FIELDS = ['brand', 'product_category', 'description', 'short_description', 
                      'stock_quantity', 'status', 'tags', 'specifications', 'attributes']
    
    def import_from_file(self, file: UploadedFile) -> ImportResult:
        """从文件导入产品"""
        result = ImportResult()
        
        try:
            # 验证文件
            allowed_formats = self.config['allowed_formats']['products']
            self.validate_file(file, allowed_formats)
            
            # 解析文件
            data = self.parse_file(file)
            
            # 批量导入
            result = self.batch_import(data)
            
        except Exception as e:
            result.add_error(0, f"文件处理失败: {e}")
        
        return result
    
    def batch_import(self, data: List[Dict]) -> ImportResult:
        """批量导入产品数据"""
        result = ImportResult()
        batch_size = self.config['batch_size']
        
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            batch_result = self._import_batch(batch, i)
            
            # 合并结果
            result.success_count += batch_result.success_count
            result.error_count += batch_result.error_count
            result.warnings.extend(batch_result.warnings)
            result.errors.extend(batch_result.errors)
            result.created_items.extend(batch_result.created_items)
        
        return result
    
    def _import_batch(self, batch: List[Dict], start_index: int) -> ImportResult:
        """导入单个批次"""
        result = ImportResult()
        
        with transaction.atomic():
            for idx, row in enumerate(batch):
                row_num = start_index + idx + 1
                
                try:
                    product = self._create_product_from_row(row, row_num, result)
                    if product:
                        result.add_success(product.id, product.name)
                        
                        # 异步同步到向量库和RAGFlow
                        sync_single_content_task.delay(
                            self.knowledge_base_id, 'product', product.id
                        )
                        
                except Exception as e:
                    result.add_error(row_num, str(e))
        
        return result
    
    def _create_product_from_row(self, row: Dict, row_num: int, result: ImportResult) -> Optional[Product]:
        """从行数据创建产品"""
        # 验证必填字段
        for field in self.REQUIRED_FIELDS:
            if not row.get(field):
                raise ValueError(f"缺少必填字段: {field}")
        
        # 验证SKU唯一性
        sku = row['sku']
        if Product.objects.filter(sku=sku).exists():
            result.add_warning(row_num, f"SKU已存在，跳过: {sku}")
            return None
        
        # 验证价格
        try:
            price = float(row['price'])
            if price < 0:
                raise ValueError("价格不能为负数")
        except (ValueError, TypeError):
            raise ValueError(f"无效的价格: {row['price']}")
        
        # 创建产品
        product_data = {
            'knowledge_base': self.knowledge_base,
            'sku': sku,
            'name': row['name'],
            'price': price,
            'brand': row.get('brand', ''),
            'product_category': row.get('product_category', ''),
            'description': row.get('description', ''),
            'short_description': row.get('short_description', ''),
            'stock_quantity': int(row.get('stock_quantity', 0)),
            'status': row.get('status', 'active'),
            'created_by_id': self.user_id,
        }
        
        # 验证状态
        valid_statuses = [choice[0] for choice in Product.ProductStatus.choices]
        if product_data['status'] not in valid_statuses:
            result.add_warning(row_num, f"无效状态，使用默认值: {product_data['status']}")
            product_data['status'] = 'active'
        
        # 处理规格参数
        if row.get('specifications'):
            try:
                if isinstance(row['specifications'], str):
                    product_data['specifications'] = json.loads(row['specifications'])
                else:
                    product_data['specifications'] = row['specifications']
            except (json.JSONDecodeError, TypeError):
                result.add_warning(row_num, "规格参数格式错误，使用默认值")
                product_data['specifications'] = {}
        
        # 处理产品属性
        if row.get('attributes'):
            try:
                if isinstance(row['attributes'], str):
                    product_data['attributes'] = json.loads(row['attributes'])
                else:
                    product_data['attributes'] = row['attributes']
            except (json.JSONDecodeError, TypeError):
                result.add_warning(row_num, "产品属性格式错误，使用默认值")
                product_data['attributes'] = {}
        
        product = Product.objects.create(**product_data)
        
        # 处理标签
        if row.get('tags'):
            tag_names = []
            if isinstance(row['tags'], str):
                tag_names = [tag.strip() for tag in row['tags'].split(',')]
            elif isinstance(row['tags'], list):
                tag_names = row['tags']
            
            if tag_names:
                tags = self.get_or_create_tags(tag_names)
                product.tags.add(*tags)
        
        return product

# Celery任务
@shared_task(bind=True)
def import_scripts_task(self, knowledge_base_id: int, user_id: int, file_data: bytes, filename: str):
    """导入话术的Celery任务"""
    try:
        # 重建文件对象
        from django.core.files.uploadedfile import SimpleUploadedFile
        file = SimpleUploadedFile(filename, file_data)
        
        service = ScriptImportService(knowledge_base_id, user_id)
        result = service.import_from_file(file)
        
        logger.info(f"话术导入任务完成: {result.to_dict()}")
        return result.to_dict()
        
    except Exception as e:
        logger.error(f"话术导入任务失败: {e}")
        raise

@shared_task(bind=True)
def import_products_task(self, knowledge_base_id: int, user_id: int, file_data: bytes, filename: str):
    """导入产品的Celery任务"""
    try:
        # 重建文件对象
        from django.core.files.uploadedfile import SimpleUploadedFile
        file = SimpleUploadedFile(filename, file_data)
        
        service = ProductImportService(knowledge_base_id, user_id)
        result = service.import_from_file(file)
        
        logger.info(f"产品导入任务完成: {result.to_dict()}")
        return result.to_dict()
        
    except Exception as e:
        logger.error(f"产品导入任务失败: {e}")
        raise 