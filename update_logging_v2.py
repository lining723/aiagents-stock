#!/usr/bin/env python3
"""批量更新所有模块使用统一日志系统 - 改进版"""

import os


def update_file_logging_v2(file_path):
    """
    更新单个文件的日志配置
    
    Args:
        file_path: 文件路径
    
    Returns:
        bool: 是否进行了更新
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        lines = content.split('\n')
        new_lines = []
        
        i = 0
        n = len(lines)
        
        while i < n:
            line = lines[i]
            
            if 'import logging' in line:
                j = i + 1
                skip_count = 0
                
                while j < n:
                    next_line = lines[j]
                    if 'logging.basicConfig' in next_line:
                        skip_count += 1
                        j += 1
                    elif 'logger = logging.getLogger(__name__)' in next_line:
                        skip_count += 1
                        j += 1
                        break
                    elif next_line.strip() == '':
                        skip_count += 1
                        j += 1
                    else:
                        break
                
                if skip_count > 0:
                    new_lines.append('from utils.logger import get_logger')
                    new_lines.append('logger = get_logger(__name__)')
                    i = j
                    continue
            
            new_lines.append(line)
            i += 1
        
        new_content = '\n'.join(new_lines)
        
        if new_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
        
        return False
    
    except Exception as e:
        print(f"  ❌ 更新失败 {file_path}: {e}")
        return False


def scan_and_update(directory):
    """
    扫描并更新目录下的所有Python文件
    
    Args:
        directory: 目录路径
    """
    print(f"\n扫描目录: {directory}")
    print("=" * 80)
    
    updated_count = 0
    total_count = 0
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                file_path = os.path.join(root, file)
                
                if 'log' in file_path or 'logger' in file_path:
                    continue
                
                total_count += 1
                if update_file_logging_v2(file_path):
                    print(f"  ✅ 更新: {file_path}")
                    updated_count += 1
    
    print("=" * 80)
    print(f"总计: {total_count} 个文件, 更新: {updated_count} 个文件")
    return updated_count


if __name__ == "__main__":
    print("=" * 80)
    print("批量更新日志系统 - 改进版")
    print("=" * 80)
    
    directories_to_update = [
        'config',
        'data',
        'db',
        'agents',
        'services',
        'strategies',
        'ui',
        'utils',
    ]
    
    for directory in directories_to_update:
        if os.path.exists(directory):
            scan_and_update(directory)
    
    print("\n✅ 批量更新完成！")
