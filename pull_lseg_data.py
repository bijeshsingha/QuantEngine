import pandas as pd
import numpy as np
import refinitiv.data as rd

rd.open_session()

target_peers = ["SUN.NS", "DIVI.NS", "CIPL.NS", "REDY.NS", "LUPN.NS"]

# The Comprehensive Driver-Based Financial Extraction
financial_fields = [
    # --- Income Statement Drivers ---
    "TR.Revenue.date",            
    "TR.Revenue",                 
    "TR.CostofRevenueTotal",       
    "TR.SGAExpenseTotal",          
    "TR.ResearchAndDevelopment",   
    "TR.EBITDA",                   
    "TR.EBIT",                     
    "TR.IncomeTaxProvision",       
    "TR.DepreciationAmortization", 
    
    # --- Balance Sheet / NWC Drivers ---
    "TR.TotalReceivablesNet",      
    "TR.TotalInventory",           
    "TR.AccountsPayable",          
    "TR.CashAndEquivalents",       
    "TR.TotalAssets",             
    "TR.TotalDebtOutstanding",    
    "TR.CommonEquity",             
    
    # --- Cash Flow Drivers ---
    "TR.CapInvestmentTotal",
    
    # --- WACC & Valuation Drivers ---
    "TR.CompanyMarketCap",
    "TR.InterestExpense",
    "TR.Beta"
]

print("Extracting financial data...")
df_financials = rd.get_data(
    universe=target_peers,
    fields=financial_fields,
    parameters={
        "SDate": "-20Q",
        "EDate": "0Q",
        "FRQ": "FQ",
        "Curn": "INR",
        "Scale": "6"
    }
)

# Save RAW data before any processing
df_financials.to_excel("raw_lseg_data.xlsx", index=False)

# Sort by Date chronologically (Instrument, then Date)
cols = df_financials.columns.tolist()
date_col = cols[1]  # Usually 'Date'

# Clean and drop duplicates based strictly on Ticker and Date
df_financials = df_financials.drop_duplicates(subset=['Instrument', date_col], keep='last')

# Convert all financial columns to standard numpy floats to avoid <NA> boolean errors
for col in df_financials.columns:
    if col not in ['Instrument', date_col]:
        df_financials[col] = pd.to_numeric(df_financials[col], errors='coerce').astype(float)

df_financials[date_col] = pd.to_datetime(df_financials[date_col])
df_financials = df_financials.sort_values(by=['Instrument', date_col]).reset_index(drop=True)

print("Structuring DCF Drivers...")

def get_col(df, keywords):
    for col in df.columns:
        if any(k.lower() in col.lower() for k in keywords):
            return col
    return None

rev_col = get_col(df_financials, ['revenue'])
ebit_col = get_col(df_financials, ['ebit'])
ebitda_col = get_col(df_financials, ['ebitda'])
rec_col = get_col(df_financials, ['receivables'])
inv_col = get_col(df_financials, ['inventory'])
pay_col = get_col(df_financials, ['payable'])
da_col = get_col(df_financials, ['depreciation', 'amortization'])
capex_col = get_col(df_financials, ['capital expenditure', 'capinvestment'])

# WACC Specific columns
mc_col = get_col(df_financials, ['market cap'])
int_exp_col = get_col(df_financials, ['interest expense'])
beta_col = get_col(df_financials, ['beta'])
total_debt_col = get_col(df_financials, ['total debt'])

# 2. Calculate Margins and Ratios
df_financials['EBITDA_Margin'] = np.where(df_financials[rev_col] != 0, df_financials[ebitda_col] / df_financials[rev_col], 0)
df_financials['EBIT_Margin'] = np.where(df_financials[rev_col] != 0, df_financials[ebit_col] / df_financials[rev_col], 0)

# Proxy tax rate
tax_rate = 0.25 

# 3. Calculate Net Working Capital (NWC)
for c in [rec_col, inv_col, pay_col, da_col]:
    if c and c in df_financials.columns:
        df_financials[c] = df_financials[c].fillna(0)

