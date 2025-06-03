"""
基础提示词类
为所有智能体提示词类提供通用接口和方法
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import random
import json


class BasePrompts(ABC):
    """提示词基础类"""
    
    def __init__(self):
        self.version = "1.0.0"
        self.last_updated = None
        self.metadata = {}
    
    def get_random_prompt(self, prompts: List[str]) -> str:
        """从提示词列表中随机选择一个"""
        if not prompts:
            return ""
        return random.choice(prompts)
    
    def format_prompt(self, template: str, **kwargs) -> str:
        """格式化提示词模板"""
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"缺少必要的参数: {e}")
    
    def merge_prompts(self, *prompt_lists: List[str]) -> List[str]:
        """合并多个提示词列表"""
        merged = []
        for prompt_list in prompt_lists:
            if isinstance(prompt_list, list):
                merged.extend(prompt_list)
        return merged
    
    def validate_prompts(self, prompts: Dict[str, Any]) -> bool:
        """验证提示词格式"""
        if not isinstance(prompts, dict):
            return False
        
        for key, value in prompts.items():
            if not isinstance(key, str):
                return False
            if not isinstance(value, (str, list, dict)):
                return False
        
        return True
    
    def get_metadata(self) -> Dict[str, Any]:
        """获取提示词元数据"""
        return {
            'version': self.version,
            'last_updated': self.last_updated,
            'metadata': self.metadata
        }
    
    def export_prompts(self) -> Dict[str, Any]:
        """导出所有提示词为字典格式"""
        result = {}
        for attr_name in dir(self):
            if not attr_name.startswith('_') and not callable(getattr(self, attr_name)):
                attr_value = getattr(self, attr_name)
                if isinstance(attr_value, (dict, list, str)):
                    result[attr_name] = attr_value
        return result
    
    def load_from_dict(self, prompts_dict: Dict[str, Any]):
        """从字典加载提示词"""
        for key, value in prompts_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def search_prompts(self, keyword: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """搜索包含关键词的提示词"""
        results = []
        search_keyword = keyword if case_sensitive else keyword.lower()
        
        def search_in_value(value, path):
            if isinstance(value, str):
                search_text = value if case_sensitive else value.lower()
                if search_keyword in search_text:
                    results.append({
                        'path': path,
                        'content': value,
                        'type': 'string'
                    })
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    search_in_value(item, f"{path}[{i}]")
            elif isinstance(value, dict):
                for k, v in value.items():
                    search_in_value(v, f"{path}.{k}")
        
        # 搜索所有属性
        for attr_name in dir(self):
            if not attr_name.startswith('_') and not callable(getattr(self, attr_name)):
                attr_value = getattr(self, attr_name)
                search_in_value(attr_value, attr_name)
        
        return results


class PromptTemplate:
    """提示词模板类"""
    
    def __init__(self, template: str, required_vars: List[str] = None):
        self.template = template
        self.required_vars = required_vars or []
        self.optional_vars = []
        self._analyze_template()
    
    def _analyze_template(self):
        """分析模板中的变量"""
        import re
        # 查找所有 {变量名} 格式的变量
        variables = re.findall(r'\{(\w+)\}', self.template)
        for var in variables:
            if var not in self.required_vars and var not in self.optional_vars:
                self.optional_vars.append(var)
    
    def render(self, **kwargs) -> str:
        """渲染模板"""
        # 检查必需变量
        missing_vars = [var for var in self.required_vars if var not in kwargs]
        if missing_vars:
            raise ValueError(f"缺少必需变量: {missing_vars}")
        
        return self.template.format(**kwargs)
    
    def get_variables(self) -> Dict[str, List[str]]:
        """获取模板变量信息"""
        return {
            'required': self.required_vars,
            'optional': self.optional_vars
        }


class PromptManager:
    """提示词管理器"""
    
    def __init__(self):
        self.prompt_classes = {}
        self.templates = {}
    
    def register_prompt_class(self, name: str, prompt_class: BasePrompts):
        """注册提示词类"""
        self.prompt_classes[name] = prompt_class
    
    def get_prompt_class(self, name: str) -> Optional[BasePrompts]:
        """获取提示词类"""
        return self.prompt_classes.get(name)
    
    def register_template(self, name: str, template: PromptTemplate):
        """注册模板"""
        self.templates[name] = template
    
    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """获取模板"""
        return self.templates.get(name)
    
    def list_prompt_classes(self) -> List[str]:
        """列出所有注册的提示词类"""
        return list(self.prompt_classes.keys())
    
    def list_templates(self) -> List[str]:
        """列出所有注册的模板"""
        return list(self.templates.keys())


# 全局提示词管理器实例
prompt_manager = PromptManager() 