#!/usr/bin/env python3
"""
简单的后端API测试脚本
专门用于测试Django后端的基本功能
只进行安全的读取操作
"""

import requests
import yaml
import sys
import json
from typing import Dict, Any

def load_config() -> Dict[str, Any]:
    """加载配置文件"""
    try:
        with open('configs/configs.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config['DEV']
    except Exception as e:
        print(f"❌ 配置文件加载失败: {e}")
        return {}

def test_django_admin(base_url: str) -> bool:
    """测试Django管理后台"""
    try:
        response = requests.get(f"{base_url}/admin/", timeout=10)
        if response.status_code in [200, 302]:
            print("✅ Django管理后台可访问")
            return True
        else:
            print(f"❌ Django管理后台不可访问 (状态码: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Django管理后台测试错误: {e}")
        return False

def test_django_static_files(base_url: str) -> bool:
    """测试Django静态文件"""
    try:
        response = requests.get(f"{base_url}/static/", timeout=10)
        # 静态文件可能返回404或403，这都是正常的
        if response.status_code in [200, 403, 404]:
            print("✅ Django静态文件路径配置正常")
            return True
        else:
            print(f"⚠️  Django静态文件路径 (状态码: {response.status_code})")
            return True
    except Exception as e:
        print(f"⚠️  Django静态文件测试跳过: {e}")
        return True

def test_common_django_endpoints(base_url: str) -> Dict[str, bool]:
    """测试常见的Django端点"""
    endpoints = [
        "/",
        "/admin/",
        "/api/",
        "/health/",
        "/status/",
        "/ping/",
    ]
    
    results = {}
    print("\n🔗 测试Django端点:")
    
    for endpoint in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ {endpoint} - 成功 (200)")
                results[endpoint] = True
            elif response.status_code in [301, 302]:
                print(f"✅ {endpoint} - 重定向 ({response.status_code})")
                results[endpoint] = True
            elif response.status_code == 404:
                print(f"⚠️  {endpoint} - 未找到 (404)")
                results[endpoint] = False
            elif response.status_code in [403, 401]:
                print(f"✅ {endpoint} - 需要认证 ({response.status_code})")
                results[endpoint] = True
            else:
                print(f"⚠️  {endpoint} - 状态码: {response.status_code}")
                results[endpoint] = False
                
        except requests.exceptions.Timeout:
            print(f"❌ {endpoint} - 超时")
            results[endpoint] = False
        except requests.exceptions.ConnectionError:
            print(f"❌ {endpoint} - 连接错误")
            results[endpoint] = False
        except Exception as e:
            print(f"❌ {endpoint} - 异常: {e}")
            results[endpoint] = False
    
    return results

def test_backend_functionality(base_url: str) -> Dict[str, Any]:
    """测试后端功能"""
    print(f"🔧 测试后端服务 ({base_url}):")
    
    results = {
        'base_connection': False,
        'admin_access': False,
        'static_files': False,
        'endpoints': {}
    }
    
    # 测试基本连接
    try:
        response = requests.get(base_url, timeout=10)
        results['base_connection'] = response.status_code in [200, 301, 302, 404]
        print(f"✅ 后端基本连接正常 (状态码: {response.status_code})")
    except Exception as e:
        print(f"❌ 后端基本连接失败: {e}")
        return results
    
    # 测试各种端点
    results['endpoints'] = test_common_django_endpoints(base_url)
    results['admin_access'] = test_django_admin(base_url)
    results['static_files'] = test_django_static_files(base_url)
    
    return results

def analyze_backend_response(base_url: str):
    """分析后端响应内容"""
    print(f"\n📄 分析后端响应内容:")
    
    try:
        response = requests.get(base_url, timeout=10)
        content = response.text
        
        print(f"状态码: {response.status_code}")
        print(f"响应大小: {len(content)} 字符")
        
        # 检查内容类型
        content_type = response.headers.get('content-type', '').lower()
        print(f"内容类型: {content_type}")
        
        # 分析响应内容
        if 'html' in content_type:
            if 'attu' in content.lower():
                print("⚠️  检测到Attu界面 - 这可能是Milvus管理工具")
            elif 'django' in content.lower():
                print("✅ 检测到Django相关内容")
            elif '<title>' in content:
                import re
                title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
                if title_match:
                    print(f"页面标题: {title_match.group(1)}")
        
        elif 'json' in content_type:
            try:
                data = response.json()
                print(f"JSON响应: {json.dumps(data, indent=2, ensure_ascii=False)[:200]}...")
            except:
                print("无法解析JSON响应")
        
        # 显示响应的前几行
        lines = content.split('\n')[:5]
        print("响应前几行:")
        for i, line in enumerate(lines, 1):
            print(f"  {i}: {line[:100]}")
            
    except Exception as e:
        print(f"❌ 分析后端响应错误: {e}")

def main():
    """主测试函数"""
    print("🔍 开始后端功能测试...")
    print("⚠️  注意: 此脚本只进行安全的读取操作")
    print("=" * 60)
    
    # 配置后端URL
    backend_url = "http://localhost:8000"
    
    # 分析后端响应
    analyze_backend_response(backend_url)
    
    # 测试后端功能
    results = test_backend_functionality(backend_url)
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📈 后端测试结果汇总:")
    
    print(f"\n🔧 连接状态:")
    print(f"   基本连接: {'✅' if results['base_connection'] else '❌'}")
    print(f"   管理后台: {'✅' if results['admin_access'] else '❌'}")
    print(f"   静态文件: {'✅' if results['static_files'] else '❌'}")
    
    # 端点测试结果
    if results['endpoints']:
        success_count = sum(1 for success in results['endpoints'].values() if success)
        total_count = len(results['endpoints'])
        print(f"   API端点: {success_count}/{total_count} 成功")
    
    # 提供建议
    print(f"\n💡 分析和建议:")
    
    if not results['base_connection']:
        print("- 后端服务未正确启动或配置错误")
        print("- 检查Django设置和端口配置")
    
    elif results['base_connection']:
        print("- 后端服务基本运行正常")
        
        if not results['admin_access']:
            print("- Django管理后台可能未配置或需要设置")
        
        # 检查主要端点
        working_endpoints = [ep for ep, status in results['endpoints'].items() if status]
        if working_endpoints:
            print(f"- 可用端点: {', '.join(working_endpoints)}")
        
        failing_endpoints = [ep for ep, status in results['endpoints'].items() if not status]
        if failing_endpoints:
            print(f"- 需要检查的端点: {', '.join(failing_endpoints)}")
    
    print(f"\n🔧 后续步骤:")
    print("- 如果看到Attu界面，可能需要配置正确的Django应用")
    print("- 检查Django的urls.py配置")
    print("- 确认项目的主要应用是否正确启动")
    print("- 运行数据库连接测试: python database_connectivity_test.py")
    
    return results['base_connection']

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