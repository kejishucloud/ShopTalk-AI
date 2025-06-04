#!/usr/bin/env python3
"""
ShopTalk-AI 简化系统测试脚本
测试项目的基础结构和配置完整性
"""

import os
import sys
import yaml
import logging
from pathlib import Path
from typing import Dict, Any
import subprocess
import socket
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleSystemTester:
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
    
    def test_network_connectivity(self) -> Dict[str, bool]:
        """测试网络连接性（端口检查）"""
        results = {}
        
        # 测试数据库端口连接
        databases = {
            'redis': ('redis', 'host', 'port'),
            'postgresql': ('postgresql', 'host', 'port'),
            'mysql': ('mysql', 'host', 'port'),
            'mongodb': ('mongodb', 'host', 'port'),
            'neo4j': ('neo4j', 'host', 'port'),
            'milvus': ('milvus', 'host', 'port')
        }
        
        for db_name, (config_key, host_key, port_key) in databases.items():
            try:
                db_config = self.config.get(config_key, {})
                host = db_config.get(host_key)
                port = db_config.get(port_key)
                
                if host and port:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    result = sock.connect_ex((host, port))
                    sock.close()
                    
                    results[db_name] = result == 0
                    status = "✅ 连通" if result == 0 else "❌ 无法连接"
                    logger.info(f"{db_name.upper()}: {status} ({host}:{port})")
                else:
                    results[db_name] = False
                    logger.error(f"{db_name.upper()}: ❌ 配置缺失")
            except Exception as e:
                results[db_name] = False
                logger.error(f"{db_name.upper()}: ❌ 连接测试失败 - {e}")
        
        return results
    
    def test_project_structure(self) -> Dict[str, bool]:
        """测试项目结构完整性"""
        results = {}
        
        # 检查主要目录
        main_dirs = [
            'backend',
            'frontend', 
            'agents',
            'configs',
            'utils'
        ]
        
        for dir_name in main_dirs:
            exists = Path(dir_name).exists()
            results[f"{dir_name}_dir"] = exists
            status = "✅ 存在" if exists else "❌ 缺失"
            logger.info(f"目录 {dir_name}: {status}")
        
        # 检查关键文件
        key_files = [
            'backend/manage.py',
            'backend/core/settings.py',
            'frontend/package.json',
            'configs/configs.yaml',
            'configs/agents.py',
            'requirements.txt'
        ]
        
        for file_path in key_files:
            exists = Path(file_path).exists()
            file_key = Path(file_path).name.replace('.', '_')
            results[f"{file_key}_file"] = exists
            status = "✅ 存在" if exists else "❌ 缺失"
            logger.info(f"文件 {file_path}: {status}")
        
        return results
    
    def test_backend_structure(self) -> bool:
        """测试后端Django结构"""
        try:
            backend_path = Path("backend")
            if not backend_path.exists():
                logger.error("❌ 后端目录不存在")
                return False
            
            # 检查Django应用
            apps_path = Path("backend/apps")
            if apps_path.exists():
                apps = [d.name for d in apps_path.iterdir() if d.is_dir() and not d.name.startswith('_')]
                logger.info(f"✅ 发现Django应用: {', '.join(apps)}")
            
            # 检查settings.py中的配置
            settings_path = Path("backend/core/settings.py")
            if settings_path.exists():
                with open(settings_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'DATABASES' in content and 'INSTALLED_APPS' in content:
                        logger.info("✅ Django核心配置完整")
                        return True
                    else:
                        logger.error("❌ Django核心配置不完整")
                        return False
            else:
                logger.error("❌ settings.py文件缺失")
                return False
                
        except Exception as e:
            logger.error(f"❌ 后端结构检查失败: {e}")
            return False
    
    def test_frontend_structure(self) -> bool:
        """测试前端Vue结构"""
        try:
            frontend_path = Path("frontend")
            if not frontend_path.exists():
                logger.error("❌ 前端目录不存在")
                return False
            
            # 检查package.json
            package_path = Path("frontend/package.json")
            if package_path.exists():
                with open(package_path, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                    
                dependencies = package_data.get('dependencies', {})
                dev_dependencies = package_data.get('devDependencies', {})
                
                # 检查关键依赖
                vue_deps = ['vue', '@vitejs/plugin-vue', 'vite']
                missing_deps = []
                
                for dep in vue_deps:
                    if dep not in dependencies and dep not in dev_dependencies:
                        missing_deps.append(dep)
                
                if missing_deps:
                    logger.warning(f"⚠️  缺少依赖: {', '.join(missing_deps)}")
                else:
                    logger.info("✅ 前端核心依赖完整")
                
                return True
            else:
                logger.error("❌ package.json文件缺失")
                return False
                
        except Exception as e:
            logger.error(f"❌ 前端结构检查失败: {e}")
            return False
    
    def test_agent_modules(self) -> Dict[str, bool]:
        """测试智能体模块"""
        results = {}
        
        agents_path = Path("agents")
        if not agents_path.exists():
            logger.error("❌ 智能体目录不存在")
            return {"agents_directory": False}
        
        # 检查智能体文件
        agent_files = [
            "base_agent.py",
            "chat_agent.py", 
            "knowledge_agent.py",
            "memory_agent.py",
            "sentiment_agent.py",
            "tag_agent.py"
        ]
        
        for agent_file in agent_files:
            agent_path = agents_path / agent_file
            agent_name = agent_file.replace('.py', '')
            
            try:
                if agent_path.exists():
                    with open(agent_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 基础检查：是否包含类定义
                        if 'class' in content and 'def' in content:
                            results[agent_name] = True
                            logger.info(f"✅ {agent_name}: 模块完整")
                        else:
                            results[agent_name] = False
                            logger.error(f"❌ {agent_name}: 模块内容不完整")
                else:
                    results[agent_name] = False
                    logger.error(f"❌ {agent_name}: 文件缺失")
            except Exception as e:
                results[agent_name] = False
                logger.error(f"❌ {agent_name}: 检查失败 - {e}")
        
        return results
    
    def test_configuration(self) -> Dict[str, bool]:
        """测试配置完整性"""
        results = {}
        
        # 测试configs.yaml
        if self.config:
            required_sections = ['llm', 'embedding', 'redis', 'postgresql']
            for section in required_sections:
                has_section = section in self.config
                results[f"config_{section}"] = has_section
                status = "✅ 配置" if has_section else "❌ 缺失"
                logger.info(f"配置节 {section}: {status}")
        else:
            results['config_yaml'] = False
            logger.error("❌ configs.yaml加载失败")
        
        # 测试agents.py配置
        agents_config_path = Path("configs/agents.py")
        results['agents_config'] = agents_config_path.exists()
        status = "✅ 存在" if agents_config_path.exists() else "❌ 缺失"
        logger.info(f"智能体配置文件: {status}")
        
        # 测试环境变量文件
        env_files = ['config.env', '.env']
        env_found = False
        for env_file in env_files:
            if Path(env_file).exists():
                env_found = True
                logger.info(f"✅ 环境配置文件: {env_file}")
                break
        
        results['env_config'] = env_found
        if not env_found:
            logger.warning("⚠️  未找到环境配置文件")
        
        return results
    
    def test_llm_endpoints(self) -> Dict[str, bool]:
        """测试LLM服务端点连通性"""
        results = {}
        
        # 测试LLM端点
        llm_config = self.config.get('llm', {})
        llm_url = llm_config.get('base_url', '')
        
        if llm_url:
            try:
                # 简单的HTTP连接测试
                import urllib.request
                import urllib.error
                
                req = urllib.request.Request(llm_url)
                req.add_header('User-Agent', 'ShopTalk-AI-Test/1.0')
                
                try:
                    with urllib.request.urlopen(req, timeout=10) as response:
                        results['llm_endpoint'] = response.getcode() < 500
                        logger.info(f"✅ LLM端点响应: {response.getcode()}")
                except urllib.error.HTTPError as e:
                    if e.code < 500:  # 4xx错误也算连通
                        results['llm_endpoint'] = True
                        logger.info(f"✅ LLM端点连通 (HTTP {e.code})")
                    else:
                        results['llm_endpoint'] = False
                        logger.error(f"❌ LLM端点服务器错误: {e.code}")
                        
            except Exception as e:
                results['llm_endpoint'] = False
                logger.error(f"❌ LLM端点测试失败: {e}")
        else:
            results['llm_endpoint'] = False
            logger.error("❌ LLM端点配置缺失")
        
        # 测试Embedding端点
        embedding_config = self.config.get('embedding', {})
        embedding_url = embedding_config.get('base_url', '')
        
        if embedding_url:
            try:
                req = urllib.request.Request(embedding_url)
                req.add_header('User-Agent', 'ShopTalk-AI-Test/1.0')
                
                try:
                    with urllib.request.urlopen(req, timeout=10) as response:
                        results['embedding_endpoint'] = response.getcode() < 500
                        logger.info(f"✅ Embedding端点响应: {response.getcode()}")
                except urllib.error.HTTPError as e:
                    if e.code < 500:
                        results['embedding_endpoint'] = True
                        logger.info(f"✅ Embedding端点连通 (HTTP {e.code})")
                    else:
                        results['embedding_endpoint'] = False
                        logger.error(f"❌ Embedding端点服务器错误: {e.code}")
                        
            except Exception as e:
                results['embedding_endpoint'] = False
                logger.error(f"❌ Embedding端点测试失败: {e}")
        else:
            results['embedding_endpoint'] = False
            logger.error("❌ Embedding端点配置缺失")
        
        return results
    
    def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始简化系统测试...")
        
        # 1. 项目结构测试
        logger.info("\n📁 测试项目结构...")
        self.test_results['structure'] = self.test_project_structure()
        
        # 2. 后端结构测试
        logger.info("\n🔧 测试后端结构...")
        self.test_results['backend'] = self.test_backend_structure()
        
        # 3. 前端结构测试
        logger.info("\n🎨 测试前端结构...")
        self.test_results['frontend'] = self.test_frontend_structure()
        
        # 4. 智能体模块测试
        logger.info("\n🤖 测试智能体模块...")
        self.test_results['agents'] = self.test_agent_modules()
        
        # 5. 配置完整性测试
        logger.info("\n📋 测试配置完整性...")
        self.test_results['config'] = self.test_configuration()
        
        # 6. 网络连通性测试
        logger.info("\n🌐 测试网络连通性...")
        self.test_results['network'] = self.test_network_connectivity()
        
        # 7. LLM端点测试
        logger.info("\n🧠 测试LLM端点...")
        self.test_results['llm_endpoints'] = self.test_llm_endpoints()
        
        # 生成测试报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        logger.info("\n" + "="*80)
        logger.info("📊 ShopTalk-AI 系统测试报告")
        logger.info("="*80)
        
        total_tests = 0
        passed_tests = 0
        
        # 项目结构测试
        structure_results = self.test_results.get('structure', {})
        for item, result in structure_results.items():
            total_tests += 1
            if result:
                passed_tests += 1
            logger.info(f"📁 {item}: {'✅ PASS' if result else '❌ FAIL'}")
        
        # 后端测试
        backend_passed = self.test_results.get('backend', False)
        total_tests += 1
        if backend_passed:
            passed_tests += 1
        logger.info(f"🔧 后端结构: {'✅ PASS' if backend_passed else '❌ FAIL'}")
        
        # 前端测试
        frontend_passed = self.test_results.get('frontend', False)
        total_tests += 1
        if frontend_passed:
            passed_tests += 1
        logger.info(f"🎨 前端结构: {'✅ PASS' if frontend_passed else '❌ FAIL'}")
        
        # 智能体测试
        agent_results = self.test_results.get('agents', {})
        for agent_name, result in agent_results.items():
            total_tests += 1
            if result:
                passed_tests += 1
            logger.info(f"🤖 {agent_name}: {'✅ PASS' if result else '❌ FAIL'}")
        
        # 配置测试
        config_results = self.test_results.get('config', {})
        for config_item, result in config_results.items():
            total_tests += 1
            if result:
                passed_tests += 1
            logger.info(f"📋 {config_item}: {'✅ PASS' if result else '❌ FAIL'}")
        
        # 网络连通性测试
        network_results = self.test_results.get('network', {})
        for service, result in network_results.items():
            total_tests += 1
            if result:
                passed_tests += 1
            logger.info(f"🌐 {service}: {'✅ PASS' if result else '❌ FAIL'}")
        
        # LLM端点测试
        llm_results = self.test_results.get('llm_endpoints', {})
        for endpoint, result in llm_results.items():
            total_tests += 1
            if result:
                passed_tests += 1
            logger.info(f"🧠 {endpoint}: {'✅ PASS' if result else '❌ FAIL'}")
        
        # 总体结果
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        logger.info("="*80)
        logger.info(f"📈 测试总结: {passed_tests}/{total_tests} 通过 ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            logger.info("🎉 系统整体状态良好！可以开始开发和测试。")
        elif success_rate >= 60:
            logger.info("⚠️  系统存在一些问题，建议先修复关键问题。")
        else:
            logger.info("🚨 系统存在严重问题，需要立即修复才能正常使用。")
        
        logger.info("="*80)
        
        # 输出修复建议
        self.generate_recommendations()
    
    def generate_recommendations(self):
        """生成修复建议"""
        logger.info("\n💡 修复建议:")
        
        # 检查网络连通性问题
        network_results = self.test_results.get('network', {})
        failed_connections = [service for service, result in network_results.items() if not result]
        
        if failed_connections:
            logger.info("🔧 数据库连接问题:")
            for service in failed_connections:
                logger.info(f"   - 检查{service}服务是否启动")
                logger.info(f"   - 确认configs.yaml中{service}配置正确")
        
        # 检查配置问题
        config_results = self.test_results.get('config', {})
        failed_configs = [item for item, result in config_results.items() if not result]
        
        if failed_configs:
            logger.info("📋 配置文件问题:")
            for config_item in failed_configs:
                logger.info(f"   - 检查{config_item}配置项")
        
        # 检查智能体问题
        agent_results = self.test_results.get('agents', {})
        failed_agents = [agent for agent, result in agent_results.items() if not result]
        
        if failed_agents:
            logger.info("🤖 智能体模块问题:")
            for agent in failed_agents:
                logger.info(f"   - 检查agents/{agent}.py文件完整性")
        
        logger.info("\n✨ 完成修复后，重新运行此脚本验证。")

def main():
    """主函数"""
    tester = SimpleSystemTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main() 