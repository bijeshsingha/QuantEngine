import pandas as pd
import refinitiv.data as rd
from scipy.optimize import root_scalar

print("Loading dynamic inputs for Reverse DCF...")
df_hist = pd.read_excel("pharma_financials_wacc.xlsx")

def get_col(df, keywords):
    for col in df.columns:
        if any(k.lower() in col.lower() for k in keywords):
            return col
    return None

sun_hist = df_hist[df_hist['Instrument'] == 'SUN.NS']
latest_row = sun_hist.iloc[-1]

latest_revenue = latest_row[get_col(df_hist, ['revenue'])]
wacc = latest_row['WACC']
latest_debt = latest_row[get_col(df_hist, ['debt'])]
latest_cash = latest_row[get_col(df_hist, ['cash'])]
market_cap = latest_row[get_col(df_hist, ['market cap'])]

# Get live price to calculate exact shares
rd.open_session()
df_market = rd.get_data(["SUN.NS"], ["TR.PriceClose"])
rd.close_session()

price_col = get_col(df_market, ['price'])
current_market_price = df_market[price_col].values[0]
shares_outstanding = market_cap / current_market_price
net_debt = latest_debt - latest_cash

# Base parameters (Holding margin constant to solve for growth)
base_margin = 0.23
tax_rate = 0.25
terminal_growth = 0.05
historical_capex_pct = 0.06
historical_nwc_pct = 0.20
forecast_years = 5

def calculate_share_price(implied_growth):
    current_rev = latest_revenue
    pv_explicit_cf = 0
    
    for year in range(1, forecast_years + 1):
        prev_rev = current_rev
        current_rev = current_rev * (1 + implied_growth)
        
        projected_ebit = current_rev * base_margin
        nopat = projected_ebit * (1 - tax_rate)
        
        projected_capex = current_rev * historical_capex_pct
        projected_da = projected_capex * 0.85
        
        # Calculate NWC drag
        change_in_rev = current_rev - prev_rev
        nwc_investment = change_in_rev * historical_nwc_pct
        
        fcff = nopat + projected_da - projected_capex - nwc_investment
        pv_explicit_cf += fcff / ((1 + wacc) ** year)
        
    terminal_value = (fcff * (1 + terminal_growth)) / (wacc - terminal_growth)
    pv_terminal_value = terminal_value / ((1 + wacc) ** forecast_years)
    
    implied_ev = pv_explicit_cf + pv_terminal_value
    implied_equity = implied_ev - net_debt
    return implied_equity / shares_outstanding

# Objective function for the root solver: (calculated_price - market_price) == 0
def objective_function(implied_growth):
    return calculate_share_price(implied_growth) - current_market_price

# Solve for the implied growth rate using scipy (searching between -50% and +100% growth)
result = root_scalar(objective_function, bracket=[-0.5, 1.0], method='brentq')

implied_market_growth = result.root

print("\n--- REVERSE DCF (SOLVING FOR MARKET DELUSION) ---")
print(f"Current Market Price:           INR {current_market_price:,.2f}")
print(f"Our Base Case Growth Rate:      10.00%")
print(f"Growth Rate Priced by Market:   {implied_market_growth * 100:.2f}%\n")

if implied_market_growth > 0.12:
    print(f"CONCLUSION: The market is pricing in {implied_market_growth*100:.1f}% annual revenue growth for the next 5 years.")
    print("Because Sun Pharma has historically never sustained growth above 12% at this scale, the market is delusional.")
    print("This confirms the SELL rating. The stock is priced for perfection that mathematically cannot be achieved.")
else:
    print(f"CONCLUSION: The market is pricing in {implied_market_growth*100:.1f}% annual revenue growth.")
    print("This is within historical bounds, meaning the market is rational.")
