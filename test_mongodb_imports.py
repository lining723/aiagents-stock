import os
import sys

def test_db_modules():
    print("Testing DB modules initialization with MongoDB...")
    
    modules = [
        "db.database",
        "db.longhubang_db",
        "db.sector_strategy_db",
        "db.portfolio_db",
        "db.news_flow_db",
        "db.monitor_db",
        "db.smart_monitor_db",
        "db.main_force_batch_db",
        "strategies.low_price_bull_monitor"
    ]
    
    success = 0
    for mod_name in modules:
        try:
            __import__(mod_name)
            print(f"✅ Successfully imported {mod_name}")
            success += 1
        except Exception as e:
            print(f"❌ Failed to import {mod_name}: {e}")
            
    print(f"\nResult: {success}/{len(modules)} modules imported successfully.")

if __name__ == "__main__":
    test_db_modules()
