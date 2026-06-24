import pandas as pd
import refinitiv.data as rd

rd.open_session()

target_peers = ["SUN.NS", "DIVI.NS", "CIPL.NS", "REDY.NS", "LUPN.NS"]

# Comprehensive list of standard financial statement fields for all 3 statements
comprehensive_fields = [
    # --- Income Statement ---
    "TR.Revenue.date",
    "TR.Revenue",
    "TR.CostofRevenueTotal",
    "TR.GrossProfit",
    "TR.SGAExpenseTotal",
    "TR.ResearchAndDevelopment",
    "TR.OperatingExpense",
    "TR.OperatingProfit",
    "TR.EBITDA",
    "TR.EBIT",
    "TR.InterestExpense",
    "TR.InterestExpenseNet",
    "TR.PreTaxIncome",
    "TR.IncomeTaxProvision",
    "TR.NetIncome",
    "TR.BasicEPS",

    # --- Balance Sheet ---
    "TR.CashAndEquivalents",
    "TR.ShortTermInvestments",
    "TR.TotalReceivablesNet",
    "TR.TotalInventory",
    "TR.TotalCurrentAssets",
    "TR.NetPropertyPlantEquipment",
    "TR.IntangibleAssets",
    "TR.TotalAssets",
    "TR.AccountsPayable",
    "TR.TotalCurrentLiabilities",
    "TR.TotalLongTermDebt",
    "TR.TotalDebtOutstanding",
    "TR.TotalLiabilities",
    "TR.CommonStock",
    "TR.RetainedEarnings",
    "TR.TotalEquity",
    "TR.TotalLiabilitiesAndEquity",

    # --- Cash Flow Statement ---
    "TR.NetIncomeStartingLine",
    "TR.DepreciationAmortization",
    "TR.NetCashFromOperatingActivities",
    "TR.CapInvestmentTotal",
    "TR.NetCashUsedInInvestingActivities",
    "TR.CashDividendsPaid",
    "TR.IssuanceRetirementOfDebtNet",
    "TR.IssuanceRetirementOfStockNet",
    "TR.NetCashFromFinancingActivities",
    "TR.NetChangeInCash",
    
    # --- Key supplemental ---
    "TR.CompanyMarketCap"
]

print("Fetching comprehensive raw financial statements for 5 years...")
df_all = rd.get_data(
    universe=target_peers,
    fields=comprehensive_fields,
    parameters={
        "SDate": "-20Q",
        "EDate": "0Q",
        "FRQ": "FQ",
        "Curn": "INR",
        "Scale": "6" # In Millions
    }
)

cols = df_all.columns.tolist()
date_col = cols[1]

# Clean duplicates based on Ticker and Date
df_all = df_all.drop_duplicates(subset=['Instrument', date_col], keep='last')

# Sort chronologically
df_all[date_col] = pd.to_datetime(df_all[date_col])
df_all = df_all.sort_values(by=['Instrument', date_col]).reset_index(drop=True)

# Save to Excel
excel_file = "comprehensive_raw_financials.xlsx"
df_all.to_excel(excel_file, index=False)
print(f"Successfully saved full financial statements to {excel_file}")

rd.close_session()
