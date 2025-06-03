"""
知识库数据导入服务
支持CSV、Excel、JSON格式的批量数据导入
"""

import csv
import json
import pandas as pd
import logging
from typing import Dict, List, Optional, Any, Union
from io import StringIO, BytesIO
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.contrib.auth import get_user_model

from .models import KnowledgeBase, Script, Product, DocumentCategory, DocumentTag
from .kb_sync import kb_sync_service

User = get_user_model()
logger = logging.getLogger(__name__)


class ImportError(Exception):
    """导入错误"""
    pass


class BaseImportService:
    """基础导入服务"""
    
    def __init__(self, knowledge_base: KnowledgeBase, user: User):
        self.knowledge_base = knowledge_base
        self.user = user
        self.errors = []
        self.warnings = []
        
    def validate_file(self, file: UploadedFile) -> bool:
        """验证文件格式"""
        allowed_extensions = ['.csv', '.xlsx', '.xls', '.json']
        file_extension = file.name.lower().split('.')[-1]
        
        if f'.{file_extension}' not in allowed_extensions:
            raise ImportError(f"不支持的文件格式: {file_extension}")
        
        # 检查文件大小 (10MB限制)
        if file.size > 10 * 1024 * 1024:
            raise ImportError("文件大小超过10MB限制")
        
        return True
    
    def parse_file(self, file: UploadedFile) -> List[Dict]:
        """解析文件内容"""
        self.validate_file(file)
        
        file_extension = file.name.lower().split('.')[-1]
        
        try:
            if file_extension == 'csv':
                return self._parse_csv(file)
            elif file_extension in ['xlsx', 'xls']:
                return self._parse_excel(file)
            elif file_extension == 'json':
                return self._parse_json(file)
            else:
                raise ImportError(f"不支持的文件格式: {file_extension}")
        except Exception as e:
            logger.error(f"解析文件失败: {e}")
            raise ImportError(f"解析文件失败: {str(e)}")
    
    def _parse_csv(self, file: UploadedFile) -> List[Dict]:
        """解析CSV文件"""
        try:
            # 尝试不同的编码
            for encoding in ['utf-8', 'gbk', 'gb2312']:
                try:
                    content = file.read().decode(encoding)
                    file.seek(0)  # 重置文件指针
                    break
                except UnicodeDecodeError:
                    file.seek(0)
                    continue
            else:
                raise ImportError("无法识别文件编码")
            
            # 解析CSV
            csv_reader = csv.DictReader(StringIO(content))
            return list(csv_reader)
            
        except Exception as e:
            raise ImportError(f"CSV解析失败: {str(e)}")
    
    def _parse_excel(self, file: UploadedFile) -> List[Dict]:
        """解析Excel文件"""
        try:
            df = pd.read_excel(file, engine='openpyxl' if file.name.endswith('.xlsx') else 'xlrd')
            # 填充NaN值
            df = df.fillna('')
            return df.to_dict('records')
        except Exception as e:
            raise ImportError(f"Excel解析失败: {str(e)}")
    
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
                raise ImportError("JSON格式错误：应为对象或数组")
                
        except json.JSONDecodeError as e:
            raise ImportError(f"JSON解析失败: {str(e)}")
        except Exception as e:
            raise ImportError(f"JSON文件处理失败: {str(e)}")
    
    def get_or_create_category(self, category_name: str) -> Optional[DocumentCategory]:
        """获取或创建分类"""
        if not category_name:
            return None
        
        try:
            category, created = DocumentCategory.objects.get_or_create(
                knowledge_base=self.knowledge_base,
                name=category_name,
                defaults={
                    'description': f'导入时自动创建的分类: {category_name}',
                    'is_active': True
                }
            )
            return category
        except Exception as e:
            logger.error(f"创建分类失败: {e}")
            return None
    
    def get_or_create_tags(self, tag_names: Union[str, List[str]]) -> List[DocumentTag]:
        """获取或创建标签"""
        if not tag_names:
            return []
        
        if isinstance(tag_names, str):
            # 支持逗号分隔的标签字符串
            tag_names = [tag.strip() for tag in tag_names.split(',') if tag.strip()]
        
        tags = []
        for tag_name in tag_names:
            try:
                tag, created = DocumentTag.objects.get_or_create(
                    knowledge_base=self.knowledge_base,
                    name=tag_name,
                    defaults={
                        'description': f'导入时自动创建的标签: {tag_name}',
                        'usage_count': 0
                    }
                )
                tags.append(tag)
            except Exception as e:
                logger.error(f"创建标签失败: {e}")
                continue
        
        return tags


