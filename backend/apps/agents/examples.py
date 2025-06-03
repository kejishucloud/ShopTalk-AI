"""
智能体功能使用示例
演示各个智能体模块的使用方法
"""

import asyncio
from datetime import datetime
from django.utils import timezone

from .controllers import (
    UserTagController, SentimentController, ContextController,
    KnowledgeController, ChatIngestionController, ComprehensiveAgentController
)
from .services import TagManager, SentimentAnalyzer, ContextManager, KBResponder, ChatIngestor


def example_tag_management():
    """用户标签管理示例"""
    print("=== 用户标签管理示例 ===")
    
    # 创建标签控制器
    tag_controller = UserTagController()
    
    # 示例用户消息
    user_id = "user_12345"
    messages = [
        "我想买一个便宜的手机",
        "这个产品质量怎么样？",
        "有什么优惠活动吗？",
        "售后服务好不好？"
    ]
    
    # 分析并更新标签
    for message in messages:
        print(f"\n分析消息: {message}")
        result = tag_controller.analyze_and_update_tags(user_id, message)
        
        if result['success']:
            print(f"检测到标签: {[tag['tag_name'] for tag in result['data'].get('new_tags', [])]}")
        else:
            print(f"标签分析失败: {result['error']}")
    
    # 获取用户所有标签
    print(f"\n获取用户 {user_id} 的所有标签:")
    tags_result = tag_controller.get_user_tags(user_id)
    
    if tags_result['success']:
        for tag in tags_result['data']['tags']:
            print(f"- {tag['tag_name']}: 权重 {tag['weight']:.2f}")
    
    print("\n" + "="*50)


def example_sentiment_analysis():
    """情感分析示例"""
    print("=== 情感分析示例 ===")
    
    # 创建情感分析控制器
    sentiment_controller = SentimentController()
    
    # 示例文本
    texts = [
        "这个产品真的很棒，我很满意！",
        "质量太差了，完全不值这个价格",
        "还可以吧，没有特别的感觉",
        "客服态度很好，解决了我的问题",
        "发货太慢了，等了一个星期"
    ]
    
    # 单个文本情感分析
    for text in texts:
        print(f"\n分析文本: {text}")
        result = sentiment_controller.analyze_text_sentiment(text)
        
        if result['success']:
            sentiment = result['data']['sentiment']
            print(f"情感极性: {sentiment['polarity']}")
            print(f"情感分数: {sentiment['score']:.3f}")
            print(f"置信度: {sentiment['confidence']:.3f}")
    
    # 批量情感分析
    print(f"\n批量分析 {len(texts)} 条文本:")
    batch_result = sentiment_controller.batch_analyze_sentiment(texts)
    
    if batch_result['success']:
        stats = batch_result['data']['statistics']
        print(f"正面情感: {stats['positive']} 条")
        print(f"负面情感: {stats['negative']} 条")
        print(f"中性情感: {stats['neutral']} 条")
        print(f"平均分数: {stats['average_score']:.3f}")
    
    print("\n" + "="*50)


def example_context_management():
    """上下文管理示例"""
    print("=== 上下文管理示例 ===")
    
    # 创建上下文控制器
    context_controller = ContextController()
    
    session_id = "session_12345"
    
    # 模拟对话
    conversation = [
        {"role": "user", "content": "你好，我想了解一下你们的产品"},
        {"role": "assistant", "content": "您好！很高兴为您服务。请问您对哪类产品感兴趣？"},
        {"role": "user", "content": "我想买一台笔记本电脑"},
        {"role": "assistant", "content": "好的，请问您的预算大概是多少？主要用途是什么？"},
        {"role": "user", "content": "预算5000左右，主要用来办公和学习"}
    ]
    
    # 添加消息到上下文
    for message in conversation:
        print(f"\n添加消息: {message['role']} - {message['content']}")
        result = context_controller.add_message_to_context(session_id, message)
        
        if result['success']:
            print(f"上下文长度: {result['data']['context_length']}")
        else:
            print(f"添加失败: {result['error']}")
    
    # 获取LLM格式的上下文
    print(f"\n获取会话 {session_id} 的LLM格式上下文:")
    context_result = context_controller.get_session_context(session_id, format_for_llm=True)
    
    if context_result['success']:
        print("上下文内容:")
        print(context_result['data']['context_text'])
    
    print("\n" + "="*50)


def example_knowledge_base_query():
    """知识库查询示例"""
    print("=== 知识库查询示例 ===")
    
    # 创建知识库控制器
    kb_controller = KnowledgeController()
    
    # 示例查询
    queries = [
        "笔记本电脑的保修期是多久？",
        "如何申请退货？",
        "有什么优惠活动？",
        "产品规格参数"
    ]
    
    user_id = "user_12345"
    session_id = "session_12345"
    
    for query in queries:
        print(f"\n查询: {query}")
        
        # 仅搜索知识库
        search_result = kb_controller.search_knowledge_only(
            query=query,
            user_id=user_id,
            top_k=3
        )
        
        if search_result['success']:
            documents = search_result['data'].get('documents', [])
            print(f"找到 {len(documents)} 个相关文档")
            
            for i, doc in enumerate(documents[:2], 1):
                print(f"文档{i}: {doc['title']} (相似度: {doc['score']:.3f})")
                print(f"内容: {doc['content'][:100]}...")
        
        # 查询并生成回答
        response_result = kb_controller.query_and_respond(
            query=query,
            user_id=user_id,
            session_id=session_id
        )
        
        if response_result['success']:
            print(f"生成回答: {response_result['data']['answer']}")
        else:
            print(f"查询失败: {response_result['error']}")
    
    print("\n" + "="*50)


