#!/usr/bin/env python3
"""
修复所有Python文件中的import乱码问题
"""
import os
import re

def fix_file(file_path):
    """修复单个文件中的import乱码"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 修复类型1: from xxx import xxx
xxx
        # 例如: from db.monitor_db import monitor_db
        # 变为: from db.monitor_db import monitor_db
        pattern = r'from (\w+)\.(\w+) import \1\.\2\x01'
        replacement = r'from \1.\2 import \2'
        content = re.sub(pattern, replacement, content)
        
        # 修复类型2: from xxx import xxx
xxx
        # 例如: from services.monitor_service import monitor_service
        # 变为: from services.monitor_service import monitor_service
        pattern = r'from (\w+)\.(\w+) import \1\.\2\x01\s*'
        replacement = r'from \1.\2 import \2\n'
        content = re.sub(pattern, replacement, content)
        
        # 修复类型3: import xxx
xxx
        # 例如: import config.config as config
        # 变为: import config.config as config
        pattern = r'import (\w+)\.(\w+)\x01(\w+)\x01'
        replacement = r'import \1.\2 as \3'
        content = re.sub(pattern, replacement, content)
        
        # 修复类型4: import xxx
xxx (没有第二个
)
        # 例如: import config.config as config
        # 变为: import config.config as config
        pattern = r'import (\w+)\.(\w+)\x01(\w+)'
        replacement = r'import \1.\2 as \3'
        content = re.sub(pattern, replacement, content)
        
        # 修复类型5: from xxx import xxx
yyy
        # 例如: from strategies.low_price_bull_monitor import low_price_bull_monitorfrom services.notification_service import notification_service
        # 先处理多个import在一行的情况
        pattern = r'from (\w+)\.(\w+) import \1\.\2\x01'
        content = re.sub(pattern, r'from \1.\2 import \2\n', content)
        
        # 修复类型6: 多个import连在一起的情况
        # 例如: from db.portfolio_db import portfolio_dbimport config.config as config
        content = re.sub(r'(\x01)(?!\n)', r'\n', content)
        
        # 清理任何残留的\x01字符
        content = content.replace('\x01', '')
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'✓ 修复: {file_path}')
            return True
        return False
    except Exception as e:
        print(f'✗ 错误 {file_path}: {e}')
        return False

def main():
    """主函数"""
    print('=' * 60)
    print('修复Python文件中的import乱码问题')
    print('=' * 60)
    
    directories = ['ui', 'data', 'agents', 'db', 'services', 'utils', 'config', 'strategies', '.']
    
    fixed_count = 0
    
    for directory in directories:
        if not os.path.isdir(directory):
            continue
        
        print(f'\n处理目录: {directory}/')
        for filename in os.listdir(directory):
            if filename.endswith('.py') and filename != '__init__.py':
                file_path = os.path.join(directory, filename)
                if fix_file(file_path):
                    fixed_count += 1
    
    print('\n' + '=' * 60)
    print(f'修复完成！共修复了 {fixed_count} 个文件')
    print('=' * 60)

if __name__ == '__main__':
    main()
