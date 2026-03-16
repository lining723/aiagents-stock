#!/usr/bin/env python3
"""测试统一日志系统"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("测试统一日志系统")
print("=" * 80)

from utils.logger import get_logger

print("\n1. 测试获取logger实例")
logger = get_logger(__name__)
logger.info("测试logger实例创建成功")

print("\n2. 测试不同级别的日志")
logger.debug("这是DEBUG日志")
logger.info("这是INFO日志")
logger.warning("这是WARNING日志")
logger.error("这是ERROR日志")
logger.critical("这是CRITICAL日志")

print("\n3. 测试其他模块的logger")
from services.news_flow_engine import NewsFlowEngine

print("  - NewsFlowEngine 导入成功")

from db.news_flow_db import NewsFlowDatabase

print("  - NewsFlowDatabase 导入成功")

from agents.news_flow_agents import NewsFlowAgents

print("  - NewsFlowAgents 导入成功")

print("\n" + "=" * 80)
print("✅ 日志系统测试完成！")
print("=" * 80)
print("\n请检查 log/app.log 文件确认日志已记录")

log_file = os.path.join(os.path.dirname(__file__), "log", "app.log")
if os.path.exists(log_file):
    print(f"\n✅ 日志文件存在: {log_file}")
    print(f"   文件大小: {os.path.getsize(log_file)} 字节")
