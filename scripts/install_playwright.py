#!/usr/bin/env python3
"""
Playwright安装脚本
"""
import os
import sys
import subprocess
import platform
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

def install_playwright():
    """安装Playwright"""
    print("=== 安装Playwright ===")
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("错误: Playwright需要Python 3.8或更高版本")
        return False
    
    # 安装Playwright包
    print("安装Playwright Python包...")
    if not run_command("pip install playwright"):
        return False
    
    # 安装浏览器
    print("安装Playwright浏览器...")
    if not run_command("playwright install"):
        return False
    
    # 安装系统依赖
    system = platform.system().lower()
    if system == "linux":
        print("安装Linux系统依赖...")
        if not run_command("playwright install-deps"):
            print("警告: 系统依赖安装失败，可能需要手动安装")
    
    print("Playwright安装完成!")
    return True

def install_chromium_only():
    """只安装Chromium浏览器"""
    print("=== 安装Chromium浏览器 ===")
    
    if not run_command("playwright install chromium"):
        return False
    
    print("Chromium浏览器安装完成!")
    return True

def verify_installation():
    """验证安装"""
    print("=== 验证Playwright安装 ===")
    
    try:
        import playwright
        print(f"Playwright版本: {playwright.__version__}")
        
        # 测试浏览器启动
        test_script = """
import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto('https://www.baidu.com')
        title = await page.title()
        print(f'页面标题: {title}')
        await browser.close()

asyncio.run(test())
"""
        
        print("测试浏览器启动...")
        result = subprocess.run([sys.executable, '-c', test_script], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✓ Playwright安装验证成功")
            print(result.stdout)
            return True
        else:
            print("✗ Playwright安装验证失败")
            print(result.stderr)
            return False
            
    except ImportError:
        print("✗ Playwright包导入失败")
        return False
    except subprocess.TimeoutExpired:
        print("✗ 测试超时")
        return False
    except Exception as e:
        print(f"✗ 验证过程出错: {str(e)}")
        return False

def setup_adspower():
    """设置Adspower指纹浏览器支持"""
    print("=== 设置Adspower支持 ===")
    
    print("Adspower指纹浏览器设置说明:")
    print("1. 下载并安装Adspower客户端")
    print("2. 启动Adspower并创建浏览器配置文件")
    print("3. 在系统配置中设置ads_id参数")
    print("4. 确保Adspower API服务运行在 http://local.adspower.net:50325")
    
    # 检查Adspower API是否可用
    try:
        import requests
        response = requests.get("http://local.adspower.net:50325/api/v1/user/list", timeout=5)
        if response.status_code == 200:
            print("✓ Adspower API服务正常")
        else:
            print("✗ Adspower API服务异常")
    except Exception as e:
        print(f"✗ 无法连接到Adspower API: {str(e)}")
        print("请确保Adspower客户端已启动")

def create_browser_config():
    """创建浏览器配置文件"""
    print("=== 创建浏览器配置文件 ===")
    
    config_dir = Path(__file__).parent.parent / 'config'
    config_dir.mkdir(exist_ok=True)
    
    browser_config = {
        "default": {
            "headless": False,
            "browser_type": "chromium",
            "viewport": {"width": 1920, "height": 1080},
            "locale": "zh-CN",
            "timezone": "Asia/Shanghai",
            "stealth": {"enabled": True},
            "browser_args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security"
            ]
        },
        "headless": {
            "headless": True,
            "browser_type": "chromium",
            "viewport": {"width": 1920, "height": 1080},
            "stealth": {"enabled": True}
        },
        "mobile": {
            "headless": False,
            "browser_type": "chromium",
            "viewport": {"width": 375, "height": 667},
            "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15",
            "locale": "zh-CN"
        }
    }
    
    config_file = config_dir / 'browser_config.json'
    
    import json
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(browser_config, f, indent=2, ensure_ascii=False)
    
    print(f"浏览器配置文件已创建: {config_file}")

def main():
    """主函数"""
    print("SmartTalk AI - Playwright安装工具")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "install":
            success = install_playwright()
        elif command == "chromium":
            success = install_chromium_only()
        elif command == "verify":
            success = verify_installation()
        elif command == "adspower":
            setup_adspower()
            success = True
        elif command == "config":
            create_browser_config()
            success = True
        else:
            print(f"未知命令: {command}")
            print("可用命令: install, chromium, verify, adspower, config")
            success = False
    else:
        # 完整安装流程
        print("开始完整安装流程...")
        
        steps = [
            ("安装Playwright", install_playwright),
            ("验证安装", verify_installation),
            ("创建配置", create_browser_config),
            ("设置Adspower", setup_adspower),
        ]
        
        success = True
        for step_name, step_func in steps:
            print(f"\n--- {step_name} ---")
            if not step_func():
                print(f"{step_name} 失败")
                success = False
                break
            print(f"{step_name} 完成")
    
    if success:
        print("\n✓ 安装完成!")
        print("\n使用说明:")
        print("1. 在平台适配器中使用Playwright进行自动化操作")
        print("2. 支持指纹浏览器(Adspower)和普通浏览器")
        print("3. 配置文件位于 config/browser_config.json")
        print("4. 查看文档了解更多使用方法")
    else:
        print("\n✗ 安装失败!")
        sys.exit(1)

if __name__ == "__main__":
    main() 