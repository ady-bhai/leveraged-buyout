import streamlit as st
import pandas as pd
import plotly.express as px
from Functions import *

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

# Amortization Table
st.header("Financial Projections")

# Generate Amortization Table
df_amortization = amortization_table(debt, interest_rate, term)

# Projections and EBITDA Table
try:
    # Dynamic Year Range
    years = range(1, term + 1)
    projections_data = {"Year": [], "EBITDA": [], "Interest": [], "Net Income": []}
    
    for year in years:
        ebitda = appreciation(growth / 100, year) * ltm_ebitda
        interest = df_amortization.loc[year, "Interest"] if year in df_amortization.index else 0
        net_income = ebitda - interest
        projections_data["Year"].append(year)
        projections_data["EBITDA"].append(ebitda)
        projections_data["Interest"].append(interest)
        projections_data["Net Income"].append(net_income)

    df_projections = pd.DataFrame(projections_data)
    st.dataframe(df_projections.style.format("${:,.0f}"))

except Exception as e:
    st.error(f"Error generating projections: {e}")

# Capital Structure Visualization
st.header("Capital Structure Over Time")
try:
    df_capital = capital_structure(df_amortization, purchase_price)
    fig = px.bar(
        df_capital,
        x=df_capital.index,
        y=["Debt", "Equity"],
        barmode="stack",
        title="Debt vs. Equity Over Time",
        labels={"value": "USD", "variable": "Capital Type"}
    )
    st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.error(f"Error generating capital structure chart: {e}")

# Exit Metrics
st.header("Exit Metrics")
try:
    exit_KPI = exit_indicators(df_amortization, growth, ltm_ebitda, entry_multiple, equity)
    col1, col2, col3 = st.columns(3)
    col1.metric(label="Exit Enterprise Value", value=f"${exit_KPI['e_ev']:,.0f}")
    col2.metric(label="MOIC", value=f"{exit_KPI['moic']:.2f}x")
    col3.metric(label="IRR", value=f"{exit_KPI['irr_exit']:.2%}")
except Exception as e:
    st.error(f"Error calculating exit metrics: {e}")

# Sensitivity Analysis
st.header("Sensitivity Analysis")
tab1, tab2, tab3 = st.tabs(["Loan Term", "Growth Rate", "Equity Percentage"])

with tab1:
    term_sensitive = st.slider("Select a new loan term", 1, 20, term)
    try:
        df_term_sensitive = amortization_table(debt, interest_rate, term_sensitive)
        exit_KPI_term = exit_indicators(df_term_sensitive, growth, ltm_ebitda, entry_multiple, equity)
        st.metric("Updated IRR", f"{exit_KPI_term['irr_exit']:.2%}")
    except Exception as e:
        st.error(f"Error with term sensitivity: {e}")

with tab2:
    growth_sensitive = st.slider("Select a new growth rate (%)", 0, 100, growth)
    try:
        exit_KPI_growth = exit_indicators(df_amortization, growth_sensitive, ltm_ebitda, entry_multiple, equity)
        st.metric("Updated IRR", f"{exit_KPI_growth['irr_exit']:.2%}")
    except Exception as e:
        st.error(f"Error with growth sensitivity: {e}")

with tab3:
    equity_pct_sensitive = st.slider("Select a new equity percentage (%)", 0, 100, equity_pct)
    try:
        updated_inputs = initial_values(ltm_ebitda, entry_multiple, equity_pct_sensitive)
        updated_equity = updated_inputs["equity"]
        exit_KPI_equity = exit_indicators(df_amortization, growth, ltm_ebitda, entry_multiple, updated_equity)
        st.metric("Updated IRR", f"{exit_KPI_equity['irr_exit']:.2%}")
    except Exception as e:
        st.error(f"Error with equity sensitivity: {e}")
