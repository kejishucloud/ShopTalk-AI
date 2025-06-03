#!/usr/bin/env python3
"""
SmartTalk AI 系统状态检查脚本
检查所有组件是否正确安装和配置
"""

import os
import sys
import subprocess
import importlib
from pathlib import Path
from typing import Dict, List, Tuple

def check_python_version() -> Tuple[bool, str]:
    """检查Python版本"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        return True, f"Python {version.major}.{version.minor}.{version.micro}"
    else:
        return False, f"Python版本过低: {version.major}.{version.minor}.{version.micro}, 需要3.8+"

def check_dependencies() -> Tuple[bool, List[str]]:
    """检查依赖包"""
    required_packages = [
        'django',
        'djangorestframework',
        'psycopg2-binary',
        'redis',
        'celery',
        'playwright',
        'selenium',
        'openai',
        'requests',
        'numpy',
        'pandas',
        'scikit-learn',
        'transformers',
        'torch'
    ]
    
    missing_packages = []
    installed_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package.replace('-', '_'))
            installed_packages.append(package)
        except ImportError:
            missing_packages.append(package)
    
    return len(missing_packages) == 0, missing_packages

def check_project_structure() -> Tuple[bool, List[str]]:
    """检查项目结构"""
    required_dirs = [
        'backend',
        'backend/apps',
        'backend/core',
        'ai_engine',
        'platform_adapters',
        'utils',
        'scripts',
        'docs',
        'configs'
    ]
    
    required_files = [
        'backend/manage.py',
        'backend/requirements.txt',
        'ai_engine/agent.py',
        'platform_adapters/base.py',
        'platform_adapters/taobao.py',
        'platform_adapters/xiaohongshu.py',
        'platform_adapters/pinduoduo.py',
        'platform_adapters/jingdong.py',
        'platform_adapters/douyin.py',
        'platform_adapters/adapter_factory.py',
        'utils/playwright_utils.py',
        'requirements.txt',
        'README.md'
    ]
    
    missing_items = []
    
    # 检查目录
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            missing_items.append(f"目录: {dir_path}")
    
    # 检查文件
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_items.append(f"文件: {file_path}")
    
    return len(missing_items) == 0, missing_items

def check_django_apps() -> Tuple[bool, List[str]]:
    """检查Django应用"""
    django_apps = [
        'backend/apps/users',
        'backend/apps/ai_models',
        'backend/apps/platforms',
        'backend/apps/knowledge',
        'backend/apps/conversations',
        'backend/apps/analytics'
    ]
    
    missing_apps = []
    
    for app_path in django_apps:
        if not os.path.exists(app_path):
            missing_apps.append(app_path)
        else:
            # 检查应用必要文件
            required_files = ['__init__.py', 'models.py', 'views.py', 'urls.py']
            for file_name in required_files:
                file_path = os.path.join(app_path, file_name)
                if not os.path.exists(file_path):
                    missing_apps.append(f"{app_path}/{file_name}")
    
    return len(missing_apps) == 0, missing_apps

def check_playwright_browsers() -> Tuple[bool, str]:
    """检查Playwright浏览器"""
    try:
        result = subprocess.run(
            ['playwright', 'install', '--dry-run'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return True, "Playwright浏览器已安装"
        else:
            return False, f"Playwright浏览器未安装: {result.stderr}"
    
    except subprocess.TimeoutExpired:
        return False, "检查Playwright浏览器超时"
    except FileNotFoundError:
        return False, "Playwright命令未找到"
    except Exception as e:
        return False, f"检查Playwright浏览器失败: {e}"

def check_environment_variables() -> Tuple[bool, List[str]]:
    """检查环境变量"""
    required_env_vars = [
        'SECRET_KEY',
        'DATABASE_URL',
        'REDIS_URL',
        'OPENAI_API_KEY'
    ]
    
    missing_vars = []
    
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    return len(missing_vars) == 0, missing_vars

def check_database_connection() -> Tuple[bool, str]:
    """检查数据库连接"""
    try:
        # 尝试导入Django设置
        sys.path.append('backend')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
        
        import django
        django.setup()
        
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            
        return True, "数据库连接正常"
    
    except Exception as e:
        return False, f"数据库连接失败: {e}"

def check_redis_connection() -> Tuple[bool, str]:
    """检查Redis连接"""
    try:
        import redis
        
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        r = redis.from_url(redis_url)
        r.ping()
        
        return True, "Redis连接正常"
    
    except Exception as e:
        return False, f"Redis连接失败: {e}"

def print_status(check_name: str, success: bool, message: str):
    """打印检查状态"""
    status = "✅" if success else "❌"
    print(f"{status} {check_name}: {message}")

def print_list_items(items: List[str], prefix: str = "  - "):
    """打印列表项"""
    for item in items:
        print(f"{prefix}{item}")

def main():
    """主函数"""
    print("🔍 SmartTalk AI 系统状态检查")
    print("=" * 50)
    
    all_checks_passed = True
    
    # 检查Python版本
    success, message = check_python_version()
    print_status("Python版本", success, message)
    if not success:
        all_checks_passed = False
    
    print()
    
    # 检查依赖包
    success, missing_packages = check_dependencies()
    if success:
        print_status("依赖包", True, "所有依赖包已安装")
    else:
        print_status("依赖包", False, f"缺少 {len(missing_packages)} 个依赖包")
        print("  缺少的包:")
        print_list_items(missing_packages)
        all_checks_passed = False
    
    print()
    
    # 检查项目结构
    success, missing_items = check_project_structure()
    if success:
        print_status("项目结构", True, "项目结构完整")
    else:
        print_status("项目结构", False, f"缺少 {len(missing_items)} 个项目文件/目录")
        print("  缺少的项目:")
        print_list_items(missing_items)
        all_checks_passed = False
    
    print()
    
    # 检查Django应用
    success, missing_apps = check_django_apps()
    if success:
        print_status("Django应用", True, "所有Django应用已创建")
    else:
        print_status("Django应用", False, f"缺少 {len(missing_apps)} 个Django应用文件")
        print("  缺少的应用文件:")
        print_list_items(missing_apps)
        all_checks_passed = False
    
    print()
    
    # 检查Playwright浏览器
    success, message = check_playwright_browsers()
    print_status("Playwright浏览器", success, message)
    if not success:
        all_checks_passed = False
    
    print()
    
    # 检查环境变量
    success, missing_vars = check_environment_variables()
    if success:
        print_status("环境变量", True, "所有必需的环境变量已设置")
    else:
        print_status("环境变量", False, f"缺少 {len(missing_vars)} 个环境变量")
        print("  缺少的环境变量:")
        print_list_items(missing_vars)
        print("  请参考 backend/env_example.txt 设置环境变量")
        all_checks_passed = False
    
    print()
    
    # 检查数据库连接（可选）
    if os.getenv('DATABASE_URL'):
        success, message = check_database_connection()
        print_status("数据库连接", success, message)
        if not success:
            all_checks_passed = False
    else:
        print_status("数据库连接", False, "未配置数据库URL，跳过检查")
    
    print()
    
    # 检查Redis连接（可选）
    if os.getenv('REDIS_URL'):
        success, message = check_redis_connection()
        print_status("Redis连接", success, message)
        if not success:
            all_checks_passed = False
    else:
        print_status("Redis连接", False, "未配置Redis URL，跳过检查")
    
    print()
    print("=" * 50)
    
    if all_checks_passed:
        print("🎉 所有检查通过！系统已准备就绪。")
        print("\n📋 下一步操作:")
        print("  1. 配置环境变量 (参考 backend/env_example.txt)")
        print("  2. 运行数据库迁移: cd backend && python manage.py migrate")
        print("  3. 创建超级用户: cd backend && python manage.py createsuperuser")
        print("  4. 启动开发服务器: cd backend && python manage.py runserver")
        print("  5. 安装Playwright浏览器: python scripts/install_playwright.py")
    else:
        print("⚠️  发现问题，请根据上述检查结果进行修复。")
        print("\n🔧 修复建议:")
        print("  1. 安装缺少的依赖: pip install -r requirements.txt")
        print("  2. 运行设置脚本: python scripts/setup.py")
        print("  3. 安装Playwright: python scripts/install_playwright.py")
    
    return 0 if all_checks_passed else 1

if __name__ == "__main__":
    sys.exit(main()) 