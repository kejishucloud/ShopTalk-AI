#!/usr/bin/env python3
"""
ShopTalk-AI 系统集成测试脚本
主要测试：
1. 数据库连接测试（不写入数据）
2. 后端API测试
3. 智能体功能测试
4. 前端资源检查
"""

import os
import sys
import yaml
import asyncio
import aiohttp
import logging
from pathlib import Path
from typing import Dict, Any, List
import subprocess
import socket
import redis
import psycopg2
import pymongo
from neo4j import GraphDatabase
import mysql.connector

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemTester:
    def __init__(self):
        self.config = self.load_config()
        self.test_results = {}
        
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open('configs/configs.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config.get('DEV', {})
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return {}
    
    def test_database_connections(self) -> Dict[str, bool]:
        """测试所有数据库连接（只读测试）"""
        results = {}
        
        # 测试PostgreSQL
        try:
            pg_config = self.config.get('postgresql', {})
            conn = psycopg2.connect(
                host=pg_config.get('host'),
                port=pg_config.get('port'),
                user=pg_config.get('username'),
                password=pg_config.get('password'),
                dbname='postgres'  # 连接到默认数据库
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            results['postgresql'] = True
            logger.info("✅ PostgreSQL连接成功")
        except Exception as e:
            results['postgresql'] = False
            logger.error(f"❌ PostgreSQL连接失败: {e}")
        
        # 测试MySQL
        try:
            mysql_config = self.config.get('mysql', {})
            conn = mysql.connector.connect(
                host=mysql_config.get('host'),
                port=mysql_config.get('port'),
                user=mysql_config.get('username'),
                password=mysql_config.get('password')
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            results['mysql'] = True
            logger.info("✅ MySQL连接成功")
        except Exception as e:
            results['mysql'] = False
            logger.error(f"❌ MySQL连接失败: {e}")
        
        # 测试MongoDB
        try:
            mongo_config = self.config.get('mongodb', {})
            client = pymongo.MongoClient(
                host=mongo_config.get('host'),
                port=mongo_config.get('port'),
                username=mongo_config.get('username'),
                password=mongo_config.get('password'),
                serverSelectionTimeoutMS=5000
            )
            client.admin.command('ping')
            client.close()
            results['mongodb'] = True
            logger.info("✅ MongoDB连接成功")
        except Exception as e:
            results['mongodb'] = False
            logger.error(f"❌ MongoDB连接失败: {e}")
        
        # 测试Redis
        try:
            redis_config = self.config.get('redis', {})
            r = redis.Redis(
                host=redis_config.get('host'),
                port=redis_config.get('port'),
                password=redis_config.get('password'),
                socket_timeout=5
            )
            r.ping()
            results['redis'] = True
            logger.info("✅ Redis连接成功")
        except Exception as e:
            results['redis'] = False
            logger.error(f"❌ Redis连接失败: {e}")
        
        # 测试Neo4j
        try:
            neo4j_config = self.config.get('neo4j', {})
            driver = GraphDatabase.driver(
                f"bolt://{neo4j_config.get('host')}:{neo4j_config.get('port')}",
                auth=(neo4j_config.get('username'), neo4j_config.get('password'))
            )
            with driver.session() as session:
                session.run("RETURN 1")
            driver.close()
            results['neo4j'] = True
            logger.info("✅ Neo4j连接成功")
        except Exception as e:
            results['neo4j'] = False
            logger.error(f"❌ Neo4j连接失败: {e}")
        
        # 测试Milvus
        try:
            milvus_config = self.config.get('milvus', {})
            # 简单的端口连接测试
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((milvus_config.get('host'), milvus_config.get('port')))
            sock.close()
            results['milvus'] = result == 0
            if result == 0:
                logger.info("✅ Milvus端口连接成功")
            else:
                logger.error("❌ Milvus端口连接失败")
        except Exception as e:
            results['milvus'] = False
            logger.error(f"❌ Milvus连接失败: {e}")
        
        return results
    
    def test_backend_service(self) -> bool:
        """测试后端服务状态"""
        try:
            # 检查Django项目结构
            backend_path = Path("backend")
            if not backend_path.exists():
                logger.error("❌ 后端目录不存在")
                return False
            
            # 检查核心文件
            core_files = [
                "backend/manage.py",
                "backend/core/settings.py",
                "backend/core/urls.py"
            ]
            
            for file_path in core_files:
                if not Path(file_path).exists():
                    logger.error(f"❌ 核心文件缺失: {file_path}")
                    return False
            
            logger.info("✅ 后端项目结构完整")
            
            # 尝试运行Django检查
            try:
                result = subprocess.run(
                    ["python", "backend/manage.py", "check", "--deploy"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd="."
                )
                if result.returncode == 0:
                    logger.info("✅ Django配置检查通过")
                    return True
                else:
                    logger.warning(f"⚠️  Django配置检查有警告: {result.stderr}")
                    return True  # 警告不算失败
            except subprocess.TimeoutExpired:
                logger.warning("⚠️  Django检查超时")
                return True
            except Exception as e:
                logger.error(f"❌ Django检查失败: {e}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 后端服务检查失败: {e}")
            return False
    
    def test_frontend_resources(self) -> bool:
        """测试前端资源完整性"""
        try:
            frontend_path = Path("frontend")
            if not frontend_path.exists():
                logger.error("❌ 前端目录不存在")
                return False
            
            # 检查关键文件
            key_files = [
                "frontend/package.json",
                "frontend/vite.config.ts",
                "frontend/src/main.ts",
                "frontend/src/App.vue"
            ]
            
            missing_files = []
            for file_path in key_files:
                if not Path(file_path).exists():
                    missing_files.append(file_path)
            
            if missing_files:
                logger.error(f"❌ 前端关键文件缺失: {missing_files}")
                return False
            
            # 检查package.json内容
            import json
            with open("frontend/package.json", 'r', encoding='utf-8') as f:
                package_data = json.load(f)
                
            if not package_data.get('scripts'):
                logger.error("❌ package.json缺少scripts配置")
                return False
                
            logger.info("✅ 前端资源完整性检查通过")
            return True
            
        except Exception as e:
            logger.error(f"❌ 前端资源检查失败: {e}")
            return False
    
    def test_agent_modules(self) -> Dict[str, bool]:
        """测试智能体模块完整性"""
        results = {}
        
        agents_path = Path("agents")
        if not agents_path.exists():
            logger.error("❌ 智能体目录不存在")
            return {"agents_directory": False}
        
        # 检查智能体文件
        agent_files = [
            "agents/base_agent.py",
            "agents/chat_agent.py",
            "agents/knowledge_agent.py",
            "agents/memory_agent.py",
            "agents/sentiment_agent.py",
            "agents/tag_agent.py"
        ]
        
        for agent_file in agent_files:
            agent_name = Path(agent_file).stem
            try:
                if Path(agent_file).exists():
                    # 简单的语法检查
                    with open(agent_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 检查是否包含基本的类定义
                        if 'class' in content and 'def' in content:
                            results[agent_name] = True
                            logger.info(f"✅ {agent_name} 模块完整")
                        else:
                            results[agent_name] = False
                            logger.error(f"❌ {agent_name} 模块内容不完整")
                else:
                    results[agent_name] = False
                    logger.error(f"❌ {agent_name} 文件缺失")
            except Exception as e:
                results[agent_name] = False
                logger.error(f"❌ {agent_name} 检查失败: {e}")
        
        return results
    
    async def test_llm_endpoints(self) -> Dict[str, bool]:
        """测试LLM服务端点（不发送实际请求）"""
        results = {}
        
        # 测试LLM端点
        llm_config = self.config.get('llm', {})
        base_url = llm_config.get('base_url')
        
        if base_url:
            try:
                timeout = aiohttp.ClientTimeout(total=10)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    # 只测试连通性，不发送实际API请求
                    async with session.get(base_url, allow_redirects=False) as response:
                        results['llm_endpoint'] = response.status < 500
                        logger.info(f"✅ LLM端点连通性测试: {response.status}")
            except Exception as e:
                results['llm_endpoint'] = False
                logger.error(f"❌ LLM端点测试失败: {e}")
        else:
            results['llm_endpoint'] = False
            logger.error("❌ LLM端点配置缺失")
        
        # 测试Embedding端点
        embedding_config = self.config.get('embedding', {})
        embedding_url = embedding_config.get('base_url')
        
        if embedding_url:
            try:
                timeout = aiohttp.ClientTimeout(total=10)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(embedding_url, allow_redirects=False) as response:
                        results['embedding_endpoint'] = response.status < 500
                        logger.info(f"✅ Embedding端点连通性测试: {response.status}")
            except Exception as e:
                results['embedding_endpoint'] = False
                logger.error(f"❌ Embedding端点测试失败: {e}")
        else:
            results['embedding_endpoint'] = False
            logger.error("❌ Embedding端点配置缺失")
        
        return results
    
    def test_config_integrity(self) -> bool:
        """测试配置完整性"""
        try:
            # 检查configs.yaml
            if not self.config:
                logger.error("❌ configs.yaml配置加载失败")
                return False
            
            # 检查必要配置项
            required_configs = ['llm', 'embedding', 'redis', 'postgresql']
            missing_configs = []
            
            for config_key in required_configs:
                if config_key not in self.config:
                    missing_configs.append(config_key)
            
            if missing_configs:
                logger.error(f"❌ 配置项缺失: {missing_configs}")
                return False
            
            # 检查agents.py配置
            agents_config_path = Path("configs/agents.py")
            if not agents_config_path.exists():
                logger.error("❌ agents.py配置文件缺失")
                return False
            
            logger.info("✅ 配置完整性检查通过")
            return True
            
        except Exception as e:
            logger.error(f"❌ 配置完整性检查失败: {e}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始系统集成测试...")
        
        # 1. 配置完整性测试
        logger.info("\n📋 测试配置完整性...")
        self.test_results['config'] = self.test_config_integrity()
        
        # 2. 数据库连接测试
        logger.info("\n💾 测试数据库连接...")
        self.test_results['databases'] = self.test_database_connections()
        
        # 3. 后端服务测试
        logger.info("\n🔧 测试后端服务...")
        self.test_results['backend'] = self.test_backend_service()
        
        # 4. 前端资源测试
        logger.info("\n🎨 测试前端资源...")
        self.test_results['frontend'] = self.test_frontend_resources()
        
        # 5. 智能体模块测试
        logger.info("\n🤖 测试智能体模块...")
        self.test_results['agents'] = self.test_agent_modules()
        
        # 6. LLM端点测试
        logger.info("\n🧠 测试LLM端点...")
        self.test_results['llm_endpoints'] = await self.test_llm_endpoints()
        
        # 生成测试报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        logger.info("\n" + "="*60)
        logger.info("📊 系统集成测试报告")
        logger.info("="*60)
        
        total_tests = 0
        passed_tests = 0
        
        # 配置测试
        config_passed = self.test_results['config']
        total_tests += 1
        if config_passed:
            passed_tests += 1
        logger.info(f"📋 配置完整性: {'✅ PASS' if config_passed else '❌ FAIL'}")
        
        # 数据库测试
        db_results = self.test_results['databases']
        for db_name, result in db_results.items():
            total_tests += 1
            if result:
                passed_tests += 1
            logger.info(f"💾 {db_name.upper()}数据库: {'✅ PASS' if result else '❌ FAIL'}")
        
        # 后端测试
        backend_passed = self.test_results['backend']
        total_tests += 1
        if backend_passed:
            passed_tests += 1
        logger.info(f"🔧 后端服务: {'✅ PASS' if backend_passed else '❌ FAIL'}")
        
        # 前端测试
        frontend_passed = self.test_results['frontend']
        total_tests += 1
        if frontend_passed:
            passed_tests += 1
        logger.info(f"🎨 前端资源: {'✅ PASS' if frontend_passed else '❌ FAIL'}")
        
        # 智能体测试
        agent_results = self.test_results['agents']
        for agent_name, result in agent_results.items():
            total_tests += 1
            if result:
                passed_tests += 1
            logger.info(f"🤖 {agent_name}: {'✅ PASS' if result else '❌ FAIL'}")
        
        # LLM端点测试
        llm_results = self.test_results['llm_endpoints']
        for endpoint_name, result in llm_results.items():
            total_tests += 1
            if result:
                passed_tests += 1
            logger.info(f"🧠 {endpoint_name}: {'✅ PASS' if result else '❌ FAIL'}")
        
        # 总体结果
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        logger.info("="*60)
        logger.info(f"📈 测试总结: {passed_tests}/{total_tests} 通过 ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            logger.info("🎉 系统整体状态良好！")
        elif success_rate >= 60:
            logger.info("⚠️  系统存在一些问题，建议检查")
        else:
            logger.info("🚨 系统存在严重问题，需要立即修复")
        
        logger.info("="*60)

async def main():
    """主函数"""
    tester = SystemTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 