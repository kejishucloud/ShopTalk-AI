from django.core.management.base import BaseCommand
from django.db import transaction
from apps.system_config.models import ConfigCategory, ConfigGroup, SystemConfig


class Command(BaseCommand):
    help = '初始化系统配置数据'

    def handle(self, *args, **options):
        with transaction.atomic():
            self.stdout.write('开始初始化系统配置...')
            
            # 创建配置分类
            self.create_categories()
            # 创建配置组
            self.create_groups()
            # 创建配置项
            self.create_configs()
            
            self.stdout.write(self.style.SUCCESS('系统配置初始化完成！'))

    def create_categories(self):
        """创建配置分类"""
        categories = [
            {
                'name': 'ai_models',
                'display_name': 'AI模型配置',
                'description': 'AI模型相关配置，包括OpenAI、Claude、智谱AI等',
                'order': 1
            },
            {
                'name': 'ecommerce_platforms',
                'display_name': '电商平台配置',
                'description': '电商平台集成配置，包括淘宝、京东、拼多多等',
                'order': 2
            },
            {
                'name': 'social_platforms',
                'display_name': '社交平台配置',
                'description': '社交平台集成配置，包括小红书、抖音、微信等',
                'order': 3
            },
            {
                'name': 'agents',
                'display_name': '智能体配置',
                'description': '智能体相关配置，包括情感分析、意图识别等',
                'order': 4
            },
            {
                'name': 'browser_automation',
                'display_name': '浏览器自动化配置',
                'description': '浏览器自动化和反检测相关配置',
                'order': 5
            },
            {
                'name': 'knowledge_base',
                'display_name': '知识库配置',
                'description': '向量数据库和RAG相关配置',
                'order': 6
            },
        ]
        
        for cat_data in categories:
            category, created = ConfigCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'创建分类: {category.display_name}')

    def create_groups(self):
        """创建配置组"""
        groups_config = [
            # AI模型配置组
            {
                'category_name': 'ai_models',
                'groups': [
                    {'name': 'openai', 'display_name': 'OpenAI配置', 'order': 1},
                    {'name': 'anthropic', 'display_name': 'Anthropic Claude配置', 'order': 2},
                    {'name': 'zhipu', 'display_name': '智谱AI配置', 'order': 3},
                    {'name': 'qwen', 'display_name': '阿里通义千问配置', 'order': 4},
                    {'name': 'ernie', 'display_name': '百度文心一言配置', 'order': 5},
                    {'name': 'local_ai', 'display_name': '本地AI模型配置', 'order': 6},
                ]
            },
            # 电商平台配置组
            {
                'category_name': 'ecommerce_platforms',
                'groups': [
                    {'name': 'taobao', 'display_name': '淘宝配置', 'order': 1},
                    {'name': 'jingdong', 'display_name': '京东配置', 'order': 2},
                    {'name': 'pinduoduo', 'display_name': '拼多多配置', 'order': 3},
                ]
            },
            # 社交平台配置组
            {
                'category_name': 'social_platforms',
                'groups': [
                    {'name': 'xiaohongshu', 'display_name': '小红书配置', 'order': 1},
                    {'name': 'douyin', 'display_name': '抖音配置', 'order': 2},
                    {'name': 'wechat', 'display_name': '微信配置', 'order': 3},
                ]
            },
            # 智能体配置组
            {
                'category_name': 'agents',
                'groups': [
                    {'name': 'sentiment', 'display_name': '情感分析配置', 'order': 1},
                    {'name': 'intent', 'display_name': '意图识别配置', 'order': 2},
                    {'name': 'multimedia', 'display_name': '多媒体处理配置', 'order': 3},
                ]
            },
        ]
        
        for group_config in groups_config:
            try:
                category = ConfigCategory.objects.get(name=group_config['category_name'])
                for group_data in group_config['groups']:
                    group_data['category'] = category
                    group, created = ConfigGroup.objects.get_or_create(
                        category=category,
                        name=group_data['name'],
                        defaults=group_data
                    )
                    if created:
                        self.stdout.write(f'创建配置组: {group.display_name}')
            except ConfigCategory.DoesNotExist:
                self.stdout.write(f'分类 {group_config["category_name"]} 不存在')

    def create_configs(self):
        """创建配置项"""
        configs = [
            # OpenAI配置
            {
                'category': 'ai_models', 'group': 'openai',
                'key': 'OPENAI_API_KEY', 'display_name': 'OpenAI API密钥',
                'description': 'OpenAI API访问密钥', 'config_type': 'password',
                'is_required': True, 'is_encrypted': True, 'order': 1
            },
            {
                'category': 'ai_models', 'group': 'openai',
                'key': 'OPENAI_BASE_URL', 'display_name': 'OpenAI API基础URL',
                'description': 'OpenAI API的基础URL地址', 'config_type': 'url',
                'default_value': 'https://api.openai.com/v1', 'order': 2
            },
            {
                'category': 'ai_models', 'group': 'openai',
                'key': 'OPENAI_MODEL', 'display_name': 'OpenAI模型',
                'description': '使用的OpenAI模型', 'config_type': 'choice',
                'choices': ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo-preview'],
                'default_value': 'gpt-3.5-turbo', 'order': 3
            },
            
            # Anthropic配置
            {
                'category': 'ai_models', 'group': 'anthropic',
                'key': 'ANTHROPIC_API_KEY', 'display_name': 'Anthropic API密钥',
                'description': 'Anthropic Claude API访问密钥', 'config_type': 'password',
                'is_encrypted': True, 'order': 1
            },
            {
                'category': 'ai_models', 'group': 'anthropic',
                'key': 'ANTHROPIC_MODEL', 'display_name': 'Claude模型',
                'description': '使用的Claude模型', 'config_type': 'choice',
                'choices': ['claude-3-sonnet-20240229', 'claude-3-opus-20240229'],
                'default_value': 'claude-3-sonnet-20240229', 'order': 2
            },
            
            # 智谱AI配置
            {
                'category': 'ai_models', 'group': 'zhipu',
                'key': 'ZHIPU_API_KEY', 'display_name': '智谱AI API密钥',
                'description': '智谱AI API访问密钥', 'config_type': 'password',
                'is_encrypted': True, 'order': 1
            },
            {
                'category': 'ai_models', 'group': 'zhipu',
                'key': 'ZHIPU_MODEL', 'display_name': '智谱AI模型',
                'description': '使用的智谱AI模型', 'config_type': 'choice',
                'choices': ['glm-4', 'glm-3-turbo'],
                'default_value': 'glm-4', 'order': 2
            },
            
            # 淘宝配置
            {
                'category': 'ecommerce_platforms', 'group': 'taobao',
                'key': 'TAOBAO_ENABLED', 'display_name': '启用淘宝',
                'description': '是否启用淘宝平台集成', 'config_type': 'boolean',
                'default_value': 'True', 'order': 1
            },
            {
                'category': 'ecommerce_platforms', 'group': 'taobao',
                'key': 'TAOBAO_USERNAME', 'display_name': '淘宝用户名',
                'description': '淘宝登录用户名', 'config_type': 'string',
                'order': 2
            },
            {
                'category': 'ecommerce_platforms', 'group': 'taobao',
                'key': 'TAOBAO_PASSWORD', 'display_name': '淘宝密码',
                'description': '淘宝登录密码', 'config_type': 'password',
                'is_encrypted': True, 'order': 3
            },
            
            # 情感分析配置
            {
                'category': 'agents', 'group': 'sentiment',
                'key': 'SENTIMENT_ENABLED', 'display_name': '启用情感分析',
                'description': '是否启用情感分析功能', 'config_type': 'boolean',
                'default_value': 'True', 'order': 1
            },
            {
                'category': 'agents', 'group': 'sentiment',
                'key': 'SENTIMENT_MODEL', 'display_name': '情感分析模型',
                'description': '使用的情感分析模型', 'config_type': 'choice',
                'choices': ['transformer', 'bert', 'lstm'],
                'default_value': 'transformer', 'order': 2
            },
            {
                'category': 'agents', 'group': 'sentiment',
                'key': 'SENTIMENT_THRESHOLD', 'display_name': '情感阈值',
                'description': '情感分析置信度阈值', 'config_type': 'float',
                'default_value': '0.7', 'order': 3
            },
        ]
        
        for config_data in configs:
            try:
                category = ConfigCategory.objects.get(name=config_data.pop('category'))
                group_name = config_data.pop('group', None)
                group = None
                if group_name:
                    group = ConfigGroup.objects.get(category=category, name=group_name)
                
                config_data['category'] = category
                config_data['group'] = group
                
                # 处理choices字段
                if 'choices' in config_data and config_data['choices']:
                    choices = config_data['choices']
                    config_data['choices'] = [{'value': choice, 'label': choice} for choice in choices]
                
                config, created = SystemConfig.objects.get_or_create(
                    key=config_data['key'],
                    defaults=config_data
                )
                if created:
                    self.stdout.write(f'创建配置项: {config.display_name}')
                    
            except (ConfigCategory.DoesNotExist, ConfigGroup.DoesNotExist) as e:
                self.stdout.write(f'创建配置项失败: {e}') 