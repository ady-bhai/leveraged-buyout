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
st.title("Leveraged Buyout Model")

# Sidebar for Inputs
st.sidebar.header("Inputs")
ltm_ebitda = st.sidebar.number_input("LTM EBITDA", value=10, step=1, help="Last Twelve Months EBITDA (Default: 10)")
entry_multiple = st.sidebar.number_input("Entry Multiple (x)", value=8, step=1, help="Entry multiple for valuation (Default: 8)")
equity_pct = st.sidebar.slider("Equity Percentage (%)", 30, 60, 40, help="Percentage of equity in the capital structure (Default: 40%)")

# Sidebar for Debt Parameters
st.sidebar.header("Debt Parameters")
interest_rate = st.sidebar.number_input("Interest Rate (%)", value=6, step=1, help="Annual interest rate on debt (Default: 6%)")
term = st.sidebar.slider("Loan Term (years)", 5, 10, 7, help="Loan term in years (Default: 7 years)")
growth = st.sidebar.number_input("YOY Growth (%)", value=8, step=1, help="Year-over-year EBITDA growth rate (Default: 8%)")

# Sidebar for Unitranche Financing
st.sidebar.header("Unitranche")
unitranche_principal = st.sidebar.number_input(
    "Unitranche Principal ($)", value=48_000_000, step=1_000_000, help="Principal for unitranche debt (Default: $48M)"
)
unitranche_interest = st.sidebar.number_input(
    "Unitranche Interest Rate (%)", value=6, step=1, help="Annual interest rate for unitranche (Default: 6%)"
)

# Sidebar for PIK Loan
st.sidebar.header("PIK Loan")
pik_principal = st.sidebar.number_input(
    "PIK Loan Principal ($)", value=8_000_000, step=1_000_000, help="Principal for PIK loan (Default: $8M)"
)
pik_interest = st.sidebar.number_input(
    "PIK Loan Interest Rate (%)", value=10, step=1, help="Annual interest rate for PIK loan (Default: 10%)"
)

# Sidebar for Preferred Equity
st.sidebar.header("Preferred Equity")
preferred_principal = st.sidebar.number_input(
    "Preferred Equity Contribution ($)", value=12_000_000, step=1_000_000, help="Preferred equity contribution (Default: $12M)"
)
preferred_return = st.sidebar.number_input(
    "Preferred Return Rate (%)", value=10, step=1, help="Return rate on preferred equity (Default: 10%)"
)

# Initial Values Calculation
inputs = initial_values(ltm_ebitda, entry_multiple, equity_pct)
purchase_price = inputs["purchase_price"]
equity = inputs["equity"]
debt = inputs["debt"]
equity_percentage = inputs["equity_percentage"]
debt_percentage = inputs["debt_percentage"]

# Display Capital Structure
st.header("Capital Structure")
col1, col2, col3 = st.columns(3)
col1.metric(label="Equity", value=f"${equity:,.0f}", delta=f"{equity_percentage:.0%}")
col2.metric(label="Debt", value=f"${debt:,.0f}", delta=f"{debt_percentage:.0%}")
col3.metric(label="Enterprise Value", value=f"${purchase_price:,.0f}")

# Financial Projections with Tabs
st.header("Financial Projections")
df_unitranche = amortization_table_unitranche(unitranche_principal, unitranche_interest, term)
df_pik = amortization_table_pik(pik_principal, pik_interest, term)

projections_tab, amortization_tab, capital_structure_tab = st.tabs(["Projections", "Loan Amortization", "Capital Structure"])

# Projections Tab
with projections_tab:
    st.subheader("EBITDA and Projections")
    projections_data = {"Year": [], "EBITDA": [], "Interest": [], "Net Income": []}
    for year in range(1, term + 1):
        ebitda = appreciation(growth / 100, year) * ltm_ebitda
        interest = df_unitranche["Interest"].iloc[year - 1] if year - 1 < len(df_unitranche) else 0
        net_income = ebitda - interest
        projections_data["Year"].append(year)
        projections_data["EBITDA"].append(ebitda)
        projections_data["Interest"].append(interest)
        projections_data["Net Income"].append(net_income)
    df_projections = pd.DataFrame(projections_data)
    st.dataframe(df_projections.style.format("${:,.0f}"))

# Loan Amortization Tab
with amortization_tab:
    st.subheader("Amortization Tables")
    st.write("Unitranche Amortization Table")
    st.dataframe(df_unitranche.style.format("${:,.0f}"))
    st.write("PIK Loan Amortization Table")
    st.dataframe(df_pik.style.format("${:,.0f}"))

# Capital Structure Tab
with capital_structure_tab:
    st.subheader("Capital Structure Over Time")
    df_capital = capital_structure_extended(df_unitranche, df_pik, preferred_principal, term, purchase_price)
    fig = px.bar(
        df_capital.reset_index(),
        x="Year",
        y=["Debt", "PIK Loan", "Preferred Equity", "Equity"],
        barmode="stack",
        title="Capital Structure Over Time",
        labels={"value": "USD", "variable": "Capital Type"}
    )
    st.plotly_chart(fig, use_container_width=True)

# Exit Metrics
st.header("Exit Metrics")
exit_KPI = exit_indicators_extended(
    df_unitranche, df_pik, preferred_principal, preferred_return, term, growth, ltm_ebitda, entry_multiple, equity
)
col1, col2, col3 = st.columns(3)
col1.metric(label="Exit Enterprise Value", value=f"${exit_KPI['e_ev']:,.0f}")
col2.metric(label="MOIC", value=f"{exit_KPI['moic']:.2f}x")
col3.metric(label="IRR", value=f"{exit_KPI['irr_exit']:.2%}")
