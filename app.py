"""
Retirement Savings Planner
A simple Streamlit app that projects retirement savings and estimates
the probability of reaching a goal using a Monte Carlo simulation.
Built with AI-assisted coding (vibe coding).
"""

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Retirement Savings Planner", page_icon="📈", layout="wide")


# ---------- Core math ----------
def simulate(start, monthly, years, mean_ret, vol, n_sims=2000, seed=42):
    """Monte Carlo of yearly balances. Returns array shape (n_sims, years+1)."""
    rng = np.random.default_rng(seed)
    returns = rng.normal(mean_ret, vol, size=(n_sims, years))
    balances = np.zeros((n_sims, years + 1))
    balances[:, 0] = start
    annual_contrib = monthly * 12
    for y in range(years):
        # contributions added through the year earn roughly half a year of return
        balances[:, y + 1] = balances[:, y] * (1 + returns[:, y]) + annual_contrib * (1 + returns[:, y] / 2)
    return balances


def deterministic(start, monthly, years, rate):
    """Fixed-rate projection with monthly compounding."""
    r = rate / 12
    out = [start]
    bal = start
    for _ in range(years):
        for _ in range(12):
            bal = bal * (1 + r) + monthly
        out.append(bal)
    return np.array(out)


def required_monthly(start, goal, years, rate):
    """Monthly contribution needed to hit the goal at a fixed rate."""
    n = years * 12
    r = rate / 12
    fv_start = start * (1 + r) ** n
    gap = goal - fv_start
    if gap <= 0:
        return 0.0
    if r == 0:
        return gap / n
    return gap * r / ((1 + r) ** n - 1)


# ---------- Sidebar inputs ----------
st.sidebar.header("Your inputs")
age = st.sidebar.number_input("Current age", 16, 80, 22)
ret_age = st.sidebar.number_input("Retirement age", age + 1, 90, max(65, age + 1))
savings = st.sidebar.number_input("Current savings ($)", 0, 10_000_000, 5_000, step=1_000)
monthly = st.sidebar.number_input("Monthly contribution ($)", 0, 100_000, 500, step=50)
goal_today = st.sidebar.number_input("Retirement goal (today's $)", 10_000, 50_000_000, 1_500_000, step=50_000)

st.sidebar.subheader("Market assumptions")
portfolio = st.sidebar.selectbox(
    "Portfolio mix",
    ["Aggressive (90/10)", "Balanced (60/40)", "Conservative (30/70)", "Custom"],
    index=1,
)
presets = {
    "Aggressive (90/10)": (9.0, 16.0),
    "Balanced (60/40)": (7.0, 11.0),
    "Conservative (30/70)": (5.0, 6.5),
}
if portfolio == "Custom":
    mean_ret = st.sidebar.slider("Expected annual return (%)", 0.0, 15.0, 7.0, 0.5)
    vol = st.sidebar.slider("Annual volatility (%)", 0.0, 30.0, 12.0, 0.5)
else:
    mean_ret, vol = presets[portfolio]
    st.sidebar.caption(f"Assumes {mean_ret}% avg return, {vol}% volatility (rough historical estimates).")
inflation = st.sidebar.slider("Inflation (%)", 0.0, 8.0, 2.5, 0.25)

years = int(ret_age - age)
mean_r, vol_r, infl_r = mean_ret / 100, vol / 100, inflation / 100
goal_nominal = goal_today * (1 + infl_r) ** years

# ---------- Calculations ----------
sims = simulate(savings, monthly, years, mean_r, vol_r)
final = sims[:, -1]
prob = (final >= goal_nominal).mean()
p10, p50, p90 = np.percentile(sims, [10, 50, 90], axis=0)
det = deterministic(savings, monthly, years, mean_r)
need = required_monthly(savings, goal_nominal, years, mean_r)
total_contrib = savings + monthly * 12 * years

# ---------- Layout ----------
st.title("📈 Retirement Savings Planner")
st.write(
    "Will your savings plan get you to your retirement goal? This app runs 2,000 simulated "
    "market paths to show a likely range of outcomes, not just one number."
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Chance of hitting goal", f"{prob:.0%}")
c2.metric("Median balance at retirement", f"${p50[-1]:,.0f}")
c3.metric("Goal in future dollars", f"${goal_nominal:,.0f}", help="Your goal adjusted for inflation")
c4.metric("Monthly needed (avg. return)", f"${need:,.0f}", delta=f"{monthly - need:+,.0f} vs. now", delta_color="normal")

if prob >= 0.8:
    st.success(f"You're on track. In {prob:.0%} of simulations you reach your goal by age {ret_age}.")
elif prob >= 0.5:
    st.warning(f"It's close — {prob:.0%} chance. Saving about ${max(need - monthly, 0):,.0f} more per month would help.")
else:
    st.error(f"Only a {prob:.0%} chance. Consider saving more, retiring later, or revisiting your goal.")

st.subheader("Projected balance over time")
ages = np.arange(age, ret_age + 1)
chart_df = pd.DataFrame(
    {
        "Pessimistic (10th pct)": p10,
        "Median": p50,
        "Optimistic (90th pct)": p90,
        "Goal": np.full_like(p50, goal_nominal),
    },
    index=pd.Index(ages, name="Age"),
)
st.line_chart(chart_df)

left, right = st.columns(2)
with left:
    st.subheader("Where the money comes from")
    growth = max(p50[-1] - total_contrib, 0)
    st.bar_chart(pd.DataFrame({"Amount ($)": [total_contrib, growth]}, index=["Your contributions", "Investment growth"]))
with right:
    st.subheader("Distribution of final balances")
    hist, edges = np.histogram(np.clip(final, 0, np.percentile(final, 99)), bins=30)
    labels = [f"${e/1e6:.1f}M" for e in edges[:-1]]
    st.bar_chart(pd.DataFrame({"Simulations": hist}, index=labels))

with st.expander("Year-by-year table"):
    table = pd.DataFrame(
        {"Age": ages, "Fixed-rate projection": det, "10th pct": p10, "Median": p50, "90th pct": p90}
    ).set_index("Age")
    st.dataframe(table.style.format("${:,.0f}"), use_container_width=True)
    st.download_button("Download CSV", table.to_csv().encode(), "retirement_projection.csv", "text/csv")

with st.expander("How it works"):
    st.markdown(
        """
- Each year's return is drawn from a normal distribution using your expected return and volatility.
- Contributions are added each year; 2,000 paths are simulated.
- The goal is inflated to future dollars so it compares fairly to future balances.
- "Monthly needed" uses the standard future-value-of-annuity formula at the average return.

*Educational tool only — not financial advice. Real returns aren't normally distributed and taxes/fees are ignored.*
"""
    )
