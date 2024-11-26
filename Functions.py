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

# Sensitivity Analysis
st.header("Sensitivity Analysis")
loan_sensitivity, growth_sensitivity, equity_sensitivity = st.tabs(["Loan Term", "Growth Rate", "Equity Percentage"])

# Loan Term Sensitivity
with loan_sensitivity:
    term_sensitive = st.slider("Select a new loan term", 1, 20, term)
    df_term_sensitivity = amortization_table_unitranche(unitranche_principal, unitranche_interest, term_sensitive)
    exit_KPI_term = exit_indicators_extended(
        df_term_sensitivity, df_pik, preferred_principal, preferred_return, term_sensitive, growth, ltm_ebitda, entry_multiple, equity
    )
    st.metric(label="Updated IRR", value=f"{exit_KPI_term['irr_exit']:.2%}")

# Growth Rate Sensitivity
with growth_sensitivity:
    growth_sensitive = st.slider("Select a new growth rate (%)", 0, 100, growth)
    exit_KPI_growth = exit_indicators_extended(
        df_unitranche, df_pik, preferred_principal, preferred_return, term, growth_sensitive, ltm_ebitda, entry_multiple, equity
    )
    st.metric(label="Updated IRR", value=f"{exit_KPI_growth['irr_exit']:.2%}")

# Equity Percentage Sensitivity
with equity_sensitivity:
    equity_pct_sensitive = st.slider("Select a new equity percentage (%)", 0, 100, equity_pct)
    updated_equity = initial_values(ltm_ebitda, entry_multiple, equity_pct_sensitive)["equity"]
    exit_KPI_equity = exit_indicators_extended(
        df_unitranche, df_pik, preferred_principal, preferred_return, term, growth, ltm_ebitda, entry_multiple, updated_equity
    )
    st.metric(label="Updated IRR", value=f"{exit_KPI_equity['irr_exit']:.2%}")
