import os
import sys
from datetime import datetime

# 导入所有DB模块
from db.database import db as stock_db
from db.longhubang_db import LonghubangDatabase
lhb_db = LonghubangDatabase()
from db.sector_strategy_db import SectorStrategyDatabase
sector_db = SectorStrategyDatabase()
from db.portfolio_db import portfolio_db
from db.news_flow_db import news_flow_db
from db.monitor_db import monitor_db
from db.smart_monitor_db import SmartMonitorDB
from db.main_force_batch_db import batch_db
from strategies.low_price_bull_monitor import low_price_bull_monitor

def test_db_read_write():
    print("=== 开始测试各数据库模块读写功能 ===")
    
    # 1. database.py (StockAnalysisDatabase)
    print("\n[1] Testing database.py...")
    try:
        record_id = stock_db.save_analysis(
            symbol="000001",
            stock_name="平安银行",
            period="1日",
            stock_info={"test": 1},
            agents_results={"test": 1},
            discussion_result={"test": 1},
            final_decision={"rating": "买入"}
        )
        print(f"  ✅ 写入成功，记录ID: {record_id}")
        record = stock_db.get_record_by_id(record_id)
        if record and record['id'] == record_id:
            print("  ✅ 读取成功")
        else:
            print("  ❌ 读取失败")
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")

    # 2. portfolio_db.py
    print("\n[2] Testing portfolio_db.py...")
    try:
        stock_id = portfolio_db.add_stock("600519", "贵州茅台", 1650.5, 100, "测试持仓")
        print(f"  ✅ 写入成功，股票ID: {stock_id}")
        stock = portfolio_db.get_stock(stock_id)
        if stock and stock['code'] == "600519":
            print("  ✅ 读取成功")
            portfolio_db.delete_stock(stock_id)
            print("  ✅ 删除成功")
        else:
            print("  ❌ 读取失败")
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        
    # 3. monitor_db.py
    print("\n[3] Testing monitor_db.py...")
    try:
        monitor_id = monitor_db.add_monitored_stock(
            symbol="AAPL", name="苹果", rating="买入", 
            entry_range={"min":150, "max":160}, take_profit=180, stop_loss=140
        )
        print(f"  ✅ 写入成功，监测ID: {monitor_id}")
        monitor_stock = monitor_db.get_stock_by_id(monitor_id)
        if monitor_stock and monitor_stock['symbol'] == "AAPL":
            print("  ✅ 读取成功")
            monitor_db.remove_monitored_stock(monitor_id)
            print("  ✅ 删除成功")
        else:
            print("  ❌ 读取失败")
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")

    # 4. news_flow_db.py
    print("\n[4] Testing news_flow_db.py...")
    try:
        snapshot_id = news_flow_db.save_flow_snapshot(
            flow_data={'total_score': 100, 'level': '测试'},
            platforms_data=[],
            stock_news=[],
            hot_topics=[]
        )
        print(f"  ✅ 写入成功，快照ID: {snapshot_id}")
        latest = news_flow_db.get_latest_snapshot()
        if latest and latest['id'] == snapshot_id:
            print("  ✅ 读取成功")
        else:
            print("  ❌ 读取失败")
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")

    # 5. main_force_batch_db.py
    print("\n[5] Testing main_force_batch_db.py...")
    try:
        record_id = batch_db.save_batch_analysis(1, "sequential", 1, 0, 1.0, [{"code":"000001"}])
        print(f"  ✅ 写入成功，批量记录ID: {record_id}")
        rec = batch_db.get_record_by_id(record_id)
        if rec and rec['id'] == record_id:
            print("  ✅ 读取成功")
            batch_db.delete_record(record_id)
        else:
            print("  ❌ 读取失败")
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")

    print("\n=== 所有测试完成 ===")

if __name__ == "__main__":
    test_db_read_write()
