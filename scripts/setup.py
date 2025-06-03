#!/usr/bin/env python3
"""
SmartTalk AI 项目设置脚本
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, cwd=None):
    """运行命令"""
    print(f"执行命令: {command}")
    result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"命令执行失败: {result.stderr}")
        return False
    print(result.stdout)
    return True

def check_requirements():
    """检查系统要求"""
    print("检查系统要求...")
    
    # 检查Python版本
    if sys.version_info < (3, 9):
        print("错误: 需要Python 3.9或更高版本")
        return False
    
    # 检查必要的命令
    required_commands = ['pip', 'npm', 'redis-server', 'psql']
    for cmd in required_commands:
        if not shutil.which(cmd):
            print(f"警告: 未找到命令 {cmd}")
    
    return True

def setup_backend():
    """设置后端"""
    print("设置Django后端...")
    
    backend_dir = Path(__file__).parent.parent / 'backend'
    
    # 创建虚拟环境
    if not run_command("python -m venv venv", cwd=backend_dir):
        return False
    
    # 激活虚拟环境并安装依赖
    if os.name == 'nt':  # Windows
        pip_path = backend_dir / 'venv' / 'Scripts' / 'pip'
        python_path = backend_dir / 'venv' / 'Scripts' / 'python'
    else:  # Unix/Linux
        pip_path = backend_dir / 'venv' / 'bin' / 'pip'
        python_path = backend_dir / 'venv' / 'bin' / 'python'
    
    if not run_command(f"{pip_path} install -r requirements.txt", cwd=backend_dir):
        return False
    
    # 创建环境变量文件
    env_file = backend_dir / '.env'
    env_example = backend_dir / 'env_example.txt'
    
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print("已创建 .env 文件，请根据需要修改配置")
    
    # 创建日志目录
    logs_dir = backend_dir / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    # 数据库迁移
    if not run_command(f"{python_path} manage.py makemigrations", cwd=backend_dir):
        return False
    
    if not run_command(f"{python_path} manage.py migrate", cwd=backend_dir):
        return False
    
    # 创建超级用户
    print("请创建超级用户账号:")
    run_command(f"{python_path} manage.py createsuperuser", cwd=backend_dir)
    
    return True

def setup_frontend():
    """设置前端"""
    print("设置React前端...")
    
    frontend_dir = Path(__file__).parent.parent / 'frontend'
    
    if not frontend_dir.exists():
        # 创建React应用
        if not run_command("npx create-react-app frontend --template typescript"):
            return False
    
    # 安装额外依赖
    additional_packages = [
        "@mui/material",
        "@emotion/react",
        "@emotion/styled",
        "axios",
        "react-router-dom",
        "@types/react-router-dom",
        "recharts",
        "socket.io-client"
    ]
    
    for package in additional_packages:
        if not run_command(f"npm install {package}", cwd=frontend_dir):
            print(f"警告: 安装 {package} 失败")
    
    return True

def setup_database():
    """设置数据库"""
    print("设置PostgreSQL数据库...")
    
    # 这里可以添加自动创建数据库的逻辑
    print("请确保PostgreSQL已安装并运行")
    print("请手动创建数据库: CREATE DATABASE smarttalk_ai;")
    
    return True

def setup_redis():
    """设置Redis"""
    print("设置Redis...")
    
    print("请确保Redis已安装并运行")
    print("默认配置: redis://localhost:6379")
    
    return True

def create_startup_scripts():
    """创建启动脚本"""
    print("创建启动脚本...")
    
    scripts_dir = Path(__file__).parent
    
    # 创建开发环境启动脚本
    if os.name == 'nt':  # Windows
        startup_script = scripts_dir / 'start_dev.bat'
        with open(startup_script, 'w', encoding='utf-8') as f:
            f.write("""@echo off
echo 启动SmartTalk AI开发环境...

echo 启动Redis...
start "Redis" redis-server

echo 启动Django后端...
cd /d "%~dp0../backend"
call venv\\Scripts\\activate
start "Django" python manage.py runserver

echo 启动Celery Worker...
start "Celery" celery -A core worker --loglevel=info

echo 启动前端...
cd /d "%~dp0../frontend"
start "React" npm start

echo 所有服务已启动
pause
""")
    else:  # Unix/Linux
        startup_script = scripts_dir / 'start_dev.sh'
        with open(startup_script, 'w') as f:
            f.write("""#!/bin/bash
echo "启动SmartTalk AI开发环境..."

# 启动Redis
echo "启动Redis..."
redis-server &

# 启动Django后端
echo "启动Django后端..."
cd "$(dirname "$0")/../backend"
source venv/bin/activate
python manage.py runserver &

# 启动Celery Worker
echo "启动Celery Worker..."
celery -A core worker --loglevel=info &

# 启动前端
echo "启动前端..."
cd "$(dirname "$0")/../frontend"
npm start &

echo "所有服务已启动"
wait
""")
        os.chmod(startup_script, 0o755)
    
    print(f"启动脚本已创建: {startup_script}")
    return True

def main():
    """主函数"""
    print("=== SmartTalk AI 项目设置 ===")
    
    if not check_requirements():
        print("系统要求检查失败")
        return False
    
    steps = [
        ("设置数据库", setup_database),
        ("设置Redis", setup_redis),
        ("设置后端", setup_backend),
        ("设置前端", setup_frontend),
        ("创建启动脚本", create_startup_scripts),
    ]
    
    for step_name, step_func in steps:
        print(f"\n--- {step_name} ---")
        if not step_func():
            print(f"{step_name} 失败")
            return False
        print(f"{step_name} 完成")
    
    print("\n=== 设置完成 ===")
    print("请按照以下步骤完成配置:")
    print("1. 修改 backend/.env 文件中的配置")
    print("2. 确保PostgreSQL和Redis服务正在运行")
    print("3. 配置AI模型API密钥")
    print("4. 运行启动脚本开始开发")
    
    return True

if __name__ == "__main__":
    main() 