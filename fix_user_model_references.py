#!/usr/bin/env python3
"""
修复User模型引用脚本
将所有 'auth.User' 引用替换为 settings.AUTH_USER_MODEL
"""

import os
import re
from pathlib import Path

def fix_user_references():
    """修复用户模型引用"""
    print("🔧 开始修复User模型引用...")
    
    # 需要修复的模式
    patterns = [
        (r"models\.ForeignKey\(['\"]auth\.User['\"]", "models.ForeignKey(settings.AUTH_USER_MODEL"),
        (r"models\.OneToOneField\(['\"]auth\.User['\"]", "models.OneToOneField(settings.AUTH_USER_MODEL"),
        (r"models\.ManyToManyField\(['\"]auth\.User['\"]", "models.ManyToManyField(settings.AUTH_USER_MODEL"),
        (r"ForeignKey\(['\"]auth\.User['\"]", "ForeignKey(settings.AUTH_USER_MODEL"),
        (r"OneToOneField\(['\"]auth\.User['\"]", "OneToOneField(settings.AUTH_USER_MODEL"),
        (r"ManyToManyField\(['\"]auth\.User['\"]", "ManyToManyField(settings.AUTH_USER_MODEL"),
    ]
    
    # 遍历apps目录下的所有Python文件
    apps_dir = Path('apps')
    if not apps_dir.exists():
        print("❌ apps目录不存在")
        return
    
    modified_files = []
    for py_file in apps_dir.rglob('*.py'):
        if 'migrations' in str(py_file):
            continue  # 跳过迁移文件
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            needs_settings_import = False
            
            # 应用所有模式替换
            for pattern, replacement in patterns:
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    needs_settings_import = True
            
            # 如果需要settings导入，添加导入语句
            if needs_settings_import and 'from django.conf import settings' not in content:
                # 在Django imports之后添加settings导入
                django_import_pattern = r'(from django\.db import models.*?\n)'
                if re.search(django_import_pattern, content):
                    content = re.sub(django_import_pattern, r'\1from django.conf import settings\n', content)
                else:
                    # 如果没有找到标准的Django导入，在文件开头添加
                    lines = content.split('\n')
                    insert_index = 0
                    for i, line in enumerate(lines):
                        if line.startswith('from django') or line.startswith('import django'):
                            insert_index = i + 1
                    lines.insert(insert_index, 'from django.conf import settings')
                    content = '\n'.join(lines)
            
            # 如果内容有变化，写回文件
            if content != original_content:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                modified_files.append(str(py_file))
                print(f"✅ 修复了: {py_file}")
        
        except Exception as e:
            print(f"❌ 处理文件 {py_file} 时出错: {e}")
    
    print(f"\n🎉 修复完成！共修复了 {len(modified_files)} 个文件")
    if modified_files:
        print("修复的文件列表:")
        for file in modified_files:
            print(f"  - {file}")

if __name__ == "__main__":
    fix_user_references() 