#!/usr/bin/env python3
"""
更新所有兼容性文件，使用通配符导入
"""
import os

def update_compat_file(filename, source_dir):
    """
    更新兼容性文件，使用通配符导入
    """
    compat_content = f"""from {source_dir} import *

__all__ = []
"""
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(compat_content)
    print(f"Updated {filename}")

def main():
    # 目录映射
    dir_mappings = {
        'data': 'data',
        'agents': 'agents',
        'db': 'db',
        'services': 'services',
        'utils': 'utils',
        'config': 'config',
        'strategies': 'strategies',
        'ui': 'ui',
    }
    
    for source_dir, target_prefix in dir_mappings.items():
        if os.path.isdir(source_dir):
            files = [f for f in os.listdir(source_dir) if f.endswith('.py') and f != '__init__.py']
            for filename in files:
                compat_file = filename
                if os.path.exists(compat_file):
                    update_compat_file(compat_file, source_dir)

if __name__ == '__main__':
    main()
