"""
基础智能体类
定义所有智能体的通用接口和功能
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """智能体基类"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self.created_at = datetime.now()
        self.is_active = True
        self.logger = logging.getLogger(f"agent.{name}")
        
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理输入数据并返回结果
        
        Args:
            input_data: 输入数据字典
            
        Returns:
            处理结果字典
        """
        pass
    
    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        验证输入数据的有效性
        
        Args:
            input_data: 输入数据字典
            
        Returns:
            验证结果
        """
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """获取智能体状态"""
        return {
            'name': self.name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'config': self.config
        }
    
    def activate(self):
        """激活智能体"""
        self.is_active = True
        self.logger.info(f"Agent {self.name} activated")
    
    def deactivate(self):
        """停用智能体"""
        self.is_active = False
        self.logger.info(f"Agent {self.name} deactivated")
    
    def update_config(self, new_config: Dict[str, Any]):
        """更新配置"""
        self.config.update(new_config)
        self.logger.info(f"Agent {self.name} config updated")
    
    async def safe_process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        安全处理数据，包含错误处理
        
        Args:
            input_data: 输入数据字典
            
        Returns:
            处理结果字典
        """
        try:
            if not self.is_active:
                return {
                    'success': False,
                    'error': f'Agent {self.name} is not active',
                    'data': None
                }
            
            if not self.validate_input(input_data):
                return {
                    'success': False,
                    'error': 'Invalid input data',
                    'data': None
                }
            
            result = await self.process(input_data)
            return {
                'success': True,
                'error': None,
                'data': result,
                'agent': self.name,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in agent {self.name}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'data': None,
                'agent': self.name,
                'timestamp': datetime.now().isoformat()
            }


class AgentManager:
    """智能体管理器"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.logger = logging.getLogger("agent.manager")
    
    def register_agent(self, agent: BaseAgent):
        """注册智能体"""
        self.agents[agent.name] = agent
        self.logger.info(f"Registered agent: {agent.name}")
    
    def unregister_agent(self, agent_name: str):
        """注销智能体"""
        if agent_name in self.agents:
            del self.agents[agent_name]
            self.logger.info(f"Unregistered agent: {agent_name}")
    
    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """获取智能体"""
        return self.agents.get(agent_name)
    
    def list_agents(self) -> List[str]:
        """列出所有智能体"""
        return list(self.agents.keys())
    
    async def process_with_agent(self, agent_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """使用指定智能体处理数据"""
        agent = self.get_agent(agent_name)
        if not agent:
            return {
                'success': False,
                'error': f'Agent {agent_name} not found',
                'data': None
            }
        
        return await agent.safe_process(input_data)
    
    async def process_pipeline(self, agent_names: List[str], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用多个智能体按顺序处理数据
        
        Args:
            agent_names: 智能体名称列表
            input_data: 输入数据
            
        Returns:
            最终处理结果
        """
        current_data = input_data
        results = []
        
        for agent_name in agent_names:
            result = await self.process_with_agent(agent_name, current_data)
            results.append(result)
            
            if not result['success']:
                return {
                    'success': False,
                    'error': f'Pipeline failed at agent {agent_name}: {result["error"]}',
                    'data': None,
                    'pipeline_results': results
                }
            
            # 将当前结果作为下一个智能体的输入
            if result['data']:
                current_data.update(result['data'])
        
        return {
            'success': True,
            'error': None,
            'data': current_data,
            'pipeline_results': results
        }
    
    def get_all_status(self) -> Dict[str, Any]:
        """获取所有智能体状态"""
        return {
            agent_name: agent.get_status()
            for agent_name, agent in self.agents.items()
        }


# 全局智能体管理器实例
agent_manager = AgentManager() 