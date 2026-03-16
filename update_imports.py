#!/usr/bin/env python3
"""
自动更新所有文件的import语句
"""
import os
import re

# 定义import映射规则
IMPORT_MAPPINGS = {
    # data模块
    'stock_data': 'data',
    'fund_flow_akshare': 'data',
    'longhubang_data': 'data',
    'macro_cycle_data': 'data',
    'market_sentiment_data': 'data',
    'news_announcement_data': 'data',
    'news_flow_data': 'data',
    'qstock_news_data': 'data',
    'quarterly_report_data': 'data',
    'risk_data_fetcher': 'data',
    'sector_strategy_data': 'data',
    'smart_monitor_data': 'data',
    'smart_monitor_tdx_data': 'data',
    
    # agents模块
    'ai_agents': 'agents',
    'deepseek_client': 'agents',
    'longhubang_agents': 'agents',
    'macro_cycle_agents': 'agents',
    'news_flow_agents': 'agents',
    'sector_strategy_agents': 'agents',
    
    # db模块
    'database': 'db',
    'longhubang_db': 'db',
    'main_force_batch_db': 'db',
    'monitor_db': 'db',
    'news_flow_db': 'db',
    'portfolio_db': 'db',
    'sector_strategy_db': 'db',
    'smart_monitor_db': 'db',
    
    # services模块
    'monitor_service': 'services',
    'monitor_manager': 'services',
    'monitor_scheduler': 'services',
    'notification_service': 'services',
    'longhubang_engine': 'services',
    'low_price_bull_service': 'services',
    'macro_cycle_engine': 'services',
    'news_flow_engine': 'services',
    'news_flow_scheduler': 'services',
    'portfolio_scheduler': 'services',
    'sector_strategy_engine': 'services',
    'sector_strategy_scheduler': 'services',
    'smart_monitor_engine': 'services',
    'main_force_analysis': 'services',
    'news_flow_alert': 'services',
    'news_flow_model': 'services',
    'news_flow_sentiment': 'services',
    'portfolio_manager': 'services',
    'smart_monitor_deepseek': 'services',
    
    # utils模块
    'pdf_generator': 'utils',
    'pdf_generator_fixed': 'utils',
    'pdf_generator_pandoc': 'utils',
    'longhubang_pdf': 'utils',
    'longhubang_scoring': 'utils',
    'macro_cycle_pdf': 'utils',
    'news_flow_pdf': 'utils',
    'sector_strategy_pdf': 'utils',
    'main_force_pdf_generator': 'utils',
    
    # config模块
    'config': 'config',
    'config_manager': 'config',
    'model_config': 'config',
    'data_source_manager': 'config',
    'miniqmt_interface': 'config',
    'smart_monitor_kline': 'config',
    'smart_monitor_qmt': 'config',
    
    # strategies模块
    'low_price_bull_monitor': 'strategies',
    'low_price_bull_selector': 'strategies',
    'low_price_bull_strategy': 'strategies',
    'main_force_selector': 'strategies',
    'profit_growth_monitor': 'strategies',
    'profit_growth_selector': 'strategies',
    'small_cap_selector': 'strategies',
    'value_stock_selector': 'strategies',
    'value_stock_strategy': 'strategies',
    
    # ui模块 (ui模块之间的导入不需要改)
}

def update_file_imports(file_path):
    """更新单个文件的import语句"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 更新 from xxx import yyy 语句
    for old_module, new_module in IMPORT_MAPPINGS.items():
        # 匹配 from old_module import ...
        pattern = rf'from {re.escape(old_module)} import'
        replacement = f'from {new_module}.{old_module} import'
        content = re.sub(pattern, replacement, content)
        
        # 匹配 import old_module
        pattern = rf'import {re.escape(old_module)}([^\w]|$)'
        replacement = f'import {new_module}.{old_module}\1'
        content = re.sub(pattern, replacement, content)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'✓ Updated: {file_path}')
        return True
    return False

def main():
    """主函数"""
    print('=' * 60)
    print('自动更新import语句')
    print('=' * 60)
    
    # 要处理的目录
    directories = ['ui', 'data', 'agents', 'db', 'services', 'utils', 'config', 'strategies']
    
    updated_count = 0
    
    for directory in directories:
        if not os.path.isdir(directory):
            continue
        
        print(f'\n处理目录: {directory}/')
        for filename in os.listdir(directory):
            if filename.endswith('.py') and filename != '__init__.py':
                file_path = os.path.join(directory, filename)
                if update_file_imports(file_path):
                    updated_count += 1
    
    # 处理根目录的文件
    print(f'\n处理根目录文件:')
    for filename in ['app.py', 'run.py']:
        if os.path.exists(filename):
            if update_file_imports(filename):
                updated_count += 1
    
    print('\n' + '=' * 60)
    print(f'更新完成！共更新了 {updated_count} 个文件')
    print('=' * 60)

if __name__ == '__main__':
    main()
