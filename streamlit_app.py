import streamlit as st
import pandas as pd
import plotly.express as px
from Functions import (
    amortization_table_unitranche,
    amortization_table_pik,
    capital_structure_extended,
    initial_values,
    exit_indicators_extended,
    appreciation,
)

# Title
st.title("Leveraged Buyout (LBO)")

# Sidebar for Inputs
st.sidebar.header("Inputs")
ltm_ebitda = st.sidebar.number_input("LTM EBITDA", value=10, step=1, help="Last Twelve Months EBITDA")
entry_multiple = st.sidebar.number_input("Entry Multiple (x)", value=6, step=1, help="Multiple used to calculate purchase price")
equity_pct = st.sidebar.slider("Equity Percentage (%)", 0, 100, 40, help="Percentage of equity in the capital structure")

# Sidebar for Debt Parameters
st.sidebar.header("Debt Parameters")
interest_rate = st.sidebar.number_input("Interest Rate (%)", value=5, step=1, help="Annual interest rate on debt")
term = st.sidebar.slider("Loan Term (years)", 1, 20, 5, help="Duration of the loan in years")
growth = st.sidebar.number_input("YOY Growth (%)", value=5, step=1, help="Year-over-year EBITDA growth rate")

# Sidebar for Additional Financing
st.sidebar.header("Unitranche")
unitranche_principal = st.sidebar.number_input("Unitranche Principal ($)", value=50_000_000)
unitranche_interest = st.sidebar.number_input("Unitranche Interest Rate (%)", value=8)

st.sidebar.header("PIK Loan")
pik_principal = st.sidebar.number_input("PIK Loan Principal ($)", value=30_000_000)
pik_interest = st.sidebar.number_input("PIK Loan Interest Rate (%)", value=12)

st.sidebar.header("Preferred Equity")
preferred_principal = st.sidebar.number_input("Preferred Equity Contribution ($)", value=20_000_000)
preferred_return = st.sidebar.number_input("Preferred Return Rate (%)", value=10)
preferred_accrual = st.sidebar.radio("Preferred Dividends", ["Accrued", "Periodic"], index=0)

# Initial Values Calculation
inputs = initial_values(ltm_ebitda, entry_multiple, equity_pct)
purchase_price = inputs["purchase_price"]
equity = inputs["equity"]
debt = inputs["debt"]
equity_percentage = inputs["equity_percentage"]
debt_percentage = inputs["debt_percentage"]

# Main Outputs Section
st.header("Capital Structure")
col1, col2, col3 = st.columns(3)
col1.metric(label="Equity", value=f"${equity:,.0f}", delta=f"{equity_percentage:.0%}")
col2.metric(label="Debt", value=f"${debt:,.0f}", delta=f"{debt_percentage:.0%}")
col3.metric(label="Enterprise Value", value=f"${purchase_price:,.0f}")

# Amortization Tables
st.header("Financial Projections")

# Generate Amortization Tables for Each Financing Type
df_unitranche = amortization_table_unitranche(unitranche_principal, unitranche_interest, term)
df_pik = amortization_table_pik(pik_principal, pik_interest, term)

# Capital Structure Visualization
st.header("Capital Structure Over Time")
try:
    df_capital = capital_structure_extended(df_unitranche, df_pik, preferred_principal, term, purchase_price)
    fig = px.bar(
        df_capital,
        x=df_capital.index,
        y=["Debt", "PIK Loan", "Preferred Equity", "Equity"],
        barmode="stack",
        title="Capital Structure Over Time",
        labels={"value": "USD", "variable": "Capital Type"}
    )
    st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.error(f"Error generating capital structure chart: {e}")

# Exit Metrics
st.header("Exit Metrics")
try:
    exit_KPI = exit_indicators_extended(df_unitranche, df_pik, preferred_principal, preferred_return, term, growth, ltm_ebitda, entry_multiple, equity)
    col1, col2, col3 = st.columns(3)
    col1.metric(label="Exit Enterprise Value", value=f"${exit_KPI['e_ev']:,.0f}")
    col2.metric(label="MOIC", value=f"{exit_KPI['moic']:.2f}x")
    col3.metric(label="IRR", value=f"{exit_KPI['irr_exit']:.2%}")
except Exception as e:
    st.error(f"Error calculating exit metrics: {e}")
