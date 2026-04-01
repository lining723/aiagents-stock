import pywencai
res = pywencai.get(query="000001近60天收盘价、开盘价、最高价、最低价、成交量", loop=True)
if res and 'tableV1' in res:
    import pandas as pd
    df = pd.DataFrame(res['tableV1'])
    print(df.columns)
    print(df.head(2))
