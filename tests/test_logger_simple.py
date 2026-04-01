#!/usr/bin/env python3
"""测试日志模块 - 简化版"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import importlib.util

spec = importlib.util.spec_from_file_location("logger", os.path.join(os.path.dirname(__file__), "utils", "logger.py"))
logger_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(logger_module)

get_logger = logger_module.get_logger
setup_logger = logger_module.setup_logger


def test_logger():
    logger = get_logger(__name__)
    
    logger.debug("这是一条DEBUG日志")
    logger.info("这是一条INFO日志")
    logger.warning("这是一条WARNING日志")
    logger.error("这是一条ERROR日志")
    logger.critical("这是一条CRITICAL日志")
    
    print("\n✅ 日志测试完成！")
    print("请检查 log/app.log 文件是否被创建并包含日志内容")
    
    log_file = os.path.join(os.path.dirname(__file__), "log", "app.log")
    if os.path.exists(log_file):
        print(f"\n✅ 日志文件已创建: {log_file}")
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"\n日志内容预览:\n{content[:500]}...")
    else:
        print(f"\n❌ 日志文件未找到: {log_file}")


if __name__ == "__main__":
    test_logger()
