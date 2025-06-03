#!/usr/bin/env python3
"""
SmartTalk AI 系统启动脚本
一键启动所有必要的服务
"""

import os
import sys
import time
import signal
import subprocess
import threading
from pathlib import Path
from typing import List, Dict

class ServiceManager:
    """服务管理器"""
    
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.running = True
        
    def start_service(self, name: str, command: List[str], cwd: str = None, env: Dict = None) -> bool:
        """启动服务"""
        try:
            print(f"🚀 启动 {name}...")
            
            # 合并环境变量
            service_env = os.environ.copy()
            if env:
                service_env.update(env)
            
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=service_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.processes[name] = process
            
            # 启动日志监控线程
            threading.Thread(
                target=self._monitor_service,
                args=(name, process),
                daemon=True
            ).start()
            
            print(f"✅ {name} 启动成功 (PID: {process.pid})")
            return True
            
        except Exception as e:
            print(f"❌ {name} 启动失败: {e}")
            return False
    
    def _monitor_service(self, name: str, process: subprocess.Popen):
        """监控服务日志"""
        try:
            while self.running and process.poll() is None:
                output = process.stdout.readline()
                if output:
                    print(f"[{name}] {output.strip()}")
                
                error = process.stderr.readline()
                if error:
                    print(f"[{name}] ERROR: {error.strip()}")
                    
        except Exception as e:
            print(f"[{name}] 监控异常: {e}")
    
    def stop_all_services(self):
        """停止所有服务"""
        print("\n🛑 正在停止所有服务...")
        self.running = False
        
        for name, process in self.processes.items():
            try:
                print(f"停止 {name}...")
                process.terminate()
                
                # 等待进程结束
                try:
                    process.wait(timeout=10)
                    print(f"✅ {name} 已停止")
                except subprocess.TimeoutExpired:
                    print(f"⚠️ {name} 强制终止")
                    process.kill()
                    
            except Exception as e:
                print(f"❌ 停止 {name} 失败: {e}")
        
        print("🏁 所有服务已停止")
    
    def wait_for_services(self):
        """等待服务运行"""
        try:
            while self.running:
                time.sleep(1)
                
                # 检查进程状态
                for name, process in list(self.processes.items()):
                    if process.poll() is not None:
                        print(f"⚠️ {name} 意外退出 (退出码: {process.returncode})")
                        
        except KeyboardInterrupt:
            print("\n收到中断信号...")

def check_prerequisites() -> bool:
    """检查前置条件"""
    print("🔍 检查前置条件...")
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ Python版本过低，需要3.8+")
        return False
    
    # 检查项目结构
    required_files = [
        'backend/manage.py',
        'backend/core/settings.py',
        'requirements.txt'
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"❌ 缺少必要文件: {file_path}")
            return False
    
    # 检查环境变量
    required_env_vars = ['SECRET_KEY']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️ 缺少环境变量: {', '.join(missing_vars)}")
        print("请参考 backend/env_example.txt 配置环境变量")
        return False
    
    print("✅ 前置条件检查通过")
    return True

def load_environment():
    """加载环境变量"""
    env_file = Path('backend/.env')
    if env_file.exists():
        print("📄 加载环境变量文件...")
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

def setup_database():
    """设置数据库"""
    print("🗄️ 设置数据库...")
    
    try:
        # 运行数据库迁移
        result = subprocess.run(
            [sys.executable, 'manage.py', 'migrate'],
            cwd='backend',
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ 数据库迁移完成")
            return True
        else:
            print(f"❌ 数据库迁移失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 数据库设置失败: {e}")
        return False

def collect_static_files():
    """收集静态文件"""
    print("📁 收集静态文件...")
    
    try:
        result = subprocess.run(
            [sys.executable, 'manage.py', 'collectstatic', '--noinput'],
            cwd='backend',
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ 静态文件收集完成")
            return True
        else:
            print(f"⚠️ 静态文件收集警告: {result.stderr}")
            return True  # 非关键错误
            
    except Exception as e:
        print(f"⚠️ 静态文件收集失败: {e}")
        return True  # 非关键错误

def main():
    """主函数"""
    print("🎯 SmartTalk AI 系统启动器")
    print("=" * 50)
    
    # 检查前置条件
    if not check_prerequisites():
        print("❌ 前置条件检查失败，请先解决问题")
        return 1
    
    # 加载环境变量
    load_environment()
    
    # 设置数据库
    if not setup_database():
        print("❌ 数据库设置失败")
        return 1
    
    # 收集静态文件
    collect_static_files()
    
    # 创建服务管理器
    service_manager = ServiceManager()
    
    # 注册信号处理器
    def signal_handler(signum, frame):
        service_manager.stop_all_services()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("\n🚀 启动服务...")
    
    # 启动Redis（如果需要）
    redis_url = os.getenv('REDIS_URL')
    if redis_url and 'localhost' in redis_url:
        service_manager.start_service(
            "Redis",
            ["redis-server", "--port", "6379"]
        )
        time.sleep(2)
    
    # 启动Celery Worker
    service_manager.start_service(
        "Celery Worker",
        [sys.executable, "manage.py", "celery", "worker", "-l", "info"],
        cwd="backend"
    )
    
    # 启动Celery Beat（定时任务）
    service_manager.start_service(
        "Celery Beat",
        [sys.executable, "manage.py", "celery", "beat", "-l", "info"],
        cwd="backend"
    )
    
    # 启动Django开发服务器
    port = os.getenv('PORT', '8000')
    service_manager.start_service(
        "Django Server",
        [sys.executable, "manage.py", "runserver", f"0.0.0.0:{port}"],
        cwd="backend"
    )
    
    print("\n" + "=" * 50)
    print("🎉 SmartTalk AI 系统启动完成！")
    print(f"🌐 Web界面: http://localhost:{port}")
    print(f"🔧 管理后台: http://localhost:{port}/admin")
    print("📊 API文档: http://localhost:{port}/api/docs")
    print("\n按 Ctrl+C 停止所有服务")
    print("=" * 50)
    
    # 等待服务运行
    service_manager.wait_for_services()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 