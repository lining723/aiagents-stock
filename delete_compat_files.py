#!/usr/bin/env python3
"""
删除根目录的兼容性文件
"""
import os

# 要保留的文件（不是兼容性文件）
KEEP_FILES = {
    'app.py',
    'run.py',
    'requirements.txt',
    'README.md',
    '.env',
    '.env.example',
    '.gitignore',
    '.dockerignore',
    'docker-compose.yml',
    'Dockerfile',
    'Dockerfile国内源版',
    'Dockerfile国际源版',
    'BUILD_CN.md',
    'start_app.bat',
    'env_example.txt',
    'stm.py',
    'test_tdx_api.py',
    'update_env_example.py',
    'arch_test.py',
    'simple_test.py',
    'test_imports.py',
    'generate_compat_files.py',
    'update_compat_files.py',
    'update_imports.py',
    'delete_compat_files.py',
}

# 数据库文件也要保留
DB_EXTENSIONS = {'.db', '.sqlite', '.sqlite3'}

# 子目录也要保留
SUBDIRS = {'ui', 'data', 'agents', 'db', 'services', 'utils', 'config', 'strategies', 'docs', '.streamlit', '.git', '.trae', '.tmp'}

def main():
    print('=' * 60)
    print('删除根目录的兼容性文件')
    print('=' * 60)
    
    deleted_count = 0
    
    for filename in os.listdir('.'):
        filepath = os.path.join('.', filename)
        
        # 如果是目录，跳过
        if os.path.isdir(filepath):
            continue
            
        # 检查是否是要保留的文件
        if filename in KEEP_FILES:
            continue
            
        # 检查是否是数据库文件
        _, ext = os.path.splitext(filename)
        if ext.lower() in DB_EXTENSIONS:
            continue
            
        # 检查是否是Python文件且不在保留列表中
        if filename.endswith('.py'):
            print(f'删除: {filename}')
            os.remove(filepath)
            deleted_count += 1
    
    print('\n' + '=' * 60)
    print(f'删除完成！共删除了 {deleted_count} 个兼容性文件')
    print('=' * 60)

if __name__ == '__main__':
    main()
