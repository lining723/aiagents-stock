#!/usr/bin/env python3
"""
测试导入是否正常工作
"""
print('Testing imports...')

try:
    from stock_data import StockDataFetcher
    print('✓ stock_data.StockDataFetcher imported')
except Exception as e:
    print(f'✗ stock_data import failed: {e}')

try:
    from ai_agents import StockAnalysisAgents
    print('✓ ai_agents.StockAnalysisAgents imported')
except Exception as e:
    print(f'✗ ai_agents import failed: {e}')

try:
    from config import DEFAULT_MODEL_NAME
    print(f'✓ config.DEFAULT_MODEL_NAME imported: {DEFAULT_MODEL_NAME}')
except Exception as e:
    print(f'✗ config import failed: {e}')

try:
    from database import db
    print('✓ database.db imported')
except Exception as e:
    print(f'✗ database import failed: {e}')

try:
    from monitor_service import monitor_service
    print('✓ monitor_service imported')
except Exception as e:
    print(f'✗ monitor_service import failed: {e}')

try:
    from ui import display_longhubang
    print('✓ ui.display_longhubang imported')
except Exception as e:
    print(f'✗ ui import failed: {e}')

print('\nTesting new imports from subdirectories...')

try:
    from data import StockDataFetcher
    print('✓ data.StockDataFetcher imported')
except Exception as e:
    print(f'✗ data import failed: {e}')

try:
    from agents import StockAnalysisAgents
    print('✓ agents.StockAnalysisAgents imported')
except Exception as e:
    print(f'✗ agents import failed: {e}')

try:
    from db import db
    print('✓ db.db imported')
except Exception as e:
    print(f'✗ db import failed: {e}')

try:
    from services import monitor_service
    print('✓ services.monitor_service imported')
except Exception as e:
    print(f'✗ services import failed: {e}')

try:
    from utils import display_pdf_export_section
    print('✓ utils.display_pdf_export_section imported')
except Exception as e:
    print(f'✗ utils import failed: {e}')

print('\nAll tests completed!')
