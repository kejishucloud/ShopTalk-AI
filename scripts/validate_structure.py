#!/usr/bin/env python3
"""
项目结构验证脚本
================

验证重新组织后的项目结构是否正确，检查：
1. 目录结构是否完整
2. 配置文件是否存在
3. 模块导入是否正常
4. 基础功能是否可用
"""

import os
import sys
import importlib
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class StructureValidator:
    """项目结构验证器"""
    
    def __init__(self):
        self.project_root = project_root
        self.errors = []
        self.warnings = []
        self.success_count = 0
        self.total_checks = 0
    
    def validate_directory_structure(self) -> bool:
        """验证目录结构"""
        print("🔍 验证目录结构...")
        
        required_dirs = [
            "frontend",
            "backend",
            "agents",
            "agents/core",
            "agents/skills", 
            "agents/memory",
            "agents/tools",
            "plugins",
            "plugins/platforms",
            "plugins/integrations",
            "plugins/tools",
            "knowledge",
            "knowledge/models",
            "knowledge/services",
            "knowledge/api",
            "knowledge/storage",
            "knowledge/search",
            "utils",
            "scripts",
            "docs",
            "tests",
            "configs"
        ]
        
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            self.total_checks += 1
            
            if full_path.exists() and full_path.is_dir():
                print(f"  ✅ {dir_path}")
                self.success_count += 1
            else:
                print(f"  ❌ {dir_path} - 目录不存在")
                self.errors.append(f"缺少目录: {dir_path}")
        
        return len(self.errors) == 0
    
    def validate_config_files(self) -> bool:
        """验证配置文件"""
        print("\n🔍 验证配置文件...")
        
        required_files = [
            "config.env",
            "requirements.txt",
            "README.md",
            "PROJECT_STRUCTURE.md",
            "BUG_FIXES.md"
        ]
        
        for file_path in required_files:
            full_path = self.project_root / file_path
            self.total_checks += 1
            
            if full_path.exists() and full_path.is_file():
                print(f"  ✅ {file_path}")
                self.success_count += 1
            else:
                print(f"  ❌ {file_path} - 文件不存在")
                self.errors.append(f"缺少文件: {file_path}")
        
        return len(self.errors) == 0
    
    def validate_module_imports(self) -> bool:
        """验证模块导入"""
        print("\n🔍 验证模块导入...")
        
        modules_to_test = [
            ("plugins", "插件系统"),
            ("plugins.platforms", "平台插件"),
            ("knowledge", "知识库模块"),
        ]
        
        for module_name, description in modules_to_test:
            self.total_checks += 1
            try:
                importlib.import_module(module_name)
                print(f"  ✅ {description} ({module_name})")
                self.success_count += 1
            except ImportError as e:
                print(f"  ❌ {description} ({module_name}) - 导入失败: {e}")
                self.errors.append(f"模块导入失败: {module_name} - {e}")
            except Exception as e:
                print(f"  ⚠️  {description} ({module_name}) - 导入警告: {e}")
                self.warnings.append(f"模块导入警告: {module_name} - {e}")
                self.success_count += 1
        
        return True
    
    def validate_config_loading(self) -> bool:
        """验证配置加载"""
        print("\n🔍 验证配置加载...")
        
        config_file = self.project_root / "config.env"
        self.total_checks += 1
        
        if not config_file.exists():
            print("  ❌ config.env 文件不存在")
            self.errors.append("config.env 文件不存在")
            return False
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 检查关键配置项
            required_configs = [
                "DEBUG=",
                "SECRET_KEY=",
                "DB_NAME=",
                "REDIS_URL=",
                "OPENAI_API_KEY=",
                "TAOBAO_ENABLED=",
                "VECTOR_DB_TYPE="
            ]
            
            missing_configs = []
            for config in required_configs:
                if config not in content:
                    missing_configs.append(config.rstrip('='))
            
            if missing_configs:
                print(f"  ⚠️  缺少配置项: {', '.join(missing_configs)}")
                self.warnings.extend([f"缺少配置项: {config}" for config in missing_configs])
            else:
                print("  ✅ 配置文件格式正确")
            
            self.success_count += 1
            return True
            
        except Exception as e:
            print(f"  ❌ 配置文件读取失败: {e}")
            self.errors.append(f"配置文件读取失败: {e}")
            return False
    
    def validate_backend_structure(self) -> bool:
        """验证后端结构"""
        print("\n🔍 验证后端结构...")
        
        backend_files = [
            "backend/manage.py",
            "backend/requirements.txt",
            "backend/core/settings.py",
            "backend/core/urls.py",
            "backend/apps/knowledge/models.py"
        ]
        
        for file_path in backend_files:
            full_path = self.project_root / file_path
            self.total_checks += 1
            
            if full_path.exists():
                print(f"  ✅ {file_path}")
                self.success_count += 1
            else:
                print(f"  ❌ {file_path} - 文件不存在")
                self.errors.append(f"后端文件缺失: {file_path}")
        
        return True
    
    def validate_frontend_structure(self) -> bool:
        """验证前端结构"""
        print("\n🔍 验证前端结构...")
        
        frontend_files = [
            "frontend/package.json",
            "frontend/vite.config.ts",
            "frontend/tsconfig.json",
            "frontend/src/main.ts",
            "frontend/src/App.vue"
        ]
        
        for file_path in frontend_files:
            full_path = self.project_root / file_path
            self.total_checks += 1
            
            if full_path.exists():
                print(f"  ✅ {file_path}")
                self.success_count += 1
            else:
                print(f"  ❌ {file_path} - 文件不存在")
                self.errors.append(f"前端文件缺失: {file_path}")
        
        return True
    
    def generate_report(self) -> Dict[str, Any]:
        """生成验证报告"""
        success_rate = (self.success_count / self.total_checks * 100) if self.total_checks > 0 else 0
        
        report = {
            "total_checks": self.total_checks,
            "success_count": self.success_count,
            "success_rate": success_rate,
            "errors": self.errors,
            "warnings": self.warnings,
            "status": "PASS" if len(self.errors) == 0 else "FAIL"
        }
        
        return report
    
    def run_validation(self) -> bool:
        """运行完整验证"""
        print("🚀 开始项目结构验证...\n")
        
        # 运行各项验证
        self.validate_directory_structure()
        self.validate_config_files()
        self.validate_module_imports()
        self.validate_config_loading()
        self.validate_backend_structure()
        self.validate_frontend_structure()
        
        # 生成报告
        report = self.generate_report()
        
        print(f"\n📊 验证报告")
        print("=" * 50)
        print(f"总检查项: {report['total_checks']}")
        print(f"成功项: {report['success_count']}")
        print(f"成功率: {report['success_rate']:.1f}%")
        print(f"状态: {report['status']}")
        
        if report['errors']:
            print(f"\n❌ 错误 ({len(report['errors'])}项):")
            for error in report['errors']:
                print(f"  - {error}")
        
        if report['warnings']:
            print(f"\n⚠️  警告 ({len(report['warnings'])}项):")
            for warning in report['warnings']:
                print(f"  - {warning}")
        
        if report['status'] == 'PASS':
            print("\n🎉 项目结构验证通过！")
            return True
        else:
            print("\n💥 项目结构验证失败，请修复上述问题。")
            return False

def main():
    """主函数"""
    validator = StructureValidator()
    success = validator.run_validation()
    
    # 返回适当的退出码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 