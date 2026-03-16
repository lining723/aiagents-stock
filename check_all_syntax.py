import os
import re

def check_syntax_errors():
    """检查所有Python文件中的import语句和后续代码连在一起的问题"""
    
    python_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    issues = []
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查import语句后直接跟着代码（没有换行）的模式
            # 查找 import xxx 后面不是换行或注释的情况
            lines = content.split('\n')
            for line_num, line in enumerate(lines, 1):
                # 检查是否有import语句后面直接跟着其他代码
                if 'import' in line and 'except' not in line and 'try:' not in line:
                    # 检查是否有多个语句在同一行
                    if line.count('import') > 1:
                        # 检查是否是正常的多import
                        if ' from ' in line and line.count('import') > 1:
                            # 可能是 from xxx import a, import b 的问题
                            pass
                    # 检查import语句后面是否有其他代码（不是注释）
                    if 'import' in line:
                        # 分割import语句后面的部分
                        parts = line.split('import', 1)
                        if len(parts) > 1:
                            after_import = parts[1].strip()
                            # 检查是否有多个语句（有空格或制表符分隔）
                            if '    ' in after_import or '\t' in after_import:
                                # 可能是import和其他代码连在一起
                                issues.append({
                                    'file': file_path,
                                    'line': line_num,
                                    'content': line.strip()
                                })
            
        except Exception as e:
            print(f"无法读取文件 {file_path}: {e}")
    
    return issues

if __name__ == "__main__":
    print("正在检查语法错误...")
    issues = check_syntax_errors()
    
    if issues:
        print(f"\n发现 {len(issues)} 个潜在问题：\n")
        for issue in issues:
            print(f"文件: {issue['file']}")
            print(f"行号: {issue['line']}")
            print(f"内容: {issue['content']}")
            print("-" * 80)
    else:
        print("✅ 未发现明显的语法错误")
