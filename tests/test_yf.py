import yfinance as yf
df = yf.download("000001.SZ", period="100d")
print(df.head())
