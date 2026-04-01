import akshare as ak
try:
    df = ak.stock_zh_a_daily(symbol="sz000001", start_date="20230101", end_date="20230601")
    print("daily ok", len(df))
except Exception as e:
    print("daily failed", e)
