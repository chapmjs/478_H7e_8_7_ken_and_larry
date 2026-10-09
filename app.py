import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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


def constraint_chart(solution, capacities):
    df = pd.DataFrame(
        {
            "Resource": RESOURCES,
            "Used": solution["used"],
            "Available": capacities,
        }
    ).melt("Resource", var_name="Measure", value_name="Amount")
    fig = px.bar(
        df,
        x="Resource",
        y="Amount",
        color="Measure",
        barmode="group",
        text_auto=".1f",
        color_discrete_map={"Used": "#1976D2", "Available": "#B0BEC5"},
        title="Resource usage at the selected plan",
    )
    fig.update_layout(yaxis_title="Units", legend_title="", height=390)
    return fig


def product_chart(x, title="Production plan"):
    df = pd.DataFrame({"Flavor": PRODUCTS, "Gallons": x})
    fig = px.bar(
        df,
        x="Flavor",
        y="Gallons",
        text_auto=".1f",
        color="Flavor",
        color_discrete_sequence=["#6D4C41", "#FFF3E0", "#F9A825"],
        title=title,
    )
    fig.update_layout(showlegend=False, yaxis_title="Gallons", height=360)
    fig.update_traces(textfont_color="#222222")
    return fig

