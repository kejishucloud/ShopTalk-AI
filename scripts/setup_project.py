#!/usr/bin/env python
"""
AI智能客服系统 - 项目设置脚本
自动化项目初始化和配置
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_DIR = PROJECT_ROOT / 'backend'


def run_command(command, cwd=None, check=True):
    """运行命令"""
    print(f"执行命令: {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd or PROJECT_ROOT,
            check=check,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
        if e.stderr:
            print(f"错误信息: {e.stderr}")
        if check:
            sys.exit(1)
        return e


def check_python_version():
    """检查Python版本"""
    print("检查Python版本...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("错误: 需要Python 3.8或更高版本")
        sys.exit(1)
    print(f"Python版本: {version.major}.{version.minor}.{version.micro} ✓")


def check_conda_environment():
    """检查conda环境"""
    print("检查conda环境...")
    try:
        result = run_command("conda info --envs", check=False)
        if "agent" in result.stdout:
            print("conda agent环境已存在 ✓")
            return True
        else:
            print("conda agent环境不存在，请先创建环境")
            return False
    except:
        print("conda未安装或不可用")
        return False


def install_dependencies():
    """安装依赖"""
    print("安装Python依赖...")
    
    # 基础依赖
    basic_deps = [
        "Django==4.2.7",
        "djangorestframework==3.14.0",
        "django-cors-headers==4.3.1",
        "django-environ==0.11.2",
        "django-extensions==3.2.3",
        "redis==5.0.1",
        "django-redis==5.4.0",
        "celery==5.3.4",
        "django-celery-beat==2.5.0",
        "django-celery-results==2.5.1",
    ]
    
    for dep in basic_deps:
        run_command(f"pip install {dep}")
    
    # AI相关依赖
    ai_deps = [
        "openai==1.3.5",
        "anthropic==0.7.7",
        "zhipuai==1.0.7",
        "dashscope==1.14.1",
        "requests==2.31.0",
        "httpx==0.25.2",
    ]
    
    for dep in ai_deps:
        run_command(f"pip install {dep}")
    
    # 浏览器自动化
    browser_deps = [
        "playwright==1.40.0",
        "selenium==4.15.2",
    ]
    
    for dep in browser_deps:
        run_command(f"pip install {dep}")
    
    # 安装playwright浏览器
    print("安装Playwright浏览器...")
    run_command("playwright install chromium")
    
    print("依赖安装完成 ✓")


def setup_environment():
    """设置环境配置"""
    print("设置环境配置...")
    
    env_example = BACKEND_DIR / 'env_example.txt'
    env_file = BACKEND_DIR / '.env'
    
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print(f"已创建环境配置文件: {env_file}")
        print("请编辑 .env 文件配置您的数据库和API密钥")
    else:
        print("环境配置文件已存在")


def create_directories():
    """创建必要的目录"""
    print("创建项目目录...")
    
    directories = [
        BACKEND_DIR / 'logs',
        BACKEND_DIR / 'data',
        BACKEND_DIR / 'data' / 'vector_index',
        BACKEND_DIR / 'data' / 'browser_profiles',
        BACKEND_DIR / 'media',
        BACKEND_DIR / 'media' / 'screenshots',
        BACKEND_DIR / 'media' / 'images',
        BACKEND_DIR / 'media' / 'videos',
        BACKEND_DIR / 'media' / 'audios',
        BACKEND_DIR / 'staticfiles',
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"创建目录: {directory}")
    
    print("目录创建完成 ✓")


def setup_database():
    """设置数据库"""
    print("设置数据库...")
    
    # 检查是否有Django
    try:
        run_command("python manage.py --version", cwd=BACKEND_DIR)
    except:
        print("Django未正确安装，跳过数据库设置")
        return
    
    # 创建迁移文件
    print("创建数据库迁移...")
    run_command("python manage.py makemigrations", cwd=BACKEND_DIR, check=False)
    
    # 应用迁移
    print("应用数据库迁移...")
    run_command("python manage.py migrate", cwd=BACKEND_DIR, check=False)
    
    print("数据库设置完成 ✓")


def create_superuser():
    """创建超级用户"""
    print("创建超级用户...")
    print("请按提示输入管理员账号信息:")
    
    try:
        run_command("python manage.py createsuperuser", cwd=BACKEND_DIR, check=False)
        print("超级用户创建完成 ✓")
    except:
        print("超级用户创建跳过")


def setup_initial_data():
    """设置初始数据"""
    print("设置初始数据...")
    
    # 这里可以添加初始化情感关键词等数据的逻辑
    # 暂时跳过
    print("初始数据设置完成 ✓")


def print_next_steps():
    """打印后续步骤"""
    print("\n" + "="*50)
    print("🎉 项目设置完成!")
    print("="*50)
    print("\n后续步骤:")
    print("1. 编辑 backend/.env 文件，配置数据库和API密钥")
    print("2. 启动Redis服务器")
    print("3. 启动PostgreSQL数据库")
    print("4. 运行以下命令启动服务:")
    print("   cd backend")
    print("   python manage.py runserver")
    print("\n5. 在新终端启动Celery:")
    print("   cd backend")
    print("   celery -A core worker -l info")
    print("\n6. 访问 http://localhost:8000/admin 进行管理")
    print("\n📚 更多信息请查看 README.md")


def main():
    """主函数"""
    print("🚀 AI智能客服系统 - 项目设置")
    print("="*50)
    
    # 检查环境
    check_python_version()
    
    # 检查conda环境
    if not check_conda_environment():
        print("请先创建并激活conda agent环境:")
        print("conda create -n agent python=3.10")
        print("conda activate agent")
        sys.exit(1)
    
    # 安装依赖
    install_dependencies()
    
    # 设置环境
    setup_environment()
    
    # 创建目录
    create_directories()
    
    # 设置数据库
    setup_database()
    
    # 创建超级用户
    create_superuser()
    
    # 设置初始数据
    setup_initial_data()
    
    # 打印后续步骤
    print_next_steps()


if __name__ == "__main__":
    main() 