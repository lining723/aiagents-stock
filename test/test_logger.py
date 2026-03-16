#!/usr/bin/env python3
"""测试日志模块"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger import get_logger, setup_logger

def test_logger():
    logger = get_logger(__name__)
    
    logger.debug("这是一条DEBUG日志")
    logger.info("这是一条INFO日志")
    logger.warning("这是一条WARNING日志")
    logger.error("这是一条ERROR日志")
    logger.critical("这是一条CRITICAL日志")
    
    print("\n✅ 日志测试完成！")
    print("请检查 log/app.log 文件是否被创建并包含日志内容")

if __name__ == "__main__":
    test_logger()