def example_chat_ingestion():
    """聊天数据入库示例"""
    print("=== 聊天数据入库示例 ===")
    
    # 创建聊天入库控制器
    ingestion_controller = ChatIngestionController()
    
    # 示例对话数据
    conversations = [
        {
            'conversation_id': 'conv_001',
            'user_id': 'user_001',
            'messages': [
                {'role': 'user', 'content': '你好，我想了解一下你们的笔记本电脑'},
                {'role': 'assistant', 'content': '您好！我们有多款笔记本电脑，请问您的预算和需求是什么？'},
                {'role': 'user', 'content': '预算5000左右，主要用来办公'},
                {'role': 'assistant', 'content': '推荐您看看我们的商务系列，性价比很高，续航能力强'}
            ],
            'tags': ['product_inquiry', 'laptop'],
            'created_at': timezone.now()
        },
        {
            'conversation_id': 'conv_002',
            'user_id': 'user_002',
            'messages': [
                {'role': 'user', 'content': '我的订单什么时候能发货？'},
                {'role': 'assistant', 'content': '请提供您的订单号，我帮您查询一下'},
                {'role': 'user', 'content': '订单号是12345'},
                {'role': 'assistant', 'content': '您的订单预计明天发货，请耐心等待'}
            ],
            'tags': ['service_request', 'shipping'],
            'created_at': timezone.now()
        }
    ]
    
    # 处理单个对话
    print("处理单个对话:")
    for conv in conversations:
        print(f"\n处理对话 {conv['conversation_id']}")
        result = ingestion_controller.process_single_conversation(conv)
        
        if result['success']:
            data = result['data']
            print(f"对话类型: {data['type']}")
            print(f"提取知识项: {len(data['knowledge_items'])} 个")
            print(f"检测意图: {data['analysis']['intents']}")
        else:
            print(f"处理失败: {result['error']}")
    
    # 批量入库
    print(f"\n批量入库 {len(conversations)} 个对话:")
    batch_result = ingestion_controller.batch_ingest_conversations(conversations)
    
    if batch_result['success']:
        data = batch_result['data']
        print(f"总数: {data['total']}")
        print(f"成功处理: {data['processed']}")
        print(f"话术知识: {data['scripts_added']} 个")
        print(f"产品知识: {data['products_added']} 个")
        if data['errors']:
            print(f"错误: {len(data['errors'])} 个")
    
    print("\n" + "="*50)


def example_comprehensive_processing():
    """综合处理示例"""
    print("=== 综合智能体处理示例 ===")
    
    # 创建综合控制器
    comprehensive_controller = ComprehensiveAgentController()
    
    user_id = "user_12345"
    session_id = "session_12345"
    
    # 模拟用户消息序列
    messages = [
        "你好，我想买一台笔记本电脑",
        "预算大概5000左右，主要用来办公",
        "有什么推荐的型号吗？",
        "这个价位的电脑质量怎么样？",
        "售后服务好不好？"
    ]
    
    for i, message in enumerate(messages, 1):
        print(f"\n=== 处理第 {i} 条消息 ===")
        print(f"用户消息: {message}")
        
        # 使用综合控制器处理消息
        result = comprehensive_controller.process_user_message(
            user_id=user_id,
            session_id=session_id,
            message=message,
            enable_kb=True
        )
        
        if result['success']:
            data = result['data']
            
            # 显示处理步骤
            print(f"助手回复: {data['answer']}")
            
            # 显示情感分析结果
            sentiment = data['steps']['sentiment']
            print(f"情感分析: {sentiment['polarity']} (分数: {sentiment['score']:.3f})")
            
            # 显示标签更新
            if 'tags' in data['steps']:
                tags = [tag['tag_name'] for tag in data['steps']['tags']]
                print(f"更新标签: {tags}")
            
            # 显示知识库使用情况
            if 'knowledge_base' in data['steps']:
                kb_info = data['steps']['knowledge_base']
                if kb_info['used']:
                    print(f"知识库查询: 找到 {kb_info['documents_found']} 个相关文档")
                else:
                    print(f"知识库查询失败: {kb_info.get('error', '未知错误')}")
        else:
            print(f"处理失败: {result['error']}")
    
    print("\n" + "="*50)


def run_all_examples():
    """运行所有示例"""
    print("开始运行智能体功能示例...\n")
    
    try:
        example_tag_management()
        example_sentiment_analysis()
        example_context_management()
        example_knowledge_base_query()
        example_chat_ingestion()
        example_comprehensive_processing()
        
        print("所有示例运行完成！")
        
    except Exception as e:
        print(f"示例运行出错: {str(e)}")


if __name__ == "__main__":
    run_all_examples() 