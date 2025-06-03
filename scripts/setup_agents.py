#!/usr/bin/env python
"""
智能体系统安装和配置脚本
自动化部署RAGFlow、Langflow和智能体环境
"""

import os
import sys
import subprocess
import json
import requests
import time
from pathlib import Path
from typing import Dict, Any, List


class AgentSystemSetup:
    """智能体系统安装器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.conda_env = "agent"
        self.services = {
            'ragflow': {
                'port': 9380,
                'health_endpoint': '/health',
                'container_name': 'ragflow-server'
            },
            'langflow': {
                'port': 7860,
                'health_endpoint': '/health',
                'container_name': 'langflow-server'
            },
            'redis': {
                'port': 6379,
                'container_name': 'redis-server'
            },
            'elasticsearch': {
                'port': 9200,
                'health_endpoint': '/_cluster/health',
                'container_name': 'elasticsearch-server'
            }
        }
    
    def print_step(self, step: str, description: str = ""):
        """打印安装步骤"""
        print(f"\n{'='*60}")
        print(f"步骤: {step}")
        if description:
            print(f"描述: {description}")
        print(f"{'='*60}")
    
    def run_command(self, command: str, check: bool = True, shell: bool = True) -> subprocess.CompletedProcess:
        """执行命令"""
        print(f"执行命令: {command}")
        try:
            result = subprocess.run(command, shell=shell, check=check, 
                                  capture_output=True, text=True)
            if result.stdout:
                print(f"输出: {result.stdout}")
            return result
        except subprocess.CalledProcessError as e:
            print(f"命令执行失败: {e}")
            if e.stderr:
                print(f"错误: {e.stderr}")
            if check:
                raise
            return e
    
    def check_conda_environment(self) -> bool:
        """检查conda环境"""
        try:
            result = self.run_command(f"conda env list | grep {self.conda_env}", check=False)
            return result.returncode == 0
        except:
            return False
    
    def create_conda_environment(self):
        """创建conda环境"""
        self.print_step("创建Conda环境", f"创建名为 '{self.conda_env}' 的Python环境")
        
        if self.check_conda_environment():
            print(f"Conda环境 '{self.conda_env}' 已存在")
            return
        
        # 创建conda环境
        self.run_command(f"conda create -n {self.conda_env} python=3.10 -y")
        print(f"Conda环境 '{self.conda_env}' 创建成功")
    
    def install_python_dependencies(self):
        """安装Python依赖"""
        self.print_step("安装Python依赖", "安装项目所需的Python包")
        
        # 激活conda环境并安装依赖
        activate_cmd = f"conda activate {self.conda_env}"
        requirements_file = self.project_root / "requirements.txt"
        
        if requirements_file.exists():
            install_cmd = f"{activate_cmd} && pip install -r {requirements_file}"
            self.run_command(install_cmd)
        else:
            print("requirements.txt文件不存在，跳过依赖安装")
    
    def setup_docker_services(self):
        """设置Docker服务"""
        self.print_step("设置Docker服务", "启动RAGFlow、Langflow等必需服务")
        
        # 检查Docker是否安装
        try:
            self.run_command("docker --version")
        except subprocess.CalledProcessError:
            print("错误: Docker未安装，请先安装Docker")
            return False
        
        # 启动Redis
        self.start_redis()
        
        # 启动Elasticsearch
        self.start_elasticsearch()
        
        # 启动RAGFlow
        self.start_ragflow()
        
        # 启动Langflow
        self.start_langflow()
        
        return True
    
    def start_redis(self):
        """启动Redis服务"""
        print("启动Redis服务...")
        
        # 检查Redis容器是否已运行
        check_cmd = f"docker ps | grep {self.services['redis']['container_name']}"
        result = self.run_command(check_cmd, check=False)
        
        if result.returncode == 0:
            print("Redis容器已在运行")
            return
        
        # 启动Redis容器
        redis_cmd = (
            f"docker run -d "
            f"--name {self.services['redis']['container_name']} "
            f"-p {self.services['redis']['port']}:6379 "
            f"redis:7-alpine redis-server --appendonly yes"
        )
        
        self.run_command(redis_cmd)
        print("Redis服务启动成功")
    
    def start_elasticsearch(self):
        """启动Elasticsearch服务"""
        print("启动Elasticsearch服务...")
        
        # 检查ES容器是否已运行
        check_cmd = f"docker ps | grep {self.services['elasticsearch']['container_name']}"
        result = self.run_command(check_cmd, check=False)
        
        if result.returncode == 0:
            print("Elasticsearch容器已在运行")
            return
        
        # 启动ES容器
        es_cmd = (
            f"docker run -d "
            f"--name {self.services['elasticsearch']['container_name']} "
            f"-p {self.services['elasticsearch']['port']}:9200 "
            f"-e discovery.type=single-node "
            f"-e ES_JAVA_OPTS='-Xms512m -Xmx512m' "
            f"elasticsearch:8.11.1"
        )
        
        self.run_command(es_cmd)
        
        # 等待ES启动
        self.wait_for_service('elasticsearch')
        print("Elasticsearch服务启动成功")
    
    def start_ragflow(self):
        """启动RAGFlow服务"""
        print("启动RAGFlow服务...")
        
        # 检查RAGFlow容器是否已运行
        check_cmd = f"docker ps | grep {self.services['ragflow']['container_name']}"
        result = self.run_command(check_cmd, check=False)
        
        if result.returncode == 0:
            print("RAGFlow容器已在运行")
            return
        
        # 创建RAGFlow数据目录
        ragflow_data_dir = self.project_root / "data" / "ragflow"
        ragflow_data_dir.mkdir(parents=True, exist_ok=True)
        
        # 启动RAGFlow容器
        ragflow_cmd = (
            f"docker run -d "
            f"--name {self.services['ragflow']['container_name']} "
            f"-p {self.services['ragflow']['port']}:9380 "
            f"-v {ragflow_data_dir}:/app/data "
            f"-e ELASTICSEARCH_URL=http://host.docker.internal:9200 "
            f"infiniflow/ragflow:v0.19.0"
        )
        
        self.run_command(ragflow_cmd)
        
        # 等待RAGFlow启动
        self.wait_for_service('ragflow')
        print("RAGFlow服务启动成功")
    
    def start_langflow(self):
        """启动Langflow服务"""
        print("启动Langflow服务...")
        
        # 检查Langflow容器是否已运行
        check_cmd = f"docker ps | grep {self.services['langflow']['container_name']}"
        result = self.run_command(check_cmd, check=False)
        
        if result.returncode == 0:
            print("Langflow容器已在运行")
            return
        
        # 创建Langflow数据目录
        langflow_data_dir = self.project_root / "data" / "langflow"
        langflow_data_dir.mkdir(parents=True, exist_ok=True)
        
        # 启动Langflow容器
        langflow_cmd = (
            f"docker run -d "
            f"--name {self.services['langflow']['container_name']} "
            f"-p {self.services['langflow']['port']}:7860 "
            f"-v {langflow_data_dir}:/app/data "
            f"langflowai/langflow:latest"
        )
        
        self.run_command(langflow_cmd)
        
        # 等待Langflow启动
        self.wait_for_service('langflow')
        print("Langflow服务启动成功")
    
    def wait_for_service(self, service_name: str, timeout: int = 120):
        """等待服务启动"""
        service = self.services[service_name]
        port = service['port']
        health_endpoint = service.get('health_endpoint', '')
        
        print(f"等待{service_name}服务启动...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                if health_endpoint:
                    url = f"http://localhost:{port}{health_endpoint}"
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        break
                else:
                    # 简单的端口检查
                    import socket
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    result = sock.connect_ex(('localhost', port))
                    sock.close()
                    if result == 0:
                        break
            except:
                pass
            
            time.sleep(5)
            print(".", end="", flush=True)
        else:
            print(f"\n警告: {service_name}服务可能未正常启动")
        
        print(f"\n{service_name}服务检查完成")
    
    def setup_django_environment(self):
        """设置Django环境"""
        self.print_step("设置Django环境", "配置数据库和静态文件")
        
        # 切换到项目目录
        os.chdir(self.project_root)
        
        # 运行Django设置命令
        django_commands = [
            "python backend/manage.py makemigrations",
            "python backend/manage.py migrate",
            "python backend/manage.py collectstatic --noinput",
        ]
        
        for cmd in django_commands:
            self.run_command(f"conda activate {self.conda_env} && {cmd}")
    
    def create_sample_data(self):
        """创建示例数据"""
        self.print_step("创建示例数据", "添加测试知识库和用户数据")
        
        # 创建示例数据的Django命令
        sample_data_cmd = "python backend/manage.py shell -c \"\
from backend.apps.knowledge.models import KnowledgeBase, FAQ, Product; \
from django.contrib.auth import get_user_model; \
User = get_user_model(); \
user, _ = User.objects.get_or_create(username='admin', defaults={'email': 'admin@example.com'}); \
kb, _ = KnowledgeBase.objects.get_or_create(name='测试知识库', defaults={'knowledge_type': 'faq', 'created_by': user}); \
FAQ.objects.get_or_create(knowledge_base=kb, question='什么是AI智能客服？', defaults={'answer': 'AI智能客服是基于人工智能技术的自动化客户服务系统，能够理解用户需求并提供个性化回复。', 'created_by': user}); \
Product.objects.get_or_create(knowledge_base=kb, sku='TEST001', defaults={'name': '测试商品', 'price': 99.99, 'description': '这是一个测试商品，用于演示智能体功能。'}); \
print('示例数据创建成功'); \
\""
        
        self.run_command(f"conda activate {self.conda_env} && {sample_data_cmd}")
    
    def test_agent_system(self):
        """测试智能体系统"""
        self.print_step("测试智能体系统", "验证各个组件是否正常工作")
        
        # 测试Django服务器
        print("测试Django服务器...")
        test_server_cmd = (
            f"conda activate {self.conda_env} && "
            f"cd {self.project_root} && "
            f"python backend/manage.py test backend.apps.agents --verbosity=2"
        )
        
        result = self.run_command(test_server_cmd, check=False)
        if result.returncode == 0:
            print("Django测试通过")
        else:
            print("Django测试失败，请检查配置")
    
    def generate_config_files(self):
        """生成配置文件"""
        self.print_step("生成配置文件", "创建环境变量和配置文件")
        
        # 创建.env文件
        env_file = self.project_root / ".env"
        if not env_file.exists():
            env_content = f"""# ShopTalk-AI 环境配置
