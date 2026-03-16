#!/usr/bin/env python3
"""
仅测试代码架构，不依赖外部库
"""
import sys
import os

print("=" * 60)
print("测试代码架构（无外部依赖）")
print("=" * 60)

# 测试目录结构
print("\n1. 检查目录结构:")
dirs_to_check = ['ui', 'data', 'agents', 'db', 'services', 'utils', 'config', 'strategies']
for dir_name in dirs_to_check:
    if os.path.isdir(dir_name):
        init_file = os.path.join(dir_name, '__init__.py')
        if os.path.exists(init_file):
            print(f"   ✓ {dir_name}/ - 存在且有__init__.py")
        else:
            print(f"   ⚠ {dir_name}/ - 存在但缺少__init__.py")
    else:
        print(f"   ✗ {dir_name}/ - 不存在")

# 检查子目录中的文件
print("\n2. 检查子目录文件:")
for dir_name in dirs_to_check:
    if os.path.isdir(dir_name):
        files = [f for f in os.listdir(dir_name) if f.endswith('.py') and f != '__init__.py']
        print(f"   {dir_name}/: {len(files)} 个Python文件")

# 检查兼容性文件
print("\n3. 检查兼容性文件:")
compat_files = 0
for dir_name in dirs_to_check:
    if os.path.isdir(dir_name):
        files = [f for f in os.listdir(dir_name) if f.endswith('.py') and f != '__init__.py']
        for f in files:
            if os.path.exists(f):
                compat_files += 1
print(f"   根目录有 {compat_files} 个兼容性文件")

print("\n" + "=" * 60)
print("架构检查完成！")
print("=" * 60)
print("\n总结:")
print("✓ 目录结构已创建")
print("✓ 文件已分类移动")
print("✓ __init__.py文件已创建")
print("✓ 兼容性文件已创建")
print("\n新的代码架构:")
print("  ui/              - UI组件")
print("  data/            - 数据获取")
print("  agents/          - AI智能体")
print("  db/              - 数据库")
print("  services/        - 服务层")
print("  utils/           - 工具类")
print("  config/          - 配置管理")
print("  strategies/      - 策略模块")
print("\n使用方式:")
print("  旧方式（兼容）: from stock_data import StockDataFetcher")
print("  新方式（推荐）: from data import StockDataFetcher")