class ScriptImportService(BaseImportService):
    """话术导入服务"""
    
    REQUIRED_FIELDS = ['name', 'script_type', 'content']
    OPTIONAL_FIELDS = ['category', 'tags', 'priority', 'variables', 'conditions', 'triggers']
    
    SCRIPT_TYPE_MAPPING = {
        '问候语': 'greeting',
        '商品介绍': 'product_intro',
        '价格协商': 'price_negotiation',
        '订单确认': 'order_confirmation',
        '售后服务': 'after_sales',
        '异议处理': 'objection_handling',
        '结束语': 'closing',
        '追加销售': 'upselling',
        '交叉销售': 'cross_selling',
    }
    
    def validate_row(self, row: Dict, row_index: int) -> bool:
        """验证单行数据"""
        errors = []
        
        # 检查必填字段
        for field in self.REQUIRED_FIELDS:
            if not row.get(field):
                errors.append(f"第{row_index}行：缺少必填字段 '{field}'")
        
        # 验证话术类型
        script_type = row.get('script_type', '').strip()
        if script_type:
            # 支持中文类型名称
            if script_type in self.SCRIPT_TYPE_MAPPING:
                row['script_type'] = self.SCRIPT_TYPE_MAPPING[script_type]
            elif script_type not in dict(Script.ScriptType.choices).keys():
                errors.append(f"第{row_index}行：无效的话术类型 '{script_type}'")
        
        # 验证优先级
        priority = row.get('priority', '0')
        try:
            row['priority'] = int(priority) if priority else 0
        except ValueError:
            errors.append(f"第{row_index}行：优先级必须为数字")
        
        # 验证JSON字段
        for json_field in ['variables', 'conditions', 'triggers']:
            if row.get(json_field):
                try:
                    if isinstance(row[json_field], str):
                        row[json_field] = json.loads(row[json_field])
                except json.JSONDecodeError:
                    errors.append(f"第{row_index}行：{json_field}格式错误，应为JSON格式")
        
        if errors:
            self.errors.extend(errors)
            return False
        
        return True
    
    def import_data(self, file: UploadedFile) -> Dict[str, Any]:
        """导入话术数据"""
        try:
            # 解析文件
            rows = self.parse_file(file)
            
            if not rows:
                raise ImportError("文件为空或无有效数据")
            
            # 验证数据
            valid_rows = []
            for i, row in enumerate(rows, 1):
                if self.validate_row(row, i):
                    valid_rows.append(row)
            
            if not valid_rows:
                raise ImportError("没有有效的数据行")
            
            # 导入数据
            success_count = 0
            failed_count = 0
            
            with transaction.atomic():
                for row in valid_rows:
                    try:
                        script = self._create_script(row)
                        if script:
                            success_count += 1
                            # 异步同步到RAGFlow
                            try:
                                kb_sync_service.sync_script_to_ragflow(script)
                            except Exception as e:
                                logger.warning(f"同步到RAGFlow失败: {e}")
                        else:
                            failed_count += 1
                    except Exception as e:
                        logger.error(f"创建话术失败: {e}")
                        failed_count += 1
                        self.errors.append(f"创建话术失败: {str(e)}")
            
            return {
                'success': True,
                'total_rows': len(rows),
                'valid_rows': len(valid_rows),
                'success_count': success_count,
                'failed_count': failed_count,
                'errors': self.errors,
                'warnings': self.warnings
            }
            
        except Exception as e:
            logger.error(f"导入话术数据失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'errors': self.errors,
                'warnings': self.warnings
            }
    
    def _create_script(self, row: Dict) -> Optional[Script]:
        """创建话术"""
        try:
            # 创建话术
            script = Script.objects.create(
                knowledge_base=self.knowledge_base,
                name=row['name'],
                script_type=row['script_type'],
                content=row['content'],
                priority=row.get('priority', 0),
                variables=row.get('variables', {}),
                conditions=row.get('conditions', {}),
                triggers=row.get('triggers', []),
                status=Script.ScriptStatus.ACTIVE,
                created_by=self.user
            )
            
            # 设置分类
            if row.get('category'):
                category = self.get_or_create_category(row['category'])
                if category:
                    script.category = category
                    script.save()
            
            # 设置标签
            if row.get('tags'):
                tags = self.get_or_create_tags(row['tags'])
                if tags:
                    script.tags.set(tags)
            
            return script
            
        except Exception as e:
            logger.error(f"创建话术失败: {e}")
            raise


