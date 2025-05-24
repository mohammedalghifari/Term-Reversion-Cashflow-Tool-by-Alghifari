import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="10-Year Term & Reversion Cash Flow", layout="centered")
st.title("🏢 Multi-Tenant Property Cash Flow Tool")
st.markdown("Upload lease data, set valuation date, and apply escalation to generate a 10-year rent cash flow including reversion.")

# Sample data for download
sample_data = pd.DataFrame({
    "Tenant": ["Tenant A", "Tenant B", "Tenant C"],
    "Lease Start": ["2023-01-01", "2024-06-01", "2025-01-01"],
    "Lease End": ["2027-12-31", "2029-05-31", "2035-12-31"],
    "Passing Rent (AED/year)": [100000, 120000, 90000],
    "Market Rent (AED/year)": [120000, 140000, 95000]
})
sample_output = BytesIO()
with pd.ExcelWriter(sample_output, engine='openpyxl') as writer:
    sample_data.to_excel(writer, index=False, sheet_name="Sample Data")
sample_output.seek(0)

st.download_button(
    label="⬇️ Download Sample Excel Format",
    data=sample_output,
    file_name="sample_lease_data.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# Upload Excel file
uploaded_file = st.file_uploader("📁 Upload Lease Excel File", type=["xlsx"])

# Input valuation date and rent escalation
valuation_date_input = st.date_input("📅 Valuation Date", value=datetime.today())
escalation_percent = st.number_input("📈 Rent Escalation per Year (%)", min_value=0.0, max_value=20.0, value=0.0, step=0.1)

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        st.success("✅ Lease data loaded successfully.")

        # Check required columns
        required_cols = {'Tenant', 'Lease Start', 'Lease End', 'Passing Rent (AED/year)', 'Market Rent (AED/year)'}
        if not required_cols.issubset(df.columns):
            st.error(f"❌ Missing columns. Required: {required_cols}")
        else:
            # Convert date columns to datetime
            df['Lease Start'] = pd.to_datetime(df['Lease Start'])
            df['Lease End'] = pd.to_datetime(df['Lease End'])

            # Generate 10-year period from valuation date
            valuation_year = valuation_date_input.year
            years = list(range(valuation_year, valuation_year + 10))

            # Build cash flow matrix
            cashflow_matrix = []
            for idx, row in df.iterrows():
                tenant_row = []
                for i, year in enumerate(years):
                    start_of_year = pd.Timestamp(f"{year}-01-01")
                    end_of_year = pd.Timestamp(f"{year}-12-31")
                    lease_start = row['Lease Start']
                    lease_end = row['Lease End']

                    days_in_year = (end_of_year - start_of_year).days + 1

                    if lease_end < start_of_year:
                        # Reversion period (use Market Rent)
                        annual_rent = row['Market Rent (AED/year)'] * ((1 + escalation_percent / 100) ** i)
                        tenant_row.append(round(annual_rent, 2))
                    elif lease_start > end_of_year:
                        tenant_row.append(0)
                    else:
                        # In-term (use Passing Rent)
                        period_start = max(start_of_year, lease_start)
                        period_end = min(end_of_year, lease_end)
                        days_covered = (period_end - period_start).days + 1

                        annual_rent = row['Passing Rent (AED/year)'] * ((1 + escalation_percent / 100) ** i)
                        pro_rated_rent = annual_rent * (days_covered / days_in_year)
                        tenant_row.append(round(pro_rated_rent, 2))
                cashflow_matrix.append(tenant_row)

            cashflow_df = pd.DataFrame(cashflow_matrix, columns=[str(y) for y in years])
            cashflow_df.insert(0, 'Tenant', df['Tenant'])

            st.subheader("💰 10-Year Term & Reversion Cash Flow")
            st.dataframe(cashflow_df)

            # Export to Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                cashflow_df.to_excel(writer, index=False, sheet_name="Cash Flow")
            output.seek(0)

            st.download_button(
                label="⬇️ Download Cash Flow Excel",
                data=output,
                file_name="10_year_cash_flow.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"❌ Error: {e}")
