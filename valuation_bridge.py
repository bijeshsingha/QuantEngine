import pandas as pd
import refinitiv.data as rd

print("Fetching live market data...")
rd.open_session()
df_market = rd.get_data(
    universe=["SUN.NS"],
    fields=["TR.PriceClose"]
)
rd.close_session()

def get_col(df, keywords):
    for col in df.columns:
        if any(k.lower() in col.lower() for k in keywords):
            return col
    return None

price_col = get_col(df_market, ['price'])
current_market_price = df_market[price_col].values[0]

# 1. Ingest Data from Previous Steps
df_hist = pd.read_excel("pharma_financials_wacc.xlsx")
df_base_case = pd.read_excel("base_case_forecast.xlsx")

sun_hist = df_hist[df_hist['Instrument'] == 'SUN.NS'].iloc[-1]

latest_debt = sun_hist[get_col(df_hist, ['debt'])]
latest_cash = sun_hist[get_col(df_hist, ['cash'])]
market_cap = sun_hist[get_col(df_hist, ['market cap'])]
wacc_rate = sun_hist['WACC']

# Calculate exact shares outstanding
shares_outstanding = market_cap / current_market_price

terminal_growth_rate = 0.05  # 5% long-term growth rate for India

# 2. Discount the 5-Year Explicit Forecast Period
df_base_case['Discount Factor'] = [1 / ((1 + wacc_rate) ** i) for i in range(1, 6)]
df_base_case['PV of FCFF'] = df_base_case['FCFF'] * df_base_case['Discount Factor']

sum_pv_explicit_fcff = df_base_case['PV of FCFF'].sum()

# 3. Calculate Terminal Value (Gordon Growth Model)
final_year_fcff = df_base_case['FCFF'].iloc[-1]
terminal_value = (final_year_fcff * (1 + terminal_growth_rate)) / (wacc_rate - terminal_growth_rate)
pv_of_terminal_value = terminal_value * df_base_case['Discount Factor'].iloc[-1]

# 4. Total Enterprise Value (EV)
implied_enterprise_value = sum_pv_explicit_fcff + pv_of_terminal_value

# 5. The Valuation Bridge to Equity Value
net_debt = latest_debt - latest_cash
implied_equity_value = implied_enterprise_value - net_debt

# 6. Calculate Intrinsic Share Price
implied_share_price = implied_equity_value / shares_outstanding

print("\n--- PHASE 3: DETERMINISTIC VALUATION BRIDGE REPORT ---")
print(f"PV of 5-Year Explicit Cash Flows:  INR {sum_pv_explicit_fcff:,.2f} Mn")
print(f"PV of Terminal Value (Perpetual):  INR {pv_of_terminal_value:,.2f} Mn")
print(f"Implied Enterprise Value (EV):     INR {implied_enterprise_value:,.2f} Mn")
print(f"Less: Total Debt Outstanding:     -INR {latest_debt:,.2f} Mn")
print(f"Plus: Cash & Equivalents:         +INR {latest_cash:,.2f} Mn")
print(f"-------------------------------------------------------")
print(f"Implied Equity Value:              INR {implied_equity_value:,.2f} Mn")
print(f"Total Shares Outstanding:          {shares_outstanding:,.2f} Mn")
print(f"-------------------------------------------------------")
print(f"Calculated Intrinsic Share Price:  INR {implied_share_price:,.2f}")
print(f"Current Market Trading Price:      INR {current_market_price:,.2f}")
upside = ((implied_share_price / current_market_price) - 1) * 100
print(f"Implied Upside/Downside:           {upside:.2f}%")

# Export to Excel
report_data = {
    "Metric": [
        "PV of 5-Year Explicit Cash Flows (Mn)",
        "PV of Terminal Value (Perpetual) (Mn)",
        "Implied Enterprise Value (EV) (Mn)",
        "Less: Total Debt Outstanding (Mn)",
        "Plus: Cash & Equivalents (Mn)",
        "Implied Equity Value (Mn)",
        "Total Shares Outstanding (Mn)",
        "Calculated Intrinsic Share Price",
        "Current Market Trading Price",
        "Implied Upside/Downside (%)"
    ],
    "Value": [
        round(sum_pv_explicit_fcff, 2),
        round(pv_of_terminal_value, 2),
        round(implied_enterprise_value, 2),
        round(-latest_debt, 2),
        round(latest_cash, 2),
        round(implied_equity_value, 2),
        round(shares_outstanding, 2),
        round(implied_share_price, 2),
        round(current_market_price, 2),
        round(upside, 2)
    ]
}

df_report = pd.DataFrame(report_data)
df_report.to_excel("valuation_bridge_report.xlsx", index=False)
print("\nExported Valuation Bridge to valuation_bridge_report.xlsx")