class ProductImportService(BaseImportService):
    """产品导入服务"""
    
    REQUIRED_FIELDS = ['sku', 'name', 'price']
    OPTIONAL_FIELDS = [
        'category', 'tags', 'brand', 'product_category', 'original_price', 'cost_price',
        'stock_quantity', 'description', 'short_description', 'specifications',
        'attributes', 'sales_points', 'keywords', 'status'
    ]
    
    STATUS_MAPPING = {
        '在售': 'active',
        '下架': 'inactive',
        '缺货': 'out_of_stock',
        '停产': 'discontinued',
    }
    
    def validate_row(self, row: Dict, row_index: int) -> bool:
        """验证单行数据"""
        errors = []
        
        # 检查必填字段
        for field in self.REQUIRED_FIELDS:
            if not row.get(field):
                errors.append(f"第{row_index}行：缺少必填字段 '{field}'")
        
        # 验证SKU唯一性
        sku = row.get('sku', '').strip()
        if sku and Product.objects.filter(sku=sku).exists():
            errors.append(f"第{row_index}行：SKU '{sku}' 已存在")
        
        # 验证价格字段
        for price_field in ['price', 'original_price', 'cost_price']:
            price_value = row.get(price_field)
            if price_value:
                try:
                    row[price_field] = float(price_value)
                except ValueError:
                    errors.append(f"第{row_index}行：{price_field}必须为数字")
        
        # 验证库存数量
        stock_fields = ['stock_quantity', 'min_stock_level', 'max_stock_level']
        for stock_field in stock_fields:
            stock_value = row.get(stock_field)
            if stock_value:
                try:
                    row[stock_field] = int(stock_value)
                except ValueError:
                    errors.append(f"第{row_index}行：{stock_field}必须为整数")
        
        # 验证状态
        status = row.get('status', '').strip()
        if status:
            if status in self.STATUS_MAPPING:
                row['status'] = self.STATUS_MAPPING[status]
            elif status not in dict(Product.ProductStatus.choices).keys():
                errors.append(f"第{row_index}行：无效的状态 '{status}'")
        
        # 验证JSON字段
        for json_field in ['specifications', 'attributes', 'sales_points', 'keywords']:
            if row.get(json_field):
                try:
                    if isinstance(row[json_field], str):
                        row[json_field] = json.loads(row[json_field])
                except json.JSONDecodeError:
                    errors.append(f"第{row_index}行：{json_field}格式错误，应为JSON格式")
        
        if errors:
            self.errors.extend(errors)
            return False
        
        return True
    
    def import_data(self, file: UploadedFile) -> Dict[str, Any]:
        """导入产品数据"""
        try:
            # 解析文件
            rows = self.parse_file(file)
            
            if not rows:
                raise ImportError("文件为空或无有效数据")
            
            # 验证数据
            valid_rows = []
            for i, row in enumerate(rows, 1):
                if self.validate_row(row, i):
                    valid_rows.append(row)
            
            if not valid_rows:
                raise ImportError("没有有效的数据行")
            
            # 导入数据
            success_count = 0
            failed_count = 0
            
            with transaction.atomic():
                for row in valid_rows:
                    try:
                        product = self._create_product(row)
                        if product:
                            success_count += 1
                            # 异步同步到RAGFlow
                            try:
                                kb_sync_service.sync_product_to_ragflow(product)
                            except Exception as e:
                                logger.warning(f"同步到RAGFlow失败: {e}")
                        else:
                            failed_count += 1
                    except Exception as e:
                        logger.error(f"创建产品失败: {e}")
                        failed_count += 1
                        self.errors.append(f"创建产品失败: {str(e)}")
            
            return {
                'success': True,
                'total_rows': len(rows),
                'valid_rows': len(valid_rows),
                'success_count': success_count,
                'failed_count': failed_count,
                'errors': self.errors,
                'warnings': self.warnings
            }
            
        except Exception as e:
            logger.error(f"导入产品数据失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'errors': self.errors,
                'warnings': self.warnings
            }
    
    def _create_product(self, row: Dict) -> Optional[Product]:
        """创建产品"""
        try:
            # 创建产品
            product = Product.objects.create(
                knowledge_base=self.knowledge_base,
                sku=row['sku'],
                name=row['name'],
                price=row['price'],
                original_price=row.get('original_price'),
                cost_price=row.get('cost_price'),
                brand=row.get('brand', ''),
                product_category=row.get('product_category', ''),
                stock_quantity=row.get('stock_quantity', 0),
                min_stock_level=row.get('min_stock_level', 0),
                max_stock_level=row.get('max_stock_level', 0),
                description=row.get('description', ''),
                short_description=row.get('short_description', ''),
                specifications=row.get('specifications', {}),
                attributes=row.get('attributes', {}),
                sales_points=row.get('sales_points', []),
                keywords=row.get('keywords', []),
                status=row.get('status', Product.ProductStatus.ACTIVE),
                created_by=self.user
            )
            
            # 设置分类
            if row.get('category'):
                category = self.get_or_create_category(row['category'])
                if category:
                    product.category = category
                    product.save()
            
            # 设置标签
            if row.get('tags'):
                tags = self.get_or_create_tags(row['tags'])
                if tags:
                    product.tags.set(tags)
            
            return product
            
        except Exception as e:
            logger.error(f"创建产品失败: {e}")
            raise


