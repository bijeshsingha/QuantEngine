import pandas as pd

# --- Standalone 5-Year Driver Forecast Engine ---

# 1. Establish the Baseline (Using the most recent figures from your Day 2 output)
latest_historical_revenue = 450000.0  # Base Year Revenue in INR Millions

# 2. Hardcode Your Most Likely Strategic Drivers
expected_revenue_growth = 0.10        # 10% annual top-line growth
target_ebit_margin = 0.23             # 23% operating margin (based on your verified baseline)
tax_rate = 0.25                       # Corporate tax rate
reinvestment_rate = 0.30              # 30% of EBIT must be reinvested into CapEx and NWC to support growth

# 3. The Forecast Loop
forecast_records = []
current_revenue = latest_historical_revenue

for year in range(1, 6):
    # Step A: Project Top-Line Revenue
    current_revenue = current_revenue * (1 + expected_revenue_growth)
    
    # Step B: Compute Operating Profitability (EBIT)
    projected_ebit = current_revenue * target_ebit_margin
    
    # Step C: Compute Net Operating Profit After Tax (NOPAT)
    nopat = projected_ebit * (1 - tax_rate)
    
    # Step D: Apply the Reinvestment Driver
    # Capital Reinvestment = CapEx + Change in NWC - D&A
    required_reinvestment = projected_ebit * reinvestment_rate
    
    # Step E: Calculate Free Cash Flow to the Firm
    # FCFF = NOPAT - Reinvestment
    fcff = nopat - required_reinvestment
    
    forecast_records.append({
        "Year": f"Year {year}",
        "Projected Revenue": round(current_revenue, 2),
        "Projected EBIT": round(projected_ebit, 2),
        "NOPAT": round(nopat, 2),
        "Required Reinvestment": round(required_reinvestment, 2),
        "FCFF": round(fcff, 2)
    })

# Convert to DataFrame for presentation
df_base_case_forecast = pd.DataFrame(forecast_records)

print("--- BASE CASE DETERMINISTIC 5-YEAR FORECAST (INR Millions) ---")
print(df_base_case_forecast.to_string(index=False))

# Export to excel
df_base_case_forecast.to_excel("base_case_forecast.xlsx", index=False)
print("\nExported to base_case_forecast.xlsx")
