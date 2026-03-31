import akshare as ak
import datetime
symbol = "000001"
end_date = datetime.datetime.now()
start_date = end_date - datetime.timedelta(days=150)
df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date.strftime("%Y%m%d"), end_date=end_date.strftime("%Y%m%d"), adjust="qfq")
print(df.head())
