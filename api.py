from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import pandas as pd
import math

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache data
print("Loading core data for API...")
df_hist = pd.read_excel("pharma_financials_wacc.xlsx")

def get_col(df, keywords):
    for col in df.columns:
        if any(k.lower() in col.lower() for k in keywords):
            return col
    return None

sun_hist = df_hist[df_hist['Instrument'] == 'SUN.NS']
latest_row = sun_hist.iloc[-1]

latest_revenue = float(latest_row[get_col(df_hist, ['revenue'])])
wacc = float(latest_row['WACC'])
latest_debt = float(latest_row[get_col(df_hist, ['debt'])])
latest_cash = float(latest_row[get_col(df_hist, ['cash'])])
market_cap = float(latest_row[get_col(df_hist, ['market cap'])])

current_market_price = 1868.0
shares_outstanding = market_cap / current_market_price
net_debt = latest_debt - latest_cash

tax_rate = 0.25
historical_capex_pct = 0.06
historical_nwc_pct = 0.20
forecast_years = 5

class MonteCarloParams(BaseModel):
    mean_growth: float
    std_growth: float
    mean_margin: float
    std_margin: float
    terminal_growth: float
    simulations: int = 10000

@app.post("/api/monte-carlo")
def run_monte_carlo(params: MonteCarloParams):
    simulated_share_prices = []
    
    for sim in range(params.simulations):
        sim_growth = np.random.normal(params.mean_growth, params.std_growth)
        sim_margin = np.random.normal(params.mean_margin, params.std_margin)
        
        current_rev = latest_revenue
        pv_explicit_cf = 0
        
        for year in range(1, forecast_years + 1):
            prev_rev = current_rev
            current_rev = current_rev * (1 + sim_growth)
            
            projected_ebit = current_rev * sim_margin
            nopat = projected_ebit * (1 - tax_rate)
            
            projected_capex = current_rev * historical_capex_pct
            projected_da = projected_capex * 0.85
            
            change_in_rev = current_rev - prev_rev
            nwc_investment = change_in_rev * historical_nwc_pct
            
            fcff = nopat + projected_da - projected_capex - nwc_investment
            pv_explicit_cf += fcff / ((1 + wacc) ** year)
            
        terminal_value = (fcff * (1 + params.terminal_growth)) / (wacc - params.terminal_growth)
        pv_terminal_value = terminal_value / ((1 + wacc) ** forecast_years)
        
        implied_ev = pv_explicit_cf + pv_terminal_value
        implied_equity = implied_ev - net_debt
        simulated_share_prices.append(implied_equity / shares_outstanding)

    arr = np.array(simulated_share_prices)
    arr = arr[np.isfinite(arr)]
    
    # Generate histogram data for the frontend Chart.js
    hist, bin_edges = np.histogram(arr, bins=50, density=True)
    
    return {
        "bear_case": float(np.percentile(arr, 10)),
        "base_case": float(np.percentile(arr, 50)),
        "bull_case": float(np.percentile(arr, 90)),
        "std_dev": float(np.std(arr)),
        "histogram": {
            "bins": [float((bin_edges[i] + bin_edges[i+1])/2) for i in range(len(hist))],
            "counts": [float(h) for h in hist]
        }
    }
