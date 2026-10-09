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
    "use the original data and the original optimal basis, exactly as a Solver "
    "sensitivity report is intended to be used."
)

st.header("1. Current model solution")
cols = st.columns(4)
for col, flavor, quantity in zip(cols[:3], PRODUCTS, solution["x"]):
    col.metric(flavor, gallons(quantity))
cols[3].metric("Total profit", money(solution["profit"]))

left, right = st.columns(2)
with left:
    st.subheader("Production plan")
    st.bar_chart(product_chart_data(solution["x"]), y="Gallons", height=360)
with right:
    st.subheader("Resource usage vs. availability")
    st.bar_chart(constraint_chart_data(solution, capacities), height=390)

usage = pd.DataFrame(
    {
        "Resource": RESOURCES,
        "Used": solution["used"],
        "Available": capacities,
        "Slack": solution["slack"],
        "Binding?": np.isclose(solution["slack"], 0, atol=1e-7),
    }
)
st.dataframe(usage.style.format({"Used": "{:.2f}", "Available": "{:.2f}", "Slack": "{:.2f}"}), use_container_width=True, hide_index=True)

st.header("2. Textbook questions using the original sensitivity report")
base = base_solution()
sens = sensitivity_table(base)

tab_a, tab_b, tab_c, tab_d, tab_e, tab_f = st.tabs(["a) Base case", "b) Banana = $1.00", "c) Banana = $0.92", "d) Cream − 3", "e) Buy sugar?", "f) Milk report"])

with tab_a:
    render_answer_card(
        "a) Optimal solution and total profit",
        "Produce **0 gallons of chocolate, 300 gallons of vanilla, and 75 gallons of banana**. "
        "Maximum profit is **$341.25**.",
        "Sugar and cream are binding: 0.40V + 0.40B = 150 and 0.15V + 0.20B = 60. "
        "Solving those two binding equations gives V = 300 and B = 75. Milk usage is "
        "150 + 30 = 180 gallons, leaving 20 gallons unused. Chocolate has a negative "
        "reduced-cost opportunity at the optimum, so C = 0.",
    )
    st.subheader("Original optimal production")
    st.bar_chart(product_chart_data(base["x"]), y="Gallons", height=360)

with tab_b:
    changed = solve_lp(np.array([1.00, 0.90, 1.00]), BASE_CAPACITY)
    render_answer_card(
        "b) Banana profit increases to $1.00",
        "**Yes, the optimal solution changes:** produce **100 chocolate, 0 vanilla, and 250 banana gallons**. "
        "Profit becomes **$350.00**, an increase of **$8.75**.",
        "The banana objective coefficient has an allowable increase of only about $0.02143 "
        "from the original $0.95. Raising it to $1.00 exceeds that range, so the original "
        "basis is no longer optimal. The new plan uses sugar and cream fully and leaves 55 "
        "gallons of milk unused.",
    )
    st.subheader("Plan when banana profit = $1.00")
    st.bar_chart(product_chart_data(changed["x"]), y="Gallons", height=360)

with tab_c:
    changed = solve_lp(np.array([1.00, 0.90, 0.92]), BASE_CAPACITY)
    render_answer_card(
        "c) Banana profit decreases to $0.92",
        "**No, the optimal production quantities stay the same:** 0 chocolate, 300 vanilla, and 75 banana gallons. "
        "Profit decreases by **$2.25**, from $341.25 to **$339.00**.",
        "The banana coefficient falls by $0.03, which is within its allowable decrease of $0.05. "
        "Therefore the current basis remains optimal. Only the objective value changes: "
        "$341.25 − (75 × $0.03) = $339.00.",
    )
    st.subheader("Plan when banana profit = $0.92")
    st.bar_chart(product_chart_data(changed["x"]), y="Gallons", height=360)

with tab_d:
    changed_capacity = BASE_CAPACITY.copy()
    changed_capacity[2] -= 3
    changed = solve_lp(BASE_PROFITS, changed_capacity)
    render_answer_card(
        "d) Three gallons of cream go sour",
        "**Yes, the quantities change:** produce **0 chocolate, 360 vanilla, and 15 banana gallons**. "
        "Profit falls by **$3.00**, from $341.25 to **$338.25**.",
        "The cream shadow price is $1.00 per gallon, and a 3-gallon reduction is within the "
        "allowable decrease of 3 gallons. Thus the same basis remains optimal. The value of "
        "the lost cream is 3 × $1.00 = $3.00.",
    )
    st.subheader("Plan after losing 3 gallons of cream")
    st.bar_chart(product_chart_data(changed["x"]), y="Gallons", height=360)

with tab_e:
    render_answer_card(
        "e) Buy 15 pounds of sugar for $15",
        "**Yes. Buy it.** The first 10 pounds are worth $18.75 at the shadow price, already exceeding the $15 purchase price. "
        "The minimum net gain is therefore **$3.75**.",
        "Sugar's shadow price is $1.875 per pound, and its allowable increase is 10 pounds. "
        "For those first 10 pounds, the modeled benefit is 10 × $1.875 = $18.75. The offer "
        "is $15 for all 15 pounds, so even without knowing the marginal value of the remaining "
        "5 pounds, the purchase is profitable. The extra sugar cannot make the feasible set worse. "
        "Because 15 exceeds the allowable increase, the exact final profit cannot be inferred "
        "from the original sensitivity report alone.",
    )
    st.metric("Guaranteed net gain from the first 10 pounds", money(10 * 1.875 - 15))

with tab_f:
    st.subheader("f) Milk constraint sensitivity report")
    st.markdown(
        "The completed milk row is shown below. Solver often displays a very large number "
        "such as **1E+30** for an effectively unbounded allowable increase."
    )
    milk_row = sens.iloc[[0]].copy()
    milk_row["Allowable Increase"] = "1E+30 (effectively ∞)"
    st.dataframe(milk_row, use_container_width=True, hide_index=True)
    st.markdown(
        "**How each number is deduced:**\n\n"
        "- **Final value = 180:** 0.45(0) + 0.50(300) + 0.40(75) = 180 gallons of milk used.\n"
        "- **Shadow price = $0:** milk has 20 gallons of slack, so one more gallon has no marginal value at the current plan.\n"
        "- **R.H. side = 200:** this is the stated milk inventory.\n"
        "- **Allowable decrease = 20:** milk can fall from 200 to 180 before the constraint becomes binding.\n"
        "- **Allowable increase = effectively infinite:** additional milk does not improve the current optimum because sugar and cream are already the bottlenecks."
    )

st.header("3. Original Solver-style sensitivity report")
display_sens = sens.copy()
display_sens["Allowable Increase"] = display_sens["Allowable Increase"].map(lambda x: "1E+30" if x > 1e20 else f"{x:.2f}")
st.dataframe(
    display_sens.style.format(
        {
            "Final Value": "{:.2f}",
            "Shadow Price": "${:.3f}",
            "Constraint R.H. Side": "{:.2f}",
            "Allowable Decrease": "{:.2f}",
            "Slack": "{:.2f}",
        }
    ),
    use_container_width=True,
    hide_index=True,
)

st.caption("Educational model. Dollars and resource quantities are based on the problem statement; no demand limits are included.")
