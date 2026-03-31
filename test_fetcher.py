from config.smart_monitor_kline import SmartMonitorKline
from data.smart_monitor_data import SmartMonitorDataFetcher

fetcher = SmartMonitorDataFetcher()
kline = SmartMonitorKline()

df = kline.get_kline_data("000001", 60, fetcher)
if df is not None:
    print(df.head())
else:
    print("None returned")