DEBUG=True
SECRET_KEY=your-secret-key-{int(time.time())}
ALLOWED_HOSTS=localhost,127.0.0.1

# 数据库配置
DATABASE_URL=sqlite:///{self.project_root}/db.sqlite3
REDIS_URL=redis://localhost:6379/0

# RAGFlow配置
RAGFLOW_API_ENDPOINT=http://localhost:9380
RAGFLOW_API_KEY=your-ragflow-api-key
RAGFLOW_DATASET_ID=

# Langflow配置
LANGFLOW_ENDPOINT=http://localhost:7860
LANGFLOW_API_KEY=your-langflow-api-key
LANGFLOW_FLOW_ID=

# LLM配置
OPENAI_API_KEY=your-openai-api-key
LLM_MODEL=gpt-3.5-turbo
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=1000

# 智能体配置
TAG_AGENT_CONFIDENCE_THRESHOLD=0.6
SENTIMENT_AGENT_THRESHOLD=0.5
MEMORY_AGENT_MAX_SHORT=50
MEMORY_AGENT_MAX_LONG=200
KNOWLEDGE_AGENT_TOP_K=5
"""
            env_file.write_text(env_content)
            print(f"已创建环境配置文件: {env_file}")
    
    def print_completion_info(self):
        """打印完成信息"""
        self.print_step("安装完成", "智能体系统已成功安装")
        
        print("\n🎉 智能体系统安装完成！")
        print("\n📋 服务信息:")
        print(f"  • RAGFlow:      http://localhost:{self.services['ragflow']['port']}")
        print(f"  • Langflow:     http://localhost:{self.services['langflow']['port']}")
        print(f"  • Redis:        localhost:{self.services['redis']['port']}")
        print(f"  • Elasticsearch: http://localhost:{self.services['elasticsearch']['port']}")
        
        print("\n🚀 启动Django服务器:")
        print(f"  conda activate {self.conda_env}")
        print(f"  cd {self.project_root}")
        print("  python backend/manage.py runserver")
        
        print("\n📝 API端点:")
        print("  • 聊天API:       POST /api/agents/chat/")
        print("  • 标签分析:       POST /api/agents/analyze/tags/")
        print("  • 情感分析:       POST /api/agents/analyze/sentiment/")
        print("  • 知识库查询:     POST /api/agents/knowledge/query/")
        print("  • 智能体状态:     GET  /api/agents/status/")
        
        print("\n⚠️  注意事项:")
        print("  1. 请在.env文件中配置你的API密钥")
        print("  2. 确保RAGFlow和Langflow服务正常运行")
        print("  3. 根据需要上传知识库文档到RAGFlow")
        print("  4. 在Langflow中创建对话流程")
        
        print("\n📖 更多信息请查看README.md")
    
    def run_setup(self):
        """运行完整安装流程"""
        try:
            print("🤖 开始安装ShopTalk-AI智能体系统")
            
            # 1. 创建conda环境
            self.create_conda_environment()
            
            # 2. 安装Python依赖
            self.install_python_dependencies()
            
            # 3. 设置Docker服务
            if not self.setup_docker_services():
                print("Docker服务设置失败，但可以继续手动配置")
            
            # 4. 生成配置文件
            self.generate_config_files()
            
            # 5. 设置Django环境
            self.setup_django_environment()
            
            # 6. 创建示例数据
            self.create_sample_data()
            
            # 7. 测试系统
            self.test_agent_system()
            
            # 8. 打印完成信息
            self.print_completion_info()
            
        except Exception as e:
            print(f"\n❌ 安装过程中出现错误: {e}")
            print("请检查错误信息并手动解决相关问题")
            sys.exit(1)


def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("""
ShopTalk-AI智能体系统安装脚本

用法:
  python scripts/setup_agents.py              # 完整安装
  python scripts/setup_agents.py --help       # 显示帮助

此脚本将：
1. 创建conda虚拟环境
2. 安装Python依赖
3. 启动Docker服务 (RAGFlow, Langflow, Redis, Elasticsearch)
4. 配置Django环境
5. 创建示例数据
6. 测试系统功能

要求:
- 已安装conda和Docker
- 有足够的磁盘空间 (至少5GB)
- 网络连接正常
        """)
        return
    
    setup = AgentSystemSetup()
    setup.run_setup()


if __name__ == "__main__":
    main() 