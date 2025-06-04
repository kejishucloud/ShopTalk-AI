#!/usr/bin/env python3
"""
Django调试测试脚本
检查Django后端的具体配置和运行状态
"""

import requests
import sys
import json
from typing import Dict, Any

def test_django_server(base_url: str = "http://localhost:8080"):
    """测试Django服务器"""
    print(f"🔧 测试Django服务器 ({base_url}):")
    
    # 测试根路径
    try:
        response = requests.get(base_url, timeout=10)
        print(f"根路径 /: 状态码 {response.status_code}")
        if response.headers.get('content-type'):
            print(f"内容类型: {response.headers['content-type']}")
        
        # 如果是JSON响应，显示内容
        if 'json' in response.headers.get('content-type', ''):
            try:
                data = response.json()
                print(f"响应内容: {json.dumps(data, indent=2, ensure_ascii=False)}")
            except:
                print(f"响应内容: {response.text[:200]}")
        else:
            print(f"响应内容: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ 根路径测试失败: {e}")
        return False
    
    # 测试Django特定端点
    django_endpoints = [
        '/admin/',
        '/api/',
        '/api/v1/',
        '/api/docs/',
        '/api/schema/',
        '/api/v1/users/',
        '/api/v1/tags/',
        '/api/v1/prompts/',
    ]
    
    print(f"\n🔗 测试Django端点:")
    working_endpoints = []
    
    for endpoint in django_endpoints:
        try:
            url = f"{base_url}{endpoint}"
            response = requests.get(url, timeout=5)
            
            status = response.status_code
            content_type = response.headers.get('content-type', '')
            
            if status == 200:
                print(f"✅ {endpoint} - 成功 (200)")
                working_endpoints.append(endpoint)
            elif status in [301, 302]:
                print(f"✅ {endpoint} - 重定向 ({status})")
                working_endpoints.append(endpoint)
            elif status == 404:
                print(f"⚠️  {endpoint} - 未找到 (404)")
                # 显示404响应内容
                if 'json' in content_type:
                    try:
                        data = response.json()
                        print(f"     响应: {data}")
                    except:
                        pass
            elif status in [401, 403]:
                print(f"✅ {endpoint} - 需要认证 ({status})")
                working_endpoints.append(endpoint)
            elif status == 500:
                print(f"❌ {endpoint} - 服务器错误 (500)")
                print(f"     可能的配置问题")
            else:
                print(f"⚠️  {endpoint} - 状态码: {status}")
                
        except Exception as e:
            print(f"❌ {endpoint} - 错误: {e}")
    
    return len(working_endpoints) > 0

def check_django_configuration():
    """检查Django配置"""
    print(f"\n⚙️  检查Django配置:")
    
    # 检查Django进程
    import subprocess
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        django_processes = [line for line in result.stdout.split('\n') 
                          if 'manage.py' in line and 'runserver' in line]
        
        if django_processes:
            print("✅ Django进程正在运行:")
            for process in django_processes:
                # 提取端口信息
                parts = process.split()
                for i, part in enumerate(parts):
                    if 'runserver' in part and i + 1 < len(parts):
                        print(f"   进程: {parts[1]} 端口: {parts[i+1]}")
                        break
        else:
            print("❌ 未找到Django进程")
            
    except Exception as e:
        print(f"❌ 检查Django进程失败: {e}")
    
    # 检查端口占用
    try:
        result = subprocess.run(['netstat', '-tlnp'], capture_output=True, text=True)
        python_ports = [line for line in result.stdout.split('\n') 
                       if 'python' in line and 'LISTEN' in line]
        
        if python_ports:
            print("✅ Python进程监听的端口:")
            for line in python_ports:
                parts = line.split()
                if len(parts) >= 4:
                    local_address = parts[3]
                    if ':' in local_address:
                        port = local_address.split(':')[-1]
                        print(f"   端口: {port}")
        else:
            print("⚠️  未找到Python进程监听的端口")
            
    except Exception as e:
        print(f"❌ 检查端口占用失败: {e}")

def test_django_apps():
    """测试Django应用"""
    print(f"\n📱 测试Django应用端点:")
    
    base_url = "http://localhost:8080"
    app_endpoints = [
        '/api/v1/users/',
        '/api/v1/tags/',
        '/api/v1/prompts/',
        '/api/v1/agents/',
        '/api/v1/knowledge/',
        '/api/v1/chatbot/',
        '/api/v1/applications/',
        '/api/v1/keywords/',
        '/api/v1/history/',
        '/api/v1/ai-models/',
        '/api/v1/system-config/',
    ]
    
    working_apps = []
    
    for endpoint in app_endpoints:
        try:
            url = f"{base_url}{endpoint}"
            response = requests.get(url, timeout=5)
            
            app_name = endpoint.split('/')[3]  # 提取应用名
            
            if response.status_code == 200:
                print(f"✅ {app_name} - 工作正常")
                working_apps.append(app_name)
            elif response.status_code in [401, 403]:
                print(f"✅ {app_name} - 需要认证（正常）")
                working_apps.append(app_name)
            elif response.status_code == 404:
                print(f"❌ {app_name} - 应用未配置或URL错误")
            elif response.status_code == 500:
                print(f"❌ {app_name} - 服务器错误")
            else:
                print(f"⚠️  {app_name} - 状态码: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {app_name} - 错误: {e}")
    
    return working_apps

def main():
    """主测试函数"""
    print("🔍 开始Django调试测试...")
    print("=" * 60)
    
    # 检查Django配置
    check_django_configuration()
    
    # 测试Django服务器
    server_working = test_django_server()
    
    # 测试Django应用
    working_apps = test_django_apps()
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📈 Django调试结果汇总:")
    
    print(f"\n🔧 服务器状态:")
    print(f"   基本连接: {'✅' if server_working else '❌'}")
    
    print(f"\n📱 应用状态:")
    if working_apps:
        print(f"   工作正常的应用: {len(working_apps)}")
        print(f"   应用列表: {', '.join(working_apps)}")
    else:
        print(f"   ❌ 没有应用正常工作")
    
    # 提供诊断建议
    print(f"\n💡 诊断建议:")
    
    if not server_working:
        print("- Django服务器可能未正确启动")
        print("- 检查Django设置文件 (backend/core/settings.py)")
        print("- 查看Django日志输出")
    
    if not working_apps:
        print("- Django应用可能未正确配置")
        print("- 检查各应用的urls.py文件")
        print("- 确认应用已在INSTALLED_APPS中注册")
        print("- 运行数据库迁移: python manage.py migrate")
    
    print(f"\n🔧 建议的调试步骤:")
    print("1. 检查Django日志输出")
    print("2. 运行: cd backend && python manage.py check")
    print("3. 运行: cd backend && python manage.py showmigrations")
    print("4. 运行: cd backend && python manage.py collectstatic")
    print("5. 重启Django服务器")
    
    return server_working

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试过程中发生未知错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 