nwc_calc = 0
if rec_col: nwc_calc += df_financials[rec_col]
if inv_col: nwc_calc += df_financials[inv_col]
if pay_col: nwc_calc -= df_financials[pay_col]
df_financials['NWC'] = nwc_calc

df_financials['Change_in_NWC'] = df_financials.groupby('Instrument')['NWC'].diff().fillna(0)

# 4. Calculate Historical Free Cash Flow to the Firm (FCFF)
df_financials['NOPAT'] = df_financials[ebit_col] * (1 - tax_rate)

if capex_col:
    capex_vals = df_financials[capex_col].fillna(0).abs()
else:
    capex_vals = 0

da_vals = df_financials[da_col] if da_col else 0

df_financials['FCFF'] = (
    df_financials['NOPAT'] + 
    da_vals - 
    capex_vals - 
    df_financials['Change_in_NWC']
)

# ---------------------------------------------------------
# STEP 5: CALCULATE WACC (Weighted Average Cost of Capital)
# ---------------------------------------------------------
print("Calculating WACC...")
rf = 0.07  # India 10Y Risk-Free Rate ~7.0%
erp = 0.06 # Equity Risk Premium ~6.0%

# Cost of Equity (CAPM)
if beta_col and not df_financials[beta_col].isna().all():
    betas = df_financials[beta_col].fillna(0.75)
else:
    betas = 0.75 # Proxy beta for defensive pharma

df_financials['Cost_of_Equity'] = rf + (betas * erp)

# Cost of Debt
if int_exp_col and total_debt_col and not df_financials[int_exp_col].isna().all():
    int_exp = df_financials[int_exp_col].fillna(0).abs()
    debt = df_financials[total_debt_col].replace(0, np.nan)
    # Multiply by 4 because interest expense is quarterly
    cost_of_debt = np.where(debt.notna(), (int_exp / debt) * 4, 0.08)
else:
    cost_of_debt = 0.08 # Proxy 8.0% cost of debt

# Cap cost of debt to reasonable bounds (e.g. max 15%)
cost_of_debt = np.clip(cost_of_debt, 0.05, 0.15)
df_financials['Cost_of_Debt'] = cost_of_debt

# Capital Structure (Weights)
if mc_col:
    equity_val = df_financials[mc_col].fillna(0)
    # LSEG Market Cap might be unscaled. If it's huge, divide by 1 million.
    equity_val = np.where(equity_val > 100000000, equity_val / 1000000, equity_val)
else:
    equity_val = 0

debt_val = df_financials[total_debt_col].fillna(0) if total_debt_col else 0

total_capital = equity_val + debt_val
weight_equity = np.where(total_capital > 0, equity_val / total_capital, 0.8)
weight_debt = np.where(total_capital > 0, debt_val / total_capital, 0.2)

# WACC Formula
df_financials['WACC'] = (weight_equity * df_financials['Cost_of_Equity']) + (weight_debt * df_financials['Cost_of_Debt'] * (1 - tax_rate))

# Fill NaNs
df_financials = df_financials.fillna(0)

# Set Index for final export
df_financials = df_financials.set_index(['Instrument', date_col])

print("\n--- Valuation Drivers & WACC Calculated ---")
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
columns_to_view = ['FCFF', 'Cost_of_Equity', 'Cost_of_Debt', 'WACC']
print(df_financials[columns_to_view].tail(10))

# Keep only essential columns for the final model
cash_col = get_col(df_financials, ['cash'])
essential_cols = [
    rev_col, ebit_col, ebitda_col, total_debt_col, cash_col, mc_col,
    'EBITDA_Margin', 'EBIT_Margin', 
    'NWC', 'Change_in_NWC', capex_col,
    'NOPAT', 'FCFF',
    'Cost_of_Equity', 'Cost_of_Debt', 'WACC'
]
essential_cols = [col for col in essential_cols if col is not None and col in df_financials.columns]

# Export to Excel
excel_filename = "pharma_financials_wacc.xlsx"
df_financials[essential_cols].to_excel(excel_filename)
print(f"\nCleaned Model Data successfully exported to {excel_filename}")
print("Raw API data saved to raw_lseg_data.xlsx")

rd.close_session()
