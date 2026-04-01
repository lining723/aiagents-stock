import tushare as ts
import os
from dotenv import load_dotenv
load_dotenv()
token = os.getenv("TUSHARE_TOKEN")
pro = ts.pro_api(token)
df = pro.daily(ts_code='000001.SZ', start_date='20230101', end_date='20230601')
print(df.head())
