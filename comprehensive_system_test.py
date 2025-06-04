#!/usr/bin/env python3
"""
综合系统测试脚本
自动检测服务端口并测试前后端功能
只进行安全的读取操作
"""

import requests
import yaml
import sys
import json
import subprocess
import socket
from typing import Dict, Any, List, Tuple

def load_config() -> Dict[str, Any]:
    """加载配置文件"""
    try:
        with open('configs/configs.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config['DEV']
    except Exception as e:
        print(f"❌ 配置文件加载失败: {e}")
        return {}

def find_active_ports() -> List[int]:
    """查找活跃的HTTP端口"""
    common_ports = [3000, 8000, 8080, 8888, 5000, 3001, 4000]
    active_ports = []
    
    for port in common_ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            if result == 0:
                active_ports.append(port)
            sock.close()
        except:
            pass
    
    return active_ports

def identify_service_type(url: str) -> Tuple[str, Dict[str, Any]]:
    """识别服务类型"""
    try:
        response = requests.get(url, timeout=5)
        content = response.text.lower()
        headers = response.headers
        
        info = {
            'status_code': response.status_code,
            'content_type': headers.get('content-type', ''),
            'server': headers.get('server', ''),
            'content_length': len(content)
        }
        
        # 识别服务类型
        if 'attu' in content:
            return 'milvus-attu', info
        elif 'django' in content or 'csrftoken' in content:
            return 'django', info
        elif response.status_code == 200 and 'json' in info['content_type']:
            try:
                data = response.json()
                if 'detail' in data and data['detail'] == 'Not Found':
                    return 'django-api', info
            except:
                pass
            return 'api', info
        elif 'vue' in content or 'vite' in content or 'react' in content:
            return 'frontend', info
        elif response.status_code == 404:
            return 'unknown-404', info
        else:
            return 'unknown', info
            
    except requests.exceptions.ConnectionError:
        return 'connection-error', {}
    except Exception as e:
        return 'error', {'error': str(e)}

def test_django_endpoints(base_url: str) -> Dict[str, Any]:
    """测试Django端点"""
    endpoints = [
        '/',
        '/admin/',
        '/api/',
        '/api/health/',
        '/api/status/',
        '/health/',
        '/status/',
    ]
    
    results = {}
    print(f"\n🔗 测试Django端点 ({base_url}):")
    
    for endpoint in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            response = requests.get(url, timeout=5)
            
            status = response.status_code
            content_type = response.headers.get('content-type', '')
            
            if status == 200:
                print(f"✅ {endpoint} - 成功 (200)")
                results[endpoint] = {'status': 'success', 'code': status}
            elif status in [301, 302]:
                print(f"✅ {endpoint} - 重定向 ({status})")
                results[endpoint] = {'status': 'redirect', 'code': status}
            elif status == 404:
                print(f"⚠️  {endpoint} - 未找到 (404)")
                results[endpoint] = {'status': 'not_found', 'code': status}
            elif status in [401, 403]:
                print(f"✅ {endpoint} - 需要认证 ({status})")
                results[endpoint] = {'status': 'auth_required', 'code': status}
            else:
                print(f"⚠️  {endpoint} - 状态码: {status}")
                results[endpoint] = {'status': 'other', 'code': status}
                
            # 尝试解析JSON响应
            if 'json' in content_type:
                try:
                    data = response.json()
                    results[endpoint]['data'] = data
                except:
                    pass
                    
        except Exception as e:
            print(f"❌ {endpoint} - 错误: {e}")
            results[endpoint] = {'status': 'error', 'error': str(e)}
    
    return results

def test_frontend_service(base_url: str) -> Dict[str, Any]:
    """测试前端服务"""
    print(f"\n🎨 测试前端服务 ({base_url}):")
    
    results = {
        'accessible': False,
        'static_resources': False,
        'build_info': {}
    }
    
    try:
        # 测试主页
        response = requests.get(base_url, timeout=10)
        if response.status_code == 200:
            print("✅ 前端主页可访问")
            results['accessible'] = True
            
            content = response.text
            
            # 检查构建信息
            if 'vite' in content.lower():
                results['build_info']['bundler'] = 'vite'
            if 'vue' in content.lower():
                results['build_info']['framework'] = 'vue'
            if 'react' in content.lower():
                results['build_info']['framework'] = 'react'
                
        else:
            print(f"❌ 前端主页不可访问 (状态码: {response.status_code})")
            
        # 测试静态资源
        static_paths = ['/assets/', '/static/', '/js/', '/css/']
        for path in static_paths:
            try:
                resp = requests.get(f"{base_url}{path}", timeout=5)
                if resp.status_code in [200, 403]:  # 403也表示路径存在
                    results['static_resources'] = True
                    print(f"✅ 静态资源路径 {path} 存在")
                    break
            except:
                continue
                
    except Exception as e:
        print(f"❌ 前端测试错误: {e}")
        
    return results

def main():
    """主测试函数"""
    print("🔍 开始综合系统测试...")
    print("⚠️  注意: 此脚本只进行安全的读取操作")
    print("=" * 60)
    
    # 查找活跃端口
    print("🔍 扫描活跃端口:")
    active_ports = find_active_ports()
    if not active_ports:
        print("❌ 未发现活跃的HTTP端口")
        return False
    
    print(f"发现活跃端口: {active_ports}")
    
    # 识别各端口的服务类型
    services = {}
    print(f"\n🔍 识别服务类型:")
    
    for port in active_ports:
        url = f"http://localhost:{port}"
        service_type, info = identify_service_type(url)
        services[port] = {'type': service_type, 'info': info, 'url': url}
        
        print(f"端口 {port}: {service_type}")
        if info.get('status_code'):
            print(f"   状态码: {info['status_code']}")
        if info.get('content_type'):
            print(f"   内容类型: {info['content_type']}")
    
    # 测试Django后端
    django_ports = [port for port, data in services.items() 
                   if data['type'] in ['django', 'django-api']]
    
    if django_ports:
        print(f"\n🔧 测试Django后端:")
        for port in django_ports:
            url = services[port]['url']
            django_results = test_django_endpoints(url)
            services[port]['django_tests'] = django_results
    else:
        print(f"\n⚠️  未发现Django后端服务")
    
    # 测试前端服务
    frontend_ports = [port for port, data in services.items() 
                     if data['type'] == 'frontend']
    
    if frontend_ports:
        print(f"\n🎨 测试前端服务:")
        for port in frontend_ports:
            url = services[port]['url']
            frontend_results = test_frontend_service(url)
            services[port]['frontend_tests'] = frontend_results
    else:
        print(f"\n⚠️  未发现前端服务")
    
    # 测试数据库连接（简化版）
    print(f"\n📊 快速数据库连接测试:")
    config = load_config()
    if config:
        # 测试Redis
        try:
            import redis
            r = redis.Redis(
                host=config['redis']['host'],
                port=config['redis']['port'],
                password=config['redis']['password'],
                socket_timeout=3
            )
            if r.ping():
                print("✅ Redis连接正常")
            else:
                print("❌ Redis连接失败")
        except Exception as e:
            print(f"❌ Redis测试错误: {e}")
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📈 系统测试结果汇总:")
    
    print(f"\n🔍 发现的服务:")
    for port, data in services.items():
        service_type = data['type']
        status_icon = "✅" if data['info'].get('status_code') == 200 else "⚠️"
        print(f"   {status_icon} 端口 {port}: {service_type}")
    
    # Django后端状态
    if django_ports:
        print(f"\n🔧 Django后端状态:")
        for port in django_ports:
            print(f"   端口 {port}:")
            django_tests = services[port].get('django_tests', {})
            working_endpoints = [ep for ep, result in django_tests.items() 
                               if result.get('status') in ['success', 'redirect', 'auth_required']]
            print(f"     可用端点: {len(working_endpoints)}/{len(django_tests)}")
            if working_endpoints:
                print(f"     工作端点: {', '.join(working_endpoints)}")
    
    # 前端状态
    if frontend_ports:
        print(f"\n🎨 前端状态:")
        for port in frontend_ports:
            print(f"   端口 {port}:")
            frontend_tests = services[port].get('frontend_tests', {})
            if frontend_tests.get('accessible'):
                print(f"     ✅ 可访问")
            if frontend_tests.get('static_resources'):
                print(f"     ✅ 静态资源正常")
            build_info = frontend_tests.get('build_info', {})
            if build_info:
                print(f"     构建信息: {build_info}")
    
    # 提供建议
    print(f"\n💡 系统状态分析:")
    
    if not django_ports:
        print("- ⚠️  未检测到Django后端，可能需要启动")
        print("  建议: cd backend && python manage.py runserver 0.0.0.0:8001")
    
    if not frontend_ports:
        print("- ⚠️  未检测到前端服务，可能需要启动")
        print("  建议: cd frontend && npm run dev")
    
    if django_ports and frontend_ports:
        print("- ✅ 前后端服务都在运行")
        print("- 可以进行进一步的集成测试")
    
    # 端口冲突检查
    if 8000 in services and services[8000]['type'] == 'milvus-attu':
        print("- ⚠️  端口8000被Milvus Attu占用，Django可能需要使用其他端口")
    
    print(f"\n🔧 下一步建议:")
    print("- 运行完整数据库测试: python database_connectivity_test.py")
    print("- 检查具体的API端点功能")
    print("- 测试前后端数据交互")
    
    return len(django_ports) > 0 or len(frontend_ports) > 0

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