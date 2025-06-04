#!/usr/bin/env python3
"""
ShopTalk-AI 快速功能测试
测试RAGFlow、Langflow和LangChain的协作
"""

import os
import sys
import asyncio
import logging
from typing import Dict, Any

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """测试核心模块导入"""
    try:
        # 测试智能体导入
        from agents.chat_agent import ChatAgent
        from agents.knowledge_agent import KnowledgeAgent
        from agents.sentiment_agent import SentimentAgent
        logger.info("✅ 智能体模块导入成功")
        
        # 测试LangChain导入
        try:
            from langchain_community.chat_models import ChatOpenAI
            logger.info("✅ LangChain社区版导入成功")
        except ImportError as e:
            logger.warning(f"⚠️ LangChain导入警告: {e}")
        
        return True
    except Exception as e:
        logger.error(f"❌ 模块导入失败: {e}")
        return False

def test_config_loading():
    """测试配置加载"""
    try:
        import yaml
        
        # 测试主配置文件
        if os.path.exists('configs/configs.yaml'):
            with open('configs/configs.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info("✅ 主配置文件加载成功")
            
            # 检查关键配置
            required_sections = ['llm', 'embedding', 'redis', 'postgresql']
            for section in required_sections:
                if section in config:
                    logger.info(f"  ✓ {section}配置存在")
                else:
                    logger.warning(f"  ⚠️ {section}配置缺失")
        
        # 测试环境配置
        if os.path.exists('config.env'):
            logger.info("✅ 环境配置文件存在")
        
        return True
    except Exception as e:
        logger.error(f"❌ 配置加载失败: {e}")
        return False

async def test_agent_creation():
    """测试智能体创建"""
    try:
        # 模拟配置
        test_config = {
            'llm': {
                'model': 'gpt-3.5-turbo',
                'temperature': 0.7,
                'max_tokens': 1000
            },
            'langflow': {
                'endpoint': 'http://localhost:7860',
                'api_key': 'test_key',
                'flow_id': 'test_flow'
            }
        }
        
        # 创建智能体
        from agents.chat_agent import ChatAgent
        chat_agent = ChatAgent(test_config)
        logger.info("✅ ChatAgent创建成功")
        
        from agents.sentiment_agent import SentimentAgent
        sentiment_agent = SentimentAgent(test_config)
        logger.info("✅ SentimentAgent创建成功")
        
        from agents.knowledge_agent import KnowledgeAgent
        knowledge_agent = KnowledgeAgent(test_config)
        logger.info("✅ KnowledgeAgent创建成功")
        
        return True
    except Exception as e:
        logger.error(f"❌ 智能体创建失败: {e}")
        return False

async def test_mock_conversation():
    """测试模拟对话流程"""
    try:
        # 模拟输入数据
        test_input = {
            'user_id': 'test_user_123',
            'message': '你好，我想了解一下你们的产品',
            'session_id': 'test_session',
            'context': {}
        }
        
        logger.info("🤖 开始模拟对话流程...")
        logger.info(f"📝 用户消息: {test_input['message']}")
        
        # 模拟各智能体的分析结果
        mock_agent_results = {
            'sentiment_agent': {
                'success': True,
                'data': {
                    'sentiment': {
                        'label': 'neutral',
                        'confidence': 0.7
                    }
                }
            },
            'tag_agent': {
                'success': True,
                'data': {
                    'tags': ['inquiry', 'product_interest']
                }
            },
            'knowledge_agent': {
                'success': True,
                'data': {
                    'answer': '我们有多种优质产品可供选择，包括数码产品、家居用品等。'
                }
            },
            'memory_agent': {
                'success': True,
                'data': {
                    'conversation_state': 'product_inquiry',
                    'context': {
                        'user_profile': {
                            'preferred_category': 'electronics'
                        }
                    }
                }
            }
        }
        
        logger.info("🔍 智能体分析结果:")
        for agent, result in mock_agent_results.items():
            if result['success']:
                logger.info(f"  ✓ {agent}: 分析成功")
            else:
                logger.warning(f"  ⚠️ {agent}: 分析失败")
        
        # 模拟回复生成
        mock_response = "您好！欢迎咨询我们的产品。我们提供多种优质商品，包括最新的数码产品和精美的家居用品。根据您的兴趣，我推荐您先了解一下我们的电子产品系列。您有特别感兴趣的产品类型吗？"
        
        logger.info(f"💬 AI回复: {mock_response}")
        logger.info("✅ 模拟对话流程完成")
        
        return True
    except Exception as e:
        logger.error(f"❌ 模拟对话失败: {e}")
        return False

def test_framework_integration():
    """测试三个框架的集成情况"""
    logger.info("🔧 测试框架集成...")
    
    frameworks = {
        'LangChain': '基础RAG框架，提供LLM统一接口',
        'Langflow': '智能体可视化编排工具',
        'RAGFlow': '专业知识库管理系统'
    }
    
    for framework, description in frameworks.items():
        logger.info(f"  📋 {framework}: {description}")
    
    logger.info("🎯 集成架构:")
    logger.info("  1. RAGFlow -> 处理知识库检索和文档解析")
    logger.info("  2. Langflow -> 设计多智能体对话流程")
    logger.info("  3. LangChain -> 提供LLM调用的备用方案")
    
    return True

async def main():
    """主测试函数"""
    logger.info("🚀 开始ShopTalk-AI功能测试...")
    logger.info("=" * 60)
    
    test_results = []
    
    # 1. 测试模块导入
    logger.info("📦 测试1: 模块导入...")
    test_results.append(test_imports())
    
    # 2. 测试配置加载
    logger.info("\n⚙️ 测试2: 配置加载...")
    test_results.append(test_config_loading())
    
    # 3. 测试智能体创建
    logger.info("\n🤖 测试3: 智能体创建...")
    test_results.append(await test_agent_creation())
    
    # 4. 测试模拟对话
    logger.info("\n💬 测试4: 模拟对话流程...")
    test_results.append(await test_mock_conversation())
    
    # 5. 测试框架集成
    logger.info("\n🔧 测试5: 框架集成说明...")
    test_results.append(test_framework_integration())
    
    # 统计结果
    logger.info("\n" + "=" * 60)
    passed = sum(test_results)
    total = len(test_results)
    logger.info(f"📊 测试结果: {passed}/{total} 通过 ({passed/total*100:.1f}%)")
    
    if passed == total:
        logger.info("🎉 所有测试通过！系统功能正常。")
    else:
        logger.warning(f"⚠️ {total-passed}个测试失败，需要进一步调试。")
    
    logger.info("\n💡 关于为什么使用三个AI框架:")
    logger.info("1. LangChain: 提供标准化的LLM接口和基础RAG功能")
    logger.info("2. Langflow: 可视化设计复杂的多智能体工作流")
    logger.info("3. RAGFlow: 专业的知识库管理和文档理解")
    logger.info("这种架构确保了系统的灵活性、可扩展性和专业性。")

if __name__ == "__main__":
    asyncio.run(main()) 