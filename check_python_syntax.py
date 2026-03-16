import os
import py_compile
import sys

def check_all_python_files():
    """检查所有Python文件的语法"""
    
    python_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                # 跳过一些不需要检查的目录
                if '__pycache__' in root or '.git' in root:
                    continue
                python_files.append(os.path.join(root, file))
    
    errors = []
    
    for file_path in sorted(python_files):
        try:
            # 尝试编译文件，这样可以检查语法错误
            py_compile.compile(file_path, doraise=True)
            print(f"✅ {file_path}")
        except py_compile.PyCompileError as e:
            print(f"❌ {file_path}")
            errors.append({
                'file': file_path,
                'error': str(e)
            })
        except Exception as e:
            print(f"⚠️  {file_path}: {str(e)[:50]}")
    
    return errors

if __name__ == "__main__":
    print("=" * 80)
    print("检查所有Python文件的语法错误")
    print("=" * 80)
    print()
    
    errors = check_all_python_files()
    
    print()
    print("=" * 80)
    if errors:
        print(f"发现 {len(errors)} 个语法错误：")
        print("=" * 80)
        for err in errors:
            print(f"\n文件: {err['file']}")
            print(f"错误: {err['error']}")
            print("-" * 80)
        sys.exit(1)
    else:
        print("✅ 所有Python文件语法检查通过！")
        print("=" * 80)
        sys.exit(0)
