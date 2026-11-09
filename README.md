# Retirement Savings Planner

A Streamlit app that answers a common personal-finance question: *"Am I saving enough for retirement?"*

## Features
- Inputs: age, retirement age, savings, monthly contribution, goal, portfolio mix, inflation
- Monte Carlo simulation (2,000 paths) → probability of reaching your goal
- Inflation-adjusted goal and required monthly contribution
- Charts: projected balance range, contributions vs. growth, distribution of outcomes
- Downloadable year-by-year CSV

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Built with
Python, Streamlit, NumPy, pandas. Developed with AI-assisted coding (Claude).

*Educational purposes only — not financial advice.*
