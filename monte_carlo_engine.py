import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import refinitiv.data as rd

# 1. Ingest Automated Data (Dynamically replacing hardcoded placeholders)
print("Loading dynamic inputs from Phase 1 & 2...")
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

# Base parameters from your script
mean_growth, std_growth = 0.10, 0.02
mean_margin, std_margin = 0.23, 0.015
tax_rate = 0.25
terminal_growth = 0.05
historical_capex_pct = 0.06
historical_nwc_pct = 0.20

# 2. Simulation Setup
simulations = 10000
forecast_years = 5
simulated_share_prices = []

print(f"Running {simulations:,} Monte Carlo valuation iterations...")

# 3. The Master Loop
for sim in range(simulations):
    # Randomly sample the operational drivers for this specific iteration
    sim_growth = np.random.normal(mean_growth, std_growth)
    sim_margin = np.random.normal(mean_margin, std_margin)
    
    current_rev = latest_revenue
    pv_explicit_cf = 0
    
    # 5-Year Explicit Forecast
    for year in range(1, forecast_years + 1):
        prev_rev = current_rev
        current_rev = current_rev * (1 + sim_growth)
        
        projected_ebit = current_rev * sim_margin
        nopat = projected_ebit * (1 - tax_rate)
        
        projected_capex = current_rev * historical_capex_pct
        projected_da = projected_capex * 0.85
        
        # Calculate NWC drag: Growth requires cash tied up in working capital
        change_in_rev = current_rev - prev_rev
        nwc_investment = change_in_rev * historical_nwc_pct
        
        # True Free Cash Flow
        fcff = nopat + projected_da - projected_capex - nwc_investment
        
        # Discount to Present Value
        pv_explicit_cf += fcff / ((1 + wacc) ** year)
        
    # Terminal Value Calculation
    terminal_value = (fcff * (1 + terminal_growth)) / (wacc - terminal_growth)
    pv_terminal_value = terminal_value / ((1 + wacc) ** forecast_years)
    
    # Enterprise Value Bridge to Share Price
    implied_ev = pv_explicit_cf + pv_terminal_value
    implied_equity_value = implied_ev - net_debt
    implied_share_price = implied_equity_value / shares_outstanding
    
    simulated_share_prices.append(implied_share_price)

# 4. Statistical Output
df_sim = pd.DataFrame(simulated_share_prices, columns=['Share_Price'])

print("\n--- MONTE CARLO TARGET PRICE DISTRIBUTION ---")
print(f"10th Percentile (Bear Case):  INR {df_sim['Share_Price'].quantile(0.10):,.2f}")
print(f"50th Percentile (Base Case):  INR {df_sim['Share_Price'].median():,.2f}")
print(f"90th Percentile (Bull Case):  INR {df_sim['Share_Price'].quantile(0.90):,.2f}")
print(f"Standard Deviation (Risk):    INR {df_sim['Share_Price'].std():,.2f}")

# 5. Generate Visuals (Seaborn Bell Curve)
plt.figure(figsize=(12, 7))
sns.histplot(df_sim['Share_Price'], kde=True, bins=100, color='#1E88E5', stat='density', alpha=0.5)

# Plot threshold lines
plt.axvline(df_sim['Share_Price'].quantile(0.10), color='#D32F2F', linestyle='--', linewidth=2, label=f"Bear Case (10th %ile): INR {df_sim['Share_Price'].quantile(0.10):.0f}")
plt.axvline(df_sim['Share_Price'].median(), color='#2E7D32', linestyle='-', linewidth=2.5, label=f"Base Case (50th %ile): INR {df_sim['Share_Price'].median():.0f}")
plt.axvline(df_sim['Share_Price'].quantile(0.90), color='#7B1FA2', linestyle='--', linewidth=2, label=f"Bull Case (90th %ile): INR {df_sim['Share_Price'].quantile(0.90):.0f}")
plt.axvline(current_market_price, color='#212121', linestyle=':', linewidth=3, label=f"Current Market Price: INR {current_market_price:.0f}")

plt.title('Monte Carlo Simulation: 10,000 Intrinsic Value Iterations for SUN.NS', fontsize=16, fontweight='bold', pad=15)
plt.xlabel('Implied Target Share Price (INR)', fontsize=14, labelpad=10)
plt.ylabel('Probability Density', fontsize=14, labelpad=10)
plt.legend(fontsize=12, loc='upper right')
plt.grid(True, alpha=0.3)
plt.tight_layout()

plt.savefig('monte_carlo_distribution.png', dpi=300)
print("\nSaved Monte Carlo visualization to monte_carlo_distribution.png")

# Save results to Excel
df_sim.to_excel("monte_carlo_results.xlsx", index=False)
print("Saved all 10,000 iterations to monte_carlo_results.xlsx")
