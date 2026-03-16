#!/usr/bin/env python3
"""
自动生成兼容性文件的脚本
为每个子模块中的文件在根目录创建兼容性包装
"""
import os
import sys

def generate_compat_file(module_name, source_dir):
    """
    生成兼容性文件
    """
    files = [f for f in os.listdir(source_dir) if f.endswith('.py') and f != '__init__.py']
    
    for filename in files:
        module_name_no_ext = filename[:-3]
        
        # 尝试从__init__.py中获取导出内容
        init_file = os.path.join(source_dir, '__init__.py')
        exports = []
        
        if os.path.exists(init_file):
            with open(init_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 简单的解析，查找from .xxx import xxx
                lines = content.split('\n')
                for line in lines:
                    if line.strip().startswith(f'from .{module_name_no_ext}'):
                        parts = line.split('import')
                        if len(parts) > 1:
                            export_part = parts[1].strip()
                            # 移除括号等
                            export_part = export_part.replace('(', '').replace(')', '').replace(',', ' ')
                            exports.extend([x.strip() for x in export_part.split() if x.strip()])
        
        # 生成兼容性文件
        compat_content = f"""from {source_dir} import {', '.join(exports) if exports else '*'}

__all__ = {exports if exports else ['*']}
"""
        
        compat_file = os.path.join('.', filename)
        
        # 避免覆盖已有的文件
        if os.path.exists(compat_file):
            print(f"Skipping {filename} (already exists)")
            continue
            
        with open(compat_file, 'w', encoding='utf-8') as f:
            f.write(compat_content)
        print(f"Created {filename}")

def main():
    # 为每个目录生成兼容性文件
    directories = ['data', 'agents', 'db', 'services', 'utils', 'config', 'strategies', 'ui']
    
    for directory in directories:
        if os.path.isdir(directory):
            print(f"\nProcessing {directory}/...")
            generate_compat_file(directory, directory)

if __name__ == '__main__':
    main()
