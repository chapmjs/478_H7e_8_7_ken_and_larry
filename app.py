import numpy as np
import pandas as pd
import streamlit as st
from scipy.optimize import linprog


st.set_page_config(
    page_title="Ken & Larry Ice Cream LP",
    page_icon="🍦",
    layout="wide",
)


PRODUCTS = ["Chocolate", "Vanilla", "Banana"]
RESOURCES = ["Milk", "Sugar", "Cream"]
A = np.array(
    [
        [0.45, 0.50, 0.40],
        [0.50, 0.40, 0.40],
        [0.10, 0.15, 0.20],
    ],
    dtype=float,
)
BASE_PROFITS = np.array([1.00, 0.90, 0.95], dtype=float)
BASE_CAPACITY = np.array([200.0, 150.0, 60.0], dtype=float)


def solve_lp(profits: np.ndarray, capacities: np.ndarray):
    result = linprog(
        -profits,
        A_ub=A,
        b_ub=capacities,
        bounds=[(0, None)] * 3,
        method="highs",
    )
    if not result.success:
        raise ValueError(result.message)
    x = result.x
    used = A @ x
    return {
        "x": x,
        "profit": float(profits @ x),
        "used": used,
        "slack": capacities - used,
        "result": result,
    }


def money(value):
    return f"${value:,.2f}"


def gallons(value):
    return f"{value:,.2f} gal"


def base_solution():
    return solve_lp(BASE_PROFITS, BASE_CAPACITY)


def sensitivity_table(solution):
    # Solver's convention: for a max problem with <= constraints, shadow prices
    # are reported as positive marginal values.
    result = solution["result"]
    shadow_prices = -np.asarray(result.ineqlin.marginals)
    final_values = solution["used"]
    slacks = solution["slack"]
    rhs = BASE_CAPACITY

    # For the two binding constraints, the current basis is V/B. The basis
    # remains feasible as long as the basic variables remain nonnegative.
    # Milk is nonbinding, so its decrease range ends at its slack; its increase
    # range is unbounded for purposes of the Solver report.
    allowable_increase = [np.inf, 10.0, 1.0e30]
    allowable_decrease = [20.0, 10.0, 3.0]
    return pd.DataFrame(
        {
            "Constraint": RESOURCES,
            "Final Value": final_values,
            "Shadow Price": shadow_prices,
            "Constraint R.H. Side": rhs,
            "Allowable Increase": allowable_increase,
            "Allowable Decrease": allowable_decrease,
            "Slack": slacks,
        }
    )


def constraint_chart_data(solution, capacities):
    return pd.DataFrame(
        {"Used": solution["used"], "Available": capacities}, index=RESOURCES
    )


def product_chart_data(x):
    return pd.DataFrame({"Gallons": x}, index=PRODUCTS)


def render_answer_card(title, answer, explanation):
    st.subheader(title)
    st.markdown(answer)
    with st.expander("Why this follows from sensitivity analysis"):
        st.markdown(explanation)


st.title("🍦 Ken & Larry, Inc. — Ice Cream Production Optimizer")
st.caption("Linear programming, Solver-style sensitivity analysis, and decision support")

with st.sidebar:
    st.header("Model inputs")
    st.write("Adjust the profit and inventory assumptions, then click **Run model**.")
    chocolate_profit = st.number_input("Chocolate profit / gallon", 0.0, 10.0, 1.00, 0.01)
    vanilla_profit = st.number_input("Vanilla profit / gallon", 0.0, 10.0, 0.90, 0.01)
    banana_profit = st.number_input("Banana profit / gallon", 0.0, 10.0, 0.95, 0.01)
    milk = st.number_input("Milk available (gallons)", 0.0, 10000.0, 200.0, 1.0)
    sugar = st.number_input("Sugar available (pounds)", 0.0, 10000.0, 150.0, 1.0)
    cream = st.number_input("Cream available (gallons)", 0.0, 10000.0, 60.0, 1.0)
    run = st.button("Run model", type="primary", use_container_width=True)

profits = np.array([chocolate_profit, vanilla_profit, banana_profit])
capacities = np.array([milk, sugar, cream])
solution = solve_lp(profits, capacities)

if run or "ran_once" not in st.session_state:
    st.session_state.ran_once = True

st.info(
    "The app solves the selected LP for exploration. The textbook answers below "
