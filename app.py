)

st.header("1. Current model solution")
cols = st.columns(4)
for col, flavor, quantity in zip(cols[:3], PRODUCTS, solution["x"]):
    col.metric(flavor, gallons(quantity))
cols[3].metric("Total profit", money(solution["profit"]))

left, right = st.columns(2)
with left:
    st.plotly_chart(product_chart(solution["x"]), use_container_width=True)
with right:
    st.plotly_chart(constraint_chart(solution, capacities), use_container_width=True)

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
    st.plotly_chart(product_chart(base["x"], "Original optimal production"), use_container_width=True)

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
    st.plotly_chart(product_chart(changed["x"], "Plan when banana profit = $1.00"), use_container_width=True)

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
    st.plotly_chart(product_chart(changed["x"], "Plan when banana profit = $0.92"), use_container_width=True)

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
    st.plotly_chart(product_chart(changed["x"], "Plan after losing 3 gallons of cream"), use_container_width=True)

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
