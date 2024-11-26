import pandas as pd

def amortization_table_unitranche(principal, interest_rate, term):
    interest_rate = interest_rate / 100  # Annual rate
    payments = [{'Year': i, 'Interest': principal * interest_rate, 'Balance': principal} for i in range(1, term + 1)]
    payments[-1]['Balance'] = 0  # Bullet repayment
    return pd.DataFrame(payments)

def amortization_table_pik(principal, interest_rate, term):
    balance = principal
    rate = interest_rate / 100
    payments = []
    for year in range(1, term + 1):
        accrued_interest = balance * rate
        balance += accrued_interest  # PIK accrual
        payments.append({'Year': year, 'Interest': accrued_interest, 'Balance': balance})
    return pd.DataFrame(payments)

def capital_structure_extended(unitranche_df, pik_df, preferred_principal, term, purchase_price):
    # Initialize dataframe for the term range
    df = pd.DataFrame({"Year": range(1, term + 1)})
    
    # Assign capital components
    df["Debt"] = unitranche_df["Balance"].values if not unitranche_df.empty else [0] * term
    df["PIK Loan"] = pik_df["Balance"].values if not pik_df.empty else [0] * term
    df["Preferred Equity"] = [preferred_principal] * term  # Constant over time
    df["Equity"] = purchase_price - (df["Debt"] + df["PIK Loan"] + df["Preferred Equity"])

    # Ensure no negative equity (should be 0 at minimum)
    df["Equity"] = df["Equity"].clip(lower=0)

    return df.set_index("Year")



def initial_values(ltm_ebitda, entry_multiple, equity_pct):
    try:
        purchase_price = ltm_ebitda * entry_multiple
        equity = purchase_price * (equity_pct / 100)
        debt = purchase_price - equity
        equity_percentage = equity / purchase_price
        debt_percentage = debt / purchase_price
    except:
        purchase_price = equity = debt = equity_percentage = debt_percentage = 0
    return {
        "purchase_price": purchase_price,
        "equity": equity,
        "debt": debt,
        "equity_percentage": equity_percentage,
        "debt_percentage": debt_percentage,
    }

def appreciation(rate, term):
    if rate is None or term is None or rate < -1 or term < 0:
        print(f"Invalid inputs to appreciation: rate={rate}, term={term}")
        return 0
    return (1 + rate) ** term

def exit_indicators_extended(unitranche_df, pik_df, preferred_principal, preferred_return, term, growth, ltm_ebitda, entry_multiple, equity):
    try:
        # Calculate Exit Enterprise Value
        e_ev = appreciation(growth / 100, term) * ltm_ebitda * entry_multiple

        # Calculate Outstanding Balances
        debt_balance = unitranche_df["Balance"].iloc[-1] if not unitranche_df.empty else 0
        pik_balance = pik_df["Balance"].iloc[-1] if not pik_df.empty else 0
        preferred_accrued = preferred_principal * (1 + preferred_return / 100) ** term

        # Calculate Equity Proceeds
        equity_proceeds = e_ev - (debt_balance + pik_balance + preferred_accrued)

        # Prevent negative equity proceeds
        if equity_proceeds <= 0:
            equity_proceeds = 0

        # Calculate MOIC
        moic = equity_proceeds / equity if equity > 0 else 0

        # Calculate IRR
        irr_exit = (moic ** (1 / term)) - 1 if moic > 0 and term > 0 else 0
    except Exception as e:
        print(f"Error in exit_indicators_extended: {e}")
        e_ev = moic = irr_exit = 0

    return {"e_ev": e_ev, "moic": moic, "irr_exit": irr_exit}



