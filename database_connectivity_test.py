#!/usr/bin/env python3
"""
数据库连接测试脚本
只进行安全的读取操作，不写入任何数据
用于测试前端和后端功能的完整性
"""

import yaml
import sys
import traceback
from typing import Dict, Any
import warnings
warnings.filterwarnings("ignore")

def load_config() -> Dict[str, Any]:
    """加载配置文件"""
    try:
        with open('configs/configs.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config['DEV']
    except Exception as e:
        print(f"❌ 配置文件加载失败: {e}")
        return {}

def test_redis_connection(config: Dict[str, Any]) -> bool:
    """测试Redis连接"""
    try:
        import redis
        redis_config = config['redis']
        
        r = redis.Redis(
            host=redis_config['host'],
            port=redis_config['port'],
            password=redis_config['password'],
            decode_responses=True,
            socket_timeout=5
        )
        
        # 只进行ping测试，不写入数据
        result = r.ping()
        if result:
            print("✅ Redis连接成功")
            # 获取一些基本信息（只读操作）
            info = r.info('server')
            print(f"   Redis版本: {info.get('redis_version', 'Unknown')}")
            print(f"   连接数: {info.get('connected_clients', 'Unknown')}")
            return True
        else:
            print("❌ Redis连接失败")
            return False
            
    except ImportError:
        print("⚠️  Redis库未安装，跳过测试")
        return False
    except Exception as e:
        print(f"❌ Redis连接错误: {e}")
        return False

def test_mysql_connection(config: Dict[str, Any]) -> bool:
    """测试MySQL连接"""
    try:
        import pymysql
        mysql_config = config['mysql']
        
        connection = pymysql.connect(
            host=mysql_config['host'],
            port=mysql_config['port'],
            user=mysql_config['username'],
            password=mysql_config['password'],
            connect_timeout=5
        )
        
        with connection.cursor() as cursor:
            # 只执行查询操作，不修改数据
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print("✅ MySQL连接成功")
            print(f"   MySQL版本: {version[0]}")
            
            # 查看数据库列表
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            print(f"   数据库数量: {len(databases)}")
            
        connection.close()
        return True
        
    except ImportError:
        print("⚠️  PyMySQL库未安装，跳过测试")
        return False
    except Exception as e:
        print(f"❌ MySQL连接错误: {e}")
        return False

def test_postgresql_connection(config: Dict[str, Any]) -> bool:
    """测试PostgreSQL连接"""
    try:
        import psycopg2
        pg_config = config['postgresql']
        
        connection = psycopg2.connect(
            host=pg_config['host'],
            port=pg_config['port'],
            user=pg_config['username'],
            password=pg_config['password'],
            connect_timeout=5
        )
        
        with connection.cursor() as cursor:
            # 只执行查询操作
            cursor.execute("SELECT version()")
            version = cursor.fetchone()
            print("✅ PostgreSQL连接成功")
            print(f"   PostgreSQL版本: {version[0][:50]}...")
            
            # 查看数据库列表
            cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false")
            databases = cursor.fetchall()
            print(f"   数据库数量: {len(databases)}")
            
        connection.close()
        return True
        
    except ImportError:
        print("⚠️  psycopg2库未安装，跳过测试")
        return False
    except Exception as e:
        print(f"❌ PostgreSQL连接错误: {e}")
        return False

def test_mongodb_connection(config: Dict[str, Any]) -> bool:
    """测试MongoDB连接"""
    try:
        from pymongo import MongoClient
        mongo_config = config['mongodb']
        
        client = MongoClient(
            host=mongo_config['host'],
            port=mongo_config['port'],
            username=mongo_config['username'],
            password=mongo_config['password'],
            serverSelectionTimeoutMS=5000
        )
        
        # 只进行读取操作
        server_info = client.server_info()
        print("✅ MongoDB连接成功")
        print(f"   MongoDB版本: {server_info['version']}")
        
        # 获取数据库列表
        db_list = client.list_database_names()
        print(f"   数据库数量: {len(db_list)}")
        
        client.close()
        return True
        
    except ImportError:
        print("⚠️  pymongo库未安装，跳过测试")
        return False
    except Exception as e:
        print(f"❌ MongoDB连接错误: {e}")
        return False

def test_neo4j_connection(config: Dict[str, Any]) -> bool:
    """测试Neo4j连接"""
    try:
        from neo4j import GraphDatabase
        neo4j_config = config['neo4j']
        
        driver = GraphDatabase.driver(
            f"bolt://{neo4j_config['host']}:{neo4j_config['port']}",
            auth=(neo4j_config['username'], neo4j_config['password'])
        )
        
        # 验证连接
        driver.verify_connectivity()
        
        with driver.session() as session:
            # 只执行查询操作
            result = session.run("CALL dbms.components()")
            components = list(result)
            print("✅ Neo4j连接成功")
            for component in components:
                print(f"   Neo4j版本: {component['versions'][0]}")
                break
                
        driver.close()
        return True
        
    except ImportError:
        print("⚠️  neo4j库未安装，跳过测试")
        return False
    except Exception as e:
        print(f"❌ Neo4j连接错误: {e}")
        return False

def test_milvus_connection(config: Dict[str, Any]) -> bool:
    """测试Milvus连接"""
    try:
        from pymilvus import connections, utility
        milvus_config = config['milvus']
        
        # 连接到Milvus
        connections.connect(
            alias="default",
            host=milvus_config['host'],
            port=milvus_config['port']
        )
        
        # 只进行查询操作
        version = utility.get_server_version()
        print("✅ Milvus连接成功")
        print(f"   Milvus版本: {version}")
        
        # 获取集合列表
        collections = utility.list_collections()
        print(f"   集合数量: {len(collections)}")
        
        connections.disconnect("default")
        return True
        
    except ImportError:
        print("⚠️  pymilvus库未安装，跳过测试")
        return False
    except Exception as e:
        print(f"❌ Milvus连接错误: {e}")
        return False

def test_llm_endpoint(config: Dict[str, Any]) -> bool:
    """测试LLM端点"""
    try:
        import requests
        llm_config = config['llm']
        
        # 测试健康检查端点
        health_url = f"{llm_config['base_url']}/health"
        try:
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                print("✅ LLM服务端点可访问")
                return True
        except:
            pass
            
        # 如果没有健康检查端点，尝试获取模型列表
        models_url = f"{llm_config['base_url']}/models"
        headers = {"Authorization": f"Bearer {llm_config['key']}"} if llm_config['key'] else {}
        
        response = requests.get(models_url, headers=headers, timeout=5)
        if response.status_code == 200:
            print("✅ LLM服务端点可访问")
            print(f"   配置模型: {llm_config['model_id']}")
            return True
        else:
            print(f"❌ LLM服务端点不可访问 (状态码: {response.status_code})")
            return False
            
    except ImportError:
        print("⚠️  requests库未安装，跳过测试")
        return False
    except Exception as e:
        print(f"❌ LLM端点测试错误: {e}")
        return False

def main():
    """主测试函数"""
    print("🔍 开始数据库连接测试...")
    print("⚠️  注意: 此脚本只进行安全的读取操作，不会写入任何数据")
    print("=" * 60)
    
    # 加载配置
    config = load_config()
    if not config:
        print("❌ 无法加载配置文件，测试终止")
        sys.exit(1)
    
    # 测试结果统计
    test_results = {}
    
    # 测试各个数据库
    print("\n📊 数据库连接测试:")
    test_results['redis'] = test_redis_connection(config)
    test_results['mysql'] = test_mysql_connection(config)
    test_results['postgresql'] = test_postgresql_connection(config)
    test_results['mongodb'] = test_mongodb_connection(config)
    test_results['neo4j'] = test_neo4j_connection(config)
    test_results['milvus'] = test_milvus_connection(config)
    
    print("\n🤖 服务端点测试:")
    test_results['llm'] = test_llm_endpoint(config)
    
    # 统计结果
    print("\n" + "=" * 60)
    print("📈 测试结果汇总:")
    
    successful_tests = []
    failed_tests = []
    skipped_tests = []
    
    for service, result in test_results.items():
        if result is True:
            successful_tests.append(service)
        elif result is False:
            failed_tests.append(service)
        else:
            skipped_tests.append(service)
    
    print(f"✅ 成功: {len(successful_tests)} 个服务")
    if successful_tests:
        print(f"   {', '.join(successful_tests)}")
    
    print(f"❌ 失败: {len(failed_tests)} 个服务")
    if failed_tests:
        print(f"   {', '.join(failed_tests)}")
    
    if skipped_tests:
        print(f"⚠️  跳过: {len(skipped_tests)} 个服务")
        print(f"   {', '.join(skipped_tests)}")
    
    print("\n💡 提示:")
    print("- 如果有服务连接失败，请检查网络连接和服务状态")
    print("- 如果有库未安装，可以运行: pip install [库名]")
    print("- 此测试脚本只进行读取操作，不会影响数据完整性")
    
    return len(failed_tests) == 0

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试过程中发生未知错误: {e}")
        traceback.print_exc()
        sys.exit(1) 