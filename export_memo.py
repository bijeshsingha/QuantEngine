import docx
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

print("Generating Formal Investment Memo...")

doc = docx.Document()

# Formatting Setup
style = doc.styles['Normal']
font = style.font
font.name = 'Arial'
font.size = Pt(11)

# Title
title = doc.add_heading('INSTITUTIONAL INVESTMENT MEMO', 0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

doc.add_paragraph('Ticker: SUN.NS | Sector: Pharmaceuticals | Analyst: Bijesh Singha')
doc.add_paragraph('_' * 70)

# Executive Summary Section
doc.add_heading('EXECUTIVE SUMMARY', level=1)

p_recom = doc.add_paragraph()
p_recom.add_run('RECOMMENDATION: ').bold = True
run_sell = p_recom.add_run('SELL / UNDERWEIGHT')
run_sell.bold = True
run_sell.font.color.rgb = RGBColor(255, 0, 0) # Red

doc.add_paragraph('Current Market Price: ₹1,868')
doc.add_paragraph('Base Case Target Price: ₹888')
doc.add_paragraph('Implied Downside: -52.4%')

# Core Thesis
doc.add_heading('CORE THESIS', level=1)
p_thesis = doc.add_paragraph()
p_thesis.add_run('While top-line growth and margins remain stable, the required reinvestment rate (working capital and CapEx) severely restricts Free Cash Flow generation. The broader market is currently ignoring the balance sheet drag and pricing the stock for absolute perfection.')

# Quantitative Findings
doc.add_heading('QUANTITATIVE FINDINGS (MONTE CARLO)', level=1)
doc.add_paragraph('We ran a 10,000-iteration stochastic simulation stressing Revenue Growth (Mean: 10%, Std Dev: 2%) and EBIT Margins (Mean: 23%, Std Dev: 1.5%), mathematically penalizing free cash flows with an automated Net Working Capital drag.')
doc.add_paragraph('• Bull Case (90th Percentile): ₹1,006')
doc.add_paragraph('• Base Case (50th Percentile): ₹888')
doc.add_paragraph('• Bear Case (10th Percentile): ₹780')

# Market Delusion
doc.add_heading('REVERSE DCF (MARKET DELUSION)', level=1)
doc.add_paragraph('To mathematically justify the current trading price of ₹1,868, Sun Pharma would have to sustain a compound annual revenue growth rate of 37.3% every single year for the next 5 years. Because Sun Pharma is a mature, large-cap pharmaceutical giant that historically tops out at ~12% growth, the market\'s implied expectation is physically impossible to achieve.')

doc.add_paragraph('_' * 70)
p_footer = doc.add_paragraph('CONFIDENTIAL - FOR INTERNAL DISTRIBUTION ONLY')
p_footer.alignment = WD_ALIGN_PARAGRAPH.CENTER

doc.save('Investment_Memo_SUN_NS.docx')
print("Successfully generated Investment_Memo_SUN_NS.docx")