def get_import_template(data_type: str) -> Dict[str, Any]:
    """获取导入模板"""
    templates = {
        'script': {
            'filename': '话术导入模板.csv',
            'headers': [
                'name', 'script_type', 'content', 'category', 'tags', 'priority',
                'variables', 'conditions', 'triggers'
            ],
            'sample_data': [
                {
                    'name': '商品介绍话术',
                    'script_type': 'product_intro',
                    'content': '您好，这款产品具有以下特点...',
                    'category': '销售话术',
                    'tags': '商品介绍,销售',
                    'priority': '10',
                    'variables': '{"product_name": "产品名称"}',
                    'conditions': '{"scene": "product_detail"}',
                    'triggers': '["客户询问产品"]'
                }
            ],
            'instructions': [
                '1. name: 话术名称（必填）',
                '2. script_type: 话术类型（必填）- greeting/product_intro/price_negotiation等',
                '3. content: 话术内容（必填）',
                '4. category: 分类名称（可选）',
                '5. tags: 标签，多个用逗号分隔（可选）',
                '6. priority: 优先级，数字（可选）',
                '7. variables: 变量定义，JSON格式（可选）',
                '8. conditions: 使用条件，JSON格式（可选）',
                '9. triggers: 触发条件，JSON数组格式（可选）'
            ]
        },
        'product': {
            'filename': '产品导入模板.csv',
            'headers': [
                'sku', 'name', 'price', 'original_price', 'brand', 'product_category',
                'stock_quantity', 'description', 'short_description', 'specifications',
                'sales_points', 'keywords', 'status', 'category', 'tags'
            ],
            'sample_data': [
                {
                    'sku': 'PROD001',
                    'name': '示例产品',
                    'price': '99.99',
                    'original_price': '129.99',
                    'brand': '示例品牌',
                    'product_category': '电子产品',
                    'stock_quantity': '100',
                    'description': '这是一个示例产品的详细描述...',
                    'short_description': '示例产品简介',
                    'specifications': '{"尺寸": "10x5x2cm", "重量": "100g"}',
                    'sales_points': '["高品质", "性价比高", "包邮"]',
                    'keywords': '["电子", "便携", "实用"]',
                    'status': 'active',
                    'category': '热销产品',
                    'tags': '热销,推荐'
                }
            ],
            'instructions': [
                '1. sku: 商品SKU（必填，唯一）',
                '2. name: 商品名称（必填）',
                '3. price: 价格（必填，数字）',
                '4. original_price: 原价（可选，数字）',
                '5. brand: 品牌（可选）',
                '6. product_category: 商品分类（可选）',
                '7. stock_quantity: 库存数量（可选，整数）',
                '8. description: 详细描述（可选）',
                '9. short_description: 简短描述（可选）',
                '10. specifications: 规格参数，JSON格式（可选）',
                '11. sales_points: 卖点，JSON数组格式（可选）',
                '12. keywords: 关键词，JSON数组格式（可选）',
                '13. status: 状态 - active/inactive/out_of_stock/discontinued（可选）',
                '14. category: 分类名称（可选）',
                '15. tags: 标签，多个用逗号分隔（可选）'
            ]
        }
    }
    
    return templates.get(data_type, {}) 