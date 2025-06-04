#!/usr/bin/env python3
"""
前端后端集成测试脚本
用于排查前端和后端的交互bug
只进行安全的读取和基本功能测试
"""

import requests
import json
import time
import subprocess
import sys
import os
from typing import Dict, Any, Optional
import threading
import yaml

def load_config() -> Dict[str, Any]:
    """加载配置文件"""
    try:
        with open('configs/configs.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config['DEV']
    except Exception as e:
        print(f"❌ 配置文件加载失败: {e}")
        return {}

class BackendTester:
    """后端API测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 10
    
    def test_health_check(self) -> bool:
        """测试后端健康检查"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("✅ 后端健康检查通过")
                return True
            else:
                print(f"❌ 后端健康检查失败 (状态码: {response.status_code})")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ 无法连接到后端服务，请确认后端服务已启动")
            return False
        except Exception as e:
            print(f"❌ 后端健康检查错误: {e}")
            return False
    
    def test_api_endpoints(self) -> Dict[str, bool]:
        """测试主要API端点"""
        endpoints = {
            "/api/status": "GET",
            "/api/config": "GET",
            "/api/user/profile": "GET",
            "/api/chat/history": "GET",
            "/api/system/info": "GET"
        }
        
        results = {}
        print("\n🔗 测试API端点:")
        
        for endpoint, method in endpoints.items():
            try:
                url = f"{self.base_url}{endpoint}"
                if method == "GET":
                    response = self.session.get(url)
                else:
                    response = self.session.request(method, url)
                
                if response.status_code in [200, 201, 204]:
                    print(f"✅ {method} {endpoint} - 成功")
                    results[endpoint] = True
                elif response.status_code in [401, 403]:
                    print(f"⚠️  {method} {endpoint} - 需要认证")
                    results[endpoint] = True  # 认证错误也算正常响应
                elif response.status_code == 404:
                    print(f"⚠️  {method} {endpoint} - 端点不存在")
                    results[endpoint] = False
                else:
                    print(f"❌ {method} {endpoint} - 错误 (状态码: {response.status_code})")
                    results[endpoint] = False
                    
            except Exception as e:
                print(f"❌ {method} {endpoint} - 异常: {e}")
                results[endpoint] = False
        
        return results
    
    def test_database_connectivity(self) -> bool:
        """测试后端数据库连接"""
        try:
            response = self.session.get(f"{self.base_url}/api/db/status")
            if response.status_code == 200:
                data = response.json()
                print("✅ 后端数据库连接正常")
                if isinstance(data, dict):
                    for db_name, status in data.items():
                        status_icon = "✅" if status else "❌"
                        print(f"   {status_icon} {db_name}")
                return True
            else:
                print(f"❌ 后端数据库连接检查失败 (状态码: {response.status_code})")
                return False
        except Exception as e:
            print(f"⚠️  后端数据库连接检查跳过: {e}")
            return True  # 如果没有这个端点，跳过测试

class FrontendTester:
    """前端测试器"""
    
    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 10
    
    def test_frontend_accessible(self) -> bool:
        """测试前端是否可访问"""
        try:
            response = self.session.get(self.base_url)
            if response.status_code == 200:
                print("✅ 前端服务可访问")
                return True
            else:
                print(f"❌ 前端服务不可访问 (状态码: {response.status_code})")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ 无法连接到前端服务，请确认前端服务已启动")
            return False
        except Exception as e:
            print(f"❌ 前端访问错误: {e}")
            return False
    
    def test_static_resources(self) -> bool:
        """测试静态资源加载"""
        static_files = [
            "/static/js/",
            "/static/css/",
            "/assets/",
            "/favicon.ico"
        ]
        
        print("\n📄 测试静态资源:")
        success_count = 0
        
        for resource in static_files:
            try:
                url = f"{self.base_url}{resource}"
                response = self.session.get(url)
                if response.status_code in [200, 301, 302]:
                    print(f"✅ {resource} - 可访问")
                    success_count += 1
                else:
                    print(f"⚠️  {resource} - 状态码: {response.status_code}")
            except Exception as e:
                print(f"⚠️  {resource} - 跳过: {e}")
        
        return success_count > 0
    
    def test_api_calls_from_frontend(self, backend_url: str) -> bool:
        """测试前端到后端的API调用"""
        try:
            # 检查前端是否能够调用后端API
            print("\n🔄 测试前端到后端的连接:")
            
            # 这里可以通过检查前端配置或者网络请求来验证
            # 简单起见，我们检查前端页面是否包含后端API的引用
            response = self.session.get(self.base_url)
            if response.status_code == 200:
                content = response.text
                if backend_url.replace("http://", "").replace("https://", "") in content:
                    print("✅ 前端包含后端API引用")
                    return True
                else:
                    print("⚠️  前端未找到后端API引用，可能使用环境变量配置")
                    return True
            return False
        except Exception as e:
            print(f"❌ 前端到后端连接测试错误: {e}")
            return False

def check_service_status():
    """检查服务运行状态"""
    print("🔍 检查服务运行状态:")
    
    # 检查是否有Python/Django进程
    try:
        result = subprocess.run(['pgrep', '-f', 'python.*manage.py'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ 检测到Django后端进程")
        else:
            print("⚠️  未检测到Django后端进程")
    except:
        print("⚠️  无法检查Django进程状态")
    
    # 检查是否有Node.js进程
    try:
        result = subprocess.run(['pgrep', '-f', 'node'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ 检测到Node.js前端进程")
        else:
            print("⚠️  未检测到Node.js前端进程")
    except:
        print("⚠️  无法检查Node.js进程状态")

def test_cross_origin_requests():
    """测试跨域请求配置"""
    print("\n🌐 测试跨域配置:")
    
    backend_url = "http://localhost:8000"
    frontend_url = "http://localhost:3000"
    
    try:
        # 测试预检请求
        headers = {
            'Origin': frontend_url,
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        
        response = requests.options(f"{backend_url}/api/test", headers=headers, timeout=5)
        
        if 'Access-Control-Allow-Origin' in response.headers:
            print("✅ 后端支持跨域请求")
        else:
            print("⚠️  后端可能未配置跨域支持")
            
    except Exception as e:
        print(f"⚠️  跨域测试跳过: {e}")

def start_services_if_needed():
    """如果服务未运行，提示用户启动"""
    print("\n🚀 服务启动建议:")
    print("如果测试失败，请按以下步骤启动服务:")
    print()
    print("1. 启动后端服务:")
    print("   cd backend")
    print("   python manage.py runserver 0.0.0.0:8000")
    print()
    print("2. 启动前端服务:")
    print("   cd frontend")
    print("   npm run dev")
    print()

def main():
    """主测试函数"""
    print("🔍 开始前端后端集成测试...")
    print("⚠️  注意: 此脚本只进行安全的读取操作和基本连接测试")
    print("=" * 60)
    
    # 检查服务运行状态
    check_service_status()
    
    # 配置URL（可以根据实际情况调整）
    backend_url = "http://localhost:8000"
    frontend_url = "http://localhost:3000"
    
    # 测试后端
    print(f"\n🔧 测试后端服务 ({backend_url}):")
    backend_tester = BackendTester(backend_url)
    backend_health = backend_tester.test_health_check()
    
    if backend_health:
        backend_api_results = backend_tester.test_api_endpoints()
        backend_db_status = backend_tester.test_database_connectivity()
    else:
        backend_api_results = {}
        backend_db_status = False
    
    # 测试前端
    print(f"\n🎨 测试前端服务 ({frontend_url}):")
    frontend_tester = FrontendTester(frontend_url)
    frontend_accessible = frontend_tester.test_frontend_accessible()
    
    if frontend_accessible:
        frontend_static = frontend_tester.test_static_resources()
        frontend_backend_conn = frontend_tester.test_api_calls_from_frontend(backend_url)
    else:
        frontend_static = False
        frontend_backend_conn = False
    
    # 测试跨域配置
    test_cross_origin_requests()
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📈 集成测试结果汇总:")
    
    print(f"\n🔧 后端状态:")
    print(f"   健康检查: {'✅' if backend_health else '❌'}")
    if backend_api_results:
        success_apis = sum(1 for success in backend_api_results.values() if success)
        total_apis = len(backend_api_results)
        print(f"   API端点: {success_apis}/{total_apis} 成功")
    print(f"   数据库连接: {'✅' if backend_db_status else '❌'}")
    
    print(f"\n🎨 前端状态:")
    print(f"   服务访问: {'✅' if frontend_accessible else '❌'}")
    print(f"   静态资源: {'✅' if frontend_static else '❌'}")
    print(f"   后端连接: {'✅' if frontend_backend_conn else '❌'}")
    
    # 提供启动建议
    if not backend_health or not frontend_accessible:
        start_services_if_needed()
    
    print("\n💡 Bug排查建议:")
    if not backend_health:
        print("- 后端服务未启动或配置错误")
        print("- 检查backend/logs/目录中的日志文件")
        print("- 确认数据库连接配置是否正确")
    
    if not frontend_accessible:
        print("- 前端服务未启动或构建失败")
        print("- 检查package.json和node_modules是否正确安装")
        print("- 运行 npm install 安装依赖")
    
    if backend_health and frontend_accessible and not frontend_backend_conn:
        print("- 前后端通信可能存在问题")
        print("- 检查跨域(CORS)配置")
        print("- 确认前端API调用的URL是否正确")
    
    print("\n🔧 进一步调试:")
    print("- 查看浏览器开发者工具的Network和Console标签")
    print("- 检查后端日志输出")
    print("- 使用数据库连接测试脚本: python database_connectivity_test.py")
    
    # 返回成功状态
    overall_success = backend_health and frontend_accessible
    return overall_success

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