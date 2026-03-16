#!/usr/bin/env python3
"""
简单的导入测试脚本
"""
print("=" * 60)
print("测试新代码架构的导入")
print("=" * 60)

# 测试旧的导入方式（兼容性）
print("\n1. 测试旧的导入方式（兼容性）:")
try:
    import config
    print(f"   ✓ config 导入成功")
    print(f"   - DEFAULT_MODEL_NAME: {config.DEFAULT_MODEL_NAME}")
except Exception as e:
    print(f"   ✗ config 导入失败: {e}")

try:
    from stock_data import StockDataFetcher
    print(f"   ✓ stock_data.StockDataFetcher 导入成功")
except Exception as e:
    print(f"   ✗ stock_data 导入失败: {e}")

try:
    from ai_agents import StockAnalysisAgents
    print(f"   ✓ ai_agents.StockAnalysisAgents 导入成功")
except Exception as e:
    print(f"   ✗ ai_agents 导入失败: {e}")

try:
    from database import db
    print(f"   ✓ database.db 导入成功")
except Exception as e:
    print(f"   ✗ database 导入失败: {e}")

# 测试新的导入方式
print("\n2. 测试新的导入方式（推荐）:")
try:
    from config import DEFAULT_MODEL_NAME
    print(f"   ✓ config.DEFAULT_MODEL_NAME 导入成功: {DEFAULT_MODEL_NAME}")
except Exception as e:
    print(f"   ✗ config 导入失败: {e}")

try:
    from data import StockDataFetcher
    print(f"   ✓ data.StockDataFetcher 导入成功")
except Exception as e:
    print(f"   ✗ data 导入失败: {e}")

try:
    from agents import StockAnalysisAgents
    print(f"   ✓ agents.StockAnalysisAgents 导入成功")
except Exception as e:
    print(f"   ✗ agents 导入失败: {e}")

try:
    from db import db
    print(f"   ✓ db.db 导入成功")
except Exception as e:
    print(f"   ✗ db 导入失败: {e}")

try:
    from services import monitor_service
    print(f"   ✓ services.monitor_service 导入成功")
except Exception as e:
    print(f"   ✗ services 导入失败: {e}")

try:
    from utils import display_pdf_export_section
    print(f"   ✓ utils.display_pdf_export_section 导入成功")
except Exception as e:
    print(f"   ✗ utils 导入失败: {e}")

try:
    from ui import display_longhubang
    print(f"   ✓ ui.display_longhubang 导入成功")
except Exception as e:
    print(f"   ✗ ui 导入失败: {e}")

try:
    from strategies import MainForceSelector
    print(f"   ✓ strategies.MainForceSelector 导入成功")
except Exception as e:
    print(f"   ✗ strategies 导入失败: {e}")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)
