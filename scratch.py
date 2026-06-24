import pandas as pd
import refinitiv.data as rd

rd.open_session()
df_market = rd.get_data(
    universe=["SUN.NS"],
    fields=["TR.TotalSharesOutstanding", "TR.PriceClose"]
)
print("Market columns:", df_market.columns.tolist())
print(df_market)
rd.close_session()
